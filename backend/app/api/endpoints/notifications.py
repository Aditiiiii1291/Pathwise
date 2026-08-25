from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

try:
    from app.core.database import get_db
    from app.models.user import User
    from app.api.deps import get_current_user
    from app.schemas.notification import (
        NotificationItem,
        PaginatedNotificationResponse,
        UnreadCountResponse,
        MarkReadResponse,
    )
    from app.services.notifications import NotificationService
except ImportError:
    from backend.app.core.database import get_db
    from backend.app.models.user import User
    from backend.app.api.deps import get_current_user
    from backend.app.schemas.notification import (
        NotificationItem,
        PaginatedNotificationResponse,
        UnreadCountResponse,
        MarkReadResponse,
    )
    from backend.app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])

def _to_notification_item(notif) -> NotificationItem:
    student_name = notif.student.name if notif.student else None
    student_roll = notif.student.roll_number if notif.student else None
    student_dept = notif.student.department if notif.student else None

    return NotificationItem(
        id=notif.id,
        student_id=notif.student_id,
        student_name=student_name,
        student_roll=student_roll,
        student_dept=student_dept,
        notification_type=notif.notification_type,
        severity=notif.severity,
        title=notif.title,
        message=notif.message,
        is_read=notif.is_read,
        created_at=notif.created_at,
        read_at=notif.read_at,
    )

@router.get("", response_model=PaginatedNotificationResponse, status_code=status.HTTP_200_OK)
def list_notifications(
    page: int = Query(1, ge=1, description="Page number starting at 1"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    unread_only: bool = Query(False, description="Filter unread notifications only"),
    severity: Optional[str] = Query(None, description="Filter by severity (INFO, WARNING, HIGH, CRITICAL)"),
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a paginated list of in-app notifications, ordered newest first.
    Requires authenticated user.
    """
    items, total, pages, unread_count = NotificationService.get_notifications(
        db=db,
        page=page,
        page_size=page_size,
        unread_only=unread_only,
        severity=severity,
        student_id=student_id,
    )

    response_items = [_to_notification_item(n) for n in items]

    return PaginatedNotificationResponse(
        items=response_items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        unread_count=unread_count,
    )

@router.get("/unread-count", response_model=UnreadCountResponse, status_code=status.HTTP_200_OK)
def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the total count of unread notifications for quick UI badge polling.
    Requires authenticated user.
    """
    count = NotificationService.get_unread_count(db)
    return UnreadCountResponse(unread_count=count)

@router.patch("/{notification_id}/read", response_model=NotificationItem, status_code=status.HTTP_200_OK)
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Marks a single notification as read.
    Requires authenticated user.
    """
    notif = NotificationService.mark_as_read(db, notification_id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found.",
        )
    return _to_notification_item(notif)

@router.patch("/read-all", response_model=MarkReadResponse, status_code=status.HTTP_200_OK)
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Marks all unread notifications as read.
    Requires authenticated user.
    """
    updated_count = NotificationService.mark_all_as_read(db)
    return MarkReadResponse(success=True, updated_count=updated_count)
