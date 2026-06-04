import React from 'react';
import { X } from 'lucide-react';

export default function SettingsModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center px-4 bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white dark:bg-slate-900 w-full max-w-md rounded-3xl overflow-hidden shadow-2xl border border-slate-200 dark:border-slate-800" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-800 dark:text-white">Settings</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700 transition-colors p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800">
            <X size={18} />
          </button>
        </div>

        {/* Content Tabs */}
        <div className="px-6 py-2.5 flex gap-6 border-b border-slate-100 dark:border-slate-800 text-sm font-medium">
          <button className="text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors py-1">Account</button>
          <button className="text-aman-primary border-b-2 border-aman-primary py-1">Preferences</button>
          <button className="text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors py-1">Security</button>
        </div>

        {/* Form Body */}
        <div className="px-6 py-6 space-y-6">
          <div className="flex flex-col items-center gap-3">
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-aman-primary to-aman-tertiary flex items-center justify-center text-3xl text-white font-bold shadow-md">
              A
            </div>
            <button className="text-sm font-medium px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-full hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors">
              Change Photo
            </button>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-slate-700 dark:text-slate-300 font-medium text-sm">App Theme</span>
              <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-full p-1">
                <button className="px-3 py-1 rounded-full text-xs font-medium bg-white dark:bg-slate-700 shadow-sm text-slate-800 dark:text-white">Light</button>
                <button className="px-3 py-1 rounded-full text-xs font-medium text-slate-400 hover:text-slate-700 dark:hover:text-white">Dark</button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-slate-700 dark:text-slate-300 font-medium text-sm">Language</span>
              <select className="bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full px-3 py-1.5 text-sm text-slate-700 dark:text-slate-300 outline-none focus:ring-2 focus:ring-aman-primary">
                <option value="en">English</option>
                <option value="ar">العربية</option>
              </select>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-end gap-3">
          <button onClick={onClose} className="px-4 py-2 rounded-full text-sm font-medium text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            Cancel
          </button>
          <button onClick={onClose} className="px-5 py-2 rounded-full text-sm font-medium text-white bg-aman-primary hover:bg-aman-primary/90 shadow-md shadow-aman-primary/20 transition-all">
            Save
          </button>
        </div>
      </div>
    </div>
  );
}
