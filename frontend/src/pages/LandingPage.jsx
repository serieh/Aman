import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Brain, Wind, Shield } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen aman-gradient-bg flex flex-col font-sans">
      {/* Navbar */}
      <nav className="w-full px-6 py-4 flex items-center justify-between z-10 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-aman-primary to-aman-tertiary flex items-center justify-center text-white font-bold text-xl shadow-lg">
            A
          </div>
          <span className="text-xl font-bold text-slate-800 tracking-tight">Aman Reformed</span>
        </div>
        <div className="flex items-center gap-4">
          <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-aman-primary transition-colors">
            Login
          </Link>
          <Link to="/login" className="text-sm font-bold bg-slate-900 text-white px-5 py-2.5 rounded-full hover:bg-slate-800 transition-colors shadow-md">
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center z-10">
        <div className="max-w-3xl mx-auto space-y-8 animate-in slide-in-from-bottom-6 fade-in duration-700">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 leading-[1.1]">
            How are you <span className="text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary">feeling today?</span>
          </h1>
          <p className="text-lg md:text-xl text-slate-600 font-medium max-w-2xl mx-auto leading-relaxed">
            Aman is your personal, secure, and intelligent companion for mental well-being and clear thinking. A safe space to explore your thoughts.
          </p>
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/login" className="w-full sm:w-auto px-8 py-4 bg-aman-primary text-white rounded-full font-bold text-lg shadow-xl shadow-aman-primary/30 hover:scale-105 active:scale-95 transition-all">
              Start Chatting Free
            </Link>
          </div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto mt-24 mb-12">
          <div className="bg-white/60 backdrop-blur-md border border-white/50 p-8 rounded-3xl text-left shadow-lg hover:-translate-y-1 transition-transform">
            <div className="w-12 h-12 rounded-2xl bg-rose-100 flex items-center justify-center mb-6 text-rose-500">
              <Heart size={24} />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">Emotional Support</h3>
            <p className="text-slate-600 leading-relaxed">Discuss your feelings in a judgement-free zone. Aman is designed to listen and help you process emotions.</p>
          </div>
          
          <div className="bg-white/60 backdrop-blur-md border border-white/50 p-8 rounded-3xl text-left shadow-lg hover:-translate-y-1 transition-transform">
            <div className="w-12 h-12 rounded-2xl bg-violet-100 flex items-center justify-center mb-6 text-violet-500">
              <Brain size={24} />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">Clear Thinking</h3>
            <p className="text-slate-600 leading-relaxed">View Aman's internal "thought process" as it reasons through complex advice, providing transparency and depth.</p>
          </div>

          <div className="bg-white/60 backdrop-blur-md border border-white/50 p-8 rounded-3xl text-left shadow-lg hover:-translate-y-1 transition-transform">
            <div className="w-12 h-12 rounded-2xl bg-sky-100 flex items-center justify-center mb-6 text-sky-500">
              <Shield size={24} />
            </div>
            <h3 className="text-xl font-bold text-slate-800 mb-3">Total Privacy</h3>
            <p className="text-slate-600 leading-relaxed">You control your data. Clear your long-term memory or delete your chat history with a single click at any time.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
