import React from 'react';
import { Inbox } from 'lucide-react';

export default function EmptyState({
  title = 'No records found',
  message = 'There is currently no data matching your criteria.',
  icon: Icon = Inbox,
  actionText,
  onAction,
}) {
  return (
    <div className="bg-slate-50/70 border border-slate-200/60 rounded-2xl p-8 text-center max-w-md mx-auto my-6 space-y-3">
      <div className="w-10 h-10 bg-slate-100 text-slate-400 rounded-full flex items-center justify-center mx-auto">
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        <p className="text-xs text-slate-500 mt-1 leading-relaxed">{message}</p>
      </div>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-brand-50 text-brand-700 border border-brand-200 rounded-lg hover:bg-brand-100 transition"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}
