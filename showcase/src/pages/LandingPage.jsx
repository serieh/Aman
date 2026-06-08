import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, Brain, Wind, Shield } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';

export default function LandingPage() {
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);

  return (
    <div className="min-h-screen aman-gradient-bg flex flex-col font-sans">
      {/* Navbar */}
      <nav className="w-full px-6 py-4 flex items-center justify-between z-10 max-w-7xl mx-auto">
        <div className="flex items-center gap-2">

          <span className="text-xl font-bold text-slate-800 tracking-tight">Aman</span>
        </div>
        <div className="flex items-center gap-4">
          {isAuthenticated ? (
            <Link to="/app" className="text-sm font-bold bg-aman-primary text-white px-5 py-2.5 rounded-full hover:bg-aman-primary/90 transition-colors shadow-md">
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-slate-600 hover:text-aman-primary transition-colors">
                Login
              </Link>
              <Link to="/login" className="text-sm font-bold bg-slate-900 text-white px-5 py-2.5 rounded-full hover:bg-slate-800 transition-colors shadow-md">
                Get Started
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Hero Section / Title Slide */}
      <main className="flex-1 flex flex-col items-center justify-center p-6 text-center z-10">
        <div className="max-w-4xl mx-auto space-y-8 animate-in slide-in-from-bottom-6 fade-in duration-700">
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-slate-900 leading-[1.1]">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary">Aman</span>
          </h1>
          <h2 className="text-2xl md:text-3xl text-slate-700 font-semibold max-w-3xl mx-auto leading-relaxed">
            An AI-Powered Bilingual Emotional Wellness Support Agent
          </h2>
          
          <div className="py-8 space-y-4">
            <p className="text-lg text-slate-600 font-medium">
              <span className="font-bold text-slate-800">By:</span> Ahmad Feras Serieh, Mohammad Ahmed Irsheid, Laith Hussam Jarrar, Mouath Rushdi Hajhoor
            </p>
            <p className="text-lg text-slate-600 font-medium">
              <span className="font-bold text-slate-800">Supervised by:</span> Dr. Sumaia Sabouni
            </p>
            <p className="text-lg text-slate-500 font-medium pt-2">
              June, 2026
            </p>
          </div>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/login?autoPlay=true" className="w-full sm:w-auto px-8 py-4 bg-aman-primary text-white rounded-full font-bold text-lg shadow-xl shadow-aman-primary/40 hover:scale-105 hover:shadow-aman-primary/60 active:scale-95 transition-all duration-300 animate-pulse">
              Start Chatting
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
