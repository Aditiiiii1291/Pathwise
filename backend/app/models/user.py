import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base


class UserRoleEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    MENTOR = "MENTOR"
    COUNSELLOR = "COUNSELLOR"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    role = Column(String(20), default=UserRoleEnum.MENTOR.value, nullable=False)
    mentor_id = Column(Integer, ForeignKey("mentors.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    mentor = relationship("Mentor")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
