import React from 'react';
import { Target, ShieldCheck, Languages, Layout } from 'lucide-react';

export default function Slide5_Conclusion() {
  return (
    <div className="flex flex-col h-full items-center justify-center p-8 animate-in fade-in slide-in-from-bottom-8 duration-700 relative overflow-hidden">
      
      {/* Background Decorative Shapes */}
      <div className="absolute top-10 right-10 w-[500px] h-[500px] bg-rose-400/20 rounded-full mix-blend-multiply filter blur-[150px] animate-pulse"></div>
      <div className="absolute bottom-10 left-10 w-[400px] h-[400px] bg-amber-400/20 rounded-full mix-blend-multiply filter blur-[150px] animate-pulse" style={{ animationDelay: '1.5s' }}></div>

      <div className="max-w-4xl w-full bg-white/90 dark:bg-slate-800/90 backdrop-blur-xl rounded-3xl p-10 shadow-2xl border border-slate-200/50 dark:border-slate-700/50 z-10">
        <h2 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary mb-10 text-center drop-shadow-sm">
          5. Conclusion & Key Findings
        </h2>
        
        <div className="space-y-6">
          <div className="flex items-start gap-5 bg-gradient-to-r from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm transition-all">
            <div className="w-14 h-14 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-500 flex-shrink-0 shadow-inner animate-pulse">
              <Target size={26} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-1">Retrieval Accuracy</h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed">Evaluated using the RAGAS framework, demonstrating exceptional context precision and conversational faithfulness without clinical hallucinations.</p>
            </div>
          </div>

          <div className="flex items-start gap-5 bg-gradient-to-r from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm transition-all">
            <div className="w-14 h-14 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center text-red-500 flex-shrink-0 shadow-inner animate-pulse">
              <ShieldCheck size={26} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-1">Safety Prioritization</h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed">Mathematical thresholds in the semantic firewall were explicitly tuned to maximize Recall over Precision, preventing catastrophic False Negatives during severe crisis routing.</p>
            </div>
          </div>

          <div className="flex items-start gap-5 bg-gradient-to-r from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm transition-all">
            <div className="w-14 h-14 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center text-purple-500 flex-shrink-0 shadow-inner animate-pulse">
              <Languages size={26} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-1">Bilingual Consistency</h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed">Human-in-the-Loop (HITL) assessments proved the agent maintains therapeutic state without breaking character during mid-conversation linguistic transitions.</p>
            </div>
          </div>

          <div className="flex items-start gap-5 bg-gradient-to-r from-slate-50 to-white dark:from-slate-900/50 dark:to-slate-800/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm transition-all">
            <div className="w-14 h-14 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center text-emerald-500 flex-shrink-0 shadow-inner animate-pulse">
              <Layout size={26} />
            </div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-1">Intuitive Interface</h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed">The distraction-free, minimalist UI design significantly reduced cognitive load, allowing users to focus entirely on therapeutic engagement.</p>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
