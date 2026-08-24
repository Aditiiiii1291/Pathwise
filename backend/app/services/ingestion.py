import io
import math
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
from sqlalchemy.orm import Session

try:
    from app.services.column_mapper import map_columns
    from app.schemas.upload import UploadSummary, UploadError
    from app.models import (
        Student,
        AttendanceRecord,
        MarksRecord,
        ExamTypeEnum,
        FeeRecord,
        FeeStatusEnum,
        AttemptRecord,
        BacklogStatusEnum,
    )
except ImportError:
    from backend.app.services.column_mapper import map_columns
    from backend.app.schemas.upload import UploadSummary, UploadError
    from backend.app.models import (
        Student,
        AttendanceRecord,
        MarksRecord,
        ExamTypeEnum,
        FeeRecord,
        FeeStatusEnum,
        AttemptRecord,
        BacklogStatusEnum,
    )

EXAM_TYPE_MAP = {
    "test1": ExamTypeEnum.TEST1,
    "test_1": ExamTypeEnum.TEST1,
    "test 1": ExamTypeEnum.TEST1,
    "t1": ExamTypeEnum.TEST1,
    "test2": ExamTypeEnum.TEST2,
    "test_2": ExamTypeEnum.TEST2,
    "test 2": ExamTypeEnum.TEST2,
    "t2": ExamTypeEnum.TEST2,
    "test3": ExamTypeEnum.TEST3,
    "test_3": ExamTypeEnum.TEST3,
    "test 3": ExamTypeEnum.TEST3,
    "t3": ExamTypeEnum.TEST3,
    "midterm": ExamTypeEnum.MIDTERM,
    "mid_term": ExamTypeEnum.MIDTERM,
    "mid term": ExamTypeEnum.MIDTERM,
    "midsem": ExamTypeEnum.MIDTERM,
    "final": ExamTypeEnum.FINAL,
    "endsem": ExamTypeEnum.FINAL,
    "end_term": ExamTypeEnum.FINAL,
    "other": ExamTypeEnum.OTHER,
}

FEE_STATUS_MAP = {
    "paid": FeeStatusEnum.PAID,
    "complete": FeeStatusEnum.PAID,
    "completed": FeeStatusEnum.PAID,
    "partial": FeeStatusEnum.PARTIAL,
    "partially_paid": FeeStatusEnum.PARTIAL,
    "part": FeeStatusEnum.PARTIAL,
    "pending": FeeStatusEnum.PENDING,
    "due": FeeStatusEnum.PENDING,
    "unpaid": FeeStatusEnum.PENDING,
}

BACKLOG_STATUS_MAP = {
    "active": BacklogStatusEnum.ACTIVE,
    "uncleared": BacklogStatusEnum.ACTIVE,
    "pending": BacklogStatusEnum.ACTIVE,
    "fail": BacklogStatusEnum.ACTIVE,
    "failed": BacklogStatusEnum.ACTIVE,
    "cleared": BacklogStatusEnum.CLEARED,
    "passed": BacklogStatusEnum.CLEARED,
    "pass": BacklogStatusEnum.CLEARED,
}

