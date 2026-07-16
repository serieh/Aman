import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatStore } from '../store/useChatStore';
import { useVoiceStore } from '../store/useVoiceStore';
import { useTranslation } from '../hooks/useTranslation';
import api from '../api/axios';
import { Heart, Brain, Wind, Lightbulb, Phone } from 'lucide-react';

export default function Dashboard() {
  const { setInputMessage, setTriggerSend } = useChatStore();
  const { t } = useTranslation();
  const navigate = useNavigate();

  useEffect(() => {
    // Clear current chat state when landing on the dashboard
    useChatStore.getState().setCurrentChat(null);
  }, []);

  const handleChipClick = (text) => {
    setInputMessage(text);
    setTriggerSend(true);
  };

  const handleVoiceStart = async () => {
    // Synchronously initialize AudioContext on user gesture to avoid browser sandbox suspension
    if (typeof window !== 'undefined') {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        try {
          if (!window.__amanAudioContext) {
            window.__amanAudioContext = new AudioCtx();
          }
          if (window.__amanAudioContext.state === 'suspended') {
            window.__amanAudioContext.resume();
          }
        } catch (e) {
          console.error("Failed to initialize gesture AudioContext:", e);
        }
      }
    }

    try {
      const { data } = await api.post('/chats/', {
        persona_id: useChatStore.getState().selectedPersonaId || 'aman',
        is_voice: true
      });
      const newChatId = String(data.chat_id);
      
      // Update chat store list
      const currentChats = useChatStore.getState().chats;
      useChatStore.setState({
        chats: [data, ...currentChats],
        currentChat: data
      });
      
      // Open Voice overlay and bind to new chat ID
      useVoiceStore.setState({ activeChatId: newChatId });
      useVoiceStore.getState().setIsOpen(true);
      
      // Navigate to chat
      navigate(`/app/chat/${newChatId}`);
    } catch (e) {
      console.error("Failed to start voice chat from dashboard", e);
    }
  };

  const suggestions = [
    { text: t('suggestion_anxious'), icon: Heart, color: 'text-rose-500' },
    { text: t('suggestion_stress'), icon: Brain, color: 'text-violet-500' },
    { text: t('suggestion_meditation'), icon: Wind, color: 'text-sky-500' },
    { text: t('suggestion_overthinking'), icon: Lightbulb, color: 'text-amber-500' },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full p-4 aman-gradient-bg overflow-y-auto">
      <div className="text-center space-y-10 max-w-2xl mx-auto -mt-20">
        {/* Greeting */}
        <div className="space-y-3">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            <span className="text-slate-800">{t('hero_title_pre')}</span>
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary">{t('hero_title_post')}</span>
          </h1>
          <p className="text-slate-600 text-lg font-medium">{t('suggestions_desc')}</p>
        </div>
        
        {/* Suggestion Chips */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
          {suggestions.map((chip) => {
            const Icon = chip.icon;
            return (
              <button 
                key={chip.text}
                onClick={() => handleChipClick(chip.text)}
                className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-white/60 backdrop-blur-md hover:bg-white/90 border border-white/50 hover:border-slate-200 hover:scale-[1.02] active:scale-[0.98] transition-all text-start shadow-sm hover:shadow-lg group cursor-pointer"
              >
                <Icon size={20} className={`${chip.color} group-hover:scale-110 transition-transform flex-shrink-0`} />
                <span className="text-slate-700 font-medium text-sm leading-snug">{chip.text}</span>
              </button>
            );
          })}
        </div>

        {/* Dashboard Voice Action */}
        <div className="flex justify-center pt-2">
          <button
            onClick={handleVoiceStart}
            className="flex items-center gap-2.5 px-6 py-3.5 rounded-full bg-slate-900 hover:bg-slate-800 active:scale-95 text-white text-sm font-bold tracking-wide shadow-lg hover:shadow-slate-900/20 transition-all hover:scale-105 cursor-pointer"
          >
            <Phone size={16} className="text-indigo-400" />
            {t('start_voice')}
          </button>
        </div>
      </div>
    </div>
  );
}
