import React, { useState, useEffect } from 'react';
import { Outlet, useParams, useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import InputBar from '../components/InputBar';
import SettingsModal from '../components/SettingsModal';
import { Menu } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

export default function AppLayout() {
  const [showSettings, setShowSettings] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { chatId } = useParams();
  const navigate = useNavigate();
  const user = useAuthStore(state => state.user);
  const fetchUser = useAuthStore(state => state.fetchUser);

  useEffect(() => {
    const handleKeyDown = (e) => {
      // Don't intercept if user is typing in an input or textarea
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      
      const currentId = parseInt(chatId) || 1;
      
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        const nextId = Math.min(currentId + 1, 6);
        navigate(`/app/chat/${nextId}`);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        const prevId = Math.max(currentId - 1, 1);
        navigate(`/app/chat/${prevId}`);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [chatId, navigate]);

  useEffect(() => {
    if (!user) {
      fetchUser();
    }
  }, [user, fetchUser]);
  useEffect(() => {
    if (user?.theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
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
        
      </main>
      
      {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
    </div>
  );
}
