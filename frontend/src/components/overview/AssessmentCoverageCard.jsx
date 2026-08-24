import React from 'react';
import { ShieldCheck, Users, Activity, AlertTriangle } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function AssessmentCoverageCard({
  totalStudents = 0,
  assessedStudents = 0,
  averageFinalScore = 0.0,
  atRiskCount = 0,
}) {
  const coveragePct = totalStudents > 0
    ? ((assessedStudents / totalStudents) * 100).toFixed(1)
    : '0.0';

  const unassessedCount = Math.max(0, totalStudents - assessedStudents);

  const atRiskRate = assessedStudents > 0
    ? ((atRiskCount / assessedStudents) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-card flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-xs font-bold text-slate-800 tracking-tight uppercase">
            Assessment Coverage & Cohort Health
          </h3>
          <span className="text-[10px] font-semibold text-brand-700 bg-brand-50 border border-brand-200/80 px-2 py-0.5 rounded-full">
            {coveragePct}% Assessed
          </span>
        </div>

        <div className="space-y-3 mt-2">
          {/* Coverage Bar */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500 font-medium">Evaluation Coverage</span>
              <span className="font-semibold text-slate-800">
                {assessedStudents} / {totalStudents} students
              </span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-500 rounded-full transition-all duration-300"
                style={{ width: `${Math.min(100, Math.max(0, parseFloat(coveragePct)))}%` }}
              />
            </div>
          </div>

          {/* Core Metric Highlights */}
          <div className="grid grid-cols-2 gap-2 pt-1">
            <div className="p-2.5 bg-slate-50 border border-slate-100 rounded-xl">
              <span className="text-[10px] font-semibold uppercase text-slate-400 block">
                Average Risk Score
              </span>
              <span className="text-sm font-bold text-slate-800 mt-0.5 block">
                {averageFinalScore.toFixed(1)} <span className="text-[10px] text-slate-400 font-normal">/ 100</span>
              </span>
            </div>

            <div className="p-2.5 bg-slate-50 border border-slate-100 rounded-xl">
              <span className="text-[10px] font-semibold uppercase text-slate-400 block">
                At-Risk Ratio
              </span>
              <span className="text-sm font-bold text-amber-600 mt-0.5 block">
                {atRiskRate}% <span className="text-[10px] text-slate-400 font-normal">({atRiskCount})</span>
              </span>
            </div>
          </div>

          {/* Unassessed status */}
          {unassessedCount > 0 ? (
            <p className="text-[11px] text-slate-500 leading-normal">
              <strong className="text-slate-700">{unassessedCount}</strong> student records awaiting initial risk evaluation.
            </p>
          ) : (
            <p className="text-[11px] text-emerald-700 font-medium leading-normal flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Complete cohort evaluated with active risk assessments.</span>
            </p>
          )}
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-50 flex items-center justify-end">
        <Link
          to="/students"
          className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition"
        >
          View assessment roster &rarr;
        </Link>
      </div>
    </div>
  );
}
