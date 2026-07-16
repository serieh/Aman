import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PhoneCall } from 'lucide-react';
import { useVoiceStore } from '../store/useVoiceStore';
import { useChatStore } from '../store/useChatStore';
import api from '../api/axios';

export default function VoiceModeButton({ chatId }) {
  const setIsOpen = useVoiceStore((state) => state.setIsOpen);
  const navigate = useNavigate();

  const handleClick = async () => {
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

    let targetChatId = chatId;

    if (!targetChatId || targetChatId === 'new') {
      try {
        const { data } = await api.post('/chats/', {
          persona_id: useChatStore.getState().selectedPersonaId || 'aman',
          is_voice: true
        });
        targetChatId = String(data.chat_id);
        
        // Update Chat Store list
        const currentChats = useChatStore.getState().chats;
        useChatStore.setState({
          chats: [data, ...currentChats],
          currentChat: data
        });

        // Navigate page
        navigate(`/app/chat/${targetChatId}`, { replace: true });
      } catch (e) {
        console.error("Failed to create chat in VoiceModeButton:", e);
        return;
      }
    }

    useVoiceStore.setState({ activeChatId: targetChatId });
    setIsOpen(true);
  };

  return (
    <button
      onClick={handleClick}
      type="button"
      className="p-2.5 bg-slate-100 hover:bg-slate-200 border border-slate-200 rounded-full text-slate-600 hover:text-aman-primary hover:scale-105 active:scale-95 transition-all shadow-sm flex items-center justify-center shrink-0"
      title="Start Voice Session"
    >
      <PhoneCall size={18} />
    </button>
  );
}
