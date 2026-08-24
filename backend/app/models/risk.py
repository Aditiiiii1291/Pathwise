import enum
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

class RiskTierEnum(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TrendEnum(str, enum.Enum):
    IMPROVING = "IMPROVING"
    STABLE = "STABLE"
    GRADUALLY_DETERIORATING = "GRADUALLY_DETERIORATING"
    RAPIDLY_DETERIORATING = "RAPIDLY_DETERIORATING"

class RiskSnapshot(Base):
    __tablename__ = "risk_snapshots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    rule_score = Column(Float, nullable=False)
    ml_probability = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False)
    risk_tier = Column(Enum(RiskTierEnum), nullable=False)
    trend = Column(Enum(TrendEnum), nullable=False)
    factors_json = Column(JSON, nullable=True)
    feature_imp_json = Column(JSON, nullable=True)
    recommendations_json = Column(JSON, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="risk_snapshots")
