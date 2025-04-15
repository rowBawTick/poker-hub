# Poker Notes Manager

This module provides functionality for importing and exporting poker player notes between PokerStars XML files and 
the application's database.

## Overview

The Poker Notes Manager allows you to:

1. Import player notes from PokerStars XML files
2. Export player notes to PokerStars-compatible XML files
3. Merge notes from multiple sources without losing data
4. Maintain separation between different Poker Stars users' notes

## File Structure

- `db_utils.py` - Database models and utilities
- `xml_utils.py` - XML parsing and generation utilities
- `import_notes.py` - Note import functionality
- `export_notes.py` - Note export functionality
- `notes_manager.py` - Command-line interface

## Setup

### Prerequisites

1. Make sure you have Python 3.7+ installed
2. Create and activate a virtual environment:

```bash
# From the project root (specifying python3 here but can drop it after)
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Importing Notes

Import notes from one or more XML files:

```bash
# From the project root
cd backend
python notes.py import <username> <path_to_xml_file> [<path_to_another_xml_file> ...]
```

Example:
```bash
python notes.py import waromano poker_notes/notes.waromano-old.xml poker_notes/notes.waromano-new.xml
```

This will:
- Parse the XML files
- Extract player notes and labels
- Store them in the database
- Merge notes for the same player instead of overwriting
- Keep notes separated by username

### Exporting Notes

Export notes to a PokerStars-compatible XML file:

```bash
# From the project root
cd backend
python notes.py export <username> [--output <output_file_path>]
```

Example:
```bash
python notes.py export waromano
```

This will create a file named `notes.waromano.xml` in the current directory.

You can also specify a custom output path:
```bash
python notes.py export waromano --output /path/to/my-notes.xml
```

## Note Merging Behavior

When importing notes for a player that already has notes in the database:

1. If the content is different, the new content is appended to the existing content
2. Duplicate content is not added
3. The most recent timestamp is used
4. Source file information is preserved

## Database Integration

The notes are stored in the same database specified in the main application's `config.py` file. This ensures all data is kept in a single location.

## Troubleshooting

### Import/Export Not Working

1. Make sure your virtual environment is activated
2. Verify that all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Check that the XML files exist and are in the correct format
4. Ensure you have the correct permissions to read/write files

### Database Connection Issues

1. Check that the database URL in `config.py` is correct
2. Verify that the database exists and is accessible
3. Make sure the necessary tables are created (they should be created automatically)

## Development

If you want to extend or modify the notes functionality:

1. The code follows a modular design with clear separation of concerns
2. Each file has a single responsibility
3. The database models are defined in `db_utils.py`
4. XML parsing and generation are handled in `xml_utils.py`
5. The command-line interface is defined in `notes_manager.py`
