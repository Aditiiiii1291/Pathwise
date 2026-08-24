import enum
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

class InterventionTypeEnum(str, enum.Enum):
    COUNSELLING = "COUNSELLING"
    ACADEMIC_SUPPORT = "ACADEMIC_SUPPORT"
    FEE_VERIFICATION = "FEE_VERIFICATION"
    ATTENDANCE_PLAN = "ATTENDANCE_PLAN"
    BACKLOG_PLAN = "BACKLOG_PLAN"
    OTHER = "OTHER"

class InterventionStatusEnum(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class InterventionOutcomeEnum(str, enum.Enum):
    PENDING = "PENDING"
    IMPROVED = "IMPROVED"
    UNCHANGED = "UNCHANGED"
    ESCALATED = "ESCALATED"

class Intervention(Base):
    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    mentor_id = Column(Integer, ForeignKey("mentors.id"), nullable=False, index=True)
    date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    type = Column(Enum(InterventionTypeEnum), nullable=False)
    notes = Column(Text, nullable=True)
    risk_score_before = Column(Float, nullable=False)
    followup_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(InterventionStatusEnum), default=InterventionStatusEnum.SCHEDULED, nullable=False)
    outcome = Column(Enum(InterventionOutcomeEnum), default=InterventionOutcomeEnum.PENDING, nullable=False)
    risk_score_after = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="interventions")
    mentor = relationship("Mentor", back_populates="interventions")
