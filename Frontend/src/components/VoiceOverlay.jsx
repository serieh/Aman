import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  PhoneOff, 
  Mic, 
  MicOff, 
  X, 
  ChevronDown, 
  Brain, 
  Zap 
} from 'lucide-react';
import { useVoiceStore } from '../store/useVoiceStore';
import { useChatStore } from '../store/useChatStore';
import { useAudioStreamer } from '../hooks/useAudioStreamer';
import VoiceOrb from './VoiceOrb';

export default function VoiceOverlay() {
  const { 
    voiceId, 
    modelPreference, 
    personaId, 
    preferredLanguage,
    setVoiceId, 
    setModelPreference, 
    setPersonaId, 
    setPreferredLanguage,
    setIsOpen 
  } = useVoiceStore();

  const [isMuted, setIsMuted] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(null);
  const [isVisible, setIsVisible] = useState(false); // local visibility for transition animations
  const navigate = useNavigate();

  // Get active chat details
  const activeChat = useVoiceStore((state) => state.activeChatId);
  const token = localStorage.getItem('access');

  // Trigger fade/slide entrance transition on mount
  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      setIsVisible(true);
    });
    return () => cancelAnimationFrame(raf);
  }, []);

  // Activate audio streamer
  const { 
    state, 
    subtitles, 
    micVolume,
    thresholdVolume,
    micAnalyser, 
    playAnalyser 
  } = useAudioStreamer(activeChat, token, {
    modelPreference,
    voiceId,
    personaId,
    preferredLanguage,
    isMuted,
    onError: (err) => console.error('Voice Streamer Error:', err)
  });

  const companions = [
    { id: 'aman', name: 'Aman (Arabic Female)', voiceId: 'ar_zariyah', personaId: 'aman' },
    { id: 'tariq', name: 'Tariq (Arabic Male)', voiceId: 'ar_hamed', personaId: 'tariq' },
    { id: 'layla', name: 'Layla (Clinical Female)', voiceId: 'en_emma', personaId: 'layla' }
  ];

  const currentCompanion = companions.find(
    (c) => c.voiceId === voiceId && c.personaId === personaId
  ) || companions[0];

  const handleSelectCompanion = (comp) => {
    setVoiceId(comp.voiceId);
    setPersonaId(comp.personaId);
    setDropdownOpen(null);
  };

  const handleClose = () => {
    setIsVisible(false); // trigger close slide down animation
  };

  const handleTransitionEnd = () => {
    if (!isVisible) {
      setIsOpen(false); // safely unmount via Zustand store when transition completes
    }
  };

  const getStatusText = () => {
    switch (state) {
      case 'listening': return 'Listening...';
      case 'transcribing': return 'Transcribing...';
      case 'thinking': return 'Thinking...';
      case 'speaking': return 'Speaking...';
      case 'muted': return 'Muted';
      default: return 'Waiting for you to speak';
    }
  };

  const getCompanionName = () => {
    if (personaId === 'tariq') return 'Tariq';
    if (personaId === 'layla') return 'Layla';
    return 'Aman';
  };

  const getHelperText = () => {
    if (isMuted) return 'Microphone is muted';
    const name = getCompanionName();
    switch (state) {
      case 'thinking': return `${name} is thinking...`;
      case 'transcribing': return 'Transcribing your voice...';
      case 'speaking': return `${name} is speaking...`;
      case 'listening': return `${name} is listening...`;
      default: return `Talk naturally. ${name} is listening...`;
    }
  };

  // Muting should not stop Aman's visuals when speaking or thinking
  const orbState = isMuted && (state === 'idle' || state === 'listening') ? 'muted' : state;

  return (
    <div 
      onTransitionEnd={handleTransitionEnd}
      className={`fixed inset-0 z-50 flex flex-col bg-slate-900/95 backdrop-blur-3xl text-white select-none transition-all duration-500 ease-out ${
        isVisible 
          ? 'opacity-100 translate-y-0 scale-100' 
          : 'opacity-0 translate-y-16 scale-95 pointer-events-none'
      }`}
    >
      {/* Top Header */}
      <header className="flex items-center justify-between px-6 py-5 shrink-0 z-10">
        <div className="flex items-center gap-3">
          <button 
            onClick={handleClose}
            className="p-2 bg-slate-800/40 hover:bg-slate-800/70 active:scale-95 border border-slate-700/60 rounded-full transition-all text-slate-300 hover:text-white"
          >
            <X size={20} />
          </button>
          <span className="text-sm font-semibold tracking-wide text-slate-400">VOICE SESSION</span>
        </div>

        {/* Status Pill */}
        <div className="px-4 py-1.5 rounded-full bg-slate-800/40 border border-slate-700/60 flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${
            state === 'listening' ? 'bg-cyan-400 animate-pulse' :
            state === 'speaking' ? 'bg-violet-400 animate-pulse' :
            state === 'thinking' ? 'bg-purple-400 animate-pulse' : 'bg-slate-500'
          }`} />
          <span className="text-xs font-bold tracking-wider uppercase text-slate-200">
            {getStatusText()}
          </span>
        </div>
      </header>

      {/* Center Visualizer & Subtitles */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 relative max-w-2xl mx-auto w-full">
        
        {/* The Morphing Audio Orb */}
        <VoiceOrb 
          state={orbState} 
          micAnalyser={micAnalyser} 
          playAnalyser={playAnalyser} 
          isRecording={state === 'listening'}
        />

        {/* Real-time Mic Level Visualizer */}
        {state === 'listening' && !isMuted && (
          <div className="w-56 mt-4 flex flex-col items-center gap-1.5 z-10">
            <span className="text-[10px] tracking-wider font-semibold text-slate-500 uppercase">Live Mic Level</span>
            <div className="w-full bg-slate-900 border border-slate-700/30 rounded-full h-1.5 overflow-hidden relative">
              <div 
                className="bg-cyan-400 h-full transition-all duration-75 ease-out rounded-full"
                style={{ width: `${micVolume}%` }}
              />
              {/* Threshold line marker */}
              <div 
                className="absolute top-0 bottom-0 w-0.5 bg-rose-500/80" 
                style={{ left: `${thresholdVolume}%` }}
                title="VAD Threshold"
              />
            </div>
          </div>
        )}

        {/* Subtitles Overlay */}
        <div className="h-28 w-full mt-10 flex flex-col justify-center items-center text-center px-4 overflow-hidden">
          {subtitles ? (
            <p className="text-lg md:text-xl font-medium leading-relaxed bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-300 animate-fade-in max-w-xl">
              {subtitles}
            </p>
          ) : (
            <p className="text-sm md:text-base text-slate-500 italic max-w-sm">
              {getHelperText()}
            </p>
          )}
        </div>
      </main>

      {/* Settings / Controls Dock */}
      <footer className="w-full max-w-md mx-auto shrink-0 px-6 pb-12 pt-4 flex flex-col gap-6 items-center z-10">
        
        {/* Toggle Panel */}
        <div className="w-full grid grid-cols-2 gap-2 p-1 bg-slate-800/40 border border-slate-700/60 rounded-2xl">
          
          {/* Fast vs Thinking mode toggle */}
          <button
            onClick={() => setModelPreference(modelPreference === '2' ? '1' : '2')}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold uppercase transition-all duration-300 ${
              modelPreference === '1' 
                ? 'bg-purple-600 text-white shadow-md' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Brain size={14} />
            Thinking
          </button>
          
          <button
            onClick={() => setModelPreference(modelPreference === '2' ? '1' : '2')}
            className={`flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-bold uppercase transition-all duration-300 ${
              modelPreference === '2' 
                ? 'bg-indigo-600 text-white shadow-md' 
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Zap size={14} />
            Fast Mode
          </button>
        </div>

        {/* Unified Companion Selector */}
        <div className="w-full relative">
          <button
            onClick={() => setDropdownOpen(dropdownOpen === 'companion' ? null : 'companion')}
            className="w-full flex items-center justify-between px-5 py-3.5 rounded-2xl bg-slate-800/40 border border-slate-700/60 text-xs font-semibold tracking-wide text-slate-200 hover:bg-slate-800/60 transition-all"
          >
            <div className="flex flex-col text-left">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider mb-0.5">Companion</span>
              <span className="text-sm font-semibold">{currentCompanion.name}</span>
            </div>
            <ChevronDown size={16} className="text-slate-400 shrink-0" />
          </button>
          
          {dropdownOpen === 'companion' && (
            <div className="absolute bottom-full mb-2 left-0 right-0 max-h-56 overflow-y-auto bg-slate-900 border border-slate-700/60 rounded-2xl shadow-xl z-20">
              {companions.map((comp) => (
                <button
                  key={comp.id}
                  onClick={() => handleSelectCompanion(comp)}
                  className={`w-full text-left px-5 py-3.5 border-b border-slate-800/20 hover:bg-slate-800/50 transition-all truncate flex items-center justify-between ${
                    currentCompanion.id === comp.id ? 'text-indigo-400 font-bold bg-slate-800/50' : 'text-slate-300'
                  }`}
                >
                  <span className="text-sm">{comp.name}</span>
                  {currentCompanion.id === comp.id && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Language Selection Row */}
        <div className="w-full flex flex-col gap-1.5">
          <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider pl-1">Speech Language</span>
          <div className="w-full grid grid-cols-3 gap-1.5 p-1 bg-slate-800/40 border border-slate-700/60 rounded-2xl">
            <button
              onClick={() => setPreferredLanguage('auto')}
              className={`py-2 rounded-xl text-xs font-bold uppercase transition-all duration-300 ${
                preferredLanguage === 'auto'
                  ? 'bg-slate-700/70 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Auto
            </button>
            <button
              onClick={() => setPreferredLanguage('ar')}
              className={`py-2 rounded-xl text-xs font-bold uppercase transition-all duration-300 ${
                preferredLanguage === 'ar'
                  ? 'bg-slate-700/70 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              العربية
            </button>
            <button
              onClick={() => setPreferredLanguage('en')}
              className={`py-2 rounded-xl text-xs font-bold uppercase transition-all duration-300 ${
                preferredLanguage === 'en'
                  ? 'bg-slate-700/70 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              English
            </button>
          </div>
        </div>

        {/* Primary Controls Row */}
        <div className="flex items-center gap-6 mt-2">
          
          {/* Mute Button */}
          <button
            onClick={() => setIsMuted(!isMuted)}
            className={`p-4 rounded-full transition-all active:scale-95 border ${
              isMuted 
                ? 'bg-red-500/10 border-red-500/50 text-red-500' 
                : 'bg-slate-800/40 border-slate-700/60 text-slate-300 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            {isMuted ? <MicOff size={22} /> : <Mic size={22} />}
          </button>

          {/* End Call Button */}
          <button
            onClick={handleClose}
            className="p-5 rounded-full bg-red-600 hover:bg-red-500 active:scale-95 text-white transition-all shadow-lg hover:shadow-red-600/30"
          >
            <PhoneOff size={24} />
          </button>
        </div>

      </footer>
    </div>
  );
}
