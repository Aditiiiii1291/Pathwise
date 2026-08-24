import React from 'react';

export function SkeletonCard({ height = 'h-32', className = '' }) {
  return (
    <div className={`bg-white border border-slate-100 rounded-2xl p-5 shadow-card animate-pulse ${height} ${className}`}>
      <div className="h-4 bg-slate-100 rounded w-1/3 mb-4"></div>
      <div className="h-8 bg-slate-100 rounded w-1/2 mb-2"></div>
      <div className="h-3 bg-slate-100 rounded w-2/3"></div>
    </div>
  );
}

export function SkeletonTable({ rows = 5 }) {
  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card animate-pulse space-y-4">
      <div className="h-5 bg-slate-100 rounded w-1/4 mb-4"></div>
      <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className="flex gap-4 py-2 border-b border-slate-50">
            <div className="h-4 bg-slate-100 rounded w-1/6"></div>
            <div className="h-4 bg-slate-100 rounded w-1/4"></div>
            <div className="h-4 bg-slate-100 rounded w-1/6"></div>
            <div className="h-4 bg-slate-100 rounded w-1/6"></div>
            <div className="h-4 bg-slate-100 rounded w-1/6"></div>
          </div>
        ))}
      </div>
    </div>
  );
}

export function LoadingSpinner({ text = 'Loading data...' }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-slate-400 space-y-3">
      <div className="w-8 h-8 border-2 border-brand-200 border-t-brand-500 rounded-full animate-spin"></div>
      <span className="text-sm font-medium text-slate-500">{text}</span>
    </div>
  );
}
