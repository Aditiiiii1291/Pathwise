import enum
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

class ExamTypeEnum(str, enum.Enum):
    TEST1 = "TEST1"
    TEST2 = "TEST2"
    TEST3 = "TEST3"
    MIDTERM = "MIDTERM"
    FINAL = "FINAL"
    OTHER = "OTHER"

class MarksRecord(Base):
    __tablename__ = "marks_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    subject_name = Column(String, nullable=False)
    exam_type = Column(Enum(ExamTypeEnum), nullable=False)
    max_marks = Column(Float, nullable=False)
    obtained_marks = Column(Float, nullable=False)
    attempt_number = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="marks_records")
