# Celery tasks for asynchronous notification sending.

from typing import Optional
from celery import Celery
from celery.utils.log import get_task_logger
from kombu.exceptions import OperationalError # For connection errors
import time
import smtplib # For email
from email.mime.text import MIMEText # For email
from twilio.rest import Client as TwilioClient # For SMS, if using actual Twilio
from twilio.base.exceptions import TwilioRestException

from config import settings # Import application settings
# It's good practice to initialize db session/engine per task if needed,
# or pass necessary data directly to the task.
# For updating status, we might need a way to get a DB session.
# A simple way is to re-create a session, or pass notification_id and update via a CRUD function.

# Initialize Celery
# The first argument to Celery is the name of the current module.
# The broker argument specifies the URL of the message broker you want to use.
# The backend argument specifies the result backend to use.
celery_app = Celery(
    "notification_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Optional Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # task_acks_late=True, # If you want tasks to be acknowledged after completion/failure
    # worker_prefetch_multiplier=1, # If you want workers to fetch one task at a time
)

logger = get_task_logger(__name__)

# --- Mock Notification Sending Functions ---
def _mock_send_email(recipient_email: str, subject: str, body: str):
    logger.info(f"MOCKING: Sending email to {recipient_email} with subject '{subject}' and body '{body}'")
    # Simulate network delay or processing time
    time.sleep(2)
    # Simulate potential failure
    # if random.random() < 0.1: # 10% chance of failure
    #     raise Exception("Mock email provider down")
    logger.info(f"MOCK Email sent to {recipient_email}")
    return True

def _send_actual_email(recipient_email: str, subject: str, body: str):
    logger.info(f"Attempting to send actual email to {recipient_email}...")
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = settings.EMAIL_FROM_ADDRESS
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            if settings.USE_TLS:
                server.starttls()
            server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
            server.sendmail(settings.EMAIL_FROM_ADDRESS, [recipient_email], msg.as_string())
        logger.info(f"Successfully sent actual email to {recipient_email}")
        return True
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error sending email to {recipient_email}: {e}")
        raise # Re-raise to trigger Celery retry
    except Exception as e:
        logger.error(f"Unexpected error sending actual email to {recipient_email}: {e}")
        raise # Re-raise to trigger Celery retry


def _mock_send_sms(recipient_phone: str, message: str):
    logger.info(f"MOCKING: Sending SMS to {recipient_phone} with message: '{message}'")
    time.sleep(1)
    logger.info(f"MOCK SMS sent to {recipient_phone}")
    return True

def _send_actual_sms(recipient_phone: str, message_body: str):
    logger.info(f"Attempting to send actual SMS to {recipient_phone}...")
    try:
        client = TwilioClient(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=message_body,
            from_=settings.TWILIO_FROM_NUMBER,
            to=recipient_phone
        )
        logger.info(f"SMS sent via Twilio. SID: {message.sid}")
        return True
    except TwilioRestException as e:
        logger.error(f"Twilio Error sending SMS to {recipient_phone}: {e}")
        raise # Re-raise to trigger Celery retry
    except Exception as e:
        logger.error(f"Unexpected error sending actual SMS: {e}")
        raise

def _handle_in_app_notification(user_id: int, message: str, notification_id: int):
    logger.info(f"HANDLING: In-app notification for user_id {user_id}, notification_id {notification_id} with message: '{message}'")
    # In a real system, this might involve:
    # 1. Ensuring the notification is in the DB (already done before task).
    # 2. Pushing to a WebSocket if the user is connected.
    # 3. Updating a 'seen' status or similar.
    # For this assignment, simply logging is sufficient for the "sending" part.
    # The status update to 'SENT' or 'DELIVERED' will happen after this task succeeds.
    time.sleep(0.5)
    logger.info(f"In-app notification for user_id {user_id}, notification_id {notification_id} processed.")
    return True

