import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useChatStore } from '../store/useChatStore';
import { useVoiceStore } from '../store/useVoiceStore';
import api from '../api/axios';
import MessageBubble from '../components/MessageBubble';

const EMPTY_ARRAY = [];

export default function ChatRoom() {
  const { chatId } = useParams();
  const messages = useChatStore(state => state.messagesByChat[String(chatId)] || EMPTY_ARRAY);
  const setChatMessages = useChatStore(state => state.setChatMessages);
  const isVoiceOpen = useVoiceStore(state => state.isOpen);
  const scrollRef = useRef(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(true);

  // Fetch History when navigating to a real chat
  useEffect(() => {
    let isCancelled = false;

    if (!chatId || chatId === 'temp') {
      useChatStore.getState().setCurrentChat(null);
      return;
    }

    // Set currentChat object from chats or temporary object
    const currentChat = useChatStore.getState().chats.find(c => String(c.chat_id) === String(chatId));
    if (currentChat) {
      useChatStore.getState().setCurrentChat(currentChat);
      if (currentChat.persona_id) {
        useChatStore.getState().setSelectedPersonaId(currentChat.persona_id);
      }
    } else {
      useChatStore.getState().setCurrentChat({ chat_id: chatId });
    }

    const fetchHistory = async () => {
      try {
        const { data } = await api.get(`/chats/${chatId}/`);
        if (isCancelled) return;
        
        useChatStore.getState().setCurrentChat(data);
        
        // Sync persona dropdown to this chat's last-used persona
        if (data.persona_id) {
          useChatStore.getState().setSelectedPersonaId(data.persona_id);
        }
        
        // Trust local state if we are currently generating. The websocket will send generation_status: false to unlock it.
        const isGeneratingDb = data.is_generating;
        const localIsGenerating = !!useChatStore.getState().isGeneratingByChat[String(chatId)];
        const isGenerating = isGeneratingDb || localIsGenerating;
        
        useChatStore.getState().setIsGeneratingForChat(chatId, isGenerating);
        
        const currentMsgs = useChatStore.getState().messagesByChat[String(chatId)] || [];
        const dbIds = new Set((data.messages || []).map(m => String(m.message_id)));
        
        // Filter for messages that exist locally but not yet in the DB (optimistic user/generating assistant messages)
        const optimisticMsgs = currentMsgs.filter(m => {
          if (dbIds.has(String(m.message_id))) return false;
          // Discard AI messages ONLY if we are definitely not generating
          if (!isGenerating && m.isGenerating) return false;
          return m.role === 'user' || m.isGenerating;
        });
        
        let newMessages = data.messages && data.messages.length > 0 ? data.messages : [];
        newMessages = [...newMessages, ...optimisticMsgs];
        
        setChatMessages(chatId, newMessages);
      } catch (err) {
        if (!isCancelled) {
          console.error("Failed to fetch chat history", err);
        }
      }
    };
    
    fetchHistory();

    return () => {
      isCancelled = true;
    };
  }, [chatId, setChatMessages, isVoiceOpen]);


  // Smart Auto-scrolling — triggers on every message change
  useEffect(() => {
    const scrollContainer = scrollRef.current;
    if (!scrollContainer || !isAutoScrollEnabled) return;
    scrollContainer.scrollTop = scrollContainer.scrollHeight;
  }, [messages, isAutoScrollEnabled]);

  const handleScroll = (e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    const isAtBottom = (scrollHeight - scrollTop - clientHeight) < 150;
    setIsAutoScrollEnabled(isAtBottom);
  };

  return (
    <div className="flex-1 flex flex-col h-full aman-gradient-bg overflow-hidden">
      <div 
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 md:px-8"
      >
        {/* Top spacing */}
        <div className="h-6" />

        <div className="space-y-5">
          {messages.map((msg, i) => (
            <MessageBubble key={msg.message_id || i} message={msg} isGenerating={msg.isGenerating} />
          ))}
        </div>

        {/* Bottom spacer — clears the floating input bar */}
        <div className="h-44 w-full flex-shrink-0" />
      </div>
    </div>
  );
}
