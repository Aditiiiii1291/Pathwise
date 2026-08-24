import React from 'react';
import { TrendingUp, TrendingDown, Minus, ArrowDownRight } from 'lucide-react';

const TREND_CONFIG = {
  IMPROVING: {
    label: 'Improving',
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
    icon: TrendingUp,
    iconColor: 'text-emerald-500',
  },
  STABLE: {
    label: 'Stable',
    badge: 'bg-blue-50 text-blue-700 border-blue-200/60',
    icon: Minus,
    iconColor: 'text-blue-500',
  },
  GRADUALLY_DETERIORATING: {
    label: 'Gradually Deteriorating',
    badge: 'bg-amber-50 text-amber-700 border-amber-200/60',
    icon: ArrowDownRight,
    iconColor: 'text-amber-500',
  },
  RAPIDLY_DETERIORATING: {
    label: 'Rapidly Deteriorating',
    badge: 'bg-rose-50 text-rose-700 border-rose-200/60',
    icon: TrendingDown,
    iconColor: 'text-rose-500',
  },
};

export default function TrendBadge({ trend, size = 'sm' }) {
  if (!trend) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-500 border border-slate-200">
        Unknown
      </span>
    );
  }

  const normalized = trend.toUpperCase();
  const config = TREND_CONFIG[normalized] || {
    label: trend,
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: Minus,
    iconColor: 'text-slate-400',
  };

  const IconComponent = config.icon;
  const sizeClasses = size === 'lg' 
    ? 'px-3 py-1 text-sm font-semibold' 
    : 'px-2.5 py-0.5 text-xs font-medium';

  return (
    <span className={`inline-flex items-center gap-1 rounded-full border ${config.badge} ${sizeClasses}`}>
      <IconComponent className={`w-3.5 h-3.5 ${config.iconColor}`} />
      <span>{config.label}</span>
    </span>
  );
}
