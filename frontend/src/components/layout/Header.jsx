import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Search, ChevronDown, User, LogOut, Shield } from 'lucide-react';
import PathwiseLogo from '../common/PathwiseLogo';
import NotificationBellDropdown from '../notifications/NotificationBellDropdown';
import { getStoredUser, logout } from '../../utils/api';

export default function Header() {
  const [searchTerm, setSearchTerm] = useState('');
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(getStoredUser());
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    setCurrentUser(getStoredUser());
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setUserDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/students?search=${encodeURIComponent(searchTerm.trim())}`);
    } else {
      navigate('/students');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const roleColors = {
    ADMIN: 'bg-purple-50 text-purple-700 border-purple-200',
    COUNSELLOR: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    MENTOR: 'bg-blue-50 text-blue-700 border-blue-200',
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
        {/* In-App Notification Bell */}
        <NotificationBellDropdown />

        <div className="h-6 w-px bg-slate-200/80 mx-1" />

        {/* User / Mentor Menu */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setUserDropdownOpen(!userDropdownOpen)}
            className="flex items-center gap-2.5 px-2.5 py-1.5 rounded-xl hover:bg-slate-50 border border-transparent hover:border-slate-200/60 transition cursor-pointer"
          >
            <div className="w-7 h-7 rounded-full bg-brand-50 border border-brand-200/60 text-brand-700 flex items-center justify-center font-bold text-xs">
              {currentUser?.display_name ? currentUser.display_name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
            </div>
            <div className="text-left hidden sm:block">
              <span className="text-xs font-semibold text-slate-700 block leading-tight">
                {currentUser?.display_name || 'Academic Advisor'}
              </span>
              <span className="text-[10px] text-slate-400 font-mono">
                {currentUser?.role || 'MENTOR'}
              </span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          </button>

          {/* Profile Dropdown */}
          {userDropdownOpen && (
            <div className="absolute right-0 mt-2 w-56 bg-white border border-slate-200/80 rounded-2xl shadow-xl py-2 z-50 animate-fadeIn">
              <div className="px-4 py-2.5 border-b border-slate-100">
                <p className="text-xs font-bold text-slate-800">
                  {currentUser?.display_name || 'User'}
                </p>
                <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                  @{currentUser?.username || 'user'}
                </p>
                <div className="mt-2">
                  <span className={`inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full border ${roleColors[currentUser?.role] || roleColors.MENTOR}`}>
                    <Shield className="w-3 h-3" />
                    <span>{currentUser?.role || 'MENTOR'}</span>
                  </span>
                </div>
              </div>

              <div className="py-1">
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full px-4 py-2 text-left text-xs text-red-600 hover:bg-red-50/80 flex items-center gap-2 transition cursor-pointer font-medium"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
