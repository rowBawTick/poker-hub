"""
Tournament parser component for extracting tournament information from poker hand histories.
"""
import re
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.parser.components.base_parser import BaseParser

logger = logging.getLogger(__name__)


class TournamentParser(BaseParser):
    """
    Parser component for extracting tournament information from poker hand histories.
    """
    
    # Regular expression for parsing tournament information from hand headers
    TOURNAMENT_HEADER_PATTERN = re.compile(
        r"PokerStars (?:Game|Hand) #(\d+): "  # Hand ID
        r"Tournament #(\d+), "  # Tournament ID
        r"(?:\$[\d.]+\+\$[\d.]+(?:\+\$[\d.]+)? [A-Z]{3} )?"  # Buy-in (optional)
        r"(.*?) - "  # Game type
        r"Level [XVI]+ \((\d+)/(\d+)\) - "  # Blinds
        r"(\d{4}/\d{2}/\d{2}) (\d{1,2}:\d{2}:\d{2}) (?:ET|UTC|WET)"  # Date, time
    )
    
    # For tournament hands, we need to extract the blinds from the format: Level IX (100/200)
    TOURNAMENT_BLIND_PATTERN = re.compile(r"Level [XVI]+ \((\d+)/(\d+)\)")
    
    # Pattern for table information
    TABLE_PATTERN = re.compile(r"Table '([^']+)' (\d+)-max Seat #(\d+) is the button")
    
    def __init__(self):
        """Initialize the tournament parser component."""
        super().__init__()
    
    def parse_hand(self, hand_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse tournament information from a single hand history.
        
        Args:
            hand_text: Text of a single poker hand history.
            
        Returns:
            Dictionary containing tournament data, or None if parsing failed.
        """
        # Skip empty hands
        if not hand_text.strip():
            return None
        
        lines = hand_text.strip().split('\n')
        return self.parse_tournament_info_lines(lines)
    
    def parse_tournament_info_lines(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse tournament information from hand history lines.
        
        Args:
            lines: List of lines from a hand history.
            
        Returns:
            Dictionary containing tournament data and remaining lines, or None if parsing failed.
        """
        if not lines or len(lines) < 2:
            return None
            
        # Parse tournament information from the header
        tournament_data = self._parse_tournament_header(lines[0])
        if not tournament_data:
            logger.warning(f"Could not parse tournament header: {lines[0][:100]}...")
            return None
        
        # Parse table information from the second line
        table_data = self._parse_table_info(lines[1])
        if table_data:
            tournament_data.update(table_data)
        
        # Return the tournament data along with the remaining lines
        # This allows the main parser to avoid reprocessing these lines
        tournament_data['remaining_lines'] = lines[2:]
        
        return tournament_data
    
    def _parse_tournament_header(self, header_line: str) -> Optional[Dict[str, Any]]:
        """
        Parse tournament information from the hand header.
        
        Args:
            header_line: First line of a hand history.
            
        Returns:
            Dictionary containing tournament data, or None if parsing failed.
        """
        tournament_match = self.TOURNAMENT_HEADER_PATTERN.search(header_line)
        if not tournament_match:
            return None
        
        hand_id = tournament_match.group(1)
        tournament_id = tournament_match.group(2)
        game_type = tournament_match.group(3)
        small_blind = float(tournament_match.group(4))
        big_blind = float(tournament_match.group(5))
        date_str = tournament_match.group(6)
        time_str = tournament_match.group(7)
        
        # Convert date and time to datetime
        try:
            date_time = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M:%S")
        except ValueError:
            date_time = None
        
        tournament_data = {
            'hand_id': hand_id,
            'tournament_id': tournament_id,
            'game_type': game_type,
            'date_time': date_time,
            'small_blind': small_blind,
            'big_blind': big_blind
        }
        
        return tournament_data
    
    def _parse_table_info(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse table information from a single line.
        
        Args:
            line: A line from the hand history text, typically the second line.
            
        Returns:
            Dictionary containing table data, or None if parsing failed.
        """
        table_match = self.TABLE_PATTERN.search(line)
        if not table_match:
            return None
        
        table_name = table_match.group(1)
        max_players = int(table_match.group(2))
        button_seat = int(table_match.group(3))
        
        return {
            'table_name': table_name,
            'max_players': max_players,
            'button_seat': button_seat
        }
