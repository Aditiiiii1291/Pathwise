import React, { useState, useEffect } from 'react';
import {
  Users,
  AlertTriangle,
  ShieldAlert,
  TrendingUp,
  Activity,
  Calendar,
  RefreshCw,
} from 'lucide-react';
import { getDashboardOverview, getDepartmentAnalytics, getStudents } from '../utils/api';
import KPICard from '../components/common/KPICard';
import RiskDonut from '../components/overview/RiskDonut';
import AssessmentCoverageCard from '../components/overview/AssessmentCoverageCard';
import TrendDonut from '../components/overview/TrendDonut';
import DepartmentRiskChart from '../components/overview/DepartmentRiskChart';
import PriorityStudentTable from '../components/overview/PriorityStudentTable';
import DetailedAnalytics from '../components/overview/DetailedAnalytics';
import MentorActionModal from '../components/mentor/MentorActionModal';
import { SkeletonCard, SkeletonTable } from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

export default function OverviewPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [overviewData, setOverviewData] = useState(null);
  const [departmentData, setDepartmentData] = useState([]);
  const [priorityStudents, setPriorityStudents] = useState({ items: [], total: 0 });
  const [isMentorModalOpen, setIsMentorModalOpen] = useState(false);

  const fetchAllData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [overview, departments, priorityRes] = await Promise.all([
        getDashboardOverview(),
        getDepartmentAnalytics(),
        // Priority flagged students for attention table (page 1, top priority)
        getStudents({ page: 1, pageSize: 5, riskTier: 'CRITICAL' }),
      ]);
      setOverviewData(overview);
      setDepartmentData(departments || []);
      setPriorityStudents(priorityRes || { items: [], total: 0 });
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err.message || 'Unable to connect to Pathwise API server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, []);

  // Calculate high-level KPIs from real overview API data
  const totalStudents = overviewData?.total_students || 0;
  const assessedStudents = overviewData?.assessed_students || 0;
  const criticalCount = overviewData?.risk_distribution?.CRITICAL || 0;
  const highCount = overviewData?.risk_distribution?.HIGH || 0;
  const atRiskCount = criticalCount + highCount;
  const improvingCount = overviewData?.trend_distribution?.IMPROVING || 0;
  const avgScore = overviewData?.average_final_score !== undefined && overviewData?.average_final_score !== null
    ? `${overviewData.average_final_score.toFixed(1)} / 100`
    : '—';

  if (error) {
    return (
      <div className="py-12">
        <ErrorState
          title="Unable to load dashboard overview"
          message={error}
          onRetry={fetchAllData}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* SECTION 1: Overview Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-800">
            Overview
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Early insights at a glance
          </p>
        </div>

        {/* Date / Term Indicator */}
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200/80 rounded-xl text-xs font-medium text-slate-600 shadow-subtle">
            <Calendar className="w-3.5 h-3.5 text-slate-400" />
            <span>Academic Term 2026</span>
          </div>
          <button
            onClick={fetchAllData}
            disabled={loading}
            className="p-2 bg-white border border-slate-200/80 rounded-xl text-slate-500 hover:text-slate-800 hover:bg-slate-50 shadow-subtle transition disabled:opacity-50 cursor-pointer"
            title="Refresh dashboard data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* SECTION 2: Primary KPI Cards (100% Genuine Metrics) */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <SkeletonCard key={i} height="h-28" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <KPICard
            title="Total Students"
            value={totalStudents}
            subtitle="All Departments"
            icon={Users}
            variant="blue"
          />
          <KPICard
            title="At Risk"
            value={atRiskCount}
            subtitle={assessedStudents > 0 ? `${((atRiskCount / assessedStudents) * 100).toFixed(1)}% of assessed` : '0% of assessed'}
            icon={AlertTriangle}
            variant="amber"
          />
          <KPICard
            title="Critical Risk"
            value={criticalCount}
            subtitle={assessedStudents > 0 ? `${((criticalCount / assessedStudents) * 100).toFixed(1)}% of assessed` : '0% of assessed'}
            icon={ShieldAlert}
            variant="rose"
          />
          <KPICard
            title="Improving"
            value={improvingCount}
            subtitle={assessedStudents > 0 ? `${((improvingCount / assessedStudents) * 100).toFixed(1)}% of assessed` : '0% of assessed'}
            icon={TrendingUp}
            variant="green"
          />
          <KPICard
            title="Average Risk Score"
            value={avgScore}
            subtitle="Across assessed cohort"
            icon={Activity}
            variant="lilac"
          />
        </div>
      )}

      {/* SECTION 3: Core Analytics (4-Card Grid) */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonCard key={i} height="h-64" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <RiskDonut
            riskDistribution={overviewData?.risk_distribution}
            totalAssessed={assessedStudents}
          />
          <AssessmentCoverageCard
            totalStudents={totalStudents}
            assessedStudents={assessedStudents}
            averageFinalScore={overviewData?.average_final_score || 0}
            atRiskCount={atRiskCount}
          />
          <TrendDonut
            trendDistribution={overviewData?.trend_distribution}
            totalAssessed={assessedStudents}
          />
          <DepartmentRiskChart
            departmentData={departmentData}
          />
        </div>
      )}

      {/* SECTION 4: Priority Students + Mentor Action Panel */}
      {loading ? (
        <SkeletonTable rows={5} />
      ) : (
        <PriorityStudentTable
          students={priorityStudents.items}
          total={priorityStudents.total}
          onOpenMentorPanel={() => setIsMentorModalOpen(true)}
        />
      )}

      {/* SECTION 5: Detailed Analytics (100% Genuine Metrics from overview & department data) */}
      {!loading && (
        <DetailedAnalytics
          overviewData={overviewData}
          departmentData={departmentData}
        />
      )}

      {/* Mentor Action Workspace Modal */}
      <MentorActionModal
        isOpen={isMentorModalOpen}
        onClose={() => setIsMentorModalOpen(false)}
      />
    </div>
  );
}
