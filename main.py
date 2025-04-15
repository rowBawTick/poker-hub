"""
Main entry point for the Poker Hud application.
"""
import argparse
import logging
import sys
import time
from pathlib import Path

from backend.collector.history_collector import HandHistoryCollector
from backend.parser.hand_parser import HandParser
from backend.storage.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to INFO to reduce verbosity
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set specific loggers to DEBUG level
logging.getLogger('backend.storage.database').setLevel(logging.DEBUG)
logging.getLogger('backend.parser.hand_parser').setLevel(logging.DEBUG)


def sync_command(args):
    """
    Sync hand history files without starting the monitoring service.
    """
    logger.info("Starting hand history sync")
    
    # Initialize the database and ensure tables exist
    db = Database()
    logger.info("Creating database tables if they don't exist")
    db.create_tables()
    
    # Initialize the collector
    collector = HandHistoryCollector(args.history_path)

    # Log the number of hand history files found
    history_files = collector.get_history_files()
    logger.info(f"Found {len(history_files)} hand history files")

    # Print the first few files for verification
    if history_files:
        logger.info("Sample files:")
        for file in history_files[:5]:
            logger.info(f"  - {file.name}")

    # Sync the files
    num_processed = collector.sync_history_files()
    
    # Display database summary after sync
    session = db.get_session()
    try:
        from backend.storage.database import Hand, HandParticipant, Player, Action, Winner
        
        # Count records in each table
        tournament_count = session.query(Hand.tournament_id).distinct().count()
        player_count = session.query(Player).count()
        hand_count = session.query(Hand).count()
        action_count = session.query(Action).count()
        
        logger.info("Database summary:")
        logger.info(f"  - Tournaments: {tournament_count}")
        logger.info(f"  - Players: {player_count}")
        logger.info(f"  - Hands: {hand_count}")
        logger.info(f"  - Actions: {action_count}")
    except Exception as e:
        logger.error(f"Error getting database summary: {e}")
    finally:
        db.close_session(session)
    
    logger.info("Hand history sync completed")


