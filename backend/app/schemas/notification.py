from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class NotificationItem(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    student_roll: Optional[str] = None
    student_dept: Optional[str] = None
    notification_type: str
    severity: str
    title: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None

class PaginatedNotificationResponse(BaseModel):
    items: List[NotificationItem]
    page: int
    page_size: int
    total: int
    pages: int
    unread_count: int

class UnreadCountResponse(BaseModel):
    unread_count: int

class MarkReadResponse(BaseModel):
    success: bool
    updated_count: int
