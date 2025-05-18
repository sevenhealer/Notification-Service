from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from config import settings

# --- Database Configuration ---
# Prefer environment variables for sensitive data
DATABASE_URL = settings.DATABASE_URL
# Example for local development: "postgresql://youruser:yourpassword@localhost/notification_db"
# For Docker Compose, it might be: "postgresql://user:password@db:5432/notificationdb"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to create tables (useful for initial setup, but Alembic is better for production)
# from models import Base # Assuming models.py is in the same directory
# def create_db_tables():
#     Base.metadata.create_all(bind=engine)

# if __name__ == "__main__":
#     # This can be run once to create tables if not using Alembic
#     print("Creating database tables...")
#     create_db_tables()
#     print("Database tables created (if they didn't exist).")