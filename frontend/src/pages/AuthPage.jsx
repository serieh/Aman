import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import api from '../api/axios';
import { ChevronDown, Calendar, AlertCircle } from 'lucide-react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({ name: '', email: '', password: '', birthdate: '', gender: 'female', country: 'US' });
  const [errors, setErrors] = useState({});
  const [globalError, setGlobalError] = useState('');
  const [loading, setLoading] = useState(false);
  const [genderOpen, setGenderOpen] = useState(false);
  
  const genderRef = useRef(null);
  const navigate = useNavigate();
  const login = useAuthStore(state => state.login);

  // Close gender dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (genderRef.current && !genderRef.current.contains(event.target)) {
        setGenderOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [genderRef]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors({});
    setGlobalError('');
    setLoading(true);
    try {
      if (isLogin) {
        const { data } = await api.post('/auth/login/', { email: formData.email, password: formData.password });
        login(data.access, data.refresh, null);
        navigate('/app');
      } else {
        const { data } = await api.post('/auth/register/', formData);
        login(data.access, data.refresh, null);
        navigate('/app');
      }
    } catch (err) {
      const data = err.response?.data;
      if (data) {
        if (data.error) {
          setGlobalError(data.error);
        } else if (data.detail) {
          setGlobalError(data.detail);
        } else if (typeof data === 'object') {
          setErrors(data);
        } else {
          setGlobalError('Authentication failed. Please check your credentials.');
        }
      } else {
        setGlobalError('Network error. Please check your connection.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => setFormData({ ...formData, [e.target.name]: e.target.value });
  
  const handleGenderSelect = (val) => {
    setFormData({ ...formData, gender: val });
    setGenderOpen(false);
  };

  const renderError = (field) => {
    if (!errors[field]) return null;
    const msg = Array.isArray(errors[field]) ? errors[field][0] : errors[field];
    return <p className="text-red-500 text-xs mt-1 ml-4 flex items-center gap-1"><AlertCircle size={12}/> {msg}</p>;
  };

  return (
    <div className="flex min-h-screen">
      {/* Left side: Animated Gradient */}
      <div className="hidden lg:flex w-1/2 aman-gradient-bg items-center justify-center relative overflow-hidden">
        <div className="glass-panel w-3/4 max-w-md p-10 rounded-3xl text-center z-10 shadow-2xl">
          <div className="flex justify-center mb-6">
            <h1 className="text-6xl font-bold text-slate-800 tracking-tighter">Aman</h1>
          </div>
          <p className="text-xl text-slate-700 font-medium leading-relaxed">
            Welcome to Aman. Find your emotional balance and a safe space for mental well-being.
          </p>
        </div>
      </div>

      {/* Right side: Login Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 bg-white dark:bg-slate-900 overflow-y-auto">
        <div className="w-full max-w-md space-y-8 pb-10">
          <div className="text-center lg:text-left">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white">{isLogin ? 'Login to Aman' : 'Sign Up for Aman'}</h2>
            <p className="mt-2 text-slate-600 dark:text-slate-400">
              {isLogin ? 'Welcome back! Please enter your details.' : 'Create your account to get started.'}
            </p>
          </div>

          {globalError && (
            <div className="p-4 bg-red-50 border border-red-100 text-red-600 rounded-2xl text-sm font-medium flex items-start gap-2 shadow-sm animate-in fade-in slide-in-from-top-2">
              <AlertCircle size={18} className="mt-0.5 shrink-0"/>
              <span>{globalError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div className="space-y-4">
              {!isLogin && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 ml-1">Full Name</label>
                  <input type="text" name="name" required value={formData.name} onChange={handleChange} className={`w-full px-5 py-3.5 rounded-full border ${errors.name ? 'border-red-300 focus:ring-red-500' : 'border-slate-200 dark:border-slate-700 focus:ring-aman-primary'} bg-slate-50 dark:bg-slate-800 focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:border-transparent outline-none transition-all dark:text-white font-medium`} placeholder="Sarah Connor" />
                  {renderError('name')}
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 ml-1">Email Address</label>
                <input type="email" name="email" required value={formData.email} onChange={handleChange} className={`w-full px-5 py-3.5 rounded-full border ${errors.email ? 'border-red-300 focus:ring-red-500' : 'border-slate-200 dark:border-slate-700 focus:ring-aman-primary'} bg-slate-50 dark:bg-slate-800 focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:border-transparent outline-none transition-all dark:text-white font-medium`} placeholder="you@example.com" />
                {renderError('email')}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 ml-1">Password</label>
                <input type="password" name="password" required value={formData.password} onChange={handleChange} className={`w-full px-5 py-3.5 rounded-full border ${errors.password ? 'border-red-300 focus:ring-red-500' : 'border-slate-200 dark:border-slate-700 focus:ring-aman-primary'} bg-slate-50 dark:bg-slate-800 focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:border-transparent outline-none transition-all dark:text-white font-medium`} placeholder="••••••••" />
                {renderError('password')}
              </div>

              {!isLogin && (
                <div className="flex gap-4">
                  <div className="flex-1">
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 ml-1">Birthdate</label>
                    <div className="relative">
                      <DatePicker 
                        selected={formData.birthdate ? new Date(formData.birthdate) : null} 
                        onChange={(date) => {
                          if (date) {
                            // Account for timezone offset to avoid getting the day before
                            const offset = date.getTimezoneOffset()
                            const adjustedDate = new Date(date.getTime() - (offset*60*1000))
                            const formatted = adjustedDate.toISOString().split('T')[0];
                            setFormData({ ...formData, birthdate: formatted });
                          } else {
                            setFormData({ ...formData, birthdate: '' });
                          }
                        }} 
                        className={`w-full px-5 py-3.5 rounded-full border ${errors.birthdate ? 'border-red-300 focus:ring-red-500' : 'border-slate-200 dark:border-slate-700 focus:ring-aman-primary'} bg-slate-50 dark:bg-slate-800 focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:border-transparent outline-none transition-all dark:text-white font-medium`} 
                        dateFormat="yyyy-MM-dd"
                        placeholderText="YYYY-MM-DD"
                        maxDate={new Date()}
                        showYearDropdown
                        scrollableYearDropdown
                        yearDropdownItemNumber={100}
                        required
                      />
                      <Calendar className="absolute right-4 top-1/2 transform -translate-y-1/2 text-slate-400 pointer-events-none" size={18} />
                    </div>
                    {renderError('birthdate')}
                  </div>
                  
                  <div className="flex-1 relative" ref={genderRef}>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1 ml-1">Gender</label>
                    <div 
                      onClick={() => setGenderOpen(!genderOpen)}
                      className={`w-full px-5 py-3.5 rounded-full border ${errors.gender ? 'border-red-300 focus:ring-red-500' : 'border-slate-200 dark:border-slate-700 hover:border-slate-300'} bg-slate-50 dark:bg-slate-800 cursor-pointer flex items-center justify-between transition-all dark:text-white font-medium`}
                    >
                      <span className="capitalize">{formData.gender}</span>
                      <ChevronDown size={18} className={`text-slate-400 transition-transform ${genderOpen ? 'rotate-180' : ''}`} />
                    </div>
                    
                    {genderOpen && (
                      <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-slate-800 border border-slate-100 dark:border-slate-700 rounded-2xl shadow-xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-2">
                        {['female', 'male'].map(opt => (
                          <div 
                            key={opt}
                            onClick={() => handleGenderSelect(opt)}
                            className="px-5 py-3 hover:bg-slate-50 dark:hover:bg-slate-700 cursor-pointer text-sm font-medium capitalize text-slate-700 dark:text-slate-200 transition-colors"
                          >
                            {opt}
                          </div>
                        ))}
                      </div>
                    )}
                    {renderError('gender')}
                  </div>
                </div>
              )}
            </div>

            <button disabled={loading} type="submit" className="w-full py-3.5 px-4 bg-aman-primary hover:bg-aman-primary/90 text-white rounded-full font-bold shadow-lg shadow-aman-primary/30 transition-all hover:scale-[1.02] active:scale-95 disabled:opacity-70 disabled:hover:scale-100 mt-6">
              {loading ? 'Please wait...' : 'Continue'}
            </button>
            
            <div className="text-center mt-6">
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {isLogin ? "Don't have an account? " : "Already have an account? "}
                <button type="button" onClick={() => { setIsLogin(!isLogin); setErrors({}); setGlobalError(''); }} className="text-aman-primary font-bold hover:underline transition-all">
                  {isLogin ? 'Sign Up' : 'Login'}
                </button>
              </span>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
