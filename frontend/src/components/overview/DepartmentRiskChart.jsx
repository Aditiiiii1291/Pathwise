import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { Link } from 'react-router-dom';

export default function DepartmentRiskChart({ departmentData = [] }) {
  // Format data for chart
  const formattedData = departmentData.map((d) => ({
    name: d.department,
    Total: d.student_count,
    AtRisk: d.at_risk_count,
    Critical: d.critical_count,
    AvgScore: d.average_final_score,
  }));

  return (
    <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-card flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-xs font-bold text-slate-800 tracking-tight uppercase">
            Department Risk Overview
          </h3>
          <div className="flex items-center gap-3 text-[10px]">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-slate-300"></span> Total
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-amber-400"></span> At Risk
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-rose-500"></span> Critical
            </span>
          </div>
        </div>

        {formattedData.length > 0 ? (
          <div className="w-full h-36 mt-1">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                layout="vertical"
                data={formattedData}
                margin={{ top: 5, right: 10, left: 15, bottom: 5 }}
              >
                <XAxis type="number" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                <YAxis
                  type="category"
                  dataKey="name"
                  tick={{ fontSize: 10, fill: '#475569', fontWeight: 500 }}
                  width={35}
                />
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
                <Bar dataKey="Total" fill="#E2E8F0" radius={[0, 4, 4, 0]} barSize={6} />
                <Bar dataKey="AtRisk" fill="#F59E0B" radius={[0, 4, 4, 0]} barSize={6} />
                <Bar dataKey="Critical" fill="#EF4444" radius={[0, 4, 4, 0]} barSize={6} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div className="h-36 flex items-center justify-center text-xs text-slate-400">
            No departmental data available
          </div>
        )}
      </div>

      <div className="mt-2 pt-2.5 border-t border-slate-50 flex items-center justify-end">
        <Link
          to="/students"
          className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition"
        >
          View all departments &rarr;
        </Link>
      </div>
    </div>
  );
}
