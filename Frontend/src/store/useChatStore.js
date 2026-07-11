import { create } from 'zustand';

export const useChatStore = create((set) => ({
  chats: [],
  currentChat: null,
  messagesByChat: {}, // { [chatId]: [...] }
  isGeneratingByChat: {}, // { [chatId]: boolean }
  generationStartedAt: {}, // { [chatId]: timestamp }
  model: '1', // Default: thinking model
  inputMessage: '',
  triggerSend: false,
  generatingTitleChatId: null, // Track which chat is waiting for a title
  selectedPersonaId: 'aman',
  personas: [],
  
  setSelectedPersonaId: (id) => set({ selectedPersonaId: id }),
  setPersonas: (personas) => set({ personas }),
  setInputMessage: (inputMessage) => set({ inputMessage }),
  setTriggerSend: (triggerSend) => set({ triggerSend }),
  setChats: (chats) => set({ chats }),
  setCurrentChat: (currentChat) => set({ currentChat }),
  setModel: (model) => set({ model }),
  setGeneratingTitleChatId: (id) => set({ generatingTitleChatId: id }),
  
  // Cache Management Actions
  setChatMessages: (chatId, messages) => set((state) => ({
    messagesByChat: {
      ...state.messagesByChat,
      [String(chatId)]: messages
    }
  })),
  
  addChatMessage: (chatId, message) => set((state) => {
    const existing = state.messagesByChat[String(chatId)] || [];
    return {
      messagesByChat: {
        ...state.messagesByChat,
        [String(chatId)]: [...existing, message]
      }
    };
  }),
  
  setIsGeneratingForChat: (chatId, isGenerating) => set((state) => ({
    isGeneratingByChat: {
      ...state.isGeneratingByChat,
      [String(chatId)]: isGenerating
    },
    generationStartedAt: isGenerating ? {
      ...state.generationStartedAt,
      [String(chatId)]: Date.now()
    } : state.generationStartedAt
  })),
  
  updateChatTitle: (chatId, title) => set((state) => {
    const isCurrent = state.currentChat && String(state.currentChat.chat_id) === String(chatId);
    return {
      chats: state.chats.map(c => String(c.chat_id) === String(chatId) ? { ...c, title } : c),
      currentChat: isCurrent ? { ...state.currentChat, title } : state.currentChat,
      generatingTitleChatId: String(state.generatingTitleChatId) === String(chatId) ? null : state.generatingTitleChatId,
    };
  }),
  
  removeChat: (chatId) => set((state) => {
    const isCurrent = state.currentChat && String(state.currentChat.chat_id) === String(chatId);
    const newMessagesByChat = { ...state.messagesByChat };
    delete newMessagesByChat[String(chatId)];
    const newIsGeneratingByChat = { ...state.isGeneratingByChat };
    delete newIsGeneratingByChat[String(chatId)];
    
    return {
      chats: state.chats.filter(c => String(c.chat_id) !== String(chatId)),
      currentChat: isCurrent ? null : state.currentChat,
      messagesByChat: newMessagesByChat,
      isGeneratingByChat: newIsGeneratingByChat
    };
  }),
  
  clearAllMessages: () => set({ messagesByChat: {}, isGeneratingByChat: {} }),
}));
