import re
from typing import Dict, List, Tuple, Optional

# Canonical schema definitions and common institutional aliases
CANONICAL_SCHEMAS = {
    "students": {
        "required": ["student_id", "roll_number", "name", "department", "semester"],
        "optional": ["guardian_name", "guardian_phone", "guardian_email", "mentor_id", "enrollment_year"],
        "aliases": {
            "student_id": ["student_id", "student id", "studentid", "id", "std_id", "uid"],
            "roll_number": ["roll_number", "roll no", "roll_no", "rollnumber", "roll", "reg_no", "registration_no", "usn"],
            "name": ["name", "student_name", "student name", "full_name", "fullname"],
            "department": ["department", "dept", "branch", "stream", "program"],
            "semester": ["semester", "sem", "current_semester", "term"],
            "guardian_name": ["guardian_name", "guardian name", "parent_name", "parent name", "father_name"],
            "guardian_phone": ["guardian_phone", "guardian phone", "parent_phone", "parent phone", "contact_phone", "phone"],
            "guardian_email": ["guardian_email", "guardian email", "parent_email", "parent email", "email"],
            "mentor_id": ["mentor_id", "mentor id", "faculty_mentor_id", "advisor_id"],
            "enrollment_year": ["enrollment_year", "enrollment year", "admission_year", "batch", "year_of_joining"],
        }
    },
    "attendance": {
        "required": ["student_id", "week_number", "total_classes", "attended_classes"],
        "optional": ["month", "percentage"],
        "aliases": {
            "student_id": ["student_id", "student id", "studentid", "id", "roll_no", "roll_number", "roll"],
            "week_number": ["week_number", "week number", "week", "wk", "week_no"],
            "month": ["month", "mon", "month_name"],
            "total_classes": ["total_classes", "total classes", "total", "conducted", "held_classes", "total_sessions"],
            "attended_classes": ["attended_classes", "attended classes", "attended", "present", "present_classes", "classes_attended"],
            "percentage": ["percentage", "percent", "pct", "att_pct", "attendance_percentage", "attendance_percent"],
        }
    },
    "marks": {
        "required": ["student_id", "subject_name", "exam_type", "max_marks", "obtained_marks"],
        "optional": ["attempt_number"],
        "aliases": {
            "student_id": ["student_id", "student id", "studentid", "id", "roll_no", "roll_number", "roll"],
            "subject_name": ["subject_name", "subject name", "subject", "course", "course_name", "sub_name"],
            "exam_type": ["exam_type", "exam type", "exam", "assessment_type", "test_type", "assessment"],
            "max_marks": ["max_marks", "max marks", "maximum_marks", "total_marks", "out_of"],
            "obtained_marks": ["obtained_marks", "obtained marks", "marks", "score", "marks_obtained", "scored"],
            "attempt_number": ["attempt_number", "attempt number", "attempt", "attempt_no", "try_count"],
        }
    },
    "fees": {
        "required": ["student_id", "semester", "total_fee", "paid_amount", "due_date", "status"],
        "optional": [],
        "aliases": {
            "student_id": ["student_id", "student id", "studentid", "id", "roll_no", "roll_number", "roll"],
            "semester": ["semester", "sem", "term", "academic_semester"],
            "total_fee": ["total_fee", "total fee", "fee_amount", "tuition_fee", "payable_fee", "fee"],
            "paid_amount": ["paid_amount", "paid amount", "amount_paid", "paid", "received_amount"],
            "due_date": ["due_date", "due date", "deadline", "payment_due_date"],
            "status": ["status", "fee_status", "payment_status", "paid_status"],
        }
    },
    "attempts": {
        "required": ["student_id", "subject_name", "semester", "attempt_number", "status"],
        "optional": [],
        "aliases": {
            "student_id": ["student_id", "student id", "studentid", "id", "roll_no", "roll_number", "roll"],
            "subject_name": ["subject_name", "subject name", "subject", "course", "backlog_subject"],
            "semester": ["semester", "sem", "term", "backlog_semester"],
            "attempt_number": ["attempt_number", "attempt number", "attempt", "attempt_no", "attempts"],
            "status": ["status", "backlog_status", "cleared_status", "result"],
        }
    }
}

def normalize_header(header: str) -> str:
    """Normalizes header string by stripping, lowercasing, and replacing spaces/punctuations with underscores."""
    if not isinstance(header, str):
        return str(header)
    cleaned = header.strip().lower()
    cleaned = re.sub(r'[\s\-_.]+', '_', cleaned)
    return cleaned

def map_columns(data_type: str, columns: List[str]) -> Tuple[Dict[str, str], List[str], Optional[str]]:
    """
    Maps incoming file column headers to canonical field names.
    
    Returns:
        (mapped_dict, missing_required_fields, error_message)
        mapped_dict: {original_col_name: canonical_field_name}
    """
    if data_type not in CANONICAL_SCHEMAS:
        return {}, [], f"Unsupported data type '{data_type}'"

    schema = CANONICAL_SCHEMAS[data_type]
    aliases = schema["aliases"]
    required_fields = schema["required"]

    normalized_cols = {col: normalize_header(col) for col in columns}
    
    canonical_to_original: Dict[str, List[str]] = {field: [] for field in aliases}

    for original_col, norm_col in normalized_cols.items():
        for canonical_field, alias_list in aliases.items():
            norm_aliases = [normalize_header(a) for a in alias_list]
            if norm_col in norm_aliases or norm_col == canonical_field:
                canonical_to_original[canonical_field].append(original_col)

    # Check for ambiguity: multiple original columns mapping to the same canonical field
    for canonical_field, matched_cols in canonical_to_original.items():
        if len(matched_cols) > 1:
            return {}, [], f"Ambiguous column mapping: multiple columns {matched_cols} map to canonical field '{canonical_field}'"

    # Invert mapping: {original_col: canonical_field}
    mapped_dict = {}
    for canonical_field, matched_cols in canonical_to_original.items():
        if len(matched_cols) == 1:
            mapped_dict[matched_cols[0]] = canonical_field

    # Check for missing required fields
    mapped_canonicals = set(mapped_dict.values())
    missing_required = [req for req in required_fields if req not in mapped_canonicals]

    return mapped_dict, missing_required, None
