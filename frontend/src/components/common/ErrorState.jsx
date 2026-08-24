import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export default function ErrorState({
  title = 'Unable to load data',
  message = 'An unexpected error occurred while communicating with the server.',
  onRetry,
}) {
  return (
    <div className="bg-rose-50/60 border border-rose-200/80 rounded-2xl p-6 text-center max-w-lg mx-auto my-6 space-y-3">
      <div className="w-10 h-10 bg-rose-100 text-rose-600 rounded-full flex items-center justify-center mx-auto">
        <AlertCircle className="w-5 h-5" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-rose-900">{title}</h3>
        <p className="text-xs text-rose-700 mt-1 leading-relaxed">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-rose-600 text-white rounded-lg hover:bg-rose-500 transition shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Try Again
        </button>
      )}
    </div>
  );
}
