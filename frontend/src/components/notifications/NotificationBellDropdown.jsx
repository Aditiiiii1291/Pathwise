import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Bell, Check, ExternalLink, ShieldAlert, AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { getNotifications, getUnreadNotificationCount, markNotificationAsRead, markAllNotificationsAsRead } from '../../utils/api';

const SEVERITY_STYLES = {
  CRITICAL: 'bg-rose-50 text-rose-700 border-rose-200',
  HIGH: 'bg-orange-50 text-orange-700 border-orange-200',
  WARNING: 'bg-amber-50 text-amber-700 border-amber-200',
  INFO: 'bg-emerald-50 text-emerald-700 border-emerald-200',
};

function formatRelativeTime(dateString) {
  if (!dateString) return '';
  const now = new Date();
  const date = new Date(dateString);
  const diffSec = Math.floor((now - date) / 1000);

  if (diffSec < 60) return 'Just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}d ago`;
  return date.toLocaleDateString();
}

export default function NotificationBellDropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  const fetchUnreadCount = async () => {
    try {
      const res = await getUnreadNotificationCount();
      setUnreadCount(res.unread_count || 0);
    } catch {
      // Graceful fallback
    }
  };

  const fetchRecentNotifications = async () => {
    setLoading(true);
    try {
      const res = await getNotifications({ page: 1, pageSize: 6 });
      setNotifications(res.items || []);
      setUnreadCount(res.unread_count || 0);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    // Poll every 30s for in-app alert updates
    const interval = setInterval(fetchUnreadCount, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchRecentNotifications();
    }
  }, [isOpen]);

  // Click outside listener
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleItemClick = async (notif) => {
    if (!notif.is_read) {
      try {
        await markNotificationAsRead(notif.id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
        );
        setUnreadCount((prev) => Math.max(0, prev - 1));
      } catch (err) {
        console.error('Failed to mark read:', err);
      }
    }
    setIsOpen(false);
    if (notif.student_id) {
      navigate(`/students/${notif.student_id}`);
    }
  };

  const handleMarkAllRead = async (e) => {
    e.stopPropagation();
    try {
      await markAllNotificationsAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all read:', err);
    }
  };

  const badgeText = unreadCount > 99 ? '99+' : unreadCount;

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Notification Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-50 rounded-xl transition cursor-pointer"
        title="In-App Notifications"
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 min-w-[16px] h-4 px-1 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center ring-2 ring-white">
            {badgeText}
          </span>
        )}
      </button>

      {/* Popover Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white border border-slate-100 rounded-2xl shadow-xl z-50 overflow-hidden animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-800">Notifications</span>
              {unreadCount > 0 && (
                <span className="text-[10px] font-semibold px-2 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded-full">
                  {unreadCount} new
                </span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-[11px] font-medium text-brand-600 hover:text-brand-700 transition flex items-center gap-1 cursor-pointer"
              >
                <Check className="w-3 h-3" />
                <span>Mark all as read</span>
              </button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto divide-y divide-slate-50">
            {loading ? (
              <div className="p-6 text-center text-xs text-slate-400">
                Loading notifications...
              </div>
            ) : notifications.length > 0 ? (
              notifications.map((n) => {
                const sevStyle = SEVERITY_STYLES[n.severity] || SEVERITY_STYLES.INFO;
                return (
                  <div
                    key={n.id}
                    onClick={() => handleItemClick(n)}
                    className={`p-3.5 hover:bg-slate-50 transition cursor-pointer flex items-start gap-3 ${
                      !n.is_read ? 'bg-blue-50/20' : 'bg-white'
                    }`}
                  >
                    {/* Unread indicator dot */}
                    <div className="mt-1 shrink-0">
                      {!n.is_read ? (
                        <span className="w-2 h-2 rounded-full bg-brand-500 block ring-2 ring-brand-100" />
                      ) : (
                        <span className="w-2 h-2 rounded-full bg-slate-200 block" />
                      )}
                    </div>

                    <div className="flex-1 space-y-1 min-w-0">
                      <div className="flex items-center justify-between gap-1">
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.5 rounded border uppercase tracking-wider ${sevStyle}`}
                        >
                          {n.severity}
                        </span>
                        <span className="text-[10px] text-slate-400">
                          {formatRelativeTime(n.created_at)}
                        </span>
                      </div>

                      <p
                        className={`text-xs leading-tight ${
                          !n.is_read ? 'font-semibold text-slate-900' : 'font-medium text-slate-700'
                        }`}
                      >
                        {n.title}
                      </p>

                      <p className="text-[11px] text-slate-500 leading-snug line-clamp-2">
                        {n.message}
                      </p>

                      {n.student_name && (
                        <div className="flex items-center gap-1 text-[10px] text-slate-400 pt-0.5">
                          <span>Student:</span>
                          <strong className="text-slate-600 font-medium">{n.student_name}</strong>
                          {n.student_dept && <span>&bull; {n.student_dept}</span>}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-8 text-center space-y-2">
                <div className="w-10 h-10 bg-slate-50 text-slate-400 rounded-2xl flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <p className="text-xs font-semibold text-slate-700">No notifications yet</p>
                <p className="text-[11px] text-slate-400 max-w-[200px] mx-auto">
                  New student risk transitions and escalation alerts will appear here.
                </p>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-2.5 bg-slate-50/70 border-t border-slate-100 text-center">
            <Link
              to="/notifications"
              onClick={() => setIsOpen(false)}
              className="text-xs font-semibold text-brand-600 hover:text-brand-700 inline-flex items-center gap-1 transition"
            >
              <span>View all notifications</span>
              <span>&rarr;</span>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
