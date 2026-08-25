import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  Users,
  HeartHandshake,
  Bell,
  UploadCloud,
  Sliders,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';
import { getStoredUser } from '../../utils/api';

export default function Sidebar() {
  const [isExpanded, setIsExpanded] = useState(false);
  const currentUser = getStoredUser();
  const isAdmin = currentUser?.role === 'ADMIN';

  const baseNavItems = [
    { to: '/', label: 'Overview', icon: Home },
    { to: '/students', label: 'Students', icon: Users },
    { to: '/interventions', label: 'Interventions', icon: HeartHandshake },
    { to: '/notifications', label: 'Notifications', icon: Bell },
    { to: '/rules', label: 'Rule Engine', icon: Sliders },
  ];

  // Upload data is an institutional action reserved for administrators
  const navItems = isAdmin
    ? [...baseNavItems.slice(0, 4), { to: '/upload', label: 'Upload Data', icon: UploadCloud }, baseNavItems[4]]
    : baseNavItems;

  return (
    <aside
      className={`bg-white border-r border-slate-100/80 flex flex-col justify-between transition-all duration-200 z-30 shrink-0 select-none ${
        isExpanded ? 'w-56' : 'w-16'
      }`}
    >
      {/* Top Section / Navigation */}
      <div className="py-4 flex flex-col items-center">
        {/* Navigation links */}
        <nav className="w-full px-2.5 space-y-1.5 mt-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-2.5 py-2.5 rounded-xl text-sm font-medium transition group relative ${
                  isActive
                    ? 'bg-blue-50/80 text-brand-600 font-semibold shadow-subtle border border-blue-100/60'
                    : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
                }`
              }
              title={!isExpanded ? item.label : undefined}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {isExpanded && <span className="truncate">{item.label}</span>}
              {!isExpanded && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded-md shadow-md opacity-0 pointer-events-none group-hover:opacity-100 transition whitespace-nowrap z-50">
                  {item.label}
                </div>
              )}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Bottom Controls / Expand Menu */}
      <div className="p-3 border-t border-slate-100/80 flex flex-col items-center gap-2">
        {isExpanded && currentUser && (
          <div className="w-full px-2 py-1.5 bg-slate-50 border border-slate-100 rounded-lg flex items-center gap-2 text-slate-500 text-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="truncate font-medium">{currentUser.role} Mode</span>
          </div>
        )}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-center gap-2 p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl transition text-xs font-medium cursor-pointer"
          title={isExpanded ? 'Collapse menu' : 'Expand menu'}
        >
          {isExpanded ? (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span>Collapse menu</span>
            </>
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </button>
      </div>
    </aside>
  );
}
