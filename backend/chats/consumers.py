import json, logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from agent.runner import run_agent
from chats.models import Chat

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]

        if isinstance(self.user, AnonymousUser):
            await self.close(code=4003)
            return

        chat_exists = await self.check_chat_exists(self.chat_id, self.user)
        if not chat_exists:
            await self.close(code=4004)
            return

        await self.accept()
        logger.info(f"WebSocket connected for chat {self.chat_id}")

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected with code {close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
            return

        message = data.get("message", "").strip()
        model_preference = data.get("model_preference", "2")
        mode = data.get("mode", "normal")

        audio_input = data.get("audio_input")
        
        if audio_input:
            try:
                from agent.voice.stt import transcribe_audio
                message = await transcribe_audio(audio_input)
                if not message:
                    await self.send(text_data=json.dumps({"error": "Could not hear any speech. Please try again."}))
                    return
                # Tell the client what they said so it shows in the UI
                await self.send(text_data=json.dumps({"user_message_echo": message}))
            except Exception as e:
                logger.error(f"STT Error: {e}")
                await self.send(text_data=json.dumps({"error": "Speech to text transcription failed."}))
                return
        else:
            if not message:
                await self.send(text_data=json.dumps({"error": "Empty message"}))
                return

        try:
            # Yield chunks or signals back to client
            async for payload in run_agent(str(self.user.id), self.chat_id, message, model_preference, mode):
                if isinstance(payload, dict):
                    await self.send(text_data=json.dumps(payload))
                else:
                    await self.send(text_data=json.dumps({"chunk": payload}))
            
            # Send completion signal
            await self.send(text_data=json.dumps({"done": True}))
        except Exception as e:
            logger.error(f"Error in consumer: {e}")
            await self.send(text_data=json.dumps({"error": "An error occurred while generating the response."}))

    @database_sync_to_async
    def check_chat_exists(self, chat_id, user):
        return Chat.objects.filter(chat_id=chat_id, user=user).exists()
