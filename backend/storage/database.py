"""
Database module for storing poker hand data.
"""
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

from backend.config import DATABASE_URL

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Hand(Base):
    """
    SQLAlchemy model for a poker hand.
    """
    __tablename__ = "hands"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(String, unique=True, index=True)
    tournament_id = Column(String, index=True, nullable=True)
    game_type = Column(String)
    date_time = Column(DateTime)
    small_blind = Column(Float, nullable=False, default=0)
    big_blind = Column(Float, nullable=False, default=0)
    ante = Column(Float, nullable=True)
    pot = Column(Float)
    rake = Column(Float)
    board = Column(String)  # Stored as space-separated cards

    players = relationship("Player", back_populates="hand", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="hand", cascade="all, delete-orphan")
    winners = relationship("Winner", back_populates="hand", cascade="all, delete-orphan")


class Player(Base):
    """
    SQLAlchemy model for a player in a hand.
    """
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"))
    name = Column(String, index=True)
    seat = Column(Integer)
    stack = Column(Float)
    cards = Column(String, nullable=True)  # Stored as space-separated cards

    hand = relationship("Hand", back_populates="players")
    actions = relationship("Action", back_populates="player", cascade="all, delete-orphan")


class Action(Base):
    """
    SQLAlchemy model for a player action in a hand.
    """
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    action_type = Column(String)  # fold, check, call, bet, raise, all-in
    street = Column(String)  # preflop, flop, turn, river, showdown
    amount = Column(Float, nullable=True)
    is_all_in = Column(Boolean, default=False)
    sequence = Column(Integer)  # Order of actions in the hand

    hand = relationship("Hand", back_populates="actions")
    player = relationship("Player", back_populates="actions")


class Winner(Base):
    """
    SQLAlchemy model for a winner of a hand.
    """
    __tablename__ = "winners"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"))
    player_name = Column(String, index=True)
    amount = Column(Float)

    hand = relationship("Hand", back_populates="winners")


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
    status = Column(String)  # processed, error, etc.
    error_message = Column(Text, nullable=True)


class Database:
    """
    Database manager for storing and retrieving poker hand data.
    """

    def __init__(self):
        """
        Initialize the database manager.
        """
        self._create_tables()

    def _create_tables(self):
        """
        Create database tables if they don't exist.
        """
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")

    def get_session(self) -> Session:
        """
        Get a database session.

        Returns:
            SQLAlchemy session.
        """
        return SessionLocal()

    def close_session(self, session: Session):
        """
        Close a database session.

        Args:
            session: SQLAlchemy session to close.
        """
        session.close()

    def is_file_processed(self, file_path: str) -> bool:
        """
        Check if a hand history file has already been processed.

        Args:
            file_path: Path to the hand history file.

        Returns:
            True if the file has been processed, False otherwise.
        """
        session = self.get_session()
        try:
            result = session.query(HandFile).filter(HandFile.file_path == str(file_path)).first()
            return result is not None
        finally:
            self.close_session(session)

    def mark_file_processed(self, file_path: str, hand_count: int, status: str = "processed", error_message: Optional[str] = None):
        """
        Mark a hand history file as processed.

        Args:
            file_path: Path to the hand history file.
            hand_count: Number of hands processed from the file.
            status: Processing status.
            error_message: Error message if processing failed.
        """
        session = self.get_session()
        try:
            file_size = Path(file_path).stat().st_size
            hand_file = HandFile(
                file_path=str(file_path),
                processed_at=datetime.utcnow(),
                file_size=file_size,
                hand_count=hand_count,
                status=status,
                error_message=error_message
            )
            session.add(hand_file)
            session.commit()
            logger.info(f"Marked file as processed: {file_path}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error marking file as processed: {e}")
        finally:
            self.close_session(session)

    def store_hand(self, hand_data: Dict[str, Any]):
        """
        Store a parsed hand in the database.

        Args:
            hand_data: Dictionary containing parsed hand data.
        """
        session = self.get_session()
        try:
            # Check if hand already exists
            existing_hand = session.query(Hand).filter(Hand.hand_id == hand_data['hand_id']).first()
            if existing_hand:
                logger.debug(f"Hand already exists in database: {hand_data['hand_id']}")
                return

            # Create new hand
            hand = Hand(
                hand_id=hand_data['hand_id'],
                tournament_id=hand_data['tournament_id'],
                game_type=hand_data['game_type'],
                date_time=hand_data['date_time'],
                small_blind=float(hand_data['small_blind']) if hand_data['small_blind'] is not None else 0,
                big_blind=float(hand_data['big_blind']) if hand_data['big_blind'] is not None else 0,
                ante=hand_data.get('ante'),
                pot=hand_data['pot'],
                rake=hand_data['rake'],
                board=' '.join(hand_data['board']) if hand_data['board'] else None
            )
            session.add(hand)
            session.flush()  # Flush to get the hand ID

            # Add players
            player_objects = {}
            for player_name, player_data in hand_data['players'].items():
                # Check if the player showed cards at showdown
                showed_cards = player_data.get('showed_cards', False)
                
                player = Player(
                    hand_id=hand.id,
                    name=player_name,
                    seat=player_data['seat'],
                    stack=player_data['stack'],
                    cards=' '.join(player_data['cards']) if player_data['cards'] else None
                )
                session.add(player)
                session.flush()  # Flush to get the player ID
                player_objects[player_name] = player

            # Add actions
            for i, action_data in enumerate(hand_data['actions']):
                player = player_objects.get(action_data['player'])
                if player:
                    action = Action(
                        hand_id=hand.id,
                        player_id=player.id,
                        action_type=action_data['action'],
                        street=action_data['street'],
                        amount=action_data.get('amount'),
                        is_all_in=action_data.get('is_all_in', False),
                        sequence=i
                    )
                    session.add(action)

            # Add winners
            for winner_data in hand_data['winners']:
                winner = Winner(
                    hand_id=hand.id,
                    player_name=winner_data['player'],
                    amount=winner_data['amount']
                )
                session.add(winner)

            session.commit()
            logger.debug(f"Stored hand in database: {hand_data['hand_id']}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing hand: {e}")
        finally:
            self.close_session(session)

    def store_hands(self, hands: List[Dict[str, Any]]):
        """
        Store multiple parsed hands in the database.

        Args:
            hands: List of dictionaries containing parsed hand data.
        """
        for hand_data in hands:
            self.store_hand(hand_data)

        logger.info(f"Stored {len(hands)} hands in database")
