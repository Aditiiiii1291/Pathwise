import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  Home,
  Users,
  HeartHandshake,
  Bell,
  UploadCloud,
  Sliders,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';

export default function Sidebar() {
  const [isExpanded, setIsExpanded] = useState(false);

  const navItems = [
    { to: '/', label: 'Overview', icon: Home },
    { to: '/students', label: 'Students', icon: Users },
    { to: '/interventions', label: 'Interventions', icon: HeartHandshake },
    { to: '/notifications', label: 'Notifications', icon: Bell },
    { to: '/upload', label: 'Upload Data', icon: UploadCloud },
    { to: '/rules', label: 'Rule Engine', icon: Sliders },
  ];

  const secondaryItems = [
    { label: 'Reports', icon: FileText, disabled: true, tag: 'Phase 15' },
    { label: 'Settings', icon: Settings, disabled: true, tag: 'Phase 16' },
  ];

  return (
    <aside
      className={`bg-white border-r border-slate-100/80 flex flex-col justify-between transition-all duration-200 z-30 shrink-0 select-none ${
        isExpanded ? 'w-56' : 'w-16'
      }`}
    >
      {/* Top Section / Brand Icon */}
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

          <div className="pt-2 my-2 border-t border-slate-100" />

          {secondaryItems.map((item, idx) => (
            <div
              key={idx}
              className={`flex items-center gap-3 px-2.5 py-2 rounded-xl text-sm transition group relative ${
                item.disabled
                  ? 'text-slate-300 cursor-not-allowed'
                  : 'text-slate-500 hover:text-slate-800 hover:bg-slate-50'
              }`}
              title={!isExpanded ? `${item.label} (${item.tag || 'Soon'})` : undefined}
            >
              <item.icon className="w-5 h-5 shrink-0" />
              {isExpanded && (
                <div className="flex items-center justify-between w-full">
                  <span className="truncate">{item.label}</span>
                  {item.tag && (
                    <span className="text-[10px] bg-slate-100 text-slate-400 px-1.5 py-0.5 rounded font-mono">
                      {item.tag}
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </nav>
      </div>

      {/* Bottom Controls / Expand Menu */}
      <div className="p-3 border-t border-slate-100/80 flex flex-col items-center">
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
