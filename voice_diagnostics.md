# Project Context & Voice Mode Diagnostics for Claude Web

> **To Claude Web:** 
> You are helping debug a hands-free Voice Mode feature inside a mental wellness web application named **Aman**. Below is the complete description of the project stack, architecture, and core codebase files. Please review this context and help troubleshoot why the voice mode is not working as expected (e.g. failing to connect, staying silent, or crashing).

---

## 1. Project Stack & Architecture Overview

The system is a real-time, bilingual (Arabic & English) voice wellness companion. It operates as follows:

```
[User Mic] ➔ VAD (Web Audio API) ➔ MediaRecorder (Turn-by-turn WebM) ➔ WebSocket
                                                                         │
[User Speaker] ⇠ edge-tts (MP3 Segments) ⇠ LangGraph LLM Pipeline ⇠ Groq Whisper STT
```

### A. The Backend (Django Channels & ASGI)
* **WebSocket Server**: Django Channels running via Daphne on port `8000` (`/ws/voice/{chat_id}/?token=...`).
* **STT**: User voice audio bytes (WebM format) are received over the socket, accumulated on the consumer, and transcribed using **Groq Whisper** (`whisper-large-v3`).
* **LLM Pipeline**: The transcription is fed into a LangGraph pipeline which generates a response streaming tokens.
* **TTS**: Tokens are gathered into sentences. As each sentence is completed, it is synthesized in real-time to MP3 bytes using `edge-tts`. The MP3 bytes are base64-encoded and streamed down to the client over the WebSocket as `audio_segment` frames.

### B. The Frontend (Vite + React)
* **API Connection**: Vite acts as a local proxy (`vite.config.js`), forwarding WebSocket connections at `/ws` to `ws://127.0.0.1:8000/ws`.
* **Microphone VAD**: Captures microphone stream via `navigator.mediaDevices.getUserMedia`. An `AudioContext` and `ScriptProcessorNode` analyze the input volume in decibels.
* **Turn-by-Turn MediaRecorder**:
  - The client initializes a `MediaRecorder` at the start of each user turn (`state === 'idle'`).
  - When the user starts speaking (VAD volume crosses the threshold for at least 180ms), the system stops assistant playback, sends an `interrupt` signal to the backend, and listens.
  - When the user stops speaking (silence detected for 950ms), the client stops the `MediaRecorder`, grabs the completed turn `Blob`, sends it over the WebSocket as a binary frame, and sends `"end_turn"` to trigger the server-side transcription and generation.
* **Visualizer Orb**: A custom `<canvas>` component renders a fluid liquid morphing orb. It changes colors according to state (`listening`, `speaking`, `thinking`) and adjusts its wave amplitude based on `micAnalyser` and `playAnalyser` frequency data.

---

## 2. Core Frontend Code: `useAudioStreamer.js`

Here is the current implementation of the React hook that manages the voice WebSocket, VAD node, and audio playback:

