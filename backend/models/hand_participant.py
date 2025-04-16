"""
HandParticipant model for tracking players participating in a hand.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from backend.models.base import Base


class HandParticipant(Base):
    """
    SQLAlchemy model for a player's participation in a specific hand.
    This is a pivot table between Hand and Player that stores hand-specific player data.
    """
    __tablename__ = "hand_participants"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    seat = Column(Integer)
    stack = Column(Float)
    cards = Column(String, nullable=True)  # Stored as space-separated cards
    is_button = Column(Boolean, default=False)
    is_small_blind = Column(Boolean, default=False)
    is_big_blind = Column(Boolean, default=False)
    showed_cards = Column(Boolean, default=False)
    net_profit = Column(Float, nullable=True)
    
    # Relationships
    hand = relationship("Hand", back_populates="participants")
    player = relationship("Player", back_populates="participations")
    actions = relationship("Action", back_populates="participant")
    pot_winnings = relationship("PotWinner", back_populates="participant")
    
    def __repr__(self):
        return f"<HandParticipant(player='{self.player.name if self.player else None}', seat={self.seat})>"
