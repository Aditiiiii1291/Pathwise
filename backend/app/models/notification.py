import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

class NotificationTypeEnum(str, enum.Enum):
    RISK_ESCALATION = "RISK_ESCALATION"
    CRITICAL_RISK = "CRITICAL_RISK"
    RAPID_DETERIORATION = "RAPID_DETERIORATION"
    RISK_IMPROVEMENT = "RISK_IMPROVEMENT"
    ATTENDANCE_ALERT = "ATTENDANCE_ALERT"
    ACADEMIC_ALERT = "ACADEMIC_ALERT"
    # Legacy Phase 2 types
    EMAIL = "EMAIL"
    MOCK = "MOCK"

class NotificationSeverityEnum(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

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
    risk_snapshot_id = Column(Integer, ForeignKey("risk_snapshots.id"), nullable=True, index=True)

    notification_type = Column(String, default="RISK_ESCALATION", nullable=False, index=True)
    severity = Column(String, default="INFO", nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Optional / Legacy Phase 2 fields for backward compatibility
    type = Column(Enum(NotificationTypeEnum), default=NotificationTypeEnum.MOCK, nullable=True)
    recipient_type = Column(Enum(RecipientTypeEnum), default=RecipientTypeEnum.MENTOR, nullable=True)
    recipient_email = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    body = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
    status = Column(Enum(NotificationStatusEnum), default=NotificationStatusEnum.PENDING, nullable=True)

    # Relationships
    student = relationship("Student", back_populates="notifications")
    risk_snapshot = relationship("RiskSnapshot")

    def __init__(self, **kwargs):
        # Auto-map legacy subject/body to title/message if not explicitly passed
        if "subject" in kwargs and "title" not in kwargs:
            kwargs["title"] = kwargs["subject"]
        if "body" in kwargs and "message" not in kwargs:
            kwargs["message"] = kwargs["body"]
        if "title" in kwargs and "subject" not in kwargs:
            kwargs["subject"] = kwargs["title"]
        if "message" in kwargs and "body" not in kwargs:
            kwargs["body"] = kwargs["message"]
        super().__init__(**kwargs)