```javascript
// Frontend/src/hooks/useAudioStreamer.js
import { useRef, useCallback, useState, useEffect } from 'react';

export function useAudioStreamer(chatId, token, options = {}) {
  const {
    modelPreference = '2',
    voiceId = 'en_emma',
    personaId = 'aman',
    onStateChange = null,
    onTranscript = null,
    onSubtitles = null,
    onError = null,
  } = options;

  const [state, setState] = useState('idle'); // idle | listening | transcribing | thinking | speaking | muted
  const [subtitles, setSubtitles] = useState('');
  const [micVolume, setMicVolume] = useState(0);
  const [thresholdVolume, setThresholdVolume] = useState(40);
  const [micAnalyser, setMicAnalyser] = useState(null);
  const [playAnalyser, setPlayAnalyser] = useState(null);
  
  const onStateChangeRef = useRef(onStateChange);
  const onTranscriptRef = useRef(onTranscript);
  const onSubtitlesRef = useRef(onSubtitles);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onStateChangeRef.current = onStateChange;
    onTranscriptRef.current = onTranscript;
    onSubtitlesRef.current = onSubtitles;
    onErrorRef.current = onError;
  });

  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const vadNodeRef = useRef(null);
  const micStreamRef = useRef(null);
  
  const playbackQueueRef = useRef([]); 
  const activeSourceRef = useRef(null);
  const isPlayingRef = useRef(false);
  const currentSentenceRef = useRef('');
  const lastPlayedSentenceRef = useRef('');

  const noiseSamplesRef = useRef([]);
  const adaptiveThresholdRef = useRef(-48);
  const SILENCE_DURATION = 950; 
  const isUserSpeakingRef = useRef(false);
  const silenceTimerRef = useRef(null);
  
  const speechSamplesCountRef = useRef(0);
  const DEBOUNCE_SAMPLES = 4; // ~180ms
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtxRef.current.state === 'suspended') {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }, []);

  const base64ToArrayBuffer = useCallback((base64) => {
    const binary = window.atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }, []);

  const stopPlayback = useCallback(() => {
    if (activeSourceRef.current) {
      try {
        activeSourceRef.current.stop();
      } catch (e) {}
      activeSourceRef.current = null;
    }
    playbackQueueRef.current = [];
    isPlayingRef.current = false;
    currentSentenceRef.current = '';
    setSubtitles('');
    setPlayAnalyser(null);
    if (onSubtitlesRef.current) onSubtitlesRef.current('');
  }, []);

  const playNextInQueue = useCallback(() => {
    if (playbackQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      currentSentenceRef.current = '';
      setSubtitles('');
      setPlayAnalyser(null);
      if (onSubtitlesRef.current) onSubtitlesRef.current('');
      
      setState((prev) => {
        const nextState = prev === 'speaking' ? 'idle' : prev;
        if (onStateChangeRef.current) onStateChangeRef.current(nextState);
        return nextState;
      });
      return;
    }

    const ctx = getAudioContext();
    const item = playbackQueueRef.current.shift();
    
    let analyser = playAnalyser;
    if (!analyser) {
      analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.connect(ctx.destination);
      setPlayAnalyser(analyser);
    }

    const source = ctx.createBufferSource();
    source.buffer = item.audioBuffer;
    source.connect(analyser);

    activeSourceRef.current = source;
    isPlayingRef.current = true;
    currentSentenceRef.current = item.text;
    setSubtitles(item.text);
    if (onSubtitlesRef.current) onSubtitlesRef.current(item.text);

    setState('speaking');
    if (onStateChangeRef.current) onStateChangeRef.current('speaking');

    source.onended = () => {
      if (activeSourceRef.current === source) {
        lastPlayedSentenceRef.current = item.text;
        activeSourceRef.current = null;
        playNextInQueue();
      }
    };

    source.start(0);
  }, [getAudioContext, playAnalyser]);

  const enqueueSegment = useCallback(async (text, base64Audio, aiMessageId) => {
    if (!base64Audio) return;
    try {
      const ctx = getAudioContext();
      const arrayBuf = base64ToArrayBuffer(base64Audio);
      const audioBuffer = await ctx.decodeAudioData(arrayBuf);
      playbackQueueRef.current.push({ text, audioBuffer, aiMessageId });
      if (!isPlayingRef.current) {
        playNextInQueue();
      }
    } catch (e) {
      console.error('Failed to decode segment audio data:', e);
    }
  }, [getAudioContext, base64ToArrayBuffer, playNextInQueue]);

  const startRecordingSession = useCallback(() => {
    if (!micStreamRef.current) return;

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
    }

    try {
      audioChunksRef.current = [];
      const options = { mimeType: 'audio/webm;codecs=opus' };
      const recorder = new MediaRecorder(micStreamRef.current, options);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm;codecs=opus' });
        audioChunksRef.current = [];

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && audioBlob.size > 500) {
          console.log("Sending complete voice turn blob | size:", audioBlob.size);
          wsRef.current.send(audioBlob);
        }
      };

      recorder.start(100);
      console.log("Started fresh MediaRecorder session");
    } catch (e) {
      console.error("Failed to start MediaRecorder session:", e);
    }
  }, []);

  const stopRecordingSession = useCallback((shouldSend = true) => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      if (!shouldSend) {
        mediaRecorderRef.current.onstop = null;
      }
      try {
        mediaRecorderRef.current.stop();
      } catch (e) {}
    }
  }, []);

  const handleVADProcess = useCallback((e) => {
    const input = e.inputBuffer.getChannelData(0);
    let sum = 0;
    for (let i = 0; i < input.length; i++) {
      sum += input[i] * input[i];
    }
    const rms = Math.sqrt(sum / input.length);
    const db = 20 * Math.log10(rms || 0.00001);
    const volumePercent = Math.round(Math.max(0, Math.min(100, ((db + 85) / 85) * 100)));
    
    if (state === 'thinking' || state === 'transcribing') {
      speechSamplesCountRef.current = 0;
      setMicVolume(0);
      return;
    }

    setMicVolume(volumePercent);

    if (noiseSamplesRef.current.length < 35) {
      noiseSamplesRef.current.push(db);
      const avg = noiseSamplesRef.current.reduce((a, b) => a + b, 0) / noiseSamplesRef.current.length;
      adaptiveThresholdRef.current = Math.min(Math.max(avg + 11, -52), -32);
      const thresholdPercent = Math.round(Math.max(0, Math.min(100, ((adaptiveThresholdRef.current + 85) / 85) * 100)));
      setThresholdVolume(thresholdPercent);
      return;
    }

    const activeThreshold = state === 'speaking' 
      ? Math.min(adaptiveThresholdRef.current + 7, -30) 
      : adaptiveThresholdRef.current;

    const isSpeaking = db > activeThreshold;

    if (isSpeaking) {
      speechSamplesCountRef.current += 1;

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      if (speechSamplesCountRef.current >= DEBOUNCE_SAMPLES && !isUserSpeakingRef.current) {
        isUserSpeakingRef.current = true;
        stopPlayback();

        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ action: 'start_turn' }));
          wsRef.current.send(JSON.stringify({
            action: 'interrupt',
            last_played_text: lastPlayedSentenceRef.current
          }));
        }

        startRecordingSession();
        setState('listening');
        if (onStateChangeRef.current) onStateChangeRef.current('listening');
      }
    } else {
      speechSamplesCountRef.current = 0;

      if (isUserSpeakingRef.current && !silenceTimerRef.current) {
        silenceTimerRef.current = setTimeout(() => {
          isUserSpeakingRef.current = false;
          silenceTimerRef.current = null;
          
          setState('thinking');
          if (onStateChangeRef.current) onStateChangeRef.current('thinking');

          stopRecordingSession(true);

          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({
              action: 'end_turn',
              model_preference: modelPreference,
              voice_id: voiceId,
              persona_id: personaId
            }));
          }
        }, SILENCE_DURATION);
      }
    }
  }, [state, SILENCE_DURATION, stopPlayback, modelPreference, voiceId, personaId, startRecordingSession, stopRecordingSession]);

  const startMicVAD = useCallback(async () => {
    if (micStreamRef.current) return;

    try {
      const ctx = getAudioContext();
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      micStreamRef.current = stream;

      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      setMicAnalyser(analyser);

      const vadNode = ctx.createScriptProcessor(2048, 1, 1);
      vadNode.onaudioprocess = handleVADProcess;
      source.connect(vadNode);
      vadNode.connect(ctx.destination);
      vadNodeRef.current = vadNode;

      startRecordingSession();
    } catch (e) {
      console.error('Failed to configure VAD microphone:', e);
    }
  }, [getAudioContext, handleVADProcess, startRecordingSession]);

  const stopMicVAD = useCallback(() => {
    if (vadNodeRef.current) {
      try {
        vadNodeRef.current.disconnect();
        vadNodeRef.current.onaudioprocess = null;
      } catch (e) {}
      vadNodeRef.current = null;
    }
    
    stopRecordingSession(false);

    if (micStreamRef.current) {
      try {
        micStreamRef.current.getTracks().forEach((track) => track.stop());
      } catch (e) {}
      micStreamRef.current = null;
    }
    
    isUserSpeakingRef.current = false;
    speechSamplesCountRef.current = 0;
    noiseSamplesRef.current = [];
    setMicVolume(0);
    setMicAnalyser(null);
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, [stopRecordingSession]);

  useEffect(() => {
    if (state === 'idle' && micStreamRef.current) {
      startRecordingSession();
    }
  }, [state, startRecordingSession]);

  const connectWebSocket = useCallback(() => {
    if (!chatId || chatId === 'new') return;

    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {}
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const url = `${protocol}//${host}/ws/voice/${chatId}/?token=${encodeURIComponent(token)}`;
    console.log("Opening Voice WebSocket connection:", url);
    
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Voice WebSocket connected');
      startMicVAD();
      setState('idle');
      if (onStateChangeRef.current) onStateChangeRef.current('idle');
    };

    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.status) {
          const nextState = data.status;
          setState(nextState);
          if (onStateChangeRef.current) onStateChangeRef.current(nextState);
        }

        if (data.user_transcript) {
          if (onTranscriptRef.current) onTranscriptRef.current(data.user_transcript, 'user');
        }

        if (data.audio_segment) {
          const seg = data.audio_segment;
          if (onTranscriptRef.current) onTranscriptRef.current(seg.text, 'assistant');
          await enqueueSegment(seg.text, seg.audio_base64, seg.ai_message_id);
        }

        if (data.error) {
          console.error('Server Voice Error:', data.error);
        }
      } catch (e) {
        console.error('Error handling voice websocket message:', e);
      }
    };

    ws.onerror = (e) => {
      console.error('Voice WebSocket encountered error:', e);
    };

    ws.onclose = (e) => {
      console.log('Voice WebSocket closed:', e.code, e.reason);
      stopMicVAD();
      stopPlayback();
      setState('idle');
      if (onStateChangeRef.current) onStateChangeRef.current('idle');
    };
  }, [chatId, token, startMicVAD, stopMicVAD, stopPlayback, enqueueSegment]);

  useEffect(() => {
    if (chatId && chatId !== 'new' && token) {
      connectWebSocket();
    }
    return () => {
      if (wsRef.current) {
        try {
          wsRef.current.close();
        } catch (e) {}
      }
    };
  }, [chatId, token, connectWebSocket]);

  return {
    state,
    subtitles,
    micVolume,
    thresholdVolume,
    micAnalyser,
    playAnalyser,
    stopPlayback,
    reconnect: connectWebSocket,
    isRecording: isUserSpeakingRef.current
  };
}
```

---

## 3. Core Backend Code: `voice_consumer.py`

Here is the Django Channels WebSocket consumer that processes the binary frames and streams sentences/voices:

```python
# Backend/chats/voice_consumer.py
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
from agent.voice.voices import resolve_voice_for_language, get_voice

