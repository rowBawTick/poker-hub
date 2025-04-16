"""
Action parser component for extracting player actions from poker hand histories.
"""
import re
import logging
from typing import Dict, List, Any, Optional, Tuple

from backend.parser.components.base_parser import BaseParser

logger = logging.getLogger(__name__)


class PlayerActionParser(BaseParser):
    """
    Parser component for extracting player actions from poker hand histories.
    """
    
    # Patterns for blinds and antes
    ANTE_PATTERN = re.compile(r"(.*?): posts the ante (\d+)")
    SMALL_BLIND_PATTERN = re.compile(r"(.*?): posts small blind (\d+)")
    BIG_BLIND_PATTERN = re.compile(r"(.*?): posts big blind (\d+)")
    
    # Patterns for player actions
    ACTION_PATTERNS = {
        'fold': re.compile(r"(.*?): folds"),
        'check': re.compile(r"(.*?): checks"),
        'call': re.compile(r"(.*?): calls \$?([\d,]+(?:\.\d+)?)"),
        'bet': re.compile(r"(.*?): bets \$?([\d,]+(?:\.\d+)?)"),
        'raise': re.compile(r"(.*?): raises \$?([\d,]+(?:\.\d+)?) to \$?([\d,]+(?:\.\d+)?)"),
        # Separate pattern for detecting all-in actions
        'all-in': re.compile(r"(.*?): (calls|bets|raises) \$?([\d,]+(?:\.\d+)?)(?:.* to \$?([\d,]+(?:\.\d+)?))?.*and is all-in"),
    }
    
    def __init__(self):
        """Initialize the action parser component."""
        super().__init__()
    
    def parse_hand(self, hand_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse player actions from a single hand history.
        
        Args:
            hand_text: Text of a single poker hand history.
            
        Returns:
            Dictionary containing action data, or None if parsing failed.
        """
        # Skip empty hands
        if not hand_text.strip():
            return None
        
        lines = hand_text.strip().split('\n')
        return self.parse_action_lines(lines)
    
    def parse_action_lines(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse player actions from hand history lines.
        
        Args:
            lines: List of lines from a hand history.
            
        Returns:
            Dictionary containing action data and remaining lines, or None if parsing failed.
        """
        if not lines:
            return None
        
        # Parse blinds, antes, and actions
        actions = []
        sequence_counter = 0
        
        # Track the current street
        current_street = 'preflop'
        
        # Process blinds and antes first, and get remaining lines
        blinds_antes_actions, sequence_counter, remaining_lines = self._process_blinds_antes(lines, sequence_counter)
        actions.extend(blinds_antes_actions)
        
        # Use the remaining lines for further processing
        lines = remaining_lines
        
        # Find summary section to avoid processing it for actions
        summary_start_index = -1
        for i, line in enumerate(lines):
            if '*** SUMMARY ***' in line:
                summary_start_index = i
                break
                
        # Lines to process for actions (exclude summary section and blinds/antes)
        action_lines = lines if summary_start_index == -1 else lines[:summary_start_index]
        
        # Parse regular actions
        for line in action_lines:
            # Detect street changes
            if '*** HOLE CARDS ***' in line:
                current_street = 'preflop'
                continue  # Skip this line for action parsing
            elif '*** FLOP ***' in line:
                current_street = 'flop'
                continue  # Skip this line for action parsing
            elif '*** TURN ***' in line:
                current_street = 'turn'
                continue  # Skip this line for action parsing
            elif '*** RIVER ***' in line:
                current_street = 'river'
                continue  # Skip this line for action parsing
            elif '*** SHOW DOWN ***' in line:
                current_street = 'showdown'
                continue  # Skip this line for action parsing
            
            # Parse player action from this line
            action_data = self._parse_player_action(line, current_street, sequence_counter)
            if action_data:
                actions.append(action_data)
                sequence_counter += 1
        
        # Identify lines that are only relevant to pot parsing (summary section)
        pot_relevant_lines = []
        if summary_start_index != -1:
            pot_relevant_lines = lines[summary_start_index:]
        
        return {
            'actions': actions,
            'remaining_lines': pot_relevant_lines
        }

    def _parse_ante(self, line: str, sequence: int) -> Optional[Dict[str, Any]]:
        """
        Parse ante post from a line.
        
        Args:
            line: Line of hand history text.
            sequence: Current sequence number.
            
        Returns:
            Action data dictionary or None if no ante in this line.
        """
        ante_match = self.ANTE_PATTERN.search(line)
        if not ante_match:
            return None
        
        player_name = ante_match.group(1)
        ante_amount = float(ante_match.group(2))

        # TODO: chrischambers 16/04/2025 - Sometimes there are rare cases when a player is all in on an ante
        return {
            'sequence': sequence,
            'player_name': player_name,
            'action_type': 'ante',
            'street': 'preflop',
            'amount': ante_amount,
            'is_all_in': False
        }
    
    def _parse_small_blind(self, line: str, sequence: int) -> Optional[Dict[str, Any]]:
        """
        Parse small blind post from a line.
        
        Args:
            line: Line of hand history text.
            sequence: Current sequence number.
            
        Returns:
            Action data dictionary or None if no small blind in this line.
        """
        sb_match = self.SMALL_BLIND_PATTERN.search(line)
        if not sb_match:
            return None
        
        player_name = sb_match.group(1)
        sb_amount = float(sb_match.group(2))
        
        return {
            'sequence': sequence,
            'player_name': player_name,
            'action_type': 'small_blind',
            'street': 'preflop',
            'amount': sb_amount,
            'is_all_in': False
        }
    
    def _parse_big_blind(self, line: str, sequence: int) -> Optional[Dict[str, Any]]:
        """
        Parse big blind post from a line.
        
        Args:
            line: Line of hand history text.
            sequence: Current sequence number.
            
        Returns:
            Action data dictionary or None if no big blind in this line.
        """
        bb_match = self.BIG_BLIND_PATTERN.search(line)
        if not bb_match:
            return None
        
        player_name = bb_match.group(1)
        bb_amount = float(bb_match.group(2))

        # TODO: chrischambers 16/04/2025 - a user can be all in on a BB or SB...
        return {
            'sequence': sequence,
            'player_name': player_name,
            'action_type': 'big_blind',
            'street': 'preflop',
            'amount': bb_amount,
            'is_all_in': False
        }
        
    def _process_blinds_antes(self, lines: List[str], sequence_counter: int) -> Tuple[List[Dict[str, Any]], int, List[str]]:
        """
        Process blinds and antes from hand history lines.
        
        Args:
            lines: List of lines from a hand history.
            sequence_counter: Current sequence counter.
            
        Returns:
            Tuple containing:
            - List of blinds and antes actions
            - Updated sequence counter
            - Remaining lines that don't contain processed blinds/antes
        """
        actions = []
        processed_indices = set()

        # First pass: find all blinds and antes lines
        for i, line in enumerate(lines):
            # Once we reach the hole cards section, we're done with blinds and antes
            # TODO: chrischambers 16/04/2025 - sometimes you get moved to a table and don't have any hold cards yet...
            # Of if you're observing a table you won't have cards... Does PokerStars saves these hands? Don't think so
            if '*** HOLE CARDS ***' in line:
                break
                
            # Parse ante posts
            ante_action = self._parse_ante(line, sequence_counter)
            if ante_action:
                actions.append(ante_action)
                sequence_counter += 1
                processed_indices.add(i)
                continue
            
            # Parse small blind posts
            sb_action = self._parse_small_blind(line, sequence_counter)
            if sb_action:
                actions.append(sb_action)
                sequence_counter += 1
                processed_indices.add(i)
                continue
            
            # Parse big blind posts
            bb_action = self._parse_big_blind(line, sequence_counter)
            if bb_action:
                actions.append(bb_action)
                sequence_counter += 1
                processed_indices.add(i)
                # Once we've found the big blind, we can stop processing blinds and antes
                # as they always come in order: antes -> small blind -> big blind
                break
        
        # Create a new list of lines excluding the processed blinds and antes
        remaining_lines = [line for i, line in enumerate(lines) if i not in processed_indices]
        
        return actions, sequence_counter, remaining_lines
        
    def _parse_player_action(self, line: str, current_street: str, sequence: int) -> Optional[Dict[str, Any]]:
        """
        Parse a player action from a line.
        
        Args:
            line: Line of hand history text.
            current_street: Current street (preflop, flop, turn, river).
            sequence: Current sequence number.
            
        Returns:
            Action data dictionary or None if no action in this line.
        """
        # Check if this is an all-in action
        is_all_in = 'all-in' in line and 'and is all-in' in line
        
        # Try each action pattern
        for action_type, pattern in self.ACTION_PATTERNS.items():
            action_match = pattern.search(line)
            if not action_match:
                continue
                
            player_name = action_match.group(1)
            
            action_data = {
                'sequence': sequence,
                'player_name': player_name,
                'action_type': action_type,
                'street': current_street,
                'is_all_in': is_all_in
            }
            
            # Parse and add amount for actions that have amounts
            amount = self._parse_action_amount(action_type, action_match)
            if amount is not None:
                action_data['amount'] = amount
            
            return action_data
            
        return None
    

    def _parse_action_amount(self, action_type: str, action_match: re.Match) -> Optional[float]:
        """
        Parse the amount from an action match.
        
        Args:
            action_type: Type of action (call, bet, raise).
            action_match: Regex match object.
            
        Returns:
            Amount as a float, or None if no amount.
        """
        if action_type in ['call', 'bet']:
            return float(action_match.group(2).replace(',', ''))
        elif action_type == 'raise':
            return float(action_match.group(3).replace(',', ''))  # to_amount
        elif action_type == 'all-in':
            if action_match.group(4):  # Raise all-in
                return float(action_match.group(4).replace(',', ''))
            else:  # Call or bet all-in
                return float(action_match.group(3).replace(',', ''))
                
        return None
