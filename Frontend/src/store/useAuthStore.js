import { create } from 'zustand';
import api from '../api/axios';

export const useAuthStore = create((set, get) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access'),
  needsOnboarding: false,
  setNeedsOnboarding: (val) => set({ needsOnboarding: val }),
  login: (access, refresh, user) => {
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
    set({ isAuthenticated: true, user });
  },
  updateUser: (user) => {
    set({ user });
  },
  fetchUser: async () => {
    try {
      if (get().isAuthenticated) {
        const { data } = await api.get('/users/me/');
        set({ user: data });
      }
    } catch (err) {
      console.error('Failed to fetch user', err);
    }
  },
  logout: () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    set({ isAuthenticated: false, user: null });
  },
}));
