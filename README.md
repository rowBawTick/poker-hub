# Poker Hub

A poker statistics and analysis tool that works with PokerStars hand history files.

## Features

- Automatic hand history collection and synchronization
- Hand parsing and analysis
- Statistics tracking and storage
- Vue.js frontend with Electron for overlay capabilities

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Configure the `.env` file with your PokerStars hand history path

3. Run the application:
   ```
   python -m poker_hub
   ```

## Project Structure

- `poker_hub/` - Main package
  - `collector/` - Hand history collection and monitoring
  - `parser/` - Hand history parsing
  - `analyzer/` - Statistical analysis
  - `storage/` - Database and persistence
  - `api/` - FastAPI endpoints for frontend communication
