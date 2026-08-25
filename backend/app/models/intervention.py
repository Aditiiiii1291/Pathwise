import enum
from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy import Column, Integer, Float, String, DateTime, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base


class InterventionTypeEnum(str, enum.Enum):
    COUNSELLING = "COUNSELLING"
    ACADEMIC_SUPPORT = "ACADEMIC_SUPPORT"
    ATTENDANCE_SUPPORT = "ATTENDANCE_SUPPORT"
    FINANCIAL_GUIDANCE = "FINANCIAL_GUIDANCE"
    MENTOR_MEETING = "MENTOR_MEETING"
    GUARDIAN_CONTACT = "GUARDIAN_CONTACT"
    STUDY_PLAN = "STUDY_PLAN"
    OTHER = "OTHER"

    # Legacy enum values preserved for backward-compatibility with Phase 2 tests
    FEE_VERIFICATION = "FEE_VERIFICATION"
    ATTENDANCE_PLAN = "ATTENDANCE_PLAN"
    BACKLOG_PLAN = "BACKLOG_PLAN"


class InterventionStatusEnum(str, enum.Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    # Legacy status alias for Phase 2 tests
    SCHEDULED = "SCHEDULED"


class InterventionOutcomeEnum(str, enum.Enum):
    PENDING = "PENDING"
    IMPROVED = "IMPROVED"
    UNCHANGED = "UNCHANGED"
    ESCALATED = "ESCALATED"


class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.id", ondelete="SET NULL"), nullable=True, index=True)

    # Core Phase 14 metadata
    intervention_type = Column(String(50), nullable=False, default=InterventionTypeEnum.COUNSELLING.value, index=True)
    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default=InterventionStatusEnum.PLANNED.value, index=True)

    # Scheduling and lifecycle timestamps
    follow_up_date = Column(Date, nullable=True, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Legacy / Phase 2 fields maintained for backward compatibility
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    type = Column(String(50), nullable=True)
    risk_score_before = Column(Float, nullable=True, default=0.0)
    risk_score_after = Column(Float, nullable=True)
    followup_date = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(String(50), nullable=True, default=InterventionOutcomeEnum.PENDING.value)

    # Relationships
    student = relationship("Student", back_populates="interventions")
    mentor = relationship("Mentor", back_populates="interventions")

    def __init__(self, **kwargs):
        # Support legacy argument names seamlessly
        if "type" in kwargs and "intervention_type" not in kwargs:
            t = kwargs.pop("type")
            kwargs["intervention_type"] = t.value if isinstance(t, enum.Enum) else str(t)
            kwargs["type"] = kwargs["intervention_type"]
        elif "intervention_type" in kwargs:
            it = kwargs["intervention_type"]
            kwargs["type"] = it.value if isinstance(it, enum.Enum) else str(it)

        if "status" in kwargs:
            s = kwargs["status"]
            val = s.value if isinstance(s, enum.Enum) else str(s)
            # Map legacy SCHEDULED to PLANNED
            if val == "SCHEDULED":
                kwargs["status"] = "PLANNED"
            else:
                kwargs["status"] = val

        if "outcome" in kwargs:
            o = kwargs["outcome"]
            kwargs["outcome"] = o.value if isinstance(o, enum.Enum) else str(o)

        if "followup_date" in kwargs and "follow_up_date" not in kwargs:
            f_date = kwargs.pop("followup_date")
            if isinstance(f_date, datetime):
                kwargs["follow_up_date"] = f_date.date()
                kwargs["followup_date"] = f_date
            elif isinstance(f_date, date):
                kwargs["follow_up_date"] = f_date
                kwargs["followup_date"] = datetime(f_date.year, f_date.month, f_date.day, tzinfo=timezone.utc)
        elif "follow_up_date" in kwargs:
            f_date = kwargs["follow_up_date"]
            if isinstance(f_date, date) and not isinstance(f_date, datetime):
                kwargs["followup_date"] = datetime(f_date.year, f_date.month, f_date.day, tzinfo=timezone.utc)

        if "title" not in kwargs or not kwargs["title"]:
            itype = kwargs.get("intervention_type", "COUNSELLING")
            kwargs["title"] = f"{str(itype).replace('_', ' ').title()} Support"

        super().__init__(**kwargs)