def monitor_command(args):
    """
    Start monitoring hand history files and API server.
    """
    logger.info("Starting Poker Hud monitoring service")

    # Initialize and start the hand history collector
    collector = HandHistoryCollector(args.history_path)

    # Log the number of hand history files found
    history_files = collector.get_history_files()
    logger.info(f"Found {len(history_files)} hand history files")

    # Start monitoring for new files
    logger.info("Starting hand history monitoring...")
    collector.start_monitoring()

    # Start the API server in a separate thread
    import uvicorn
    import threading
    from backend.api.stats_api import app

    api_host = args.api_host
    api_port = args.api_port

    logger.info(f"Starting API server at http://{api_host}:{api_port}")
    api_thread = threading.Thread(
        target=uvicorn.run,
        kwargs={
            "app": app,
            "host": api_host,
            "port": api_port,
            "log_level": "info"
        },
        daemon=True
    )
    api_thread.start()

    # Keep the application running
    logger.info("Poker Hud is running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        # Clean up
        collector.stop_monitoring()
        logger.info("Poker Hud monitoring service stopped")


def parse_command(args):
    """
    Parse a specific hand history file without storing it.
    """
    logger.info(f"Parsing hand history file: {args.file}")

    # Initialize the parser
    parser = HandParser()

    # Parse the file
    hands = parser.parse_file(Path(args.file))

    # Print the results
    logger.info(f"Parsed {len(hands)} hands from file: {args.file}")

    if args.verbose:
        for i, hand in enumerate(hands[:5]):  # Show first 5 hands only
            logger.info(f"Hand {i+1}:")
            logger.info(f"  ID: {hand['hand_id']}")
            logger.info(f"  Date: {hand['date_time']}")
            logger.info(f"  Players: {list(hand['players'].keys())}")
            logger.info(f"  Board: {hand['board']}")
            logger.info(f"  Winners: {[w['player'] for w in hand['winners']]}")
            logger.info(f"  Pot: {hand['pot']}")


def init_db_command(args):
    """
    Initialize the database.
    """
    logger.info("Initializing database")

    # Initialize the database
    db = Database()

    logger.info("Database initialized")


def api_command(args):
    """
    Start only the API server without monitoring for new hand history files.
    """
    logger.info("Starting Poker Hud API server only")

    # Start the API server
    import uvicorn
    from backend.api.stats_api import app

    api_host = args.api_host
    api_port = args.api_port

    logger.info(f"Starting API server at http://{api_host}:{api_port}")
    logger.info("Poker Hud API is running. Press Ctrl+C to exit.")
    
    try:
        uvicorn.run(
            app=app,
            host=api_host,
            port=api_port,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        logger.info("Poker Hud API server stopped")


def check_db_command(args):
    """
    Check the database contents directly.
    """
    logger.info("Checking database contents")
    
    # Initialize the database
    db = Database()
    
    # Get a session
    session = db.get_session()
    try:
        from backend.storage.database import Hand, HandParticipant, Player, Action, Winner
        
        # Count records in each table
        hand_count = session.query(Hand).count()
        participant_count = session.query(HandParticipant).count()
        player_count = session.query(Player).count()
        action_count = session.query(Action).count()
        winner_count = session.query(Winner).count()
        
        logger.info("Database contents:")
        logger.info(f"  - Hands: {hand_count}")
        logger.info(f"  - Hand Participants: {participant_count}")
        logger.info(f"  - Players: {player_count}")
        logger.info(f"  - Actions: {action_count}")
        logger.info(f"  - Winners: {winner_count}")
        
        # List a few hands for verification
        if hand_count > 0:
            hands = session.query(Hand).order_by(Hand.id.desc()).limit(5).all()
            logger.info("Recent hands:")
            for hand in hands:
                logger.info(f"  - Hand ID: {hand.hand_id}, Tournament: {hand.tournament_id}, Game: {hand.game_type}")
                logger.info(f"    Participants: {len(hand.participants)}, Actions: {len(hand.actions)}, Winners: {len(hand.winners)}")
                
                # Show details of the first hand
                if hand == hands[0]:
                    logger.info("Detailed view of most recent hand:")
                    logger.info(f"  ID: {hand.id}")
                    logger.info(f"  Hand ID: {hand.hand_id}")
                    logger.info(f"  Tournament ID: {hand.tournament_id}")
                    logger.info(f"  Game Type: {hand.game_type}")
                    logger.info(f"  Date/Time: {hand.date_time}")
                    logger.info(f"  Small Blind: {hand.small_blind}")
                    logger.info(f"  Big Blind: {hand.big_blind}")
                    logger.info(f"  Ante: {hand.ante}")
                    logger.info(f"  Pot: {hand.pot}")
                    logger.info(f"  Rake: {hand.rake}")
                    logger.info(f"  Board: {hand.board}")
                    logger.info(f"  Button Seat: {hand.button_seat}")
                    logger.info(f"  Max Players: {hand.max_players}")
                    logger.info(f"  Table Name: {hand.table_name}")
                    
                    # Show participants
                    logger.info("  Participants:")
                    for p in hand.participants:
                        logger.info(f"    - ID: {p.id}, Player: {p.player.name if p.player else p.player_id}, Seat: {p.seat}, Stack: {p.stack}")
                    
                    # Show actions
                    logger.info("  Actions:")
                    for a in sorted(hand.actions, key=lambda x: x.sequence)[:5]:  # Show first 5 actions
                        logger.info(f"    - Seq: {a.sequence}, Type: {a.action_type}, Street: {a.street}, Amount: {a.amount}")
                    
                    # Show winners
                    logger.info("  Winners:")
                    for w in hand.winners:
                        logger.info(f"    - Player: {w.player_name}, Amount: {w.amount}")
        else:
            logger.info("No hands found in the database.")
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        db.close_session(session)
    
    logger.info("Database check completed")


def main():
    """
    Main entry point for the Poker Hud application.
    """
    parser = argparse.ArgumentParser(description="Poker Hud")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync hand history files")
    sync_parser.add_argument("--history-path", help="Path to hand history directory")
    sync_parser.set_defaults(func=sync_command)

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start monitoring for new hand history files")
    monitor_parser.add_argument("--history-path", help="Path to hand history directory")
    monitor_parser.add_argument("--api-host", default="localhost", help="Host for API server")
    monitor_parser.add_argument("--api-port", type=int, default=8000, help="Port for API server")
    monitor_parser.set_defaults(func=monitor_command)

    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse a hand history file")
    parse_parser.add_argument("file", help="Hand history file to parse")
    parse_parser.set_defaults(func=parse_command)

    # Initialize database command
    init_db_parser = subparsers.add_parser("init-db", help="Initialize the database")
    init_db_parser.set_defaults(func=init_db_command)

    # API command
    api_parser = subparsers.add_parser("api", help="Start the API server")
    api_parser.add_argument("--host", default="localhost", help="Host for API server")
    api_parser.add_argument("--port", type=int, default=8000, help="Port for API server")
    api_parser.set_defaults(func=api_command)
    
    # Check database command
    check_db_parser = subparsers.add_parser("check-db", help="Check database contents")
    check_db_parser.set_defaults(func=check_db_command)

    args = parser.parse_args()

    try:
        if args.command == "sync":
            sync_command(args)
        elif args.command == "monitor":
            monitor_command(args)
        elif args.command == "api":
            api_command(args)
        elif args.command == "parse":
            parse_command(args)
        elif args.command == "init-db":
            init_db_command(args)
        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Error in Poker Hud: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
