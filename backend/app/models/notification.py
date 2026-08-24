import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

class NotificationTypeEnum(str, enum.Enum):
    EMAIL = "EMAIL"
    MOCK = "MOCK"

class RecipientTypeEnum(str, enum.Enum):
    MENTOR = "MENTOR"
    GUARDIAN = "GUARDIAN"

class NotificationStatusEnum(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    type = Column(Enum(NotificationTypeEnum), default=NotificationTypeEnum.MOCK, nullable=False)
    recipient_type = Column(Enum(RecipientTypeEnum), nullable=False)
    recipient_email = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(Enum(NotificationStatusEnum), default=NotificationStatusEnum.PENDING, nullable=False)

    # Relationships
    student = relationship("Student", back_populates="notifications")
