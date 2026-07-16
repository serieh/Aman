import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Sparkles, Zap, User } from 'lucide-react';

export default function Slide4_ScriptedChat({ isAutoPlay, onAutoComplete }) {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const [model, setModel] = useState('2'); // '2' is Fast, '1' is Thinking
  
  const [scriptStarted, setScriptStarted] = useState(false);
  const messagesEndRef = useRef(null);

  const models = [
    { id: '2', label: 'Fast', icon: Zap, description: 'Quick responses' },
    { id: '1', label: 'Thinking', icon: Sparkles, description: 'Deeper reasoning' },
  ];
  const activeModel = models.find(m => m.id === model) || models[0];
  const ActiveIcon = activeModel.icon;

  const script = [
    {
      user: "Hello Aman, I'm feeling a bit overwhelmed today. There's so much pressure.",
      aman: "I'm sorry you're feeling overwhelmed. It's completely normal to feel that way when pressure builds up. Take a deep breath. Can you tell me a little bit about what's causing this pressure right now?",
    },
    {
      user: "Work deadlines, family expectations... it feels like I'm failing everyone.",
      aman: "That sounds like a heavy burden to carry. Remember, you are human, and it's okay to have limits. When we try to be everything to everyone, we often forget our own well-being. What is one small thing you can control right now to ease this burden?",
    },
    {
      user: "I guess I could take a short break and organize my tasks.",
      aman: "That is an excellent idea. Taking a step back to organize can give you a clearer perspective. You've got this. Take it one step at a time, and remember that I'm here for you whenever you need to talk.",
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, inputValue]);

  useEffect(() => {
    if (isAutoPlay && !scriptStarted) {
      const timer = setTimeout(() => {
        runScript();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [isAutoPlay, scriptStarted]);

  const runScript = async () => {
    if (scriptStarted) return;
    setScriptStarted(true);
    
    for (let i = 0; i < script.length; i++) {
      const turn = script[i];
      
      // 1. Auto-type user message
      setInputValue('');
      for (let j = 0; j < turn.user.length; j++) {
        setInputValue(prev => prev + turn.user[j]);
        await new Promise(r => setTimeout(r, 15)); // Faster typing
      }
      
      // Short pause before submitting
      await new Promise(r => setTimeout(r, 100));
      
      // Submit user message
      setInputValue('');
      setMessages(prev => [...prev, { role: 'user', content: turn.user }]);
      setIsGenerating(true);
      
      // 2. Show thinking
      const aiMsgIndex = messages.length + (i * 2) + 1;
      setMessages(prev => [...prev, { role: 'assistant', content: '', isGenerating: true }]);
      
      // Simulate "Thinking" delay
      const thinkTime = model === '1' ? 800 : 200; // Significantly reduced
      await new Promise(r => setTimeout(r, thinkTime));
      
      // 3. Stream AI response
      setMessages(prev => prev.map((msg, idx) => idx === aiMsgIndex ? { ...msg, isGenerating: false } : msg));
      
      let currentAiContent = '';
      const words = turn.aman.split(' ');
      
      for (let w = 0; w < words.length; w++) {
        currentAiContent += (w === 0 ? '' : ' ') + words[w];
        setMessages(prev => prev.map((msg, idx) => idx === aiMsgIndex ? { ...msg, content: currentAiContent } : msg));
        await new Promise(r => setTimeout(r, 20)); // Super fast streaming
      }
      
      setIsGenerating(false);
      
      // Pause before next message
      await new Promise(r => setTimeout(r, 400));
    }
    
    // Return focus to page so arrow keys work
    if (document.activeElement) {
      document.activeElement.blur();
    }
    
    // Signal completion for autoPlay
    if (onAutoComplete) {
      onAutoComplete();
    }
  };

  return (
    <div className="flex flex-col h-full w-full max-w-4xl mx-auto px-4 animate-in fade-in duration-500">
      <div className="flex-1 overflow-y-auto pt-8 pb-32 scrollbar-hide">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
            <h2 className="text-3xl font-bold text-slate-800 dark:text-white mb-2">Aman Prototype</h2>
            <p className="text-slate-500">Type Anything below to begin.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {messages.map((msg, index) => (
              <div key={index} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-aman-primary to-aman-tertiary flex items-center justify-center flex-shrink-0 text-white font-bold text-xs shadow-lg">
                    A
                  </div>
                )}
                
                <div className={`max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm ${msg.role === 'user' ? 'bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200 rounded-tr-sm' : 'bg-white dark:bg-slate-800/80 border border-slate-100 dark:border-slate-700/50 text-slate-700 dark:text-slate-300 rounded-tl-sm'}`}>
                  {msg.isGenerating && !msg.content ? (
                    <div className="flex items-center gap-2 h-6">
                      <div className="w-2 h-2 bg-aman-primary rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-aman-primary rounded-full animate-bounce [animation-delay:-.3s]"></div>
                      <div className="w-2 h-2 bg-aman-primary rounded-full animate-bounce [animation-delay:-.5s]"></div>
                    </div>
                  ) : (
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                  )}
                </div>
                
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center flex-shrink-0 text-slate-500">
                    <User size={16} />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <div className="absolute bottom-0 left-0 right-0 px-4 md:px-0 flex justify-center z-10 pb-5">
        <div className="w-full max-w-3xl pointer-events-auto">
          <div className="rounded-3xl p-1.5 shadow-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-700/80 mb-4">
            
            <div className="flex items-center gap-1 px-2">
              <input 
                type="text" 
                value={inputValue}
                readOnly
                onClick={runScript}
                placeholder="Type Anything below to begin..."
                className="flex-1 bg-transparent border-none outline-none text-slate-700 dark:text-slate-100 placeholder:text-slate-400 py-3 px-3 cursor-pointer font-medium text-[15px]"
              />
              <button disabled={!inputValue.trim()} className="p-2 bg-slate-800 dark:bg-white text-white dark:text-slate-800 rounded-full transition-all disabled:opacity-30 disabled:cursor-not-allowed flex-shrink-0">
                <ArrowUp size={16} strokeWidth={2.5} />
              </button>
            </div>

            <div className="flex items-center justify-between px-3 pb-1 pt-0.5">
              <div className="relative">
                <button 
                  onClick={() => setModelMenuOpen(!modelMenuOpen)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
                >
                  <ActiveIcon size={13} className="text-aman-primary" />
                  {activeModel.label}
                </button>

                {modelMenuOpen && (
                  <div className="absolute bottom-full left-0 mb-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl overflow-hidden w-48 z-50">
                    {models.map(m => {
                      const Icon = m.icon;
                      return (
                        <button
                          key={m.id}
                          onClick={() => { setModel(m.id); setModelMenuOpen(false); }}
                          className={`w-full flex items-center gap-3 px-4 py-3 text-left text-sm transition-colors ${model === m.id ? 'bg-aman-primary/10 text-aman-primary font-semibold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                        >
                          <Icon size={16} className={model === m.id ? 'text-aman-primary' : 'text-slate-400'} />
                          <div>
                            <div className="font-medium">{m.label}</div>
                            <div className="text-[10px] text-slate-400 font-normal">{m.description}</div>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
}
