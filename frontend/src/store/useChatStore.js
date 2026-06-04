import { create } from 'zustand';

export const useChatStore = create((set) => ({
  chats: [],
  currentChat: null,
  messages: [],
  model: '2', // Default: fast model
  inputMessage: '',
  triggerSend: false,
  generatingTitleChatId: null, // Track which chat is waiting for a title
  setInputMessage: (inputMessage) => set({ inputMessage }),
  setTriggerSend: (triggerSend) => set({ triggerSend }),
  setChats: (chats) => set({ chats }),
  setCurrentChat: (currentChat) => set({ currentChat }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
  setModel: (model) => set({ model }),
  setGeneratingTitleChatId: (id) => set({ generatingTitleChatId: id }),
  updateChatTitle: (chatId, title) => set((state) => ({
    chats: state.chats.map(c => c.chat_id === chatId ? { ...c, title } : c),
    generatingTitleChatId: state.generatingTitleChatId === chatId ? null : state.generatingTitleChatId,
  })),
}));
