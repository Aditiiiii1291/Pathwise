import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  HeartHandshake,
  Plus,
  Filter,
  RefreshCw,
  User,
  Calendar,
  Clock,
  CheckCircle2,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Edit2,
  FileText,
} from 'lucide-react';
import { getInterventions, getInterventionsSummary } from '../utils/api';
import InterventionModal from '../components/interventions/InterventionModal';
import { SkeletonTable } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

const STATUS_BADGES = {
  PLANNED: 'bg-blue-50 text-blue-700 border-blue-200',
  IN_PROGRESS: 'bg-amber-50 text-amber-700 border-amber-200',
  COMPLETED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  CANCELLED: 'bg-slate-100 text-slate-500 border-slate-200',
};

const CATEGORY_NAMES = {
  COUNSELLING: 'Counselling',
  ACADEMIC_SUPPORT: 'Academic Support',
  ATTENDANCE_SUPPORT: 'Attendance Plan',
  FINANCIAL_GUIDANCE: 'Financial Guidance',
  MENTOR_MEETING: 'Mentor Meeting',
  GUARDIAN_CONTACT: 'Guardian Contact',
  STUDY_PLAN: 'Study Plan',
  OTHER: 'Other Support',
};

export default function InterventionsPage() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [followUpsDueOnly, setFollowUpsDueOnly] = useState(false);

  const [data, setData] = useState({ items: [], total: 0, pages: 1 });
  const [summary, setSummary] = useState({
    total_interventions: 0,
    active_count: 0,
    planned_count: 0,
    completed_count: 0,
    cancelled_count: 0,
    follow_ups_due_count: 0,
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalInitialData, setModalInitialData] = useState(null);
  const [successToast, setSuccessToast] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [listRes, summaryRes] = await Promise.all([
        getInterventions({
          page,
          pageSize,
          status: selectedStatus,
          interventionType: selectedType,
          followUpsDue: followUpsDueOnly,
        }),
        getInterventionsSummary(),
      ]);
      setData(listRes);
      setSummary(summaryRes);
    } catch (err) {
      console.error('Failed to load interventions:', err);
      setError(err.message || 'Unable to retrieve intervention records.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, selectedStatus, selectedType, followUpsDueOnly]);

  const handleOpenCreate = () => {
    setModalInitialData(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (item, e) => {
    e.stopPropagation();
    setModalInitialData(item);
    setIsModalOpen(true);
  };

  const handleModalSuccess = (saved) => {
    setSuccessToast(`Intervention "${saved.title}" saved successfully.`);
    setTimeout(() => setSuccessToast(null), 3500);
    fetchData();
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-800 flex items-center gap-2">
            <HeartHandshake className="w-5 h-5 text-brand-600" />
            Interventions & Support Management
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Record, coordinate, and review student counselling actions and academic support plans
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-2 bg-white border border-slate-200 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-50 shadow-subtle transition disabled:opacity-50 cursor-pointer"
            title="Refresh list"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>

          <button
            onClick={handleOpenCreate}
            className="px-3.5 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl text-xs font-semibold shadow-sm transition flex items-center gap-1.5 cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>Record Intervention</span>
          </button>
        </div>
      </div>

      {successToast && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-medium animate-in fade-in flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{successToast}</span>
        </div>
      )}

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-card">
          <p className="text-[11px] font-medium text-slate-400">Total Actions</p>
          <p className="text-xl font-bold text-slate-800 mt-1">{summary.total_interventions}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Logged records</p>
        </div>

        <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-card">
          <p className="text-[11px] font-medium text-amber-600">Active in Progress</p>
          <p className="text-xl font-bold text-amber-700 mt-1">{summary.active_count}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Ongoing support</p>
        </div>

        <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-card">
          <p className="text-[11px] font-medium text-blue-600">Planned / Scheduled</p>
          <p className="text-xl font-bold text-blue-700 mt-1">{summary.planned_count}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Awaiting meeting</p>
        </div>

        <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-card">
          <p className="text-[11px] font-medium text-emerald-600">Completed</p>
          <p className="text-xl font-bold text-emerald-700 mt-1">{summary.completed_count}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Actions resolved</p>
        </div>

        <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-card col-span-2 sm:col-span-1">
          <p className="text-[11px] font-medium text-rose-600 flex items-center justify-between">
            <span>Follow-ups Due</span>
            {summary.follow_ups_due_count > 0 && (
              <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            )}
          </p>
          <p className="text-xl font-bold text-rose-700 mt-1">{summary.follow_ups_due_count}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">Due today or prior</p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-card flex flex-wrap items-center justify-between gap-3 text-xs">
        {/* Status Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => {
              setSelectedStatus('');
              setFollowUpsDueOnly(false);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl font-medium transition cursor-pointer ${
              !selectedStatus && !followUpsDueOnly
                ? 'bg-slate-800 text-white font-semibold shadow-xs'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            All ({summary.total_interventions})
          </button>

          <button
            onClick={() => {
              setSelectedStatus('IN_PROGRESS');
              setFollowUpsDueOnly(false);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl font-medium transition cursor-pointer ${
              selectedStatus === 'IN_PROGRESS'
                ? 'bg-amber-100 text-amber-800 font-semibold shadow-xs border border-amber-200'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            Active ({summary.active_count})
          </button>

          <button
            onClick={() => {
              setSelectedStatus('PLANNED');
              setFollowUpsDueOnly(false);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl font-medium transition cursor-pointer ${
              selectedStatus === 'PLANNED'
                ? 'bg-blue-100 text-blue-800 font-semibold shadow-xs border border-blue-200'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            Planned ({summary.planned_count})
          </button>

          <button
            onClick={() => {
              setSelectedStatus('COMPLETED');
              setFollowUpsDueOnly(false);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl font-medium transition cursor-pointer ${
              selectedStatus === 'COMPLETED'
                ? 'bg-emerald-100 text-emerald-800 font-semibold shadow-xs border border-emerald-200'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            Completed ({summary.completed_count})
          </button>

          <button
            onClick={() => {
              setFollowUpsDueOnly(!followUpsDueOnly);
              setSelectedStatus('');
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-xl font-medium transition cursor-pointer flex items-center gap-1.5 ${
              followUpsDueOnly
                ? 'bg-rose-100 text-rose-800 font-semibold shadow-xs border border-rose-200'
                : 'bg-slate-50 text-slate-600 hover:bg-slate-100'
            }`}
          >
            <span>Follow-ups Due</span>
            {summary.follow_ups_due_count > 0 && (
              <span className="px-1.5 py-0.2 bg-rose-500 text-white text-[10px] font-bold rounded-full">
                {summary.follow_ups_due_count}
              </span>
            )}
          </button>
        </div>

        {/* Category Dropdown */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 font-medium">Category:</span>
          <select
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          >
            <option value="">All Categories</option>
            {Object.entries(CATEGORY_NAMES).map(([val, label]) => (
              <option key={val} value={val}>
                {label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Table View */}
      {error ? (
        <ErrorState title="Error loading interventions" message={error} onRetry={fetchData} />
      ) : loading ? (
        <SkeletonTable rows={6} />
      ) : data.items.length === 0 ? (
        <EmptyState
          title="No interventions found"
          message="Record a counselling session or academic support action to begin tracking student interventions."
          actionText="+ Record First Intervention"
          onAction={handleOpenCreate}
        />
      ) : (
        <div className="bg-white border border-slate-100 rounded-2xl shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50/70 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                  <th className="py-3.5 px-4">Student</th>
                  <th className="py-3.5 px-4">Intervention Title & Type</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Follow-up Date</th>
                  <th className="py-3.5 px-4">Created Date</th>
                  <th className="py-3.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.items.map((item) => {
                  const statusBadge = STATUS_BADGES[item.status] || STATUS_BADGES.PLANNED;
                  const categoryLabel = CATEGORY_NAMES[item.intervention_type] || item.intervention_type;
                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-slate-50/80 transition group"
                    >
                      {/* Student Info */}
                      <td className="py-3.5 px-4">
                        <Link
                          to={`/students/${item.student_id}`}
                          className="font-bold text-slate-800 hover:text-brand-600 transition block"
                        >
                          {item.student_name || `Student #${item.student_id}`}
                        </Link>
                        <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-mono mt-0.5">
                          <span>{item.student_roll || `ID: ${item.student_id}`}</span>
                          {item.student_dept && <span>&bull; {item.student_dept}</span>}
                        </div>
                      </td>

                      {/* Title & Type */}
                      <td className="py-3.5 px-4 max-w-xs">
                        <p className="font-semibold text-slate-800 leading-snug line-clamp-1">
                          {item.title}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[10px] font-medium px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md">
                            {categoryLabel}
                          </span>
                          {item.notes && (
                            <span className="text-[10px] text-slate-400 line-clamp-1 italic max-w-[180px]">
                              "{item.notes}"
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-block px-2.5 py-1 rounded-lg text-[10px] font-bold border uppercase tracking-wider ${statusBadge}`}
                        >
                          {item.status.replace('_', ' ')}
                        </span>
                      </td>

                      {/* Follow-up Date */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {item.follow_up_date ? (
                          <div className="flex items-center gap-1.5">
                            <Calendar className="w-3.5 h-3.5 text-slate-400" />
                            <span className="font-medium text-slate-700">{item.follow_up_date}</span>
                            {item.is_follow_up_due && (
                              <span className="px-1.5 py-0.5 bg-rose-50 border border-rose-200 text-rose-700 text-[9px] font-bold rounded-md uppercase">
                                Due
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>

                      {/* Created Date */}
                      <td className="py-3.5 px-4 whitespace-nowrap text-slate-500">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString() : '—'}
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={(e) => handleOpenEdit(item, e)}
                          className="px-2.5 py-1 text-[11px] font-medium text-brand-700 bg-brand-50 hover:bg-brand-100 rounded-lg transition inline-flex items-center gap-1 cursor-pointer"
                        >
                          <Edit2 className="w-3 h-3" />
                          <span>Update</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination Toolbar */}
          <div className="p-4 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-500">
            <div>
              Showing <strong className="text-slate-800">{(page - 1) * pageSize + 1}</strong> to{' '}
              <strong className="text-slate-800">{Math.min(page * pageSize, data.total)}</strong> of{' '}
              <strong className="text-slate-800">{data.total}</strong> records
            </div>

            <div className="flex items-center gap-2 self-center sm:self-auto">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>

              <span className="px-2 font-medium text-slate-700">
                Page {page} of {data.pages || 1}
              </span>

              <button
                disabled={page >= data.pages}
                onClick={() => setPage((p) => p + 1)}
                className="p-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Intervention Modal */}
      <InterventionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleModalSuccess}
        initialData={modalInitialData}
      />
    </div>
  );
}
