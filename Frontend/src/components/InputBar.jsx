import React, { useState, useEffect, useRef } from 'react';
import { Paperclip, ArrowUp, Square, Sparkles, Zap, Mic, MicOff, User } from 'lucide-react';
import { useChatStore } from '../store/useChatStore';
import { useAuthStore } from '../store/useAuthStore';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import VoiceModeButton from './VoiceModeButton';

export default function InputBar({ chatId }) {
  const isGenerating = useChatStore(state => chatId ? !!state.isGeneratingByChat[String(chatId)] : false);
  const setIsGenerating = (val) => useChatStore.getState().setIsGeneratingForChat(chatId, val);
  
  const { inputMessage, setInputMessage, triggerSend, setTriggerSend, model, setModel, chats, setChats, setCurrentChat, setGeneratingTitleChatId, updateChatTitle, personas, selectedPersonaId, setSelectedPersonaId } = useChatStore();
  const [abortController, setAbortController] = useState(null);
  const [modelMenuOpen, setModelMenuOpen] = useState(false);
  const [personaMenuOpen, setPersonaMenuOpen] = useState(false);
  const navigate = useNavigate();
  const formRef = useRef(null);
  const modelRef = useRef(null);
  const personaRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (triggerSend) {
      if (formRef.current) formRef.current.requestSubmit();
      setTriggerSend(false);
    }
  }, [triggerSend, setTriggerSend]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (modelRef.current && !modelRef.current.contains(event.target)) {
        setModelMenuOpen(false);
      }
      if (personaRef.current && !personaRef.current.contains(event.target)) {
        setPersonaMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (formRef.current) formRef.current.requestSubmit();
    }
  };

  const wsRef = useRef(null);

  const connectWs = (targetChatId) => {
    if (wsRef.current) {
      if (wsRef.current.chatId === String(targetChatId)) return wsRef.current;
      wsRef.current.onmessage = null;
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.close();
    }
    
    const token = localStorage.getItem('access');
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws/chat/${targetChatId}/?token=${token}`;
    const ws = new WebSocket(wsUrl);
    ws.chatId = String(targetChatId);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.title_update) {
        updateChatTitle(data.title_update.chat_id, data.title_update.title);
        useChatStore.getState().setGeneratingTitleChatId(null);
        return;
      }

      if (data.generation_status) {
        const { chat_id, is_generating } = data.generation_status;
        
        // Prevent connect sync from overriding local active generation state
        if (!is_generating) {
          const messages = useChatStore.getState().messagesByChat[String(chat_id)] || [];
          const hasActiveGeneratingMessage = messages.some(m => m.isGenerating);
          if (hasActiveGeneratingMessage) {
            return;
          }
        }

        const currentChats = useChatStore.getState().chats;
        useChatStore.setState({
          chats: currentChats.map(c => String(c.chat_id) === String(chat_id) ? { ...c, is_generating } : c)
        });
        useChatStore.getState().setIsGeneratingForChat(chat_id, is_generating);
        return;
      }

      if (data.user_message) {
        const currentMessages = useChatStore.getState().messagesByChat[String(targetChatId)] || [];
        const exists = currentMessages.some(m => 
          (m.message_id === data.user_message.message_id) || 
          (data.user_message.client_message_id && m.message_id === data.user_message.client_message_id)
        );
        if (!exists) {
          useChatStore.getState().addChatMessage(targetChatId, {
            role: 'user',
            content: data.user_message.content,
            message_id: data.user_message.message_id
          });
        } else {
          // Update the message ID of the optimistic message to the database ID
          const updated = currentMessages.map(m => 
            m.message_id === data.user_message.client_message_id 
              ? { ...m, message_id: data.user_message.message_id } 
              : m
          );
          useChatStore.getState().setChatMessages(targetChatId, updated);
        }
        return;
      }

      const currentMessages = useChatStore.getState().messagesByChat[String(targetChatId)] || [];
      const activeAiMsg = currentMessages.find(m => m.isGenerating);
      const aiMsgId = activeAiMsg ? activeAiMsg.message_id : (data.message_id || 'temp-ai-id');

      // Ensure the assistant message bubble exists if we are receiving chunks/replacement/clear/catchup
      const hasAiMsg = currentMessages.some(m => m.message_id === aiMsgId);
      if (!hasAiMsg && (data.chunk || data.replace_all || data.clear || data.catchup)) {
        useChatStore.getState().addChatMessage(targetChatId, {
          role: 'assistant',
          content: '',
          message_id: aiMsgId,
          isGenerating: true,
          persona_id: useChatStore.getState().selectedPersonaId,
          timeToFirstToken: null
        });
      }

      if (data.catchup) {
        useChatStore.getState().setIsGeneratingForChat(targetChatId, true);
        const updated = (useChatStore.getState().messagesByChat[String(targetChatId)] || []).map(m =>
          m.message_id === aiMsgId ? { ...m, content: data.content, isGenerating: true } : m
        );
        useChatStore.getState().setChatMessages(targetChatId, updated);
        return;
      }

      if (data.error) {
        const updated = (useChatStore.getState().messagesByChat[String(targetChatId)] || []).map(m =>
          m.message_id === aiMsgId ? { ...m, content: `Sorry, something went wrong: ${data.error}`, isGenerating: false } : m
        );
        useChatStore.getState().setChatMessages(targetChatId, updated);
        useChatStore.getState().setIsGeneratingForChat(targetChatId, false);
        setAbortController(null);
        return;
      }
      
      if (data.clear) {
        const updated = (useChatStore.getState().messagesByChat[String(targetChatId)] || []).map(m => 
          m.message_id === aiMsgId ? { ...m, content: '', timeToFirstToken: null } : m
        );
        useChatStore.getState().setChatMessages(targetChatId, updated);
        return;
      }

      if (data.replace_all) {
        const updated = (useChatStore.getState().messagesByChat[String(targetChatId)] || []).map(m => 
          m.message_id === aiMsgId ? { ...m, content: data.replace_all, isGenerating: !data.done } : m
        );
        useChatStore.getState().setChatMessages(targetChatId, updated);
        if (data.done) {
          useChatStore.getState().setIsGeneratingForChat(targetChatId, false);
          setAbortController(null);
        }
        return;
      } else if (data.chunk) {
        const currentMessages = useChatStore.getState().messagesByChat[String(targetChatId)] || [];
        const exists = currentMessages.some(m => m.message_id === data.message_id);
        
        let updated;
        if (exists) {
          updated = currentMessages.map(m => 
            m.message_id === data.message_id 
              ? { ...m, content: m.content + data.chunk, isGenerating: true } 
              : m
          );
        } else {
          // If we receive a chunk but have no AI message (e.g. in another tab), create it!
          updated = [...currentMessages, {
            role: 'assistant',
            content: data.chunk,
            message_id: data.message_id,
            isGenerating: true,
            persona_id: useChatStore.getState().selectedPersonaId,
            startTime: Date.now()
          }];
        }
        useChatStore.getState().setChatMessages(targetChatId, updated);
      }
      
      if (data.done) {
        const updated = (useChatStore.getState().messagesByChat[String(targetChatId)] || []).map(m => 
          m.message_id === aiMsgId || m.message_id === data.message_id ? { ...m, isGenerating: false } : m
        );
        useChatStore.getState().setChatMessages(targetChatId, updated);
        useChatStore.getState().setIsGeneratingForChat(targetChatId, false);
        setAbortController(null);
      }
    };

    ws.onerror = () => {
      // Don't auto-fail generating on error, because backend might still be generating
    };

    ws.onclose = () => {
      // Backend handles generation decoupling.
    };

    return ws;
  };

  useEffect(() => {
    if (chatId && chatId !== 'temp') {
      const nextChat = useChatStore.getState().chats.find(c => String(c.chat_id) === String(chatId));
      const currentlyGeneratingLocally = !!useChatStore.getState().isGeneratingByChat[String(chatId)];
      if (!currentlyGeneratingLocally) {
        useChatStore.getState().setIsGeneratingForChat(chatId, nextChat ? !!nextChat.is_generating : false);
      }
      connectWs(chatId);
    } else {
      useChatStore.getState().setIsGeneratingForChat(chatId, false);
    }
    return () => {
      if (wsRef.current && wsRef.current.chatId === String(chatId)) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [chatId]);

  const user = useAuthStore(state => state.user);

  useEffect(() => {
    if ((!chatId || chatId === 'temp') && user?.default_persona_id) {
      setSelectedPersonaId(user.default_persona_id);
    }
  }, [chatId, user, setSelectedPersonaId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isGenerating) return;
    
    const messageToSend = inputMessage;
    setInputMessage('');
    
    let activeChatId = chatId;
    const isTemp = !activeChatId || activeChatId === 'temp';
    if (isTemp) {
      activeChatId = 'temp';
      navigate(`/app/chat/temp`);
    }

    const generateUUID = () => {
      if (typeof crypto !== 'undefined' && crypto.randomUUID) {
        return crypto.randomUUID();
      }
      return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
      });
    };

    const clientMsgId = generateUUID();
    const userMsg = { role: 'user', content: messageToSend, message_id: clientMsgId };
    
    useChatStore.getState().addChatMessage(activeChatId, userMsg);
    useChatStore.getState().setIsGeneratingForChat(activeChatId, true);
    
    const aiMsgId = generateUUID();
    useChatStore.getState().addChatMessage(activeChatId, { 
      role: 'assistant', 
      content: '', 
      message_id: aiMsgId, 
      isGenerating: true, 
      persona_id: useChatStore.getState().selectedPersonaId,
      timeToFirstToken: null 
    });
    
    // Optimistically set generation status in chats list
    const currentChats = useChatStore.getState().chats;
    useChatStore.setState({
      chats: currentChats.map(c => String(c.chat_id) === String(activeChatId) ? { ...c, is_generating: true } : c)
    });

    const controller = new AbortController();
    setAbortController(controller);

    try {
      if (isTemp) {
        const { data } = await api.post('/chats/', {
          persona_id: useChatStore.getState().selectedPersonaId
        });
        activeChatId = String(data.chat_id);
        
        // Move messages from 'temp' to activeChatId in the store cache
        const tempMessages = useChatStore.getState().messagesByChat['temp'] || [];
        useChatStore.getState().setChatMessages(activeChatId, tempMessages);
        useChatStore.getState().setChatMessages('temp', []);
        useChatStore.getState().setIsGeneratingForChat(activeChatId, true);
        useChatStore.getState().setIsGeneratingForChat('temp', false);
        
        setChats([data, ...chats]);
        setCurrentChat(data);
        setGeneratingTitleChatId(activeChatId);
        navigate(`/app/chat/${activeChatId}`, { replace: true });
      }

      const ws = connectWs(activeChatId);

      const sendPayload = () => {
        ws.send(JSON.stringify({
          message: messageToSend,
          client_message_id: clientMsgId,
          ai_message_id: aiMsgId,
          model_preference: model,
          persona_id: useChatStore.getState().selectedPersonaId,
          mode: "normal",
        }));
      };

      if (ws.readyState === WebSocket.OPEN) {
        sendPayload();
      } else {
        ws.addEventListener('open', sendPayload, { once: true });
      }

    } catch (err) {
      useChatStore.getState().setIsGeneratingForChat(activeChatId, false);
      setAbortController(null);
    }
  };

  const handleStop = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "stop" }));
    }
    useChatStore.getState().setIsGeneratingForChat(chatId, false);
    
    // Mark generating message bubble as finalized locally
    const currentMsgs = useChatStore.getState().messagesByChat[String(chatId)] || [];
    const updated = currentMsgs.map(m => m.isGenerating ? { ...m, isGenerating: false } : m);
    useChatStore.getState().setChatMessages(chatId, updated);

    setAbortController(null);
    const currentChats = useChatStore.getState().chats;
    useChatStore.setState({
      chats: currentChats.map(c => String(c.chat_id) === String(chatId) ? { ...c, is_generating: false } : c)
    });
  };

  const models = [
    { id: '2', label: 'Fast', icon: Zap, description: 'Quick responses' },
    { id: '1', label: 'Thinking', icon: Sparkles, description: 'Deeper reasoning' },
  ];
  const activeModel = models.find(m => m.id === model) || models[0];
  const ActiveIcon = activeModel.icon;

  const personaTones = {
    aman: 'Warm & funny friend',
    tariq: 'Calm wise mentor',
    layla: 'Professional counselor',
  };
  const personaNames = {
    aman: 'Aman',
    tariq: 'Tariq',
    layla: 'Layla'
  };
  const activePersona = personas.find(p => p.id === selectedPersonaId) || personas[0];
  const activePersonaName = activePersona?.name || personaNames[selectedPersonaId] || 'Aman';

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
          placeholder={`Message ${activePersonaName}...`}
          disabled={isGenerating}
          className="flex-1 bg-transparent border-none outline-none text-slate-700 dark:text-slate-100 placeholder:text-slate-400 py-3 px-3 disabled:opacity-50 font-medium text-[15px]"
        />
        
        {isGenerating ? (
          <button type="button" onClick={handleStop} className="p-2 bg-slate-800 dark:bg-white text-white dark:text-slate-800 rounded-full hover:opacity-80 transition-all flex-shrink-0">
            <Square size={16} className="fill-current" />
          </button>
        ) : (
          <div className="flex items-center gap-1.5 flex-shrink-0">
            {chatId !== 'temp' && <VoiceModeButton chatId={chatId || 'new'} />}
            <button type="submit" disabled={!inputMessage.trim()} className="p-2 bg-slate-800 dark:bg-white text-white dark:text-slate-800 rounded-full transition-all disabled:opacity-30 disabled:cursor-not-allowed hover:bg-slate-700 active:scale-90">
              <ArrowUp size={16} strokeWidth={2.5} />
            </button>
          </div>
        )}
      </form>

      {/* Bottom toolbar row */}
      <div className="flex items-center justify-between px-3 pb-1 pt-0.5">
        <div className="flex items-center gap-1">
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

          {/* Persona selector (right of model) */}
          <div className="relative" ref={personaRef}>
            <button 
              type="button"
              onClick={() => setPersonaMenuOpen(!personaMenuOpen)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold text-slate-500 hover:text-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all"
            >
              <User size={13} className="text-aman-primary" />
              {activePersonaName}
            </button>

            {personaMenuOpen && (
              <div className="absolute bottom-full left-0 mb-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-2xl shadow-xl overflow-hidden w-56 z-50">
                {personas.map(p => (
                  <button
                    key={p.id}
                    onClick={() => { setSelectedPersonaId(p.id); setPersonaMenuOpen(false); }}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left text-sm transition-colors ${selectedPersonaId === p.id ? 'bg-aman-primary/10 text-aman-primary font-semibold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800'}`}
                  >
                    <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${selectedPersonaId === p.id ? 'bg-aman-primary text-white' : 'bg-slate-100 dark:bg-slate-800 text-slate-400'}`}>
                      {p.name.charAt(0)}
                    </div>
                    <div>
                      <div className="font-medium">{p.name}</div>
                      <div className="text-[10px] text-slate-400 font-normal">{personaTones[p.id] || p.description?.slice(0, 30)}</div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
