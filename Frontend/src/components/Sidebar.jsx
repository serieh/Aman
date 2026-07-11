import React, { useEffect, useState } from 'react';
import { Plus, Settings, LogOut, PanelLeftClose, MessageSquare, Edit2, Trash2, Check, X } from 'lucide-react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useChatStore } from '../store/useChatStore';
import { useAuthStore } from '../store/useAuthStore';
import api from '../api/axios';

export default function Sidebar({ isOpen, setIsOpen, onOpenSettings }) {
  const navigate = useNavigate();
  const location = useLocation();
  const chatId = location.pathname.split('/chat/')[1] || null;
  const logout = useAuthStore(state => state.logout);
  const { chats, setChats, updateChatTitle, removeChat, generatingTitleChatId, setPersonas } = useChatStore();

  const [editingChatId, setEditingChatId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

  useEffect(() => {
    const fetchChats = async () => {
      try {
        const { data } = await api.get('/chats/');
        setChats(data);
      } catch (err) {
        console.error("Failed to fetch chats", err);
      }
    };
    const fetchPersonas = async () => {
      try {
        const { data } = await api.get('/personas/');
        setPersonas(data);
      } catch (err) {
        console.error("Failed to fetch personas", err);
      }
    };
    fetchChats();
    fetchPersonas();
  }, [setChats, setPersonas]);

  const handleNewChat = () => {
    navigate('/app');
    if (window.innerWidth < 768) setIsOpen(false);
  };

  const handleChatClick = (id) => {
    if (window.innerWidth < 768) setIsOpen(false);
  };

  const handleLogout = async () => {
    try {
      const refresh = localStorage.getItem('refresh');
      await api.post('/auth/logout/', { refresh });
    } catch (err) {
      console.error(err);
    } finally {
      logout();
      navigate('/login');
    }
  };

  const handleSaveTitle = async (id, e) => {
    e?.preventDefault();
    if (!editTitle.trim()) {
      setEditingChatId(null);
      return;
    }
    try {
      await api.patch(`/chats/${id}/`, { title: editTitle });
      updateChatTitle(id, editTitle);
    } catch (err) {
      console.error("Failed to rename", err);
    }
    setEditingChatId(null);
  };

  const handleDeleteChat = async (id, e) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await api.delete(`/chats/${id}/`);
      removeChat(id);
      if (String(chatId) === String(id)) {
        useChatStore.getState().setCurrentChat(null);
        navigate('/app');
      }
    } catch (err) {
      console.error("Failed to delete", err);
    }
  };
  
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
      
      <aside className={`fixed top-0 left-0 h-full w-72 bg-white dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 flex flex-col z-50 transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        
        {/* Header */}
        <div className="p-5 flex items-center justify-between border-b border-slate-100 dark:border-slate-800">
          <Link to="/" className="text-xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary tracking-tighter">Aman</Link>
          <button onClick={() => setIsOpen(false)} className="text-slate-400 hover:text-slate-700 transition-colors p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800" title="Close sidebar">
             <PanelLeftClose size={18} />
          </button>
        </div>
        
        {/* New Chat Button */}
        <div className="p-3">
          <button onClick={handleNewChat} className="w-full flex items-center gap-2.5 px-4 py-2.5 text-slate-700 dark:text-slate-200 rounded-xl font-semibold text-sm transition-all hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 hover:border-aman-primary/40">
            <Plus size={16} className="text-aman-primary" />
            New Chat
          </button>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto px-3 pt-2">
          <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-2 px-2">Recent</h3>
          <ul className="relative mt-1">
            {/* Sliding Indicator */}
            {(() => {
              const activeIndex = chats.findIndex(c => String(c.chat_id) === String(chatId));
              if (activeIndex === -1) return null;
              return (
                <div 
                  className="absolute left-0 right-0 h-[40px] bg-aman-primary/10 rounded-xl transition-transform duration-500 ease-[cubic-bezier(0.4,0,0.2,1)] pointer-events-none"
                  style={{ transform: `translateY(${activeIndex * 44}px)` }} 
                />
              );
            })()}
            {chats.map(chat => {
              const isGeneratingTitle = generatingTitleChatId === chat.chat_id;
              const displayTitle = (!chat.title || chat.title === 'Untitled Chat') && isGeneratingTitle;
              const isEditing = editingChatId === chat.chat_id;

              return (
                <li key={chat.chat_id} className="group relative h-[40px] mb-1">
                  <Link 
                    to={`/app/chat/${chat.chat_id}`} 
                    onClick={() => handleChatClick(chat.chat_id)}
                    className={`flex items-center h-full gap-2.5 px-3 rounded-xl text-sm transition-colors ${String(chatId) === String(chat.chat_id) ? 'text-aman-primary font-semibold' : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white font-medium'}`}
                  >
                    <MessageSquare size={14} className={String(chatId) === String(chat.chat_id) ? 'text-aman-primary flex-shrink-0' : 'text-slate-400 flex-shrink-0'} />
                    
                    {isEditing ? (
                      <div className="flex-1 flex items-center gap-1" onClick={(e) => e.preventDefault()}>
                        <input 
                          autoFocus
                          value={editTitle}
                          onChange={e => setEditTitle(e.target.value)}
                          onKeyDown={e => { if (e.key === 'Enter') handleSaveTitle(chat.chat_id, e); if (e.key === 'Escape') setEditingChatId(null); }}
                          className="flex-1 bg-white dark:bg-slate-800 text-sm border border-aman-primary rounded px-1.5 py-0.5 outline-none text-slate-700 dark:text-slate-200 min-w-0"
                        />
                        <button onClick={(e) => handleSaveTitle(chat.chat_id, e)} className="text-aman-primary hover:text-aman-tertiary flex-shrink-0">
                          <Check size={14} />
                        </button>
                        <button onClick={(e) => { e.preventDefault(); setEditingChatId(null); }} className="text-slate-400 hover:text-slate-600 flex-shrink-0">
                          <X size={14} />
                        </button>
                      </div>
                    ) : displayTitle ? (
                      <div className="flex-1 flex items-center gap-1.5 overflow-hidden pr-12">
                        <span className="text-xs bg-clip-text text-transparent bg-gradient-to-r from-aman-primary to-aman-tertiary font-bold animate-pulse tracking-wide truncate">
                          Generating title
                        </span>
                        <span className="flex gap-0.5 mt-0.5 flex-shrink-0">
                          <span className="w-1 h-1 bg-aman-primary rounded-full animate-bounce"></span>
                          <span className="w-1 h-1 bg-aman-tertiary rounded-full animate-bounce [animation-delay:0.15s]"></span>
                          <span className="w-1 h-1 bg-aman-primary rounded-full animate-bounce [animation-delay:0.3s]"></span>
                        </span>
                      </div>
                    ) : (
                      <div className="flex-1 flex items-center justify-between min-w-0 pr-12">
                        <span className="truncate">{chat.title || "Untitled Chat"}</span>
                        {chat.is_generating && (
                          <span className="flex h-2 w-2 relative flex-shrink-0 ml-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-aman-primary opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-aman-primary"></span>
                          </span>
                        )}
                      </div>
                    )}
                  </Link>

                  {/* Actions */}
                  {!isEditing && (
                    <div className="absolute right-2 top-1/2 -translate-y-1/2 hidden group-hover:flex items-center gap-0.5 bg-slate-100 dark:bg-slate-800/90 rounded-lg p-0.5 shadow-sm border border-slate-200 dark:border-slate-700 backdrop-blur-sm">
                      <button 
                        onClick={(e) => { 
                          e.preventDefault(); 
                          e.stopPropagation();
                          setEditTitle(chat.title || "Untitled Chat"); 
                          setEditingChatId(chat.chat_id); 
                        }}
                        className="p-1.5 text-slate-500 hover:text-aman-primary transition-colors rounded hover:bg-white dark:hover:bg-slate-700"
                        title="Rename"
                      >
                        <Edit2 size={13} />
                      </button>
                      <button 
                        onClick={(e) => handleDeleteChat(chat.chat_id, e)}
                        className="p-1.5 text-slate-500 hover:text-red-500 transition-colors rounded hover:bg-white dark:hover:bg-slate-700"
                        title="Delete"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  )}
                </li>
              );
            })}
            {chats.length === 0 && (
              <li className="text-sm text-slate-400 px-3 py-4 text-center italic">No conversations yet</li>
            )}
          </ul>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <button onClick={onOpenSettings} className="flex items-center justify-center w-9 h-9 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-500 hover:text-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors" title="Settings">
            <Settings size={16} />
          </button>
          <button onClick={() => setShowLogoutConfirm(true)} className="flex items-center justify-center w-9 h-9 rounded-lg text-red-500 hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-600 transition-colors" title="Log Out">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* Logout Confirmation Modal */}
      {showLogoutConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 backdrop-blur-sm animate-in fade-in" onClick={() => setShowLogoutConfirm(false)}>
          <div className="bg-white/80 dark:bg-slate-900/80 backdrop-blur-2xl w-full max-w-sm rounded-3xl p-6 shadow-2xl border border-slate-200/50 dark:border-slate-800/50 text-center animate-in zoom-in-95 duration-200" onClick={e => e.stopPropagation()}>
            <div className="w-12 h-12 rounded-full bg-red-50 dark:bg-red-950/50 flex items-center justify-center mx-auto mb-4 text-red-500">
              <LogOut size={22} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">Log Out</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6 leading-relaxed">Are you sure you want to log out of your Companion account?</p>
            <div className="flex gap-3">
              <button 
                onClick={() => setShowLogoutConfirm(false)}
                className="flex-1 py-2.5 rounded-full text-sm font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-850 transition-colors border border-slate-200/50 dark:border-slate-700/50"
              >
                Cancel
              </button>
              <button 
                onClick={handleLogout}
                className="flex-1 py-2.5 rounded-full text-sm font-bold text-white bg-red-500 hover:bg-red-600 transition-colors shadow-lg shadow-red-500/20 active:scale-95"
              >
                Log Out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
