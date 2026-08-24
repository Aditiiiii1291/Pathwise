from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

class RuleConfig(Base):
    __tablename__ = "rule_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    department = Column(String, unique=True, nullable=True)  # Global default if null
    config_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now(), nullable=False)
    updated_by = Column(String, nullable=True)
