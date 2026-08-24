import React from 'react';

export default function KPICard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'blue',
}) {
  const THEMES = {
    blue: {
      card: 'bg-[#F4F8FE] border-blue-100/70',
      iconBg: 'bg-blue-100/80 text-blue-600',
      valueColor: 'text-slate-800',
      subColor: 'text-slate-500',
    },
    amber: {
      card: 'bg-[#FFFBF2] border-amber-100/80',
      iconBg: 'bg-amber-100/90 text-amber-600',
      valueColor: 'text-slate-800',
      subColor: 'text-slate-500',
    },
    rose: {
      card: 'bg-[#FEF5F5] border-rose-100/80',
      iconBg: 'bg-rose-100/90 text-rose-600',
      valueColor: 'text-slate-800',
      subColor: 'text-slate-500',
    },
    green: {
      card: 'bg-[#F2FAF6] border-emerald-100/80',
      iconBg: 'bg-emerald-100/90 text-emerald-600',
      valueColor: 'text-slate-800',
      subColor: 'text-slate-500',
    },
    lilac: {
      card: 'bg-[#F8F6FF] border-purple-100/80',
      iconBg: 'bg-purple-100/90 text-purple-600',
      valueColor: 'text-slate-800',
      subColor: 'text-slate-500',
    },
  };

  const theme = THEMES[variant] || THEMES.blue;

  return (
    <div className={`p-4 rounded-2xl border ${theme.card} shadow-subtle flex flex-col justify-between transition hover:shadow-card relative overflow-hidden`}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <span className="text-xs font-semibold text-slate-500 tracking-tight block">
            {title}
          </span>
          <div className="flex items-baseline gap-2">
            <span className={`text-2xl font-bold tracking-tight ${theme.valueColor}`}>
              {value}
            </span>
          </div>
        </div>
        {Icon && (
          <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${theme.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between">
        <span className={`text-xs ${theme.subColor}`}>
          {subtitle}
        </span>
      </div>
    </div>
  );
}
