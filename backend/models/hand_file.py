"""
HandFile model for tracking processed hand history files.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text

from backend.models.base import Base


class HandFile(Base):
    """
    SQLAlchemy model for tracking processed hand history files.
    """
    __tablename__ = "hand_files"

    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String, unique=True, index=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    file_size = Column(Integer)
    hand_count = Column(Integer)
    status = Column(String)
    error_message = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<HandFile(file_path='{self.file_path}', status='{self.status}')>"
