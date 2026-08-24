import React from 'react';

const BADGE_STYLES = {
  LOW: 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
  MEDIUM: 'bg-amber-50 text-amber-700 border-amber-200/60',
  HIGH: 'bg-orange-50 text-orange-700 border-orange-200/60',
  CRITICAL: 'bg-rose-50 text-rose-700 border-rose-200/60',
};

const DOT_STYLES = {
  LOW: 'bg-emerald-500',
  MEDIUM: 'bg-amber-500',
  HIGH: 'bg-orange-500',
  CRITICAL: 'bg-rose-500',
};

export default function RiskBadge({ tier, showDot = true, size = 'sm' }) {
  if (!tier) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-500 border border-slate-200">
        Unassessed
      </span>
    );
  }

  const normalized = tier.toUpperCase();
  const badgeClass = BADGE_STYLES[normalized] || 'bg-slate-100 text-slate-700 border-slate-200';
  const dotClass = DOT_STYLES[normalized] || 'bg-slate-400';

  const sizeClasses = size === 'lg' 
    ? 'px-3 py-1 text-sm font-semibold' 
    : 'px-2.5 py-0.5 text-xs font-medium';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${badgeClass} ${sizeClasses}`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${dotClass}`} />}
      {normalized}
    </span>
  );
}
