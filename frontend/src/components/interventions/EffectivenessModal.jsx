import React, { useState, useEffect } from 'react';
import {
  X,
  TrendingDown,
  TrendingUp,
  Minus,
  Clock,
  HelpCircle,
  Calendar,
  ShieldAlert,
  Info,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { getInterventionEffectiveness } from '../../utils/api';
import RiskBadge from '../common/RiskBadge';
import TrendBadge from '../common/TrendBadge';

const CLASSIFICATION_STYLES = {
  IMPROVED: {
    badge: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    icon: TrendingDown,
    color: 'text-emerald-700',
    bg: 'bg-emerald-50/60 border-emerald-100',
  },
  STABLE: {
    badge: 'bg-blue-50 text-blue-800 border-blue-200',
    icon: Minus,
    color: 'text-blue-700',
    bg: 'bg-blue-50/60 border-blue-100',
  },
  WORSENED: {
    badge: 'bg-rose-50 text-rose-800 border-rose-200',
    icon: TrendingUp,
    color: 'text-rose-700',
    bg: 'bg-rose-50/60 border-rose-100',
  },
  AWAITING_REASSESSMENT: {
    badge: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: Clock,
    color: 'text-slate-600',
    bg: 'bg-slate-50 border-slate-100',
  },
  INSUFFICIENT_DATA: {
    badge: 'bg-slate-100 text-slate-500 border-slate-200',
    icon: HelpCircle,
    color: 'text-slate-500',
    bg: 'bg-slate-50 border-slate-100',
  },
};

export default function EffectivenessModal({ isOpen, onClose, interventionId }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && interventionId) {
      setLoading(true);
      setError(null);
      getInterventionEffectiveness(interventionId)
        .then((res) => {
          setData(res);
        })
        .catch((err) => {
          console.error('Failed to load effectiveness:', err);
          setError(err.message || 'Unable to retrieve trajectory analysis.');
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setData(null);
    }
  }, [isOpen, interventionId]);

  if (!isOpen) return null;

  const style = CLASSIFICATION_STYLES[data?.classification] || CLASSIFICATION_STYLES.INSUFFICIENT_DATA;
  const IconComp = style.icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl shadow-xl border border-slate-100 max-w-xl w-full overflow-hidden animate-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
              <Activity className="w-4 h-4 text-brand-600" />
              <span>Observed Risk Trajectory Comparison</span>
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {data?.title || 'Intervention Analysis'} &bull; ID #{interventionId}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-50 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Non-causal Disclaimer */}
          <div className="p-3 bg-slate-50 border border-slate-200/80 rounded-xl flex items-start gap-2 text-xs text-slate-600 leading-relaxed">
            <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <span>
              {data?.disclaimer ||
                'Observed changes describe student risk assessments over time and do not establish that an intervention caused the change.'}
            </span>
          </div>

          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-400 space-y-2">
              <div className="w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              <span className="text-xs">Analyzing risk snapshots...</span>
            </div>
          ) : error ? (
            <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-800">
              {error}
            </div>
          ) : (
            <>
              {/* Classification Banner */}
              <div className={`p-4 rounded-xl border ${style.bg} space-y-2`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-700">Observed Trajectory Status</span>
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold border uppercase tracking-wider ${style.badge}`}
                  >
                    <IconComp className="w-3.5 h-3.5" />
                    <span>{data.classification.replace('_', ' ')}</span>
                  </span>
                </div>
                <p className="text-xs text-slate-700 font-medium">
                  {data.interpretation}
                </p>
              </div>

              {/* Before vs After Side-by-Side */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 pt-1">
                {/* Pre-Intervention Baseline */}
                <div className="p-4 bg-slate-50/70 border border-slate-100 rounded-xl space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Pre-Intervention Baseline
                    </span>
                  </div>

                  {data.before ? (
                    <div className="space-y-2">
                      <div className="flex items-baseline gap-1.5">
                        <span className="text-2xl font-bold text-slate-800">
                          {data.before.score.toFixed(1)}
                        </span>
                        <span className="text-xs text-slate-400">/ 100</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <RiskBadge tier={data.before.risk_tier} />
                        <TrendBadge trend={data.before.trend} />
                      </div>

                      <p className="text-[10px] text-slate-400 flex items-center gap-1 font-mono pt-1">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(data.before.computed_at).toLocaleDateString()}</span>
                      </p>
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 py-3 italic">
                      No baseline assessment found prior to intervention creation.
                    </p>
                  )}
                </div>

                {/* Latest Post-Intervention */}
                <div className="p-4 bg-slate-50/70 border border-slate-100 rounded-xl space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Latest Assessment
                    </span>
                  </div>

                  {data.after ? (
                    <div className="space-y-2">
                      <div className="flex items-baseline gap-1.5">
                        <span className="text-2xl font-bold text-slate-800">
                          {data.after.score.toFixed(1)}
                        </span>
                        <span className="text-xs text-slate-400">/ 100</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <RiskBadge tier={data.after.risk_tier} />
                        <TrendBadge trend={data.after.trend} />
                      </div>

                      <p className="text-[10px] text-slate-400 flex items-center gap-1 font-mono pt-1">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(data.after.computed_at).toLocaleDateString()}</span>
                      </p>
                    </div>
                  ) : (
                    <div className="py-2 space-y-1">
                      <p className="text-xs font-semibold text-slate-600">
                        Awaiting new assessment
                      </p>
                      <p className="text-[11px] text-slate-400">
                        Compute and persist a new snapshot on the student's profile to observe changes.
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Observed Transition Detail */}
              {data.score_delta !== null && (
                <div className="p-3.5 bg-white border border-slate-200/80 rounded-xl space-y-2 text-xs">
                  <span className="font-semibold text-slate-700 block">Assessment Transitions</span>
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="p-2 bg-slate-50 rounded-lg">
                      <span className="text-[10px] text-slate-400 block">Score Delta</span>
                      <span
                        className={`font-bold text-sm ${
                          data.score_delta < 0
                            ? 'text-emerald-700'
                            : data.score_delta > 0
                            ? 'text-rose-700'
                            : 'text-slate-700'
                        }`}
                      >
                        {data.score_delta > 0 ? `+${data.score_delta}` : `${data.score_delta}`} pts
                      </span>
                    </div>

                    <div className="p-2 bg-slate-50 rounded-lg">
                      <span className="text-[10px] text-slate-400 block">Tier Shift</span>
                      <span className="font-bold text-slate-800 text-xs truncate block" title={data.tier_transition}>
                        {data.tier_transition}
                      </span>
                    </div>

                    <div className="p-2 bg-slate-50 rounded-lg">
                      <span className="text-[10px] text-slate-400 block">Trend Shift</span>
                      <span className="font-bold text-slate-800 text-xs truncate block" title={data.trend_transition}>
                        {data.trend_transition}
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-900 text-white rounded-xl text-xs font-semibold transition cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
