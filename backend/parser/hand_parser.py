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
    
    # Patterns for blinds and antes
    ANTE_PATTERN = re.compile(r"(.*?): posts the ante (\d+)")
    SMALL_BLIND_PATTERN = re.compile(r"(.*?): posts small blind (\d+)")
    BIG_BLIND_PATTERN = re.compile(r"(.*?): posts big blind (\d+)")
    
    # Pattern for player information with seat number and stack
    PLAYER_PATTERN = re.compile(
        r"Seat (\d+): (.*?) \(\$?([\d,]+(?:\.\d+)?) in chips(?:, \$?([\d.]+) bounty)?\)"  # Seat, player name, stack, bounty
    )
    
    # Pattern for table information
    TABLE_PATTERN = re.compile(r"Table '([^']+)' (\d+)-max Seat #(\d+) is the button")
    
    ACTION_PATTERNS = {
        'fold': re.compile(r"(.*?): folds"),
        'check': re.compile(r"(.*?): checks"),
        'call': re.compile(r"(.*?): calls \$?([\d,]+(?:\.\d+)?)"),
        'bet': re.compile(r"(.*?): bets \$?([\d,]+(?:\.\d+)?)"),
        'raise': re.compile(r"(.*?): raises \$?([\d,]+(?:\.\d+)?) to \$?([\d,]+(?:\.\d+)?)"),
        'all-in': re.compile(r"(.*?): (calls|bets|raises) \$?([\d,]+(?:\.\d+)?)(?:.* to \$?([\d,]+(?:\.\d+)?))?(?:.* and is all-in)"),
    }
    
    # Updated pattern to handle different summary formats
    SUMMARY_PATTERN = re.compile(r"Total pot \$?([\d,]+(?:\.\d+)?)(?:\s*\|\s*Rake \$?([\d,]+(?:\.\d+)?))?")
    
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
            
        Raises:
            Exception: If there is an error parsing the file or if no hands were successfully parsed.
        """
        logger.info(f"Parsing hand history file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Split the content into individual hands
            # PokerStars hands are separated by blank lines
            hand_texts = re.split(r'\n\n+', content)
            
            hands = []
            errors = []
            for i, hand_text in enumerate(hand_texts):
                if not hand_text.strip():
                    continue
                
                try:
                    hand_data = self.parse_hand(hand_text)
                    if hand_data:
                        hands.append(hand_data)
                except Exception as e:
                    error_msg = f"Error parsing hand #{i+1}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    logger.debug(f"Hand text: {hand_text[:200]}...")
            
            # Log the results
            logger.info(f"Parsed {len(hands)} hands from file: {file_path}")
            
            # If we didn't parse any hands successfully and had errors, raise an exception
            if len(hands) == 0 and errors:
                error_summary = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_summary += f"\n...and {len(errors) - 5} more errors"
                raise Exception(f"Failed to parse any hands from file. Errors: {error_summary}")
                
            return hands
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            # Re-raise the exception to be handled by the caller
            raise
    
    def parse_hand(self, hand_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single hand history text into structured data.
        
        Args:
            hand_text: Text of a single poker hand history.
            
        Returns:
            Dictionary containing structured hand data, or None if parsing failed.
            
        Raises:
            Exception: If there is an error parsing the hand.
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

        # Initialize hand data with default values for required fields
        hand_data = {
            'hand_id': hand_id,
            'tournament_id': tournament_id,
            'game_type': game_type,
            'date_time': date_time,
            'small_blind': float(small_blind.replace('$', '')) if small_blind else 0,
            'big_blind': float(big_blind) if big_blind else 0,
            'participants': [],  # List of players participating in this hand
            'actions': [],
            'board': [],
            'winners': [],
            'pot': 0,  # Initialize to 0 to ensure it's never None
            'rake': 0,  # Initialize to 0 to ensure it's never None
            'ante': 0,  # Initialize to 0 to ensure it's never None
            'button_seat': None,
            'max_players': None,
            'table_name': None,
        }
        
        # Parse table information
        for line in lines:
            table_match = self.TABLE_PATTERN.search(line)
            if table_match:
                hand_data['table_name'] = table_match.group(1)
                hand_data['max_players'] = int(table_match.group(2))
                hand_data['button_seat'] = int(table_match.group(3))
                break
        
        # Parse players
        player_dict = {}  # Temporary dict to help with action mapping
        for line in lines:
            player_match = self.PLAYER_PATTERN.search(line)
            if player_match:
                seat = int(player_match.group(1))
                player_name = player_match.group(2)
                stack = float(player_match.group(3).replace(',', ''))
                bounty = float(player_match.group(4)) if player_match.group(4) else None
                
                # Create participant data (player in this specific hand)
                participant_data = {
                    'id': len(hand_data['participants']) + 1,  # Generate sequential ID for this hand
                    'player_name': player_name,  # Store player name for lookup
                    'seat': seat,
                    'stack': stack,
                    'cards': None,
                    'bounty': bounty,
                    'is_small_blind': False,
                    'is_big_blind': False,
                    'is_button': seat == hand_data['button_seat'],
                    'final_stack': None,  # Will be calculated after hand is parsed
                    'net_won': None  # Will be calculated after hand is parsed
                }
                
                hand_data['participants'].append(participant_data)
                player_dict[player_name] = participant_data
        
        # Parse antes, small blinds, and big blinds
        sequence_counter = 0
        for line in lines:
            # Parse ante posts
            ante_match = self.ANTE_PATTERN.search(line)
            if ante_match:
                player_name = ante_match.group(1)
                ante_amount = float(ante_match.group(2))
                
                # Set the ante amount in hand data
                # If we've seen multiple antes, use the largest one
                if hand_data['ante'] < ante_amount:
                    hand_data['ante'] = ante_amount
                
                # Add ante post as an action
                # Find the participant for this player
                participant = next((p for p in hand_data['participants'] if p['player_name'] == player_name), None)
                participant_id = participant['id'] if participant else None
                
                action_data = {
                    'sequence': sequence_counter,
                    'player_name': player_name,
                    'participant_id': participant_id,
                    'action_type': 'ante',
                    'street': 'preflop',
                    'amount': ante_amount,
                    'is_all_in': False
                }
                hand_data['actions'].append(action_data)
                sequence_counter += 1
            
            # Parse small blind posts
            sb_match = self.SMALL_BLIND_PATTERN.search(line)
            if sb_match:
                player_name = sb_match.group(1)
                sb_amount = float(sb_match.group(2))
                
                # Mark player as small blind
                for participant in hand_data['participants']:
                    if participant['player_name'] == player_name:
                        participant['is_small_blind'] = True
                        break
                
                # Add small blind post as an action
                # Find the participant for this player
                participant = next((p for p in hand_data['participants'] if p['player_name'] == player_name), None)
                participant_id = participant['id'] if participant else None
                
                action_data = {
                    'sequence': sequence_counter,
                    'player_name': player_name,
                    'participant_id': participant_id,
                    'action_type': 'small_blind',
                    'street': 'preflop',
                    'amount': sb_amount,
                    'is_all_in': False
                }
                hand_data['actions'].append(action_data)
                sequence_counter += 1
            
            # Parse big blind posts
            bb_match = self.BIG_BLIND_PATTERN.search(line)
            if bb_match:
                player_name = bb_match.group(1)
                bb_amount = float(bb_match.group(2))
                
                # Mark player as big blind
                for participant in hand_data['participants']:
                    if participant['player_name'] == player_name:
                        participant['is_big_blind'] = True
                        break
                
                # Add big blind post as an action
                # Find the participant for this player
                participant = next((p for p in hand_data['participants'] if p['player_name'] == player_name), None)
                participant_id = participant['id'] if participant else None
                
                action_data = {
                    'sequence': sequence_counter,
                    'player_name': player_name,
                    'participant_id': participant_id,
                    'action_type': 'big_blind',
                    'street': 'preflop',
                    'amount': bb_amount,
                    'is_all_in': False
                }
                hand_data['actions'].append(action_data)
                sequence_counter += 1
        
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
                    
                    # Find the participant ID for this player
                    participant = next((p for p in hand_data['participants'] if p['player_name'] == player_name), None)
                    participant_id = participant['id'] if participant else None
                    
                    action_data = {
                        'sequence': sequence_counter,
                        'player_name': player_name,
                        'participant_id': participant_id,
                        'action_type': action_type,
                        'street': current_street,
                        'is_all_in': False
                    }
                    sequence_counter += 1
                    
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
                for participant in hand_data['participants']:
                    if participant['player_name'] == player_name:
                        participant['cards'] = cards
                        break
            
            # Parse showdown
            showdown_match = self.SHOWDOWN_PATTERN.search(line)
            if showdown_match:
                player_name = showdown_match.group(1)
                cards = showdown_match.group(2).split()
                for participant in hand_data['participants']:
                    if participant['player_name'] == player_name:
                        participant['cards'] = cards
                        participant['showed_cards'] = True
                        break
        
        # Parse summary
        for line in lines:
            # Parse pot and rake with better error handling
            summary_match = self.SUMMARY_PATTERN.search(line)
            if summary_match:
                try:
                    pot_str = summary_match.group(1)
                    if pot_str:
                        pot = float(pot_str.replace(',', ''))
                        hand_data['pot'] = pot
                    else:
                        hand_data['pot'] = 0
                        
                    rake_str = summary_match.group(2)
                    if rake_str:
                        rake = float(rake_str.replace(',', ''))
                        hand_data['rake'] = rake
                    else:
                        hand_data['rake'] = 0
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing pot/rake: {e}. Line: {line}")
                    # Set default values if parsing fails
                    if 'pot' not in hand_data or hand_data['pot'] is None:
                        hand_data['pot'] = 0
                    if 'rake' not in hand_data or hand_data['rake'] is None:
                        hand_data['rake'] = 0
            
            # Parse winners
            winner_match = self.WINNER_PATTERN.search(line)
            if winner_match:
                player_name = winner_match.group(1)
                amount = float(winner_match.group(2).replace(',', ''))
                # Find the participant for this winner
                participant = next((p for p in hand_data['participants'] if p['player_name'] == player_name), None)
                
                winner_data = {
                    'player_name': player_name,
                    'amount': amount,
                }
                
                # Add participant ID if found
                if participant:
                    winner_data['participant_id'] = participant['id']
                    
                    # Update the participant's final stack and net won amount
                    if participant['final_stack'] is None:
                        # If not set yet, assume they ended with their starting stack plus winnings
                        participant['final_stack'] = participant['stack'] + amount
                    else:
                        participant['final_stack'] += amount
                        
                    # Calculate net won (can be negative if they lost)
                    if participant['net_won'] is None:
                        participant['net_won'] = amount
                    else:
                        participant['net_won'] += amount
                
                hand_data['winners'].append(winner_data)
            
            # Parse board if not already parsed
            if not hand_data['board']:
                board_match = self.BOARD_PATTERN.search(line)
                if board_match:
                    hand_data['board'] = board_match.group(1).split()
        
        return hand_data
