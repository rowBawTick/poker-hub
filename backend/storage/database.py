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
    pot = Column(Float, nullable=True, default=0)
    rake = Column(Float, nullable=True, default=0)
    board = Column(String)  # Stored as space-separated cards
    button_seat = Column(Integer, nullable=True)  # Seat number of the button
    max_players = Column(Integer, nullable=True)  # Maximum number of players at the table
    table_name = Column(String, nullable=True)  # Name of the table

    participants = relationship("HandParticipant", back_populates="hand", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="hand", cascade="all, delete-orphan")
    winners = relationship("Winner", back_populates="hand", cascade="all, delete-orphan")


class Player(Base):
    """
    SQLAlchemy model for a poker player.
    This table stores unique players across all hands.
    """
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)  # Player name must be unique
    first_seen = Column(DateTime, default=datetime.utcnow)  # When we first saw this player
    last_seen = Column(DateTime, default=datetime.utcnow)  # Last time we saw this player
    
    # Relationships
    participations = relationship("HandParticipant", back_populates="player", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="player", cascade="all, delete-orphan")


class HandParticipant(Base):
    """
    SQLAlchemy model for a player's participation in a specific hand.
    This is a pivot table between Hand and Player that stores hand-specific player data.
    """
    __tablename__ = "hand_participants"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    seat = Column(Integer)  # Seat position at the table
    stack = Column(Float)  # Starting stack in this hand
    cards = Column(String, nullable=True)  # Hole cards (space-separated)
    bounty = Column(Float, nullable=True)  # Player's bounty in tournament
    is_small_blind = Column(Boolean, default=False)  # Whether player posted small blind
    is_big_blind = Column(Boolean, default=False)  # Whether player posted big blind
    is_button = Column(Boolean, default=False)  # Whether player is on the button
    showed_cards = Column(Boolean, default=False)  # Whether player showed cards at showdown
    final_stack = Column(Float, nullable=True)  # Final stack after the hand
    net_won = Column(Float, nullable=True)  # Net amount won/lost in this hand
    
    # Relationships
    hand = relationship("Hand", back_populates="participants")
    player = relationship("Player", back_populates="participations")
    actions = relationship("Action", back_populates="participant", foreign_keys="Action.participant_id")


class Action(Base):
    """
    SQLAlchemy model for a player action in a hand.
    """
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), index=True)
    participant_id = Column(Integer, ForeignKey("hand_participants.id"), nullable=True, index=True)
    action_type = Column(String)  # fold, check, call, bet, raise, all-in, ante, small_blind, big_blind
    street = Column(String)  # preflop, flop, turn, river, showdown
    amount = Column(Float, nullable=True)
    is_all_in = Column(Boolean, default=False)
    sequence = Column(Integer)  # Order of actions in the hand

    hand = relationship("Hand", back_populates="actions")
    player = relationship("Player", back_populates="actions")
    participant = relationship("HandParticipant", back_populates="actions", foreign_keys=[participant_id])


