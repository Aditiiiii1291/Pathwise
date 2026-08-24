import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogIn, ArrowRight, Info, Lock, Mail } from 'lucide-react';
import PathwiseLogo from '../components/common/PathwiseLogo';

// =========================================================================
// DEVELOPMENT SHELL NOTICE:
// Real authentication, password hashing, JWT tokens, and RBAC belong to a
// subsequent security phase.
//
// In this development shell:
// - Password values are NEVER persisted or stored (no localStorage / sessionStorage)
// - No fake authentication tokens are created
// - No fake credential validation is performed
// - Clicking "Sign In" simply transitions the user to development mode ('/')
// =========================================================================

export default function LoginPage() {
  const [email, setEmail] = useState('advisor@institution.edu');
  const [password, setPassword] = useState('••••••••••••');
  const [rememberMe, setRememberMe] = useState(true);
  const navigate = useNavigate();

  const handleSignIn = (e) => {
    e.preventDefault();
    // Non-production development transition only
    navigate('/');
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

          <form onSubmit={handleSignIn} className="space-y-4">
            {/* Email / Username Field */}
            <div className="space-y-1.5">
              <label
                htmlFor="email"
                className="block text-xs font-semibold text-slate-700"
              >
                Institutional Email or Username
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  id="email"
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="advisor@university.edu"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 focus:bg-white transition"
                  required
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
                <span className="text-[10px] text-slate-400 select-none">
                  Available when institutional authentication is enabled
                </span>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter institutional password"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 focus:bg-white transition"
                  required
                />
              </div>
            </div>

            {/* Remember Me Checkbox */}
            <div className="flex items-center gap-2 pt-1">
              <input
                id="remember"
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-4 h-4 rounded text-brand-600 focus:ring-brand-500/20 border-slate-300"
              />
              <label htmlFor="remember" className="text-xs text-slate-500 select-none">
                Remember this workstation session
              </label>
            </div>

            {/* Primary Sign In Button */}
            <button
              type="submit"
              className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-xl text-xs shadow-md transition flex items-center justify-center gap-2 mt-2 cursor-pointer"
            >
              <LogIn className="w-4 h-4" />
              <span>Sign In to Dashboard</span>
            </button>

            {/* Development Shortcut Button */}
            <button
              type="button"
              onClick={() => navigate('/')}
              className="w-full py-2.5 px-4 bg-slate-50 hover:bg-slate-100 text-slate-700 font-medium rounded-xl text-xs border border-slate-200/80 transition flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Continue in Development Mode</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          {/* Security & Future Auth Notice */}
          <div className="p-3.5 bg-blue-50/60 border border-blue-100 rounded-2xl flex items-start gap-2.5 text-xs text-blue-900 leading-relaxed">
            <Info className="w-4 h-4 text-brand-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block text-[11px]">Authentication Notice</span>
              <span className="text-[11px] text-blue-700/90">
                Institutional SSO and secure authentication will be integrated in a future security phase. This interface is currently a development shell.
              </span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-[11px] text-slate-400 text-center">
          &copy; 2026 Pathwise Retention Intelligence &bull; Authorized Institutional Access
        </p>
      </div>
    </div>
  );
}
