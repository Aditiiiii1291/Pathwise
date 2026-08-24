import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Save,
  CheckCircle,
  AlertTriangle,
  Info,
  RefreshCw,
  RotateCcw,
} from 'lucide-react';
import { getRulesConfig, updateRulesConfig } from '../utils/api';
import { SkeletonCard } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function RulesPage() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const [weights, setWeights] = useState({
    attendance: 0.3,
    marks: 0.25,
    backlogs: 0.15,
    fees: 0.1,
    trends: 0.2,
  });

  const [thresholds, setThresholds] = useState({
    attendance_min_pct: 75.0,
    attendance_drop_pp: 10.0,
    marks_passing_pct: 40.0,
    marks_drop_pp: 5.0,
    backlog_critical_count: 3,
    fee_overdue_days: 30,
  });

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const config = await getRulesConfig();
      if (config.weights) setWeights(config.weights);
      if (config.thresholds) setThresholds(config.thresholds);
    } catch (err) {
      console.error('Failed to load rules:', err);
      setError(err.message || 'Unable to retrieve rule engine configuration.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  const totalWeight = Object.values(weights).reduce((sum, val) => sum + (parseFloat(val) || 0), 0);
  const isWeightValid = Math.abs(totalWeight - 1.0) < 0.001;

  const handleWeightChange = (key, value) => {
    const num = parseFloat(value) || 0;
    setWeights((prev) => ({ ...prev, [key]: num }));
  };

  const handleThresholdChange = (key, value) => {
    const num = parseFloat(value) || 0;
    setThresholds((prev) => ({ ...prev, [key]: num }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    if (!isWeightValid) {
      setFeedback({
        type: 'error',
        text: `Weights currently sum to ${(totalWeight * 100).toFixed(1)}%. They must equal exactly 100.0%.`,
      });
      return;
    }

    setSaving(true);
    setFeedback(null);
    try {
      const updated = await updateRulesConfig({ weights, thresholds });
      if (updated.weights) setWeights(updated.weights);
      if (updated.thresholds) setThresholds(updated.thresholds);
      setFeedback({ type: 'success', text: 'Rule configuration successfully updated and saved!' });
      setTimeout(() => setFeedback(null), 5000);
    } catch (err) {
      setFeedback({ type: 'error', text: err.message || 'Failed to save configuration.' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-800 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-brand-600" />
            Rule Engine Configuration
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Adjust multi-factor weighting and institutional sensitivity thresholds
          </p>
        </div>

        <button
          onClick={fetchConfig}
          disabled={loading || saving}
          className="self-start sm:self-auto px-3 py-1.5 bg-white border border-slate-200/80 rounded-xl text-xs font-medium text-slate-600 shadow-subtle hover:bg-slate-50 transition flex items-center gap-1.5"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Reset to Loaded</span>
        </button>
      </div>

      {error ? (
        <ErrorState
          title="Unable to load rule configuration"
          message={error}
          onRetry={fetchConfig}
        />
      ) : loading ? (
        <div className="space-y-4">
          <SkeletonCard height="h-64" />
          <SkeletonCard height="h-64" />
        </div>
      ) : (
        <form onSubmit={handleSave} className="space-y-6">
          {/* Feedback Alert */}
          {feedback && (
            <div
              className={`p-4 rounded-2xl border flex items-center gap-3 text-xs ${
                feedback.type === 'success'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-rose-50 border-rose-200 text-rose-800'
              }`}
            >
              {feedback.type === 'success' ? (
                <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0" />
              )}
              <span className="font-medium">{feedback.text}</span>
            </div>
          )}

          {/* Card 1: Factor Weights Editor */}
          <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-100 gap-2">
              <div>
                <h3 className="text-sm font-bold text-slate-800">
                  Factor Risk Weights
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Proportional contributions to deterministic rule evaluation (Sum must equal 1.0)
                </p>
              </div>

              <div
                className={`px-3 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 self-start sm:self-auto border ${
                  isWeightValid
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-rose-50 text-rose-700 border-rose-200'
                }`}
              >
                {isWeightValid ? (
                  <>
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Sum: {(totalWeight * 100).toFixed(0)}% (Valid)</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                    <span>Sum: {(totalWeight * 100).toFixed(1)}% (Must be 100%)</span>
                  </>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {[
                { key: 'attendance', label: 'Attendance Factor', desc: 'Current level and consecutive drop triggers' },
                { key: 'marks', label: 'Academic Marks Factor', desc: 'Assessment failure and downward slopes' },
                { key: 'backlogs', label: 'Backlog / Attempt Factor', desc: 'Cumulative backlog volume and retakes' },
                { key: 'fees', label: 'Fee Context Factor', desc: 'Administrative billing verification flag' },
                { key: 'trends', label: 'Temporal Velocity Factor', desc: 'Multivariate deterioration rates' },
              ].map(({ key, label, desc }) => {
                const val = weights[key] !== undefined ? weights[key] : 0;
                return (
                  <div key={key} className="p-4 bg-slate-50/60 border border-slate-100 rounded-xl space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-semibold text-slate-800">
                        {label}
                      </label>
                      <div className="flex items-center gap-1">
                        <input
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={val}
                          onChange={(e) => handleWeightChange(key, e.target.value)}
                          className="w-16 px-2 py-1 bg-white border border-slate-200 rounded-lg text-xs font-mono font-semibold text-slate-800 text-right focus:outline-none focus:ring-1 focus:ring-brand-500"
                        />
                        <span className="text-xs font-medium text-slate-400">({(val * 100).toFixed(0)}%)</span>
                      </div>
                    </div>

                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={val}
                      onChange={(e) => handleWeightChange(key, e.target.value)}
                      className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-brand-500"
                    />
                    <p className="text-[11px] text-slate-400">{desc}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Card 2: Sensitivity Thresholds Editor */}
          <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-5">
            <div className="pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-800">
                Institutional Sensitivity Thresholds
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Exact benchmark boundaries required to trigger deterministic flags
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-3.5 bg-slate-50/60 border border-slate-100 rounded-xl space-y-1">
                <label className="text-xs font-semibold text-slate-700 block">
                  Min. Attendance (%)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={thresholds.attendance_min_pct || 75.0}
                  onChange={(e) => handleThresholdChange('attendance_min_pct', e.target.value)}
                  className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium"
                />
                <span className="text-[10px] text-slate-400 block">Default: 75.0%</span>
              </div>

              <div className="p-3.5 bg-slate-50/60 border border-slate-100 rounded-xl space-y-1">
                <label className="text-xs font-semibold text-slate-700 block">
                  Attendance Drop (pp)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={thresholds.attendance_drop_pp || 10.0}
                  onChange={(e) => handleThresholdChange('attendance_drop_pp', e.target.value)}
                  className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium"
                />
                <span className="text-[10px] text-slate-400 block">Default: 10.0 pp</span>
              </div>

              <div className="p-3.5 bg-slate-50/60 border border-slate-100 rounded-xl space-y-1">
                <label className="text-xs font-semibold text-slate-700 block">
                  Passing Marks (%)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={thresholds.marks_passing_pct || 40.0}
                  onChange={(e) => handleThresholdChange('marks_passing_pct', e.target.value)}
                  className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium"
                />
                <span className="text-[10px] text-slate-400 block">Default: 40.0%</span>
              </div>

              <div className="p-3.5 bg-slate-50/60 border border-slate-100 rounded-xl space-y-1">
                <label className="text-xs font-semibold text-slate-700 block">
                  Marks Drop (pp/stage)
                </label>
                <input
                  type="number"
                  step="0.5"
                  value={thresholds.marks_drop_pp || 5.0}
                  onChange={(e) => handleThresholdChange('marks_drop_pp', e.target.value)}
                  className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium"
                />
                <span className="text-[10px] text-slate-400 block">Default: 5.0 pp</span>
              </div>

              <div className="p-3.5 bg-slate-50/60 border border-slate-100 rounded-xl space-y-1">
                <label className="text-xs font-semibold text-slate-700 block">
                  Critical Backlogs (Count)
                </label>
                <input
                  type="number"
                  step="1"
                  value={thresholds.backlog_critical_count || 3}
                  onChange={(e) => handleThresholdChange('backlog_critical_count', e.target.value)}
                  className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium"
                />
                <span className="text-[10px] text-slate-400 block">Default: 3</span>
              </div>

              <div className="p-3.5 bg-slate-50/60 border border-slate-100 rounded-xl space-y-1">
                <label className="text-xs font-semibold text-slate-700 block">
                  Fee Overdue (Days)
                </label>
                <input
                  type="number"
                  step="1"
                  value={thresholds.fee_overdue_days || 30}
                  onChange={(e) => handleThresholdChange('fee_overdue_days', e.target.value)}
                  className="w-full px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs font-medium"
                />
                <span className="text-[10px] text-slate-400 block">Default: 30 days</span>
              </div>
            </div>
          </div>

          {/* Safety Notice Card */}
          <div className="p-4 bg-blue-50/60 border border-blue-100 rounded-2xl flex items-start gap-3 text-xs text-blue-900 leading-relaxed">
            <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold block">Configuration Immutability & ML Boundary Notice</span>
              <span>
                Rule changes modify future risk assessments only and do not rewrite previously recorded historical RiskSnapshot entries. Updating rule weights or thresholds does NOT retrain or alter the Random Forest ML prediction model.
              </span>
            </div>
          </div>

          {/* Submit Action Bar */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={saving || !isWeightValid}
              className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 text-white font-semibold rounded-xl text-xs shadow-md transition flex items-center gap-2"
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              <span>{saving ? 'Saving Configuration...' : 'Save Rule Configuration'}</span>
            </button>
          </div>
        </form>
      )}
    </div>
  );
}
