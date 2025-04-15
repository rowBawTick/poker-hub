# Poker Hud

A poker statistics and analysis tool that works with PokerStars hand history files. This application provides a comprehensive dashboard for tracking and analyzing your poker performance with a clean, modern interface.

## Features

- Automatic hand history collection and synchronization
- Hand parsing and analysis
- Statistics tracking and storage in SQLite database
- Vue.js frontend with interactive statistics dashboard
- Player performance metrics (VPIP, PFR, Aggression Factor, etc.)
- Recent hands tracking and profit/loss analysis
- PokerStars notes import and export functionality

## Project Structure

- `poker_hud/` - Main package
  - `collector/` - Hand history collection and monitoring
  - `parser/` - Hand history parsing
  - `storage/` - Database and persistence
  - `api/` - FastAPI endpoints for frontend communication
  - `poker_notes/` - PokerStars notes import/export functionality
- `frontend/` - Vue.js frontend application

## Requirements

### Backend
- Python 3.7+
- Dependencies listed in `requirements.txt`

### Frontend
- Node.js 14+
- npm 6+

## Setup

### 1. Backend Setup

1. Create and activate a virtual environment (recommended) from the project root:
   ```bash
    # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure the environment:
   - Create a `.env` file in the project root
   - Add your PokerStars hand history path:
     ```
     HAND_HISTORY_PATH=C:\Users\username\AppData\Local\PokerStars.UK\HandHistory\yourusername
     ```
     (Replace with your actual path)

3. Initialize the database:
   ```bash
   python main.py init-db
   ```

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install npm dependencies:
   ```bash
   npm install
   ```

## Running the Application

### 1. Starting the Backend

You have two options for running the backend:

#### Option A: Sync and Monitor (Recommended)

This will sync existing hand histories and then continuously monitor for new ones, while also starting the API server:

```bash
python main.py monitor
```

The API server will be available at http://localhost:8000

#### Option B: One-time Sync

If you only want to sync existing hand histories without starting the monitoring service:

```bash
python main.py sync
```

### 2. Starting the Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Start the development server:
   ```bash
   npm run serve
   ```

3. Access the application at http://localhost:8080

### 3. Using the Notes Functionality

The poker_notes module allows you to import and export PokerStars player notes.

1. Make sure your virtual environment is activated

2. Import notes from XML files:
   ```bash
   # From the project root
   cd backend
   python3 notes.py import <username> <path_to_xml_file> [<path_to_another_xml_file> ...]
   ```

3. Export notes to XML file:
   ```bash
   # From the project root
   cd backend
   python3 notes.py export <username> [--output <output_file_path>]
   ```

For more details, see the [Notes README](backend/poker_notes/README.md).

## Syncing Hand Histories

When you restart the application or want to manually sync your hand histories:

1. Run the sync command to process all new hand history files:
   ```bash
   python main.py sync
   ```

2. Or start the monitoring service which will automatically sync existing files first:
   ```bash
   python main.py monitor
   ```

## Using the Application

### Home Dashboard

The home dashboard displays:
- A list of all players found in your hand histories
- Recent hands with details like pot size, players, and winners

### Player Statistics

Click on any player name to view detailed statistics:
- Win rate and hands played
- Total winnings and average stack
- VPIP (Voluntarily Put Money In Pot) percentage
- PFR (Pre-Flop Raise) percentage
- Aggression Factor (AF)
- Recent results with profit/loss tracking

## Troubleshooting

### Hand Histories Not Being Found

1. Verify your hand history path in the `.env` file
2. Check if the files exist at the specified location
3. Run `python main.py parse <file_path>` on a specific file to test parsing

### API Connection Issues

1. Ensure the backend server is running (`python main.py monitor`)
2. Check that the API server is running at http://localhost:8000
3. Verify the proxy settings in `frontend/vue.config.js`


### Building for Production

```bash
cd frontend
npm run build
```

This will create a production-ready build in the `frontend/dist` directory.
