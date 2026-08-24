from typing import Optional, List
from sqlalchemy.orm import Session, selectinload

try:
    from app.models import Student
except ImportError:
    from backend.app.models import Student

def get_student_query(db: Session):
    """Base query for Student with eager-loaded academic relationships to prevent N+1 queries."""
    return db.query(Student).options(
        selectinload(Student.mentor),
        selectinload(Student.attendance_records),
        selectinload(Student.marks_records),
        selectinload(Student.fee_records),
        selectinload(Student.attempt_records),
    )

def get_student_by_id(db: Session, student_id: int) -> Optional[Student]:
    """Retrieves a single student by primary key ID with all relationships."""
    return get_student_query(db).filter(Student.id == student_id).first()

def get_student_by_roll_number(db: Session, roll_number: str) -> Optional[Student]:
    """Retrieves a single student by roll number with all relationships."""
    return get_student_query(db).filter(Student.roll_number == roll_number).first()

def get_all_students(db: Session, skip: int = 0, limit: int = 1000) -> List[Student]:
    """Retrieves students in batches with all relationships."""
    return get_student_query(db).offset(skip).limit(limit).all()
