import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Clock } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';
import { useTranslation } from '../hooks/useTranslation';

export const MessageBubble = React.memo(function MessageBubble({ message, isGenerating = false }) {
  const [showThought, setShowThought] = useState(false);
  const { t } = useTranslation();
  const isUser = message.role === 'user';

  const personas = useChatStore(state => state.personas);
  const persona = !isUser && message.persona_id 
    ? personas.find(p => p.id === message.persona_id) 
    : null;
  const fallbackNames = {
    aman: 'Aman',
    tariq: 'Tariq',
    layla: 'Layla'
  };
  const personaNames = {
    aman: t('persona_name_aman'),
    tariq: t('persona_name_tariq'),
    layla: t('persona_name_layla'),
  };
  
  const personaName = personaNames[message.persona_id] || persona?.name || (!isUser ? (fallbackNames[message.persona_id] || 'Aman') : null);

  if (isUser) {
    return (
      // Physical alignment: User messages always on the right side of the screen
      <div className="flex ltr:justify-end rtl:justify-start">
        {/* Physical tails: rounded-br-sm tail stays on bottom-right */}
        <div className="bg-aman-primary text-white px-5 py-3 rounded-2xl rounded-br-sm max-w-[85%] md:max-w-[75%] font-medium text-[15px] leading-relaxed shadow-sm text-start">
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
    // Physical alignment: Companion messages always on the left side of the screen
    <div className="flex justify-start ltr:justify-start rtl:justify-end">
      <div className="flex items-start gap-3 max-w-[90%] md:max-w-[80%] ltr:flex-row rtl:flex-row-reverse">
        
        {/* Avatar */}
        <div className="flex flex-col items-center gap-1 flex-shrink-0">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center mt-1 ${isGenerating ? 'bg-gradient-to-br from-aman-primary to-aman-tertiary shadow-md animate-pulse' : 'bg-white shadow-sm border border-slate-200/50'}`}>
            {personaName ? (
              <span className={`text-sm font-bold ${isGenerating ? 'text-white' : 'text-aman-primary'}`}>{personaName.charAt(0)}</span>
            ) : (
              <img src="/favicon.ico" alt="Aman" className={`w-5 h-5 object-contain ${isGenerating ? 'opacity-90' : 'opacity-100'}`} />
            )}
          </div>
          {personaName && (
            <span className="text-[10px] font-semibold text-slate-400 leading-none">{personaName}</span>
          )}
        </div>
        
        {/* Message Content Area */}
        <div className="flex flex-col gap-2 min-w-0 flex-1">
          
          {/* Timer badge */}
          {!isGenerating && message.timeToFirstToken && (
             <div className="flex items-center gap-1 text-[11px] text-slate-400 font-medium">
               <Clock size={11} />
               {/* Prevent Safari bidirectional number scrambling */}
               <span><bdi dir="ltr">{message.timeToFirstToken}s</bdi></span>
             </div>
          )}

          {/* Thinking Accordion */}
          {(thinkText || isThinkingActive) && (
            <div className="bg-white/60 dark:bg-slate-800/60 backdrop-blur-sm rounded-xl overflow-hidden border border-slate-200/50 dark:border-slate-700/50">
              <button 
                onClick={() => setShowThought(!showThought)}
                className="w-full flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-slate-500 hover:bg-slate-50/80 dark:hover:bg-slate-700/50 transition-colors cursor-pointer text-start"
              >
                {/* Mirror expansion arrow in RTL */}
                {showThought ? <ChevronDown size={13} /> : <ChevronRight size={13} className="rtl:rotate-180" />}
                {isThinkingActive && isGenerating ? (
                   <span className="flex items-center gap-2">
                     {t('thinking')}
                     <span className="flex gap-0.5">
                       <span className="w-1 h-1 bg-aman-primary rounded-full animate-bounce"></span>
                       <span className="w-1 h-1 bg-aman-primary rounded-full animate-bounce [animation-delay:0.15s]"></span>
                       <span className="w-1 h-1 bg-aman-primary rounded-full animate-bounce [animation-delay:0.3s]"></span>
                     </span>
                   </span>
                ) : (
                   t('thought_process')
                )}
              </button>
              
              {showThought && (
                <div className="px-3.5 py-2.5 text-sm text-slate-500 dark:text-slate-400 bg-slate-50/50 dark:bg-slate-900/30 border-t border-slate-200/50 dark:border-slate-700/50 whitespace-pre-wrap leading-relaxed italic text-start">
                  {thinkText}
                </div>
              )}
            </div>
          )}

          {/* Loading dots placeholder */}
          {showLoadingDots && (
            // Physical tails: rounded-tl-sm tail stays on top-left next to avatar
            <div className="bg-white dark:bg-slate-800 px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm border border-slate-200/50 dark:border-slate-700/50 text-start">
              <span className="inline-flex items-center gap-1.5 h-5">
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0.15s]"></span>
                <span className="w-2 h-2 bg-slate-300 rounded-full animate-bounce [animation-delay:0.3s]"></span>
              </span>
            </div>
          )}

          {/* Actual Response */}
          {mainContent && (
            // Physical tails: rounded-tl-sm tail stays on top-left next to avatar
            <div className="bg-white dark:bg-slate-800 px-5 py-4 rounded-2xl rounded-tl-sm shadow-sm border border-slate-200/50 dark:border-slate-700/50 text-slate-700 dark:text-slate-200 text-[15px] leading-relaxed whitespace-pre-wrap font-medium text-start">
              {mainContent}
              {isGenerating && !isThinkingActive && (
                 <span className="ms-1.5 inline-flex items-center gap-1 align-middle h-5">
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
});

export default MessageBubble;
