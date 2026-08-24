import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Search, Bell, ChevronDown, User } from 'lucide-react';
import PathwiseLogo from '../common/PathwiseLogo';

export default function Header() {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/students?search=${encodeURIComponent(searchTerm.trim())}`);
    } else {
      navigate('/students');
    }
  };

  return (
    <header className="bg-white border-b border-slate-100/80 px-6 py-3 flex items-center justify-between gap-4 sticky top-0 z-20 shadow-[0_1px_2px_rgba(0,0,0,0.02)]">
      {/* Brand Identity */}
      <Link to="/" className="shrink-0 hover:opacity-90 transition">
        <PathwiseLogo size="md" />
      </Link>

      {/* Global Search Bar */}
      <div className="max-w-md w-full">
        <form onSubmit={handleSearchSubmit} className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by name, roll no., department..."
            className="w-full pl-9 pr-14 py-2 bg-slate-50 border border-slate-200/70 rounded-xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 focus:bg-white transition"
          />
          <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-0.5 text-[10px] font-mono text-slate-400 bg-white border border-slate-200 px-1.5 py-0.5 rounded shadow-xs">
            Ctrl + K
          </div>
        </form>
      </div>

      {/* Right Controls / Notification & Profile */}
      <div className="flex items-center gap-3 shrink-0">
        {/* Notification Bell (Placeholder for Phase 13) */}
        <button
          className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl transition"
          title="Notifications (Phase 13)"
        >
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-white">
            8
          </span>
        </button>

        <div className="h-6 w-px bg-slate-200/80 mx-1" />

        {/* User / Mentor Menu */}
        <div className="flex items-center gap-2.5 px-2 py-1.5 rounded-xl hover:bg-slate-50 transition cursor-pointer">
          <div className="w-7 h-7 rounded-full bg-slate-100 border border-slate-200 text-slate-600 flex items-center justify-center">
            <User className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold text-slate-700">Mentor</span>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        </div>
      </div>
    </header>
  );
}
