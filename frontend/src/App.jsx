import React, { useState, useEffect } from 'react';
import { checkHealth } from './utils/api';
import { ShieldAlert, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

export default function App() {
  const [healthStatus, setHealthStatus] = useState('checking'); // checking | connected | unavailable
  const [serviceInfo, setServiceInfo] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const fetchHealth = async () => {
    setHealthStatus('checking');
    const result = await checkHealth();
    if (result.status === 'healthy') {
      setHealthStatus('connected');
      setServiceInfo(result.service || 'pathwise-api');
    } else {
      setHealthStatus('unavailable');
      setServiceInfo(null);
    }
    setLastChecked(new Date().toLocaleTimeString());
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-6 font-sans">
      <div className="max-w-md w-full bg-slate-800 border border-slate-700 rounded-2xl p-8 shadow-2xl space-y-6">
        
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
            <ShieldAlert className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">PATHWISE</h1>
            <p className="text-xs text-slate-400 font-medium">Early Warning & Retention Platform</p>
          </div>
        </div>

        <div className="border-t border-slate-700/60 pt-4">
          <p className="text-sm text-slate-300">
            Phase 1 Foundation: Application and API connectivity verification.
          </p>
        </div>

        {/* Backend Connectivity Status Card */}
        <div className="bg-slate-900/80 border border-slate-700/80 rounded-xl p-5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
              Backend Status
            </span>
            {lastChecked && (
              <span className="text-xs text-slate-500 font-mono">
                Checked: {lastChecked}
              </span>
            )}
          </div>

          <div className="flex items-center gap-3">
            {healthStatus === 'checking' && (
              <>
                <RefreshCw className="w-5 h-5 text-amber-400 animate-spin" />
                <span className="text-amber-400 font-medium text-sm">Checking backend...</span>
              </>
            )}
            {healthStatus === 'connected' && (
              <>
                <CheckCircle className="w-5 h-5 text-emerald-400" />
                <div>
                  <span className="text-emerald-400 font-semibold text-sm">Connected</span>
                  {serviceInfo && (
                    <span className="text-xs text-slate-400 block font-mono">Service: {serviceInfo}</span>
                  )}
                </div>
              </>
            )}
            {healthStatus === 'unavailable' && (
              <>
                <AlertCircle className="w-5 h-5 text-rose-400" />
                <div>
                  <span className="text-rose-400 font-semibold text-sm">Unavailable</span>
                  <span className="text-xs text-slate-500 block">Start backend at http://127.0.0.1:8000</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Action Button */}
        <button
          onClick={fetchHealth}
          disabled={healthStatus === 'checking'}
          className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold rounded-xl text-sm transition flex items-center justify-center gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${healthStatus === 'checking' ? 'animate-spin' : ''}`} />
          Recheck Connection
        </button>
      </div>

      <p className="text-xs text-slate-500 mt-8 font-mono">
        Pathwise Phase 1: Repository & Application Foundation
      </p>
    </div>
  );
}
