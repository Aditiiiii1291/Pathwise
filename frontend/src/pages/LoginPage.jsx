import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn, Lock, User, AlertCircle, Eye, EyeOff, Loader2 } from 'lucide-react';
import PathwiseLogo from '../components/common/PathwiseLogo';
import { login } from '../utils/api';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSignIn = async (e) => {
    e.preventDefault();
    setError(null);

    // 1. Client-side local formatting validation
    const trimmedUser = username.trim();
    if (!trimmedUser) {
      setError('Enter your username.');
      return;
    }
    if (!password) {
      setError('Enter your password.');
      return;
    }

    setLoading(true);
    try {
      await login(trimmedUser, password);
      navigate('/');
    } catch (err) {
      // Server authentication failure: protect against username enumeration
      if (err.status === 401 || err.message?.includes('401')) {
        setError('Invalid username or password.');
      } else {
        setError(err.message || 'Unable to connect to Pathwise service. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-4 sm:p-6 font-sans text-slate-800 antialiased">
      <div className="max-w-md w-full space-y-6">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center space-y-2">
          <PathwiseLogo size="lg" showSubtitle={false} />
          <p className="text-xs text-slate-500 font-medium max-w-xs">
            Student Retention & Early Support Intelligence Platform
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white border border-slate-100 rounded-3xl p-8 shadow-card space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-slate-800">
              Institutional Sign In
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Authorized academic advisors, faculty mentors, and deans
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200/80 rounded-2xl flex items-center gap-2.5 text-xs text-red-700 animate-fadeIn">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSignIn} className="space-y-4">
            {/* Username Field */}
            <div className="space-y-1.5">
              <label
                htmlFor="username"
                className="block text-xs font-semibold text-slate-700"
              >
                Username
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="Enter institutional username"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 focus:bg-white transition"
                  autoComplete="username"
                  disabled={loading}
                />
              </div>
            </div>

            {/* Password Field */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold text-slate-700"
                >
                  Password
                </label>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="Enter your password"
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 focus:bg-white transition"
                  autoComplete="current-password"
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 focus:outline-none"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Primary Sign In Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-xs shadow-md transition flex items-center justify-center gap-2 mt-4 cursor-pointer"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Verifying credentials...</span>
                </>
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>Sign In to Dashboard</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Footer */}
        <p className="text-[11px] text-slate-400 text-center">
          &copy; 2026 Pathwise Retention Intelligence &bull; Authorized Institutional Access
        </p>
      </div>
    </div>
  );
}
