"""
Synthetic Data Generator for Pathwise (Backend Package)

Generates realistic, temporal student trajectory datasets for retention intelligence.
This dataset is strictly synthetic and generated for demonstration/development purposes.
"""

import os
import json
import argparse
from datetime import datetime, timezone
import numpy as np
import pandas as pd

TRAJECTORY_DISTRIBUTION = {
    "STABLE": 0.35,
    "IMPROVING": 0.15,
    "GRADUALLY_DETERIORATING": 0.20,
    "RAPIDLY_DETERIORATING": 0.12,
    "ACADEMIC_DISTRESS_ONLY": 0.10,
    "FINANCIAL_CONTEXT_ONLY": 0.08,
}

DEPARTMENTS = ["CSE", "ECE", "ME", "CE", "EEE"]

SUBJECTS_POOL = [
    "Mathematics",
    "Programming",
    "Data Structures",
    "Electronics",
    "Communication Skills",
    "Engineering Fundamentals",
]

EXAM_TYPES = [
    {"name": "TEST1", "max_marks": 20.0, "weight_in_term": 0.15},
    {"name": "TEST2", "max_marks": 20.0, "weight_in_term": 0.15},
    {"name": "MIDTERM", "max_marks": 50.0, "weight_in_term": 0.30},
    {"name": "FINAL", "max_marks": 100.0, "weight_in_term": 0.40},
]

MONTHS = ["August", "September", "October", "November"]