class IngestionService:
    """Service to process, validate, and persist tabular student retention datasets."""

    def __init__(self, db: Session):
        self.db = db

    def parse_file(self, filename: str, content: bytes) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """Reads file bytes into DataFrame based on file extension."""
        lower_name = filename.lower()
        try:
            if lower_name.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content))
            elif lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
                df = pd.read_excel(io.BytesIO(content), engine="openpyxl")
            else:
                return None, f"Unsupported file type for '{filename}'. Only .csv and .xlsx files are supported."
            
            if df.empty:
                return None, f"Uploaded file '{filename}' is empty."
            return df, None
        except Exception as e:
            return None, f"Failed to parse file '{filename}': {str(e)}"

    def ingest(self, data_type: str, filename: str, content: bytes) -> UploadSummary:
        """Main ingestion pipeline."""
        df, parse_error = self.parse_file(filename, content)
        if parse_error:
            return UploadSummary(
                data_type=data_type,
                filename=filename,
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                inserted_rows=0,
                errors=[UploadError(code="PARSE_ERROR", message=parse_error)],
            )

        # Map column headers
        col_map, missing_req, map_error = map_columns(data_type, list(df.columns))
        if map_error:
            return UploadSummary(
                data_type=data_type,
                filename=filename,
                total_rows=len(df),
                valid_rows=0,
                invalid_rows=len(df),
                inserted_rows=0,
                errors=[UploadError(code="AMBIGUOUS_COLUMN_MAPPING", message=map_error)],
            )

        if missing_req:
            return UploadSummary(
                data_type=data_type,
                filename=filename,
                total_rows=len(df),
                valid_rows=0,
                invalid_rows=len(df),
                inserted_rows=0,
                errors=[
                    UploadError(
                        code="MISSING_REQUIRED_COLUMN",
                        message=f"Missing required column(s): {', '.join(missing_req)}"
                    )
                ],
            )

        # Rename columns in dataframe to canonical names
        renamed_df = df.rename(columns=col_map)

        # Dispatch to specific validator
        if data_type == "students":
            return self._ingest_students(renamed_df, filename)
        elif data_type == "attendance":
            return self._ingest_attendance(renamed_df, filename)
        elif data_type == "marks":
            return self._ingest_marks(renamed_df, filename)
        elif data_type == "fees":
            return self._ingest_fees(renamed_df, filename)
        elif data_type == "attempts":
            return self._ingest_attempts(renamed_df, filename)
        else:
            return UploadSummary(
                data_type=data_type,
                filename=filename,
                total_rows=len(df),
                valid_rows=0,
                invalid_rows=len(df),
                inserted_rows=0,
                errors=[UploadError(code="INVALID_DATA_TYPE", message=f"Unknown data type: '{data_type}'")],
            )

    def _get_existing_student_ids(self) -> set:
        """Helper to get set of all existing student IDs in database."""
        students = self.db.query(Student.id).all()
        return {s[0] for s in students}

    def _ingest_students(self, df: pd.DataFrame, filename: str) -> UploadSummary:
        errors: List[UploadError] = []
        valid_objects: List[Student] = []
        seen_student_ids = set()
        seen_roll_numbers = set()

        for idx, row in df.iterrows():
            row_num = idx + 2  # 1-indexed plus header row

            # Required field validation
            s_id = row.get("student_id")
            roll = row.get("roll_number")
            name = row.get("name")
            dept = row.get("department")
            sem = row.get("semester")

            if pd.isna(s_id) or pd.isna(roll) or pd.isna(name) or pd.isna(dept) or pd.isna(sem):
                errors.append(UploadError(row_number=row_num, field="required_fields", code="MISSING_REQUIRED_VALUE", message="Missing required student attributes"))
                continue

            try:
                s_id = int(s_id)
                sem = int(sem)
            except (ValueError, TypeError):
                errors.append(UploadError(row_number=row_num, field="type", code="INVALID_TYPE", message="student_id and semester must be integers"))
                continue

            roll = str(roll).strip()
            name = str(name).strip()
            dept = str(dept).strip()

            # Duplicate check within upload batch
            if s_id in seen_student_ids:
                errors.append(UploadError(row_number=row_num, field="student_id", code="DUPLICATE_ROW", message=f"Duplicate student_id '{s_id}' in file"))
                continue
            if roll in seen_roll_numbers:
                errors.append(UploadError(row_number=row_num, field="roll_number", code="DUPLICATE_ROW", message=f"Duplicate roll_number '{roll}' in file"))
                continue

            seen_student_ids.add(s_id)
            seen_roll_numbers.add(roll)

            # Optional fields
            g_name = str(row["guardian_name"]).strip() if pd.notna(row.get("guardian_name")) else None
            g_phone = str(row["guardian_phone"]).strip() if pd.notna(row.get("guardian_phone")) else None
            g_email = str(row["guardian_email"]).strip() if pd.notna(row.get("guardian_email")) else None
            mentor_id = int(row["mentor_id"]) if pd.notna(row.get("mentor_id")) else None
            enroll_year = int(row["enrollment_year"]) if pd.notna(row.get("enrollment_year")) else None

            student = Student(
                id=s_id,
                roll_number=roll,
                name=name,
                department=dept,
                semester=sem,
                guardian_name=g_name,
                guardian_phone=g_phone,
                guardian_email=g_email,
                mentor_id=mentor_id,
                enrollment_year=enroll_year,
            )
            valid_objects.append(student)

        # Batch DB insertion with merge/upsert safety
        inserted = 0
        if valid_objects:
            try:
                for obj in valid_objects:
                    self.db.merge(obj)
                self.db.commit()
                inserted = len(valid_objects)
            except Exception as e:
                self.db.rollback()
                errors.append(UploadError(code="DB_ERROR", message=f"Database insertion failed: {str(e)}"))

        return UploadSummary(
            data_type="students",
            filename=filename,
            total_rows=len(df),
            valid_rows=len(valid_objects),
            invalid_rows=len(df) - len(valid_objects),
            inserted_rows=inserted,
            errors=errors[:100],  # Cap returned diagnostics
        )

    def _ingest_attendance(self, df: pd.DataFrame, filename: str) -> UploadSummary:
        errors: List[UploadError] = []
        valid_objects: List[AttendanceRecord] = []
        existing_student_ids = self._get_existing_student_ids()
        seen_keys = set()

        for idx, row in df.iterrows():
            row_num = idx + 2

            s_id = row.get("student_id")
            week = row.get("week_number")
            total = row.get("total_classes")
            attended = row.get("attended_classes")

            if pd.isna(s_id) or pd.isna(week) or pd.isna(total) or pd.isna(attended):
                errors.append(UploadError(row_number=row_num, field="required_fields", code="MISSING_REQUIRED_VALUE", message="Missing required attendance values"))
                continue

            try:
                s_id = int(s_id)
                week = int(week)
                total = int(total)
                attended = int(attended)
            except (ValueError, TypeError):
                errors.append(UploadError(row_number=row_num, field="type", code="INVALID_TYPE", message="Attendance counts and week must be numeric integers"))
                continue

            if s_id not in existing_student_ids:
                errors.append(UploadError(row_number=row_num, field="student_id", code="UNKNOWN_STUDENT", message=f"Student ID {s_id} does not exist in roster"))
                continue

            if total <= 0:
                errors.append(UploadError(row_number=row_num, field="total_classes", code="VALUE_OUT_OF_RANGE", message="total_classes must be greater than 0"))
                continue

            if attended < 0 or attended > total:
                errors.append(UploadError(row_number=row_num, field="attended_classes", code="VALUE_OUT_OF_RANGE", message="attended_classes must be between 0 and total_classes"))
                continue

            key = (s_id, week)
            if key in seen_keys:
                errors.append(UploadError(row_number=row_num, field="week_number", code="DUPLICATE_ROW", message=f"Duplicate attendance record for student {s_id} in week {week}"))
                continue
            seen_keys.add(key)

            month = str(row["month"]).strip() if pd.notna(row.get("month")) else None
            percentage = round((attended / total) * 100.0, 2)

            valid_objects.append(AttendanceRecord(
                student_id=s_id,
                week_number=week,
                month=month,
                total_classes=total,
                attended_classes=attended,
                percentage=percentage,
            ))

        inserted = 0
        if valid_objects:
            try:
                self.db.add_all(valid_objects)
                self.db.commit()
                inserted = len(valid_objects)
            except Exception as e:
                self.db.rollback()
                errors.append(UploadError(code="DB_ERROR", message=f"Database insertion failed: {str(e)}"))

        return UploadSummary(
            data_type="attendance",
            filename=filename,
            total_rows=len(df),
            valid_rows=len(valid_objects),
            invalid_rows=len(df) - len(valid_objects),
            inserted_rows=inserted,
            errors=errors[:100],
        )

    def _ingest_marks(self, df: pd.DataFrame, filename: str) -> UploadSummary:
        errors: List[UploadError] = []
        valid_objects: List[MarksRecord] = []
        existing_student_ids = self._get_existing_student_ids()
        seen_keys = set()

        for idx, row in df.iterrows():
            row_num = idx + 2

            s_id = row.get("student_id")
            subj = row.get("subject_name")
            exam_raw = row.get("exam_type")
            max_m = row.get("max_marks")
            obt_m = row.get("obtained_marks")

            if pd.isna(s_id) or pd.isna(subj) or pd.isna(exam_raw) or pd.isna(max_m) or pd.isna(obt_m):
                errors.append(UploadError(row_number=row_num, field="required_fields", code="MISSING_REQUIRED_VALUE", message="Missing required marks values"))
                continue

            try:
                s_id = int(s_id)
                max_m = float(max_m)
                obt_m = float(obt_m)
                attempt_num = int(row.get("attempt_number", 1)) if pd.notna(row.get("attempt_number")) else 1
            except (ValueError, TypeError):
                errors.append(UploadError(row_number=row_num, field="type", code="INVALID_TYPE", message="Marks, student_id, and attempt_number must be numeric"))
                continue

            if s_id not in existing_student_ids:
                errors.append(UploadError(row_number=row_num, field="student_id", code="UNKNOWN_STUDENT", message=f"Student ID {s_id} does not exist in roster"))
                continue

            subj = str(subj).strip()
            norm_exam_str = str(exam_raw).strip().lower().replace("-", "_")
            enum_exam = EXAM_TYPE_MAP.get(norm_exam_str, ExamTypeEnum.OTHER)

            if max_m <= 0:
                errors.append(UploadError(row_number=row_num, field="max_marks", code="VALUE_OUT_OF_RANGE", message="max_marks must be greater than 0"))
                continue

            if obt_m < 0 or obt_m > max_m:
                errors.append(UploadError(row_number=row_num, field="obtained_marks", code="VALUE_OUT_OF_RANGE", message="obtained_marks must be between 0 and max_marks"))
                continue

            if attempt_num < 1:
                errors.append(UploadError(row_number=row_num, field="attempt_number", code="VALUE_OUT_OF_RANGE", message="attempt_number must be >= 1"))
                continue

            key = (s_id, subj, enum_exam.value, attempt_num)
            if key in seen_keys:
                errors.append(UploadError(row_number=row_num, field="subject_name", code="DUPLICATE_ROW", message=f"Duplicate marks record for student {s_id}, subject '{subj}', exam {enum_exam.value}"))
                continue
            seen_keys.add(key)

            valid_objects.append(MarksRecord(
                student_id=s_id,
                subject_name=subj,
                exam_type=enum_exam,
                max_marks=max_m,
                obtained_marks=obt_m,
                attempt_number=attempt_num,
            ))

        inserted = 0
        if valid_objects:
            try:
                self.db.add_all(valid_objects)
                self.db.commit()
                inserted = len(valid_objects)
            except Exception as e:
                self.db.rollback()
                errors.append(UploadError(code="DB_ERROR", message=f"Database insertion failed: {str(e)}"))

        return UploadSummary(
            data_type="marks",
            filename=filename,
            total_rows=len(df),
            valid_rows=len(valid_objects),
            invalid_rows=len(df) - len(valid_objects),
            inserted_rows=inserted,
            errors=errors[:100],
        )

    def _ingest_fees(self, df: pd.DataFrame, filename: str) -> UploadSummary:
        errors: List[UploadError] = []
        valid_objects: List[FeeRecord] = []
        existing_student_ids = self._get_existing_student_ids()
        seen_keys = set()

        for idx, row in df.iterrows():
            row_num = idx + 2

            s_id = row.get("student_id")
            sem = row.get("semester")
            total = row.get("total_fee")
            paid = row.get("paid_amount")
            status_raw = row.get("status")

            if pd.isna(s_id) or pd.isna(sem) or pd.isna(total) or pd.isna(paid) or pd.isna(status_raw):
                errors.append(UploadError(row_number=row_num, field="required_fields", code="MISSING_REQUIRED_VALUE", message="Missing required fee attributes"))
                continue

            try:
                s_id = int(s_id)
                sem = int(sem)
                total = float(total)
                paid = float(paid)
            except (ValueError, TypeError):
                errors.append(UploadError(row_number=row_num, field="type", code="INVALID_TYPE", message="Fee amounts, student_id, and semester must be numeric"))
                continue

            if s_id not in existing_student_ids:
                errors.append(UploadError(row_number=row_num, field="student_id", code="UNKNOWN_STUDENT", message=f"Student ID {s_id} does not exist in roster"))
                continue

            if total < 0 or paid < 0 or paid > total:
                errors.append(UploadError(row_number=row_num, field="paid_amount", code="VALUE_OUT_OF_RANGE", message="paid_amount must be between 0 and total_fee"))
                continue

            norm_status = str(status_raw).strip().lower()
            if norm_status not in FEE_STATUS_MAP:
                errors.append(UploadError(row_number=row_num, field="status", code="INVALID_ENUM", message=f"Invalid fee status: '{status_raw}'"))
                continue
            enum_status = FEE_STATUS_MAP[norm_status]

            key = (s_id, sem)
            if key in seen_keys:
                errors.append(UploadError(row_number=row_num, field="semester", code="DUPLICATE_ROW", message=f"Duplicate fee record for student {s_id}, semester {sem}"))
                continue
            seen_keys.add(key)

            due_date = str(row["due_date"]).strip() if pd.notna(row.get("due_date")) else None

            valid_objects.append(FeeRecord(
                student_id=s_id,
                semester=sem,
                total_fee=total,
                paid_amount=paid,
                due_date=due_date,
                status=enum_status,
            ))

        inserted = 0
        if valid_objects:
            try:
                self.db.add_all(valid_objects)
                self.db.commit()
                inserted = len(valid_objects)
            except Exception as e:
                self.db.rollback()
                errors.append(UploadError(code="DB_ERROR", message=f"Database insertion failed: {str(e)}"))

        return UploadSummary(
            data_type="fees",
            filename=filename,
            total_rows=len(df),
            valid_rows=len(valid_objects),
            invalid_rows=len(df) - len(valid_objects),
            inserted_rows=inserted,
            errors=errors[:100],
        )

    def _ingest_attempts(self, df: pd.DataFrame, filename: str) -> UploadSummary:
        errors: List[UploadError] = []
        valid_objects: List[AttemptRecord] = []
        existing_student_ids = self._get_existing_student_ids()
        seen_keys = set()

        for idx, row in df.iterrows():
            row_num = idx + 2

            s_id = row.get("student_id")
            subj = row.get("subject_name")
            sem = row.get("semester")
            attempt_num = row.get("attempt_number")
            status_raw = row.get("status")

            if pd.isna(s_id) or pd.isna(subj) or pd.isna(sem) or pd.isna(attempt_num) or pd.isna(status_raw):
                errors.append(UploadError(row_number=row_num, field="required_fields", code="MISSING_REQUIRED_VALUE", message="Missing required attempt values"))
                continue

            try:
                s_id = int(s_id)
                sem = int(sem)
                attempt_num = int(attempt_num)
            except (ValueError, TypeError):
                errors.append(UploadError(row_number=row_num, field="type", code="INVALID_TYPE", message="student_id, semester, and attempt_number must be integers"))
                continue

            if s_id not in existing_student_ids:
                errors.append(UploadError(row_number=row_num, field="student_id", code="UNKNOWN_STUDENT", message=f"Student ID {s_id} does not exist in roster"))
                continue

            if attempt_num < 1:
                errors.append(UploadError(row_number=row_num, field="attempt_number", code="VALUE_OUT_OF_RANGE", message="attempt_number must be >= 1"))
                continue

            subj = str(subj).strip()
            norm_status = str(status_raw).strip().lower()
            if norm_status not in BACKLOG_STATUS_MAP:
                errors.append(UploadError(row_number=row_num, field="status", code="INVALID_ENUM", message=f"Invalid attempt/backlog status: '{status_raw}'"))
                continue
            enum_status = BACKLOG_STATUS_MAP[norm_status]

            key = (s_id, subj, attempt_num)
            if key in seen_keys:
                errors.append(UploadError(row_number=row_num, field="subject_name", code="DUPLICATE_ROW", message=f"Duplicate attempt record for student {s_id}, subject '{subj}', attempt {attempt_num}"))
                continue
            seen_keys.add(key)

            valid_objects.append(AttemptRecord(
                student_id=s_id,
                subject_name=subj,
                semester=sem,
                attempt_number=attempt_num,
                status=enum_status,
            ))

        inserted = 0
        if valid_objects:
            try:
                self.db.add_all(valid_objects)
                self.db.commit()
                inserted = len(valid_objects)
            except Exception as e:
                self.db.rollback()
                errors.append(UploadError(code="DB_ERROR", message=f"Database insertion failed: {str(e)}"))

        return UploadSummary(
            data_type="attempts",
            filename=filename,
            total_rows=len(df),
            valid_rows=len(valid_objects),
            invalid_rows=len(df) - len(valid_objects),
            inserted_rows=inserted,
            errors=errors[:100],
        )
