import { useRef, useCallback, useState, useEffect } from 'react';

function pickSupportedMimeType() {
  const candidates = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
    'audio/wav',
    ''
  ];
  if (typeof MediaRecorder === 'undefined') return '';
  return candidates.find(t => t === '' || MediaRecorder.isTypeSupported(t)) ?? '';
}

export function useAudioStreamer(chatId, token, options = {}) {
  const {
    modelPreference = '2',
    voiceId = 'en_emma',
    personaId = 'aman',
    preferredLanguage = 'auto',
    isMuted = false,
    onStateChange = null, // (state) => {}
    onTranscript = null,  // (text, role) => {}
    onSubtitles = null,   // (text) => {}
    onError = null,       // (err) => {}
  } = options;

  const [state, setState] = useState('idle'); // idle | listening | transcribing | thinking | speaking | muted
  const [subtitles, setSubtitles] = useState('');
  const [micVolume, setMicVolume] = useState(0);
  const [thresholdVolume, setThresholdVolume] = useState(40); // default fallback ~-50dB normalized
  const [micAnalyser, setMicAnalyser] = useState(null);
  const [playAnalyser, setPlayAnalyser] = useState(null);
  
  // Callback refs to prevent infinite re-render loops from inline callback definitions
  const onStateChangeRef = useRef(onStateChange);
  const onTranscriptRef = useRef(onTranscript);
  const onSubtitlesRef = useRef(onSubtitles);
  const onErrorRef = useRef(onError);

  // Keep refs up-to-date on every render
  useEffect(() => {
    onStateChangeRef.current = onStateChange;
    onTranscriptRef.current = onTranscript;
    onSubtitlesRef.current = onSubtitles;
    onErrorRef.current = onError;
  });

  // State refs to prevent stale closure bugs inside continuous VAD onaudioprocess loop
  const stateRef = useRef(state);
  const voiceIdRef = useRef(voiceId);
  const personaIdRef = useRef(personaId);
  const modelPreferenceRef = useRef(modelPreference);
  const isMutedRef = useRef(isMuted);
  const preferredLanguageRef = useRef(preferredLanguage);

  useEffect(() => {
    stateRef.current = state;
    voiceIdRef.current = voiceId;
    personaIdRef.current = personaId;
    modelPreferenceRef.current = modelPreference;
    isMutedRef.current = isMuted;
    preferredLanguageRef.current = preferredLanguage;
  }, [state, voiceId, personaId, modelPreference, isMuted, preferredLanguage]);

  const wsRef = useRef(null);
  const audioCtxRef = useRef(null);
  const vadNodeRef = useRef(null);
  const micStreamRef = useRef(null);
  const voiceFilterRef = useRef(null);
  
  // Playback Queue State
  const playbackQueueRef = useRef([]); // Items: { text, audioBuffer, aiMessageId }
  const activeSourceRef = useRef(null);
  const isPlayingRef = useRef(false);
  const currentSentenceRef = useRef('');
  const lastPlayedSentenceRef = useRef('');
  const playAnalyserRef = useRef(null);

  // Active AI response tracking for truncation on interrupt
  const currentAiMessageIdRef = useRef(null);

  // VAD Threshold parameters
  const noiseSamplesRef = useRef([]);
  const adaptiveThresholdRef = useRef(-52);
  const SILENCE_DURATION = 1500; // ms of continuous silence before turn ends
  const isUserSpeakingRef = useRef(false);
  const silenceTimerRef = useRef(null);
  
  // Speech Debouncing & Lockout parameters
  const speechSamplesCountRef = useRef(0);
  const DEBOUNCE_SAMPLES = 4; // requires ~180ms of continuous voice crossing threshold (4 * 46ms)
  
  // MediaRecorder session state
  const mediaRecorderRef = useRef(null);

  // Helper: Get or create AudioContext
  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtxRef.current.state === 'suspended') {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }, []);

  // Helper: Base64 to ArrayBuffer
  const base64ToArrayBuffer = useCallback((base64) => {
    const binary = window.atob(base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    return bytes.buffer;
  }, []);

  // Helper: Stop assistant audio playback immediately
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
    playAnalyserRef.current = null;
    setPlayAnalyser(null);
    if (onSubtitlesRef.current) onSubtitlesRef.current('');
  }, []);

  // Interrupt if companion configuration changes mid-turn
  useEffect(() => {
    const current = stateRef.current;
    if (current === 'thinking' || current === 'speaking' || current === 'transcribing') {
      console.log("Companion or model config changed during active turn, interrupting...");
      stopPlayback();
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          action: 'interrupt',
          ai_message_id: currentAiMessageIdRef.current,
          last_played_text: lastPlayedSentenceRef.current
        }));
      }
      setState('idle');
      if (onStateChangeRef.current) onStateChangeRef.current('idle');
    }
  }, [voiceId, personaId, modelPreference, preferredLanguage, stopPlayback]);

  // Queue-based Audio Player
  const playNextInQueue = useCallback(() => {
    if (playbackQueueRef.current.length === 0) {
      isPlayingRef.current = false;
      currentSentenceRef.current = '';
      setSubtitles('');
      playAnalyserRef.current = null;
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
    
    let analyser = playAnalyserRef.current;
    if (!analyser) {
      analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.connect(ctx.destination);
      playAnalyserRef.current = analyser;
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
  }, [getAudioContext]);

  // Push received base64 audio segment to queue
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
      if (onErrorRef.current) onErrorRef.current('Failed to decode audio segment: ' + e.message);
    }
  }, [getAudioContext, base64ToArrayBuffer, playNextInQueue]);

  // Recorder session controller (Isolated variables per instance to avoid stop/start races)
  const startRecordingSession = useCallback(() => {
    if (!micStreamRef.current) return;

    // Disconnect old handlers and stop previous instance
    const prev = mediaRecorderRef.current;
    if (prev && prev.state !== 'inactive') {
      prev.ondataavailable = null;
      prev.onstop = null;
      try {
        prev.stop();
      } catch (e) {}
    }

    try {
      const localChunks = [];
      const mimeType = pickSupportedMimeType();
      const options = mimeType ? { mimeType } : {};
      const recorder = new MediaRecorder(micStreamRef.current, options);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          localChunks.push(e.data);
        }
      };

      recorder.onstop = () => {
        const audioBlob = new Blob(localChunks, { type: recorder.mimeType || 'audio/webm' });
        
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          if (audioBlob.size > 100) {
            console.log("Sending complete voice turn blob | size:", audioBlob.size, "mime:", audioBlob.type);
            wsRef.current.send(audioBlob);
          } else {
            console.warn("Discarding small voice blob | size:", audioBlob.size);
          }
          
          // Send end_turn message synchronously after the binary blob is sent to avoid server-side timing races
          wsRef.current.send(JSON.stringify({
            action: 'end_turn',
            model_preference: modelPreferenceRef.current,
            voice_id: voiceIdRef.current,
            persona_id: personaIdRef.current,
            preferred_language: preferredLanguageRef.current,
            mime_type: recorder.mimeType || 'audio/webm'
          }));
        }
      };

      recorder.start(100);
      console.log("Started fresh MediaRecorder session | mime:", mimeType);
    } catch (e) {
      console.error("Failed to start MediaRecorder session:", e);
    }
  }, []);

  const stopRecordingSession = useCallback((shouldSend = true) => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      if (!shouldSend) {
        recorder.onstop = null;
        recorder.ondataavailable = null;
      }
      try {
        recorder.stop();
      } catch (e) {}
    }
  }, []);

  // VAD Processing logic (Runs continuously on the mic track)
  const handleVADProcess = useCallback((e) => {
    const input = e.inputBuffer.getChannelData(0);
    let sum = 0;
    for (let i = 0; i < input.length; i++) {
      sum += input[i] * input[i];
    }
    const rms = Math.sqrt(sum / input.length);
    const db = 20 * Math.log10(rms || 0.00001);

    // Normalize live decibels to 0-100 percentage bar
    const volumePercent = Math.round(Math.max(0, Math.min(100, ((db + 85) / 85) * 100)));
    
    // Check stateRef to prevent stale closure lockup bugs
    const currentState = stateRef.current;
    if (isMutedRef.current || currentState === 'thinking' || currentState === 'transcribing') {
      speechSamplesCountRef.current = 0;
      setMicVolume(0);
      return;
    }

    setMicVolume(volumePercent);

    // Calibrate adaptive ambient noise floor for the first 35 samples (~1.5 seconds)
    if (noiseSamplesRef.current.length < 35) {
      noiseSamplesRef.current.push(db);
      const avg = noiseSamplesRef.current.reduce((a, b) => a + b, 0) / noiseSamplesRef.current.length;
      
      // Set initial threshold 10 dB above average noise floor (clamping -52dB to -30dB)
      adaptiveThresholdRef.current = Math.min(Math.max(avg + 10, -52), -30);
      
      const thresholdPercent = Math.round(Math.max(0, Math.min(100, ((adaptiveThresholdRef.current + 85) / 85) * 100)));
      setThresholdVolume(thresholdPercent);
      return;
    }

    // Continuous adaptation of ambient noise floor when not speaking:
    if (!isUserSpeakingRef.current && db < adaptiveThresholdRef.current) {
      const alpha = 0.02; // slow drift adaptation
      const currentAmbient = adaptiveThresholdRef.current - 10;
      const newAmbient = currentAmbient * (1 - alpha) + db * alpha;
      
      adaptiveThresholdRef.current = Math.min(Math.max(newAmbient + 10, -52), -30);
      
      const thresholdPercent = Math.round(Math.max(0, Math.min(100, ((adaptiveThresholdRef.current + 85) / 85) * 100)));
      setThresholdVolume(thresholdPercent);
    }

    // Suppress acoustic feedback: raise VAD threshold by 10 dB during assistant speech playback
    const activeThreshold = currentState === 'speaking' 
      ? Math.min(adaptiveThresholdRef.current + 10, -26) 
      : adaptiveThresholdRef.current;

    const isSpeaking = db > activeThreshold;

    if (isSpeaking) {
      speechSamplesCountRef.current += 1;

      if (silenceTimerRef.current) {
        clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = null;
      }

      // Suppress false interrupts during active playback: require longer duration (7 samples, ~320ms) vs normal (4 samples, ~180ms)
      const requiredDebounce = currentState === 'speaking' ? 7 : 4;
      if (speechSamplesCountRef.current >= requiredDebounce && !isUserSpeakingRef.current) {
        isUserSpeakingRef.current = true;
        
        // Interrupt ongoing assistant speech immediately
        stopPlayback();

        // Notify server that user has interrupted
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({
            action: 'start_turn'
          }));
          
          // Only send interrupt action to backend if assistant was actively speaking
          if (isPlayingRef.current) {
            wsRef.current.send(JSON.stringify({
              action: 'interrupt',
              ai_message_id: currentAiMessageIdRef.current,
              last_played_text: lastPlayedSentenceRef.current
            }));
          }
        }

        // Restart recording session to capture fresh clean user speech
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

          // Stop recorder session and flush to WebSocket (end_turn is sent in onstop callback)
          stopRecordingSession(true);
        }, SILENCE_DURATION);
      }
    }
  }, [SILENCE_DURATION, stopPlayback, startRecordingSession, stopRecordingSession]);

  // Start Mic & VAD (called once on socket open, kept alive)
  const startMicVAD = useCallback(async () => {
    if (micStreamRef.current) return; // Already active

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
      
      // Mic AnalyserNode
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      setMicAnalyser(analyser);

      // Vocal Bandpass Filter (300Hz - 3000Hz) to reject AC rumble and keyboard clicks
      const voiceFilter = ctx.createBiquadFilter();
      voiceFilter.type = 'bandpass';
      voiceFilter.frequency.value = 1200; // Center frequency in Hz (vocal range)
      voiceFilter.Q.value = 0.55; // Captures roughly 300Hz to 3500Hz
      source.connect(voiceFilter);
      voiceFilterRef.current = voiceFilter;

      // VAD Node (connect to filter instead of direct mic source)
      const vadNode = ctx.createScriptProcessor(2048, 1, 1);
      vadNode.onaudioprocess = handleVADProcess;
      voiceFilter.connect(vadNode);
      vadNode.connect(ctx.destination);
      vadNodeRef.current = vadNode;

      startRecordingSession();
    } catch (e) {
      console.error('Failed to configure VAD microphone:', e);
      if (onErrorRef.current) onErrorRef.current('Microphone access or VAD setup failed: ' + e.message);
    }
  }, [getAudioContext, handleVADProcess, startRecordingSession]);

  // Clean up Mic & VAD
  const stopMicVAD = useCallback(() => {
    if (vadNodeRef.current) {
      try {
        vadNodeRef.current.disconnect();
        vadNodeRef.current.onaudioprocess = null;
      } catch (e) {}
      vadNodeRef.current = null;
    }

    if (voiceFilterRef.current) {
      try {
        voiceFilterRef.current.disconnect();
      } catch (e) {}
      voiceFilterRef.current = null;
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

  // Monitor state transitions to restart recording for subsequent turns
  useEffect(() => {
    if (state === 'idle' && micStreamRef.current && !isMutedRef.current) {
      startRecordingSession();
    }
  }, [state, startRecordingSession]);

  // Monitor mute transitions to dynamically halt/resume recording sessions
  useEffect(() => {
    if (isMuted) {
      stopRecordingSession(false);
    } else {
      if (stateRef.current === 'idle' && micStreamRef.current) {
        startRecordingSession();
      }
    }
  }, [isMuted, stopRecordingSession, startRecordingSession]);

  // WebSocket Connection Lifecycle
  const connectWebSocket = useCallback(() => {
    if (!chatId || chatId === 'new') return;

    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch (e) {}
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host; // Connect via Vite's proxy directly
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
          
          // Track message ID during thinking state for truncation purposes
          if (nextState === 'thinking' && data.ai_message_id) {
            currentAiMessageIdRef.current = data.ai_message_id;
          }
        }

        if (data.user_transcript) {
          if (onTranscriptRef.current) onTranscriptRef.current(data.user_transcript, 'user');
        }

        if (data.audio_segment) {
          const seg = data.audio_segment;
          // Discard late segments if we have returned to idle/listening or if the message ID mismatches
          const currentState = stateRef.current;
          if (currentState === 'idle' || currentState === 'listening' || seg.ai_message_id !== currentAiMessageIdRef.current) {
            console.log("Discarding late audio segment for message:", seg.ai_message_id);
            return;
          }
          if (onTranscriptRef.current) onTranscriptRef.current(seg.text, 'assistant');
          await enqueueSegment(seg.text, seg.audio_base64, seg.ai_message_id);
        }

        if (data.error) {
          console.error('Server Voice Error:', data.error);
          if (onErrorRef.current) onErrorRef.current(data.error);
        }
      } catch (e) {
        console.error('Error handling voice websocket message:', e);
      }
    };

    ws.onerror = (e) => {
      console.error('Voice WebSocket encountered error:', e);
      if (onErrorRef.current) onErrorRef.current('Voice WebSocket connection error.');
    };

    ws.onclose = (e) => {
      console.log('Voice WebSocket closed:', e.code, e.reason);
      stopMicVAD();
      stopPlayback();
      setState('idle');
      if (onStateChangeRef.current) onStateChangeRef.current('idle');
      
      // Notify client of auth/connection close frames
      if (e.code === 4003) {
        if (onErrorRef.current) onErrorRef.current('Authentication failed. Please log in again.');
      } else if (e.code === 4004) {
        if (onErrorRef.current) onErrorRef.current('Chat session not found.');
      } else if (e.code !== 1000 && e.code !== 1001 && e.code !== 1005) {
        if (onErrorRef.current) onErrorRef.current('Voice server connection lost.');
      }
    };
  }, [chatId, token, startMicVAD, stopMicVAD, stopPlayback, enqueueSegment]);

  // Initialize and clean up WebSockets
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
      stopMicVAD();
      stopPlayback();
    };
  }, [chatId, token, connectWebSocket, stopMicVAD, stopPlayback]);

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
