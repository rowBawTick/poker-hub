#!/usr/bin/env python3
"""
Poker Notes Import Script

This script imports poker player notes from multiple XML files and stores them in a SQLite database.
It supports user-based separation to ensure notes from different users don't get mixed up.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

# Handle imports for both module and direct script usage
try:
    # When imported as a module
    from ..config import DATABASE_URL
    from .db_utils import get_database_session, get_or_create_user, Label, Note
    from .xml_utils import parse_xml_file
except ImportError:
    # When run as a script
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from backend.config import DATABASE_URL
    from backend.poker_notes.db_utils import get_database_session, get_or_create_user, Label, Note
    from backend.poker_notes.xml_utils import parse_xml_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def import_labels(session: Session, user_id: int, labels_dict: Dict[int, Dict]) -> Dict[int, Label]:
    """
    Import labels into the database.
    
    Args:
        session: Database session.
        user_id: User ID.
        labels_dict: Dictionary of labels from XML.
        
    Returns:
        Dictionary mapping original label IDs to Label objects.
    """
    label_map = {}
    
    for xml_label_id, label_data in labels_dict.items():
        # Check if this label already exists for this user
        existing_label = session.query(Label).filter(
            Label.user_id == user_id,
            Label.label_id == xml_label_id
        ).first()
        
        if existing_label:
            # Update existing label if needed
            if (existing_label.color != label_data["color"] or 
                existing_label.name != label_data["name"]):
                existing_label.color = label_data["color"]
                existing_label.name = label_data["name"]
                session.add(existing_label)
                logger.info(f"Updated label {xml_label_id} for user {user_id}")
            
            label_map[xml_label_id] = existing_label
        else:
            # Create new label
            new_label = Label(
                user_id=user_id,
                label_id=xml_label_id,
                color=label_data["color"],
                name=label_data["name"]
            )
            session.add(new_label)
            label_map[xml_label_id] = new_label
            logger.info(f"Created new label {xml_label_id} for user {user_id}")
    
    # Commit changes
    session.commit()
    
    return label_map


def import_notes(session: Session, user_id: int, notes_list: List[Dict], label_map: Dict[int, Label]) -> int:
    """
    Import notes into the database.
    
    Args:
        session: Database session.
        user_id: User ID.
        notes_list: List of notes from XML.
        label_map: Dictionary mapping original label IDs to Label objects.
        
    Returns:
        Number of notes imported.
    """
    imported_count = 0
    
    for note_data in notes_list:
        player_name = note_data["player"]
        content = note_data["content"]
        xml_label_id = note_data["label_id"]
        updated = note_data["updated"]
        source_file = note_data["source_file"]
        
        # Get label ID from map
        label_id = None
        if xml_label_id in label_map:
            label_id = label_map[xml_label_id].id
        
        # Check if this note already exists for this user and player
        existing_note = session.query(Note).filter(
            Note.user_id == user_id,
            Note.player_name == player_name
        ).first()
        
        if existing_note:
            # If the existing note is older or the content is different, update it
            if existing_note.last_updated < updated or existing_note.content != content:
                # If content is different, append the new content
                if existing_note.content != content:
                    # Check if the new content is already part of the existing content
                    if content not in existing_note.content:
                        existing_note.content = f"{existing_note.content}\n\n{content}"
                        logger.info(f"Appended note content for player {player_name}")
                    
                # Update the last updated timestamp if newer
                if existing_note.last_updated < updated:
                    existing_note.last_updated = updated
                    
                # Update label if provided
                if label_id is not None:
                    existing_note.label_id = label_id
                
                existing_note.source_file = f"{existing_note.source_file}, {source_file}"
                session.add(existing_note)
                imported_count += 1
        else:
            # Create new note
            new_note = Note(
                user_id=user_id,
                label_id=label_id,
                player_name=player_name,
                content=content,
                last_updated=updated,
                source_file=source_file
            )
            session.add(new_note)
            imported_count += 1
            logger.info(f"Created new note for player {player_name}")
    
    # Commit changes
    session.commit()
    
    return imported_count


def import_notes_from_files(username: str, file_paths: List[str], database_url: str = DATABASE_URL) -> int:
    """
    Import notes from XML files into the database.
    
    Args:
        username: Username.
        file_paths: List of paths to XML files.
        database_url: Database URL.
        
    Returns:
        Total number of notes imported.
    """
    # Get database session
    session, _ = get_database_session(database_url)
    
    try:
        # Get or create user
        user = get_or_create_user(session, username)
        
        total_imported = 0
        
        # Process each file
        for file_path in file_paths:
            logger.info(f"Processing file: {file_path}")
            
            # Parse XML file
            labels_dict, notes_list = parse_xml_file(file_path)
            
            # Import labels
            label_map = import_labels(session, user.id, labels_dict)
            
            # Import notes
            imported_count = import_notes(session, user.id, notes_list, label_map)
            total_imported += imported_count
            
            logger.info(f"Imported {imported_count} notes from {file_path}")
        
        logger.info(f"Total notes imported: {total_imported}")
        return total_imported
        
    finally:
        # Close session
        session.close()


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Import poker notes from XML files.")
    parser.add_argument("username", help="Username for the notes.")
    parser.add_argument("files", nargs="+", help="XML files to import.")
    parser.add_argument("--db", default=DATABASE_URL, help="Database URL.")
    
    args = parser.parse_args()
    
    # Validate files
    valid_files = []
    for file_path in args.files:
        if os.path.isfile(file_path):
            valid_files.append(file_path)
        else:
            logger.warning(f"File not found: {file_path}")
    
    if not valid_files:
        logger.error("No valid files provided.")
        return 1
    
    # Import notes
    try:
        import_notes_from_files(args.username, valid_files, args.db)
        return 0
    except Exception as e:
        logger.error(f"Error importing notes: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
