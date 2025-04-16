"""
Player model for storing poker player information.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Player(Base):
    """
    SQLAlchemy model for a poker player.
    """
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Relationships
    participations = relationship("HandParticipant", back_populates="player", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="player", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Player(name='{self.name}')>"
