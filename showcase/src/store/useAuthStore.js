import { create } from 'zustand';

export const useAuthStore = create((set, get) => ({
  user: { id: 1, name: 'John Halo', email: 'johnhalo@microslop.com', theme: 'dark' },
  isAuthenticated: !!localStorage.getItem('access'),
  login: (access, refresh, user) => {
    localStorage.setItem('access', access || 'fake_access');
    set({ isAuthenticated: true });
  },
  updateUser: (user) => {
    set({ user });
  },
  fetchUser: async () => {
    // mock fetch
    if (get().isAuthenticated) {
      set({ user: { id: 1, name: 'John Halo', email: 'johnhalo@microslop.com', theme: 'dark' } });
    }
  },
  logout: () => {
    localStorage.removeItem('access');
    set({ isAuthenticated: false });
  },
}));
