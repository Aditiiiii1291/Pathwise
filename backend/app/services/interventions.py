import math
from datetime import datetime, date, timezone
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from fastapi import HTTPException, status

try:
    from app.models.student import Student
    from app.models.mentor import Mentor
    from app.models.intervention import Intervention, InterventionStatusEnum, InterventionTypeEnum
    from app.schemas.intervention import (
        InterventionCreate,
        InterventionUpdate,
        InterventionItem,
        InterventionSummaryResponse,
    )
except ImportError:
    from backend.app.models.student import Student
    from backend.app.models.mentor import Mentor
    from backend.app.models.intervention import Intervention, InterventionStatusEnum, InterventionTypeEnum
    from backend.app.schemas.intervention import (
        InterventionCreate,
        InterventionUpdate,
        InterventionItem,
        InterventionSummaryResponse,
    )


class InterventionService:
    @staticmethod
    def _is_follow_up_due(follow_up_date: Optional[date], status_str: str) -> bool:
        if not follow_up_date:
            return False
        if status_str in (InterventionStatusEnum.COMPLETED.value, InterventionStatusEnum.CANCELLED.value):
            return False
        return follow_up_date <= date.today()

    @classmethod
    def to_item_dto(cls, intervention: Intervention) -> InterventionItem:
        student = intervention.student
        mentor = intervention.mentor
        status_val = str(intervention.status)
        is_due = cls._is_follow_up_due(intervention.follow_up_date, status_val)

        return InterventionItem(
            id=intervention.id,
            student_id=intervention.student_id,
            student_name=student.name if student else None,
            student_roll=student.roll_number if student else None,
            student_dept=student.department if student else None,
            mentor_id=intervention.mentor_id,
            mentor_name=mentor.name if mentor else None,
            intervention_type=str(intervention.intervention_type or intervention.type or "COUNSELLING"),
            title=intervention.title or "Intervention Record",
            notes=intervention.notes,
            status=status_val,
            follow_up_date=intervention.follow_up_date,
            completed_at=intervention.completed_at,
            created_at=intervention.created_at,
            updated_at=intervention.updated_at,
            is_follow_up_due=is_due,
        )

    @classmethod
    def create_intervention(cls, db: Session, payload: InterventionCreate) -> Intervention:
        """
        Creates a new intervention record after validating student and optional mentor.
        """
        # Validate student existence
        student = db.query(Student).filter(Student.id == payload.student_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student with ID {payload.student_id} not found."
            )

        # Validate mentor if supplied
        if payload.mentor_id is not None:
            mentor = db.query(Mentor).filter(Mentor.id == payload.mentor_id).first()
            if not mentor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Mentor with ID {payload.mentor_id} not found."
                )

        completed_at = None
        if payload.status == InterventionStatusEnum.COMPLETED:
            completed_at = datetime.now(timezone.utc)

        intervention = Intervention(
            student_id=payload.student_id,
            mentor_id=payload.mentor_id,
            intervention_type=payload.intervention_type.value,
            title=payload.title,
            notes=payload.notes,
            status=payload.status.value,
            follow_up_date=payload.follow_up_date,
            completed_at=completed_at,
        )

        db.add(intervention)
        db.commit()
        db.refresh(intervention)
        return intervention

    @classmethod
    def get_intervention_by_id(cls, db: Session, intervention_id: int) -> Optional[Intervention]:
        """
        Retrieves a single intervention by primary key.
        """
        return db.query(Intervention).filter(Intervention.id == intervention_id).first()

    @classmethod
    def get_interventions(
        cls,
        db: Session,
        page: int = 1,
        page_size: int = 20,
        student_id: Optional[int] = None,
        mentor_id: Optional[int] = None,
        status: Optional[str] = None,
        intervention_type: Optional[str] = None,
        follow_ups_due: bool = False,
    ) -> Tuple[List[Intervention], int, int]:
        """
        Queries paginated interventions with optional filters, newest first.
        """
        query = db.query(Intervention)

        if student_id is not None:
            query = query.filter(Intervention.student_id == student_id)
        if mentor_id is not None:
            query = query.filter(Intervention.mentor_id == mentor_id)
        if status:
            query = query.filter(Intervention.status == status.upper())
        if intervention_type:
            query = query.filter(
                or_(
                    Intervention.intervention_type == intervention_type.upper(),
                    Intervention.type == intervention_type.upper()
                )
            )
        if follow_ups_due:
            today = date.today()
            query = query.filter(
                and_(
                    Intervention.follow_up_date.isnot(None),
                    Intervention.follow_up_date <= today,
                    Intervention.status.notin_([
                        InterventionStatusEnum.COMPLETED.value,
                        InterventionStatusEnum.CANCELLED.value
                    ])
                )
            )

        total = query.count()
        pages = max(1, math.ceil(total / page_size)) if total > 0 else 1
        offset = (page - 1) * page_size

        items = query.order_by(
            Intervention.created_at.desc(),
            Intervention.id.desc()
        ).offset(offset).limit(page_size).all()

        return items, total, pages

    @classmethod
    def update_intervention(
        cls,
        db: Session,
        intervention_id: int,
        payload: InterventionUpdate,
    ) -> Optional[Intervention]:
        """
        Updates an existing intervention record.
        """
        intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not intervention:
            return None

        # Validate mentor if provided
        if payload.mentor_id is not None:
            mentor = db.query(Mentor).filter(Mentor.id == payload.mentor_id).first()
            if not mentor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Mentor with ID {payload.mentor_id} not found."
                )
            intervention.mentor_id = payload.mentor_id

        if payload.title is not None:
            intervention.title = payload.title
        if payload.notes is not None:
            intervention.notes = payload.notes
        if payload.intervention_type is not None:
            intervention.intervention_type = payload.intervention_type.value
            intervention.type = payload.intervention_type.value
        if payload.follow_up_date is not None:
            intervention.follow_up_date = payload.follow_up_date
            if payload.follow_up_date:
                intervention.followup_date = datetime(
                    payload.follow_up_date.year,
                    payload.follow_up_date.month,
                    payload.follow_up_date.day,
                    tzinfo=timezone.utc,
                )
            else:
                intervention.followup_date = None

        if payload.status is not None:
            new_status = payload.status.value
            old_status = intervention.status

            if new_status == InterventionStatusEnum.COMPLETED.value and old_status != InterventionStatusEnum.COMPLETED.value:
                intervention.completed_at = datetime.now(timezone.utc)
            elif new_status != InterventionStatusEnum.COMPLETED.value and old_status == InterventionStatusEnum.COMPLETED.value:
                intervention.completed_at = None

            intervention.status = new_status

        db.commit()
        db.refresh(intervention)
        return intervention

    @classmethod
    def delete_intervention(cls, db: Session, intervention_id: int) -> bool:
        """
        Administrative deletion of an intervention record.
        """
        intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
        if not intervention:
            return False
        db.delete(intervention)
        db.commit()
        return True

    @classmethod
    def get_summary(cls, db: Session) -> InterventionSummaryResponse:
        """
        Returns live count aggregates for the intervention management dashboard.
        """
        total = db.query(Intervention).count()
        active = db.query(Intervention).filter(Intervention.status == InterventionStatusEnum.IN_PROGRESS.value).count()
        planned = db.query(Intervention).filter(
            or_(
                Intervention.status == InterventionStatusEnum.PLANNED.value,
                Intervention.status == "SCHEDULED"
            )
        ).count()
        completed = db.query(Intervention).filter(Intervention.status == InterventionStatusEnum.COMPLETED.value).count()
        cancelled = db.query(Intervention).filter(Intervention.status == InterventionStatusEnum.CANCELLED.value).count()

        today = date.today()
        follow_ups_due = db.query(Intervention).filter(
            and_(
                Intervention.follow_up_date.isnot(None),
                Intervention.follow_up_date <= today,
                Intervention.status.notin_([
                    InterventionStatusEnum.COMPLETED.value,
                    InterventionStatusEnum.CANCELLED.value
                ])
            )
        ).count()

        return InterventionSummaryResponse(
            total_interventions=total,
            active_count=active,
            planned_count=planned,
            completed_count=completed,
            cancelled_count=cancelled,
            follow_ups_due_count=follow_ups_due,
        )
