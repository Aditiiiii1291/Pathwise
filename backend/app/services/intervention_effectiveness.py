import math
from datetime import datetime, date, timezone
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

try:
    from app.models.student import Student
    from app.models.intervention import Intervention, InterventionStatusEnum
    from app.models.risk import RiskSnapshot
    from app.schemas.intervention_effectiveness import (
        SnapshotContext,
        InterventionEffectivenessDetail,
        InterventionEffectivenessSummaryItem,
        AggregateEffectivenessSummary,
        FollowUpItem,
        EFFECTIVENESS_DISCLAIMER,
    )
except ImportError:
    from backend.app.models.student import Student
    from backend.app.models.intervention import Intervention, InterventionStatusEnum
    from backend.app.models.risk import RiskSnapshot
    from backend.app.schemas.intervention_effectiveness import (
        SnapshotContext,
        InterventionEffectivenessDetail,
        InterventionEffectivenessSummaryItem,
        AggregateEffectivenessSummary,
        FollowUpItem,
        EFFECTIVENESS_DISCLAIMER,
    )


class InterventionEffectivenessService:
    # An application-defined tolerance on Pathwise's 0–100 risk scale used to avoid
    # classifying small score fluctuations as improvement or worsening.
    STABILITY_THRESHOLD = 5.0

    CLASSIFICATION_IMPROVED = "IMPROVED"
    CLASSIFICATION_STABLE = "STABLE"
    CLASSIFICATION_WORSENED = "WORSENED"
    CLASSIFICATION_AWAITING = "AWAITING_REASSESSMENT"
    CLASSIFICATION_INSUFFICIENT = "INSUFFICIENT_DATA"

    FOLLOW_UP_OVERDUE = "OVERDUE"
    FOLLOW_UP_DUE_TODAY = "DUE_TODAY"
    FOLLOW_UP_UPCOMING = "UPCOMING"
    FOLLOW_UP_CLOSED = "CLOSED"
    FOLLOW_UP_NO_DATE = "NO_FOLLOW_UP"

    @classmethod
    def resolve_baseline_snapshot(
        cls,
        db: Session,
        student_id: int,
        created_at: datetime,
    ) -> Optional[RiskSnapshot]:
        """
        Finds the latest RiskSnapshot computed at or before the intervention was created.
        Chronological ordering: computed_at DESC, id DESC.
        """
        return db.query(RiskSnapshot).filter(
            and_(
                RiskSnapshot.student_id == student_id,
                RiskSnapshot.computed_at <= created_at
            )
        ).order_by(
            RiskSnapshot.computed_at.desc(),
            RiskSnapshot.id.desc()
        ).first()

    @classmethod
    def resolve_post_snapshot(
        cls,
        db: Session,
        student_id: int,
        created_at: datetime,
        baseline_id: Optional[int] = None,
    ) -> Optional[RiskSnapshot]:
        """
        Finds the latest RiskSnapshot computed strictly after the intervention was created.
        Chronological ordering: computed_at DESC, id DESC.
        """
        post = db.query(RiskSnapshot).filter(
            and_(
                RiskSnapshot.student_id == student_id,
                RiskSnapshot.computed_at > created_at
            )
        ).order_by(
            RiskSnapshot.computed_at.desc(),
            RiskSnapshot.id.desc()
        ).first()

        if post and baseline_id is not None and post.id == baseline_id:
            return None
        return post

    @classmethod
    def evaluate_intervention(
        cls,
        db: Session,
        intervention: Intervention,
    ) -> InterventionEffectivenessDetail:
        """
        Calculates observed before-and-after risk trajectory metrics for a single intervention.
        """
        student = intervention.student
        baseline = cls.resolve_baseline_snapshot(
            db=db,
            student_id=intervention.student_id,
            created_at=intervention.created_at,
        )
        post = cls.resolve_post_snapshot(
            db=db,
            student_id=intervention.student_id,
            created_at=intervention.created_at,
            baseline_id=baseline.id if baseline else None,
        )

        before_ctx = None
        after_ctx = None
        score_delta = None
        tier_transition = None
        trend_transition = None

        if baseline:
            before_ctx = SnapshotContext(
                snapshot_id=baseline.id,
                score=round(baseline.final_score, 1),
                risk_tier=baseline.risk_tier.value if hasattr(baseline.risk_tier, "value") else str(baseline.risk_tier),
                trend=baseline.trend.value if hasattr(baseline.trend, "value") else str(baseline.trend),
                computed_at=baseline.computed_at,
            )

        if post:
            after_ctx = SnapshotContext(
                snapshot_id=post.id,
                score=round(post.final_score, 1),
                risk_tier=post.risk_tier.value if hasattr(post.risk_tier, "value") else str(post.risk_tier),
                trend=post.trend.value if hasattr(post.trend, "value") else str(post.trend),
                computed_at=post.computed_at,
            )

        # Determine observational classification
        if not baseline:
            classification = cls.CLASSIFICATION_INSUFFICIENT
            interpretation = "No pre-intervention risk assessment baseline found."
        elif not post:
            classification = cls.CLASSIFICATION_AWAITING
            interpretation = "A new student risk assessment is required before change can be evaluated."
        else:
            score_delta = round(post.final_score - baseline.final_score, 1)
            before_tier = before_ctx.risk_tier
            after_tier = after_ctx.risk_tier
            tier_transition = f"{before_tier} → {after_tier}"

            before_trend = before_ctx.trend
            after_trend = after_ctx.trend
            trend_transition = f"{before_trend} → {after_trend}"

            if score_delta <= -cls.STABILITY_THRESHOLD:
                classification = cls.CLASSIFICATION_IMPROVED
                interpretation = f"Student risk decreased after this intervention (score reduced by {abs(score_delta):.1f} points)."
            elif score_delta >= cls.STABILITY_THRESHOLD:
                classification = cls.CLASSIFICATION_WORSENED
                interpretation = f"Student risk increased after this intervention (score increased by {score_delta:.1f} points)."
            else:
                classification = cls.CLASSIFICATION_STABLE
                interpretation = f"Student risk remained stable following this intervention (score changed by {score_delta:+.1f} points)."

        return InterventionEffectivenessDetail(
            intervention_id=intervention.id,
            student_id=intervention.student_id,
            student_name=student.name if student else None,
            title=intervention.title or "Intervention Record",
            intervention_type=str(intervention.intervention_type or intervention.type or "COUNSELLING"),
            status=str(intervention.status),
            created_at=intervention.created_at,
            classification=classification,
            before=before_ctx,
            after=after_ctx,
            score_delta=score_delta,
            tier_transition=tier_transition,
            trend_transition=trend_transition,
            interpretation=interpretation,
            disclaimer=EFFECTIVENESS_DISCLAIMER,
        )

    @classmethod
    def derive_follow_up_state(cls, follow_up_date: Optional[date], status_str: str) -> Tuple[str, Optional[int]]:
        """
        Derives follow-up urgency state based on scheduled date and current workflow status.
        """
        if status_str in (InterventionStatusEnum.COMPLETED.value, InterventionStatusEnum.CANCELLED.value):
            return cls.FOLLOW_UP_CLOSED, None

        if not follow_up_date:
            return cls.FOLLOW_UP_NO_DATE, None

        today = date.today()
        days_diff = (follow_up_date - today).days

        if days_diff < 0:
            return cls.FOLLOW_UP_OVERDUE, days_diff
        elif days_diff == 0:
            return cls.FOLLOW_UP_DUE_TODAY, 0
        else:
            return cls.FOLLOW_UP_UPCOMING, days_diff

    @classmethod
    def get_aggregate_summary(cls, db: Session) -> AggregateEffectivenessSummary:
        """
        Calculates cohort-wide aggregate counts and average score delta across all logged interventions.
        """
        interventions = db.query(Intervention).all()
        total = len(interventions)

        improved = 0
        stable = 0
        worsened = 0
        awaiting = 0
        insufficient = 0
        score_deltas: List[float] = []

        for item in interventions:
            detail = cls.evaluate_intervention(db=db, intervention=item)
            if detail.classification == cls.CLASSIFICATION_IMPROVED:
                improved += 1
            elif detail.classification == cls.CLASSIFICATION_STABLE:
                stable += 1
            elif detail.classification == cls.CLASSIFICATION_WORSENED:
                worsened += 1
            elif detail.classification == cls.CLASSIFICATION_AWAITING:
                awaiting += 1
            elif detail.classification == cls.CLASSIFICATION_INSUFFICIENT:
                insufficient += 1

            if detail.score_delta is not None:
                score_deltas.append(detail.score_delta)

        evaluated = len(score_deltas)
        avg_delta = round(sum(score_deltas) / evaluated, 1) if evaluated > 0 else None

        return AggregateEffectivenessSummary(
            total_interventions=total,
            evaluated_interventions=evaluated,
            improved_count=improved,
            stable_count=stable,
            worsened_count=worsened,
            awaiting_reassessment_count=awaiting,
            insufficient_data_count=insufficient,
            average_score_change=avg_delta,
            disclaimer=EFFECTIVENESS_DISCLAIMER,
        )

    @classmethod
    def get_follow_ups(
        cls,
        db: Session,
        state: Optional[str] = None,
        student_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[FollowUpItem], int, int, int, int, int]:
        """
        Queries interventions and classifies their follow-up states with server-side pagination.
        """
        query = db.query(Intervention)
        if student_id is not None:
            query = query.filter(Intervention.student_id == student_id)

        all_items = query.order_by(
            Intervention.created_at.desc(),
            Intervention.id.desc()
        ).all()

        classified_items: List[FollowUpItem] = []
        overdue_cnt = 0
        due_today_cnt = 0
        upcoming_cnt = 0

        for item in all_items:
            f_state, days = cls.derive_follow_up_state(item.follow_up_date, str(item.status))

            if f_state == cls.FOLLOW_UP_OVERDUE:
                overdue_cnt += 1
            elif f_state == cls.FOLLOW_UP_DUE_TODAY:
                due_today_cnt += 1
            elif f_state == cls.FOLLOW_UP_UPCOMING:
                upcoming_cnt += 1

            # Filter if state requested
            if state and f_state != state.upper():
                continue

            student = item.student
            classified_items.append(
                FollowUpItem(
                    intervention_id=item.id,
                    student_id=item.student_id,
                    student_name=student.name if student else None,
                    student_roll=student.roll_number if student else None,
                    student_dept=student.department if student else None,
                    title=item.title or "Intervention Record",
                    intervention_type=str(item.intervention_type or item.type or "COUNSELLING"),
                    status=str(item.status),
                    follow_up_date=item.follow_up_date,
                    follow_up_state=f_state,
                    days_until_due=days,
                    created_at=item.created_at,
                )
            )

        total = len(classified_items)
        pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        offset = (page - 1) * page_size
        paginated_items = classified_items[offset:offset + page_size]

        return paginated_items, total, pages, overdue_cnt, due_today_cnt, upcoming_cnt
