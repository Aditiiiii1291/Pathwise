import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  X,
  ChevronLeft,
  ChevronRight,
  User,
  GraduationCap,
  RefreshCw,
} from 'lucide-react';
import { getStudents } from '../utils/api';
import RiskBadge from '../components/common/RiskBadge';
import TrendBadge from '../components/common/TrendBadge';
import { SkeletonTable } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

const DEPARTMENTS = ['CE', 'CSE', 'ECE', 'EEE', 'ME'];
const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8];
const RISK_TIERS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
const TRENDS = [
  { value: 'IMPROVING', label: 'Improving' },
  { value: 'STABLE', label: 'Stable' },
  { value: 'GRADUALLY_DETERIORATING', label: 'Gradual Decline' },
  { value: 'RAPIDLY_DETERIORATING', label: 'Rapid Decline' },
];

export default function StudentsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  // State from URL search params or defaults
  const page = parseInt(searchParams.get('page') || '1', 10);
  const pageSize = parseInt(searchParams.get('page_size') || '20', 10);
  const search = searchParams.get('search') || '';
  const department = searchParams.get('department') || '';
  const semester = searchParams.get('semester') || '';
  const riskTier = searchParams.get('risk_tier') || '';
  const trend = searchParams.get('trend') || '';

  const [searchInput, setSearchInput] = useState(search);
  const [data, setData] = useState({ items: [], total: 0, pages: 1 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Sync searchInput when URL search param changes
  useEffect(() => {
    setSearchInput(search);
  }, [search]);

  const updateFilters = (newParams) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(newParams).forEach(([k, v]) => {
      if (v === '' || v === null || v === undefined) {
        next.delete(k);
      } else {
        next.set(k, v);
      }
    });
    // Reset to page 1 on filter changes unless page is explicitly given
    if (!newParams.page) {
      next.set('page', '1');
    }
    setSearchParams(next);
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    updateFilters({ search: searchInput });
  };

  const handleResetFilters = () => {
    setSearchInput('');
    setSearchParams({});
  };

  const fetchStudents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getStudents({
        page,
        pageSize,
        search,
        department,
        semester,
        riskTier,
        trend,
      });
      setData(res);
    } catch (err) {
      console.error('Failed to load students:', err);
      setError(err.message || 'Error loading student records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStudents();
  }, [page, pageSize, search, department, semester, riskTier, trend]);

  const hasActiveFilters = Boolean(search || department || semester || riskTier || trend);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-800">
            Student Cohort Roster
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage, filter, and review retention risk profiles across all departments
          </p>
        </div>

        <button
          onClick={fetchStudents}
          disabled={loading}
          className="self-start sm:self-auto px-3 py-1.5 bg-white border border-slate-200/80 rounded-xl text-xs font-medium text-slate-600 shadow-subtle hover:bg-slate-50 transition flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-card space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          {/* Search Bar */}
          <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-[200px]">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search by name or roll number..."
              className="w-full pl-9 pr-8 py-2 bg-slate-50 border border-slate-200/70 rounded-xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 focus:bg-white transition"
            />
            {searchInput && (
              <button
                type="button"
                onClick={() => {
                  setSearchInput('');
                  updateFilters({ search: '' });
                }}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </form>

          {/* Department Filter */}
          <select
            value={department}
            onChange={(e) => updateFilters({ department: e.target.value })}
            className="px-3 py-2 bg-slate-50 border border-slate-200/70 rounded-xl text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          >
            <option value="">All Departments</option>
            {DEPARTMENTS.map((dept) => (
              <option key={dept} value={dept}>
                {dept}
              </option>
            ))}
          </select>

          {/* Semester Filter */}
          <select
            value={semester}
            onChange={(e) => updateFilters({ semester: e.target.value })}
            className="px-3 py-2 bg-slate-50 border border-slate-200/70 rounded-xl text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          >
            <option value="">All Semesters</option>
            {SEMESTERS.map((sem) => (
              <option key={sem} value={sem}>
                Semester {sem}
              </option>
            ))}
          </select>

          {/* Risk Tier Filter */}
          <select
            value={riskTier}
            onChange={(e) => updateFilters({ risk_tier: e.target.value })}
            className="px-3 py-2 bg-slate-50 border border-slate-200/70 rounded-xl text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          >
            <option value="">All Risk Tiers</option>
            {RISK_TIERS.map((tier) => (
              <option key={tier} value={tier}>
                {tier} Risk
              </option>
            ))}
          </select>

          {/* Trend Filter */}
          <select
            value={trend}
            onChange={(e) => updateFilters({ trend: e.target.value })}
            className="px-3 py-2 bg-slate-50 border border-slate-200/70 rounded-xl text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
          >
            <option value="">All Trends</option>
            {TRENDS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>

          {/* Reset button */}
          {hasActiveFilters && (
            <button
              onClick={handleResetFilters}
              className="px-3 py-2 text-xs font-semibold text-rose-600 bg-rose-50 hover:bg-rose-100 rounded-xl transition flex items-center gap-1"
            >
              <X className="w-3.5 h-3.5" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      {/* Main Student Data Table */}
      {error ? (
        <ErrorState
          title="Error loading students"
          message={error}
          onRetry={fetchStudents}
        />
      ) : loading ? (
        <SkeletonTable rows={10} />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="No students match the selected filters"
          message="Try adjusting your search query, department, semester, or risk criteria."
          actionText="Reset all filters"
          onAction={handleResetFilters}
        />
      ) : (
        <div className="bg-white border border-slate-100 rounded-2xl shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50/70 border-b border-slate-100 text-slate-400 font-semibold uppercase text-[10px] tracking-wider">
                  <th className="py-3 px-4">Roll No.</th>
                  <th className="py-3 px-4">Student Name</th>
                  <th className="py-3 px-4">Dept</th>
                  <th className="py-3 px-4">Sem</th>
                  <th className="py-3 px-4">Mentor</th>
                  <th className="py-3 px-4">Final Score</th>
                  <th className="py-3 px-4">Risk Tier</th>
                  <th className="py-3 px-4">Observed Trend</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-50">
                {data.items.map((s) => {
                  const score = s.latest_final_score !== null && s.latest_final_score !== undefined
                    ? s.latest_final_score.toFixed(1)
                    : '—';

                  return (
                    <tr
                      key={s.id}
                      onClick={() => navigate(`/students/${s.id}`)}
                      className="hover:bg-slate-50/80 cursor-pointer transition"
                    >
                      <td className="py-3.5 px-4 font-mono font-medium text-slate-600">
                        {s.roll_number}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-800">
                        {s.name}
                      </td>
                      <td className="py-3.5 px-4 text-slate-600">
                        {s.department}
                      </td>
                      <td className="py-3.5 px-4 text-slate-600">
                        Sem {s.semester}
                      </td>
                      <td className="py-3.5 px-4 text-slate-500">
                        {s.mentor_name || '—'}
                      </td>
                      <td className="py-3.5 px-4 font-semibold text-slate-800">
                        {score}
                      </td>
                      <td className="py-3.5 px-4">
                        <RiskBadge tier={s.latest_risk_tier} />
                      </td>
                      <td className="py-3.5 px-4">
                        <TrendBadge trend={s.latest_trend} />
                      </td>
                      <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => navigate(`/students/${s.id}`)}
                          className="px-3 py-1 text-xs font-semibold text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100 rounded-lg transition"
                        >
                          Inspect Profile
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Toolbar */}
          <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-500">
            <div>
              Showing <strong className="text-slate-800">{(page - 1) * pageSize + 1}</strong> to{' '}
              <strong className="text-slate-800">{Math.min(page * pageSize, data.total)}</strong> of{' '}
              <strong className="text-slate-800">{data.total}</strong> students
            </div>

            <div className="flex items-center gap-2 self-center sm:self-auto">
              <button
                disabled={page <= 1}
                onClick={() => updateFilters({ page: page - 1 })}
                className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
                title="Previous page"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <span className="px-2 font-medium text-slate-700">
                Page {page} of {data.pages || 1}
              </span>

              <button
                disabled={page >= data.pages}
                onClick={() => updateFilters({ page: page + 1 })}
                className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
                title="Next page"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