# --- Celery Task Definition ---
@celery_app.task(
    bind=True, # Gives access to `self` (the task instance)
    max_retries=settings.TASK_RETRY_MAX_RETRIES,
    default_retry_delay=settings.TASK_RETRY_DEFAULT_DELAY,
    autoretry_for=(OperationalError, smtplib.SMTPException, Exception) # Add other specific exceptions
)
def send_notification_task(self, notification_id: int, notification_type: str, user_id: int, message: str, recipient_address: Optional[str] = None):
    """
    Celery task to send a notification.
    It will call the appropriate sender (email, sms, in-app).
    It also updates the notification status in the database.
    """
    from database import SessionLocal # Import here to avoid circular imports at module level
    from crud import update_notification_status # Import here
    from models import NotificationStatus as DBNotificationStatus # Import enum for DB update

    db = SessionLocal()
    try:
        logger.info(f"Processing notification ID: {notification_id}, Type: {notification_type}, User ID: {user_id}")

        success = False
        if notification_type == "email":
            # In a real app, you'd get the user's email from their profile using user_id
            # For now, we assume recipient_address is the email if provided, or mock it.
            email_to = recipient_address # Mock email
            subject = f"Notification for User {user_id}"
            # success = _mock_send_email(email_to, subject, message)
            success = _send_actual_email(email_to, subject, message) # Use this for actual sending
        elif notification_type == "sms":
            # Similarly, get phone number from user profile or use recipient_address
            phone_to = recipient_address# Mock phone
            # success = _mock_send_sms(phone_to, message)
            success = _send_actual_sms(phone_to, message) # Uncomment for actual Twilio
            # logger.warning("Actual SMS sending is commented out. Using mock.")
            # success = _mock_send_sms(phone_to, message) # Keep mock for now unless Twilio is set up
        elif notification_type == "in-app":
            success = _handle_in_app_notification(user_id, message, notification_id)
        else:
            logger.error(f"Unknown notification type: {notification_type} for notification ID: {notification_id}")
            # Optionally update status to FAILED here if it's an unrecoverable type error
            update_notification_status(db, notification_id, DBNotificationStatus.FAILED)
            return # No retry for unknown type

        if success:
            logger.info(f"Notification ID: {notification_id} processed successfully. Updating status to SENT.")
            update_notification_status(db, notification_id, DBNotificationStatus.SENT)
            # For in-app, you might use DELIVERED if there's a distinction
            if notification_type == "in-app":
                 update_notification_status(db, notification_id, DBNotificationStatus.DELIVERED)
        else:
            # This part might not be reached if send functions raise exceptions for retries
            logger.warning(f"Notification ID: {notification_id} failed after processing. Status remains PENDING or will be retried.")
            # If not auto-retrying, explicitly set to FAILED
            # update_notification_status(db, notification_id, DBNotificationStatus.FAILED)


    except OperationalError as exc: # Broker connection error
        logger.error(f"Broker connection error for notification ID {notification_id}: {exc}. Retrying...")
        raise self.retry(exc=exc)
    except smtplib.SMTPException as exc: # Specific email error for retry
        logger.error(f"SMTP error for notification ID {notification_id}: {exc}. Retrying...")
        # update_notification_status(db, notification_id, DBNotificationStatus.FAILED) # Update to FAILED before retry
        raise self.retry(exc=exc, countdown=int(settings.TASK_RETRY_DEFAULT_DELAY * (self.request.retries + 1)))
    # except TwilioRestException as exc: # Specific SMS error for retry
    #     logger.error(f"Twilio error for notification ID {notification_id}: {exc}. Retrying...")
    #     # update_notification_status(db, notification_id, DBNotificationStatus.FAILED)
    #     raise self.retry(exc=exc, countdown=int(settings.TASK_RETRY_DEFAULT_DELAY * (self.request.retries + 1)))
    except Exception as exc:
        logger.error(f"Unexpected error processing notification ID {notification_id}: {exc}. Retrying if attempts left.")
        # update_notification_status(db, notification_id, DBNotificationStatus.FAILED) # Update to FAILED
        # Celery's autoretry_for or self.retry handles the retry logic.
        # If max_retries is reached, the task will eventually fail permanently.
        # It's good to have a mechanism to handle such "dead" tasks, e.g., moving them to a dead-letter queue.
        try:
            # Ensure status is FAILED if all retries are exhausted
            if self.request.retries >= settings.TASK_RETRY_MAX_RETRIES:
                 update_notification_status(db, notification_id, DBNotificationStatus.FAILED)
            else:
                # If we are here due to a non-auto-retried exception but still want to retry:
                raise self.retry(exc=exc, countdown=int(settings.TASK_RETRY_DEFAULT_DELAY * (self.request.retries + 1)))
        except Exception as final_exc:
            logger.critical(f"Failed to update status to FAILED or retry for notification ID {notification_id} after error: {final_exc}")
            # This is a fallback, ideally the retry logic handles it.
            if not db.is_active: # Re-establish session if it was closed due to error
                db = SessionLocal()
            update_notification_status(db, notification_id, DBNotificationStatus.FAILED)
            raise # Re-raise the original exception if not retrying
    finally:
        db.close()

# To run a Celery worker:
# celery -A tasks.celery_app worker -l info
# Ensure your broker (Redis/RabbitMQ) is running.