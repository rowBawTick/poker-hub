"""
API endpoints for retrieving poker statistics.
"""
import logging
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from poker_hud.storage.database import Database, Hand, Player, Action, Winner

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Poker Hud API", description="API for poker statistics")

# Database dependency
def get_db():
    db = Database()
    session = db.get_session()
    try:
        yield session
    finally:
        db.close_session(session)


@app.get("/api/players")
def get_players(db: Session = Depends(get_db)):
    """
    Get a list of all players in the database.
    """
    try:
        # Get unique player names
        players = db.query(Player.name).distinct().all()
        return {"players": [player[0] for player in players]}
    except Exception as e:
        logger.error(f"Error getting players: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/player/{player_name}/stats")
def get_player_stats(player_name: str, db: Session = Depends(get_db)):
    """
    Get statistics for a specific player.
    """
    try:
        # Count total hands played
        hands_played = db.query(func.count(Player.id)).filter(Player.name == player_name).scalar() or 0

        if hands_played == 0:
            raise HTTPException(status_code=404, detail=f"Player {player_name} not found")

        # Calculate win rate
        hands_won = db.query(func.count(Winner.id)).filter(Winner.player_name == player_name).scalar() or 0
        win_rate = (hands_won / hands_played) * 100 if hands_played > 0 else 0

        # Calculate total winnings
        total_winnings = db.query(func.sum(Winner.amount)).filter(Winner.player_name == player_name).scalar() or 0

        # Calculate average stack
        avg_stack = db.query(func.avg(Player.stack)).filter(Player.name == player_name).scalar() or 0

        # Calculate VPIP (Voluntarily Put Money In Pot)
        vpip_actions = db.query(func.count(Action.id)).filter(
            Action.player.has(name=player_name),
            Action.street == "preflop",
            Action.action_type.in_(["call", "bet", "raise"])
        ).scalar() or 0

        vpip = (vpip_actions / hands_played) * 100 if hands_played > 0 else 0

        # Calculate PFR (Pre-Flop Raise)
        pfr_actions = db.query(func.count(Action.id)).filter(
            Action.player.has(name=player_name),
            Action.street == "preflop",
            Action.action_type == "raise"
        ).scalar() or 0

        pfr = (pfr_actions / hands_played) * 100 if hands_played > 0 else 0

        # Calculate AF (Aggression Factor)
        aggressive_actions = db.query(func.count(Action.id)).filter(
            Action.player.has(name=player_name),
            Action.action_type.in_(["bet", "raise"])
        ).scalar() or 0

        passive_actions = db.query(func.count(Action.id)).filter(
            Action.player.has(name=player_name),
            Action.action_type == "call"
        ).scalar() or 0

        af = aggressive_actions / passive_actions if passive_actions > 0 else 0

        # Get recent hands
        recent_hands = db.query(Hand).join(Player).filter(
            Player.name == player_name
        ).order_by(desc(Hand.date_time)).limit(10).all()

        recent_results = []
        for hand in recent_hands:
            # Check if player won this hand
            won = any(winner.player_name == player_name for winner in hand.winners)

            # Calculate profit/loss for this hand
            profit = 0
            for winner in hand.winners:
                if winner.player_name == player_name:
                    profit += winner.amount

            # Find player's actions in this hand
            player_actions = [action for action in hand.actions
                             if action.player.name == player_name]

            # Calculate money invested
            money_invested = sum(action.amount or 0 for action in player_actions
                               if action.action_type in ["call", "bet", "raise"])

            profit -= money_invested

            recent_results.append({
                "hand_id": hand.hand_id,
                "date_time": hand.date_time.isoformat(),
                "won": won,
                "profit": profit,
                "pot": hand.pot
            })

        return {
            "player_name": player_name,
            "hands_played": hands_played,
            "hands_won": hands_won,
            "win_rate": win_rate,
            "total_winnings": total_winnings,
            "avg_stack": avg_stack,
            "vpip": vpip,
            "pfr": pfr,
            "af": af,
            "recent_results": recent_results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting player stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hands/recent")
def get_recent_hands(limit: int = 10, db: Session = Depends(get_db)):
    """
    Get the most recent hands.
    """
    try:
        hands = db.query(Hand).order_by(desc(Hand.date_time)).limit(limit).all()

        result = []
        for hand in hands:
            hand_data = {
                "hand_id": hand.hand_id,
                "date_time": hand.date_time.isoformat(),
                "game_type": hand.game_type,
                "pot": hand.pot,
                "players": [player.name for player in hand.players],
                "winners": [{"player": winner.player_name, "amount": winner.amount} for winner in hand.winners]
            }
            result.append(hand_data)

        return {"hands": result}
    except Exception as e:
        logger.error(f"Error getting recent hands: {e}")
        raise HTTPException(status_code=500, detail=str(e))
