#!/usr/bin/env python3
"""
Poker Notes Export Script

This script exports poker player notes from the SQLite database to XML files
in a format compatible with PokerStars.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

# Handle imports for both module and direct script usage
try:
    # When imported as a module
    from ..config import DATABASE_URL
    from .db_utils import get_database_session, get_or_create_user, Label, Note
    from .xml_utils import generate_xml, write_xml_to_file
except ImportError:
    # When run as a script
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from backend.config import DATABASE_URL
    from backend.poker_notes.db_utils import get_database_session, get_or_create_user, Label, Note
    from backend.poker_notes.xml_utils import generate_xml, write_xml_to_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_user_notes_and_labels(session: Session, username: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Get all notes and labels for a user.
    
    Args:
        session: Database session.
        username: Username.
        
    Returns:
        Tuple of (notes_list, labels_list).
    """
    # Get user
    user = get_or_create_user(session, username)
    
    # Get labels
    labels_query = session.query(Label).filter(Label.user_id == user.id)
    labels = []
    
    for label in labels_query:
        labels.append({
            "label_id": label.label_id,
            "color": label.color,
            "name": label.name
        })
    
    # Get notes
    notes_query = session.query(Note).filter(Note.user_id == user.id)
    notes = []
    
    for note in notes_query:
        notes.append({
            "player_name": note.player_name,
            "label_id": note.label_id,
            "content": note.content,
            "last_updated": note.last_updated
        })
    
    return notes, labels


def export_notes_to_file(username: str, output_file: str = None, database_url: str = DATABASE_URL) -> bool:
    """
    Export notes from the database to an XML file.
    
    Args:
        username: Username.
        output_file: Output file path. If None, uses the default format "notes.{username}.xml".
        database_url: Database URL.
        
    Returns:
        True if successful, False otherwise.
    """
    # Get database session
    session, _ = get_database_session(database_url)
    
    try:
        # Get notes and labels
        notes, labels = get_user_notes_and_labels(session, username)
        
        if not notes:
            logger.warning(f"No notes found for user {username}")
            return False
        
        # Generate XML
        root = generate_xml(username, labels, notes)
        
        # Determine output file path
        if not output_file:
            output_file = f"notes.{username}.xml"
        
        # Write XML to file
        success = write_xml_to_file(root, output_file)
        
        if success:
            logger.info(f"Exported {len(notes)} notes to {output_file}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error exporting notes: {e}")
        return False
        
    finally:
        # Close session
        session.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Export poker notes to XML file.")
    parser.add_argument("username", help="Username for the notes.")
    parser.add_argument("--output", "-o", help="Output file path. Default: notes.{username}.xml")
    parser.add_argument("--db", default=DATABASE_URL, help="Database URL.")
    
    args = parser.parse_args()
    
    # Export notes
    try:
        success = export_notes_to_file(args.username, args.output, args.db)
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Error exporting notes: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
