from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
    from app.models import RuleConfig
    from app.schemas.rules import RuleEngineConfig, RuleWeights, RuleThresholds
    from app.schemas.api import RuleConfigUpdate
    from app.services.rules import RuleEngine
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.models import RuleConfig
    from backend.app.schemas.rules import RuleEngineConfig, RuleWeights, RuleThresholds
    from backend.app.schemas.api import RuleConfigUpdate
    from backend.app.services.rules import RuleEngine

router = APIRouter(prefix="/rules", tags=["rules"])

@router.get("", response_model=RuleEngineConfig, status_code=status.HTTP_200_OK)
def get_rules(
    department: Optional[str] = Query(None, description="Department-specific rules if configured"),
    db: Session = Depends(get_db),
):
    """
    Retrieves active rule weights and thresholds for a department or institutional default.
    """
    return RuleEngine.load_config_from_db(db, department=department)

@router.put("", response_model=RuleEngineConfig, status_code=status.HTTP_200_OK)
def update_rules(
    body: RuleConfigUpdate,
    db: Session = Depends(get_db),
):
    """
    Updates rule engine configuration. Validates weight normalization (sum == 1.0).
    Does NOT modify historical snapshots.
    """
    # Look for existing rule configuration record
    config_record = None
    if body.department:
        config_record = db.query(RuleConfig).filter(RuleConfig.department == body.department).first()
    else:
        config_record = db.query(RuleConfig).filter(RuleConfig.department.is_(None)).first()

    config_data = {
        "weights": body.weights.model_dump(),
        "thresholds": body.thresholds.model_dump(),
    }

    if config_record:
        config_record.config_json = config_data
    else:
        config_record = RuleConfig(
            department=body.department,
            config_json=config_data,
        )
        db.add(config_record)

    db.commit()
    db.refresh(config_record)

    return RuleEngineConfig(
        weights=body.weights,
        thresholds=body.thresholds,
        department=body.department,
    )
