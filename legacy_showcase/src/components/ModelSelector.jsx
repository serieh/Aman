import React from 'react';
import { Sparkles, Zap } from 'lucide-react';

export default function ModelSelector({ model, setModel }) {
  // model: "1" (Thinking/Gemma-4:26b) or "2" (Fast/Gemma-4:e2b)
  return (
    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-20">
      <div className="glass-panel rounded-full p-1 flex items-center">
        <button 
          onClick={() => setModel('2')}
          className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
            model === '2' ? 'bg-white text-aman-primary shadow-sm' : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          <Zap size={14} className={model === '2' ? 'text-aman-primary' : 'text-slate-400'} />
          Fast
        </button>
        <button 
          onClick={() => setModel('1')}
          className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
            model === '1' ? 'bg-white text-aman-primary shadow-sm' : 'text-slate-600 hover:text-slate-800'
          }`}
        >
          <Sparkles size={14} className={model === '1' ? 'text-aman-primary' : 'text-slate-400'} />
          Thinking
        </button>
      </div>
    </div>
  );
}
