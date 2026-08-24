import React from 'react';
import { AlertCircle, RefreshCw, CheckCircle, Server, ExternalLink } from 'lucide-react';
import PathwiseLogo from '../components/common/PathwiseLogo';
import { API_BASE_URL } from '../utils/api';

export default function ConnectionStatusPage({
  status = 'checking', // checking | connected | unavailable
  serviceInfo = null,
  onRetry,
}) {
  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-6 font-sans text-slate-800 antialiased">
      <div className="max-w-md w-full text-center space-y-6">
        {/* Brand Header */}
        <div className="flex justify-center">
          <PathwiseLogo size="lg" />
        </div>

        {/* Status Card */}
        <div className="bg-white border border-slate-100 rounded-3xl p-8 shadow-card space-y-6">
          {/* 1. CHECKING STATE */}
          {status === 'checking' && (
            <div className="space-y-4 py-4">
              <div className="w-12 h-12 border-3 border-brand-200 border-t-brand-600 rounded-full animate-spin mx-auto" />
              <div className="space-y-1">
                <h2 className="text-base font-bold text-slate-800">
                  Starting Pathwise...
                </h2>
                <p className="text-xs text-slate-500">
                  Verifying Pathwise service availability
                </p>
              </div>
            </div>
          )}

          {/* 2. CONNECTED STATE */}
          {status === 'connected' && (
            <div className="space-y-4 py-4">
              <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs">
                <CheckCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h2 className="text-base font-bold text-slate-800">
                  Pathwise is Ready
                </h2>
                <p className="text-xs text-emerald-600 font-medium">
                  Connected to {serviceInfo || 'pathwise-api'}
                </p>
              </div>
            </div>
          )}

          {/* 3. UNAVAILABLE STATE */}
          {status === 'unavailable' && (
            <div className="space-y-5">
              <div className="w-14 h-14 bg-rose-50 text-rose-600 rounded-2xl flex items-center justify-center mx-auto shadow-xs">
                <AlertCircle className="w-7 h-7" />
              </div>

              <div className="space-y-1.5">
                <h2 className="text-base font-bold text-slate-800">
                  Backend Service Unavailable
                </h2>
                <p className="text-xs text-slate-500 leading-relaxed max-w-sm mx-auto">
                  The Pathwise frontend was unable to establish a connection with the backend API.
                </p>
              </div>

              {/* Troubleshooting helper */}
              <div className="p-3.5 bg-slate-50 border border-slate-200/70 rounded-xl text-left text-xs space-y-1.5 text-slate-600">
                <div className="flex items-center gap-1.5 font-semibold text-slate-700">
                  <Server className="w-3.5 h-3.5 text-brand-600" />
                  <span>Troubleshooting Checklist</span>
                </div>
                <ul className="text-[11px] list-disc list-inside space-y-0.5 text-slate-500">
                  <li>Verify FastAPI backend is running</li>
                  <li>Server expected at: <code className="font-mono text-slate-700 bg-white px-1 py-0.5 rounded border border-slate-200">{API_BASE_URL}</code></li>
                  <li>Check terminal logs for backend errors</li>
                </ul>
              </div>

              <button
                onClick={onRetry}
                className="w-full py-2.5 px-4 bg-brand-600 hover:bg-brand-500 text-white font-semibold rounded-xl text-xs shadow-md transition flex items-center justify-center gap-2 cursor-pointer"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Retry Connection</span>
              </button>
            </div>
          )}
        </div>

        <p className="text-[11px] text-slate-400">
          Pathwise Early Warning & Retention Platform
        </p>
      </div>
    </div>
  );
}
