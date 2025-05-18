# FastAPI application entry point

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

import crud
import schemas
from database import engine, get_db, SessionLocal # Added SessionLocal for startup event
from models import Base as DBBase # For creating tables on startup (dev only)

from tasks import send_notification_task # Import Celery task
from config import settings

# --- Database Initialization (for development/testing) ---
# In a production environment, you would use Alembic for migrations.
def create_db_and_tables():
    DBBase.metadata.create_all(bind=engine)

# Call this function when the application starts
# This is useful for quickly setting up the DB in dev,
# but for production, use migrations (e.g., Alembic).
# Comment out if you manage DB schema separately.
# create_db_and_tables() # Create tables on startup

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG_MODE,
    description="A service to send notifications via Email, SMS, and In-App channels.",
    version="0.1.0"
)

@app.on_event("startup")
async def startup_event():
    # This is a good place to initialize things if needed
    # For example, check DB connection or run create_db_and_tables()
    try:
        # Attempt to connect to the database to ensure it's available
        db = SessionLocal()
        db.execute(text("SELECT 1")) # Simple query to test connection
        db.close()
        print("Database connection successful.")
        # If you want to create tables on startup (dev/testing only):
        print("Creating database tables if they don't exist (for dev)...")
        create_db_and_tables()
    except Exception as e:
        print(f"Error connecting to database during startup: {e}")
        # Depending on severity, you might want to exit or log prominently


# --- API Endpoints ---

@app.post("/notifications", response_model=schemas.Notification, status_code=status.HTTP_202_ACCEPTED)
async def create_and_send_notification(
    notification_in: schemas.NotificationCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new notification.
    The notification is first stored in the database and then a task is queued
    to an asynchronous worker (Celery) for actual sending.

    - **userId**: ID of the user to notify.
    - **type**: Notification type (`email`, `sms`, `in-app`).
    - **message**: The content of the notification.
    """
    # 1. Store the notification in the database
    print(notification_in)
    db_notification = crud.create_notification(db=db, notification=notification_in)
    if not db_notification:
        # This case should ideally not happen if DB operations are sound
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create notification record in DB")

    # 2. Send a task to Celery to process the notification
    # We pass primitive types to Celery tasks as a best practice.
    task_args = {
        "notification_id": db_notification.id,
        "notification_type": db_notification.type.value, # Pass enum value
        "user_id": db_notification.user_id,
        "message": db_notification.message,
        "recipient_address": db_notification.recipient_address # If you stored it
    }

    try:
        send_notification_task.delay(**task_args)
        # .delay() is a shortcut for .send_task(args=[...], kwargs={...})
        print(f"Notification task enqueued for ID: {db_notification.id} with args: {task_args}")
    except Exception as e: # Catch Celery connection errors specifically if possible
        # If queuing fails, we should ideally handle it:
        # - Log the error
        # - Optionally, change notification status to FAILED_TO_QUEUE or similar
        # - Return an error to the client, or a success with a warning
        print(f"Error enqueuing notification task for ID {db_notification.id}: {e}")
        # For now, we'll let the client know it was created in DB, but queuing failed.
        # This is a critical failure point to monitor.
        # Depending on requirements, you might want to make this atomic or have a fallback.
        # crud.update_notification_status(db, db_notification.id, models.NotificationStatus.FAILED) # Example
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notification created (ID: {db_notification.id}) but failed to enqueue sending task. Please check worker status."
        )

    # Return the database object, which Pydantic will serialize using Notification schema
    return db_notification


@app.get("/users/{user_id}/notifications", response_model=schemas.NotificationList) # Using the new NotificationList
async def get_user_notifications(
    user_id: int,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    Retrieve all notifications for a specific user.

    - **user_id**: The ID of the user whose notifications to retrieve.
    - **skip**: Number of records to skip (for pagination).
    - **limit**: Maximum number of records to return (for pagination).
    """
    notifications = crud.get_notifications_by_user_id(db=db, user_id=user_id, skip=skip, limit=limit)
    if not notifications:
        # It's not an error if a user has no notifications, return an empty list.
        # If you want to return 404 if the user_id itself is invalid (e.g., no such user),
        # you'd need a User model and a check here. For now, we assume user_id is valid.
        pass
    return {"notifications": notifications} # Wrap in the NotificationList schema


@app.get("/notifications/{notification_id}", response_model=schemas.Notification)
async def get_notification_details(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    Retrieve details for a specific notification by its ID.
    """
    db_notification = crud.get_notification_by_id(db=db, notification_id=notification_id)
    if db_notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return db_notification

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}

# To run the FastAPI application (e.g., using uvicorn):
# uvicorn main:app --reload --port 8000
