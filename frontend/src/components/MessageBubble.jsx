import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Clock, Bot } from 'lucide-react';

export default function MessageBubble({ message, isGenerating = false }) {
  const [showThought, setShowThought] = useState(false);
  const isUser = message.role === 'user';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="bg-aman-primary text-white px-5 py-3 rounded-2xl rounded-br-sm max-w-[85%] md:max-w-[75%] font-medium text-[15px] leading-relaxed shadow-sm">
          {message.content}
        </div>
      </div>
    );
  }

  // Parse <think> tags
  let thinkText = null;
  let mainContent = message.content || '';
  let isThinkingActive = false;
  
  const thinkMatch = mainContent.match(/<think>([\s\S]*?)<\/think>/);
  if (thinkMatch) {
     thinkText = thinkMatch[1].trim();
     mainContent = mainContent.replace(thinkMatch[0], '').trim();
  } else if (mainContent.includes('<think>')) {
     isThinkingActive = true;
     const parts = mainContent.split('<think>');
     thinkText = parts[1]?.trim() || '';
     mainContent = parts[0].trim();
  }

  const showLoadingDots = isGenerating && !isThinkingActive && !mainContent;

  return (
    <div className="flex justify-start">
      <div className="flex items-start gap-3 max-w-[90%] md:max-w-[80%]">
        
        {/* Avatar */}
        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 ${isGenerating ? 'bg-gradient-to-br from-aman-primary to-aman-tertiary shadow-md animate-pulse' : 'bg-white shadow-sm border border-slate-200/50'}`}>
          <img src="/favicon.ico" alt="Aman" className={`w-5 h-5 object-contain ${isGenerating ? 'opacity-90' : 'opacity-100'}`} />
        </div>
        
        {/* Message Content Area */}
        <div className="flex flex-col gap-2 min-w-0 flex-1">
          
          {/* Timer badge */}
          {!isGenerating && message.timeToFirstToken && (
             <div className="flex items-center gap-1 text-[11px] text-slate-400 font-medium">
               <Clock size={11} />
               <span>{message.timeToFirstToken}s</span>
             </div>
          )}

          {/* Thinking Accordion */}
          {(thinkText || isThinkingActive) && (
            <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl overflow-hidden border border-slate-200/50 dark:border-slate-700/50">
              <button 
                onClick={() => setShowThought(!showThought)}
                className="w-full flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-500 hover:bg-slate-50/80 dark:hover:bg-slate-700/50 transition-colors"
              >
                {showThought ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                {isThinkingActive && isGenerating ? (
                   <span className="flex items-center gap-2">
                     Thinking
                     <span className="flex gap-0.5">
                       <span className="w-1 h-1 bg-aman-primary rounded-full animate-bounce"></span>
                       <span className="w-1 h-1 bg-aman-primary rounded-full animate-bounce [animation-delay:0.15s]"></span>
                       <span className="w-1 h-1 bg-aman-primary rounded-full animate-bounce [animation-delay:0.3s]"></span>
                     </span>
                   </span>
                ) : (
                   "Thought Process"
                )}
              </button>
              
              {showThought && (
                <div className="px-3.5 py-2.5 text-sm text-slate-500 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-900/30 border-t border-slate-200/50 dark:border-slate-700/50 whitespace-pre-wrap leading-relaxed italic">
                  {thinkText}
                </div>
              )}
            </div>
          )}

          {/* Loading dots placeholder */}
          {showLoadingDots && (
            <div className="bg-white dark:bg-slate-800 px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm border border-slate-200/50 dark:border-slate-700/50">
              <span className="inline-flex items-center gap-1.5 h-5">
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0.15s]"></span>
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0.3s]"></span>
              </span>
            </div>
          )}

          {/* Actual Response */}
          {mainContent && (
            <div className="bg-white dark:bg-slate-800 px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm border border-slate-200/50 dark:border-slate-700/50 text-slate-700 dark:text-slate-200 text-[15px] leading-relaxed whitespace-pre-wrap font-medium">
              {mainContent}
              {isGenerating && !isThinkingActive && (
                 <span className="ml-1.5 inline-flex items-center gap-1 align-middle h-5">
                   <span className="w-1.5 h-1.5 bg-aman-primary rounded-full animate-bounce"></span>
                   <span className="w-1.5 h-1.5 bg-aman-primary rounded-full animate-bounce [animation-delay:0.15s]"></span>
                   <span className="w-1.5 h-1.5 bg-aman-primary rounded-full animate-bounce [animation-delay:0.3s]"></span>
                 </span>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
