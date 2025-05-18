from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "Notification Service"
    DEBUG_MODE: bool = False

    DATABASE_URL: str = os.getenv("DATABASE_URL")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND")

    EMAIL_HOST: str = os.getenv("EMAIL_HOST")
    EMAIL_PORT: int = os.getenv("EMAIL_PORT")
    EMAIL_USERNAME: str = os.getenv("EMAIL_USERNAME")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD")
    EMAIL_FROM_ADDRESS: str = os.getenv("EMAIL_FROM_ADDRESS")
    USE_TLS: bool = True

    TWILIO_ACCOUNT_SID: str = "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    TWILIO_AUTH_TOKEN: str = "your_auth_token"
    TWILIO_FROM_NUMBER: str = "+1234567890"

    TASK_RETRY_MAX_RETRIES: int = 3
    TASK_RETRY_DEFAULT_DELAY: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()
