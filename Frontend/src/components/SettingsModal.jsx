import React, { useState, useEffect } from 'react';
import { X, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useChatStore } from '../store/useChatStore';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';

export default function SettingsModal({ onClose }) {
  const [activeTab, setActiveTab] = useState('Account');
  const { user, updateUser, logout } = useAuthStore();
  const { setChats, setMessages, setCurrentChat } = useChatStore();
  const { personas } = useChatStore();
  const navigate = useNavigate();

  // Form States
  const [accountData, setAccountData] = useState({
    name: user?.name || '',
    birthdate: user?.birthdate || '',
    gender: user?.gender || 'female',
    country: user?.country || 'US'
  });
  const [prefsData, setPrefsData] = useState({
    theme: user?.theme || 'light',
    language: user?.language || 'en',
    default_persona_id: user?.default_persona_id || 'aman'
  });
  const [securityData, setSecurityData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null); // { type: 'success' | 'error', text: '' }

  // Sync data when user loads
  useEffect(() => {
    if (user) {
      setAccountData({
        name: user.name || '',
        birthdate: user.birthdate || '',
        gender: user.gender || 'female',
        country: user.country || 'US'
      });
      setPrefsData({
        theme: user.theme || 'light',
        language: user.language || 'en',
        default_persona_id: user.default_persona_id || 'aman'
      });
    }
  }, [user]);

  // Handlers
  const handleAccountChange = (e) => setAccountData({ ...accountData, [e.target.name]: e.target.value });
  const handlePrefsChange = (e) => setPrefsData({ ...prefsData, [e.target.name]: e.target.value });
  const handleSecurityChange = (e) => setSecurityData({ ...securityData, [e.target.name]: e.target.value });

  const applyTheme = (themeStr) => {
    if (themeStr === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const handleSaveAccount = async () => {
    setLoading(true); setMessage(null);
    try {
      const { data } = await api.put('/users/me/', accountData);
      updateUser(data);
      setMessage({ type: 'success', text: 'Account updated successfully.' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update account.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSavePrefs = async () => {
    setLoading(true); setMessage(null);
    try {
      const { data } = await api.put('/users/me/', prefsData);
      updateUser(data);
      applyTheme(data.theme);
      setMessage({ type: 'success', text: 'Preferences updated successfully.' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update preferences.' });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSecurity = async () => {
    if (securityData.new_password !== securityData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match.' });
      return;
    }
    setLoading(true); setMessage(null);
    try {
      await api.post('/users/change-password/', {
        old_password: securityData.old_password,
        new_password: securityData.new_password
      });
      setMessage({ type: 'success', text: 'Password changed successfully.' });
      setSecurityData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      const detail = err.response?.data?.old_password?.[0] || err.response?.data?.new_password?.[0] || 'Failed to change password.';
      setMessage({ type: 'error', text: detail });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMemory = async () => {
    if (!window.confirm("Are you sure you want to delete Aman's long-term memory of you? Your chats will remain intact, but Aman will forget any learned facts.")) return;
    setLoading(true); setMessage(null);
    try {
      await api.delete('/chats/memory/');
      setMessage({ type: 'success', text: 'AI long-term memory cleared successfully.' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to clear memory.' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteHistory = async () => {
    if (!window.confirm("Are you sure you want to delete all chat history and memory? This action cannot be undone.")) return;
    setLoading(true); setMessage(null);
    try {
      await api.delete('/chats/history/');
      setChats([]);
      setMessages([]);
      setCurrentChat(null);
      navigate('/app');
      setMessage({ type: 'success', text: 'Chat history and memory cleared.' });
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to clear history.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center px-4 bg-black/40 backdrop-blur-sm animate-in fade-in" onClick={onClose}>
      <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-3xl overflow-hidden shadow-2xl border border-slate-200 dark:border-slate-800" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
          <h2 className="text-lg font-bold text-slate-800 dark:text-white">Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800">
            <X size={18} />
          </button>
        </div>

        {/* Content Tabs */}
        <div className="px-6 py-2 flex gap-6 border-b border-slate-100 dark:border-slate-800 text-sm font-medium bg-slate-50/50 dark:bg-slate-900/50">
          {['Account', 'Preferences', 'Security'].map(tab => (
            <button 
              key={tab}
              onClick={() => { setActiveTab(tab); setMessage(null); }}
              className={`py-2 transition-colors ${activeTab === tab ? 'text-aman-primary border-b-2 border-aman-primary' : 'text-slate-400 hover:text-slate-700 dark:hover:text-white'}`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Form Body */}
        <div className="px-6 py-6 max-h-[60vh] overflow-y-auto">
          
          {message && (
            <div className={`p-3 mb-6 rounded-2xl text-sm font-medium flex items-start gap-2 animate-in slide-in-from-top-2 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100 dark:bg-green-900/30 dark:text-green-400 dark:border-green-900/50' : 'bg-red-50 text-red-600 border border-red-100 dark:bg-red-900/30 dark:text-red-400 dark:border-red-900/50'}`}>
              {message.type === 'success' ? <CheckCircle2 size={18} className="shrink-0 mt-0.5" /> : <AlertCircle size={18} className="shrink-0 mt-0.5" />}
              <span>{message.text}</span>
            </div>
          )}

          {activeTab === 'Account' && (
            <div className="space-y-4">
              <div className="flex flex-col items-center gap-3 mb-6">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-aman-primary to-aman-tertiary flex items-center justify-center text-3xl text-white font-bold shadow-md">
                  {user?.name?.[0]?.toUpperCase() || 'A'}
                </div>
                <div className="text-sm font-medium text-slate-500">{user?.email}</div>
              </div>
              
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-slate-500 mb-1 ml-1 uppercase tracking-wider">Name</label>
                  <input type="text" name="name" value={accountData.name} onChange={handleAccountChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all font-medium text-sm" />
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-slate-500 mb-1 ml-1 uppercase tracking-wider">Birthdate</label>
                  <input type="date" name="birthdate" value={accountData.birthdate} onChange={handleAccountChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all font-medium text-sm" />
                </div>
              </div>

              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-slate-500 mb-1 ml-1 uppercase tracking-wider">Gender</label>
                  <select name="gender" value={accountData.gender} onChange={handleAccountChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all font-medium text-sm">
                    <option value="female">Female</option>
                    <option value="male">Male</option>
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-slate-500 mb-1 ml-1 uppercase tracking-wider">Country</label>
                  <input type="text" name="country" maxLength={2} value={accountData.country} onChange={handleAccountChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all font-medium text-sm" />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'Preferences' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-800">
                <span className="text-slate-700 dark:text-slate-200 font-medium text-sm">App Theme</span>
                <div className="flex items-center bg-slate-200/50 dark:bg-slate-900 rounded-full p-1 border border-slate-200 dark:border-slate-700">
                  <button onClick={() => setPrefsData({...prefsData, theme: 'light'})} className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${prefsData.theme === 'light' ? 'bg-white text-slate-800 shadow-sm dark:bg-slate-700 dark:text-white' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`}>Light</button>
                  <button onClick={() => setPrefsData({...prefsData, theme: 'dark'})} className={`px-4 py-1.5 rounded-full text-xs font-semibold transition-all ${prefsData.theme === 'dark' ? 'bg-white text-slate-800 shadow-sm dark:bg-slate-700 dark:text-white' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`}>Dark</button>
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-800">
                <span className="text-slate-700 dark:text-slate-200 font-medium text-sm">Language</span>
                <select name="language" value={prefsData.language} onChange={handlePrefsChange} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-full px-4 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-aman-primary shadow-sm">
                  <option value="en">English</option>
                  <option value="ar">العربية (Arabic)</option>
                  <option value="es">Español (Spanish)</option>
                </select>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-800">
                <div>
                  <span className="text-slate-700 dark:text-slate-200 font-medium text-sm">Default Companion</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">Used when starting new chats</p>
                </div>
                <select 
                  name="default_persona_id" 
                  value={prefsData.default_persona_id} 
                  onChange={handlePrefsChange} 
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-full px-4 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-aman-primary shadow-sm"
                >
                  {personas.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {activeTab === 'Security' && (
            <div className="space-y-6">
              
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-800 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-2">Change Password</h3>
                <div>
                  <input type="password" name="old_password" placeholder="Current Password" value={securityData.old_password} onChange={handleSecurityChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all text-sm mb-3" />
                  <input type="password" name="new_password" placeholder="New Password" value={securityData.new_password} onChange={handleSecurityChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all text-sm mb-3" />
                  <input type="password" name="confirm_password" placeholder="Confirm New Password" value={securityData.confirm_password} onChange={handleSecurityChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all text-sm" />
                  <p className="text-[11px] text-slate-400 mt-2 ml-1">Password must be at least 8 characters long.</p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
                <h3 className="text-sm font-bold text-red-600 dark:text-red-400">Danger Zone</h3>
                <div className="p-4 bg-orange-50 dark:bg-orange-900/10 border border-orange-100 dark:border-orange-900/30 rounded-2xl mb-3">
                  <p className="text-xs text-orange-700 dark:text-orange-400 mb-3 leading-relaxed">This will permanently delete Aman's long-term memory of you (learned facts, preferences), but keep your chat history intact.</p>
                  <button onClick={handleDeleteMemory} disabled={loading} className="w-full py-2.5 px-4 bg-orange-100 hover:bg-orange-200 dark:bg-orange-900/40 dark:hover:bg-orange-900/60 text-orange-700 dark:text-orange-300 rounded-xl text-sm font-bold transition-colors disabled:opacity-50">
                    Clear AI Memory Only
                  </button>
                </div>

                <div className="p-4 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-2xl">
                  <p className="text-xs text-red-700 dark:text-red-400 mb-3 leading-relaxed">This will permanently delete all your chats AND Aman's long-term memory of you.</p>
                  <button onClick={handleDeleteHistory} disabled={loading} className="w-full py-2.5 px-4 bg-red-100 hover:bg-red-200 dark:bg-red-900/40 dark:hover:bg-red-900/60 text-red-700 dark:text-red-300 rounded-xl text-sm font-bold transition-colors disabled:opacity-50">
                    Clear History & Memory
                  </button>
                </div>
              </div>

            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-3 bg-slate-50/50 dark:bg-slate-900/50">
          <button onClick={onClose} className="px-5 py-2 rounded-full text-sm font-semibold text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors">
            Close
          </button>
          {(activeTab === 'Account' || activeTab === 'Preferences' || activeTab === 'Security') && (
            <button 
              onClick={() => {
                if (activeTab === 'Account') handleSaveAccount();
                if (activeTab === 'Preferences') handleSavePrefs();
                if (activeTab === 'Security') handleSaveSecurity();
              }}
              disabled={loading}
              className="px-6 py-2 rounded-full text-sm font-bold text-white bg-aman-primary hover:bg-aman-primary/90 shadow-lg shadow-aman-primary/20 transition-all disabled:opacity-50 active:scale-95"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
