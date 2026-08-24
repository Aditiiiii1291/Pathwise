import React from 'react';
import { X, CheckCircle, Calendar, MessageSquare, BookOpen, AlertCircle } from 'lucide-react';

export default function MentorActionModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/30 backdrop-blur-xs transition-opacity animate-in fade-in duration-150">
      <div className="bg-white border border-slate-100 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50">
          <div>
            <h3 className="text-base font-bold text-slate-800">
              Mentor Support Workspace
            </h3>
            <p className="text-xs text-slate-500">
              Focused intervention and follow-up console
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs text-slate-600 leading-relaxed">
          {/* Phase 14 notice */}
          <div className="p-3.5 bg-blue-50/70 border border-blue-100 rounded-xl flex items-start gap-3">
            <AlertCircle className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-blue-900 text-xs">
                Phase 14 Counselling Workflow Preview
              </p>
              <p className="text-[11px] text-blue-700 mt-0.5">
                This focused workspace provides structured mentor action templates. Persistent counselling workflows and effectiveness logging will be activated in Phase 14.
              </p>
            </div>
          </div>

          {/* Action Templates */}
          <div>
            <h4 className="text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2.5">
              Recommended Intervention Templates
            </h4>
            <div className="space-y-2">
              <div className="p-3 border border-slate-100 rounded-xl bg-slate-50/50 hover:bg-white hover:border-slate-200 transition flex items-start gap-3">
                <Calendar className="w-4 h-4 text-emerald-600 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-800 block">Schedule Attendance Recovery Discussion</span>
                  <span className="text-slate-500 text-[11px]">Initiate 1-on-1 check-in to identify commute or scheduling barriers.</span>
                </div>
              </div>

              <div className="p-3 border border-slate-100 rounded-xl bg-slate-50/50 hover:bg-white hover:border-slate-200 transition flex items-start gap-3">
                <BookOpen className="w-4 h-4 text-brand-600 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-800 block">Academic Tutoring Referral</span>
                  <span className="text-slate-500 text-[11px]">Connect student with departmental peer tutoring support.</span>
                </div>
              </div>

              <div className="p-3 border border-slate-100 rounded-xl bg-slate-50/50 hover:bg-white hover:border-slate-200 transition flex items-start gap-3">
                <MessageSquare className="w-4 h-4 text-purple-600 mt-0.5" />
                <div>
                  <span className="font-semibold text-slate-800 block">Backlog & Exam Preparation Roadmap</span>
                  <span className="text-slate-500 text-[11px]">Review previous attempt history and formulate a staged study timetable.</span>
                </div>
              </div>
            </div>
          </div>

          {/* Advisor Notes Area */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Mentor Follow-up Notes
            </label>
            <textarea
              rows={3}
              placeholder="Record notes from student consultation, agreed milestones, and next check-in date..."
              className="w-full p-3 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 focus:bg-white transition"
              disabled
            />
            <span className="text-[10px] text-slate-400 block mt-1">
              Note-taking and intervention logging persistence will be enabled in Phase 14.
            </span>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-slate-100 bg-slate-50/50 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 hover:bg-slate-100 rounded-xl transition"
          >
            Close Workspace
          </button>
        </div>
      </div>
    </div>
  );
}
