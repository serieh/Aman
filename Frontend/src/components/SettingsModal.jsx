import React, { useState, useEffect } from 'react';
import { X, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useChatStore } from '../store/useChatStore';
import { useTranslation } from '../hooks/useTranslation';
import api from '../api/axios';
import { useNavigate } from 'react-router-dom';
import { applyTheme } from '../utils/theme';

export default function SettingsModal({ onClose }) {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('Account');
  const { user, updateUser } = useAuthStore();
  const { setChats, setMessages, setCurrentChat } = useChatStore();
  const { personas } = useChatStore();
  const navigate = useNavigate();

  const parseTheme = (themeStr) => {
    const val = themeStr || 'sunrise-light';
    const parts = val.split('-');
    return {
      name: parts[0] || 'sunrise',
      mode: parts[1] || 'light'
    };
  };

  const initialParsed = parseTheme(user?.theme);
  const [selectedTheme, setSelectedTheme] = useState(initialParsed.name);
  const [selectedMode, setSelectedMode] = useState(initialParsed.mode);

  // Preview theme changes dynamically
  useEffect(() => {
    applyTheme(`${selectedTheme}-${selectedMode}`);
  }, [selectedTheme, selectedMode]);

  // Revert back to original saved theme on unmount if not saved
  useEffect(() => {
    return () => {
      const currentUser = useAuthStore.getState().user;
      if (currentUser?.theme) {
        applyTheme(currentUser.theme);
      }
    };
  }, []);

  // Form States
  const [accountData, setAccountData] = useState({
    name: user?.name || '',
    birthdate: user?.birthdate || '',
    gender: user?.gender || 'female',
    country: user?.country || 'US'
  });
  const [prefsData, setPrefsData] = useState({
    theme: user?.theme || 'sunrise-light',
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
        theme: user.theme || 'sunrise-light',
        language: user.language || 'en',
        default_persona_id: user.default_persona_id || 'aman'
      });
      const parsed = parseTheme(user.theme);
      setSelectedTheme(parsed.name);
      setSelectedMode(parsed.mode);
    }
  }, [user]);

  // Handlers
  const handleAccountChange = (e) => setAccountData({ ...accountData, [e.target.name]: e.target.value });
  const handlePrefsChange = (e) => setPrefsData({ ...prefsData, [e.target.name]: e.target.value });
  const handleSecurityChange = (e) => setSecurityData({ ...securityData, [e.target.name]: e.target.value });

  const handleSaveAccount = async () => {
    setLoading(true); setMessage(null);
    try {
      const { data } = await api.put('/users/me/', accountData);
      updateUser(data);
      setMessage({ type: 'success', text: t('msg_account_success') });
    } catch (err) {
      setMessage({ type: 'error', text: t('msg_account_error') });
    } finally {
      setLoading(false);
    }
  };

  const handleSavePrefs = async () => {
    setLoading(true); setMessage(null);
    try {
      const payload = {
        ...prefsData,
        theme: `${selectedTheme}-${selectedMode}`
      };
      
      // Update database and state for the theme & companion settings
      const { data } = await api.put('/users/me/', payload);
      updateUser(data);
      applyTheme(data.theme);
      
      // Call setLanguage to update language state, local storage, HTML attributes, and DB language preference
      const setLanguageStore = useAuthStore.getState().setLanguage;
      await setLanguageStore(prefsData.language);
      
      setMessage({ type: 'success', text: t('msg_prefs_success') });
    } catch (err) {
      setMessage({ type: 'error', text: t('msg_prefs_error') });
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSecurity = async () => {
    if (securityData.new_password !== securityData.confirm_password) {
      setMessage({ type: 'error', text: t('msg_pass_mismatch') });
      return;
    }
    setLoading(true); setMessage(null);
    try {
      await api.post('/users/change-password/', {
        old_password: securityData.old_password,
        new_password: securityData.new_password
      });
      setMessage({ type: 'success', text: t('msg_pass_success') });
      setSecurityData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      const detail = err.response?.data?.old_password?.[0] || err.response?.data?.new_password?.[0] || t('msg_account_error');
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
      setMessage({ type: 'success', text: t('msg_memory_success') });
    } catch (err) {
      setMessage({ type: 'error', text: t('msg_memory_error') });
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
      setMessage({ type: 'success', text: t('msg_history_success') });
    } catch (err) {
      setMessage({ type: 'error', text: t('msg_history_error') });
    } finally {
      setLoading(false);
    }
  };

  const tabNames = {
    Account: t('tab_account'),
    Preferences: t('tab_preferences'),
    Security: t('tab_security')
  };

  const personaNames = {
    aman: t('persona_name_aman'),
    tariq: t('persona_name_tariq'),
    layla: t('persona_name_layla')
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center px-4 bg-black/40 backdrop-blur-sm animate-in fade-in" onClick={onClose}>
      <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-3xl overflow-hidden shadow-2xl border border-slate-200 dark:border-slate-800" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50/50 dark:bg-slate-900/50">
          <h2 className="text-lg font-bold text-slate-800 dark:text-white text-start">{t('settings')}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors p-1.5 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-800 cursor-pointer" title={t('close')}>
            <X size={18} />
          </button>
        </div>

        {/* Content Tabs */}
        <div className="px-6 py-2 flex gap-6 border-b border-slate-100 dark:border-slate-800 text-sm font-medium bg-slate-50/50 dark:bg-slate-900/50">
          {['Account', 'Preferences', 'Security'].map(tab => (
            <button 
              key={tab}
              onClick={() => { setActiveTab(tab); setMessage(null); }}
              className={`py-2 transition-colors cursor-pointer ${activeTab === tab ? 'text-aman-primary border-b-2 border-aman-primary' : 'text-slate-400 hover:text-slate-700 dark:hover:text-white'}`}
            >
              {tabNames[tab]}
            </button>
          ))}
        </div>

        {/* Form Body */}
        <div className="px-6 py-6 max-h-[60vh] overflow-y-auto">
          
          {message && (
            <div className={`p-3 mb-6 rounded-2xl text-sm font-medium flex items-start gap-2 animate-in slide-in-from-top-2 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-100 dark:bg-green-900/30 dark:text-green-400 dark:border-green-900/50' : 'bg-red-50 text-red-600 border border-red-100 dark:bg-red-900/30 dark:text-red-400 dark:border-red-900/50'}`}>
              {message.type === 'success' ? <CheckCircle2 size={18} className="shrink-0 mt-0.5" /> : <AlertCircle size={18} className="shrink-0 mt-0.5" />}
              <span className="text-start">{message.text}</span>
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
                  <label className="block text-xs font-semibold text-slate-500 mb-1 ml-1 uppercase tracking-wider text-start">{t('fullname')}</label>
                  <input type="text" name="name" value={accountData.name} onChange={handleAccountChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all font-medium text-sm text-start" />
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-slate-500 mb-1 ml-1 uppercase tracking-wider text-start">{t('birthdate')}</label>
                  <input type="date" name="birthdate" value={accountData.birthdate} onChange={handleAccountChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all font-medium text-sm text-start" />
                </div>
              </div>

              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-slate-500 mb-1 ml-1 uppercase tracking-wider text-start">{t('gender')}</label>
                  <select name="gender" value={accountData.gender} onChange={handleAccountChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all font-medium text-sm text-start capitalize">
                    <option value="female">{t('gender_female')}</option>
                    <option value="male">{t('gender_male')}</option>
                  </select>
                </div>
                <div className="flex-1">
                  <label className="block text-xs font-semibold text-slate-500 mb-1 ml-1 uppercase tracking-wider text-start">{t('country')}</label>
                  <input type="text" name="country" maxLength={2} value={accountData.country} onChange={handleAccountChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all font-medium text-sm text-start" />
                </div>
              </div>
            </div>
          )}

          {activeTab === 'Preferences' && (
            <div className="space-y-5">
              {/* Dark vs Light Mode Toggle */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-2 ml-1 uppercase tracking-wider text-start">{t('appearance')}</label>
                <div className="flex items-center bg-slate-100 dark:bg-slate-800/80 rounded-2xl p-1 border border-slate-200/50 dark:border-slate-700/50">
                  <button 
                    type="button"
                    onClick={() => setSelectedMode('light')} 
                    className={`flex-1 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer ${selectedMode === 'light' ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`}
                  >
                    {t('light_mode')}
                  </button>
                  <button 
                    type="button"
                    onClick={() => setSelectedMode('dark')} 
                    className={`flex-1 py-2 rounded-xl text-sm font-semibold transition-all cursor-pointer ${selectedMode === 'dark' ? 'bg-white dark:bg-slate-700 text-slate-800 dark:text-white shadow-sm' : 'text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200'}`}
                  >
                    {t('dark_mode')}
                  </button>
                </div>
              </div>

              {/* Theme Grid */}
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-2 ml-1 uppercase tracking-wider text-start">{t('companion_theme')}</label>
                <div className="grid grid-cols-2 gap-3">
                  {[
                    { id: 'sunrise', name: t('theme_sunrise'), desc: t('theme_sunrise_desc'), colors: { start: '#ff7e5f', end: '#feb47b' } },
                    { id: 'original', name: t('theme_original'), desc: t('theme_original_desc'), colors: { start: '#8a63f5', end: '#ff8c6b' } },
                    { id: 'sunset', name: t('theme_sunset'), desc: t('theme_sunset_desc'), colors: { start: '#da4453', end: '#89216b' } },
                    { id: 'ocean', name: t('theme_ocean'), desc: t('theme_ocean_desc'), colors: { start: '#00c6ff', end: '#0072ff' } }
                  ].map(t => (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setSelectedTheme(t.id)}
                      className={`flex items-center gap-3 p-3.5 rounded-2xl border-2 text-left transition-all cursor-pointer ${selectedTheme === t.id ? 'border-aman-primary bg-slate-50 dark:bg-slate-800/80 shadow-md' : 'border-slate-100 dark:border-slate-800/40 bg-white dark:bg-slate-900 hover:border-slate-200 dark:hover:border-slate-700'}`}
                    >
                      <div className="w-8 h-8 rounded-full shadow-sm flex-shrink-0" style={{ background: `linear-gradient(135deg, ${t.colors.start} 0%, ${t.colors.end} 100%)` }} />
                      <div className="text-start">
                        <div className="text-sm font-bold text-slate-800 dark:text-white leading-tight">{t.name}</div>
                        <div className="text-[10px] text-slate-400 font-medium leading-normal">{t.desc}</div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-800">
                <span className="text-slate-700 dark:text-slate-200 font-medium text-sm text-start">{t('language')}</span>
                <select name="language" value={prefsData.language} onChange={handlePrefsChange} className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-full px-4 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-aman-primary shadow-sm cursor-pointer">
                  <option value="en">English</option>
                  <option value="ar">العربية (Arabic)</option>
                </select>
              </div>

              <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-800/50 rounded-2xl border border-slate-100 dark:border-slate-800">
                <div className="text-start">
                  <span className="text-slate-700 dark:text-slate-200 font-medium text-sm">{t('default_companion')}</span>
                  <p className="text-[11px] text-slate-400 mt-0.5">{t('default_companion_desc')}</p>
                </div>
                <select 
                  name="default_persona_id" 
                  value={prefsData.default_persona_id} 
                  onChange={handlePrefsChange} 
                  className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-full px-4 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-aman-primary shadow-sm cursor-pointer"
                >
                  {personas.map(p => (
                    <option key={p.id} value={p.id}>{personaNames[p.id] || p.name}</option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {activeTab === 'Security' && (
            <div className="space-y-6">
              
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-800 dark:text-white border-b border-slate-100 dark:border-slate-800 pb-2 text-start">{t('change_password')}</h3>
                <div>
                  <input type="password" name="old_password" placeholder={t('old_password')} value={securityData.old_password} onChange={handleSecurityChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all text-sm mb-3 text-start" />
                  <input type="password" name="new_password" placeholder={t('new_password')} value={securityData.new_password} onChange={handleSecurityChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all text-sm mb-3 text-start" />
                  <input type="password" name="confirm_password" placeholder={t('confirm_password')} value={securityData.confirm_password} onChange={handleSecurityChange} className="w-full px-4 py-2.5 rounded-2xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-700 dark:text-white focus:ring-2 focus:ring-aman-primary outline-none transition-all text-sm text-start" />
                  <p className="text-[11px] text-slate-400 mt-2 ml-1 text-start">{t('password_hint')}</p>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-100 dark:border-slate-800 space-y-3">
                <h3 className="text-sm font-bold text-red-600 dark:text-red-400 text-start">{t('danger_zone')}</h3>
                <div className="p-4 bg-orange-50 dark:bg-orange-900/10 border border-orange-100 dark:border-orange-900/30 rounded-2xl mb-3 text-start">
                  <p className="text-xs text-orange-700 dark:text-orange-400 mb-3 leading-relaxed">{t('clear_memory_desc')}</p>
                  <button onClick={handleDeleteMemory} disabled={loading} className="w-full py-2.5 px-4 bg-orange-100 hover:bg-orange-200 dark:bg-orange-900/40 dark:hover:bg-orange-900/60 text-orange-700 dark:text-orange-300 rounded-xl text-sm font-bold transition-colors disabled:opacity-50 cursor-pointer">
                    {t('clear_memory_btn')}
                  </button>
                </div>

                <div className="p-4 bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-2xl text-start">
                  <p className="text-xs text-red-700 dark:text-red-400 mb-3 leading-relaxed">{t('clear_history_desc')}</p>
                  <button onClick={handleDeleteHistory} disabled={loading} className="w-full py-2.5 px-4 bg-red-100 hover:bg-red-200 dark:bg-red-900/40 dark:hover:bg-red-900/60 text-red-700 dark:text-red-300 rounded-xl text-sm font-bold transition-colors disabled:opacity-50 cursor-pointer">
                    {t('clear_history_btn')}
                  </button>
                </div>
              </div>

            </div>
          )}

        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-3 bg-slate-50/50 dark:bg-slate-900/50">
          <button onClick={onClose} className="px-5 py-2 rounded-full text-sm font-semibold text-slate-500 hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors cursor-pointer">
            {t('close')}
          </button>
          {(activeTab === 'Account' || activeTab === 'Preferences' || activeTab === 'Security') && (
            <button 
              onClick={() => {
                if (activeTab === 'Account') handleSaveAccount();
                if (activeTab === 'Preferences') handleSavePrefs();
                if (activeTab === 'Security') handleSaveSecurity();
              }}
              disabled={loading}
              className="px-6 py-2 rounded-full text-sm font-bold text-white bg-aman-primary hover:bg-aman-primary/90 shadow-lg shadow-aman-primary/20 transition-all disabled:opacity-50 active:scale-95 cursor-pointer"
            >
              {loading ? t('saving') : t('save_changes')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
