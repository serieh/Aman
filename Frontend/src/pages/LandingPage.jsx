import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Users, Wind, Phone } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { useTranslation } from '../hooks/useTranslation';

export default function LandingPage() {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);
  const language = useAuthStore(state => state.language);
  const setLanguage = useAuthStore(state => state.setLanguage);
  const { t } = useTranslation();

  return (
    <div className="min-h-screen aman-gradient-bg flex flex-col font-sans overflow-y-auto">
      {/* Navbar */}
      <nav className="w-full px-6 py-4 flex items-center justify-between z-10 max-w-7xl mx-auto gap-4">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(var(--color-aman-primary),0.5)] animate-pulse overflow-hidden bg-transparent">
            <img src="/favicon.ico" alt="Aman" className="w-full h-full object-cover" />
          </div>
          <span className="text-xl font-bold text-slate-800 tracking-tight">{t('brand')}</span>
        </div>
        <div className="flex items-center gap-3 md:gap-4">
          {/* Pre-auth Language Selector */}
          <select 
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="bg-white/60 dark:bg-slate-900/60 border border-white/50 dark:border-slate-850 rounded-full px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-350 outline-none focus:ring-2 focus:ring-aman-primary shadow-sm cursor-pointer"
          >
            <option value="en">English</option>
            <option value="ar">العربية</option>
          </select>

          {isAuthenticated ? (
            <Link to="/app" className="text-sm font-bold bg-aman-primary text-white px-5 py-2.5 rounded-full hover:bg-aman-primary/90 transition-colors shadow-md">
              {t('dashboard')}
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-slate-650 hover:text-aman-primary transition-colors">
                {t('login')}
              </Link>
              <Link to="/login" className="text-sm font-bold bg-slate-900 text-white px-5 py-2.5 rounded-full hover:bg-slate-800 transition-colors shadow-md hidden sm:inline-block">
                {t('get_started')}
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center z-10">
        <div className="max-w-3xl mx-auto space-y-8 animate-in slide-in-from-bottom-6 fade-in duration-700">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 leading-[1.1]">
            {t('hero_title_pre')} <span className="text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary">{t('hero_title_post')}</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-655 font-medium max-w-2xl mx-auto leading-relaxed">
            {t('hero_subtitle')}
          </p>
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to={isAuthenticated ? "/app" : "/login"} className="w-full sm:w-auto px-8 py-4 bg-aman-primary text-white rounded-full font-bold text-lg shadow-xl shadow-aman-primary/40 hover:scale-105 hover:shadow-aman-primary/60 active:scale-95 transition-all duration-300 animate-pulse">
              {isAuthenticated ? t('go_to_dashboard') : t('start_chatting')}
            </Link>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mt-24 mb-12">
          <div className="bg-white/60 backdrop-blur-md border border-white/50 p-8 rounded-3xl text-start shadow-lg hover:-translate-y-2 hover:shadow-xl hover:bg-white/80 transition-all duration-300 animate-in slide-in-from-bottom-12 fade-in duration-700 delay-150 fill-mode-both">
            <div className="w-12 h-12 rounded-2xl bg-rose-100 flex items-center justify-center mb-6 text-rose-500 hover:scale-110 transition-transform">
              <Heart size={24} />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">{t('feature_emotional_title')}</h3>
            <p className="text-slate-600 leading-relaxed">{t('feature_emotional_desc')}</p>
          </div>
          
          <div className="bg-white/60 backdrop-blur-md border border-white/50 p-8 rounded-3xl text-start shadow-lg hover:-translate-y-2 hover:shadow-xl hover:bg-white/80 transition-all duration-300 animate-in slide-in-from-bottom-12 fade-in duration-700 delay-300 fill-mode-both">
            <div className="w-12 h-12 rounded-2xl bg-violet-100 flex items-center justify-center mb-6 text-violet-500 hover:scale-110 transition-transform">
              <Users size={24} />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">{t('feature_thinking_title')}</h3>
            <p className="text-slate-600 leading-relaxed">{t('feature_thinking_desc')}</p>
          </div>

          <div className="bg-white/60 backdrop-blur-md border border-white/50 p-8 rounded-3xl text-start shadow-lg hover:-translate-y-2 hover:shadow-xl hover:bg-white/80 transition-all duration-300 animate-in slide-in-from-bottom-12 fade-in duration-700 delay-500 fill-mode-both">
            <div className="w-12 h-12 rounded-2xl bg-sky-100 flex items-center justify-center mb-6 text-sky-500 hover:scale-110 transition-transform">
              <Phone size={24} />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">{t('feature_privacy_title')}</h3>
            <p className="text-slate-600 leading-relaxed">{t('feature_privacy_desc')}</p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-8 border-t border-slate-200/60 dark:border-slate-850 z-10 max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-semibold text-slate-700 dark:text-slate-300 mt-12">
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <span>
            &copy; {new Date().getFullYear()}{' '}
            <a href="https://github.com/serieh" target="_blank" rel="noopener noreferrer" className="text-slate-900 dark:text-white hover:text-aman-primary dark:hover:text-aman-primary underline transition-colors font-bold">
              Ahmad Serieh
            </a>
            . {t('footer_rights')}
          </span>
          <div className="flex gap-3">
            <a href="https://github.com/serieh" target="_blank" rel="noopener noreferrer" className="text-slate-600 dark:text-slate-400 hover:text-aman-primary dark:hover:text-aman-primary underline transition-colors">
              GitHub
            </a>
            <a href="https://www.linkedin.com/in/ahmad-serieh/" target="_blank" rel="noopener noreferrer" className="text-slate-600 dark:text-slate-400 hover:text-aman-primary dark:hover:text-aman-primary underline transition-colors">
              LinkedIn
            </a>
          </div>
        </div>
        <div className="flex gap-6">
          <Link to="/legal" className="text-slate-700 dark:text-slate-350 hover:text-aman-primary dark:hover:text-aman-primary transition-colors underline">
            {t('legal_title')}
          </Link>
        </div>
      </footer>
    </div>
  );
}