class SyntheticDataGenerator:
    """Generates synthetic student cohorts with temporal trajectories."""

    def __init__(self, num_students: int = 500, seed: int = 42, output_dir: str = "data/raw/synthetic"):
        self.num_students = num_students
        self.seed = seed
        self.output_dir = output_dir
        self.rng = np.random.default_rng(seed)

        self.students_df = None
        self.attendance_df = None
        self.marks_df = None
        self.fees_df = None
        self.attempts_df = None
        self.metadata = None

    def generate(self):
        """Generates all related tables for the cohort."""
        self._generate_students_roster()
        self._generate_attendance()
        self._generate_marks()
        self._generate_fees()
        self._generate_attempts()
        self._generate_metadata()
        return self

    def _generate_students_roster(self):
        """Generates student roster with trajectory assignments and synthetic labels."""
        trajectories = list(TRAJECTORY_DISTRIBUTION.keys())
        probabilities = list(TRAJECTORY_DISTRIBUTION.values())

        assigned_trajectories = self.rng.choice(
            trajectories, size=self.num_students, p=probabilities
        )

        students_list = []
        for i in range(1, self.num_students + 1):
            student_id = i
            dept = self.rng.choice(DEPARTMENTS)
            roll_number = f"{dept}2026{i:04d}"
            semester = int(self.rng.integers(1, 9))
            enrollment_year = 2026 - ((semester + 1) // 2)
            mentor_id = int(self.rng.integers(1, 16))
            trajectory = assigned_trajectories[i - 1]

            # Synthetic Dropout Label Policy:
            label_probs = {
                "RAPIDLY_DETERIORATING": 0.85,
                "GRADUALLY_DETERIORATING": 0.55,
                "ACADEMIC_DISTRESS_ONLY": 0.60,
                "IMPROVING": 0.05,
                "STABLE": 0.03,
                "FINANCIAL_CONTEXT_ONLY": 0.04,
            }
            p_dropout = label_probs.get(trajectory, 0.1)
            dropout_label = int(self.rng.random() < p_dropout)

            students_list.append({
                "student_id": student_id,
                "roll_number": roll_number,
                "name": f"Student {i:04d}",
                "department": dept,
                "semester": semester,
                "enrollment_year": enrollment_year,
                "guardian_name": f"Guardian {i:04d}",
                "guardian_phone": f"+91900000{i:04d}",
                "guardian_email": f"guardian{i:04d}@example.test",
                "mentor_id": mentor_id,
                "trajectory_type": trajectory,
                "dropout_label": dropout_label,
            })

        self.students_df = pd.DataFrame(students_list)

    def _generate_attendance(self):
        """Generates 14 weekly attendance records per student following assigned trajectory."""
        records = []
        weeks_count = 14

        for _, student in self.students_df.iterrows():
            s_id = student["student_id"]
            traj = student["trajectory_type"]

            if traj == "STABLE":
                base_pct = self.rng.uniform(84.0, 94.0)
                slope = self.rng.uniform(-0.15, 0.15)
            elif traj == "IMPROVING":
                base_pct = self.rng.uniform(58.0, 68.0)
                slope = self.rng.uniform(1.4, 2.2)
            elif traj == "GRADUALLY_DETERIORATING":
                base_pct = self.rng.uniform(80.0, 88.0)
                slope = self.rng.uniform(-2.2, -1.4)
            elif traj == "RAPIDLY_DETERIORATING":
                base_pct = self.rng.uniform(82.0, 90.0)
                slope = self.rng.uniform(-3.8, -2.6)
            elif traj == "ACADEMIC_DISTRESS_ONLY":
                base_pct = self.rng.uniform(82.0, 92.0)
                slope = self.rng.uniform(-0.2, 0.2)
            elif traj == "FINANCIAL_CONTEXT_ONLY":
                base_pct = self.rng.uniform(82.0, 92.0)
                slope = self.rng.uniform(-0.2, 0.2)
            else:
                base_pct = 75.0
                slope = 0.0

            for week in range(1, weeks_count + 1):
                month = MONTHS[min((week - 1) // 4, len(MONTHS) - 1)]
                total_classes = int(self.rng.integers(18, 26))

                noise = self.rng.normal(0, 2.0)
                expected_pct = np.clip(base_pct + (week - 1) * slope + noise, 0.0, 100.0)

                attended = int(np.round(total_classes * (expected_pct / 100.0)))
                attended = max(0, min(attended, total_classes))
                actual_pct = round((attended / total_classes) * 100.0, 2)

                records.append({
                    "student_id": s_id,
                    "week_number": week,
                    "month": month,
                    "total_classes": total_classes,
                    "attended_classes": attended,
                    "percentage": actual_pct,
                })

        self.attendance_df = pd.DataFrame(records)

    def _generate_marks(self):
        """Generates assessment marks across multiple subjects for each student."""
        records = []
        for _, student in self.students_df.iterrows():
            s_id = student["student_id"]
            traj = student["trajectory_type"]

            chosen_subjects = list(self.rng.choice(SUBJECTS_POOL, size=4, replace=False))

            for subject in chosen_subjects:
                if traj == "STABLE":
                    base_score_ratio = self.rng.uniform(0.68, 0.88)
                    slope = self.rng.uniform(-0.01, 0.01)
                elif traj == "IMPROVING":
                    base_score_ratio = self.rng.uniform(0.42, 0.55)
                    slope = self.rng.uniform(0.08, 0.12)
                elif traj == "GRADUALLY_DETERIORATING":
                    base_score_ratio = self.rng.uniform(0.68, 0.78)
                    slope = self.rng.uniform(-0.09, -0.05)
                elif traj == "RAPIDLY_DETERIORATING":
                    base_score_ratio = self.rng.uniform(0.62, 0.74)
                    slope = self.rng.uniform(-0.16, -0.10)
                elif traj == "ACADEMIC_DISTRESS_ONLY":
                    base_score_ratio = self.rng.uniform(0.58, 0.68)
                    slope = self.rng.uniform(-0.14, -0.08)
                elif traj == "FINANCIAL_CONTEXT_ONLY":
                    base_score_ratio = self.rng.uniform(0.65, 0.85)
                    slope = self.rng.uniform(-0.01, 0.01)
                else:
                    base_score_ratio = 0.60
                    slope = 0.0

                for step_idx, exam in enumerate(EXAM_TYPES):
                    max_marks = exam["max_marks"]
                    noise = self.rng.normal(0, 0.03)
                    ratio = np.clip(base_score_ratio + step_idx * slope + noise, 0.0, 1.0)
                    obtained = round(float(np.clip(ratio * max_marks, 0.0, max_marks)), 1)

                    records.append({
                        "student_id": s_id,
                        "subject_name": subject,
                        "exam_type": exam["name"],
                        "max_marks": max_marks,
                        "obtained_marks": obtained,
                        "attempt_number": 1,
                    })

        self.marks_df = pd.DataFrame(records)

    def _generate_fees(self):
        """Generates fee records with contextual payment status."""
        records = []
        for _, student in self.students_df.iterrows():
            s_id = student["student_id"]
            traj = student["trajectory_type"]
            current_sem = student["semester"]

            semesters_to_record = [current_sem]
            if current_sem > 1:
                semesters_to_record.insert(0, current_sem - 1)

            for sem in semesters_to_record:
                total_fee = 25000.0

                if traj == "FINANCIAL_CONTEXT_ONLY":
                    status = self.rng.choice(["PARTIAL", "PENDING", "PAID"], p=[0.55, 0.30, 0.15])
                elif traj in ["RAPIDLY_DETERIORATING", "GRADUALLY_DETERIORATING"]:
                    status = self.rng.choice(["PAID", "PARTIAL", "PENDING"], p=[0.75, 0.18, 0.07])
                else:
                    status = self.rng.choice(["PAID", "PARTIAL", "PENDING"], p=[0.92, 0.06, 0.02])

                if status == "PAID":
                    paid_amount = total_fee
                elif status == "PARTIAL":
                    paid_amount = round(float(self.rng.uniform(5000.0, 18000.0)), 2)
                else:
                    paid_amount = 0.0

                records.append({
                    "student_id": s_id,
                    "semester": sem,
                    "total_fee": total_fee,
                    "paid_amount": paid_amount,
                    "due_date": "2026-09-30",
                    "status": status,
                })

        self.fees_df = pd.DataFrame(records)

    def _generate_attempts(self):
        """Generates attempt and backlog history records."""
        records = []
        for _, student in self.students_df.iterrows():
            s_id = student["student_id"]
            traj = student["trajectory_type"]
            sem = student["semester"]

            if traj == "STABLE":
                if self.rng.random() < 0.08:
                    records.append({
                        "student_id": s_id,
                        "subject_name": "Mathematics",
                        "semester": max(1, sem - 1),
                        "attempt_number": 2,
                        "status": "CLEARED",
                    })
            elif traj == "IMPROVING":
                num_backlogs = int(self.rng.integers(1, 3))
                for b_idx in range(num_backlogs):
                    subj = SUBJECTS_POOL[b_idx % len(SUBJECTS_POOL)]
                    status = "CLEARED" if self.rng.random() < 0.75 else "ACTIVE"
                    records.append({
                        "student_id": s_id,
                        "subject_name": subj,
                        "semester": max(1, sem - 1),
                        "attempt_number": int(self.rng.integers(2, 4)),
                        "status": status,
                    })
            elif traj == "GRADUALLY_DETERIORATING":
                num_backlogs = int(self.rng.integers(1, 3))
                for b_idx in range(num_backlogs):
                    subj = SUBJECTS_POOL[b_idx % len(SUBJECTS_POOL)]
                    records.append({
                        "student_id": s_id,
                        "subject_name": subj,
                        "semester": max(1, sem - 1),
                        "attempt_number": int(self.rng.integers(1, 3)),
                        "status": "ACTIVE",
                    })
            elif traj == "RAPIDLY_DETERIORATING":
                num_backlogs = int(self.rng.integers(2, 5))
                for b_idx in range(num_backlogs):
                    subj = SUBJECTS_POOL[b_idx % len(SUBJECTS_POOL)]
                    records.append({
                        "student_id": s_id,
                        "subject_name": subj,
                        "semester": max(1, sem - 1),
                        "attempt_number": int(self.rng.integers(2, 4)),
                        "status": "ACTIVE",
                    })
            elif traj == "ACADEMIC_DISTRESS_ONLY":
                num_backlogs = int(self.rng.integers(2, 4))
                for b_idx in range(num_backlogs):
                    subj = SUBJECTS_POOL[b_idx % len(SUBJECTS_POOL)]
                    records.append({
                        "student_id": s_id,
                        "subject_name": subj,
                        "semester": max(1, sem - 1),
                        "attempt_number": int(self.rng.integers(1, 3)),
                        "status": "ACTIVE",
                    })
            elif traj == "FINANCIAL_CONTEXT_ONLY":
                if self.rng.random() < 0.05:
                    records.append({
                        "student_id": s_id,
                        "subject_name": "Mathematics",
                        "semester": max(1, sem - 1),
                        "attempt_number": 2,
                        "status": "CLEARED",
                    })

        self.attempts_df = pd.DataFrame(records)

    def _generate_metadata(self):
        """Compiles metadata describing the generated cohort."""
        traj_counts = self.students_df["trajectory_type"].value_counts().to_dict()
        dropout_counts = self.students_df["dropout_label"].value_counts().to_dict()

        self.metadata = {
            "version": "1.0.0",
            "generator": "Pathwise SyntheticDataGenerator",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "num_students": self.num_students,
            "seed": self.seed,
            "trajectory_distribution": traj_counts,
            "dropout_label_distribution": dropout_counts,
            "row_counts": {
                "students_roster": len(self.students_df),
                "attendance": len(self.attendance_df),
                "marks": len(self.marks_df),
                "fees": len(self.fees_df),
                "attempts": len(self.attempts_df),
            },
            "warning": (
                "This dataset is entirely synthetic and generated for Pathwise "
                "development/demo purposes. It must not be interpreted as evidence of "
                "real-world student dropout behaviour. trajectory_type is ground truth "
                "metadata and must NOT be used as an ML training input feature."
            ),
        }

    def save(self):
        """Saves all generated datasets and metadata to the output directory."""
        os.makedirs(self.output_dir, exist_ok=True)

        roster_path = os.path.join(self.output_dir, "students_roster.csv")
        att_path = os.path.join(self.output_dir, "attendance.csv")
        marks_path = os.path.join(self.output_dir, "marks.csv")
        fees_path = os.path.join(self.output_dir, "fees.csv")
        attempts_path = os.path.join(self.output_dir, "attempts.csv")
        meta_path = os.path.join(self.output_dir, "metadata.json")

        self.students_df.to_csv(roster_path, index=False)
        self.attendance_df.to_csv(att_path, index=False)
        self.marks_df.to_csv(marks_path, index=False)
        self.fees_df.to_csv(fees_path, index=False)
        self.attempts_df.to_csv(attempts_path, index=False)

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2)

        print(f"Generated synthetic dataset saved to: {self.output_dir}")
        print(f"- Students: {len(self.students_df)}")
        print(f"- Attendance rows: {len(self.attendance_df)}")
        print(f"- Marks rows: {len(self.marks_df)}")
        print(f"- Fee rows: {len(self.fees_df)}")
        print(f"- Attempt rows: {len(self.attempts_df)}")


def main():
    parser = argparse.ArgumentParser(description="Pathwise Synthetic Dataset Generator")
    parser.add_argument("--students", type=int, default=500, help="Number of students to generate (default: 500)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output-dir", type=str, default="data/raw/synthetic", help="Output directory path")

    args = parser.parse_args()
    generator = SyntheticDataGenerator(
        num_students=args.students,
        seed=args.seed,
        output_dir=args.output_dir,
    )
    generator.generate().save()


if __name__ == "__main__":
    main()
