import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import InputBar from '../components/InputBar';
import SettingsModal from '../components/SettingsModal';
import { Menu } from 'lucide-react';
import { applyTheme } from '../utils/theme';
import { useAuthStore } from '../store/useAuthStore';

export default function AppLayout() {
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
  const chatId = location.pathname.split('/chat/')[1] || null;
  const user = useAuthStore(state => state.user);
  const fetchUser = useAuthStore(state => state.fetchUser);

  useEffect(() => {
    if (!user) {
      fetchUser();
    }
  }, [user, fetchUser]);

  useEffect(() => {
    applyTheme(user?.theme);
  }, [user?.theme]);

  return (
    <div className="flex h-screen w-full bg-aman-bg-light overflow-hidden relative">
      <Sidebar 
        isOpen={sidebarOpen} 
        setIsOpen={setSidebarOpen} 
        onOpenSettings={() => setShowSettings(true)} 
      />
      
      <main className={`flex-1 flex flex-col relative h-full transition-all duration-300 ${sidebarOpen ? 'md:ml-72' : 'ml-0'}`}>
        
        {/* Reopen sidebar toggle — shown only when sidebar is collapsed */}
        {!sidebarOpen && (
          <button 
            onClick={() => setSidebarOpen(true)}
            className="absolute top-5 left-5 z-20 p-2.5 bg-white/80 backdrop-blur-md border border-slate-200/50 rounded-full shadow-sm text-slate-600 hover:text-aman-primary hover:bg-white transition-all"
          >
            <Menu size={20} />
          </button>
        )}

        <Outlet />
        
        {/* Global Input Bar at bottom */}
        <div className="absolute bottom-0 left-0 right-0 px-4 md:px-0 flex justify-center pointer-events-none z-10 pb-5">
          <div className="w-full max-w-3xl pointer-events-auto">
            <InputBar chatId={chatId} />
          </div>
        </div>
      </main>
      
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  );
}
