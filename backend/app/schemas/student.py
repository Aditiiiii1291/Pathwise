from typing import List, Optional
from pydantic import BaseModel, Field

class MentorSummary(BaseModel):
    id: int
    name: str
    email: str
    department: str
    phone: Optional[str] = None

class StudentBasic(BaseModel):
    id: int
    roll_number: str
    name: str
    department: str
    semester: int
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None
    enrollment_year: Optional[int] = None
    mentor: Optional[MentorSummary] = None

class AttendanceHistoryItem(BaseModel):
    id: Optional[int] = None
    week_number: int
    month: Optional[str] = None
    total_classes: int
    attended_classes: int
    percentage: float

class MarksHistoryItem(BaseModel):
    id: Optional[int] = None
    subject_name: str
    exam_type: str
    max_marks: float
    obtained_marks: float
    attempt_number: int

class FeeHistoryItem(BaseModel):
    id: Optional[int] = None
    semester: int
    total_fee: float
    paid_amount: float
    due_date: Optional[str] = None
    status: str

class AttemptHistoryItem(BaseModel):
    id: Optional[int] = None
    subject_name: str
    semester: int
    attempt_number: int
    status: str

class UnifiedStudentProfile(BaseModel):
    student: StudentBasic
    attendance: List[AttendanceHistoryItem] = Field(default_factory=list)
    marks: List[MarksHistoryItem] = Field(default_factory=list)
    fees: List[FeeHistoryItem] = Field(default_factory=list)
    attempts: List[AttemptHistoryItem] = Field(default_factory=list)
    
    # Structural count metadata (non-analytical)
    attendance_record_count: int = 0
    marks_record_count: int = 0
    fee_record_count: int = 0
    attempt_record_count: int = 0
