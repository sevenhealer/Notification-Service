from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()

# Enum for notification types
class NotificationType(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in-app"

# Enum for notification status
class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered" # For in-app or if delivery receipts are used
    SEEN = "seen" # For in-app

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False) # Assuming user_id is an integer.
                                                        # In a real system, this might be a ForeignKey to a 'users' table.
    type = Column(SQLAlchemyEnum(NotificationType), nullable=False)
    message = Column(String, nullable=False)
    status = Column(SQLAlchemyEnum(NotificationStatus), default=NotificationStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # Optional: Store recipient details if they vary or are not derivable from user_id alone
    recipient_address = Column(String, nullable=True) # e.g., email address or phone number for that specific notification

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, type='{self.type}', status='{self.status}')>"

# If you had a User model, it might look like this (optional for this assignment):
# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True, index=True)
#     email = Column(String, unique=True, index=True, nullable=True)
#     phone_number = Column(String, unique=True, index=True, nullable=True)
#     # ... other user fields
#     notifications = relationship("Notification", back_populates="user") # If using a direct relationship

# Note: For this assignment, we'll assume user_id is sufficient and user details
# (like email/phone for sending) are either passed in the message/API call
# or handled by a separate user service.

# To create the tables in your database, you would typically use Alembic migrations
# or a simple script with:
# from database import engine # Assuming you have a database.py setting up the engine
# Base.metadata.create_all(bind=engine)