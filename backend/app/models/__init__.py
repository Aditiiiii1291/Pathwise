try:
    from app.models.student import Student
    from app.models.mentor import Mentor
    from app.models.attendance import AttendanceRecord
    from app.models.marks import MarksRecord, ExamTypeEnum
    from app.models.fee import FeeRecord, FeeStatusEnum
    from app.models.attempt import AttemptRecord, BacklogStatusEnum
    from app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
    from app.models.intervention import (
        Intervention,
        InterventionTypeEnum,
        InterventionStatusEnum,
        InterventionOutcomeEnum,
    )
    from app.models.rule_config import RuleConfig
    from app.models.notification import (
        Notification,
        NotificationTypeEnum,
        RecipientTypeEnum,
        NotificationStatusEnum,
    )
except ImportError:
    from backend.app.models.student import Student
    from backend.app.models.mentor import Mentor
    from backend.app.models.attendance import AttendanceRecord
    from backend.app.models.marks import MarksRecord, ExamTypeEnum
    from backend.app.models.fee import FeeRecord, FeeStatusEnum
    from backend.app.models.attempt import AttemptRecord, BacklogStatusEnum
    from backend.app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
    from backend.app.models.intervention import (
        Intervention,
        InterventionTypeEnum,
        InterventionStatusEnum,
        InterventionOutcomeEnum,
    )
    from backend.app.models.rule_config import RuleConfig
    from backend.app.models.notification import (
        Notification,
        NotificationTypeEnum,
        RecipientTypeEnum,
        NotificationStatusEnum,
    )

__all__ = [
    "Student",
    "Mentor",
    "AttendanceRecord",
    "MarksRecord",
    "ExamTypeEnum",
    "FeeRecord",
    "FeeStatusEnum",
    "AttemptRecord",
    "BacklogStatusEnum",
    "RiskSnapshot",
    "RiskTierEnum",
    "TrendEnum",
    "Intervention",
    "InterventionTypeEnum",
    "InterventionStatusEnum",
    "InterventionOutcomeEnum",
    "RuleConfig",
    "Notification",
    "NotificationTypeEnum",
    "RecipientTypeEnum",
    "NotificationStatusEnum",
]
