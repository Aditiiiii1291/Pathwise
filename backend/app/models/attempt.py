import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

class BacklogStatusEnum(str, enum.Enum):
    ACTIVE = "ACTIVE"
    CLEARED = "CLEARED"

class AttemptRecord(Base):
    __tablename__ = "attempt_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    subject_name = Column(String, nullable=False)
    semester = Column(Integer, nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    status = Column(Enum(BacklogStatusEnum), default=BacklogStatusEnum.ACTIVE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="attempt_records")
