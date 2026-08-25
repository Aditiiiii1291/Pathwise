from typing import List, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func

try:
    from app.core.database import get_db
    from app.models import Student, RiskSnapshot
    from app.models.user import User
    from app.api.deps import get_current_user
    from app.crud.snapshot import get_latest_risk_snapshot_subquery
    from app.schemas.api import DashboardOverviewResponse, DepartmentSummaryItem
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.models import Student, RiskSnapshot
    from backend.app.models.user import User
    from backend.app.api.deps import get_current_user
    from backend.app.crud.snapshot import get_latest_risk_snapshot_subquery
    from backend.app.schemas.api import DashboardOverviewResponse, DepartmentSummaryItem

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/overview", response_model=DashboardOverviewResponse, status_code=status.HTTP_200_OK)
def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Computes institutional cohort overview metrics using the canonical latest snapshot per student
    ordered primarily by computed_at DESC, id DESC.
    Guarantees no historical double-counting.
    """
    total_students = db.query(func.count(Student.id)).scalar() or 0

    # Canonical subquery selecting latest RiskSnapshot
    latest_snapshot_subq = get_latest_risk_snapshot_subquery(db)

    # Query latest snapshots only
    latest_snapshots = (
        db.query(RiskSnapshot)
        .join(latest_snapshot_subq, RiskSnapshot.id == latest_snapshot_subq.c.latest_snapshot_id)
        .all()
    )

    assessed_count = len(latest_snapshots)
    risk_counts: Dict[str, int] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    trend_counts: Dict[str, int] = {
        "IMPROVING": 0,
        "STABLE": 0,
        "GRADUALLY_DETERIORATING": 0,
        "RAPIDLY_DETERIORATING": 0,
    }
    total_score = 0.0

    for snap in latest_snapshots:
        tier_val = snap.risk_tier.value if snap.risk_tier else "LOW"
        trend_val = snap.trend.value if snap.trend else "STABLE"
        if tier_val in risk_counts:
            risk_counts[tier_val] += 1
        if trend_val in trend_counts:
            trend_counts[trend_val] += 1
        total_score += snap.final_score

    avg_score = round(total_score / assessed_count, 2) if assessed_count > 0 else 0.0

    return DashboardOverviewResponse(
        total_students=total_students,
        assessed_students=assessed_count,
        risk_distribution=risk_counts,
        trend_distribution=trend_counts,
        average_final_score=avg_score,
    )

@router.get("/departments", response_model=List[DepartmentSummaryItem], status_code=status.HTTP_200_OK)
def get_department_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Aggregates student retention and risk distribution across academic departments.
    """
    # Canonical subquery selecting latest RiskSnapshot
    latest_snapshot_subq = get_latest_risk_snapshot_subquery(db)

    records = (
        db.query(Student.department, RiskSnapshot)
        .outerjoin(latest_snapshot_subq, Student.id == latest_snapshot_subq.c.student_id)
        .outerjoin(RiskSnapshot, RiskSnapshot.id == latest_snapshot_subq.c.latest_snapshot_id)
        .all()
    )

    dept_map: Dict[str, Dict[str, Any]] = {}
    for dept, snap in records:
        if dept not in dept_map:
            dept_map[dept] = {
                "student_count": 0,
                "at_risk_count": 0,
                "critical_count": 0,
                "total_score": 0.0,
                "assessed_count": 0,
            }
        dept_map[dept]["student_count"] += 1
        if snap:
            dept_map[dept]["assessed_count"] += 1
            dept_map[dept]["total_score"] += snap.final_score
            tier_val = snap.risk_tier.value if snap.risk_tier else "LOW"
            if tier_val in ("HIGH", "CRITICAL"):
                dept_map[dept]["at_risk_count"] += 1
            if tier_val == "CRITICAL":
                dept_map[dept]["critical_count"] += 1

    results: List[DepartmentSummaryItem] = []
    for dept, stats in sorted(dept_map.items()):
        avg_score = (
            round(stats["total_score"] / stats["assessed_count"], 2)
            if stats["assessed_count"] > 0
            else 0.0
        )
        results.append(
            DepartmentSummaryItem(
                department=dept,
                student_count=stats["student_count"],
                at_risk_count=stats["at_risk_count"],
                critical_count=stats["critical_count"],
                average_final_score=avg_score,
            )
        )

    return results
