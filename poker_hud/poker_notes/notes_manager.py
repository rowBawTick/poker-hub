#!/usr/bin/env python3
"""
Poker Notes Manager Script

This script provides a command-line interface for importing and exporting poker notes.
It serves as the main entry point for the notes management functionality.
"""
import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List

# Set up path to ensure imports work correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import the modules
from poker_hud.poker_notes.import_notes import import_notes_from_files
from poker_hud.poker_notes.export_notes import export_notes_to_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def import_notes(args):
    """Import notes from XML files."""
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
        import_notes_from_files(args.username, valid_files)
        return 0
    except Exception as e:
        logger.error(f"Error importing notes: {e}")
        return 1


def export_notes(args):
    """Export notes to an XML file."""
    try:
        success = export_notes_to_file(args.username, args.output)
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Error exporting notes: {e}")
        return 1


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Manage poker notes.")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import notes from XML files")
    import_parser.add_argument("username", help="Username for the notes")
    import_parser.add_argument("files", nargs="+", help="XML files to import")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export notes to an XML file")
    export_parser.add_argument("username", help="Username for the notes")
    export_parser.add_argument("--output", "-o", help="Output file path. Default: notes.{username}.xml")
    
    args = parser.parse_args()
    
    if args.command == "import":
        return import_notes(args)
    elif args.command == "export":
        return export_notes(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
