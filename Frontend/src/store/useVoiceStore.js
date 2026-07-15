import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useVoiceStore = create(
  persist(
    (set) => ({
      isOpen: false,
      voiceId: 'en_emma',
      modelPreference: '2', // '2' for Fast, '1' for Thinking
      personaId: 'aman',
      preferredLanguage: 'auto', // 'auto' | 'ar' | 'en'

      setIsOpen: (isOpen) => set({ isOpen }),
      setVoiceId: (voiceId) => set({ voiceId }),
      setModelPreference: (modelPreference) => set({ modelPreference }),
      setPersonaId: (personaId) => set({ personaId }),
      setPreferredLanguage: (preferredLanguage) => set({ preferredLanguage }),
      
      reset: () => set({
        isOpen: false,
        voiceId: 'en_emma',
        modelPreference: '2',
        personaId: 'aman',
        preferredLanguage: 'auto'
      })
    }),
    {
      name: 'aman-voice-settings',
      partialize: (state) => ({
        voiceId: state.voiceId,
        modelPreference: state.modelPreference,
        personaId: state.personaId,
        preferredLanguage: state.preferredLanguage
      }),
    }
  )
);
