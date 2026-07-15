import { useState, useRef, useCallback, useEffect } from 'react';

const PREFERRED_MIME_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/wav',
];

function getSupportedMimeType() {
  if (typeof MediaRecorder === 'undefined') return '';
  for (const mime of PREFERRED_MIME_TYPES) {
    if (MediaRecorder.isTypeSupported(mime)) return mime;
  }
  return '';
}

export function useAudioRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [durationMs, setDurationMs] = useState(0);
  const [error, setError] = useState(null);

  const mediaRecorderRef = useRef(null);
  const streamRef = useRef(null);
  const timerRef = useRef(null);
  const startTimeRef = useRef(0);
  const chunksRef = useRef([]);

  const cleanUpStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => cleanUpStream();
  }, [cleanUpStream]);

  const startRecording = useCallback(async (onDataAvailable = null) => {
    setError(null);
    chunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const mimeType = getSupportedMimeType();
      const options = mimeType ? { mimeType } : {};
      const recorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunksRef.current.push(e.data);
          if (onDataAvailable) {
            onDataAvailable(e.data);
          }
        }
      };

      // Slice audio every 200ms for real-time streaming
      recorder.start(200);
      startTimeRef.current = Date.now();
      setDurationMs(0);
      
      timerRef.current = setInterval(() => {
        setDurationMs(Date.now() - startTimeRef.current);
      }, 100);

      setIsRecording(true);
      return recorder;
    } catch (err) {
      cleanUpStream();
      setError(err.message || 'Failed to access mic');
      throw err;
    }
  }, [cleanUpStream]);

  const stopRecording = useCallback(() => {
    return new Promise((resolve, reject) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === 'inactive') {
        setIsRecording(false);
        cleanUpStream();
        reject(new Error('Recorder is not active'));
        return;
      }

      recorder.onstop = () => {
        const mimeType = recorder.mimeType || 'audio/webm';
        const blob = new Blob(chunksRef.current, { type: mimeType });
        
        setIsRecording(false);
        setDurationMs(Date.now() - startTimeRef.current);
        cleanUpStream();
        
        mediaRecorderRef.current = null;
        chunksRef.current = [];
        resolve(blob);
      };

      recorder.onerror = (e) => {
        setIsRecording(false);
        cleanUpStream();
        reject(new Error('Audio recording error occurred'));
      };

      recorder.stop();
    });
  }, [cleanUpStream]);

  const cancelRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== 'inactive') {
      recorder.onstop = null;
      recorder.stop();
    }
    chunksRef.current = [];
    setIsRecording(false);
    cleanUpStream();
    mediaRecorderRef.current = null;
  }, [cleanUpStream]);

  return {
    isRecording,
    durationMs,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
    isSupported: typeof window !== 'undefined' && !!navigator.mediaDevices?.getUserMedia,
  };
}