class Winner(Base):
    """
    SQLAlchemy model for a winner of a hand.
    """
    __tablename__ = "winners"

    id = Column(Integer, primary_key=True, index=True)
    hand_id = Column(Integer, ForeignKey("hands.id"), index=True)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=True, index=True)
    player_name = Column(String, index=True)  # Keep for backward compatibility
    participant_id = Column(Integer, ForeignKey("hand_participants.id"), nullable=True, index=True)
    amount = Column(Float)

    hand = relationship("Hand", back_populates="winners")
    player = relationship("Player", foreign_keys=[player_id], backref="winnings")
    participant = relationship("HandParticipant", foreign_keys=[participant_id], backref="winnings")


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
        self.engine = engine
        self.SessionLocal = SessionLocal

    def create_tables(self):
        """
        Create database tables if they don't exist.
        """
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    def get_session(self) -> Session:
        """
        Get a database session.

        Returns:
            SQLAlchemy session.
        """
        return self.SessionLocal()

    def close_session(self, session: Session):
        """
        Close a database session.

        Args:
            session: SQLAlchemy session to close.
        """
        session.close()
        
    def migrate_database(self):
        """
        Migrate the database schema to add new columns.
        
        This is a helper method to add new columns to existing tables without losing data.
        It's a simple implementation that checks if columns exist and adds them if they don't.
        """
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        
        # Check and add new columns to the hands table
        existing_columns = [col['name'] for col in inspector.get_columns('hands')]
        with self.engine.begin() as conn:
            if 'button_seat' not in existing_columns:
                conn.execute('ALTER TABLE hands ADD COLUMN button_seat INTEGER')
                logger.info("Added button_seat column to hands table")
            if 'max_players' not in existing_columns:
                conn.execute('ALTER TABLE hands ADD COLUMN max_players INTEGER')
                logger.info("Added max_players column to hands table")
            if 'table_name' not in existing_columns:
                conn.execute('ALTER TABLE hands ADD COLUMN table_name VARCHAR')
                logger.info("Added table_name column to hands table")
        
        # Check and add new columns to the players table
        existing_columns = [col['name'] for col in inspector.get_columns('players')]
        with self.engine.begin() as conn:
            if 'bounty' not in existing_columns:
                conn.execute('ALTER TABLE players ADD COLUMN bounty FLOAT')
                logger.info("Added bounty column to players table")
            if 'is_small_blind' not in existing_columns:
                conn.execute('ALTER TABLE players ADD COLUMN is_small_blind BOOLEAN DEFAULT FALSE')
                logger.info("Added is_small_blind column to players table")
            if 'is_big_blind' not in existing_columns:
                conn.execute('ALTER TABLE players ADD COLUMN is_big_blind BOOLEAN DEFAULT FALSE')
                logger.info("Added is_big_blind column to players table")
            if 'is_button' not in existing_columns:
                conn.execute('ALTER TABLE players ADD COLUMN is_button BOOLEAN DEFAULT FALSE')
                logger.info("Added is_button column to players table")
            if 'showed_cards' not in existing_columns:
                conn.execute('ALTER TABLE players ADD COLUMN showed_cards BOOLEAN DEFAULT FALSE')
                logger.info("Added showed_cards column to players table")
                
        logger.info("Database migration completed successfully.")

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
            # Track tournaments we've seen to avoid duplicate logging
            if not hasattr(self, '_processed_tournaments'):
                self._processed_tournaments = set()
                
            # Only log when processing a new tournament
            tournament_id = hand_data.get('tournament_id')
            if tournament_id and tournament_id not in self._processed_tournaments:
                self._processed_tournaments.add(tournament_id)
                logger.info(f"Processing tournament: {tournament_id} - {hand_data.get('game_type', '')}")
            
            # Check if hand already exists
            existing_hand = session.query(Hand).filter(Hand.hand_id == hand_data['hand_id']).first()
            if existing_hand:
                return

            # Create new hand with proper handling of None values
            hand = Hand(
                hand_id=hand_data['hand_id'],
                tournament_id=hand_data['tournament_id'],
                game_type=hand_data['game_type'],
                date_time=hand_data['date_time'],
                small_blind=float(hand_data['small_blind']) if hand_data['small_blind'] is not None else 0,
                big_blind=float(hand_data['big_blind']) if hand_data['big_blind'] is not None else 0,
                ante=hand_data.get('ante'),
                pot=hand_data.get('pot', 0),  # Default to 0 if missing
                rake=hand_data.get('rake', 0),  # Default to 0 if missing
                board=' '.join(hand_data['board']) if hand_data['board'] else None,
                button_seat=hand_data.get('button_seat'),
                max_players=hand_data.get('max_players'),
                table_name=hand_data.get('table_name')
            )
            session.add(hand)
            session.flush()  # Flush to get the hand ID

            # Dictionary to map participant IDs to their objects
            participant_objects = {}
            
            # Process participants (players in this specific hand)
            for participant_data in hand_data.get('participants', []):
                player_name = participant_data.get('player_name')
                
                # Find or create the global player record
                player = session.query(Player).filter(Player.name == player_name).first()
                if not player:
                    # Create a new player record if this is the first time we've seen them
                    player = Player(
                        name=player_name,
                        first_seen=hand_data['date_time'],
                        last_seen=hand_data['date_time']
                    )
                    session.add(player)
                else:
                    # Update the last_seen timestamp for existing players
                    player.last_seen = hand_data['date_time']
                
                session.flush()  # Ensure player has an ID
                
                # Create the hand participant record (player in this specific hand)
                participant = HandParticipant(
                    hand_id=hand.id,
                    player_id=player.id,
                    seat=participant_data['seat'],
                    stack=participant_data['stack'],
                    cards=' '.join(participant_data['cards']) if participant_data.get('cards') else None,
                    bounty=participant_data.get('bounty'),
                    is_small_blind=participant_data.get('is_small_blind', False),
                    is_big_blind=participant_data.get('is_big_blind', False),
                    is_button=participant_data.get('is_button', False),
                    showed_cards=participant_data.get('showed_cards', False),
                    final_stack=participant_data.get('final_stack'),
                    net_won=participant_data.get('net_won')
                )
                session.add(participant)
                session.flush()  # Ensure participant has an ID
                
                # Store the participant object for later reference
                participant_objects[participant_data['id']] = participant
            
            # Handle backwards compatibility with old format
            if not hand_data.get('participants') and hand_data.get('players'):
                # Old format with players as a dictionary
                if isinstance(hand_data['players'], dict):
                    for player_name, player_data in hand_data['players'].items():
                        # Find or create the global player record
                        player = session.query(Player).filter(Player.name == player_name).first()
                        if not player:
                            player = Player(
                                name=player_name,
                                first_seen=hand_data['date_time'],
                                last_seen=hand_data['date_time']
                            )
                            session.add(player)
                        else:
                            player.last_seen = hand_data['date_time']
                        
                        session.flush()
                        
                        # Create the hand participant record
                        participant = HandParticipant(
                            hand_id=hand.id,
                            player_id=player.id,
                            seat=player_data['seat'],
                            stack=player_data['stack'],
                            cards=' '.join(player_data['cards']) if player_data.get('cards') else None,
                            bounty=player_data.get('bounty'),
                            is_small_blind=player_data.get('is_small_blind', False),
                            is_big_blind=player_data.get('is_big_blind', False),
                            is_button=player_data.get('is_button', False),
                            showed_cards=player_data.get('showed_cards', False)
                        )
                        session.add(participant)
                        session.flush()
                        
                        # Store for action mapping
                        participant_objects[player_name] = participant
                # New format with players as a list
                elif isinstance(hand_data['players'], list):
                    for player_data in hand_data['players']:
                        player_name = player_data.get('name')
                        
                        # Find or create the global player record
                        player = session.query(Player).filter(Player.name == player_name).first()
                        if not player:
                            player = Player(
                                name=player_name,
                                first_seen=hand_data['date_time'],
                                last_seen=hand_data['date_time']
                            )
                            session.add(player)
                        else:
                            player.last_seen = hand_data['date_time']
                        
                        session.flush()
                        
                        # Create the hand participant record
                        participant = HandParticipant(
                            hand_id=hand.id,
                            player_id=player.id,
                            seat=player_data['seat'],
                            stack=player_data['stack'],
                            cards=' '.join(player_data['cards']) if player_data.get('cards') else None,
                            bounty=player_data.get('bounty'),
                            is_small_blind=player_data.get('is_small_blind', False),
                            is_big_blind=player_data.get('is_big_blind', False),
                            is_button=player_data.get('is_button', False),
                            showed_cards=player_data.get('showed_cards', False)
                        )
                        session.add(participant)
                        session.flush()
                        
                        # Store for action mapping
                        participant_objects[player_data.get('id', player_name)] = participant

            # Add actions
            for i, action_data in enumerate(hand_data.get('actions', [])):
                # Find the participant for this action
                participant = None
                
                # Try to find by participant_id first (new format)
                if action_data.get('participant_id') and action_data['participant_id'] in participant_objects:
                    participant = participant_objects[action_data['participant_id']]
                
                # Fall back to player_name (both formats)
                elif action_data.get('player_name'):
                    # Try to find by player_name in participant_objects
                    for p in participant_objects.values():
                        if hasattr(p, 'player') and p.player and p.player.name == action_data['player_name']:
                            participant = p
                            break
                
                # Fall back to 'player' field (old format)
                elif action_data.get('player') and action_data['player'] in participant_objects:
                    participant = participant_objects[action_data['player']]
                
                if participant:
                    # Create the action record
                    action = Action(
                        hand_id=hand.id,
                        player_id=participant.player_id,
                        participant_id=participant.id,
                        action_type=action_data.get('action_type', action_data.get('action')),  # Support both formats
                        street=action_data['street'],
                        amount=action_data.get('amount'),
                        is_all_in=action_data.get('is_all_in', False),
                        sequence=action_data.get('sequence', i)  # Use provided sequence or index
                    )
                    session.add(action)

            # Add winners
            for winner_data in hand_data.get('winners', []):
                # Find the participant for this winner
                participant = None
                
                # Try to find by participant_id first (new format)
                if winner_data.get('participant_id') and winner_data['participant_id'] in participant_objects:
                    participant = participant_objects[winner_data['participant_id']]
                
                # Fall back to player_name (both formats)
                elif winner_data.get('player_name'):
                    # Try to find by player_name in participant_objects
                    for p in participant_objects.values():
                        if hasattr(p, 'player') and p.player and p.player.name == winner_data['player_name']:
                            participant = p
                            break
                
                # Fall back to 'player' field (old format)
                elif winner_data.get('player') and winner_data['player'] in participant_objects:
                    participant = participant_objects[winner_data['player']]
                
                # Create the winner record
                winner = Winner(
                    hand_id=hand.id,
                    player_name=winner_data.get('player_name', winner_data.get('player')),  # Support both formats
                    amount=winner_data['amount']
                )
                
                # Add player and participant references if available
                if participant:
                    winner.player_id = participant.player_id
                    winner.participant_id = participant.id
                
                session.add(winner)

            # Commit the transaction
            session.commit()
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error storing hand {hand_data.get('hand_id')}: {e}")
            
        finally:
            self.close_session(session)

    def store_hands(self, hands: List[Dict[str, Any]]):
        """
        Store multiple parsed hands in the database.

        Args:
            hands: List of dictionaries containing parsed hand data.
        """
        # Initialize counters
        stats = {
            'tournaments': set(),
            'players': set(),
            'hands': 0,
            'actions': 0,
            'participants': 0
        }
        
        # Process each hand
        for hand_data in hands:
            # Update statistics
            if hand_data.get('tournament_id'):
                stats['tournaments'].add(hand_data['tournament_id'])
            
            for participant in hand_data.get('participants', []):
                player_name = participant.get('name')
                if player_name:
                    stats['players'].add(player_name)
            
            stats['hands'] += 1
            stats['actions'] += len(hand_data.get('actions', []))
            stats['participants'] += len(hand_data.get('participants', []))
            
            # Store the hand
            self.store_hand(hand_data)

        # Log summary in the requested order
        logger.info("Processing summary:")
        
        if stats['tournaments']:
            tournament_str = f"{len(stats['tournaments'])} tournament{'s' if len(stats['tournaments']) != 1 else ''}"
            if len(stats['tournaments']) <= 3:
                tournament_ids = ', '.join(sorted(stats['tournaments']))
                tournament_str += f" ({tournament_ids})"
            
            logger.info(f"  - Tournaments: {tournament_str}")
            
        logger.info(f"  - Players: {len(stats['players'])}")
        
        logger.info(f"  - Hands: {stats['hands']}")
        
        logger.info(f"  - Actions: {stats['actions']}")
        
        logger.info(f"  - Participants: {stats['participants']}")
