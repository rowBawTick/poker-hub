#!/usr/bin/env python3
"""
Poker Notes Manager Script

This script provides a simple command-line interface for importing and exporting poker notes.
It can be run directly from the backend directory and delegates to the modular implementation.
"""
import sys
from pathlib import Path

# Import the poker_notes module
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.poker_notes.notes_manager import main

if __name__ == "__main__":
    sys.exit(main())
