import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import RiskBadge from '../common/RiskBadge';
import TrendBadge from '../common/TrendBadge';
import { ArrowRight } from 'lucide-react';

export default function PriorityStudentTable({ students = [], total = 0, onOpenMentorPanel }) {
  const navigate = useNavigate();

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Priority Student Table (Left 2 Columns) */}
      <div className="lg:col-span-2 bg-white border border-slate-100 rounded-2xl p-6 shadow-card flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-800 tracking-tight">
                Students Needing Attention
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Priority students requiring immediate mentor follow-up
              </p>
            </div>
            <Link
              to="/students?risk_tier=CRITICAL"
              className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition"
            >
              View all critical students &rarr;
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-100 text-slate-400 font-semibold uppercase text-[10px]">
                  <th className="py-2.5 px-2">Roll No.</th>
                  <th className="py-2.5 px-2">Student Name</th>
                  <th className="py-2.5 px-2">Dept</th>
                  <th className="py-2.5 px-2">Sem</th>
                  <th className="py-2.5 px-2">Mentor</th>
                  <th className="py-2.5 px-2">Final Risk Score</th>
                  <th className="py-2.5 px-2">Risk Tier</th>
                  <th className="py-2.5 px-2">Observed Trend</th>
                  <th className="py-2.5 px-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {students.length > 0 ? (
                  students.slice(0, 5).map((s) => {
                    const score = s.latest_final_score !== null && s.latest_final_score !== undefined
                      ? s.latest_final_score.toFixed(1)
                      : '—';

                    return (
                      <tr key={s.id} className="hover:bg-slate-50/70 transition">
                        <td className="py-3 px-2 font-mono text-slate-600 font-medium">
                          {s.roll_number}
                        </td>
                        <td className="py-3 px-2 font-semibold text-slate-800">
                          {s.name}
                        </td>
                        <td className="py-3 px-2 text-slate-600">
                          {s.department}
                        </td>
                        <td className="py-3 px-2 text-slate-600">
                          Sem {s.semester}
                        </td>
                        <td className="py-3 px-2 text-slate-500">
                          {s.mentor_name || '—'}
                        </td>
                        <td className="py-3 px-2 font-semibold text-slate-800">
                          {score}
                        </td>
                        <td className="py-3 px-2">
                          <RiskBadge tier={s.latest_risk_tier} />
                        </td>
                        <td className="py-3 px-2">
                          <TrendBadge trend={s.latest_trend} />
                        </td>
                        <td className="py-3 px-2 text-right">
                          <button
                            onClick={() => navigate(`/students/${s.id}`)}
                            className="px-2.5 py-1 text-xs font-semibold text-brand-600 hover:text-brand-700 hover:bg-brand-50 rounded-lg transition"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={9} className="py-8 text-center text-slate-400 text-xs">
                      No students currently flagged in high-risk categories.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer pagination info */}
        <div className="mt-4 pt-3 border-t border-slate-50 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing priority students (<strong className="text-slate-700">{Math.min(5, students.length)}</strong> of <strong className="text-slate-700">{total}</strong> total)
          </span>
          <Link
            to="/students"
            className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition"
          >
            Explore all in Student Roster &rarr;
          </Link>
        </div>
      </div>

      {/* Mentor Action Panel Card (Right 1 Column) */}
      <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card flex flex-col justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-800 tracking-tight">
            Mentor Action Panel
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Open when you need to take action
          </p>

          <div className="my-6 flex flex-col items-center justify-center p-6 bg-slate-50/60 rounded-xl border border-slate-100/80 text-center space-y-2">
            <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center shadow-xs">
              <span className="text-xl">📋</span>
            </div>
            <span className="text-xs font-semibold text-slate-700">
              Student Intervention Console
            </span>
            <p className="text-[11px] text-slate-500 max-w-[200px] leading-relaxed">
              Launch mentor consultations, log advising notes, and assign support roadmaps.
            </p>
          </div>
        </div>

        <div className="space-y-2">
          <button
            onClick={onOpenMentorPanel}
            className="w-full py-2.5 px-4 bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200/80 font-semibold rounded-xl text-xs transition flex items-center justify-center gap-2 shadow-xs cursor-pointer"
          >
            <span>Open Action Panel</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
          <span className="text-[10px] text-slate-400 block text-center">
            🔒 Opens in a focused workspace
          </span>
        </div>
      </div>
    </div>
  );
}
