import React from 'react';

export default function Slide1_Intro() {
  return (
    <div className="flex flex-col h-full items-center justify-center p-8 animate-in fade-in slide-in-from-bottom-8 duration-700 relative overflow-hidden">
      
      {/* Background Decorative Shapes */}
      <div className="absolute top-0 right-0 w-80 h-80 bg-purple-300 rounded-full mix-blend-multiply filter blur-[100px] opacity-40 animate-pulse"></div>
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-blue-300 rounded-full mix-blend-multiply filter blur-[100px] opacity-40 animate-pulse" style={{ animationDelay: '2s' }}></div>

      <div className="max-w-4xl w-full bg-white/90 dark:bg-slate-800/90 backdrop-blur-xl rounded-3xl p-10 shadow-2xl border border-slate-200/50 dark:border-slate-700/50 z-10">
        <h2 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary mb-10 text-center drop-shadow-sm">
          1. Introduction & Objectives
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex flex-col gap-4 bg-slate-50/80 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-lg">
            <div className="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center flex-shrink-0 text-blue-600 dark:text-blue-400 font-bold text-xl animate-pulse">1</div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Target Demographic</h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-sm">Specifically tailored for marginalized and conservative demographics within the Middle East and North Africa (MENA) region.</p>
            </div>
          </div>

          <div className="flex flex-col gap-4 bg-slate-50/80 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-lg" style={{ transitionDelay: '100ms' }}>
            <div className="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center flex-shrink-0 text-purple-600 dark:text-purple-400 font-bold text-xl animate-pulse">2</div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Tested on 2 Languages</h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-sm">Engineered for seamless mid-sentence linguistic switching between Modern Standard Arabic (MSA) and English.</p>
            </div>
          </div>

          <div className="flex flex-col gap-4 bg-slate-50/80 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-lg" style={{ transitionDelay: '200ms' }}>
            <div className="w-12 h-12 rounded-xl bg-rose-100 dark:bg-rose-900/30 flex items-center justify-center flex-shrink-0 text-rose-600 dark:text-rose-400 font-bold text-xl animate-pulse">3</div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Clinical Framework</h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-sm">Structurally integrates evidence-based Cognitive Behavioral Therapy (CBT) techniques with Arab cultural frameworks.</p>
            </div>
          </div>

          <div className="flex flex-col gap-4 bg-slate-50/80 dark:bg-slate-900/50 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-lg" style={{ transitionDelay: '300ms' }}>
            <div className="w-12 h-12 rounded-xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center flex-shrink-0 text-emerald-600 dark:text-emerald-400 font-bold text-xl animate-pulse">4</div>
            <div>
              <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-2">Core Goal</h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-sm">To de-pathologize mental health support and function as a highly accessible digital mate for users navigating acute psychological distress.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
