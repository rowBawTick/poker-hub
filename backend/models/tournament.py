"""
Tournament model for storing poker tournament information.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from backend.models.base import Base


class Tournament(Base):
    """
    SQLAlchemy model for a poker tournament.
    """
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(String, unique=True, index=True)
    game_type = Column(String)
    max_players_per_table = Column(Integer)
    
    # Relationships
    hands = relationship("Hand", back_populates="tournament", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Tournament(tournament_id='{self.tournament_id}', game_type='{self.game_type}')>"
