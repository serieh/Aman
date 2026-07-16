import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, ShieldAlert, BrainCircuit, HeartHandshake, Cpu, Code } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';

export default function LegalPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 font-sans flex flex-col items-center py-10 px-4 md:px-8">
      <div className="w-full max-w-2xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
          <Link to="/" className="inline-flex items-center gap-1.5 text-sm font-semibold text-slate-500 hover:text-aman-primary dark:hover:text-aman-primary transition-colors group">
            <ArrowLeft size={16} className="group-hover:-translate-x-0.5 transition-transform rtl:rotate-180 rtl:group-hover:translate-x-0.5" />
            {t('back_to_home')}
          </Link>
          <span className="text-xs uppercase tracking-widest text-slate-400 dark:text-slate-500 font-bold">{t('brand')}</span>
        </div>

        {/* Title */}
        <div className="space-y-3 text-center md:text-start">
          <h1 className="text-3xl md:text-4xl font-extrabold text-slate-900 dark:text-white leading-tight">
            {t('legal_title')}
          </h1>
          <p className="text-sm md:text-base text-slate-600 dark:text-slate-400 leading-relaxed text-start">
            {t('legal_intro')}
          </p>
        </div>

        {/* Content Cards */}
        <div className="space-y-6">
          {/* Card 1: Clinical Disclaimer */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm hover:shadow-md transition-all text-start">
            <div className="w-10 h-10 rounded-xl bg-rose-50 dark:bg-rose-950/30 flex items-center justify-center text-rose-500 mb-4">
              <HeartHandshake size={20} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">
              {t('legal_section_1_title')}
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              {t('legal_section_1_desc')}
            </p>
          </div>

          {/* Card 2: AI Accuracy Disclaimer */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm hover:shadow-md transition-all text-start">
            <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950/30 flex items-center justify-center text-amber-500 mb-4">
              <ShieldAlert size={20} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">
              {t('legal_section_2_title')}
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              {t('legal_section_2_desc')}
            </p>
          </div>

          {/* Card 3: Privacy & Liability */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm hover:shadow-md transition-all text-start">
            <div className="w-10 h-10 rounded-xl bg-sky-50 dark:bg-sky-950/30 flex items-center justify-center text-sky-500 mb-4">
              <BrainCircuit size={20} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">
              {t('legal_section_3_title')}
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              {t('legal_section_3_desc')}
            </p>
          </div>

          {/* Card 4: How Aman Works */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm hover:shadow-md transition-all text-start">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-950/30 flex items-center justify-center text-indigo-500 mb-4">
              <Cpu size={20} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">
              {t('legal_section_4_title')}
            </h3>
            <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              {t('legal_section_4_desc')}
            </p>
          </div>

          {/* Card 5: Technology Credits */}
          <div className="bg-white dark:bg-slate-800 border border-slate-200/60 dark:border-slate-800/80 p-6 rounded-3xl shadow-sm hover:shadow-md transition-all text-start">
            <div className="w-10 h-10 rounded-xl bg-teal-50 dark:bg-teal-950/30 flex items-center justify-center text-teal-500 mb-4">
              <Code size={20} />
            </div>
            <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-2">
              {t('legal_section_5_title')}
            </h3>
            <div className="space-y-3">
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                {t('legal_section_5_desc')}
              </p>
              <ul className="list-disc list-inside space-y-1.5 text-xs text-slate-600 dark:text-slate-350 leading-relaxed font-mono">
                <li>{t('legal_credit_django')}</li>
                <li>{t('legal_credit_react')}</li>
                <li>{t('legal_credit_tailwind')}</li>
                <li>{t('legal_credit_langchain')}</li>
                <li>{t('legal_credit_qdrant')}</li>
                <li>{t('legal_credit_embedding')}</li>
                <li>{t('legal_credit_groq')}</li>
                <li>{t('legal_credit_huggingface')}</li>
                <li>{t('legal_credit_dataset')}</li>
                <li>{t('legal_credit_clinical')}</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-slate-600 dark:text-slate-400 pt-6 border-t border-slate-200 dark:border-slate-800 space-y-2.5 flex flex-col items-center">
          <div>
            &copy; {new Date().getFullYear()}{' '}
            <a href="https://github.com/serieh" target="_blank" rel="noopener noreferrer" className="text-slate-800 dark:text-slate-200 hover:text-aman-primary dark:hover:text-aman-primary underline transition-colors font-bold">
              Ahmad Serieh
            </a>
            . {t('footer_rights')}
          </div>
          <div className="flex gap-4">
            <a href="https://github.com/serieh" target="_blank" rel="noopener noreferrer" className="text-slate-600 dark:text-slate-400 hover:text-aman-primary dark:hover:text-aman-primary underline transition-colors font-medium">
              GitHub
            </a>
            <a href="https://www.linkedin.com/in/ahmad-serieh/" target="_blank" rel="noopener noreferrer" className="text-slate-600 dark:text-slate-400 hover:text-aman-primary dark:hover:text-aman-primary underline transition-colors font-medium">
              LinkedIn
            </a>
          </div>
        </div>

      </div>
    </div>
  );
}
