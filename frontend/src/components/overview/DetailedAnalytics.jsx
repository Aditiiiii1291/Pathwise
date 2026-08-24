import React, { useState } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';
import { ChevronDown, ChevronUp } from 'lucide-react';

const RISK_COLORS = {
  LOW: '#10B981',
  MEDIUM: '#F59E0B',
  HIGH: '#F97316',
  CRITICAL: '#EF4444',
};

const TREND_COLORS = {
  IMPROVING: '#10B981',
  STABLE: '#3B82F6',
  GRADUALLY_DETERIORATING: '#F59E0B',
  RAPIDLY_DETERIORATING: '#EF4444',
};

export default function DetailedAnalytics({
  overviewData,
  departmentData = [],
}) {
  const [isOpen, setIsOpen] = useState(true);

  // 1. Department Average Risk Score Benchmark (from real department analytics)
  const deptScoreData = departmentData.map((d) => ({
    name: d.department,
    avgScore: d.average_final_score,
  }));

  // 2. Department At-Risk Density (from real department analytics)
  const deptRiskDensityData = departmentData.map((d) => {
    const density = d.student_count > 0 ? (d.at_risk_count / d.student_count) * 100 : 0;
    return {
      name: d.department,
      density: parseFloat(density.toFixed(1)),
      atRiskCount: d.at_risk_count,
      totalCount: d.student_count,
    };
  });

  // 3. Risk Tier Composition (from real overview risk distribution)
  const totalAssessed = overviewData?.assessed_students || 0;
  const riskCompData = [
    { name: 'Low', count: overviewData?.risk_distribution?.LOW || 0, color: RISK_COLORS.LOW },
    { name: 'Medium', count: overviewData?.risk_distribution?.MEDIUM || 0, color: RISK_COLORS.MEDIUM },
    { name: 'High', count: overviewData?.risk_distribution?.HIGH || 0, color: RISK_COLORS.HIGH },
    { name: 'Critical', count: overviewData?.risk_distribution?.CRITICAL || 0, color: RISK_COLORS.CRITICAL },
  ].filter((d) => d.count > 0);

  // 4. Trend Trajectory Composition (from real overview trend distribution)
  const trendCompData = [
    { name: 'Improving', count: overviewData?.trend_distribution?.IMPROVING || 0, color: TREND_COLORS.IMPROVING },
    { name: 'Stable', count: overviewData?.trend_distribution?.STABLE || 0, color: TREND_COLORS.STABLE },
    { name: 'Gradual', count: overviewData?.trend_distribution?.GRADUALLY_DETERIORATING || 0, color: TREND_COLORS.GRADUALLY_DETERIORATING },
    { name: 'Rapid', count: overviewData?.trend_distribution?.RAPIDLY_DETERIORATING || 0, color: TREND_COLORS.RAPIDLY_DETERIORATING },
  ].filter((d) => d.count > 0);

  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-4">
      {/* Header with Collapsible Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-bold text-slate-800 tracking-tight">
            Detailed Cohort Analytics
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Verifiable institutional metrics and departmental distribution breakdowns
          </p>
        </div>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl transition"
          title={isOpen ? 'Collapse section' : 'Expand section'}
        >
          {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>
      </div>

      {isOpen && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 pt-2">
          {/* 1. Department Risk Score Benchmark */}
          <div className="p-4 bg-slate-50/50 border border-slate-100 rounded-xl flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-700 block mb-2">
              Department Avg. Score
            </span>
            {deptScoreData.length > 0 ? (
              <div className="h-36 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={deptScoreData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#64748B' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#94A3B8' }} />
                    <Tooltip
                      formatter={(val) => [`${val} / 100`, 'Avg Score']}
                      contentStyle={{ fontSize: '10px', borderRadius: '6px' }}
                    />
                    <Bar dataKey="avgScore" fill="#38BDF8" radius={[4, 4, 0, 0]} name="Avg Score" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-36 flex items-center justify-center text-xs text-slate-400">
                No departmental data
              </div>
            )}
            <span className="text-[10px] text-slate-400 mt-1 block text-right">Average Score per Dept</span>
          </div>

          {/* 2. Department At-Risk Density */}
          <div className="p-4 bg-slate-50/50 border border-slate-100 rounded-xl flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-700 block mb-2">
              Department At-Risk Rate (%)
            </span>
            {deptRiskDensityData.length > 0 ? (
              <div className="h-36 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={deptRiskDensityData} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#64748B' }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#94A3B8' }} />
                    <Tooltip
                      formatter={(val, name, item) => [
                        `${val}% (${item.payload.atRiskCount}/${item.payload.totalCount})`,
                        'At-Risk Density',
                      ]}
                      contentStyle={{ fontSize: '10px', borderRadius: '6px' }}
                    />
                    <Bar dataKey="density" fill="#F59E0B" radius={[4, 4, 0, 0]} name="At-Risk %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-36 flex items-center justify-center text-xs text-slate-400">
                No departmental data
              </div>
            )}
            <span className="text-[10px] text-slate-400 mt-1 block text-right">% of Students at Risk</span>
          </div>

          {/* 3. Risk Tier Composition */}
          <div className="p-4 bg-slate-50/50 border border-slate-100 rounded-xl flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-700 block mb-2">
              Risk Tier Breakdown
            </span>
            {riskCompData.length > 0 ? (
              <div className="h-36 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={riskCompData}
                      innerRadius={28}
                      outerRadius={44}
                      paddingAngle={3}
                      dataKey="count"
                      stroke="none"
                    >
                      {riskCompData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val, name) => [
                        `${val} students (${totalAssessed > 0 ? ((val / totalAssessed) * 100).toFixed(1) : 0}%)`,
                        name,
                      ]}
                      contentStyle={{ fontSize: '10px', borderRadius: '6px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-36 flex items-center justify-center text-xs text-slate-400">
                No assessment records
              </div>
            )}
            <div className="flex justify-around text-[10px] text-slate-500 mt-1">
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Low</span>
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> Med</span>
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-orange-500" /> High</span>
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-rose-500" /> Crit</span>
            </div>
          </div>

          {/* 4. Trend Trajectory Composition */}
          <div className="p-4 bg-slate-50/50 border border-slate-100 rounded-xl flex flex-col justify-between">
            <span className="text-xs font-semibold text-slate-700 block mb-2">
              Trajectory Progression
            </span>
            {trendCompData.length > 0 ? (
              <div className="h-36 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={trendCompData}
                      innerRadius={28}
                      outerRadius={44}
                      paddingAngle={3}
                      dataKey="count"
                      stroke="none"
                    >
                      {trendCompData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val, name) => [
                        `${val} students (${totalAssessed > 0 ? ((val / totalAssessed) * 100).toFixed(1) : 0}%)`,
                        name,
                      ]}
                      contentStyle={{ fontSize: '10px', borderRadius: '6px' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-36 flex items-center justify-center text-xs text-slate-400">
                No trend evaluations
              </div>
            )}
            <div className="flex justify-around text-[10px] text-slate-500 mt-1">
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-emerald-500" /> Imp</span>
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-blue-500" /> Stable</span>
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-amber-500" /> Grad</span>
              <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-rose-500" /> Rapid</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
