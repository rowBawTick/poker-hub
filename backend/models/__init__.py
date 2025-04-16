"""
Models package for the poker-hud application.
"""
from backend.models.base import Base, engine, SessionLocal, get_db
from backend.models.hand_file import HandFile
from backend.models.tournament import Tournament
from backend.models.hand import Hand
from backend.models.player import Player
from backend.models.hand_participant import HandParticipant
from backend.models.pot import Pot
from backend.models.pot_winner import PotWinner
from backend.models.action import Action


def create_tables():
    """
    Create all database tables if they don't exist.
    """
    Base.metadata.create_all(bind=engine)
