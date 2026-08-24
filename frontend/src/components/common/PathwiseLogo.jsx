import React from 'react';
import { Sparkles } from 'lucide-react';

export default function PathwiseLogo({ size = 'md', showSubtitle = true }) {
  const iconSizes = {
    sm: 'w-6 h-6',
    md: 'w-8 h-8',
    lg: 'w-11 h-11',
  };

  const sparkleSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-6 h-6',
  };

  const titleSizes = {
    sm: 'text-sm font-bold',
    md: 'text-base font-bold',
    lg: 'text-2xl font-extrabold tracking-tight',
  };

  return (
    <div className="flex items-center gap-3 select-none">
      <div
        className={`${iconSizes[size] || iconSizes.md} rounded-xl bg-gradient-to-tr from-brand-500 to-teal-400 flex items-center justify-center text-white shadow-sm shrink-0`}
      >
        <Sparkles className={sparkleSizes[size] || sparkleSizes.md} />
      </div>
      <div>
        <h1 className={`${titleSizes[size] || titleSizes.md} text-slate-800 leading-tight`}>
          Pathwise
        </h1>
        {showSubtitle && (
          <p className="text-[11px] font-medium text-slate-400 leading-none mt-0.5">
            Student Retention & Early Warning
          </p>
        )}
      </div>
    </div>
  );
}
