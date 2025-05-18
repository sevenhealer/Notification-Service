from pydantic import BaseModel, EmailStr, constr
from typing import List, Optional
from datetime import datetime
from models import NotificationType, NotificationStatus # Import enums from models.py

# Base model for Notification attributes
class NotificationBase(BaseModel):
    user_id: int
    type: NotificationType
    message: constr(min_length=1) # type: ignore # Message cannot be empty

# Schema for creating a new notification (request body for POST /notifications)
class NotificationCreate(NotificationBase):
    # Optional: If recipient details are explicitly provided during creation
    recipient_address: Optional[str] = None # e.g. email or phone
    pass

# Schema for reading/returning a notification (used in GET responses)
class Notification(NotificationBase):
    id: int
    status: NotificationStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    recipient_address: Optional[str] = None

    class Config:
        orm_mode = True # Pydantic's orm_mode will tell Pydantic to read the data even if it is not a dict, but an ORM model

# Schema for the response of GET /users/{id}/notifications
class NotificationList(BaseModel):
    notifications: List[Notification]

