from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
    from app.models.user import User
    from app.api.deps import get_current_user
    from app.schemas.intervention import (
        InterventionCreate,
        InterventionUpdate,
        InterventionItem,
        PaginatedInterventionResponse,
        InterventionSummaryResponse,
    )
    from app.schemas.intervention_effectiveness import (
        InterventionEffectivenessDetail,
        AggregateEffectivenessSummary,
        PaginatedFollowUpResponse,
    )
    from app.services.interventions import InterventionService
    from app.services.intervention_effectiveness import InterventionEffectivenessService
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.models.user import User
    from backend.app.api.deps import get_current_user
    from backend.app.schemas.intervention import (
        InterventionCreate,
        InterventionUpdate,
        InterventionItem,
        PaginatedInterventionResponse,
        InterventionSummaryResponse,
    )
    from backend.app.schemas.intervention_effectiveness import (
        InterventionEffectivenessDetail,
        AggregateEffectivenessSummary,
        PaginatedFollowUpResponse,
    )
    from backend.app.services.interventions import InterventionService
    from backend.app.services.intervention_effectiveness import InterventionEffectivenessService

router = APIRouter(prefix="/interventions", tags=["interventions"])


@router.post("", response_model=InterventionItem, status_code=status.HTTP_201_CREATED)
def create_intervention(
    payload: InterventionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new counselling or intervention record for a student.
    Enforces authenticated mentor attribution for MENTOR accounts.
    """
    if isinstance(current_user, User) and current_user.role == "MENTOR" and current_user.mentor_id is not None:
        payload.mentor_id = current_user.mentor_id
    intervention = InterventionService.create_intervention(db=db, payload=payload)
    return InterventionService.to_item_dto(intervention)


@router.get("/summary", response_model=InterventionSummaryResponse, status_code=status.HTTP_200_OK)
def get_interventions_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns operational summary metrics across all intervention records.
    """
    return InterventionService.get_summary(db=db)


@router.get("/effectiveness/summary", response_model=AggregateEffectivenessSummary, status_code=status.HTTP_200_OK)
def get_effectiveness_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns cohort-wide aggregate trajectory outcomes (improved, stable, worsened, awaiting).
    """
    return InterventionEffectivenessService.get_aggregate_summary(db=db)


@router.get("/follow-ups", response_model=PaginatedFollowUpResponse, status_code=status.HTTP_200_OK)
def list_follow_ups(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    state: Optional[str] = Query(None, description="Filter by state (OVERDUE, DUE_TODAY, UPCOMING, CLOSED, NO_FOLLOW_UP)"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a paginated list of scheduled follow-ups with derived urgency state.
    """
    items, total, pages, overdue_cnt, due_today_cnt, upcoming_cnt = InterventionEffectivenessService.get_follow_ups(
        db=db,
        state=state,
        student_id=student_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedFollowUpResponse(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        overdue_count=overdue_cnt,
        due_today_count=due_today_cnt,
        upcoming_count=upcoming_cnt,
    )


@router.get("/{intervention_id}/effectiveness", response_model=InterventionEffectivenessDetail, status_code=status.HTTP_200_OK)
def get_intervention_effectiveness(
    intervention_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves observed before-and-after risk trajectory metrics for a specific intervention.
    """
    intervention = InterventionService.get_intervention_by_id(db=db, intervention_id=intervention_id)
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intervention with ID {intervention_id} not found."
        )
    return InterventionEffectivenessService.evaluate_intervention(db=db, intervention=intervention)


@router.get("", response_model=PaginatedInterventionResponse, status_code=status.HTTP_200_OK)
def list_interventions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    mentor_id: Optional[int] = Query(None, description="Filter by mentor ID"),
    status: Optional[str] = Query(None, description="Filter by status (PLANNED, IN_PROGRESS, COMPLETED, CANCELLED)"),
    intervention_type: Optional[str] = Query(None, description="Filter by type (COUNSELLING, ACADEMIC_SUPPORT, etc.)"),
    follow_ups_due: bool = Query(False, description="Filter only interventions with follow-up due on or before today"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a paginated list of interventions with optional multi-attribute filters.
    """
    items, total, pages = InterventionService.get_interventions(
        db=db,
        page=page,
        page_size=page_size,
        student_id=student_id,
        mentor_id=mentor_id,
        status=status,
        intervention_type=intervention_type,
        follow_ups_due=follow_ups_due,
    )

    response_items = [InterventionService.to_item_dto(item) for item in items]

    return PaginatedInterventionResponse(
        items=response_items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )


@router.get("/{intervention_id}", response_model=InterventionItem, status_code=status.HTTP_200_OK)
def get_intervention_by_id(
    intervention_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a specific intervention by ID.
    """
    intervention = InterventionService.get_intervention_by_id(db=db, intervention_id=intervention_id)
    if not intervention:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intervention with ID {intervention_id} not found."
        )
    return InterventionService.to_item_dto(intervention)


@router.patch("/{intervention_id}", response_model=InterventionItem, status_code=status.HTTP_200_OK)
def update_intervention(
    intervention_id: int,
    payload: InterventionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates an existing intervention status, title, notes, follow-up date, or mentor.
    """
    updated = InterventionService.update_intervention(
        db=db,
        intervention_id=intervention_id,
        payload=payload,
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intervention with ID {intervention_id} not found."
        )
    return InterventionService.to_item_dto(updated)


@router.delete("/{intervention_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_intervention(
    intervention_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Administratively deletes an intervention record.
    """
    success = InterventionService.delete_intervention(db=db, intervention_id=intervention_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intervention with ID {intervention_id} not found."
        )
    return None
