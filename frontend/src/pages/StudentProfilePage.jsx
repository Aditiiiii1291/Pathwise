import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  BookOpen,
  User,
  ShieldAlert,
  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  Sparkles,
  RefreshCw,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts';
import { getStudentProfile, getStudentAssessment, computeAndPersistAssessment } from '../utils/api';
import RiskBadge from '../components/common/RiskBadge';
import TrendBadge from '../components/common/TrendBadge';
import { SkeletonCard } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function StudentProfilePage() {
  const { id } = useParams();
  const studentId = parseInt(id, 10);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [assessmentData, setAssessmentData] = useState(null);
  const [isPersisting, setIsPersisting] = useState(false);
  const [persistMessage, setPersistMessage] = useState(null);

  const fetchProfileAndAssessment = async () => {
    setLoading(true);
    setError(null);
    try {
      const [profileRes, assessmentRes] = await Promise.all([
        getStudentProfile(studentId),
        getStudentAssessment(studentId),
      ]);
      setProfileData(profileRes.profile);
      setAssessmentData(assessmentRes);
    } catch (err) {
      console.error('Failed to load profile/assessment:', err);
      setError(err.message || 'Unable to retrieve student profile.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileAndAssessment();
  }, [studentId]);

  const handleSaveAssessmentSnapshot = async () => {
    setIsPersisting(true);
    setPersistMessage(null);
    try {
      const saved = await computeAndPersistAssessment(studentId);
      setAssessmentData(saved);
      setPersistMessage({ type: 'success', text: 'Risk assessment snapshot persisted to history!' });
      setTimeout(() => setPersistMessage(null), 4000);
    } catch (err) {
      setPersistMessage({ type: 'error', text: err.message || 'Failed to persist assessment.' });
    } finally {
      setIsPersisting(false);
    }
  };

  if (error) {
    return (
      <div className="py-12">
        <ErrorState
          title="Student Profile Not Found"
          message={error}
          onRetry={fetchProfileAndAssessment}
        />
        <div className="text-center mt-4">
          <Link
            to="/students"
            className="text-xs font-semibold text-brand-600 hover:text-brand-700"
          >
            &larr; Back to Student Cohort
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-6 bg-slate-100 rounded w-1/4 animate-pulse"></div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} height="h-28" />
          ))}
        </div>
        <SkeletonCard height="h-64" />
      </div>
    );
  }

  const student = profileData?.student;
  const mentor = profileData?.mentor;
  const attendance = profileData?.attendance || [];
  const marks = profileData?.marks || [];
  const attempts = profileData?.attempts || [];
  const fees = profileData?.fees || [];

  const assessment = assessmentData?.assessment;
  const explanation = assessmentData?.explanation;

  // Format attendance records for line chart
  const attendanceChartData = attendance.map((att) => ({
    week: `W${att.week_number}`,
    percentage: att.percentage !== null && att.percentage !== undefined ? att.percentage : (att.attended_hours / att.total_hours * 100),
    attended: att.attended_hours,
    total: att.total_hours,
  }));

  // Format marks records for performance chart
  const marksChartData = marks.map((m) => ({
    name: `${m.course_code} (${m.exam_type})`,
    score: m.marks_obtained,
    maxScore: m.max_marks,
    pct: ((m.marks_obtained / m.max_marks) * 100).toFixed(1),
  }));

  const predProb = assessment?.ml_probability !== undefined && assessment?.ml_probability !== null
    ? `${(assessment.ml_probability * 100).toFixed(1)}%`
    : '—';

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Link to="/students" className="hover:text-brand-600 font-medium transition flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            Students
          </Link>
          <span>/</span>
          <span className="text-slate-800 font-semibold">{student?.name}</span>
          <span className="font-mono text-slate-400">({student?.roll_number})</span>
        </div>

        <div className="flex items-center gap-2">
          {persistMessage && (
            <span
              className={`text-xs px-2.5 py-1 rounded-lg ${
                persistMessage.type === 'success' ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
              }`}
            >
              {persistMessage.text}
            </span>
          )}
          <button
            onClick={handleSaveAssessmentSnapshot}
            disabled={isPersisting}
            className="px-3.5 py-1.5 bg-brand-50 hover:bg-brand-100 text-brand-700 border border-brand-200 rounded-xl text-xs font-semibold shadow-subtle transition flex items-center gap-1.5 disabled:opacity-50"
            title="Saves current evaluation as an immutable historical RiskSnapshot"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isPersisting ? 'animate-spin' : ''}`} />
            <span>Persist Assessment Snapshot</span>
          </button>
        </div>
      </div>

      {/* Student Identity Dossier Header */}
      <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-100 to-blue-50 border border-blue-200/60 text-brand-600 flex items-center justify-center font-bold text-xl shadow-xs">
            {student?.name?.charAt(0) || 'S'}
          </div>
          <div>
            <div className="flex items-center gap-2.5">
              <h2 className="text-lg font-bold text-slate-800 tracking-tight">
                {student?.name}
              </h2>
              <span className="text-xs font-mono font-medium px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md">
                {student?.roll_number}
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-500 mt-1">
              <span><strong>Department:</strong> {student?.department}</span>
              <span>&bull;</span>
              <span><strong>Current Semester:</strong> {student?.semester}</span>
              <span>&bull;</span>
              <span><strong>Enrolled:</strong> {student?.enrollment_year}</span>
              {mentor && (
                <>
                  <span>&bull;</span>
                  <span><strong>Mentor:</strong> {mentor.name}</span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Assessment Status Badges */}
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider block">
              Risk Tier
            </span>
            <RiskBadge tier={assessment?.risk_tier} size="lg" />
          </div>
          <div className="text-right">
            <span className="text-[10px] text-slate-400 font-medium uppercase tracking-wider block">
              Observed Trend
            </span>
            <TrendBadge trend={assessment?.trend} size="lg" />
          </div>
        </div>
      </div>

      {/* Primary Vital Metric Cards (4 Grid) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Final Retention Risk Score */}
        <div className="bg-[#F8FAFF] border border-blue-100/80 rounded-2xl p-4 shadow-subtle flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-500">Final Risk Score</span>
          <div className="my-1 flex items-baseline gap-1">
            <span className="text-2xl font-bold text-slate-800">
              {assessment?.final_score !== undefined ? assessment.final_score.toFixed(1) : '—'}
            </span>
            <span className="text-xs text-slate-400 font-medium">/ 100</span>
          </div>
          <span className="text-[11px] text-slate-500">
            Fused rule score ({assessment?.rule_score?.toFixed(1) || 0}) + ML
          </span>
        </div>

        {/* Card 2: Predicted Dropout Probability */}
        <div className="bg-[#FAF5FF] border border-purple-100/80 rounded-2xl p-4 shadow-subtle flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-500">Predicted Dropout Probability</span>
          <div className="my-1">
            <span className="text-2xl font-bold text-purple-900">
              {predProb}
            </span>
          </div>
          <span className="text-[11px] text-purple-700/80">
            Random Forest model estimation
          </span>
        </div>

        {/* Card 3: Backlog & Attempt Status */}
        <div className="bg-[#FFFDF5] border border-amber-100/80 rounded-2xl p-4 shadow-subtle flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-500">Backlogs & Attempts</span>
          <div className="my-1">
            <span className="text-2xl font-bold text-slate-800">
              {attempts.filter(a => a.status === 'FAIL' || a.status === 'ABSENT').length}
            </span>
          </div>
          <span className="text-[11px] text-slate-500">
            Total recorded attempt logs: {attempts.length}
          </span>
        </div>

        {/* Card 4: Fee Standing */}
        <div className="bg-[#F3FAF7] border border-emerald-100/80 rounded-2xl p-4 shadow-subtle flex flex-col justify-between">
          <span className="text-xs font-semibold text-slate-500">Fee Payment Standing</span>
          <div className="my-1">
            <span className="text-lg font-bold text-slate-800">
              {fees.some(f => f.status === 'OVERDUE') ? 'Verification Needed' : 'In Good Standing'}
            </span>
          </div>
          <span className="text-[11px] text-slate-500">
            {fees.length} billing installment records
          </span>
        </div>
      </div>

      {/* Trajectory & Academic Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weekly Attendance Timeline */}
        <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-tight">
              Weekly Attendance History
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              75% Passing Threshold
            </span>
          </div>

          {attendanceChartData.length > 0 ? (
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={attendanceChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="week" tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <Tooltip
                    formatter={(val) => [`${typeof val === 'number' ? val.toFixed(1) : val}%`, 'Attendance']}
                    contentStyle={{ fontSize: '11px', borderRadius: '8px' }}
                  />
                  <ReferenceLine y={75} stroke="#EF4444" strokeDasharray="3 3" label={{ value: '75% Min', fill: '#EF4444', fontSize: 9 }} />
                  <Line
                    type="monotone"
                    dataKey="percentage"
                    stroke="#0EA5E9"
                    strokeWidth={2.5}
                    dot={{ fill: '#0EA5E9', r: 3 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-xs text-slate-400">
              No weekly attendance data logged for this student.
            </div>
          )}
        </div>

        {/* Academic Marks History */}
        <div className="bg-white border border-slate-100 rounded-2xl p-5 shadow-card space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-tight">
              Academic Assessment Performance
            </h3>
            <span className="text-[10px] text-slate-400 font-mono">
              40% Passing Benchmark
            </span>
          </div>

          {marksChartData.length > 0 ? (
            <div className="h-48 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={marksChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                  <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#64748B' }} angle={-20} textAnchor="end" />
                  <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#94A3B8' }} />
                  <Tooltip
                    formatter={(val) => [`${val}%`, 'Score']}
                    contentStyle={{ fontSize: '11px', borderRadius: '8px' }}
                  />
                  <ReferenceLine y={40} stroke="#EF4444" strokeDasharray="3 3" />
                  <Bar dataKey="pct" fill="#3B82F6" radius={[4, 4, 0, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-xs text-slate-400">
              No academic assessment marks logged for this student.
            </div>
          )}
        </div>
      </div>

      {/* Explanation & Recommendations Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Why This Student Was Flagged (Factual Signals) */}
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-800">
              Why This Student Was Flagged
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Factual signals extracted from verifiable institutional records
            </p>
          </div>

          {explanation?.top_factors && explanation.top_factors.length > 0 ? (
            <div className="space-y-3">
              {explanation.top_factors.map((factor, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-slate-50/60 border border-slate-100 rounded-xl space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 bg-slate-200/80 text-slate-700 rounded uppercase tracking-wider">
                        {factor.category}
                      </span>
                      <span className="text-xs font-semibold text-slate-800">
                        {factor.title}
                      </span>
                    </div>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        factor.severity === 'HIGH'
                          ? 'bg-rose-100 text-rose-800'
                          : factor.severity === 'MEDIUM'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {factor.severity}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {factor.description}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-400 bg-slate-50/50 rounded-xl">
              No adverse risk factors currently identified. Student exhibits stable academic and attendance progression.
            </div>
          )}
        </div>

        {/* Recommended Support Actions */}
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-4">
          <div className="border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold text-slate-800">
              Recommended Support Actions
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Actionable guidance to facilitate constructive mentor follow-ups
            </p>
          </div>

          {explanation?.recommendations && explanation.recommendations.length > 0 ? (
            <div className="space-y-3">
              {explanation.recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="p-3.5 bg-emerald-50/40 border border-emerald-100/70 rounded-xl space-y-1.5"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded uppercase tracking-wider">
                        {rec.category}
                      </span>
                      <span className="text-xs font-semibold text-slate-800">
                        {rec.title}
                      </span>
                    </div>
                    <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full">
                      Priority: {rec.priority}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">
                    {rec.description}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-400 bg-slate-50/50 rounded-xl">
              No active interventions required at this time.
            </div>
          )}
        </div>
      </div>

      {/* Global Model Context (Explicitly Separated) */}
      <div className="bg-slate-50 border border-slate-200/70 rounded-2xl p-6 space-y-4">
        <div className="flex items-start gap-3">
          <div className="p-2 bg-purple-100 text-purple-700 rounded-xl shrink-0 mt-0.5">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-800">
              Global Model Context (Machine Learning Transparency)
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Macro-level Random Forest model architecture and feature contributions across the training cohort
            </p>
          </div>
        </div>

        {/* Synthetic Disclaimer */}
        <div className="p-3 bg-amber-50/70 border border-amber-200/60 rounded-xl flex items-start gap-2.5 text-xs text-amber-900 leading-relaxed">
          <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <span>
            {explanation?.global_ml_context?.disclaimer ||
              'The current prediction model was trained on synthetic development data and is intended for demonstration/testing. Institutional deployment requires validation using appropriate historical institutional records.'}
          </span>
        </div>

        {/* Top Global Features */}
        {explanation?.global_ml_context?.top_global_features && (
          <div>
            <h4 className="text-xs font-semibold text-slate-700 mb-2">
              Global Feature Importance
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {explanation.global_ml_context.top_global_features.map((feat, idx) => (
                <div key={idx} className="p-2.5 bg-white border border-slate-200/80 rounded-xl text-xs">
                  <span className="font-mono text-slate-600 block truncate" title={feat.feature}>
                    {feat.feature}
                  </span>
                  <span className="font-bold text-slate-800 text-sm mt-1 block">
                    {(feat.importance * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
