import os
import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure root and backend are in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.core.database import Base
from app.services.ingestion import IngestionService
from app.services.fusion import StudentDataFusionService
from app.services.features import FeatureEngineeringService

ML_FEATURE_NAMES = [
    "attendance_current",
    "attendance_mean",
    "attendance_slope",
    "attendance_decline_pp",
    "attendance_recent_vs_historical",
    "attendance_consecutive_decline",
    "attendance_acceleration",
    "attendance_history_count",
    "has_sufficient_attendance_history",
    "marks_current_avg",
    "marks_mean",
    "marks_slope",
    "marks_decline_pp",
    "marks_recent_vs_previous",
    "marks_consecutive_failures",
    "marks_failed_subject_count",
    "marks_history_count",
    "has_sufficient_marks_history",
    "backlog_count_active",
    "backlog_count_total",
    "backlog_new_this_semester",
    "backlog_trend_numeric",
    "max_attempt_number",
    "fee_percentage_paid",
    "fee_terms_overdue",
    "fee_pending_count",
]

def load_training_dataset(data_dir: Path) -> Tuple[pd.DataFrame, pd.Series, Dict[int, str]]:
    """
    Ingests synthetic dataset through canonical Phase 4-5-6 pipeline.
    Returns:
        X: DataFrame of engineered features (strictly excluding leakage columns)
        y: Series of binary dropout labels
        trajectories: Dict mapping student_id -> trajectory_type (for post-evaluation analysis ONLY)
    """
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()

    try:
        ingestion = IngestionService(session)
        with open(data_dir / "students_roster.csv", "rb") as f:
            ingestion.ingest("students", "students_roster.csv", f.read())
        with open(data_dir / "attendance.csv", "rb") as f:
            ingestion.ingest("attendance", "attendance.csv", f.read())
        with open(data_dir / "marks.csv", "rb") as f:
            ingestion.ingest("marks", "marks.csv", f.read())
        with open(data_dir / "fees.csv", "rb") as f:
            ingestion.ingest("fees", "fees.csv", f.read())
        with open(data_dir / "attempts.csv", "rb") as f:
            ingestion.ingest("attempts", "attempts.csv", f.read())

        # Load labels and trajectory types for target & diagnostic evaluation
        roster_df = pd.read_csv(data_dir / "students_roster.csv")
        labels_map = dict(zip(roster_df["student_id"], roster_df["dropout_label"]))
        traj_map = dict(zip(roster_df["student_id"], roster_df["trajectory_type"]))

        fusion = StudentDataFusionService(session)
        profiles = fusion.fuse_all(limit=len(roster_df))

        feature_rows = []
        target_labels = []
        student_trajs = {}

        for p in profiles:
            s_id = p.student.id
            if s_id not in labels_map:
                continue

            feats = FeatureEngineeringService.extract_features(p, reference_date="2026-10-01")
            feat_dict = feats.model_dump()

            # Build strictly filtered ordered feature row
            row = {}
            for col in ML_FEATURE_NAMES:
                val = feat_dict[col]
                row[col] = float(val) if isinstance(val, (int, float, bool)) else val

            feature_rows.append(row)
            target_labels.append(int(labels_map[s_id]))
            student_trajs[s_id] = traj_map[s_id]

        X_df = pd.DataFrame(feature_rows)[ML_FEATURE_NAMES]
        y_ser = pd.Series(target_labels, name="dropout_label")

        return X_df, y_ser, student_trajs

    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

def train_model(
    data_dir: Path = BASE_DIR / "data" / "raw" / "synthetic",
    model_output_path: Path = BASE_DIR / "ml" / "models" / "dropout_detector.joblib",
    metadata_output_path: Path = BASE_DIR / "ml" / "models" / "metadata.json",
    seed: int = 42,
) -> Dict[str, Any]:
    """Trains, evaluates, and serializes the Random Forest dropout model."""
    print("Loading synthetic data through canonical Phase 4-5-6 pipeline...")
    X, y, trajectories = load_training_dataset(data_dir)

    print(f"Dataset loaded: {len(X)} rows, {len(ML_FEATURE_NAMES)} features.")
    print(f"Overall positive class rate: {y.mean():.4f}")

    # Stratified Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=seed, stratify=y
    )

    print(f"Train split: {len(X_train)} samples ({y_train.mean():.4f} positive)")
    print(f"Test split: {len(X_test)} samples ({y_test.mean():.4f} positive)")

    # Model Configuration
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    )

    print("Training RandomForestClassifier...")
    model.fit(X_train, y_train)

    # Evaluation on Held-Out Test Set
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    cm = confusion_matrix(y_test, y_pred).tolist()

    print("\n--- HELD-OUT TEST EVALUATION (SYNTHETIC DATA) ---")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"Confusion Matrix (TN, FP / FN, TP):\n{cm}")

    # Global Feature Importance
    importances = model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    feature_importances = [
        {"feature": ML_FEATURE_NAMES[i], "importance": round(float(importances[i]), 4)}
        for i in sorted_idx
    ]

    print("\nTop 10 Global Feature Importances:")
    for item in feature_importances[:10]:
        print(f"  - {item['feature']}: {item['importance']:.4f}")

    # Financial Context Sanity Check (Post-evaluation analysis)
    all_probs = model.predict_proba(X)[:, 1]
    fee_only_indices = [i for i, (s_id, t_name) in enumerate(trajectories.items()) if t_name == "FINANCIAL_CONTEXT_ONLY"]
    fee_only_probs = all_probs[fee_only_indices]
    fee_stats = {
        "count": len(fee_only_probs),
        "mean_probability": round(float(np.mean(fee_only_probs)), 4) if len(fee_only_probs) > 0 else 0.0,
        "min_probability": round(float(np.min(fee_only_probs)), 4) if len(fee_only_probs) > 0 else 0.0,
        "max_probability": round(float(np.max(fee_only_probs)), 4) if len(fee_only_probs) > 0 else 0.0,
    }
    print(f"\nFinancial Context Only Diagnostic (N={fee_stats['count']}): Mean Prob = {fee_stats['mean_probability']:.4f}, Min = {fee_stats['min_probability']:.4f}, Max = {fee_stats['max_probability']:.4f}")

    # Trajectory Diagnostics
    traj_breakdown = {}
    for t_type in sorted(list(set(trajectories.values()))):
        t_indices = [i for i, (s_id, t_name) in enumerate(trajectories.items()) if t_name == t_type]
        t_probs = all_probs[t_indices]
        traj_breakdown[t_type] = {
            "count": len(t_probs),
            "mean_probability": round(float(np.mean(t_probs)), 4),
        }

    # Serialization
    model_output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_output_path, compress=3)
    file_size_bytes = os.path.getsize(model_output_path)
    print(f"\nSaved model artifact to: {model_output_path} ({file_size_bytes / 1024:.2f} KB)")

    metadata = {
        "model_name": "Pathwise Dropout Detector",
        "model_type": "RandomForestClassifier",
        "model_version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "synthetic_warning": "TRAINED ON SYNTHETIC COHORT DATASET. Metrics reflect development performance and require local institutional calibration.",
        "random_seed": seed,
        "total_samples": len(X),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_names": ML_FEATURE_NAMES,
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "confusion_matrix": cm,
        },
        "feature_importances": feature_importances,
        "financial_context_stats": fee_stats,
        "trajectory_diagnostic": traj_breakdown,
    }

    with open(metadata_output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to: {metadata_output_path}")

    return metadata

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Pathwise Dropout Prediction Model")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()
    train_model(seed=args.seed)
