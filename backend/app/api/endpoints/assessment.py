from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
    from app.schemas.api import StudentAssessmentResponse
    from app.services.fusion import StudentDataFusionService
    from app.services.features import FeatureEngineeringService
    from app.services.rules import RuleEngine
    from app.services.ml_predictor import MLPredictor
    from app.services.fusion_engine import RiskFusionEngine
    from app.services.explainer import ExplanationEngine
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.schemas.api import StudentAssessmentResponse
    from backend.app.services.fusion import StudentDataFusionService
    from backend.app.services.features import FeatureEngineeringService
    from backend.app.services.rules import RuleEngine
    from backend.app.services.ml_predictor import MLPredictor
    from backend.app.services.fusion_engine import RiskFusionEngine
    from backend.app.services.explainer import ExplanationEngine

router = APIRouter(prefix="/students", tags=["assessment"])

def _run_assessment_pipeline(student_id: int, db: Session):
    """Internal helper to execute the complete analytical pipeline."""
    fusion_service = StudentDataFusionService(db)
    profile = fusion_service.fuse_by_id(student_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_id} not found.",
        )

    # Phase 6: Temporal Feature Engineering
    features = FeatureEngineeringService.extract_features(profile)

    # Phase 7: Explainable Rule Engine (with DB department config if configured)
    rule_config = RuleEngine.load_config_from_db(db, department=profile.student.department)
    rule_res = RuleEngine.evaluate(features, config=rule_config)

    # Phase 8: ML Prediction Engine
    try:
        predictor = MLPredictor()
        ml_prob = predictor.predict_dropout_probability(features)
        global_imp = predictor.get_feature_importances()
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Trained ML model artifact not found. Please run training pipeline.",
        )

    # Phase 9: Risk Fusion Engine
    fusion_res = RiskFusionEngine.fuse(
        student_id=student_id,
        rule_score=rule_res.rule_score,
        ml_probability=ml_prob,
        features=features,
    )

    # Phase 10: Explanation & Recommendation Engine
    explanation = ExplanationEngine.generate_explanation(
        features=features,
        rule_result=rule_res,
        fusion_result=fusion_res,
        global_feature_importances=global_imp,
    )

    return fusion_res, explanation

@router.get("/{student_id}/assessment", response_model=StudentAssessmentResponse, status_code=status.HTTP_200_OK)
def get_student_assessment(
    student_id: int,
    db: Session = Depends(get_db),
):
    """
    On-demand read-only evaluation of the student risk and explanation pipeline.
    Does NOT persist a new snapshot.
    """
    fusion_res, explanation = _run_assessment_pipeline(student_id, db)
    return StudentAssessmentResponse(
        student_id=student_id,
        assessment=fusion_res,
        explanation=explanation,
    )

@router.post("/{student_id}/assessment", response_model=StudentAssessmentResponse, status_code=status.HTTP_200_OK)
def calculate_and_save_student_assessment(
    student_id: int,
    db: Session = Depends(get_db),
):
    """
    Computes a full risk assessment and records a persistent RiskSnapshot (append-only history).
    """
    fusion_res, explanation = _run_assessment_pipeline(student_id, db)

    # Persist RiskSnapshot in database
    snapshot = RiskFusionEngine.to_risk_snapshot(fusion_res)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return StudentAssessmentResponse(
        student_id=student_id,
        assessment=fusion_res,
        explanation=explanation,
    )
