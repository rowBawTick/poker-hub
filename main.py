"""
Main entry point for the Poker Hub application.
"""
import argparse
import logging
import sys
import time
from pathlib import Path

from poker_hub.collector.history_collector import HandHistoryCollector
from poker_hub.parser.hand_parser import HandParser
from poker_hub.storage.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def sync_command(args):
    """
    Sync hand history files without starting the monitoring service.
    """
    logger.info("Starting hand history sync")

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
    logger.info(f"Processed {num_processed} new hand history files")
    logger.info("Hand history sync completed")


def monitor_command(args):
    """
    Start monitoring hand history files.
    """
    logger.info("Starting Poker Hub monitoring service")

    # Initialize and start the hand history collector
    collector = HandHistoryCollector(args.history_path)

    # Log the number of hand history files found
    history_files = collector.get_history_files()
    logger.info(f"Found {len(history_files)} hand history files")

    # Start monitoring for new files
    logger.info("Starting hand history monitoring...")
    collector.start_monitoring()

    # Keep the application running
    logger.info("Poker Hub is running. Press Ctrl+C to exit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        # Clean up
        collector.stop_monitoring()
        logger.info("Poker Hub monitoring service stopped")


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


def main():
    """
    Main entry point for the Poker Hub application.
    """
    parser = argparse.ArgumentParser(description="Poker Hub - A poker statistics and analysis tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync hand history files")
    sync_parser.add_argument("--history-path", help="Path to hand history directory")

    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Start monitoring hand history files")
    monitor_parser.add_argument("--history-path", help="Path to hand history directory")

    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse a hand history file")
    parse_parser.add_argument("file", help="Path to hand history file")
    parse_parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")

    # Init DB command
    init_db_parser = subparsers.add_parser("init-db", help="Initialize the database")

    args = parser.parse_args()

    try:
        if args.command == "sync":
            sync_command(args)
        elif args.command == "monitor":
            monitor_command(args)
        elif args.command == "parse":
            parse_command(args)
        elif args.command == "init-db":
            init_db_command(args)
        else:
            parser.print_help()

    except Exception as e:
        logger.error(f"Error in Poker Hub: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
