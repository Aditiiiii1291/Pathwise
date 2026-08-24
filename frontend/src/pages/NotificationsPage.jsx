import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Bell,
  Check,
  CheckCheck,
  Filter,
  RefreshCw,
  User,
  ChevronLeft,
  ChevronRight,
  ShieldAlert,
  AlertTriangle,
  Info,
  Calendar,
} from 'lucide-react';
import { getNotifications, markNotificationAsRead, markAllNotificationsAsRead } from '../utils/api';
import { SkeletonTable } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

const SEVERITIES = ['CRITICAL', 'HIGH', 'WARNING', 'INFO'];

const SEVERITY_BADGES = {
  CRITICAL: 'bg-rose-50 text-rose-700 border-rose-200',
  HIGH: 'bg-orange-50 text-orange-700 border-orange-200',
  WARNING: 'bg-amber-50 text-amber-700 border-amber-200',
  INFO: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

function formatTimestamp(dateString) {
  if (!dateString) return '—';
  const d = new Date(dateString);
  return d.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function NotificationsPage() {
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [selectedSeverity, setSelectedSeverity] = useState('');
  const [data, setData] = useState({ items: [], total: 0, pages: 1, unread_count: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionMessage, setActionMessage] = useState(null);
  const navigate = useNavigate();

  const fetchNotifications = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getNotifications({
        page,
        pageSize,
        unreadOnly,
        severity: selectedSeverity,
      });
      setData(res);
    } catch (err) {
      console.error('Failed to load notifications:', err);
      setError(err.message || 'Unable to retrieve notification history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [page, unreadOnly, selectedSeverity]);

  const handleMarkOneRead = async (id, e) => {
    e.stopPropagation();
    try {
      await markNotificationAsRead(id);
      setData((prev) => ({
        ...prev,
        unread_count: Math.max(0, prev.unread_count - 1),
        items: prev.items.map((item) =>
          item.id === id ? { ...item, is_read: true } : item
        ),
      }));
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsAsRead();
      setData((prev) => ({
        ...prev,
        unread_count: 0,
        items: prev.items.map((item) => ({ ...item, is_read: true })),
      }));
      setActionMessage('All notifications marked as read.');
      setTimeout(() => setActionMessage(null), 3000);
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-800 flex items-center gap-2">
            <Bell className="w-5 h-5 text-brand-600" />
            Alert & Notification Center
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit log of student risk escalations, rapid trajectory deteriorations, and recovery milestones
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          {data.unread_count > 0 && (
            <button
              onClick={handleMarkAllRead}
              className="px-3 py-1.5 bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200/80 rounded-xl text-xs font-semibold shadow-subtle transition flex items-center gap-1.5 cursor-pointer"
            >
              <CheckCheck className="w-3.5 h-3.5" />
              <span>Mark all as read</span>
            </button>
          )}

          <button
            onClick={fetchNotifications}
            disabled={loading}
            className="p-2 bg-white border border-slate-200/80 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-50 shadow-subtle transition disabled:opacity-50 cursor-pointer"
            title="Refresh notifications"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {actionMessage && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs font-medium animate-in fade-in">
          {actionMessage}
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="bg-white border border-slate-100 rounded-2xl p-4 shadow-card flex flex-wrap items-center justify-between gap-3">
        {/* Unread / All Filter Tabs */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl text-xs font-medium">
          <button
            onClick={() => {
              setUnreadOnly(false);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer ${
              !unreadOnly
                ? 'bg-white text-slate-800 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            All Alerts ({data.total || 0})
          </button>
          <button
            onClick={() => {
              setUnreadOnly(true);
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg transition cursor-pointer flex items-center gap-1.5 ${
              unreadOnly
                ? 'bg-white text-slate-800 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-800'
            }`}
          >
            <span>Unread</span>
            {data.unread_count > 0 && (
              <span className="px-1.5 py-0.2 bg-rose-500 text-white text-[10px] font-bold rounded-full">
                {data.unread_count}
              </span>
            )}
          </button>
        </div>

        {/* Severity Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Severity:</span>
          <select
            value={selectedSeverity}
            onChange={(e) => {
              setSelectedSeverity(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-brand-500/20"
          >
            <option value="">All Severities</option>
            {SEVERITIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Notifications List */}
      {error ? (
        <ErrorState
          title="Error loading notifications"
          message={error}
          onRetry={fetchNotifications}
        />
      ) : loading ? (
        <SkeletonTable rows={6} />
      ) : data.items.length === 0 ? (
        <EmptyState
          title={unreadOnly ? 'No unread notifications' : 'No notifications yet'}
          message={
            unreadOnly
              ? 'All student risk alerts have been reviewed.'
              : 'New notifications will appear here when student risk assessments and transitions are evaluated.'
          }
          actionText={unreadOnly ? 'View all alerts' : undefined}
          onAction={unreadOnly ? () => setUnreadOnly(false) : undefined}
        />
      ) : (
        <div className="bg-white border border-slate-100 rounded-2xl shadow-card divide-y divide-slate-100 overflow-hidden">
          {data.items.map((n) => {
            const sevBadge = SEVERITY_BADGES[n.severity] || SEVERITY_BADGES.INFO;
            return (
              <div
                key={n.id}
                onClick={() => {
                  if (n.student_id) navigate(`/students/${n.student_id}`);
                }}
                className={`p-5 hover:bg-slate-50/80 transition cursor-pointer flex flex-col sm:flex-row sm:items-start justify-between gap-4 ${
                  !n.is_read ? 'bg-blue-50/20' : 'bg-white'
                }`}
              >
                <div className="flex items-start gap-3.5 flex-1">
                  {/* Unread indicator */}
                  <div className="mt-1 shrink-0">
                    {!n.is_read ? (
                      <span className="w-2.5 h-2.5 rounded-full bg-brand-500 block ring-4 ring-brand-100" />
                    ) : (
                      <span className="w-2.5 h-2.5 rounded-full bg-slate-200 block" />
                    )}
                  </div>

                  <div className="space-y-1.5 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded border uppercase tracking-wider ${sevBadge}`}
                      >
                        {n.severity}
                      </span>
                      <h3
                        className={`text-xs ${
                          !n.is_read ? 'font-bold text-slate-900' : 'font-semibold text-slate-700'
                        }`}
                      >
                        {n.title}
                      </h3>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {n.notification_type}
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
                      {n.message}
                    </p>

                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-slate-400 pt-1">
                      {n.student_name && (
                        <div className="flex items-center gap-1">
                          <User className="w-3 h-3" />
                          <span className="text-slate-700 font-medium">{n.student_name}</span>
                          <span className="font-mono text-slate-400">({n.student_roll})</span>
                          {n.student_dept && <span>&bull; {n.student_dept}</span>}
                        </div>
                      )}
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        <span>{formatTimestamp(n.created_at)}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Right Action Buttons */}
                <div
                  className="flex items-center gap-2 shrink-0 self-end sm:self-center"
                  onClick={(e) => e.stopPropagation()}
                >
                  {!n.is_read && (
                    <button
                      onClick={(e) => handleMarkOneRead(n.id, e)}
                      className="px-2.5 py-1 text-[11px] font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg transition"
                      title="Mark this alert as read"
                    >
                      Mark as read
                    </button>
                  )}

                  {n.student_id && (
                    <button
                      onClick={() => navigate(`/students/${n.student_id}`)}
                      className="px-3 py-1 text-xs font-semibold text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100 rounded-lg transition"
                    >
                      View Student Profile
                    </button>
                  )}
                </div>
              </div>
            );
          })}

          {/* Pagination Toolbar */}
          <div className="p-4 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-500">
            <div>
              Showing <strong className="text-slate-800">{(page - 1) * pageSize + 1}</strong> to{' '}
              <strong className="text-slate-800">{Math.min(page * pageSize, data.total)}</strong> of{' '}
              <strong className="text-slate-800">{data.total}</strong> alerts
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
    </div>
  );
}
