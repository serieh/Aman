import React, { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useChatStore } from '../store/useChatStore';
import { Heart, Brain, Wind, Lightbulb } from 'lucide-react';

export default function Dashboard() {
  const { setInputMessage, setTriggerSend } = useChatStore();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isAutoPlay = searchParams.get('autoPlay') === 'true';

  useEffect(() => {
    if (isAutoPlay) {
      const timer = setTimeout(() => {
        navigate('/app/chat/1?autoPlay=true');
      }, 4000); // 4-second delay before starting chats
      return () => clearTimeout(timer);
    }
  }, [isAutoPlay, navigate]);

  const handleChipClick = (text) => {
    setInputMessage(text);
    setTriggerSend(true);
  };

  const suggestions = [
    { text: "I'm feeling anxious.", icon: Heart, color: 'text-rose-500' },
    { text: "Let's talk about stress.", icon: Brain, color: 'text-violet-500' },
    { text: "Tell me a meditation technique.", icon: Wind, color: 'text-sky-500' },
    { text: "How to manage overthinking?", icon: Lightbulb, color: 'text-amber-500' },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center h-full p-4 aman-gradient-bg">
      <div className="text-center space-y-10 max-w-2xl mx-auto -mt-20">
        {/* Greeting */}
        <div className="space-y-3">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            <span className="text-slate-800">How are you</span>
            <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary">feeling today?</span>
          </h1>
          <p className="text-slate-600 text-lg font-medium">Choose a topic or type your own message below.</p>
        </div>
        
        {/* Suggestion Chips */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg mx-auto">
          {suggestions.map((chip) => {
            const Icon = chip.icon;
            return (
              <button 
                key={chip.text}
                onClick={() => handleChipClick(chip.text)}
                className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-white/60 backdrop-blur-md hover:bg-white/90 border border-white/50 hover:border-slate-200 hover:scale-[1.02] active:scale-[0.98] transition-all text-left shadow-sm hover:shadow-lg group"
              >
                <Icon size={20} className={`${chip.color} group-hover:scale-110 transition-transform flex-shrink-0`} />
                <span className="text-slate-700 font-medium text-sm leading-snug">{chip.text}</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
