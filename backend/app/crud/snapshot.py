from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

try:
    from app.models import RiskSnapshot
except ImportError:
    from backend.app.models import RiskSnapshot

def get_latest_risk_snapshot_subquery(db: Session):
    """
    Returns a canonical subquery with columns (student_id, latest_snapshot_id)
    selecting the single latest RiskSnapshot per student.
    Primary chronological ordering: computed_at DESC
    Deterministic tie-breaker: id DESC
    """
    rn_subq = (
        db.query(
            RiskSnapshot.id.label("latest_snapshot_id"),
            RiskSnapshot.student_id.label("student_id"),
            func.row_number()
            .over(
                partition_by=RiskSnapshot.student_id,
                order_by=(RiskSnapshot.computed_at.desc(), RiskSnapshot.id.desc()),
            )
            .label("rn"),
        )
        .subquery()
    )

    return (
        db.query(rn_subq.c.student_id, rn_subq.c.latest_snapshot_id)
        .filter(rn_subq.c.rn == 1)
        .subquery()
    )

def get_latest_risk_snapshot_for_student(db: Session, student_id: int) -> Optional[RiskSnapshot]:
    """
    Retrieves the single canonical latest RiskSnapshot for a student.
    Primary ordering: computed_at DESC
    Tie-breaker: id DESC
    """
    return (
        db.query(RiskSnapshot)
        .filter(RiskSnapshot.student_id == student_id)
        .order_by(RiskSnapshot.computed_at.desc(), RiskSnapshot.id.desc())
        .first()
    )
