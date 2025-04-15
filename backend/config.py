"""
Configuration module for the Poker Hud application.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Hand history path from environment variable or default
HAND_HISTORY_PATH = os.getenv('HAND_HISTORY_PATH')

# Database configuration
# Use absolute path to ensure consistent database location regardless of working directory
DATABASE_URL = os.getenv('DATABASE_URL', f'sqlite:///{BASE_DIR}/poker_hud.db')

# Application settings
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
