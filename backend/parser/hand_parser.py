"""
Parser for PokerStars hand history files.
"""
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class HandParser:
    """
    Parser for PokerStars hand history files.
    Extracts information from hand history files into structured data.
    """
    
    # Regular expressions for parsing different parts of a hand history
    # For tournament hands, we need to extract the blinds from the format: Level IX (100/200)
    TOURNAMENT_BLIND_PATTERN = re.compile(r"Level [XVI]+ \((\d+)/(\d+)\)")
    
    HAND_HEADER_PATTERN = re.compile(
        r"PokerStars (?:Game|Hand) #(\d+): "  # Hand ID
        r"(?:Tournament #(\d+), .*?|Hold'em No Limit \((\$\d+)/\$(\d+)\) - )"  # Tournament ID or cash game blinds
        r"(.*?) \[(\d{4}/\d{2}/\d{2}) (\d{1,2}:\d{2}:\d{2}) (?:ET|UTC|WET)(?:.*)\]"  # Game type, date, time
    )
    
    # Pattern to extract ante from tournament hands
    ANTE_PATTERN = re.compile(r"(.*?): posts the ante (\d+)")
    
    PLAYER_PATTERN = re.compile(
        r"Seat (\d+): (.*?) \(\$?([\d,]+(?:\.\d+)?) in chips\)"  # Seat, player name, stack
    )
    
    ACTION_PATTERNS = {
        'fold': re.compile(r"(.*?): folds"),
        'check': re.compile(r"(.*?): checks"),
        'call': re.compile(r"(.*?): calls \$?([\d,]+(?:\.\d+)?)"),
        'bet': re.compile(r"(.*?): bets \$?([\d,]+(?:\.\d+)?)"),
        'raise': re.compile(r"(.*?): raises \$?([\d,]+(?:\.\d+)?) to \$?([\d,]+(?:\.\d+)?)"),
        'all-in': re.compile(r"(.*?): (calls|bets|raises) \$?([\d,]+(?:\.\d+)?)(?:.* to \$?([\d,]+(?:\.\d+)?))?(?:.* and is all-in)"),
    }
    
    SUMMARY_PATTERN = re.compile(r"Total pot \$?([\d,]+(?:\.\d+)?) (?:\| Rake \$?([\d,]+(?:\.\d+)?))?")
    
    WINNER_PATTERN = re.compile(r"(.*?) collected \$?([\d,]+(?:\.\d+)?) from pot")
    
    SHOWDOWN_PATTERN = re.compile(r"(.*?): shows \[(.*?)\]")
    
    BOARD_PATTERN = re.compile(r"Board \[(.*?)\]")
    
    def __init__(self):
        """Initialize the hand parser."""
        pass
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse a hand history file into a list of structured hand data.
        
        Args:
            file_path: Path to the hand history file.
            
        Returns:
            List of dictionaries containing structured hand data.
        """
        logger.info(f"Parsing hand history file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Split the content into individual hands
            # PokerStars hands are separated by blank lines
            hand_texts = re.split(r'\n\n+', content)
            
            hands = []
            for hand_text in hand_texts:
                if not hand_text.strip():
                    continue
                
                try:
                    hand_data = self.parse_hand(hand_text)
                    if hand_data:
                        hands.append(hand_data)
                except Exception as e:
                    logger.error(f"Error parsing hand: {e}")
                    logger.debug(f"Hand text: {hand_text[:100]}...")
            
            logger.info(f"Parsed {len(hands)} hands from file: {file_path}")
            return hands
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            return []
    
    def parse_hand(self, hand_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single hand history text into structured data.
        
        Args:
            hand_text: Text of a single poker hand history.
            
        Returns:
            Dictionary containing structured hand data, or None if parsing failed.
        """
        # Skip empty hands
        if not hand_text.strip():
            return None
        
        lines = hand_text.strip().split('\n')
        
        # Parse basic hand information from the header
        header_match = self.HAND_HEADER_PATTERN.search(lines[0])
        if not header_match:
            logger.warning(f"Could not parse hand header: {lines[0][:100]}...")
            return None
        
        hand_id = header_match.group(1)
        tournament_id = header_match.group(2)
        small_blind = header_match.group(3)
        big_blind = header_match.group(4)
        game_type = header_match.group(5)
        date_str = header_match.group(6)
        time_str = header_match.group(7)
        
        # Convert date and time to datetime
        try:
            date_time = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M:%S")
        except ValueError:
            date_time = None
        
        # Extract game type, date, and time
        game_type = header_match.group(5)
        date_str = header_match.group(6)
        time_str = header_match.group(7)
        
        # For cash games, blinds are in the header
        small_blind = None
        big_blind = None
        
        if tournament_id:
            # For tournament hands, we need to extract blinds from the first line
            # Example: "PokerStars Hand #255494979606: Tournament #3872575757, $0.48+$0.50+$0.12 USD Hold'em No Limit - Level IX (100/200)"
            tournament_blind_match = self.TOURNAMENT_BLIND_PATTERN.search(lines[0])
            if tournament_blind_match:
                small_blind = tournament_blind_match.group(1)
                big_blind = tournament_blind_match.group(2)
            else:
                logger.warning(f"Could not extract tournament blinds from: {lines[0]}")
        else:
            # For cash games
            small_blind = header_match.group(3)
            big_blind = header_match.group(4)

        # Initialize hand data
        hand_data = {
            'hand_id': hand_id,
            'tournament_id': tournament_id,
            'game_type': game_type,
            'date_time': date_time,
            'small_blind': float(small_blind.replace('$', '')) if small_blind else None,
            'big_blind': float(big_blind) if big_blind else None,
            'players': {},
            'actions': [],
            'board': [],
            'winners': [],
            'pot': None,
            'rake': None,
            'ante': None,
        }
        
        # Parse players
        for line in lines:
            player_match = self.PLAYER_PATTERN.search(line)
            if player_match:
                seat = int(player_match.group(1))
                player_name = player_match.group(2)
                stack = float(player_match.group(3).replace(',', ''))
                hand_data['players'][player_name] = {
                    'seat': seat,
                    'stack': stack,
                    'cards': None,
                }
        
        # Parse antes
        for line in lines:
            ante_match = self.ANTE_PATTERN.search(line)
            if ante_match and hand_data['ante'] is None:
                # Just record the ante amount once, it's the same for all players
                hand_data['ante'] = float(ante_match.group(2))
        
        # Parse actions
        current_street = 'preflop'
        for line in lines:
            # Detect street changes
            if '*** HOLE CARDS ***' in line:
                current_street = 'preflop'
            elif '*** FLOP ***' in line:
                current_street = 'flop'
                # Extract flop cards
                flop_match = re.search(r'\[(.{2}) (.{2}) (.{2})\]', line)
                if flop_match:
                    hand_data['board'].extend([flop_match.group(1), flop_match.group(2), flop_match.group(3)])
            elif '*** TURN ***' in line:
                current_street = 'turn'
                # Extract turn card
                turn_match = re.search(r'\[.{8}\] \[(.{2})\]', line)
                if turn_match:
                    hand_data['board'].append(turn_match.group(1))
            elif '*** RIVER ***' in line:
                current_street = 'river'
                # Extract river card
                river_match = re.search(r'\[.{11}\] \[(.{2})\]', line)
                if river_match:
                    hand_data['board'].append(river_match.group(1))
            elif '*** SHOW DOWN ***' in line:
                current_street = 'showdown'
            elif '*** SUMMARY ***' in line:
                break  # Stop parsing actions at summary
            
            # Parse player actions
            for action_type, pattern in self.ACTION_PATTERNS.items():
                action_match = pattern.search(line)
                if action_match:
                    player_name = action_match.group(1)
                    
                    action_data = {
                        'player': player_name,
                        'action': action_type,
                        'street': current_street,
                    }
                    
                    # Add amount for bets, calls, raises
                    if action_type in ['call', 'bet']:
                        amount = float(action_match.group(2).replace(',', ''))
                        action_data['amount'] = amount
                    elif action_type == 'raise':
                        to_amount = float(action_match.group(3).replace(',', ''))
                        action_data['amount'] = to_amount
                    elif action_type == 'all-in':
                        if action_match.group(4):  # Raise all-in
                            amount = float(action_match.group(4).replace(',', ''))
                        else:  # Call or bet all-in
                            amount = float(action_match.group(3).replace(',', ''))
                        action_data['amount'] = amount
                        action_data['is_all_in'] = True
                    
                    hand_data['actions'].append(action_data)
                    break  # Only one action per line
            
            # Parse hole cards
            dealt_match = re.search(r"Dealt to (.*?) \[(.*?)\]", line)
            if dealt_match:
                player_name = dealt_match.group(1)
                cards = dealt_match.group(2).split()
                if player_name in hand_data['players']:
                    hand_data['players'][player_name]['cards'] = cards
            
            # Parse showdown
            showdown_match = self.SHOWDOWN_PATTERN.search(line)
            if showdown_match:
                player_name = showdown_match.group(1)
                cards = showdown_match.group(2).split()
                if player_name in hand_data['players']:
                    hand_data['players'][player_name]['cards'] = cards
                    hand_data['players'][player_name]['showed_cards'] = True
        
        # Parse summary
        for line in lines:
            # Parse pot and rake
            summary_match = self.SUMMARY_PATTERN.search(line)
            if summary_match:
                pot = float(summary_match.group(1).replace(',', ''))
                rake = float(summary_match.group(2).replace(',', '')) if summary_match.group(2) else 0
                hand_data['pot'] = pot
                hand_data['rake'] = rake
            
            # Parse winners
            winner_match = self.WINNER_PATTERN.search(line)
            if winner_match:
                player_name = winner_match.group(1)
                amount = float(winner_match.group(2).replace(',', ''))
                hand_data['winners'].append({
                    'player': player_name,
                    'amount': amount
                })
            
            # Parse board if not already parsed
            if not hand_data['board']:
                board_match = self.BOARD_PATTERN.search(line)
                if board_match:
                    hand_data['board'] = board_match.group(1).split()
        
        return hand_data
