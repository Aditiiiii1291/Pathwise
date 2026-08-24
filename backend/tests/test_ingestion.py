import io
import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

try:
    from app.core.database import Base, get_db
    from app.models import Student, AttendanceRecord, MarksRecord, FeeRecord, AttemptRecord
    from app.services.ingestion import IngestionService
    from app.services.column_mapper import map_columns
    from app.main import app
except ImportError:
    from backend.app.core.database import Base, get_db
    from backend.app.models import Student, AttendanceRecord, MarksRecord, FeeRecord, AttemptRecord
    from backend.app.services.ingestion import IngestionService
    from backend.app.services.column_mapper import map_columns
    from backend.app.main import app

from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="function")
def db_session():
    """Isolated in-memory SQLite database session."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

@pytest.fixture(scope="function")
def client(db_session):
    """TestClient with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Dynamically override all route database dependencies
    for route in app.routes:
        if hasattr(route, "dependant"):
            for dep in route.dependant.dependencies:
                app.dependency_overrides[dep.call] = override_get_db

    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

def test_column_mapper_aliases():
    """Verify common institutional aliases map correctly."""
    cols = ["Student ID", "Roll No", "Student Name", "Branch", "Sem", "Parent Phone"]
    mapping, missing, err = map_columns("students", cols)
    assert err is None
    assert missing == []
    assert mapping["Student ID"] == "student_id"
    assert mapping["Roll No"] == "roll_number"
    assert mapping["Student Name"] == "name"
    assert mapping["Branch"] == "department"
    assert mapping["Sem"] == "semester"
    assert mapping["Parent Phone"] == "guardian_phone"

def test_column_mapper_ambiguity():
    """Verify ambiguous headers produce error."""
    cols = ["student_id", "id", "name", "roll_number", "department", "semester"]
    mapping, missing, err = map_columns("students", cols)
    assert err is not None
    assert "Ambiguous column mapping" in err

def test_column_mapper_missing_required():
    """Verify missing required columns are flagged."""
    cols = ["student_id", "name"]
    mapping, missing, err = map_columns("students", cols)
    assert err is None
    assert "roll_number" in missing
    assert "department" in missing

def test_ingest_valid_student_roster_csv(db_session):
    """Verify ingestion of valid student roster CSV."""
    csv_data = (
        "student_id,roll_number,name,department,semester,guardian_name,guardian_phone\n"
        "101,CS2026101,Ada Lovelace,CSE,4,Lord Byron,+919000000001\n"
        "102,EC2026102,Alan Turing,ECE,4,Julius Turing,+919000000002\n"
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("students", "students.csv", csv_data)

    assert summary.total_rows == 2
    assert summary.valid_rows == 2
    assert summary.inserted_rows == 2
    assert len(summary.errors) == 0

    assert db_session.query(Student).count() == 2
    s1 = db_session.query(Student).filter_by(id=101).first()
    assert s1.name == "Ada Lovelace"
    assert s1.roll_number == "CS2026101"

def test_ingest_xlsx_support(db_session):
    """Verify ingestion of Excel (.xlsx) files."""
    df = pd.DataFrame([
        {"student_id": 201, "roll_number": "ME2026201", "name": "James Watt", "department": "ME", "semester": 2},
        {"student_id": 202, "roll_number": "CE2026202", "name": "Thomas Telford", "department": "CE", "semester": 2},
    ])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, engine="openpyxl")
    xlsx_data = buffer.getvalue()

    service = IngestionService(db_session)
    summary = service.ingest("students", "students.xlsx", xlsx_data)

    assert summary.total_rows == 2
    assert summary.valid_rows == 2
    assert summary.inserted_rows == 2
    assert db_session.query(Student).count() == 2

