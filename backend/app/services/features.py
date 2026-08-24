from typing import List, Dict, Optional, Any
from datetime import datetime
import numpy as np

try:
    from app.schemas.student import UnifiedStudentProfile
    from app.schemas.features import StudentFeatures
except ImportError:
    from backend.app.schemas.student import UnifiedStudentProfile
    from backend.app.schemas.features import StudentFeatures

DEFAULT_PASS_PERCENT = 40.0

EXAM_STAGE_ORDER = {
    "TEST1": 1,
    "TEST2": 2,
    "TEST3": 3,
    "MIDTERM": 4,
    "FINAL": 5,
    "OTHER": 6,
}

class FeatureEngineeringService:
    """Canonical temporal feature engineering service for Pathwise."""

    @staticmethod
    def extract_features(
        profile: UnifiedStudentProfile,
        reference_date: Optional[str] = None
    ) -> StudentFeatures:
        """
        Extracts temporal and behavioral feature vector from a UnifiedStudentProfile.
        
        Args:
            profile: Fused student profile
            reference_date: Optional ISO date string (YYYY-MM-DD) for deterministic fee overdue checks
        """
        # 1. Attendance Features
        att_feats = FeatureEngineeringService._extract_attendance_features(profile)

        # 2. Marks Features
        marks_feats = FeatureEngineeringService._extract_marks_features(profile)

        # 3. Backlog Features
        backlog_feats = FeatureEngineeringService._extract_backlog_features(profile)

        # 4. Fee Features
        fee_feats = FeatureEngineeringService._extract_fee_features(profile, reference_date=reference_date)

        # Assemble and ensure complete numerical stability (no NaN or Inf)
        all_feature_dict = {
            "student_id": profile.student.id,
            **att_feats,
            **marks_feats,
            **backlog_feats,
            **fee_feats,
        }

        return StudentFeatures(**all_feature_dict)

    @staticmethod
    def _extract_attendance_features(profile: UnifiedStudentProfile) -> Dict[str, Any]:
        """Computes temporal attendance metrics."""
        att_items = profile.attendance or []
        count = len(att_items)

        if count == 0:
            return {
                "attendance_current": 0.0,
                "attendance_mean": 0.0,
                "attendance_slope": 0.0,
                "attendance_decline_pp": 0.0,
                "attendance_recent_vs_historical": 1.0,
                "attendance_consecutive_decline": 0,
                "attendance_acceleration": 0.0,
                "attendance_history_count": 0,
                "has_sufficient_attendance_history": False,
            }

        percentages = [float(a.percentage) for a in att_items]
        current_pct = round(percentages[-1], 2)
        mean_pct = round(float(np.mean(percentages)), 2)

        # Linear regression slope across chronological periods (pp per week)
        if count >= 2:
            x_vals = np.arange(count)
            slope = float(np.polyfit(x_vals, percentages, 1)[0])
            slope = round(slope, 2)
        else:
            slope = 0.0

        # Decline from peak to latest in positive percentage points
        peak_pct = max(percentages)
        decline_pp = round(max(0.0, float(peak_pct - current_pct)), 2)

        # Recent (last 2 periods) vs historical (prior periods)
        if count >= 3:
            recent_mean = float(np.mean(percentages[-2:]))
            hist_mean = float(np.mean(percentages[:-2]))
            if hist_mean > 0:
                recent_vs_hist = round(recent_mean / hist_mean, 2)
            else:
                recent_vs_hist = 1.0 if recent_mean == 0 else 2.0
        else:
            recent_vs_hist = 1.0

        # Consecutive declining transitions moving backwards from latest period
        consecutive_decline = 0
        for i in range(count - 1, 0, -1):
            if percentages[i] < percentages[i - 1]:
                consecutive_decline += 1
            else:
                break

        # Attendance acceleration (slope of first differences)
        if count >= 3:
            diffs = [percentages[i + 1] - percentages[i] for i in range(count - 1)]
            x_diff = np.arange(len(diffs))
            acc = float(np.polyfit(x_diff, diffs, 1)[0])
            acc = round(acc, 2)
        else:
            acc = 0.0

        return {
            "attendance_current": current_pct,
            "attendance_mean": mean_pct,
            "attendance_slope": slope,
            "attendance_decline_pp": decline_pp,
            "attendance_recent_vs_historical": recent_vs_hist,
            "attendance_consecutive_decline": consecutive_decline,
            "attendance_acceleration": acc,
            "attendance_history_count": count,
            "has_sufficient_attendance_history": count >= 3,
        }

    @staticmethod
    def _extract_marks_features(profile: UnifiedStudentProfile) -> Dict[str, Any]:
        """Computes multi-subject academic assessment features."""
        marks_items = profile.marks or []
        count = len(marks_items)

        if count == 0:
            return {
                "marks_current_avg": 0.0,
                "marks_mean": 0.0,
                "marks_slope": 0.0,
                "marks_decline_pp": 0.0,
                "marks_recent_vs_previous": 1.0,
                "marks_consecutive_failures": 0,
                "marks_failed_subject_count": 0,
                "marks_history_count": 0,
                "has_sufficient_marks_history": False,
                "subject_slopes": {},
            }

        # Calculate normalized score (0-100) per record
        normalized_records = []
        for m in marks_items:
            max_m = float(m.max_marks)
            obt_m = float(m.obtained_marks)
            pct = (obt_m / max_m * 100.0) if max_m > 0 else 0.0
            pct = max(0.0, min(100.0, pct))
            normalized_records.append({
                "subject": m.subject_name,
                "exam_type": m.exam_type,
                "order": EXAM_STAGE_ORDER.get(m.exam_type.upper(), 99),
                "attempt": m.attempt_number,
                "percentage": pct,
            })

        all_percentages = [r["percentage"] for r in normalized_records]
        overall_mean = round(float(np.mean(all_percentages)), 2)

        # Subject-specific slopes and latest subject scores
        subjects = sorted(list({r["subject"] for r in normalized_records}))
        subject_slopes = {}
        latest_subject_scores = {}

        for subj in subjects:
            subj_recs = [r for r in normalized_records if r["subject"] == subj]
            subj_recs.sort(key=lambda r: (r["order"], r["attempt"]))
            subj_scores = [r["percentage"] for r in subj_recs]
            latest_subject_scores[subj] = subj_scores[-1]

            if len(subj_scores) >= 2:
                s_slope = float(np.polyfit(np.arange(len(subj_scores)), subj_scores, 1)[0])
                subject_slopes[subj] = round(s_slope, 2)
            else:
                subject_slopes[subj] = 0.0

        # Stage-level chronological progression
        stages = sorted(list({r["order"] for r in normalized_records}))
        stage_averages = []
        for st in stages:
            st_scores = [r["percentage"] for r in normalized_records if r["order"] == st]
            stage_averages.append(float(np.mean(st_scores)))

        current_avg = round(float(stage_averages[-1]), 2)
        peak_avg = max(stage_averages)
        marks_decline_pp = round(max(0.0, float(peak_avg - current_avg)), 2)

        # Overall marks slope: average of subject slopes if multiple exist, else fit on stage averages
        if subject_slopes:
            overall_slope = round(float(np.mean(list(subject_slopes.values()))), 2)
        elif len(stage_averages) >= 2:
            overall_slope = round(float(np.polyfit(np.arange(len(stage_averages)), stage_averages, 1)[0]), 2)
        else:
            overall_slope = 0.0

        # Recent stage vs previous stages
        if len(stage_averages) >= 2:
            recent_stage = stage_averages[-1]
            prev_stages_mean = float(np.mean(stage_averages[:-1]))
            if prev_stages_mean > 0:
                recent_vs_prev = round(recent_stage / prev_stages_mean, 2)
            else:
                recent_vs_prev = 1.0 if recent_stage == 0 else 2.0
        else:
            recent_vs_prev = 1.0

        # Consecutive failing stages (< DEFAULT_PASS_PERCENT) moving backward
        consecutive_failures = 0
        for i in range(len(stage_averages) - 1, -1, -1):
            if stage_averages[i] < DEFAULT_PASS_PERCENT:
                consecutive_failures += 1
            else:
                break

        # Number of distinct subjects currently failing in their latest assessment
        failed_subjects = sum(1 for s_score in latest_subject_scores.values() if s_score < DEFAULT_PASS_PERCENT)

        return {
            "marks_current_avg": current_avg,
            "marks_mean": overall_mean,
            "marks_slope": overall_slope,
            "marks_decline_pp": marks_decline_pp,
            "marks_recent_vs_previous": recent_vs_prev,
            "marks_consecutive_failures": consecutive_failures,
            "marks_failed_subject_count": failed_subjects,
            "marks_history_count": count,
            "has_sufficient_marks_history": count >= 2,
            "subject_slopes": subject_slopes,
        }

    @staticmethod
    def _extract_backlog_features(profile: UnifiedStudentProfile) -> Dict[str, Any]:
        """Computes attempt and backlog metrics."""
        attempt_items = profile.attempts or []
        total_count = len(attempt_items)

        active_items = [a for a in attempt_items if a.status.upper() == "ACTIVE"]
        active_count = len(active_items)

        current_sem = profile.student.semester
        new_this_sem = sum(1 for a in active_items if a.semester == current_sem)

        max_attempt = max([a.attempt_number for a in attempt_items]) if total_count > 0 else 1

        # Backlog trajectory: -1 decreasing (more cleared), 0 neutral, +1 increasing (more active)
        cleared_count = sum(1 for a in attempt_items if a.status.upper() == "CLEARED")
        if active_count > cleared_count:
            trend_numeric = 1
        elif cleared_count > active_count:
            trend_numeric = -1
        else:
            trend_numeric = 0

        return {
            "backlog_count_active": active_count,
            "backlog_count_total": total_count,
            "backlog_new_this_semester": new_this_sem,
            "backlog_trend_numeric": trend_numeric,
            "max_attempt_number": max_attempt,
        }

    @staticmethod
    def _extract_fee_features(
        profile: UnifiedStudentProfile,
        reference_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Computes neutral contextual fee indicators."""
        fee_items = profile.fees or []
        count = len(fee_items)

        if count == 0:
            return {
                "fee_status_latest": "UNKNOWN",
                "fee_percentage_paid": 100.0,
                "fee_terms_overdue": 0,
                "fee_pending_count": 0,
            }

        latest_fee = fee_items[-1]
        latest_status = latest_fee.status.upper()
        total_fee = float(latest_fee.total_fee)
        paid_amt = float(latest_fee.paid_amount)

        pct_paid = round((paid_amt / total_fee * 100.0), 2) if total_fee > 0 else 100.0
        pct_paid = max(0.0, min(100.0, pct_paid))

        pending_count = sum(1 for f in fee_items if f.status.upper() in ["PARTIAL", "PENDING"])

        # Overdue count relative to reference_date (format: YYYY-MM-DD)
        overdue_count = 0
        if reference_date:
            try:
                ref_dt = datetime.strptime(reference_date[:10], "%Y-%m-%d")
                for f in fee_items:
                    if f.status.upper() != "PAID" and f.due_date:
                        try:
                            due_dt = datetime.strptime(f.due_date[:10], "%Y-%m-%d")
                            if due_dt < ref_dt:
                                overdue_count += 1
                        except (ValueError, TypeError):
                            pass
            except (ValueError, TypeError):
                pass

        return {
            "fee_status_latest": latest_status,
            "fee_percentage_paid": pct_paid,
            "fee_terms_overdue": overdue_count,
            "fee_pending_count": pending_count,
        }
