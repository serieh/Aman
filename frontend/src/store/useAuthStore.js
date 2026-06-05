import { create } from 'zustand';

export const useAuthStore = create((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access'),
  login: (access, refresh, user) => {
    localStorage.setItem('access', access);
    localStorage.setItem('refresh', refresh);
    set({ isAuthenticated: true, user });
  },
  updateUser: (user) => {
    set({ user });
  },
  logout: () => {
    localStorage.removeItem('access');
    localStorage.removeItem('refresh');
    set({ isAuthenticated: false, user: null });
  },
}));
