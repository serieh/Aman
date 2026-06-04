import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useChatStore } from '../store/useChatStore';
import api from '../api/axios';
import MessageBubble from '../components/MessageBubble';

export default function ChatRoom() {
  const { chatId } = useParams();
  const { messages, setMessages } = useChatStore();
  const scrollRef = useRef(null);
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(true);
  const prevChatIdRef = useRef(null);

  // Fetch History when navigating to a real chat
  useEffect(() => {
    if (!chatId || chatId === 'temp') return;
    
    // Only fetch history when switching to a different real chat
    if (prevChatIdRef.current === chatId) return;
    prevChatIdRef.current = chatId;

    const fetchHistory = async () => {
      try {
        const { data } = await api.get(`/chats/${chatId}/`);
        if (data.messages && data.messages.length > 0) {
          setMessages(data.messages);
        }
      } catch (err) {
        console.error("Failed to fetch chat history", err);
      }
    };
    
    // Only fetch if we don't already have optimistic messages for this chat
    const currentMsgs = useChatStore.getState().messages;
    const hasOptimisticMessages = currentMsgs.some(m => m.isGenerating);
    if (!hasOptimisticMessages) {
      fetchHistory();
    }
  }, [chatId, setMessages]);

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
