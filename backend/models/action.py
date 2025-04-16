"""
Action model for storing player actions in a poker hand.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Action(Base):
    """
    SQLAlchemy model for a player action in a hand.
    """
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"), index=True)
    participant_id = Column(Integer, ForeignKey("hand_participants.id"), index=True)
    street = Column(String)  # 'preflop', 'flop', 'turn', 'river', 'showdown'
    action_type = Column(String)  # 'fold', 'check', 'call', 'bet', 'raise', 'all-in', etc.
    amount = Column(Float, nullable=True)
    sequence = Column(Integer)  # Order of actions in the hand
    is_all_in = Column(Boolean, default=False)
    
    # Relationships
    hand = relationship("Hand", back_populates="actions")
    participant = relationship("HandParticipant", back_populates="actions")
    
    def __repr__(self):
        return f"<Action(action_type='{self.action_type}', street='{self.street}', amount={self.amount})>"
