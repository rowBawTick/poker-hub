"""
Hand model for storing poker hand information.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Hand(Base):
    """
    SQLAlchemy model for a poker hand.
    """
    __tablename__ = "hands"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(String, unique=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True, index=True)
    small_blind = Column(Float, nullable=False, default=0)
    big_blind = Column(Float, nullable=False, default=0)
    ante = Column(Float, nullable=True, default=0)
    pot = Column(Float, nullable=True, default=0)
    rake = Column(Float, nullable=True, default=0)
    board = Column(String, nullable=True)  # Stored as space-separated cards
    button_seat = Column(Integer, nullable=True)
    table_name = Column(String, nullable=True)
    date_time = Column(DateTime)
    
    # Relationships
    tournament = relationship("Tournament", back_populates="hands")
    participants = relationship("HandParticipant", back_populates="hand", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="hand", cascade="all, delete-orphan")
    pots = relationship("Pot", back_populates="hand", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Hand(hand_id='{self.hand_id}', date_time='{self.date_time}')>"
