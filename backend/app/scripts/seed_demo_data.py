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
from app.models.risk import RiskSnapshot
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

DEFAULT_MENTORS = [
    {"id": 1, "name": "Dr. Grace Hopper", "email": "hopper@institute.edu", "department": "CSE", "phone": "+919876543201"},
    {"id": 2, "name": "Dr. Alan Turing", "email": "turing@institute.edu", "department": "CSE", "phone": "+919876543202"},
    {"id": 3, "name": "Dr. Ada Lovelace", "email": "lovelace@institute.edu", "department": "CSE", "phone": "+919876543203"},
    {"id": 4, "name": "Dr. Claude Shannon", "email": "shannon@institute.edu", "department": "ECE", "phone": "+919876543204"},
    {"id": 5, "name": "Dr. Heinrich Hertz", "email": "hertz@institute.edu", "department": "ECE", "phone": "+919876543205"},
    {"id": 6, "name": "Dr. Nikola Tesla", "email": "tesla@institute.edu", "department": "ECE", "phone": "+919876543206"},
    {"id": 7, "name": "Dr. James Watt", "email": "watt@institute.edu", "department": "ME", "phone": "+919876543207"},
    {"id": 8, "name": "Dr. Rudolf Diesel", "email": "diesel@institute.edu", "department": "ME", "phone": "+919876543208"},
    {"id": 9, "name": "Dr. Sadi Carnot", "email": "carnot@institute.edu", "department": "ME", "phone": "+919876543209"},
    {"id": 10, "name": "Dr. Thomas Telford", "email": "telford@institute.edu", "department": "CE", "phone": "+919876543210"},
    {"id": 11, "name": "Dr. Gustave Eiffel", "email": "eiffel@institute.edu", "department": "CE", "phone": "+919876543211"},
    {"id": 12, "name": "Dr. Isambard Brunel", "email": "brunel@institute.edu", "department": "CE", "phone": "+919876543212"},
    {"id": 13, "name": "Dr. Michael Faraday", "email": "faraday@institute.edu", "department": "EEE", "phone": "+919876543213"},
    {"id": 14, "name": "Dr. James Maxwell", "email": "maxwell@institute.edu", "department": "EEE", "phone": "+919876543214"},
    {"id": 15, "name": "Dr. George Westinghouse", "email": "westinghouse@institute.edu", "department": "EEE", "phone": "+919876543215"},
]


def seed_academic_cohort(db) -> int:
    """
    Seeds database with 15 department faculty mentors, 500 synthetic students,
    and baseline risk snapshots if empty.
    Idempotent: skips if students already exist.
    """
    # Ensure default faculty mentor records exist for all potential mentor IDs (1-15)
    for m_data in DEFAULT_MENTORS:
        mentor = db.query(Mentor).filter((Mentor.id == m_data["id"]) | (Mentor.email == m_data["email"])).first()
        if not mentor:
            mentor = Mentor(
                id=m_data["id"],
                name=m_data["name"],
                email=m_data["email"],
                department=m_data["department"],
                phone=m_data.get("phone"),
            )
            db.add(mentor)
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
                content = f.read()
            summary = ingestion.ingest(dtype, filename, content)
            if summary.errors or summary.inserted_rows == 0:
                err_msgs = "; ".join([e.message for e in summary.errors])
                raise RuntimeError(
                    f"Ingestion failed for '{filename}' ({dtype}): "
                    f"inserted {summary.inserted_rows}/{summary.total_rows} rows. Errors: {err_msgs}"
                )
            print(f"  [+] Ingested {summary.inserted_rows} rows from {filename}")

    # Verify student count before proceeding to risk computation
    student_count = db.query(Student).count()
    if student_count != 500:
        raise RuntimeError(
            f"Academic cohort ingestion verification failed: expected 500 students, found {student_count}."
        )

    print("[+] Computing initial baseline RiskSnapshots for cohort...")
    predictor = None
    try:
        predictor = MLPredictor()
        print("[+] Trained ML model artifact loaded for cohort risk inference.")
    except FileNotFoundError as e:
        print(f"[i] Trained ML model artifact not found in container environment ({e}).")
        print("[i] Using deterministic baseline risk probability derived from rule evaluation for demo seeding.")

    for student in db.query(Student).all():
        profile = StudentDataFusionService(db).fuse_by_id(student.id)
        if profile:
            features = FeatureEngineeringService.extract_features(profile)
            rule_res = RuleEngine.evaluate(features)

            if predictor is not None:
                ml_prob = predictor.predict_dropout_probability(features)
            else:
                # Deterministic demo fallback derived safely from normalized rule evaluation
                raw_prob = rule_res.rule_score / 100.0
                ml_prob = round(float(min(1.0, max(0.0, raw_prob))), 4)

            fusion_res = RiskFusionEngine.fuse(student.id, rule_res.rule_score, ml_prob, features)
            snapshot = RiskFusionEngine.to_risk_snapshot(fusion_res)
            db.add(snapshot)
    db.commit()

    final_student_count = db.query(Student).count()
    final_snapshot_count = db.query(RiskSnapshot).count()
    if final_student_count != 500:
        raise RuntimeError(f"Academic dataset verification failed: expected 500 students, found {final_student_count}.")
    if final_snapshot_count != 500:
        raise RuntimeError(f"Risk snapshots verification failed: expected 500 snapshots, found {final_snapshot_count}.")

    return final_student_count


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
        if count != 500:
            raise RuntimeError(f"Seeding verification failed: student count is {count}, expected 500.")
        print(f"\n[+] Academic dataset verified ({count} student records present).")

        if args.staff_password:
            print("\n[+] Initializing demo staff accounts with provided credentials...")
            seed_demo_staff_accounts(db, args.staff_password)

        print("\n" + "=" * 60)
        print("  SEEDING COMPLETE — Database Ready")
        print("=" * 60)
        print("  Note: Administrator accounts must be created using:")
        print("    python -m app.scripts.create_admin\n")
    except Exception as e:
        print(f"\n[!] FATAL ERROR: Academic cohort seeding failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
