import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.user import User
from app.models.student import Student
from app.models.mentor import Mentor
from app.models.attendance import AttendanceRecord
from app.models.marks import MarksRecord
from app.models.fee import FeeRecord
from app.models.attempt import AttemptRecord
from app.models.risk import RiskSnapshot
from app.scripts.seed_demo_data import seed_academic_cohort, seed_demo_staff_accounts


def test_seed_demo_data_idempotency():
    """Verify that seed_demo_data can be run multiple times safely with strict foreign keys enabled."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Enable SQLite foreign key constraints to mirror PostgreSQL strict FK behavior
    @event.listens_for(test_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestingSessionLocal()

    try:
        # First execution
        count1 = seed_academic_cohort(db)
        assert count1 == 500
        assert db.query(Student).count() == 500
        assert db.query(Mentor).count() == 15
        assert db.query(AttendanceRecord).count() == 7000
        assert db.query(MarksRecord).count() == 8000
        assert db.query(FeeRecord).count() >= 500
        assert db.query(AttemptRecord).count() >= 50
        assert db.query(RiskSnapshot).count() == 500

        # Create demo staff
        seed_demo_staff_accounts(db, "SecureDemoPassword123")
        user_count1 = db.query(User).count()
        assert user_count1 == 2  # mentor_hopper and counsellor_sharma

        # Second execution (Idempotency test)
        count2 = seed_academic_cohort(db)
        assert count2 == 500
        assert db.query(Student).count() == 500
        assert db.query(Mentor).count() == 15
        assert db.query(AttendanceRecord).count() == 7000
        assert db.query(MarksRecord).count() == 8000
        assert db.query(RiskSnapshot).count() == 500

        seed_demo_staff_accounts(db, "SecureDemoPassword123")
        user_count2 = db.query(User).count()
        assert user_count2 == 2

        # Verify no data corruption or duplicate primary keys
        students = db.query(Student).all()
        student_ids = [s.id for s in students]
        assert len(student_ids) == len(set(student_ids)) == 500

    finally:
        db.close()
        Base.metadata.drop_all(bind=test_engine)
