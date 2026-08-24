import os
import smtplib
import logging
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

try:
    from app.models.notification import Notification, NotificationTypeEnum, NotificationSeverityEnum
    from app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
    from app.models.student import Student
except ImportError:
    from backend.app.models.notification import Notification, NotificationTypeEnum, NotificationSeverityEnum
    from backend.app.models.risk import RiskSnapshot, RiskTierEnum, TrendEnum
    from backend.app.models.student import Student

logger = logging.getLogger(__name__)

TIER_ORDER = {
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4,
}

class NotificationService:
    @staticmethod
    def evaluate_and_create_notifications(
        db: Session,
        student_id: int,
        new_snapshot: RiskSnapshot,
    ) -> List[Notification]:
        """
        Evaluates risk state transitions between previous latest snapshot and the newly persisted snapshot.
        Generates in-app notifications only on meaningful transitions (escalations, rapid decline, improvements).
        Guarantees deduplication: does not generate duplicate alerts for unchanged states.
        """
        # Retrieve student metadata
        student = db.query(Student).filter(Student.id == student_id).first()
        if not student:
            logger.warning(f"Notification skipped: Student with ID {student_id} not found.")
            return []

        # Retrieve previous latest snapshot for comparison (excluding current snapshot)
        prev_snapshot = (
            db.query(RiskSnapshot)
            .filter(
                RiskSnapshot.student_id == student_id,
                RiskSnapshot.id != new_snapshot.id,
            )
            .order_by(desc(RiskSnapshot.computed_at), desc(RiskSnapshot.id))
            .first()
        )

        notifications_to_create: List[Notification] = []

        new_tier_str = new_snapshot.risk_tier.value if hasattr(new_snapshot.risk_tier, "value") else str(new_snapshot.risk_tier)
        new_trend_str = new_snapshot.trend.value if hasattr(new_snapshot.trend, "value") else str(new_snapshot.trend)

        if prev_snapshot is None:
            # First snapshot evaluation for this student
            if new_tier_str == "CRITICAL":
                notifications_to_create.append(
                    Notification(
                        student_id=student_id,
                        risk_snapshot_id=new_snapshot.id,
                        notification_type=NotificationTypeEnum.CRITICAL_RISK.value,
                        severity=NotificationSeverityEnum.CRITICAL.value,
                        title="Student classified as Critical Risk",
                        message=f"{student.name} ({student.roll_number}) in {student.department} has been evaluated at CRITICAL risk (score: {new_snapshot.final_score:.1f}/100).",
                        is_read=False,
                    )
                )
            elif new_tier_str == "HIGH":
                notifications_to_create.append(
                    Notification(
                        student_id=student_id,
                        risk_snapshot_id=new_snapshot.id,
                        notification_type=NotificationTypeEnum.RISK_ESCALATION.value,
                        severity=NotificationSeverityEnum.HIGH.value,
                        title="Student classified as High Risk",
                        message=f"{student.name} ({student.roll_number}) in {student.department} has been evaluated at HIGH risk (score: {new_snapshot.final_score:.1f}/100).",
                        is_read=False,
                    )
                )

            if new_trend_str == "RAPIDLY_DETERIORATING":
                notifications_to_create.append(
                    Notification(
                        student_id=student_id,
                        risk_snapshot_id=new_snapshot.id,
                        notification_type=NotificationTypeEnum.RAPID_DETERIORATION.value,
                        severity=NotificationSeverityEnum.HIGH.value,
                        title="Rapid trajectory deterioration detected",
                        message=f"{student.name} ({student.roll_number}) exhibits rapid multi-factor decline across recent evaluation milestones.",
                        is_read=False,
                    )
                )
        else:
            # Compare with previous snapshot
            prev_tier_str = prev_snapshot.risk_tier.value if hasattr(prev_snapshot.risk_tier, "value") else str(prev_snapshot.risk_tier)
            prev_trend_str = prev_snapshot.trend.value if hasattr(prev_snapshot.trend, "value") else str(prev_snapshot.trend)

            prev_tier_val = TIER_ORDER.get(prev_tier_str, 1)
            new_tier_val = TIER_ORDER.get(new_tier_str, 1)

            # 1. Check Risk Tier Transitions
            if new_tier_val > prev_tier_val:
                # Escalation
                if new_tier_str == "CRITICAL":
                    notifications_to_create.append(
                        Notification(
                            student_id=student_id,
                            risk_snapshot_id=new_snapshot.id,
                            notification_type=NotificationTypeEnum.CRITICAL_RISK.value,
                            severity=NotificationSeverityEnum.CRITICAL.value,
                            title="Risk escalated to Critical",
                            message=f"{student.name} ({student.roll_number}) escalated from {prev_tier_str} to CRITICAL risk (score: {new_snapshot.final_score:.1f}/100).",
                            is_read=False,
                        )
                    )
                elif new_tier_str == "HIGH":
                    notifications_to_create.append(
                        Notification(
                            student_id=student_id,
                            risk_snapshot_id=new_snapshot.id,
                            notification_type=NotificationTypeEnum.RISK_ESCALATION.value,
                            severity=NotificationSeverityEnum.HIGH.value,
                            title="Risk escalated to High",
                            message=f"{student.name} ({student.roll_number}) escalated from {prev_tier_str} to HIGH risk (score: {new_snapshot.final_score:.1f}/100).",
                            is_read=False,
                        )
                    )
                else:
                    notifications_to_create.append(
                        Notification(
                            student_id=student_id,
                            risk_snapshot_id=new_snapshot.id,
                            notification_type=NotificationTypeEnum.RISK_ESCALATION.value,
                            severity=NotificationSeverityEnum.WARNING.value,
                            title="Risk level increased",
                            message=f"{student.name} ({student.roll_number}) moved from {prev_tier_str} to {new_tier_str} risk (score: {new_snapshot.final_score:.1f}/100).",
                            is_read=False,
                        )
                    )
            elif new_tier_val < prev_tier_val:
                # Positive Risk Improvement
                notifications_to_create.append(
                    Notification(
                        student_id=student_id,
                        risk_snapshot_id=new_snapshot.id,
                        notification_type=NotificationTypeEnum.RISK_IMPROVEMENT.value,
                        severity=NotificationSeverityEnum.INFO.value,
                        title="Student risk level improved",
                        message=f"{student.name} ({student.roll_number}) improved from {prev_tier_str} to {new_tier_str} risk (score: {new_snapshot.final_score:.1f}/100).",
                        is_read=False,
                    )
                )

            # 2. Check Trend Transitions
            if new_trend_str == "RAPIDLY_DETERIORATING" and prev_trend_str != "RAPIDLY_DETERIORATING":
                notifications_to_create.append(
                    Notification(
                        student_id=student_id,
                        risk_snapshot_id=new_snapshot.id,
                        notification_type=NotificationTypeEnum.RAPID_DETERIORATION.value,
                        severity=NotificationSeverityEnum.HIGH.value,
                        title="Rapid trajectory deterioration detected",
                        message=f"{student.name} ({student.roll_number}) shifted from {prev_trend_str} to RAPIDLY_DETERIORATING trajectory.",
                        is_read=False,
                    )
                )
            elif prev_trend_str == "RAPIDLY_DETERIORATING" and new_trend_str in ("STABLE", "IMPROVING"):
                notifications_to_create.append(
                    Notification(
                        student_id=student_id,
                        risk_snapshot_id=new_snapshot.id,
                        notification_type=NotificationTypeEnum.RISK_IMPROVEMENT.value,
                        severity=NotificationSeverityEnum.INFO.value,
                        title="Trajectory trend stabilized",
                        message=f"{student.name} ({student.roll_number}) stabilized from Rapid Deterioration to {new_trend_str}.",
                        is_read=False,
                    )
                )

        # Persist generated notifications
        for notif in notifications_to_create:
            db.add(notif)

        if notifications_to_create:
            db.commit()
            for notif in notifications_to_create:
                db.refresh(notif)
                # Dispatch optional SMTP email if configured
                NotificationService._dispatch_optional_email(student, notif)

        return notifications_to_create

    @staticmethod
    def get_notifications(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        unread_only: bool = False,
        severity: Optional[str] = None,
        student_id: Optional[int] = None,
    ) -> Tuple[List[Notification], int, int, int]:
        """
        Retrieves paginated notifications ordered newest first (created_at DESC, id DESC).
        Returns: (items, total_count, total_pages, unread_count)
        """
        query = db.query(Notification)

        if unread_only:
            query = query.filter(Notification.is_read == False)
        if severity:
            query = query.filter(Notification.severity == severity.upper())
        if student_id:
            query = query.filter(Notification.student_id == student_id)

        # Ordering newest first with deterministic tie-breaker
        query = query.order_by(desc(Notification.created_at), desc(Notification.id))

        total_count = query.count()
        unread_count = db.query(Notification).filter(Notification.is_read == False).count()

        total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return items, total_count, total_pages, unread_count

    @staticmethod
    def get_unread_count(db: Session) -> int:
        """Returns the total number of unread notifications."""
        return db.query(Notification).filter(Notification.is_read == False).count()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int) -> Optional[Notification]:
        """Marks a single notification as read."""
        notif = db.query(Notification).filter(Notification.id == notification_id).first()
        if not notif:
            return None

        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def mark_all_as_read(db: Session) -> int:
        """Marks all unread notifications as read."""
        now = datetime.now(timezone.utc)
        updated = (
            db.query(Notification)
            .filter(Notification.is_read == False)
            .update({"is_read": True, "read_at": now}, synchronize_session="fetch")
        )
        db.commit()
        return updated

    @staticmethod
    def _dispatch_optional_email(student: Student, notification: Notification) -> bool:
        """
        Optional SMTP email dispatcher.
        If SMTP environment variables are not configured, gracefully skips email delivery.
        Core in-app notification creation is NEVER interrupted by email delivery.
        """
        smtp_host = os.environ.get("SMTP_HOST")
        if not smtp_host:
            # Gracefully skip if SMTP is not configured
            return False

        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USERNAME")
        smtp_pass = os.environ.get("SMTP_PASSWORD")
        from_email = os.environ.get("SMTP_FROM_EMAIL", "alerts@pathwise.edu")

        # Determine recipient (mentor or system address)
        recipient_email = student.mentor.email if student.mentor and student.mentor.email else student.guardian_email
        if not recipient_email:
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = recipient_email
            msg["Subject"] = f"[Pathwise Alert] {notification.title} - {student.name}"

            body = (
                f"Pathwise Retention Intelligence Alert\n\n"
                f"Severity: {notification.severity}\n"
                f"Student: {student.name} ({student.roll_number})\n"
                f"Department: {student.department}\n\n"
                f"{notification.message}\n\n"
                f"Please review the student profile in Pathwise for full analytical details."
            )
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as server:
                server.starttls()
                if smtp_user and smtp_pass:
                    server.login(smtp_user, smtp_pass)
                server.send_message(msg)

            logger.info(f"Notification email dispatched to {recipient_email}")
            return True
        except Exception as e:
            logger.warning(f"Optional SMTP email delivery skipped due to error: {e}")
            return False
