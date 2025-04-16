"""
Player parser component for extracting player information from poker hand histories.
"""
import re
import logging
from typing import Dict, List, Any, Optional

from backend.parser.components.base_parser import BaseParser

logger = logging.getLogger(__name__)


class PlayerParser(BaseParser):
    """
    Parser component for extracting player information from poker hand histories.
    """
    
    # Pattern for player information with seat number and stack
    PLAYER_PATTERN = re.compile(
        r"Seat (\d+): (.*?) \(\$?([\d,]+(?:\.\d+)?) in chips(?:, \$?([\d.]+) bounty)?\)"
    )
    
    # Pattern for hole cards
    HOLE_CARDS_PATTERN = re.compile(r"Dealt to (.*?) \[(.*?)\]")
    
    # Pattern for showdown
    SHOWDOWN_PATTERN = re.compile(r"(.*?): shows \[(.*?)\]")
    
    def __init__(self):
        """Initialize the player parser component."""
        super().__init__()
    
    def parse_hand(self, hand_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse player information from a single hand history.
        
        Args:
            hand_text: Text of a single poker hand history.
            
        Returns:
            Dictionary containing player data, or None if parsing failed.
        """
        # Skip empty hands
        if not hand_text.strip():
            return None
        
        lines = hand_text.strip().split('\n')
        return self.parse_hand_participant_lines(lines)
    
    def parse_hand_participant_lines(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse player information from hand history lines.
        
        Args:
            lines: List of lines from a hand history.
            
        Returns:
            Dictionary containing player data and remaining lines, or None if parsing failed.
        """
        if not lines:
            return None
        
        # Parse players
        players = self._parse_players(lines)
        if not players:
            logger.warning("No players found in hand")
            return None
        
        # Parse hole cards and showdowns
        self._parse_cards(lines, players)
        
        # Identify lines that are not relevant to player parsing for efficiency
        # We'll keep lines that might be relevant to action parsing and pot parsing
        non_player_lines = []
        for line in lines:
            # Skip lines that contain player information, hole cards, or showdowns
            if (not self.PLAYER_PATTERN.search(line) and 
                not self.HOLE_CARDS_PATTERN.search(line) and 
                not self.SHOWDOWN_PATTERN.search(line)):
                non_player_lines.append(line)
        
        return {
            'players': players,
            'remaining_lines': non_player_lines
        }
    
    def _parse_players(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Parse player information from hand history lines.
        
        Args:
            lines: Lines of a hand history.
            
        Returns:
            List of dictionaries containing player data.
        """
        players = []
        player_names_seen = set()
        
        for line in lines:
            player_match = self.PLAYER_PATTERN.search(line)
            if player_match:
                seat = int(player_match.group(1))
                player_name = player_match.group(2)
                stack = float(player_match.group(3).replace(',', ''))
                bounty = float(player_match.group(4)) if player_match.group(4) else None
                
                # Skip if we've already seen this player (prevents duplicates)
                if player_name in player_names_seen:
                    continue
                
                # Add to the set of seen player names
                player_names_seen.add(player_name)
                
                # Add player data
                player = {
                    'name': player_name,
                    'seat': seat,
                    'stack': stack,
                    'bounty': bounty,
                    'cards': None,
                    'showed_cards': False,
                    'is_small_blind': False,
                    'is_big_blind': False,
                    'is_button': False
                }
                players.append(player)
        
        return players
    
    def _parse_cards(self, lines: List[str], players: List[Dict[str, Any]]) -> None:
        """
        Parse hole cards and showdown information.
        
        Args:
            lines: Lines of a hand history.
            players: List of player dictionaries to update with card information.
        """
        # Parse hole cards
        for line in lines:
            hole_cards_match = self.HOLE_CARDS_PATTERN.search(line)
            if hole_cards_match:
                player_name = hole_cards_match.group(1)
                cards = hole_cards_match.group(2).split()
                
                # Update the player's cards
                for player in players:
                    if player['name'] == player_name:
                        player['cards'] = cards
                        break
        
        # Parse showdown
        for line in lines:
            showdown_match = self.SHOWDOWN_PATTERN.search(line)
            if showdown_match:
                player_name = showdown_match.group(1)
                cards = showdown_match.group(2).split()
                
                # Update the player's cards and showed_cards flag
                for player in players:
                    if player['name'] == player_name:
                        player['cards'] = cards
                        player['showed_cards'] = True
                        break
