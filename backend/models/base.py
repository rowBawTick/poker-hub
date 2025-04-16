"""
Base model configuration for SQLAlchemy models.
"""
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """
    Get a database session.
    
    Yields:
        SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
