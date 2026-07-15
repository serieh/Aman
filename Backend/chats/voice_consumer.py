# chats/voice_consumer.py
import json
import logging
import asyncio
import base64
import uuid
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from agent.runner import run_agent
from chats.models import Chat, Message
from logger import log_context
from agent.voice.stt import transcribe_audio
from agent.voice.tts import synthesize_speech
from agent.voice.voices import resolve_voice_for_language, get_voice, resolve_voice_for_text

logger = logging.getLogger(__name__)

# Active voice tasks tracking
ACTIVE_VOICE_TASKS = {}

class SentenceBuffer:
    def __init__(self, min_length=45):
        self.buffer = ""
        self.min_length = min_length
        # Split on sentence boundaries
        self.split_pat = re.compile(r'(?<=[.!?؟\n])\s+')

    def add_chunk(self, chunk: str):
        self.buffer += chunk

    def get_sentences(self, force_remaining=False):
        if not self.buffer:
            return []

        if force_remaining:
            remaining = self.buffer.strip()
            self.buffer = ""
            return [remaining] if remaining else []

        parts = self.split_pat.split(self.buffer)
        if len(parts) <= 1:
            return []

        sentences_to_yield = []
        for p in parts[:-1]:
            sentences_to_yield.append(p.strip())

        self.buffer = parts[-1]

        merged = []
        current = ""
        for s in sentences_to_yield:
            if not s:
                continue
            if not current:
                current = s
            else:
                current += " " + s
            # Yield if it's long enough or ends with terminal punctuation
            if len(current) >= self.min_length or (current and current[-1] in ".!?؟"):
                merged.append(current)
                current = ""
        if current:
            self.buffer = current + " " + self.buffer

        return merged

class VoiceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
        self.active_task = None
        self.audio_chunks = []
        self.state = "idle"  # idle | listening | processing

        user_id = self.user.id if self.user and self.user.is_authenticated else "-"
        with log_context(chat_id=self.chat_id, user_id=user_id):
            if isinstance(self.user, AnonymousUser):
                await self.close(code=4003)
                return

            chat_exists = await self.check_chat_exists(self.chat_id, self.user)
            if not chat_exists:
                await self.close(code=4004)
                return

            self.chat_group = f"chat_{self.chat_id}"
            self.user_group = f"user_{self.user.id}"

            await self.channel_layer.group_add(self.chat_group, self.channel_name)
            await self.channel_layer.group_add(self.user_group, self.channel_name)

            await self.accept()
            logger.info(f"Voice WebSocket connected for chat {self.chat_id}")

    async def disconnect(self, close_code):
        user_id = self.user.id if self.user and self.user.is_authenticated else "-"
        with log_context(chat_id=self.chat_id, user_id=user_id):
            if self.active_task and not self.active_task.done():
                self.active_task.cancel()
            
            if hasattr(self, 'chat_group'):
                await self.channel_layer.group_discard(self.chat_group, self.channel_name)
            if hasattr(self, 'user_group'):
                await self.channel_layer.group_discard(self.user_group, self.channel_name)
            logger.info(f"Voice WebSocket disconnected with code {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        user_id = self.user.id if self.user and self.user.is_authenticated else "-"
        with log_context(chat_id=self.chat_id, user_id=user_id):
            # 1. Handle Binary Audio Chunks
            if bytes_data is not None:
                if self.state == "listening":
                    self.audio_chunks.append(bytes_data)
                return

            # 2. Handle Control Signals (JSON)
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
                return

            action = data.get("action")
            
            if action == "start_turn":
                # User started speaking (Client-side VAD)
                self.state = "listening"
                self.audio_chunks = []
                # Cancel current generation immediately (Interruption)
                if self.active_task and not self.active_task.done():
                    self.active_task.cancel()
                    logger.info("Generation interrupted by start_turn")
                await self.send(text_data=json.dumps({"status": "listening"}))

            elif action == "end_turn":
                # User finished speaking (Client-side VAD)
                if self.state == "listening" and self.audio_chunks:
                    self.state = "processing"
                    audio_bytes = b"".join(self.audio_chunks)
                    self.audio_chunks = []
                    
                    # Read parameters
                    model_preference = data.get("model_preference", "2")
                    voice_id = data.get("voice_id", "en_emma")
                    persona_id = data.get("persona_id", "aman")
                    preferred_language = data.get("preferred_language", "auto")
                    mime_type = data.get("mime_type", "audio/webm")
                    
                    # Decouple processing to prevent blocking consumer receive loop
                    self.active_task = asyncio.create_task(
                        self.process_voice_turn(audio_bytes, model_preference, voice_id, persona_id, preferred_language, mime_type)
                    )
                else:
                    self.state = "idle"
                    await self.send(text_data=json.dumps({"status": "idle"}))

            elif action == "interrupt":
                # User barged in during assistant speech playback
                if self.active_task and not self.active_task.done():
                    self.active_task.cancel()
                    logger.info("Generation task cancelled by user interrupt")
                
                # Truncate assistant response up to last played segment in DB
                ai_message_id = data.get("ai_message_id")
                last_played_text = data.get("last_played_text", "").strip()
                if ai_message_id and last_played_text:
                    truncated_text = f"{last_played_text}... [interrupted]"
                    await self.db_truncate_message(self.chat_id, ai_message_id, truncated_text)
                    
                    # Broadcast truncation to sync text chat interfaces
                    await self.channel_layer.group_send(
                        self.chat_group,
                        {
                            "type": "chat.message",
                            "payload": {
                                "replace_all": truncated_text,
                                "message_id": ai_message_id,
                                "done": True,
                                "interrupted": True
                            }
                        }
                    )
                
                if self.state != "listening":
                    self.state = "idle"
                    await self.send(text_data=json.dumps({"status": "idle"}))

    async def process_voice_turn(self, audio_bytes, model_preference, preferred_voice_id, persona_id, preferred_language="auto", mime_type="audio/webm"):
        user_id = str(self.user.id)
        chat_id_str = str(self.chat_id)
        user_msg_id = None
        ai_msg_id = None
        assistant_content = ""
        
        try:
            # Step 1: Transcribe user audio
            await self.send(text_data=json.dumps({"status": "transcribing"}))
            
            # Resolve suffix from mime_type
            ext = ".webm"
            if mime_type:
                if "mp4" in mime_type or "m4a" in mime_type:
                    ext = ".m4a"
                elif "ogg" in mime_type:
                    ext = ".ogg"
                elif "wav" in mime_type:
                    ext = ".wav"
                elif "mp3" in mime_type or "mpeg" in mime_type:
                    ext = ".mp3"
            
            whisper_prompt = (
                "The following is a transcript of a bilingual Arabic and English emotional wellness conversation: "
                "كيفك اليوم؟ شو أخبارك؟ I'm feeling a bit down, بس الحمد لله على كل حال. Can you help me?"
            )

            # Force the Whisper model to transcribe in a specific language if preferred, otherwise let it auto-detect
            whisper_lang = None
            if preferred_language == "ar":
                whisper_lang = "ar"
            elif preferred_language == "en":
                whisper_lang = "en"

            stt_res = await asyncio.to_thread(
                transcribe_audio,
                audio_bytes,
                filename=f"utterance{ext}",
                content_type=mime_type,
                language=whisper_lang,
                prompt=whisper_prompt
            )
            
            transcript = stt_res.get("text", "").strip()
            detected_lang = stt_res.get("language", "en")
            
            if not transcript:
                logger.warning("Empty transcription returned from Groq Whisper")
                await self.send(text_data=json.dumps({
                    "status": "idle",
                    "error": "Could not understand audio. Please try again."
                }))
                return
                
            # Send transcription back to client
            await self.send(text_data=json.dumps({
                "user_transcript": transcript,
                "detected_language": detected_lang
            }))
            
            # Step 2: Establish voice routing (fallback static configuration)
            voice = get_voice(preferred_voice_id) or resolve_voice_for_language(preferred_voice_id)
            logger.info(f"Preferred companion voice: {voice.id} ({voice.voice})")

            # Setup message IDs for DB tracking
            user_msg_id = str(uuid.uuid4())
            ai_msg_id = str(uuid.uuid4())
            
            await self.send(text_data=json.dumps({
                "status": "thinking",
                "ai_message_id": ai_msg_id
            }))
            
            # Step 3: Run LangGraph pipeline
            buffer = SentenceBuffer()
            assistant_content = ""
            
            async for payload in run_agent(
                user_id=user_id,
                chat_id=chat_id_str,
                user_message=transcript,
                model_preference=model_preference,
                mode="voice",
                ai_msg_id=ai_msg_id,
                user_msg_id=user_msg_id,
                persona_id=persona_id
            ):
                # run_agent can return chunks or replace_all blocks
                if isinstance(payload, dict):
                    chunk = payload.get("chunk", "")
                    if "replace_all" in payload:
                        chunk = payload["replace_all"]
                        assistant_content = chunk
                        buffer.buffer = chunk
                    elif "clear" in payload:
                        assistant_content = ""
                        buffer.buffer = ""
                else:
                    chunk = str(payload)
                    
                if chunk and not isinstance(payload, dict):
                    assistant_content += chunk
                    buffer.add_chunk(chunk)
                    
                # Stream sentences dynamically
                sentences = buffer.get_sentences()
                for sentence in sentences:
                    if sentence:
                        resolved_voice = resolve_voice_for_text(sentence, preferred_voice_id, persona_id)
                        await self.synthesize_and_stream_segment(sentence, resolved_voice, ai_msg_id)

            # Flush remaining tokens in buffer
            remaining_sentences = buffer.get_sentences(force_remaining=True)
            for sentence in remaining_sentences:
                if sentence:
                    resolved_voice = resolve_voice_for_text(sentence, preferred_voice_id, persona_id)
                    await self.synthesize_and_stream_segment(sentence, resolved_voice, ai_msg_id)

            # Send complete marker
            await self.send(text_data=json.dumps({
                "status": "idle",
                "done": True,
                "ai_message_id": ai_msg_id
            }))
            
            # Broadcast the complete message to update text-based chat group peers
            await self.channel_layer.group_send(
                self.chat_group,
                {
                    "type": "chat.message",
                    "payload": {
                        "user_message": {
                            "message_id": user_msg_id,
                            "role": "user",
                            "content": transcript
                        }
                    }
                }
            )
            await self.channel_layer.group_send(
                self.chat_group,
                {
                    "type": "chat.message",
                    "payload": {
                        "replace_all": assistant_content,
                        "message_id": ai_msg_id,
                        "done": True
                    }
                }
            )
            
        except asyncio.CancelledError:
            logger.info("Voice turn processing cancelled (interrupted)")
            if assistant_content and assistant_content.strip() and ai_msg_id:
                try:
                    from agent.memory.history import save_message, update_chat_modify_date
                    await asyncio.to_thread(
                        save_message,
                        self.chat_id,
                        role="assistant",
                        content=assistant_content.strip(),
                        safety_flag="SAFE",
                        message_id=ai_msg_id,
                        persona_id=persona_id
                    )
                    await asyncio.to_thread(update_chat_modify_date, self.chat_id)
                    logger.info(f"Saved partial assistant message {ai_msg_id} on cancellation: {assistant_content[:50]}...")
                except Exception as ex:
                    logger.error(f"Failed to save partial message on cancellation: {ex}")
            await self.send(text_data=json.dumps({"status": "idle", "interrupted": True}))
        except Exception as e:
            logger.error(f"Error processing voice turn: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                "status": "idle",
                "error": "Failed to process voice response."
            }))

    async def synthesize_and_stream_segment(self, text, voice, ai_msg_id):
        """Synthesizes text segment asynchronously and sends it as base64 segment."""
        try:
            audio_bytes = await synthesize_speech(text, voice)
            audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
            
            await self.send(text_data=json.dumps({
                "audio_segment": {
                    "text": text,
                    "audio_base64": audio_b64,
                    "format": "mp3",
                    "ai_message_id": ai_msg_id
                }
            }))
        except Exception as e:
            logger.error(f"Segment TTS failed for text '{text}': {e}")
            # Send text-only fallback segment so the UI can still display subtitles
            await self.send(text_data=json.dumps({
                "audio_segment": {
                    "text": text,
                    "audio_base64": "",
                    "format": "mp3",
                    "error": str(e),
                    "ai_message_id": ai_msg_id
                }
            }))

    @database_sync_to_async
    def check_chat_exists(self, chat_id, user):
        return Chat.objects.filter(chat_id=chat_id, user=user).exists()

    @database_sync_to_async
    def db_truncate_message(self, chat_id, message_id, text):
        try:
            msg = Message.objects.get(chat=chat_id, message_id=message_id)
            msg.content = text
            msg.save()
            logger.info(f"Truncated message {message_id} in database to: {text}")
        except Message.DoesNotExist:
            logger.warning(f"Could not find message {message_id} to truncate")
        except Exception as e:
            logger.error(f"Failed to update message database entry: {e}")

    async def chat_message(self, event):
        # Ignore text chat messages in voice consumer
        pass

    async def title_update(self, event):
        # Ignore title updates in voice consumer
        pass

    async def generation_status(self, event):
        # Ignore generation status in voice consumer
        pass

    async def chat_deleted(self, event):
        # Close voice session if the chat is deleted
        await self.close(code=4009)
