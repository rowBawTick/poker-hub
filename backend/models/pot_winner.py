"""
PotWinner model for tracking winners of pots in a poker hand.
"""
from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.base import Base


class PotWinner(Base):
    """
    SQLAlchemy model for a winner of a specific pot.
    This allows for split pots where multiple players win portions of the same pot.
    """
    __tablename__ = "pot_winners"

    id = Column(Integer, primary_key=True, index=True)
    pot_id = Column(Integer, ForeignKey("pots.id"), nullable=False, index=True)
    participant_id = Column(Integer, ForeignKey("hand_participants.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    
    # Relationships
    pot = relationship("Pot", back_populates="winners")
    participant = relationship("HandParticipant", back_populates="pot_winnings")
    
    def __repr__(self):
        return f"<PotWinner(amount={self.amount})>"