logger = logging.getLogger(__name__)

class SentenceBuffer:
    def __init__(self, min_length=45):
        self.buffer = ""
        self.min_length = min_length
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
        self.state = "idle"

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
            if bytes_data is not None:
                if self.state == "listening":
                    self.audio_chunks.append(bytes_data)
                return

            try:
                data = json.loads(text_data)
            except json.JSONDecodeError:
                await self.send(text_data=json.dumps({"error": "Invalid JSON"}))
                return

            action = data.get("action")
            
            if action == "start_turn":
                self.state = "listening"
                self.audio_chunks = []
                if self.active_task and not self.active_task.done():
                    self.active_task.cancel()
                await self.send(text_data=json.dumps({"status": "listening"}))

            elif action == "end_turn":
                if self.state == "listening" and self.audio_chunks:
                    self.state = "processing"
                    audio_bytes = b"".join(self.audio_chunks)
                    self.audio_chunks = []
                    
                    model_preference = data.get("model_preference", "2")
                    voice_id = data.get("voice_id", "en_emma")
                    persona_id = data.get("persona_id", "aman")
                    
                    self.active_task = asyncio.create_task(
                        self.process_voice_turn(audio_bytes, model_preference, voice_id, persona_id)
                    )
                else:
                    self.state = "idle"
                    await self.send(text_data=json.dumps({"status": "idle"}))

            elif action == "interrupt":
                if self.active_task and not self.active_task.done():
                    self.active_task.cancel()
                
                ai_message_id = data.get("ai_message_id")
                last_played_text = data.get("last_played_text", "").strip()
                if ai_message_id and last_played_text:
                    truncated_text = f"{last_played_text}... [interrupted]"
                    await self.db_truncate_message(self.chat_id, ai_message_id, truncated_text)
                    
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
                
                self.state = "idle"
                await self.send(text_data=json.dumps({"status": "idle"}))

    async def process_voice_turn(self, audio_bytes, model_preference, preferred_voice_id, persona_id):
        user_id = str(self.user.id)
        chat_id_str = str(self.chat_id)
        
        try:
            await self.send(text_data=json.dumps({"status": "transcribing"}))
            
            stt_res = await asyncio.to_thread(
                transcribe_audio,
                audio_bytes,
                filename="utterance.webm",
                content_type="audio/webm"
            )
            
            transcript = stt_res.get("text", "").strip()
            detected_lang = stt_res.get("language", "en")
            
            if not transcript:
                await self.send(text_data=json.dumps({
                    "status": "idle",
                    "error": "Could not understand audio. Please try again."
                }))
                return
                
            await self.send(text_data=json.dumps({
                "user_transcript": transcript,
                "detected_language": detected_lang
            }))
            
            voice = resolve_voice_for_language(preferred_voice_id, detected_language=detected_lang)

            user_msg_id = str(uuid.uuid4())
            ai_msg_id = str(uuid.uuid4())
            
            await self.send(text_data=json.dumps({
                "status": "thinking",
                "ai_message_id": ai_msg_id
            }))
            
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
                    
                sentences = buffer.get_sentences()
                for sentence in sentences:
                    if sentence:
                        await self.synthesize_and_stream_segment(sentence, voice, ai_msg_id)

            remaining_sentences = buffer.get_sentences(force_remaining=True)
            for sentence in remaining_sentences:
                if sentence:
                    await self.synthesize_and_stream_segment(sentence, voice, ai_msg_id)

            await self.send(text_data=json.dumps({
                "status": "idle",
                "done": True,
                "ai_message_id": ai_msg_id
            }))
            
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
            await self.send(text_data=json.dumps({"status": "idle", "interrupted": True}))
        except Exception as e:
            logger.error(f"Error processing voice turn: {e}", exc_info=True)
            await self.send(text_data=json.dumps({
                "status": "idle",
                "error": "Failed to process voice response."
            }))

    async def synthesize_and_stream_segment(self, text, voice, ai_msg_id):
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
        except Message.DoesNotExist:
            pass
```

---

## 4. Prompt for Claude Web

Please ask Claude the following question:

```
"I am building a hands-free Voice companion. The frontend is built with React and Vite. It establishes a WebSocket connection to a Django Channels ASGI consumer running via Daphne. 

Currently, when I start the voice call, it does not work. When I speak, it either does not record or fails to transcribe and reply.

Review the code for 'useAudioStreamer.js' and 'voice_consumer.py' provided above. Identify potential bugs, edge cases, or mismatches:
1. Are there issues with browser MediaRecorder MIME types (e.g. 'audio/webm;codecs=opus') when uploading to Groq Whisper?
2. Does the turn-by-turn MediaRecorder start/stop timing look solid? Could recorder.stop() and ws.send(blob) fail to send or get swallowed due to state changes?
3. How should the websocket URL resolve correctly (Vite proxy vs direct port 8000)?
4. Suggest a step-by-step fix to ensure the browser successfully records, transmits, and the backend transcribes."
```
