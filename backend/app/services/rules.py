from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session

try:
    from app.schemas.features import StudentFeatures
    from app.schemas.rules import (
        RuleEngineConfig,
        RuleThresholds,
        RuleWeights,
        TriggeredRule,
        FactorScores,
        FactorContributions,
        RuleEvaluationResult,
    )
    from app.models import RuleConfig
except ImportError:
    from backend.app.schemas.features import StudentFeatures
    from backend.app.schemas.rules import (
        RuleEngineConfig,
        RuleThresholds,
        RuleWeights,
        TriggeredRule,
        FactorScores,
        FactorContributions,
        RuleEvaluationResult,
    )
    from backend.app.models import RuleConfig

class RuleEngine:
    """Deterministic, explainable, and configurable rule evaluation engine for Pathwise."""

    @staticmethod
    def evaluate(
        features: StudentFeatures,
        config: Optional[RuleEngineConfig] = None
    ) -> RuleEvaluationResult:
        """
        Evaluates a StudentFeatures vector against institutional rule configurations.
        """
        if config is None:
            config = RuleEngineConfig()

        thresholds = config.thresholds
        weights = config.weights

        triggered_rules: List[TriggeredRule] = []

        # 1. Attendance Factor
        att_score, att_rules = RuleEngine._score_attendance(features, thresholds)
        triggered_rules.extend(att_rules)

        # 2. Marks Factor
        marks_score, marks_rules = RuleEngine._score_marks(features, thresholds)
        triggered_rules.extend(marks_rules)

        # 3. Backlogs Factor
        backlog_score, backlog_rules = RuleEngine._score_backlogs(features, thresholds)
        triggered_rules.extend(backlog_rules)

        # 4. Contextual Fees Factor
        fee_score, fee_rules = RuleEngine._score_fees(features, thresholds)
        triggered_rules.extend(fee_rules)

        # 5. Multi-Domain Trends Factor
        trend_score, trend_rules = RuleEngine._score_trends(features, thresholds)
        triggered_rules.extend(trend_rules)

        # Factor contributions (score * weight)
        att_contrib = round(att_score * weights.attendance, 2)
        marks_contrib = round(marks_score * weights.marks, 2)
        backlog_contrib = round(backlog_score * weights.backlogs, 2)
        fee_contrib = round(fee_score * weights.fees, 2)
        trend_contrib = round(trend_score * weights.trends, 2)

        # Overall weighted rule score clamped to [0.0, 100.0]
        raw_total = att_contrib + marks_contrib + backlog_contrib + fee_contrib + trend_contrib
        final_rule_score = round(min(100.0, max(0.0, raw_total)), 2)

        return RuleEvaluationResult(
            student_id=features.student_id,
            rule_score=final_rule_score,
            factor_scores=FactorScores(
                attendance=att_score,
                marks=marks_score,
                backlogs=backlog_score,
                fees=fee_score,
                trends=trend_score,
            ),
            factor_contributions=FactorContributions(
                attendance=att_contrib,
                marks=marks_contrib,
                backlogs=backlog_contrib,
                fees=fee_contrib,
                trends=trend_contrib,
            ),
            triggered_rules=triggered_rules,
        )

    @staticmethod
    def _score_attendance(
        features: StudentFeatures,
        thresholds: RuleThresholds
    ) -> Tuple[float, List[TriggeredRule]]:
        rules: List[TriggeredRule] = []
        if features.attendance_history_count == 0:
            return 0.0, rules

        score = 0.0

        # Current attendance below threshold
        if features.attendance_current < thresholds.attendance_min:
            shortfall = thresholds.attendance_min - features.attendance_current
            score += min(50.0, (shortfall / max(1.0, thresholds.attendance_min)) * 50.0 + 20.0)
            rules.append(TriggeredRule(
                code="ATTENDANCE_BELOW_THRESHOLD",
                factor="attendance",
                feature="attendance_current",
                observed_value=features.attendance_current,
                threshold=thresholds.attendance_min,
                message=f"Current attendance ({features.attendance_current}%) is below the institutional threshold of {thresholds.attendance_min}%."
            ))

        # Large decline from peak
        if features.attendance_decline_pp >= thresholds.attendance_decline_max:
            score += min(30.0, (features.attendance_decline_pp / 30.0) * 30.0)
            rules.append(TriggeredRule(
                code="ATTENDANCE_LARGE_DECLINE",
                factor="attendance",
                feature="attendance_decline_pp",
                observed_value=features.attendance_decline_pp,
                threshold=thresholds.attendance_decline_max,
                message=f"Attendance has declined by {features.attendance_decline_pp} percentage points from its recorded peak."
            ))

        # Temporal trend rules (ONLY IF sufficient history is present)
        if features.has_sufficient_attendance_history:
            if features.attendance_slope <= thresholds.attendance_slope_min:
                score += min(30.0, (abs(features.attendance_slope) / 10.0) * 30.0)
                rules.append(TriggeredRule(
                    code="ATTENDANCE_DECLINING",
                    factor="attendance",
                    feature="attendance_slope",
                    observed_value=features.attendance_slope,
                    threshold=thresholds.attendance_slope_min,
                    message=f"Attendance is declining at {features.attendance_slope} percentage points per recorded week."
                ))

            if features.attendance_consecutive_decline >= thresholds.attendance_consecutive_decline_max:
                score += min(20.0, features.attendance_consecutive_decline * 5.0)

            if features.attendance_acceleration <= -1.0:
                score += 15.0
                rules.append(TriggeredRule(
                    code="ATTENDANCE_ACCELERATING_DECLINE",
                    factor="attendance",
                    feature="attendance_acceleration",
                    observed_value=features.attendance_acceleration,
                    threshold=-1.0,
                    message=f"The weekly rate of attendance drop is accelerating ({features.attendance_acceleration} pp/week^2)."
                ))

        clamped_score = round(min(100.0, max(0.0, score)), 2)
        return clamped_score, rules

    @staticmethod
    def _score_marks(
        features: StudentFeatures,
        thresholds: RuleThresholds
    ) -> Tuple[float, List[TriggeredRule]]:
        rules: List[TriggeredRule] = []
        if features.marks_history_count == 0:
            return 0.0, rules

        score = 0.0

        # Current average marks below pass threshold
        if features.marks_current_avg < thresholds.marks_min:
            shortfall = thresholds.marks_min - features.marks_current_avg
            score += min(45.0, (shortfall / max(1.0, thresholds.marks_min)) * 45.0 + 20.0)
            rules.append(TriggeredRule(
                code="MARKS_BELOW_THRESHOLD",
                factor="marks",
                feature="marks_current_avg",
                observed_value=features.marks_current_avg,
                threshold=thresholds.marks_min,
                message=f"Average marks in latest assessment ({features.marks_current_avg}%) are below passing threshold ({thresholds.marks_min}%)."
            ))

        # Multiple failed subjects
        if features.marks_failed_subject_count >= thresholds.failed_subjects_max:
            score += min(30.0, features.marks_failed_subject_count * 15.0)
            rules.append(TriggeredRule(
                code="MULTIPLE_FAILED_SUBJECTS",
                factor="marks",
                feature="marks_failed_subject_count",
                observed_value=float(features.marks_failed_subject_count),
                threshold=float(thresholds.failed_subjects_max),
                message=f"Student currently has {features.marks_failed_subject_count} distinct subject(s) below the passing threshold."
            ))

        # Consecutive failing assessment stages
        if features.marks_consecutive_failures >= thresholds.consecutive_failures_max:
            score += min(30.0, features.marks_consecutive_failures * 15.0)
            rules.append(TriggeredRule(
                code="REPEATED_FAILURES",
                factor="marks",
                feature="marks_consecutive_failures",
                observed_value=float(features.marks_consecutive_failures),
                threshold=float(thresholds.consecutive_failures_max),
                message=f"Student has scored below passing marks in {features.marks_consecutive_failures} consecutive assessment stages."
            ))

        # Substantial marks decline from peak
        if features.marks_decline_pp >= thresholds.marks_decline_max:
            score += min(25.0, (features.marks_decline_pp / 30.0) * 25.0)
            rules.append(TriggeredRule(
                code="MARKS_DECLINING",
                factor="marks",
                feature="marks_decline_pp",
                observed_value=features.marks_decline_pp,
                threshold=thresholds.marks_decline_max,
                message=f"Academic marks average declined by {features.marks_decline_pp} percentage points from peak."
            ))

        # Slope-based deterioration (ONLY IF sufficient marks history)
        if features.has_sufficient_marks_history and features.marks_slope <= thresholds.marks_slope_min:
            score += min(25.0, (abs(features.marks_slope) / 10.0) * 25.0)
            if not any(r.code == "MARKS_DECLINING" for r in rules):
                rules.append(TriggeredRule(
                    code="MARKS_DECLINING",
                    factor="marks",
                    feature="marks_slope",
                    observed_value=features.marks_slope,
                    threshold=thresholds.marks_slope_min,
                    message=f"Academic marks are declining at {features.marks_slope} percentage points per assessment stage."
                ))

        clamped_score = round(min(100.0, max(0.0, score)), 2)
        return clamped_score, rules

    @staticmethod
    def _score_backlogs(
        features: StudentFeatures,
        thresholds: RuleThresholds
    ) -> Tuple[float, List[TriggeredRule]]:
        rules: List[TriggeredRule] = []
        score = 0.0

        # Active backlog threshold
        if features.backlog_count_active >= thresholds.active_backlogs_max:
            score += min(50.0, features.backlog_count_active * 20.0 + 10.0)
            rules.append(TriggeredRule(
                code="MULTIPLE_ACTIVE_BACKLOGS",
                factor="backlogs",
                feature="backlog_count_active",
                observed_value=float(features.backlog_count_active),
                threshold=float(thresholds.active_backlogs_max),
                message=f"Student has {features.backlog_count_active} active uncleared backlogs on record."
            ))
        elif features.backlog_count_active > 0:
            score += 20.0

        # New backlogs in current semester
        if features.backlog_new_this_semester > 0:
            score += 25.0
            rules.append(TriggeredRule(
                code="NEW_BACKLOGS_CURRENT_SEMESTER",
                factor="backlogs",
                feature="backlog_new_this_semester",
                observed_value=float(features.backlog_new_this_semester),
                threshold=1.0,
                message=f"Student incurred {features.backlog_new_this_semester} new backlog(s) in the current semester."
            ))

        # Increasing temporal backlog trend
        if features.backlog_trend_numeric == 1:
            score += 25.0
            rules.append(TriggeredRule(
                code="BACKLOGS_INCREASING",
                factor="backlogs",
                feature="backlog_trend_numeric",
                observed_value=1.0,
                threshold=1.0,
                message="Active backlog count has been increasing across sequential semesters."
            ))

        # High examination attempt count
        if features.max_attempt_number >= 3:
            score += 20.0
            rules.append(TriggeredRule(
                code="REPEATED_ATTEMPTS",
                factor="backlogs",
                feature="max_attempt_number",
                observed_value=float(features.max_attempt_number),
                threshold=3.0,
                message=f"Student has repeated a subject examination {features.max_attempt_number} times."
            ))

        clamped_score = round(min(100.0, max(0.0, score)), 2)
        return clamped_score, rules

    @staticmethod
    def _score_fees(
        features: StudentFeatures,
        thresholds: RuleThresholds
    ) -> Tuple[float, List[TriggeredRule]]:
        rules: List[TriggeredRule] = []
        
        # If no fee records or fully paid, zero concern
        if features.fee_status_latest in ("PAID", "UNKNOWN") and features.fee_pending_count == 0 and features.fee_terms_overdue == 0:
            return 0.0, rules

        score = 0.0
        if features.fee_terms_overdue >= thresholds.fee_overdue_terms_max or features.fee_status_latest in ("PARTIAL", "PENDING"):
            score = 60.0 + min(40.0, features.fee_terms_overdue * 20.0 + (100.0 - features.fee_percentage_paid) * 0.2)
            rules.append(TriggeredRule(
                code="FEE_VERIFICATION_RECOMMENDED",
                factor="fees",
                feature="fee_terms_overdue",
                observed_value=float(features.fee_terms_overdue),
                threshold=float(thresholds.fee_overdue_terms_max),
                message="One or more fee records are overdue or pending; administrative verification may be appropriate."
            ))

        clamped_score = round(min(100.0, max(0.0, score)), 2)
        return clamped_score, rules

    @staticmethod
    def _score_trends(
        features: StudentFeatures,
        thresholds: RuleThresholds
    ) -> Tuple[float, List[TriggeredRule]]:
        rules: List[TriggeredRule] = []
        score = 0.0

        # Attendance trend contribution
        if features.has_sufficient_attendance_history:
            if features.attendance_slope <= thresholds.attendance_slope_min:
                score += min(35.0, (abs(features.attendance_slope) / 10.0) * 35.0)
            if features.attendance_acceleration <= -1.0:
                score += 15.0

        # Marks trend contribution
        if features.has_sufficient_marks_history:
            if features.marks_slope <= thresholds.marks_slope_min:
                score += min(35.0, (abs(features.marks_slope) / 10.0) * 35.0)

        # Backlog trend contribution
        if features.backlog_trend_numeric == 1:
            score += 20.0

        clamped_score = round(min(100.0, max(0.0, score)), 2)
        return clamped_score, rules

    @staticmethod
    def load_config_from_db(db: Session, department: Optional[str] = None) -> RuleEngineConfig:
        """Loads rule configuration from database, falling back to department or global defaults."""
        config_record = None
        if department:
            config_record = db.query(RuleConfig).filter(RuleConfig.department == department).first()
        if not config_record:
            config_record = db.query(RuleConfig).filter(RuleConfig.department.is_(None)).first()

        if not config_record or not config_record.weights:
            return RuleEngineConfig(department=department)

        try:
            weights = RuleWeights(**config_record.weights)
            thresholds = RuleThresholds(**(config_record.thresholds or {}))
            return RuleEngineConfig(weights=weights, thresholds=thresholds, department=department)
        except Exception:
            return RuleEngineConfig(department=department)
