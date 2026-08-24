import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Home, Users, ArrowLeft, HelpCircle } from 'lucide-react';
import PathwiseLogo from '../components/common/PathwiseLogo';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-6 font-sans text-slate-800 antialiased">
      <div className="max-w-md w-full text-center space-y-6">
        {/* Brand Logo */}
        <div className="flex justify-center">
          <PathwiseLogo size="md" />
        </div>

        {/* 404 Card */}
        <div className="bg-white border border-slate-100 rounded-3xl p-8 shadow-card space-y-5">
          <div className="w-16 h-16 bg-blue-50 text-brand-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs">
            <span className="text-2xl font-black tracking-wider">404</span>
          </div>

          <div className="space-y-1.5">
            <h2 className="text-lg font-bold text-slate-800">
              Page Not Found
            </h2>
            <p className="text-xs text-slate-500 leading-relaxed max-w-sm mx-auto">
              The page you are looking for might have been moved, renamed, or does not exist within the Pathwise portal.
            </p>
          </div>

          <div className="pt-2 space-y-2.5">
            <Link
              to="/"
              className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-xl text-xs shadow-sm transition flex items-center justify-center gap-2"
            >
              <Home className="w-4 h-4" />
              <span>Back to Overview Dashboard</span>
            </Link>

            <Link
              to="/students"
              className="w-full py-2.5 px-4 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold rounded-xl text-xs border border-slate-200/80 transition flex items-center justify-center gap-2"
            >
              <Users className="w-4 h-4" />
              <span>Explore Student Roster</span>
            </Link>

            <button
              onClick={() => navigate(-1)}
              className="w-full py-2 text-xs font-medium text-slate-400 hover:text-slate-600 transition flex items-center justify-center gap-1.5"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Go back to previous page</span>
            </button>
          </div>
        </div>

        <p className="text-[11px] text-slate-400">
          Pathwise Early Warning & Intervention Platform
        </p>
      </div>
    </div>
  );
}
