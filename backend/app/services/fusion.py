from typing import Optional, List
from sqlalchemy.orm import Session

try:
    from app.models import Student
    from app.crud.student import get_student_by_id, get_student_by_roll_number, get_all_students
    from app.schemas.student import (
        MentorSummary,
        StudentBasic,
        AttendanceHistoryItem,
        MarksHistoryItem,
        FeeHistoryItem,
        AttemptHistoryItem,
        UnifiedStudentProfile,
    )
except ImportError:
    from backend.app.models import Student
    from backend.app.crud.student import get_student_by_id, get_student_by_roll_number, get_all_students
    from backend.app.schemas.student import (
        MentorSummary,
        StudentBasic,
        AttendanceHistoryItem,
        MarksHistoryItem,
        FeeHistoryItem,
        AttemptHistoryItem,
        UnifiedStudentProfile,
    )

EXAM_TYPE_ORDER = {
    "TEST1": 1,
    "TEST2": 2,
    "TEST3": 3,
    "MIDTERM": 4,
    "FINAL": 5,
    "OTHER": 6,
}

class StudentDataFusionService:
    """Service to fuse disconnected institutional data tables into a unified student profile."""

    def __init__(self, db: Session):
        self.db = db

    def fuse_by_id(self, student_id: int) -> Optional[UnifiedStudentProfile]:
        """Loads and fuses student records by primary key ID."""
        student = get_student_by_id(self.db, student_id)
        if not student:
            return None
        return self.fuse_student(student)

    def fuse_by_roll_number(self, roll_number: str) -> Optional[UnifiedStudentProfile]:
        """Loads and fuses student records by institutional roll number."""
        student = get_student_by_roll_number(self.db, roll_number)
        if not student:
            return None
        return self.fuse_student(student)

    def fuse_all(self, skip: int = 0, limit: int = 1000) -> List[UnifiedStudentProfile]:
        """Fuses multiple students in a single eager-loaded batch."""
        students = get_all_students(self.db, skip=skip, limit=limit)
        return [self.fuse_student(s) for s in students]

    def fuse_student(self, student: Student) -> UnifiedStudentProfile:
        """Transforms a Student ORM entity and loaded relationships into a UnifiedStudentProfile."""
        
        # 1. Mentor Summary
        mentor_summary = None
        if student.mentor:
            mentor_summary = MentorSummary(
                id=student.mentor.id,
                name=student.mentor.name,
                email=student.mentor.email,
                department=student.mentor.department,
                phone=student.mentor.phone,
            )

        # 2. Student Basic Info (strictly excluding synthetic trajectory_type / dropout_label)
        student_basic = StudentBasic(
            id=student.id,
            roll_number=student.roll_number,
            name=student.name,
            department=student.department,
            semester=student.semester,
            guardian_name=student.guardian_name,
            guardian_phone=student.guardian_phone,
            guardian_email=student.guardian_email,
            enrollment_year=student.enrollment_year,
            mentor=mentor_summary,
        )

        # 3. Attendance History (sorted chronologically by week_number)
        raw_attendance = student.attendance_records or []
        sorted_attendance = sorted(
            raw_attendance,
            key=lambda r: (r.week_number, r.id or 0)
        )
        attendance_items = [
            AttendanceHistoryItem(
                id=r.id,
                week_number=r.week_number,
                month=r.month,
                total_classes=r.total_classes,
                attended_classes=r.attended_classes,
                percentage=r.percentage,
            )
            for r in sorted_attendance
        ]

        # 4. Marks History (sorted deterministically by subject_name, exam sequence, attempt_number)
        raw_marks = student.marks_records or []
        def marks_sort_key(r):
            exam_val = r.exam_type.value if hasattr(r.exam_type, "value") else str(r.exam_type)
            order = EXAM_TYPE_ORDER.get(exam_val.upper(), 99)
            return (r.subject_name.lower(), order, r.attempt_number, r.id or 0)

        sorted_marks = sorted(raw_marks, key=marks_sort_key)
        marks_items = [
            MarksHistoryItem(
                id=r.id,
                subject_name=r.subject_name,
                exam_type=r.exam_type.value if hasattr(r.exam_type, "value") else str(r.exam_type),
                max_marks=r.max_marks,
                obtained_marks=r.obtained_marks,
                attempt_number=r.attempt_number,
            )
            for r in sorted_marks
        ]

        # 5. Fee History (sorted by semester, due_date)
        raw_fees = student.fee_records or []
        sorted_fees = sorted(
            raw_fees,
            key=lambda r: (r.semester, r.due_date or "", r.id or 0)
        )
        fee_items = [
            FeeHistoryItem(
                id=r.id,
                semester=r.semester,
                total_fee=r.total_fee,
                paid_amount=r.paid_amount,
                due_date=r.due_date,
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
            )
            for r in sorted_fees
        ]

        # 6. Attempt / Backlog History (sorted by semester, subject, attempt_number)
        raw_attempts = student.attempt_records or []
        sorted_attempts = sorted(
            raw_attempts,
            key=lambda r: (r.semester, r.subject_name.lower(), r.attempt_number, r.id or 0)
        )
        attempt_items = [
            AttemptHistoryItem(
                id=r.id,
                subject_name=r.subject_name,
                semester=r.semester,
                attempt_number=r.attempt_number,
                status=r.status.value if hasattr(r.status, "value") else str(r.status),
            )
            for r in sorted_attempts
        ]

        return UnifiedStudentProfile(
            student=student_basic,
            attendance=attendance_items,
            marks=marks_items,
            fees=fee_items,
            attempts=attempt_items,
            attendance_record_count=len(attendance_items),
            marks_record_count=len(marks_items),
            fee_record_count=len(fee_items),
            attempt_record_count=len(attempt_items),
        )
