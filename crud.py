from sqlalchemy.orm import Session
from models import Notification, NotificationStatus
from schemas import NotificationCreate
from typing import List, Optional

def create_notification(db: Session, notification: NotificationCreate) -> Notification:
    """
    Creates a new notification record in the database.
    """
    db_notification = Notification(
        user_id=notification.user_id,
        type=notification.type,
        message=notification.message,
        status=NotificationStatus.PENDING, # Initial status
        recipient_address=notification.recipient_address # If provided
    )
    print(db_notification)
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notification_by_id(db: Session, notification_id: int) -> Optional[Notification]:
    """
    Retrieves a single notification by its ID.
    """
    return db.query(Notification).filter(Notification.id == notification_id).first()

def get_notifications_by_user_id(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Notification]:
    """
    Retrieves all notifications for a specific user, with pagination.
    """
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()

def update_notification_status(db: Session, notification_id: int, status: NotificationStatus) -> Optional[Notification]:
    """
    Updates the status of a notification.
    """
    db_notification = get_notification_by_id(db, notification_id)
    if db_notification:
        db_notification.status = status
        db.commit()
        db.refresh(db_notification)
    return db_notification

# You could add more CRUD operations as needed, e.g., delete_notification, etc.