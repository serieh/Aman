import React from 'react';
import { Layers, Zap, HardDrive, ShieldAlert, Cpu } from 'lucide-react';

export default function Slide2_Features() {
  return (
    <div className="flex flex-col h-full items-center justify-center p-8 animate-in fade-in slide-in-from-bottom-8 duration-700 relative overflow-hidden">
      
      {/* Background Decorative Shapes */}
      <div className="absolute top-1/4 left-0 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-[120px] opacity-30 animate-pulse"></div>
      <div className="absolute bottom-1/4 right-0 w-96 h-96 bg-teal-400 rounded-full mix-blend-multiply filter blur-[120px] opacity-30 animate-pulse" style={{ animationDelay: '1.5s' }}></div>

      <div className="max-w-5xl w-full bg-white/90 dark:bg-slate-800/90 backdrop-blur-xl rounded-3xl p-10 shadow-2xl border border-slate-200/50 dark:border-slate-700/50 z-10">
        <h2 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary mb-10 text-center drop-shadow-sm">
          2. Unique Features & Innovations
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900/80 dark:to-slate-800/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-xl transition-all">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 rounded-xl flex items-center justify-center mb-4 animate-pulse">
              <Layers size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">Dual-Tier LLM Architecture</h3>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
              Uses a high-capacity cloud model (gpt-oss-120b) for complex reasoning and a local quantized model (gemma4:e2b) for rapid background summarization.
            </p>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900/80 dark:to-slate-800/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-xl transition-all">
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400 rounded-xl flex items-center justify-center mb-4 animate-pulse">
              <Cpu size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">Memory Management</h3>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
              Compresses temporal context autonomously when active message turns reach a threshold of 25.
            </p>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900/80 dark:to-slate-800/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-xl transition-all">
            <div className="w-12 h-12 bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600 dark:text-emerald-400 rounded-xl flex items-center justify-center mb-4 animate-pulse">
              <HardDrive size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">RAG Architecture</h3>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
              Leverages Qdrant and BGE-M3 multi-granular embeddings to map permanent facts into a 1024-dimensional dense vector space.
            </p>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900/80 dark:to-slate-800/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-xl transition-all lg:col-span-1">
            <div className="w-12 h-12 bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400 rounded-xl flex items-center justify-center mb-4 animate-pulse">
              <ShieldAlert size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">Safety Firewall</h3>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
              Employs all-MiniLM-L6-v2 to map inputs, utilizing a strict 0.75 cosine similarity threshold to trigger crisis flags.
            </p>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900/80 dark:to-slate-800/50 p-6 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm hover:shadow-xl transition-all lg:col-span-2">
            <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/50 text-orange-600 dark:text-orange-400 rounded-xl flex items-center justify-center mb-4 animate-pulse">
              <Zap size={24} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">WebSocket Integration</h3>
            <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
              Bypasses RESTful bottlenecks using full-duplex WebSocket architecture via Django Channels and Daphne ASGI.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
