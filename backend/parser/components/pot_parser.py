"""
Pot parser component for extracting pot and winner information from poker hand histories.
"""
import re
import logging
from typing import Dict, List, Any, Optional

from backend.parser.components.base_parser import BaseParser

logger = logging.getLogger(__name__)


class PotParser(BaseParser):
    """
    Parser component for extracting pot and winner information from poker hand histories.
    """
    
    # Pattern for pot and rake information
    # Handles both formats:
    # 1. "Total pot 1000 | Rake 0" (single pot, no explicit mention of "Main pot")
    # 2. "Total pot 1000 Main pot 500. Side pot 500. | Rake 0" (multiple pots)
    SUMMARY_PATTERN = re.compile(
        r"Total pot \$?([\d,]+(?:\.\d+)?)(?:\s*Main pot \$?([\d,]+(?:\.\d+)?)\.?(?:\s*Side pot(?:-\d+)? \$?([\d,]+(?:\.\d+)?)\.?)?(?:\s*Side pot(?:-\d+)? \$?([\d,]+(?:\.\d+)?)\.?)?(?:\s*Side pot(?:-\d+)? \$?([\d,]+(?:\.\d+)?)\.?)?(?:\s*Side pot(?:-\d+)? \$?([\d,]+(?:\.\d+)?)\.?)?(?:\s*Side pot(?:-\d+)? \$?([\d,]+(?:\.\d+)?)\.?)?(?:\s*Side pot(?:-\d+)? \$?([\d,]+(?:\.\d+)?)\.?)?)?(?:\s*\|\s*Rake \$?([\d,]+(?:\.\d+)?))?")
    
    # Pattern for winners from specific pots
    # This handles both formats:
    # 1. "Player collected X from pot" (simple case)
    # 2. "Player collected X from main pot" or "Player collected X from side pot-1" (specific pot case)
    WINNER_PATTERN = re.compile(r"(.*?) collected \$?([\d,]+(?:\.\d+)?) from (?:(main|side)(?: pot)?(?:-(\d+))?|pot)")
    
    # Pattern for uncalled bets
    # This handles both formats:
    # 1. "Uncalled bet ($100) returned to Player1"
    # 2. "Uncalled bet (100) returned to Player1"
    UNCALLED_BET_PATTERN = re.compile(r"Uncalled bet \(\$?([\d,]+(?:\.\d+)?)\) returned to (.*)")
    
    # Pattern for pot collection (without specifying pot type)
    # This handles both formats:
    # 1. "Player collected 100 from pot"
    # 2. "Player collected (100) from pot" (with parentheses)
    POT_COLLECTION_PATTERN = re.compile(r"(.*?) collected \(?\$?([\d,]+(?:\.\d+)?)\)? from pot")
    
    # Pattern for board cards
    BOARD_PATTERN = re.compile(r"Board \[(.*?)\]")

    # --- Pot Structure Parsing Patterns ---
    TOTAL_POT_PATTERN = re.compile(r"Total pot \$?([\d,]+(?:\.\d+)?)")
    RAKE_PATTERN = re.compile(r"\|\s*Rake \$?([\d,]+(?:\.\d+)?)")
    MAIN_POT_PATTERN = re.compile(r"Main pot \$?([\d,]+(?:\.\d+)?)\.?")
    SIDE_POT_PATTERN = re.compile(r"Side pot(?:-\d+)? \$?([\d,]+(?:\.\d+)?)\.?")
    # --- End Pot Structure Patterns ---

    # Pattern for seat-based collection (e.g., "Seat 2: Player (big blind) collected (7000)")
    SEAT_COLLECTED_PATTERN = re.compile(r"Seat \d+: (.*?)(?:\s+\([^)]+\))? collected \(?(\$?[\d,]+(?:\.\d+)?)\)?")
    
    # Pattern for seat-based winning with cards shown (e.g., "Seat 3: Player showed [cards] and won (2775)")
    SEAT_WON_PATTERN = re.compile(r"Seat \d+: (.*?)(?:\s+\([^)]+\))? showed \[[^\]]+\] and won \(?(\$?[\d,]+(?:\.\d+)?)\)?(?:\s+from\s+(main|side)(?: pot)?(?:-(\d+))?)?")
    
    # Pattern for seat-based winning without showing cards (e.g., "Seat 3: Player won (2775)")
    SEAT_WON_NO_SHOW_PATTERN = re.compile(r"Seat \d+: (.*?)(?:\s+\([^)]+\))? won \(?(\$?[\d,]+(?:\.\d+)?)\)?(?:\s+from\s+(main|side)(?: pot)?(?:-(\d+))?)?")
    
    def __init__(self):
        """Initialize the pot parser component."""
        super().__init__()
    
    def parse_hand(self, hand_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse pot and winner information from a single hand history.
        
        Args:
            hand_text: Text of a single poker hand history.
            
        Returns:
            Dictionary containing pot and winner data, or None if parsing failed.
        """
        # Skip empty hands
        if not hand_text.strip():
            return None
        
        lines = hand_text.strip().split('\n')
        return self.parse_pot_lines(lines)
    
    def parse_pot_lines(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """
        Parse pot and winner information from hand history lines.
        
        Args:
            lines: List of lines from a hand history.
            
        Returns:
            Dictionary containing pot and winner data, or None if parsing failed.
        """
        if not lines:
            return None
        
        # Initialize pot data
        pot_data = {
            'pot': 0,
            'rake': 0,
            'pots': [],
            'winners': [],
            'board': [],
            'returned_bets': [],
            'pot_collections': []
        }
        
        # Parse the entire hand for pot collections and returned bets
        for line in lines:
            # Check for pot collections in the main hand text (before summary)
            pot_collection_match = self.POT_COLLECTION_PATTERN.search(line)
            if pot_collection_match:
                try:
                    player_name = pot_collection_match.group(1).strip()
                    amount_str = pot_collection_match.group(2).replace(',', '')
                    amount = float(amount_str)
                    collection_data = {
                        'player_name': player_name,
                        'amount': amount
                    }
                    pot_data['pot_collections'].append(collection_data)
                    # Also add to winners list for consistency
                    self._add_winner_to_pot(pot_data, player_name, amount)
                    logger.info(f"Found pot collection: {player_name} collected {amount} from pot")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing pot collection: {e}. Line: {line}")
            
            # Check for uncalled bets in the main hand text
            uncalled_bet_match = self.UNCALLED_BET_PATTERN.search(line)
            if uncalled_bet_match:
                try:
                    amount_str = uncalled_bet_match.group(1).replace(',', '')
                    amount = float(amount_str)
                    player_name = uncalled_bet_match.group(2).strip()
                    returned_bet_data = {
                        'player_name': player_name,
                        'amount': amount
                    }
                    pot_data['returned_bets'].append(returned_bet_data)
                    logger.info(f"Found returned bet: {amount} to {player_name}")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing uncalled bet: {e}. Line: {line}")
        
        # Parse summary section for pot information
        summary_found = False
        for i, line in enumerate(lines):
            if '*** SUMMARY ***' in line:
                summary_found = True
                # Parse the summary section
                self._parse_summary_section(lines[i:], pot_data)
                break
        
        if not summary_found:
            logger.warning("No summary section found in hand")
        
        return pot_data
    
    def _add_winner_to_pot(self, pot_data: Dict[str, Any], player_name: str, amount: float,
                         pot_type: Optional[str] = None, pot_number: Optional[str] = None) -> None:
        """
        Add a winner to the appropriate pot.

        Args:
            pot_data: Dictionary containing pot information
            player_name: Name of the player who won
            amount: Amount won
            pot_type: Type of pot (main or side)
            pot_number: Number of side pot if applicable
        """
        # Ensure amount is float
        try:
            amount = float(str(amount).replace(',', ''))
        except ValueError:
            logger.warning(f"Could not convert winner amount '{amount}' to float for player {player_name}")
            return

        # Create winner data for the general 'winners' list
        winner_data = {
            'player_name': player_name,
            'amount': amount
        }

        # Add to general winners list, avoiding duplicates
        if not any(w['player_name'] == player_name and w['amount'] == amount for w in pot_data['winners']):
            pot_data['winners'].append(winner_data)

        # Determine pot type string for assigning to specific pot's winner list
        if pot_type == 'main':
            pot_type_str = 'main'
        elif pot_type == 'side' and pot_number:
            pot_type_str = f'side-{pot_number}'
        else:
            # Default logic if pot type isn't explicitly provided by the regex match
            if len(pot_data['pots']) == 1:
                # If only one pot exists (main or side), assign winner to it
                pot_type_str = pot_data['pots'][0]['pot_type']
            else:
                # Default to 'main' if multiple pots or none defined yet
                pot_type_str = 'main'

        # Find or create the target pot in the 'pots' list
        target_pot = next((p for p in pot_data['pots'] if p['pot_type'] == pot_type_str), None)

        if not target_pot:
            # If target pot doesn't exist (e.g. side pot winner found before side pot defined, or no pots defined)
            if not pot_data['pots']:
                # If no pots defined yet (e.g., simple walkover), create a main pot
                target_pot = {
                    'pot_type': 'main', # Treat single pot as main
                    'amount': pot_data.get('pot', amount), # Use total pot if available, else winner amount
                    'winners': []
                }
                pot_data['pots'].append(target_pot)
            elif pot_type_str.startswith('side-'):
                # Create a missing side pot
                 target_pot = {
                    'pot_type': pot_type_str,
                    'amount': amount, # Best guess for side pot amount is the winner's amount
                    'winners': []
                 }
                 pot_data['pots'].append(target_pot)
            else:
                # Should ideally find the main pot if it exists, but fallback just in case
                target_pot = next((p for p in pot_data['pots'] if p['pot_type'] == 'main'), None)
                if not target_pot: # If main pot somehow still missing
                     target_pot = {
                        'pot_type': 'main',
                        'amount': pot_data.get('pot', amount),
                        'winners': []
                    }
                     pot_data['pots'].append(target_pot)

        # Add the winner specifically to the target pot's winner list
        pot_winner_specific = {
            'player_name': player_name,
            'amount': amount
        }
        # Avoid adding duplicates within the specific pot's winners
        if target_pot and not any(w['player_name'] == player_name and w['amount'] == amount for w in target_pot.get('winners', [])):
             if 'winners' not in target_pot: # Ensure 'winners' list exists
                 target_pot['winners'] = []
             target_pot['winners'].append(pot_winner_specific)

    def _parse_summary_section(self, summary_lines: List[str], pot_data: Dict[str, Any]) -> None:
        """
        Parse the summary section for pot, rake, board, and winner information.
        Uses individual patterns for robustness.
        """
        pot_structure_parsed = False
        structure_line = ""

        # Find the line containing the main pot structure information
        for line in summary_lines:
            if "Total pot" in line and "*** SUMMARY ***" not in line:
                structure_line = line
                break

        # Parse pot structure from the identified line
        if structure_line:
            try:
                # Parse Total Pot
                total_pot_match = self.TOTAL_POT_PATTERN.search(structure_line)
                if total_pot_match:
                    pot_data['pot'] = float(total_pot_match.group(1).replace(',', ''))
                else:
                    # If total pot isn't found on this line, something is wrong
                    logger.warning(f"Could not find Total Pot on structure line: {structure_line}")
                    pot_data['pot'] = 0 # Default to 0 if unparsable

                # Parse Rake (optional)
                rake_match = self.RAKE_PATTERN.search(structure_line)
                if rake_match:
                    pot_data['rake'] = float(rake_match.group(1).replace(',', ''))
                else:
                    pot_data['rake'] = 0 # Default rake to 0

                # Reset pots list before parsing
                pot_data['pots'] = []

                # Parse Main Pot (optional, indicates multiple pots if present)
                main_pot_match = self.MAIN_POT_PATTERN.search(structure_line)
                if main_pot_match:
                    main_pot_amount = float(main_pot_match.group(1).replace(',', ''))
                    pot_data['pots'].append({
                        'pot_type': 'main',
                        'amount': main_pot_amount,
                        'winners': []
                    })

                    # Parse Side Pots (only relevant if Main Pot was found)
                    side_pot_matches = self.SIDE_POT_PATTERN.finditer(structure_line)
                    side_pot_index = 1
                    for match in side_pot_matches:
                        side_pot_amount = float(match.group(1).replace(',', ''))
                        pot_data['pots'].append({
                            'pot_type': f'side-{side_pot_index}',
                            'amount': side_pot_amount,
                            'winners': []
                        })
                        side_pot_index += 1
                else:
                    # No explicit Main Pot found - implies a single pot scenario
                    # If total pot > 0, create a single 'main' pot entry
                    if pot_data.get('pot', 0) > 0:
                        pot_data['pots'].append({
                            'pot_type': 'main',
                            'amount': pot_data['pot'],
                            'winners': []
                        })

                pot_structure_parsed = True

            except (ValueError, IndexError, AttributeError) as e:
                logger.warning(f"Error parsing pot/rake structure with individual patterns: {e}. Line: {structure_line}")
                # Reset pots if structure parsing failed mid-way
                pot_data['pots'] = []
                pot_structure_parsed = False # Mark as failed

        # If structure parsing failed or wasn't found, but we have a total pot, default to single main pot
        if not pot_structure_parsed and pot_data.get('pot', 0) > 0 and not pot_data['pots']:
             pot_data['pots'].append({
                 'pot_type': 'main',
                 'amount': pot_data['pot'],
                 'winners': []
             })

        # Now, parse winners, board, and uncalled bets from ALL summary lines
        # TODO: chrischambers 17/04/2025 - Not really necessary anymore but we could use this as a check.
        for line in summary_lines:
            # Skip the summary marker line itself
            if "*** SUMMARY ***" in line:
                continue
            # Skip the structure line if we successfully processed it above
            if pot_structure_parsed and line == structure_line:
                 continue

            # Parse uncalled bets in the summary section (skip if already found in main text)
            uncalled_bet_match = self.UNCALLED_BET_PATTERN.search(line)
            if uncalled_bet_match:
                try:
                    amount_str = uncalled_bet_match.group(1).replace(',', '')
                    amount = float(amount_str)
                    player_name = uncalled_bet_match.group(2).strip()
                    returned_bet_data = {
                        'player_name': player_name,
                        'amount': amount
                    }
                    # Check if this returned bet is already recorded
                    if not any(b['player_name'] == player_name and abs(b['amount'] - amount) < 0.01 for b in pot_data['returned_bets']):
                        pot_data['returned_bets'].append(returned_bet_data)
                        logger.info(f"Added returned bet from summary: {amount} to {player_name}")
                    continue # Processed as uncalled bet
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing uncalled bet: {e}. Line: {line}")

            # Parse winners using seat-based patterns
            processed_winner = False
            seat_won_match = self.SEAT_WON_PATTERN.search(line)
            if seat_won_match:
                try:
                    player_name = seat_won_match.group(1).strip()
                    amount_str = seat_won_match.group(2).replace('$', '').replace(',', '')
                    amount = float(amount_str)
                    pot_type = seat_won_match.group(3)
                    pot_number = seat_won_match.group(4)
                    self._add_winner_to_pot(pot_data, player_name, amount, pot_type, pot_number)
                    processed_winner = True
                except (ValueError, IndexError) as e:
                     logger.warning(f"Error parsing SEAT_WON_PATTERN: {e}. Line: {line}")
            
            if processed_winner: continue

            seat_won_no_show_match = self.SEAT_WON_NO_SHOW_PATTERN.search(line)
            if seat_won_no_show_match:
                try:
                    player_name = seat_won_no_show_match.group(1).strip()
                    amount_str = seat_won_no_show_match.group(2).replace('$', '').replace(',', '')
                    amount = float(amount_str)
                    pot_type = seat_won_no_show_match.group(3)
                    pot_number = seat_won_no_show_match.group(4)
                    self._add_winner_to_pot(pot_data, player_name, amount, pot_type, pot_number)
                    processed_winner = True
                except (ValueError, IndexError) as e:
                     logger.warning(f"Error parsing SEAT_WON_NO_SHOW_PATTERN: {e}. Line: {line}")

            if processed_winner: continue

            seat_collected_match = self.SEAT_COLLECTED_PATTERN.search(line)
            if seat_collected_match:
                try:
                    player_name = seat_collected_match.group(1).strip()
                    amount_str = seat_collected_match.group(2).replace('$', '').replace(',', '')
                    amount = float(amount_str)
                    self._add_winner_to_pot(pot_data, player_name, amount, pot_type='main')
                    
                    # We don't add to pot_collections from the summary section
                    # to avoid double-counting with collections found in the main hand text
                    logger.info(f"Found pot collection in summary (not adding to avoid double-counting): {player_name} collected {amount}")
                    
                    processed_winner = True
                except (ValueError, IndexError) as e:
                     logger.warning(f"Error parsing SEAT_COLLECTED_PATTERN: {e}. Line: {line}")

            if processed_winner: continue

            # Parse board
            board_match = self.BOARD_PATTERN.search(line)
            if board_match:
                pot_data['board'] = board_match.group(1).split()
                continue # Processed board

        # Final check: Ensure pot amounts sum correctly
        if len(pot_data['pots']) > 1:
            calculated_total = sum(p.get('amount', 0) for p in pot_data['pots'])
            if abs(calculated_total - pot_data.get('pot', 0)) > 0.01:
                logger.warning(f"Parsed pot amounts ({[p.get('amount', 0) for p in pot_data['pots']]}) do not sum to total pot {pot_data.get('pot', 0)}")

        # Final check: Assign winners if unassigned (optional fallback)
        if pot_data['pots'] and pot_data['winners'] and not any(p.get('winners') for p in pot_data['pots']):
            if len(pot_data['pots']) == 1 and len(pot_data['winners']) == 1:
                pot_data['pots'][0]['winners'] = pot_data['winners']
