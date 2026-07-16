import { create } from 'zustand';
import api from '../api/axios';

// Helper to apply HTML attributes
export function applyLanguage(lang) {
  if (typeof document === 'undefined') return;
  const currentLang = lang === 'ar' ? 'ar' : 'en';
  document.documentElement.dir = currentLang === 'ar' ? 'rtl' : 'ltr';
  document.documentElement.lang = currentLang;
}

// Initial application of language
const initialLang = localStorage.getItem('aman-lang-pref') || 'en';
applyLanguage(initialLang);

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access'),
  needsOnboarding: false,
  language: initialLang,
  setNeedsOnboarding: (val) => set({ needsOnboarding: val }),
  
  login: (access, refresh, user) => {
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
    
    // Sync language preference if returned in user profile
    let lang = get().language;
    if (user && user.language) {
      lang = user.language;
      localStorage.setItem('aman-lang-pref', lang);
      applyLanguage(lang);
    }
    
    set({ isAuthenticated: true, user, language: lang });
  },

  updateUser: (user) => {
    let nextLang = get().language;
    if (user && user.language) {
      nextLang = user.language;
      localStorage.setItem('aman-lang-pref', nextLang);
      applyLanguage(nextLang);
    }
    set({ user, language: nextLang });
  },

  fetchUser: async () => {
    try {
      if (get().isAuthenticated) {
        const { data } = await api.get('/users/me/');
        
        let nextLang = get().language;
        if (data && data.language) {
          nextLang = data.language;
          localStorage.setItem('aman-lang-pref', nextLang);
          applyLanguage(nextLang);
        }
        
        set({ user: data, language: nextLang });
      }
    } catch (err) {
      console.error('Failed to fetch user', err);
    }
  },

  setLanguage: async (lang) => {
    const nextLang = lang === 'ar' ? 'ar' : 'en';
    
    // 1. Update client-side state
    localStorage.setItem('aman-lang-pref', nextLang);
    applyLanguage(nextLang);
    set({ language: nextLang });
    
    // 2. Only push to backend if authenticated and user object is fetched
    if (get().isAuthenticated && get().user) {
      try {
        const { data } = await api.put('/users/me/', { language: nextLang });
        set({ user: data });
      } catch (err) {
        console.error('Failed to sync language preference with backend', err);
        // Retain local state but print warning (offline support)
      }
    }
  },

  logout: () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    // We retain the local storage 'aman-lang-pref' so the visitor retains their preferred lang
    set({ isAuthenticated: false, user: null });
  },
}));
