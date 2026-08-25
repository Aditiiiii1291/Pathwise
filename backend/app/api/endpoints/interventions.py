from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
    from app.schemas.intervention import (
        InterventionCreate,
        InterventionUpdate,
        InterventionItem,
        PaginatedInterventionResponse,
        InterventionSummaryResponse,
    )
    from app.services.interventions import InterventionService
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.schemas.intervention import (
        InterventionCreate,
        InterventionUpdate,
        InterventionItem,
        PaginatedInterventionResponse,
        InterventionSummaryResponse,
    )
    from backend.app.services.interventions import InterventionService

router = APIRouter(prefix="/interventions", tags=["interventions"])


@router.post("", response_model=InterventionItem, status_code=status.HTTP_201_CREATED)
def create_intervention(
    payload: InterventionCreate,
    db: Session = Depends(get_db),
):
    """
    Creates a new counselling or intervention record for a student.
    """
    intervention = InterventionService.create_intervention(db=db, payload=payload)
    return InterventionService.to_item_dto(intervention)


@router.get("/summary", response_model=InterventionSummaryResponse, status_code=status.HTTP_200_OK)
def get_interventions_summary(
    db: Session = Depends(get_db),
):
    """
    Returns aggregate summary metrics across all intervention records.
    """
    return InterventionService.get_summary(db=db)


@router.get("", response_model=PaginatedInterventionResponse, status_code=status.HTTP_200_OK)
def list_interventions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    mentor_id: Optional[int] = Query(None, description="Filter by mentor ID"),
    status: Optional[str] = Query(None, description="Filter by status (PLANNED, IN_PROGRESS, COMPLETED, CANCELLED)"),
    intervention_type: Optional[str] = Query(None, description="Filter by type (COUNSELLING, ACADEMIC_SUPPORT, etc.)"),
    follow_ups_due: bool = Query(False, description="Filter only interventions with follow-up due on or before today"),
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
