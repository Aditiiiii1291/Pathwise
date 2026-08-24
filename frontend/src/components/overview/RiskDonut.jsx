import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { Link } from 'react-router-dom';

const RISK_COLORS = {
  LOW: '#10B981',      // Emerald
  MEDIUM: '#F59E0B',   // Amber
  HIGH: '#F97316',     // Orange
  CRITICAL: '#EF4444', // Red
};

export default function RiskDonut({ riskDistribution, totalAssessed = 0 }) {
  const data = [
    { name: 'Low', key: 'LOW', value: riskDistribution?.LOW || 0, color: RISK_COLORS.LOW },
    { name: 'Medium', key: 'MEDIUM', value: riskDistribution?.MEDIUM || 0, color: RISK_COLORS.MEDIUM },
    { name: 'High', key: 'HIGH', value: riskDistribution?.HIGH || 0, color: RISK_COLORS.HIGH },
    { name: 'Critical', key: 'CRITICAL', value: riskDistribution?.CRITICAL || 0, color: RISK_COLORS.CRITICAL },
  ].filter(d => d.value > 0);

  const displayData = data.length > 0 ? data : [
    { name: 'None', key: 'NONE', value: 1, color: '#E2E8F0' }
  ];

  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-card flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-bold text-slate-800 tracking-tight uppercase">
            Risk Distribution
          </h3>
        </div>

        <div className="flex items-center justify-between gap-4 mt-2">
          {/* Donut Chart with Center Text */}
          <div className="relative w-32 h-32 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={displayData}
                  innerRadius={36}
                  outerRadius={52}
                  paddingAngle={data.length > 1 ? 3 : 0}
                  dataKey="value"
                  stroke="none"
                >
                  {displayData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value, name) => [`${value} students`, name]}
                  contentStyle={{
                    backgroundColor: '#1E293B',
                    borderRadius: '8px',
                    border: 'none',
                    color: '#FFF',
                    fontSize: '11px',
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-sm font-bold text-slate-800 leading-none">
                {totalAssessed}
              </span>
              <span className="text-[9px] font-medium text-slate-400 mt-0.5">
                Students
              </span>
            </div>
          </div>

          {/* Legend Details */}
          <div className="space-y-1.5 flex-1 text-xs">
            {[
              { label: 'Low', key: 'LOW', color: 'bg-emerald-500', count: riskDistribution?.LOW || 0 },
              { label: 'Medium', key: 'MEDIUM', color: 'bg-amber-500', count: riskDistribution?.MEDIUM || 0 },
              { label: 'High', key: 'HIGH', color: 'bg-orange-500', count: riskDistribution?.HIGH || 0 },
              { label: 'Critical', key: 'CRITICAL', color: 'bg-rose-500', count: riskDistribution?.CRITICAL || 0 },
            ].map((item) => {
              const pct = totalAssessed > 0 ? ((item.count / totalAssessed) * 100).toFixed(1) : '0.0';
              return (
                <div key={item.key} className="flex items-center justify-between text-[11px]">
                  <div className="flex items-center gap-1.5">
                    <span className={`w-2 h-2 rounded-full ${item.color}`} />
                    <span className="text-slate-600">{item.label}</span>
                  </div>
                  <span className="font-semibold text-slate-800 font-mono">
                    {item.count} <span className="text-slate-400 font-normal">({pct}%)</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-50 flex items-center justify-end">
        <Link
          to="/students"
          className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition"
        >
          View full breakdown &rarr;
        </Link>
      </div>
    </div>
  );
}
