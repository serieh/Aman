import React, { useState, useEffect, useRef } from 'react';
import { Paperclip, ArrowUp, Square, Sparkles, Zap } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';

export default function InputBar({ chatId }) {
  const { inputMessage, setInputMessage, triggerSend, setTriggerSend, addMessage, model, setModel, messages, setMessages, chats, setChats, setCurrentChat, setGeneratingTitleChatId, updateChatTitle } = useChatStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [abortController, setAbortController] = useState(null);
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  
  const navigate = useNavigate();
  const formRef = useRef(null);
  const modelRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-focus input on mount and when chatId changes
  useEffect(() => {
    if (inputRef.current && !isGenerating) {
      inputRef.current.focus();
    }
  }, [chatId, isGenerating]);

  // Close model menu on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (modelRef.current && !modelRef.current.contains(event.target)) {
        setModelMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (triggerSend && inputMessage && !isGenerating) {
      setTriggerSend(false);
      if (formRef.current) {
        formRef.current.requestSubmit();
      }
    } else if (triggerSend) {
      setTriggerSend(false);
    }
  }, [triggerSend, inputMessage, isGenerating, setTriggerSend]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isGenerating) return;
    
    const messageToSend = inputMessage;
    setInputMessage('');
    
    let activeChatId = chatId;
    
    // OPTIMISTIC UI: Instantly navigate and show user message
    if (!activeChatId || activeChatId === 'temp') {
      activeChatId = 'temp';
      navigate(`/app/chat/temp`);
    }

    const userMsg = { role: 'user', content: messageToSend, message_id: Date.now().toString() };
    addMessage(userMsg);
    setIsGenerating(true);

    const controller = new AbortController();
    setAbortController(controller);

    try {
      // If we are in 'temp' state, create the chat in the backend
      if (activeChatId === 'temp') {
        const { data } = await api.post('/chats/');
        activeChatId = data.chat_id;
        setChats([data, ...chats]);
        setCurrentChat(data);
        setGeneratingTitleChatId(activeChatId);
        navigate(`/app/chat/${activeChatId}`, { replace: true });
      }

      // Create a temporary AI message for streaming
      const aiMsgId = (Date.now() + 1).toString();
      addMessage({ role: 'assistant', content: '', message_id: aiMsgId, isGenerating: true, timeToFirstToken: null });

      const startTime = Date.now();
      let firstTokenReceived = false;

      const token = localStorage.getItem('access');
      
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${wsProtocol}//${window.location.host}/ws/chat/${activeChatId}/?token=${token}`;
      
      const ws = new WebSocket(wsUrl);
      
      // Keep track of connection
      setAbortController({ abort: () => {
        if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
          ws.close();
        }
      }});

      let fullContent = '';
      let timeToFirstToken = null;

      ws.onopen = () => {
        ws.send(JSON.stringify({
          message: messageToSend,
          model_preference: model,
        }));
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          console.error("WebSocket error:", data.error);
          ws.close();
          const currentMessages = useChatStore.getState().messages;
          setMessages(currentMessages.map(m =>
            m.message_id === aiMsgId ? { ...m, content: `Sorry, something went wrong: ${data.error}`, isGenerating: false } : m
          ));
          setIsGenerating(false);
          setAbortController(null);
          return;
        }
        
        if (data.clear) {
          fullContent = '';
          firstTokenReceived = false;
          timeToFirstToken = null;
          setMessages(useChatStore.getState().messages.map(m => 
            m.message_id === aiMsgId ? { ...m, content: '', timeToFirstToken: null } : m
          ));
          return;
        }

        if (data.replace_all) {
          fullContent = data.replace_all;
          setMessages(useChatStore.getState().messages.map(m => 
            m.message_id === aiMsgId ? { ...m, content: fullContent } : m
          ));
          return;
        }
        
        if (data.chunk) {
          fullContent += data.chunk;
          if (!firstTokenReceived && fullContent.trim().length > 0) {
            firstTokenReceived = true;
            timeToFirstToken = ((Date.now() - startTime) / 1000).toFixed(1);
          }
          setMessages(useChatStore.getState().messages.map(m => 
            m.message_id === aiMsgId ? { ...m, content: fullContent, timeToFirstToken } : m
          ));
        }
        
        if (data.done) {
          ws.close();
          // Final update
          setMessages(useChatStore.getState().messages.map(m => 
            m.message_id === aiMsgId ? { ...m, content: fullContent, isGenerating: false } : m
          ));

          // Fetch updated chat title after response completes
          const currentGeneratingId = useChatStore.getState().generatingTitleChatId;
          if (currentGeneratingId === activeChatId) {
            const pollTitle = async (retries = 6, delay = 2000) => {
              if (retries <= 0) {
                useChatStore.getState().setGeneratingTitleChatId(null);
                return;
              }
              try {
                const { data: chatData } = await api.get(`/chats/${activeChatId}/`);
                if (chatData.title && chatData.title !== 'Untitled Chat') {
                  updateChatTitle(activeChatId, chatData.title);
                } else {
                  setTimeout(() => pollTitle(retries - 1, delay), delay);
                }
              } catch (e) {
                useChatStore.getState().setGeneratingTitleChatId(null);
              }
            };
            pollTitle();
          }
          
          setIsGenerating(false);
          setAbortController(null);
        }
      };

      ws.onerror = (err) => {
        console.error("WebSocket connection failed", err);
        const currentMessages = useChatStore.getState().messages;
        setMessages(currentMessages.map(m =>
          m.message_id === aiMsgId ? { ...m, content: 'Sorry, connection failed. Please try again.', isGenerating: false } : m
        ));
        setIsGenerating(false);
        setAbortController(null);
      };

      ws.onclose = () => {
        // Fallback in case it closes without done signal or error handled
        if (useChatStore.getState().messages.find(m => m.message_id === aiMsgId)?.isGenerating) {
            setMessages(useChatStore.getState().messages.map(m => 
                m.message_id === aiMsgId ? { ...m, isGenerating: false } : m
            ));
            setIsGenerating(false);
            setAbortController(null);
        }
      };

    } catch (err) {
      console.error("Stream initialization failed", err);
      setIsGenerating(false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    if (abortController) {
      abortController.abort();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (formRef.current) formRef.current.requestSubmit();
    }
  };

  const models = [
    { id: '2', label: 'Fast', icon: Zap, description: 'Quick responses' },
    { id: '1', label: 'Thinking', icon: Sparkles, description: 'Deeper reasoning' },
  ];
  const activeModel = models.find(m => m.id === model) || models[0];
  const ActiveIcon = activeModel.icon;

  return (
    <div className="rounded-3xl p-1.5 shadow-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-700/80 mb-4">
      {/* Input row */}
      <form ref={formRef} onSubmit={handleSubmit} className="flex items-center gap-1 px-2">
        <input 
          ref={inputRef}
          type="text" 
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Message Aman..."
          disabled={isGenerating}
          className="flex-1 bg-transparent border-none outline-none text-slate-700 dark:text-slate-100 placeholder:text-slate-400 py-3 px-3 disabled:opacity-50 font-medium text-[15px]"
        />
        
        {isGenerating ? (
          <button type="button" onClick={handleStop} className="p-2 bg-slate-800 dark:bg-white text-white dark:text-slate-800 rounded-full hover:opacity-80 transition-all flex-shrink-0">
            <Square size={16} className="fill-current" />
          </button>
        ) : (
          <button type="submit" disabled={!inputMessage.trim()} className="p-2 bg-slate-800 dark:bg-white text-white dark:text-slate-800 rounded-full transition-all disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-700 active:scale-90 flex-shrink-0">
            <ArrowUp size={16} strokeWidth={2.5} />
          </button>
        )}
      </form>

      {/* Bottom toolbar row */}
      <div className="flex items-center justify-between px-3 pb-1 pt-0.5">
        {/* Model selector (left) */}
        <div className="relative" ref={modelRef}>
          <button 
            type="button"
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
  );
}