def test_ingest_attendance_with_calculated_percentage(db_session):
    """Verify attendance ingestion and automatic percentage calculation."""
    db_session.add(Student(id=1, roll_number="CS001", name="Test Student", department="CSE", semester=4))
    db_session.commit()

    csv_data = (
        "student_id,week_number,month,total_classes,attended_classes\n"
        "1,1,August,20,16\n"
        "1,2,August,20,18\n"
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("attendance", "attendance.csv", csv_data)

    assert summary.total_rows == 2
    assert summary.valid_rows == 2
    assert summary.inserted_rows == 2
    assert db_session.query(AttendanceRecord).count() == 2

    r1 = db_session.query(AttendanceRecord).filter_by(student_id=1, week_number=1).first()
    assert r1.percentage == 80.0
    r2 = db_session.query(AttendanceRecord).filter_by(student_id=1, week_number=2).first()
    assert r2.percentage == 90.0

def test_ingest_marks_with_exam_type_mapping(db_session):
    """Verify marks ingestion and alias normalization for ExamTypeEnum."""
    db_session.add(Student(id=1, roll_number="CS001", name="Test Student", department="CSE", semester=4))
    db_session.commit()

    csv_data = (
        "student_id,subject_name,exam_type,max_marks,obtained_marks,attempt_number\n"
        "1,Mathematics,midterm,50.0,42.5,1\n"
        "1,Data Structures,Test 1,20.0,17.0,1\n"
        "1,Programming,endsem,100.0,85.0,1\n"
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("marks", "marks.csv", csv_data)

    assert summary.total_rows == 3
    assert summary.valid_rows == 3
    assert summary.inserted_rows == 3
    assert db_session.query(MarksRecord).count() == 3

def test_ingest_fees_with_status_mapping(db_session):
    """Verify fee ingestion and status normalization."""
    db_session.add(Student(id=1, roll_number="CS001", name="Test Student", department="CSE", semester=4))
    db_session.commit()

    csv_data = (
        "student_id,semester,total_fee,paid_amount,due_date,status\n"
        "1,3,25000,25000,2026-09-30,complete\n"
        "1,4,25000,10000,2026-09-30,partial\n"
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("fees", "fees.csv", csv_data)

    assert summary.total_rows == 2
    assert summary.valid_rows == 2
    assert summary.inserted_rows == 2
    assert db_session.query(FeeRecord).count() == 2

def test_ingest_attempts_with_status_mapping(db_session):
    """Verify attempts ingestion and status normalization."""
    db_session.add(Student(id=1, roll_number="CS001", name="Test Student", department="CSE", semester=4))
    db_session.commit()

    csv_data = (
        "student_id,subject_name,semester,attempt_number,status\n"
        "1,Mathematics,3,2,cleared\n"
        "1,Electronics,3,1,uncleared\n"
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("attempts", "attempts.csv", csv_data)

    assert summary.total_rows == 2
    assert summary.valid_rows == 2
    assert summary.inserted_rows == 2
    assert db_session.query(AttemptRecord).count() == 2

def test_attendance_bounds_validation(db_session):
    """Verify attended_classes > total_classes is rejected."""
    db_session.add(Student(id=1, roll_number="CS001", name="Test Student", department="CSE", semester=4))
    db_session.commit()

    csv_data = (
        "student_id,week_number,month,total_classes,attended_classes\n"
        "1,1,August,20,25\n"  # Invalid: 25 > 20
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("attendance", "attendance.csv", csv_data)

    assert summary.valid_rows == 0
    assert summary.invalid_rows == 1
    assert summary.errors[0].code == "VALUE_OUT_OF_RANGE"

def test_marks_bounds_validation(db_session):
    """Verify obtained_marks > max_marks is rejected."""
    db_session.add(Student(id=1, roll_number="CS001", name="Test Student", department="CSE", semester=4))
    db_session.commit()

    csv_data = (
        "student_id,subject_name,exam_type,max_marks,obtained_marks\n"
        "1,Mathematics,MIDTERM,50.0,55.0\n"  # Invalid: 55 > 50
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("marks", "marks.csv", csv_data)

    assert summary.valid_rows == 0
    assert summary.invalid_rows == 1
    assert summary.errors[0].code == "VALUE_OUT_OF_RANGE"

def test_fee_bounds_and_status_validation(db_session):
    """Verify paid_amount > total_fee and invalid status are rejected."""
    db_session.add(Student(id=1, roll_number="CS001", name="Test Student", department="CSE", semester=4))
    db_session.commit()

    csv_data = (
        "student_id,semester,total_fee,paid_amount,due_date,status\n"
        "1,3,25000,30000,2026-09-30,PAID\n"  # Invalid amount
        "1,4,25000,10000,2026-09-30,unknown_status\n"  # Invalid status
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("fees", "fees.csv", csv_data)

    assert summary.valid_rows == 0
    assert summary.invalid_rows == 2

def test_unknown_student_rejected(db_session):
    """Verify secondary records for non-existent students are rejected."""
    # Note: student 999 does NOT exist in DB
    csv_data = (
        "student_id,week_number,month,total_classes,attended_classes\n"
        "999,1,August,20,18\n"
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("attendance", "attendance.csv", csv_data)

    assert summary.valid_rows == 0
    assert summary.invalid_rows == 1
    assert summary.errors[0].code == "UNKNOWN_STUDENT"

def test_duplicate_row_detection(db_session):
    """Verify duplicate records within the file are flagged."""
    csv_data = (
        "student_id,roll_number,name,department,semester\n"
        "1,CS001,Student One,CSE,2\n"
        "1,CS002,Student Two,CSE,2\n"  # Duplicate student_id 1
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("students", "students.csv", csv_data)

    assert summary.valid_rows == 1
    assert summary.invalid_rows == 1
    assert summary.errors[0].code == "DUPLICATE_ROW"

def test_partial_success_mixed_rows(db_session):
    """Verify partial success: valid rows are inserted while invalid rows are rejected."""
    db_session.add(Student(id=1, roll_number="CS001", name="Test Student", department="CSE", semester=4))
    db_session.commit()

    csv_data = (
        "student_id,week_number,month,total_classes,attended_classes\n"
        "1,1,August,20,18\n"   # Valid
        "1,2,August,20,22\n"   # Invalid: attended > total
        "1,3,August,20,17\n"   # Valid
    ).encode("utf-8")

    service = IngestionService(db_session)
    summary = service.ingest("attendance", "attendance.csv", csv_data)

    assert summary.total_rows == 3
    assert summary.valid_rows == 2
    assert summary.invalid_rows == 1
    assert summary.inserted_rows == 2
    assert db_session.query(AttendanceRecord).count() == 2

def test_unsupported_file_type_rejection(db_session):
    """Verify unsupported file format (e.g. .pdf or .txt) is rejected."""
    service = IngestionService(db_session)
    summary = service.ingest("students", "students.pdf", b"%PDF-1.4...")
    assert summary.valid_rows == 0
    assert summary.errors[0].code == "PARSE_ERROR"
    assert "Unsupported file type" in summary.errors[0].message

def test_upload_api_endpoint(client, db_session):
    """Verify HTTP multipart upload endpoint POST /api/uploads/{data_type}."""
    csv_content = (
        "student_id,roll_number,name,department,semester\n"
        "301,ME301,Marie Curie,ME,3\n"
    )
    response = client.post(
        "/api/uploads/students",
        files={"file": ("roster.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["errors"] == [], f"Upload returned unexpected errors: {data.get('errors')}"
    assert data["data_type"] == "students"
    assert data["valid_rows"] == 1
    assert data["inserted_rows"] == 1
    assert db_session.query(Student).filter_by(id=301).count() == 1

def test_upload_empty_file_rejected(client):
    """Verify empty file upload returns HTTP 400."""
    response = client.post(
        "/api/uploads/students",
        files={"file": ("empty.csv", io.BytesIO(b""), "text/csv")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

def test_upload_oversized_file_rejected(client):
    """Verify oversized file (> 10MB) returns HTTP 413."""
    # 10.5 MB fake content
    oversized_data = b"a" * (10 * 1024 * 1024 + 512 * 1024)
    response = client.post(
        "/api/uploads/students",
        files={"file": ("large.csv", io.BytesIO(oversized_data), "text/csv")},
    )
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"].lower()
