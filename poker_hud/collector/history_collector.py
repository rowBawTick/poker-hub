"""
Hand history collector module for monitoring and syncing PokerStars hand history files.
"""
import os
import logging
from pathlib import Path
from typing import List, Optional, Set
from datetime import datetime
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
from dotenv import load_dotenv

from poker_hud.parser.hand_parser import HandParser
from poker_hud.storage.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class HandHistoryCollector:
    """
    Collects and monitors PokerStars hand history files.
    """
    def __init__(self, history_path: Optional[str] = None):
        """
        Initialize the hand history collector.

        Args:
            history_path: Path to the PokerStars hand history directory.
                          If None, uses the path from environment variables.
        """
        self.history_path = history_path or os.getenv('HAND_HISTORY_PATH')
        if not self.history_path:
            raise ValueError("Hand history path not provided and not found in environment variables")

        self.history_path = Path(self.history_path)
        if not self.history_path.exists():
            raise FileNotFoundError(f"Hand history path does not exist: {self.history_path}")

        self.processed_files: Set[str] = set()
        self.observer: Optional[Observer] = None
        self.parser = HandParser()
        self.database = Database()

        # Load already processed files from database
        self._load_processed_files()

        logger.info(f"Hand history collector initialized with path: {self.history_path}")

    def _load_processed_files(self) -> None:
        """
        Load the list of already processed files from the database.
        """
        session = self.database.get_session()
        try:
            from poker_hud.storage.database import HandFile
            processed_files = session.query(HandFile.file_path).all()
            for file_path, in processed_files:
                self.processed_files.add(file_path)
            logger.info(f"Loaded {len(self.processed_files)} processed files from database")
        except Exception as e:
            logger.error(f"Error loading processed files: {e}")
        finally:
            self.database.close_session(session)

    def get_history_files(self) -> List[Path]:
        """
        Get all hand history files in the configured directory.

        Returns:
            List of Path objects for all hand history files.
        """
        # PokerStars hand history files typically have a .txt extension
        return sorted(self.history_path.glob("*.txt"))

    def process_file(self, file_path: Path) -> None:
        """
        Process a single hand history file.

        Args:
            file_path: Path to the hand history file.
        """
        file_path_str = str(file_path)

        # Skip if already processed
        if file_path_str in self.processed_files or self.database.is_file_processed(file_path_str):
            logger.debug(f"File already processed: {file_path}")
            return

        logger.info(f"Processing hand history file: {file_path}")

        try:
            hands = self.parser.parse_file(file_path)
            self.database.store_hands(hands)
            self.database.mark_file_processed(file_path_str, len(hands))
            self.processed_files.add(file_path_str)

            logger.info(f"Successfully processed file with {len(hands)} hands: {file_path}")
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            # Mark as error in database
            self.database.mark_file_processed(file_path_str, 0, "error", str(e))

    def sync_history_files(self) -> int:
        """
        Sync all hand history files in the configured directory.

        Returns:
            Number of files processed.
        """
        files = self.get_history_files()
        count = 0

        for file_path in files:
            if str(file_path) not in self.processed_files:
                self.process_file(file_path)
                count += 1

        logger.info(f"Synced {count} new hand history files")
        return count

    def start_monitoring(self) -> None:
        """
        Start monitoring the hand history directory for new files.
        """
        if self.observer:
            logger.warning("Observer already running")
            return

        # First, sync existing files
        self.sync_history_files()

        # Set up the file system event handler
        event_handler = HandHistoryEventHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.history_path), recursive=False)
        self.observer.start()

        logger.info(f"Started monitoring hand history directory: {self.history_path}")

    def stop_monitoring(self) -> None:
        """
        Stop monitoring the hand history directory.
        """
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            logger.info("Stopped monitoring hand history directory")


class HandHistoryEventHandler(FileSystemEventHandler):
    """
    Event handler for hand history file changes.
    """
    def __init__(self, collector: HandHistoryCollector):
        """
        Initialize the event handler.

        Args:
            collector: The hand history collector instance.
        """
        self.collector = collector

    def on_created(self, event):
        """
        Handle file creation events.

        Args:
            event: The file system event.
        """
        if not event.is_directory and event.src_path.endswith('.txt'):
            logger.info(f"New hand history file detected: {event.src_path}")
            self.collector.process_file(Path(event.src_path))

    def on_modified(self, event):
        """
        Handle file modification events.

        Args:
            event: The file system event.
        """
        if not event.is_directory and event.src_path.endswith('.txt'):
            logger.info(f"Hand history file modified: {event.src_path}")
            self.collector.process_file(Path(event.src_path))


def main():
    """
    Main function to demonstrate the hand history collector.
    """
    try:
        collector = HandHistoryCollector()
        logger.info(f"Found {len(collector.get_history_files())} hand history files")

        # Sync existing files
        num_processed = collector.sync_history_files()
        logger.info(f"Processed {num_processed} new hand history files")

        # Start monitoring for new files
        collector.start_monitoring()

        # Keep the script running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, stopping...")
        finally:
            collector.stop_monitoring()

    except Exception as e:
        logger.error(f"Error in hand history collector: {e}")
        raise


if __name__ == "__main__":
    main()
