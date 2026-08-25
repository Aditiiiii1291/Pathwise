import sys
import os
import argparse
import tempfile
from pathlib import Path
from typing import Optional

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, init_db
from app.models.user import User, UserRoleEnum
from app.models.student import Student
from app.models.mentor import Mentor
from app.services.ingestion import IngestionService
from app.services.fusion import StudentDataFusionService
from app.services.features import FeatureEngineeringService
from app.services.rules import RuleEngine
from app.services.ml_predictor import MLPredictor
from app.services.fusion_engine import RiskFusionEngine
from app.services.auth import AuthService
from app.schemas.auth import UserCreate

try:
    from app.data_generation.generator import SyntheticDataGenerator
except ImportError:
    try:
        from ml.data_generation.generator import SyntheticDataGenerator
    except ImportError:
        SyntheticDataGenerator = None


def seed_academic_cohort(db) -> int:
    """
    Seeds database with 500 synthetic students and baseline risk snapshots if empty.
    Idempotent: skips if students already exist.
    """
    # Ensure default faculty mentor record exists
    mentor_1 = db.query(Mentor).filter(Mentor.id == 1).first()
    if not mentor_1:
        mentor_1 = Mentor(
            id=1,
            name="Dr. Grace Hopper",
            email="hopper@institute.edu",
            department="CSE",
        )
        db.add(mentor_1)
        db.commit()

    student_count = db.query(Student).count()
    if student_count > 0:
        return student_count

    if SyntheticDataGenerator is None:
        raise RuntimeError("SyntheticDataGenerator module not available.")

    print("\n[+] Generating synthetic 500-student cohort dataset...")
    with tempfile.TemporaryDirectory() as temp_dir:
        gen = SyntheticDataGenerator(num_students=500, seed=42, output_dir=temp_dir)
        gen.generate().save()

        ingestion = IngestionService(db)
        for dtype, filename in [
            ("students", "students_roster.csv"),
            ("attendance", "attendance.csv"),
            ("marks", "marks.csv"),
            ("fees", "fees.csv"),
            ("attempts", "attempts.csv"),
        ]:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, "rb") as f:
                ingestion.ingest(dtype, filename, f.read())

    print("[+] Computing initial baseline RiskSnapshots for cohort...")
    predictor = MLPredictor()
    for student in db.query(Student).all():
        profile = StudentDataFusionService(db).fuse_by_id(student.id)
        if profile:
            features = FeatureEngineeringService.extract_features(profile)
            rule_res = RuleEngine.evaluate(features)
            ml_prob = predictor.predict_dropout_probability(features)
            fusion_res = RiskFusionEngine.fuse(student.id, rule_res.rule_score, ml_prob, features)
            snapshot = RiskFusionEngine.to_risk_snapshot(fusion_res)
            db.add(snapshot)
    db.commit()
    return db.query(Student).count()


def seed_demo_staff_accounts(db, demo_password: str):
    """
    Optional helper to seed demo faculty/counsellor accounts only when an explicit password is provided.
    Does not reset existing accounts or passwords.
    """
    if not demo_password:
        return

    demo_accounts = [
        {
            "username": "mentor_hopper",
            "password": demo_password,
            "display_name": "Dr. Grace Hopper",
            "role": UserRoleEnum.MENTOR.value,
            "mentor_id": 1,
        },
        {
            "username": "counsellor_sharma",
            "password": demo_password,
            "display_name": "Dr. Priya Sharma",
            "role": UserRoleEnum.COUNSELLOR.value,
            "mentor_id": None,
        },
    ]

    for acc in demo_accounts:
        existing = db.query(User).filter(User.username == acc["username"]).first()
        if not existing:
            AuthService.create_user(db, UserCreate(**acc))
            print(f"  [+] Created demo staff account: {acc['username']} ({acc['role']})")


def main():
    parser = argparse.ArgumentParser(description="Pathwise Synthetic Academic Cohort Seeder")
    parser.add_argument(
        "--staff-password",
        help="Optional password for demo mentor/counsellor accounts (if desired for demo testing)",
        default=os.getenv("DEMO_STAFF_PASSWORD"),
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  PATHWISE — Academic Cohort & Demo Seeding Script")
    print("=" * 60)

    init_db()
    db = SessionLocal()
    try:
        count = seed_academic_cohort(db)
        print(f"\n[+] Academic dataset verified ({count} student records present).")

        if args.staff_password:
            print("\n[+] Initializing demo staff accounts with provided credentials...")
            seed_demo_staff_accounts(db, args.staff_password)

        print("\n" + "=" * 60)
        print("  SEEDING COMPLETE — Database Ready")
        print("=" * 60)
        print("  Note: Administrator accounts must be created using:")
        print("    python -m app.scripts.create_admin\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
