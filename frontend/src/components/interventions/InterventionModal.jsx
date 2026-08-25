import React, { useState, useEffect } from 'react';
import { X, HeartHandshake, Calendar, FileText, User, CheckCircle2, AlertCircle } from 'lucide-react';
import { createIntervention, updateIntervention } from '../../utils/api';

const INTERVENTION_TYPES = [
  { value: 'COUNSELLING', label: 'Counselling & Advisory' },
  { value: 'ACADEMIC_SUPPORT', label: 'Academic & Subject Tutoring' },
  { value: 'ATTENDANCE_SUPPORT', label: 'Attendance Recovery Plan' },
  { value: 'FINANCIAL_GUIDANCE', label: 'Financial / Fee Guidance' },
  { value: 'MENTOR_MEETING', label: 'One-on-One Mentor Meeting' },
  { value: 'GUARDIAN_CONTACT', label: 'Guardian Communication' },
  { value: 'STUDY_PLAN', label: 'Personalized Study Plan' },
  { value: 'OTHER', label: 'Other Support Action' },
];

const STATUS_OPTIONS = [
  { value: 'PLANNED', label: 'Planned' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'CANCELLED', label: 'Cancelled' },
];

export default function InterventionModal({
  isOpen,
  onClose,
  onSuccess,
  student = null,
  initialData = null,
}) {
  const isEdit = Boolean(initialData && initialData.id);

  const [studentId, setStudentId] = useState('');
  const [studentDisplay, setStudentDisplay] = useState(null);
  const [title, setTitle] = useState('');
  const [interventionType, setInterventionType] = useState('COUNSELLING');
  const [status, setStatus] = useState('PLANNED');
  const [followUpDate, setFollowUpDate] = useState('');
  const [notes, setNotes] = useState('');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setError(null);
      if (initialData) {
        setStudentId(initialData.student_id || (student ? student.id : ''));
        setTitle(initialData.title || '');
        setInterventionType(initialData.intervention_type || initialData.type || 'COUNSELLING');
        setStatus(initialData.status || 'PLANNED');
        setFollowUpDate(initialData.follow_up_date || '');
        setNotes(initialData.notes || '');
        setStudentDisplay(
          initialData.student_name
            ? { name: initialData.student_name, roll: initialData.student_roll, dept: initialData.student_dept }
            : student
        );
      } else if (student) {
        setStudentId(student.id);
        setTitle('Student Counselling Session');
        setInterventionType('COUNSELLING');
        setStatus('PLANNED');
        setFollowUpDate('');
        setNotes('');
        setStudentDisplay({
          name: student.name,
          roll: student.roll_number,
          dept: student.department,
        });
      } else {
        setStudentId('');
        setTitle('');
        setInterventionType('COUNSELLING');
        setStatus('PLANNED');
        setFollowUpDate('');
        setNotes('');
        setStudentDisplay(null);
      }
    }
  }, [isOpen, initialData, student]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const sId = parseInt(studentId, 10);
    if (isNaN(sId) || sId <= 0) {
      setError('Please provide a valid numeric Student ID.');
      return;
    }

    if (!title.trim()) {
      setError('Intervention title is required.');
      return;
    }

    setLoading(true);
    try {
      if (isEdit) {
        const payload = {
          title: title.trim(),
          intervention_type: interventionType,
          status,
          follow_up_date: followUpDate || null,
          notes: notes.trim() || null,
        };
        const updated = await updateIntervention(initialData.id, payload);
        if (onSuccess) onSuccess(updated);
      } else {
        const payload = {
          student_id: sId,
          title: title.trim(),
          intervention_type: interventionType,
          status,
          follow_up_date: followUpDate || null,
          notes: notes.trim() || null,
        };
        const created = await createIntervention(payload);
        if (onSuccess) onSuccess(created);
      }
      onClose();
    } catch (err) {
      console.error('Failed to save intervention:', err);
      setError(err.message || 'Failed to save intervention.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-xs animate-in fade-in">
      <div
        className="bg-white rounded-3xl shadow-2xl border border-slate-100 max-w-lg w-full overflow-hidden transition-all transform animate-in zoom-in-95"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4.5 border-b border-slate-100 flex items-center justify-between bg-slate-50/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-brand-50 border border-brand-100 flex items-center justify-center text-brand-600">
              <HeartHandshake className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-800">
                {isEdit ? 'Update Support Intervention' : 'Record Student Support Action'}
              </h3>
              <p className="text-[11px] text-slate-400">
                {isEdit ? 'Modify status, follow-up or notes' : 'Human-in-the-loop counselling record'}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-xs">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl flex items-center gap-2 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Student Context */}
          {studentDisplay ? (
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-slate-400" />
                <div>
                  <span className="font-semibold text-slate-800">{studentDisplay.name}</span>
                  {studentDisplay.roll && (
                    <span className="text-slate-400 font-mono ml-1.5">({studentDisplay.roll})</span>
                  )}
                </div>
              </div>
              {studentDisplay.dept && (
                <span className="text-[10px] font-semibold px-2 py-0.5 bg-white border border-slate-200 rounded-full text-slate-600">
                  {studentDisplay.dept}
                </span>
              )}
            </div>
          ) : (
            <div>
              <label className="block text-slate-600 font-semibold mb-1">
                Student ID <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                required
                disabled={isEdit}
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                placeholder="Enter Student ID number..."
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 disabled:opacity-60"
              />
            </div>
          )}

          {/* Intervention Title */}
          <div>
            <label className="block text-slate-600 font-semibold mb-1">
              Action Title <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Weekly attendance review & peer tutoring plan"
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />
          </div>

          {/* Type & Status Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-600 font-semibold mb-1">Intervention Category</label>
              <select
                value={interventionType}
                onChange={(e) => setInterventionType(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              >
                {INTERVENTION_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-600 font-semibold mb-1">Workflow Status</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Follow-up Date */}
          <div>
            <label className="block text-slate-600 font-semibold mb-1 flex items-center justify-between">
              <span>Follow-up Date</span>
              <span className="text-[10px] text-slate-400 font-normal">Optional</span>
            </label>
            <input
              type="date"
              value={followUpDate}
              onChange={(e) => setFollowUpDate(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-slate-600 font-semibold mb-1 flex items-center justify-between">
              <span>Counselling Notes & Key Next Steps</span>
              <span className="text-[10px] text-slate-400 font-normal">Private mentor log</span>
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Record specific agreements, root causes discussed, or scheduled milestone commitments..."
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 placeholder:text-slate-400 resize-none"
            />
          </div>

          {/* Footer Actions */}
          <div className="pt-3 border-t border-slate-100 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl font-medium transition cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-700 text-white rounded-xl font-semibold shadow-sm transition disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>{loading ? 'Saving...' : isEdit ? 'Update Record' : 'Save Intervention'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
