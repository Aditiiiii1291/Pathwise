from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

try:
    from app.core.database import get_db
    from app.models import Student, RiskSnapshot
    from app.crud.snapshot import get_latest_risk_snapshot_subquery, get_latest_risk_snapshot_for_student
    from app.schemas.api import (
        StudentListItem,
        PaginatedStudentResponse,
        StudentProfileDetailResponse,
    )
    from app.schemas.risk import RiskFusionResult
    from app.schemas.explanation import ExplanationResult
    from app.services.fusion import StudentDataFusionService
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.models import Student, RiskSnapshot
    from backend.app.crud.snapshot import get_latest_risk_snapshot_subquery, get_latest_risk_snapshot_for_student
    from backend.app.schemas.api import (
        StudentListItem,
        PaginatedStudentResponse,
        StudentProfileDetailResponse,
    )
    from backend.app.schemas.risk import RiskFusionResult
    from backend.app.schemas.explanation import ExplanationResult
    from backend.app.services.fusion import StudentDataFusionService

router = APIRouter(prefix="/students", tags=["students"])

@router.get("", response_model=PaginatedStudentResponse, status_code=status.HTTP_200_OK)
def list_students(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    search: Optional[str] = Query(None, description="Search filter for student name or roll number"),
    department: Optional[str] = Query(None, description="Filter by department"),
    semester: Optional[int] = Query(None, ge=1, le=8, description="Filter by current semester"),
    risk_tier: Optional[str] = Query(None, description="Filter by latest risk tier (LOW, MEDIUM, HIGH, CRITICAL)"),
    trend: Optional[str] = Query(None, description="Filter by latest trend"),
    db: Session = Depends(get_db),
):
    """
    Retrieves paginated students with optional filtering by department, semester, search query,
    latest risk tier, and trend. Excludes unnecessary sensitive personal contact info.
    """
    # Canonical subquery selecting latest RiskSnapshot based on computed_at DESC, id DESC
    latest_snapshot_subq = get_latest_risk_snapshot_subquery(db)

    query = (
        db.query(Student, RiskSnapshot)
        .outerjoin(latest_snapshot_subq, Student.id == latest_snapshot_subq.c.student_id)
        .outerjoin(RiskSnapshot, RiskSnapshot.id == latest_snapshot_subq.c.latest_snapshot_id)
    )

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            (Student.name.ilike(search_pattern)) | (Student.roll_number.ilike(search_pattern))
        )

    if department:
        query = query.filter(Student.department == department)

    if semester:
        query = query.filter(Student.semester == semester)

    if risk_tier:
        query = query.filter(RiskSnapshot.risk_tier == risk_tier.upper())

    if trend:
        query = query.filter(RiskSnapshot.trend == trend.upper())

    total = query.count()
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    records = (
        query.order_by(Student.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items: List[StudentListItem] = []
    for student, snapshot in records:
        mentor_name = student.mentor.name if student.mentor else None
        items.append(
            StudentListItem(
                id=student.id,
                roll_number=student.roll_number,
                name=student.name,
                department=student.department,
                semester=student.semester,
                enrollment_year=student.enrollment_year,
                mentor_name=mentor_name,
                latest_final_score=snapshot.final_score if snapshot else None,
                latest_risk_tier=snapshot.risk_tier.value if snapshot and snapshot.risk_tier else None,
                latest_trend=snapshot.trend.value if snapshot and snapshot.trend else None,
                latest_assessment_date=snapshot.computed_at if snapshot else None,
            )
        )

    return PaginatedStudentResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

@router.get("/{student_id}", response_model=StudentProfileDetailResponse, status_code=status.HTTP_200_OK)
def get_student_profile(
    student_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves full unified student profile and latest recorded risk assessment.
    Returns HTTP 404 if student does not exist.
    """
    fusion_service = StudentDataFusionService(db)
    profile = fusion_service.fuse_by_id(student_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    # Obtain latest assessment snapshot if present
    latest_snapshot = get_latest_risk_snapshot_for_student(db, student_id)

    latest_assessment = None
    if latest_snapshot:
        latest_assessment = RiskFusionResult(
            student_id=student_id,
            rule_score=latest_snapshot.rule_score,
            ml_probability=latest_snapshot.ml_probability,
            ml_score=round(latest_snapshot.ml_probability * 100.0, 2),
            rule_weight=0.5,
            ml_weight=0.5,
            final_score=latest_snapshot.final_score,
            risk_tier=latest_snapshot.risk_tier.value,
            trend=latest_snapshot.trend.value,
            computed_at=latest_snapshot.computed_at,
        )

    return StudentProfileDetailResponse(
        profile=profile,
        latest_assessment=latest_assessment,
        latest_explanation=None,
    )
