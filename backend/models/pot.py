"""
Pot model for storing information about pots in a poker hand.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Pot(Base):
    """
    SQLAlchemy model for a pot in a poker hand.
    A hand can have a main pot and multiple side pots.
    """
    __tablename__ = "pots"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"), nullable=False, index=True)
    pot_type = Column(String, nullable=False)  # 'main', 'side-1', 'side-2', etc.
    amount = Column(Float, nullable=False)
    
    # Relationships
    hand = relationship("Hand", back_populates="pots")
    winners = relationship("PotWinner", back_populates="pot", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Pot(pot_type='{self.pot_type}', amount={self.amount})>"
