from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Set

try:
    from app.schemas.features import StudentFeatures
    from app.schemas.rules import RuleEvaluationResult, TriggeredRule
    from app.schemas.risk import RiskFusionResult
    from app.schemas.explanation import (
        ExplanationFactor,
        Recommendation,
        GlobalMLContext,
        ExplanationResult,
    )
except ImportError:
    from backend.app.schemas.features import StudentFeatures
    from backend.app.schemas.rules import RuleEvaluationResult, TriggeredRule
    from backend.app.schemas.risk import RiskFusionResult
    from backend.app.schemas.explanation import (
        ExplanationFactor,
        Recommendation,
        GlobalMLContext,
        ExplanationResult,
    )

class ExplanationEngine:
    """
    Generates factual, explainable, and supportive interpretations of student risk assessments.
    Produces:
      1. Student-specific factual factors (traceable to Phase 6 features and Phase 7 rules)
      2. Executive summary respecting risk tier and trajectory
      3. Actionable mentor recommendations
      4. Clearly separated global ML context
    """

    SEVERITY_ORDER = {"HIGH": 3, "MODERATE": 2, "LOW": 1, "INFO": 0}
    CATEGORY_ORDER = {"ATTENDANCE": 0, "ACADEMICS": 1, "BACKLOG": 2, "TREND": 3, "FEES": 4}
    PRIORITY_ORDER = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}

    @classmethod
    def generate_explanation(
        cls,
        features: StudentFeatures,
        rule_result: RuleEvaluationResult,
        fusion_result: RiskFusionResult,
        global_feature_importances: Optional[List[Dict[str, Any]]] = None,
    ) -> ExplanationResult:
        """
        Synthesizes structured explanation and recommendations from multi-phase outputs.
        """
        # 1. Extract & Rank Student-Specific Factors
        factors = cls._extract_factors(features, rule_result)
        top_factors = cls._rank_and_select_factors(factors, limit=4)

        # 2. Generate Executive Summary
        summary = cls._generate_summary(fusion_result, top_factors)

        # 3. Generate Actionable Recommendations
        recommendations = cls._generate_recommendations(features, fusion_result, top_factors)

        # 4. Global ML Context
        global_ml = GlobalMLContext(top_global_features=global_feature_importances or [])

        return ExplanationResult(
            student_id=fusion_result.student_id,
            risk_tier=fusion_result.risk_tier,
            trend=fusion_result.trend,
            final_score=fusion_result.final_score,
            rule_score=fusion_result.rule_score,
            ml_probability=fusion_result.ml_probability,
            summary=summary,
            top_factors=top_factors,
            recommendations=recommendations,
            global_ml_context=global_ml,
            generated_at=datetime.now(timezone.utc),
        )

    @classmethod
    def _extract_factors(
        cls,
        features: StudentFeatures,
        rule_result: RuleEvaluationResult,
    ) -> List[ExplanationFactor]:
        """Extracts candidate factual factors from rules and temporal features."""
        factors: List[ExplanationFactor] = []
        seen_codes: Set[str] = set()

        for rule in rule_result.triggered_rules:
            code = rule.code
            if code in seen_codes:
                continue

            if code == "ATTENDANCE_BELOW_THRESHOLD":
                sev = "HIGH" if features.attendance_current < 60.0 else "MODERATE"
                factors.append(
                    ExplanationFactor(
                        code="ATTENDANCE_BELOW_THRESHOLD",
                        category="ATTENDANCE",
                        title="Attendance Below Threshold",
                        description=f"Current attendance is {features.attendance_current:.1f}%, below institutional threshold of 75.0%.",
                        severity=sev,
                        observed_value=round(features.attendance_current, 1),
                        reference_value=75.0,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "ATTENDANCE_LARGE_DECLINE":
                sev = "HIGH" if features.attendance_decline_pp >= 25.0 else "MODERATE"
                factors.append(
                    ExplanationFactor(
                        code="ATTENDANCE_LARGE_DECLINE",
                        category="ATTENDANCE",
                        title="Significant Attendance Drop",
                        description=f"Attendance has declined by {features.attendance_decline_pp:.1f} percentage points from peak.",
                        severity=sev,
                        observed_value=round(features.attendance_decline_pp, 1),
                        reference_value=10.0,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "ATTENDANCE_DECLINING":
                sev = "HIGH" if features.attendance_slope <= -8.0 else "MODERATE"
                factors.append(
                    ExplanationFactor(
                        code="ATTENDANCE_DECLINING",
                        category="ATTENDANCE",
                        title="Downward Attendance Trend",
                        description=f"Attendance is declining at {features.attendance_slope:.1f} percentage points per recorded week.",
                        severity=sev,
                        observed_value=round(features.attendance_slope, 1),
                        reference_value=-5.0,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "MARKS_BELOW_THRESHOLD":
                sev = "HIGH" if features.marks_current_avg < 35.0 else "MODERATE"
                factors.append(
                    ExplanationFactor(
                        code="MARKS_BELOW_THRESHOLD",
                        category="ACADEMICS",
                        title="Marks Below Passing Threshold",
                        description=f"Latest assessment average ({features.marks_current_avg:.1f}%) is below passing threshold (40.0%).",
                        severity=sev,
                        observed_value=round(features.marks_current_avg, 1),
                        reference_value=40.0,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "MARKS_DECLINING":
                sev = "HIGH" if features.marks_slope <= -8.0 else "MODERATE"
                factors.append(
                    ExplanationFactor(
                        code="MARKS_DECLINING",
                        category="ACADEMICS",
                        title="Downward Academic Trend",
                        description=f"Assessment marks are declining at {features.marks_slope:.1f} percentage points per stage.",
                        severity=sev,
                        observed_value=round(features.marks_slope, 1),
                        reference_value=-5.0,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "REPEATED_FAILURES":
                factors.append(
                    ExplanationFactor(
                        code="REPEATED_FAILURES",
                        category="ACADEMICS",
                        title="Consecutive Assessment Failures",
                        description=f"Recorded {features.marks_consecutive_failures} consecutive failing assessment evaluations.",
                        severity="HIGH",
                        observed_value=features.marks_consecutive_failures,
                        reference_value=2,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "MULTIPLE_FAILED_SUBJECTS":
                factors.append(
                    ExplanationFactor(
                        code="MULTIPLE_FAILED_SUBJECTS",
                        category="ACADEMICS",
                        title="Multiple Failing Subjects",
                        description=f"Recorded unsatisfactory scores across {features.marks_failed_subject_count} distinct subject assessments.",
                        severity="HIGH",
                        observed_value=features.marks_failed_subject_count,
                        reference_value=1,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "MULTIPLE_ACTIVE_BACKLOGS":
                factors.append(
                    ExplanationFactor(
                        code="MULTIPLE_ACTIVE_BACKLOGS",
                        category="BACKLOG",
                        title="Multiple Active Backlogs",
                        description=f"Student currently carries {features.backlog_count_active} uncleared subject backlogs.",
                        severity="HIGH",
                        observed_value=features.backlog_count_active,
                        reference_value=2,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "NEW_BACKLOGS_CURRENT_SEMESTER":
                factors.append(
                    ExplanationFactor(
                        code="NEW_BACKLOGS_CURRENT_SEMESTER",
                        category="BACKLOG",
                        title="New Backlog Added",
                        description=f"Added {features.backlog_new_this_semester} new backlog(s) in the current semester.",
                        severity="MODERATE",
                        observed_value=features.backlog_new_this_semester,
                        reference_value=0,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "BACKLOGS_INCREASING":
                factors.append(
                    ExplanationFactor(
                        code="BACKLOGS_INCREASING",
                        category="BACKLOG",
                        title="Increasing Backlog Trend",
                        description="Active backlog count has shown an upward trend across consecutive semesters.",
                        severity="MODERATE",
                        observed_value=1,
                        reference_value=0,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "REPEATED_ATTEMPTS":
                factors.append(
                    ExplanationFactor(
                        code="REPEATED_ATTEMPTS",
                        category="BACKLOG",
                        title="Repeated Exam Attempts",
                        description=f"Exam attempt count has reached {features.max_attempt_number} for one or more subjects.",
                        severity="MODERATE",
                        observed_value=features.max_attempt_number,
                        reference_value=3,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

            elif code == "FEE_VERIFICATION_RECOMMENDED":
                factors.append(
                    ExplanationFactor(
                        code="FEE_VERIFICATION_RECOMMENDED",
                        category="FEES",
                        title="Fee Record Verification Recommended",
                        description=f"Administrative fee records indicate {features.fee_terms_overdue} term(s) overdue ({features.fee_percentage_paid:.1f}% paid).",
                        severity="LOW",
                        observed_value=round(features.fee_percentage_paid, 1),
                        reference_value=100.0,
                        source="RULE",
                    )
                )
                seen_codes.add(code)

        # Positive / Progress Signals (when student is improving or healthy)
        if features.has_sufficient_attendance_history and features.attendance_slope >= 1.5:
            factors.append(
                ExplanationFactor(
                    code="POSITIVE_ATTENDANCE_TREND",
                    category="ATTENDANCE",
                    title="Improving Attendance Trajectory",
                    description=f"Attendance shows a positive upward trajectory of +{features.attendance_slope:.1f} pp/week.",
                    severity="INFO",
                    observed_value=round(features.attendance_slope, 1),
                    reference_value=0.0,
                    source="FEATURE",
                )
            )

        if features.has_sufficient_marks_history and features.marks_slope >= 2.0:
            factors.append(
                ExplanationFactor(
                    code="POSITIVE_MARKS_TREND",
                    category="ACADEMICS",
                    title="Improving Academic Performance",
                    description=f"Assessment marks reflect a positive trajectory of +{features.marks_slope:.1f} pp/stage.",
                    severity="INFO",
                    observed_value=round(features.marks_slope, 1),
                    reference_value=0.0,
                    source="FEATURE",
                )
            )

        return factors

    @classmethod
    def _rank_and_select_factors(
        cls,
        factors: List[ExplanationFactor],
        limit: int = 4,
    ) -> List[ExplanationFactor]:
        """Ranks factors deterministically by severity and category tie-break."""
        # Deduplication: if both large decline and slope exist for same category, keep the highest severity
        deduped: Dict[str, ExplanationFactor] = {}
        for f in factors:
            if f.code in deduped:
                existing = deduped[f.code]
                if cls.SEVERITY_ORDER[f.severity] > cls.SEVERITY_ORDER[existing.severity]:
                    deduped[f.code] = f
            else:
                deduped[f.code] = f

        unique_factors = list(deduped.values())

        # Deterministic sorting: Severity descending, Category ascending, Code ascending
        unique_factors.sort(
            key=lambda x: (
                -cls.SEVERITY_ORDER.get(x.severity, 0),
                cls.CATEGORY_ORDER.get(x.category, 99),
                x.code,
            )
        )

        return unique_factors[:limit]

    @classmethod
    def _generate_summary(
        cls,
        fusion_result: RiskFusionResult,
        top_factors: List[ExplanationFactor],
    ) -> str:
        """Constructs an executive summary respecting risk tier and trajectory."""
        risk = fusion_result.risk_tier
        trend = fusion_result.trend

        # Special State + Trajectory combinations
        if risk == "LOW" and trend == "STABLE":
            return "Student is currently classified as LOW risk with a STABLE trajectory. Routine academic monitoring is indicated."

        if risk == "LOW" and trend == "IMPROVING":
            return "Student is currently classified as LOW risk with an IMPROVING trend across recent academic and attendance indicators."

        if risk in ("HIGH", "CRITICAL") and trend == "IMPROVING":
            return f"Overall risk remains elevated ({risk}) based on current and historical records, but recent observations show an IMPROVING trajectory."

        if risk == "MEDIUM" and trend == "RAPIDLY_DETERIORATING":
            return "Current combined risk is MEDIUM, but recent indicators are RAPIDLY_DETERIORATING. Early mentor attention is advised before concerns escalate."

        # General summary synthesis
        negative_factors = [f for f in top_factors if f.severity in ("HIGH", "MODERATE", "LOW")]
        if not negative_factors:
            return f"Student is currently classified as {risk} risk with a {trend} trajectory."

        key_phrases = []
        for f in negative_factors[:2]:
            key_phrases.append(f.title.lower())

        concerns_text = " and ".join(key_phrases)
        return f"Student is currently classified as {risk} risk with a {trend} trajectory. Primary observed concerns are {concerns_text}."

    @classmethod
    def _generate_recommendations(
        cls,
        features: StudentFeatures,
        fusion_result: RiskFusionResult,
        top_factors: List[ExplanationFactor],
    ) -> List[Recommendation]:
        """Generates actionable, non-judgmental recommendations mapped from observed factors."""
        recs: List[Recommendation] = []
        seen_codes: Set[str] = set()

        factor_codes = {f.code for f in top_factors}
        has_high_concern = any(f.severity == "HIGH" for f in top_factors)
        distinct_categories = {f.category for f in top_factors if f.severity in ("HIGH", "MODERATE")}

        # 1. Multi-factor Coordination
        if len(distinct_categories) >= 2 and has_high_concern:
            recs.append(
                Recommendation(
                    code="REC_COMBINED_MENTOR_REVIEW",
                    category="COORDINATION",
                    title="Comprehensive Mentor Review",
                    description="Schedule a mentor review to discuss the combined attendance and academic concerns and agree on appropriate support steps.",
                    priority="HIGH",
                )
            )
            seen_codes.add("REC_COMBINED_MENTOR_REVIEW")

        # 2. Attendance Recommendations
        if any(c in factor_codes for c in ("ATTENDANCE_BELOW_THRESHOLD", "ATTENDANCE_DECLINING", "ATTENDANCE_LARGE_DECLINE")):
            if "REC_ATTENDANCE_REVIEW" not in seen_codes:
                prio = "HIGH" if features.attendance_current < 65.0 or features.attendance_slope <= -5.0 else "MEDIUM"
                recs.append(
                    Recommendation(
                        code="REC_ATTENDANCE_REVIEW",
                        category="ATTENDANCE",
                        title="Attendance Recovery Discussion",
                        description="Initiate an attendance recovery discussion with the student and identify possible schedule, access, or participation barriers.",
                        priority=prio,
                    )
                )
                seen_codes.add("REC_ATTENDANCE_REVIEW")

        # 3. Academic Recommendations
        if any(c in factor_codes for c in ("MARKS_BELOW_THRESHOLD", "MARKS_DECLINING")):
            if "REC_ACADEMIC_TUTORING" not in seen_codes:
                prio = "HIGH" if features.marks_current_avg < 35.0 else "MEDIUM"
                recs.append(
                    Recommendation(
                        code="REC_ACADEMIC_TUTORING",
                        category="ACADEMICS",
                        title="Academic Review & Tutoring Support",
                        description="Review recent assessment performance and identify subjects where additional academic support or tutoring may help.",
                        priority=prio,
                    )
                )
                seen_codes.add("REC_ACADEMIC_TUTORING")

        if any(c in factor_codes for c in ("REPEATED_FAILURES", "MULTIPLE_FAILED_SUBJECTS")):
            if "REC_STRUCTURED_STUDY_PLAN" not in seen_codes:
                recs.append(
                    Recommendation(
                        code="REC_STRUCTURED_STUDY_PLAN",
                        category="ACADEMICS",
                        title="Structured Subject Revision Plan",
                        description="Consider faculty support, peer study groups, or a structured study plan for failing course modules.",
                        priority="HIGH",
                    )
                )
                seen_codes.add("REC_STRUCTURED_STUDY_PLAN")

        # 4. Backlog Recommendations
        if any(c in factor_codes for c in ("MULTIPLE_ACTIVE_BACKLOGS", "NEW_BACKLOGS_CURRENT_SEMESTER", "BACKLOGS_INCREASING")):
            if "REC_BACKLOG_CLEARANCE" not in seen_codes:
                recs.append(
                    Recommendation(
                        code="REC_BACKLOG_CLEARANCE",
                        category="BACKLOG",
                        title="Backlog Clearance Roadmap",
                        description="Create a subject-wise plan for addressing outstanding academic requirements.",
                        priority="MEDIUM",
                    )
                )
                seen_codes.add("REC_BACKLOG_CLEARANCE")

        # 5. Fee Recommendations (Neutral Administrative Verification Only!)
        if "FEE_VERIFICATION_RECOMMENDED" in factor_codes:
            if "REC_FEE_VERIFICATION" not in seen_codes:
                recs.append(
                    Recommendation(
                        code="REC_FEE_VERIFICATION",
                        category="ADMINISTRATIVE",
                        title="Fee Record Verification",
                        description="Verify the fee status with the student and check whether administrative or payment-plan support is appropriate.",
                        priority="LOW",
                    )
                )
                seen_codes.add("REC_FEE_VERIFICATION")

        # 6. Improving / Recovery Support
        if fusion_result.trend == "IMPROVING" and fusion_result.risk_tier in ("HIGH", "CRITICAL"):
            if "REC_SUSTAIN_IMPROVEMENT" not in seen_codes:
                recs.append(
                    Recommendation(
                        code="REC_SUSTAIN_IMPROVEMENT",
                        category="COORDINATION",
                        title="Reinforce Ongoing Progress",
                        description="Continue existing support approaches and monitor whether the positive academic/attendance trajectory is sustained.",
                        priority="MEDIUM",
                    )
                )
                seen_codes.add("REC_SUSTAIN_IMPROVEMENT")

        # 7. Low-Risk Healthy Baseline
        if fusion_result.risk_tier == "LOW" and not recs:
            if fusion_result.trend == "IMPROVING":
                recs.append(
                    Recommendation(
                        code="REC_ROUTINE_MONITORING",
                        category="COORDINATION",
                        title="Routine Monitoring & Progress Recognition",
                        description="Recent indicators are improving; continue routine monitoring and reinforce current support where applicable.",
                        priority="LOW",
                    )
                )
            else:
                recs.append(
                    Recommendation(
                        code="REC_ROUTINE_MONITORING",
                        category="COORDINATION",
                        title="Routine Monitoring",
                        description="No immediate intervention indicated; continue routine monitoring.",
                        priority="LOW",
                    )
                )

        # Deterministic sorting: Priority descending, Category ascending, Code ascending
        recs.sort(
            key=lambda x: (
                -cls.PRIORITY_ORDER.get(x.priority, 0),
                cls.CATEGORY_ORDER.get(x.category, 99),
                x.code,
            )
        )

        return recs
