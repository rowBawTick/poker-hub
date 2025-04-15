# Poker Hud

A poker statistics and analysis tool that works with PokerStars hand history files. 
This application provides a dashboard for tracking and analyzing your poker performance.
It also provides functionality for adding/merging your poker notes from different files and exporting to an xml file
that can be uploaded to PokerStars. 

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

1. Create a virtual environment and activate it (the only time to specify python3)
   ```bash
   python3 -m venv venv
   # On Mac: 
   source venv/bin/activate  
   # On Windows: 
   venv\Scripts\activate
   ```

2. Install dependencies and the backend package in development mode:
   ```bash
   pip install -r backend/requirements.txt
   pip install -e backend
   ```
   
   This installs the backend package in development mode, which allows you to make changes to the code without having to reinstall it.

3. Configure the environment:
   - Create your `.env` file by copying the `.env.example` file in the project root and add your PokerStars hand 
   history path 

4. Initialize the database:
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
   python notes.py import <username> <path_to_xml_file> [<path_to_another_xml_file> ...]
   ```

3. Export notes to XML file:
   ```bash
   # From the project root
   cd backend
   python notes.py export <username> [--output <output_file_path>]
   ```

For more details, see the [Notes README](backend/poker_notes/README.md).

## Testing

### Running All Tests

```bash
# Make sure your virtual environment is activated and backend package is installed
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e backend  # Only needed first time

# Run all tests from the project root
python -m unittest discover -s backend/tests
```

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
