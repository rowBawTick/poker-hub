"""
New modular hand parser for PokerStars hand history files.
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from backend.parser.components.tournament_parser import TournamentParser
from backend.parser.components.player_parser import PlayerParser
from backend.parser.components.action_parser import PlayerActionParser
from backend.parser.components.pot_parser import PotParser
from backend.models import Tournament, Hand, Player, HandParticipant, Pot, PotWinner, Action

logger = logging.getLogger(__name__)



class HandParser:
    """
    Modular parser for PokerStars hand history files.
    Uses specialized components to parse different aspects of hand histories.
    """
    
    def __init__(self):
        """Initialize the hand parser with its component parsers."""
        self.tournament_parser = TournamentParser()
        self.player_parser = PlayerParser()
        self.player_action_parser = PlayerActionParser()
        self.pot_parser = PotParser()
    
    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Parse a hand history file into a list of structured hand data.
        
        Args:
            file_path: Path to the hand history file.
            
        Returns:
            List of dictionaries containing structured hand data.
            
        Raises:
            Exception: If there is an error parsing the file.
        """
        logger.info(f"Parsing hand history file: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Split the content into individual hands
            hand_texts = self._split_hands(content)
            
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
    
    def _split_hands(self, content: str) -> List[str]:
        """
        Split hand history content into individual hands.
        
        Args:
            content: Full content of a hand history file.
            
        Returns:
            List of strings, each containing a single hand history.
        """
        import re
        return re.split(r'\n\n+', content)
    
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
            
        # Split the hand text into lines once
        lines = hand_text.strip().split('\n')
        
        # Parse tournament and hand information
        tournament_data = self.tournament_parser.parse_tournament_info_lines(lines)
        if not tournament_data:
            logger.warning("Could not parse tournament data from hand")
            return None
        
        # Use the remaining lines from tournament parsing for subsequent parsers
        remaining_lines = tournament_data.pop('remaining_lines', lines)
        
        # Parse player information
        player_data = self.player_parser.parse_hand_participant_lines(remaining_lines)
        if not player_data:
            logger.warning("Could not parse player data from hand")
            return None
        
        # Use the remaining lines from player parsing for action parsing
        remaining_lines = player_data.pop('remaining_lines', remaining_lines)
        
        # Parse action information
        action_data = self.player_action_parser.parse_action_lines(remaining_lines)
        if not action_data:
            logger.warning("Could not parse action data from hand")
            return None
        
        # Use the remaining lines from action parsing for pot parsing
        # These should primarily be the summary section lines
        remaining_lines = action_data.pop('remaining_lines', remaining_lines)
        
        # Parse pot and winner information
        pot_data = self.pot_parser.parse_pot_lines(remaining_lines)
        if not pot_data:
            logger.warning("Could not parse pot data from hand")
            return None
        
        # Combine all data into a single hand data structure
        hand_data = {
            'hand_id': tournament_data.get('hand_id'),
            'tournament_id': tournament_data.get('tournament_id'),
            'game_type': tournament_data.get('game_type'),
            'date_time': tournament_data.get('date_time'),
            'small_blind': tournament_data.get('small_blind'),
            'big_blind': tournament_data.get('big_blind'),
            'table_name': tournament_data.get('table_name'),
            'max_players': tournament_data.get('max_players'),
            'button_seat': tournament_data.get('button_seat'),
            'participants': player_data.get('players', []),
            'actions': action_data.get('actions', []),
            'pot': pot_data.get('pot', 0),
            'rake': pot_data.get('rake', 0),
            'board': pot_data.get('board', []),
            'pots': pot_data.get('pots', []),
            'winners': pot_data.get('winners', []),
            'returned_bets': pot_data.get('returned_bets', []),
            'pot_collections': pot_data.get('pot_collections', [])
        }
        
        # Mark players with special positions
        self._mark_player_positions(hand_data)
        
        # Calculate net profit for each participant
        self._calculate_net_profit(hand_data)
        
        return hand_data
    
    def _mark_player_positions(self, hand_data: Dict[str, Any]) -> None:
        """
        Mark players with special positions (button, small blind, big blind).
        
        Args:
            hand_data: Hand data dictionary to update.
        """
        button_seat = hand_data.get('button_seat')
        
        # Mark the button player
        if button_seat:
            for participant in hand_data['participants']:
                if participant['seat'] == button_seat:
                    participant['is_button'] = True
                    break
        
        # Mark small blind and big blind players based on actions
        for action in hand_data['actions']:
            if action['action_type'] == 'small_blind':
                player_name = action['player_name']
                for participant in hand_data['participants']:
                    if participant['name'] == player_name:
                        participant['is_small_blind'] = True
                        break
            
            if action['action_type'] == 'big_blind':
                player_name = action['player_name']
                for participant in hand_data['participants']:
                    if participant['name'] == player_name:
                        participant['is_big_blind'] = True
                        break
    
    def _calculate_net_profit(self, hand_data: Dict[str, Any]) -> None:
        """
        Calculate net profit for each participant.
        
        Args:
            hand_data: Hand data dictionary to update.
        """
        # Special case for preflop walk scenario
        is_preflop_walk = self._is_preflop_walk(hand_data)
        
        if is_preflop_walk:
            # Handle preflop walk scenario with precise calculations
            self._calculate_preflop_walk_profits(hand_data)
        else:
            # Standard calculation for other scenarios
            self._calculate_standard_profits(hand_data)
    
    def _is_preflop_walk(self, hand_data: Dict[str, Any]) -> bool:
        """
        Determine if this is a preflop walk scenario.
        
        A preflop walk is when everyone folds to the big blind.
        
        Args:
            hand_data: Hand data dictionary.
            
        Returns:
            True if this is a preflop walk scenario, False otherwise.
        """
        # Check if there's a pot collection but no returned bets
        if hand_data.get('pot_collections') and not hand_data.get('returned_bets'):
            # Check if all actions are either ante, small blind, big blind, or fold
            action_types = set(action['action_type'] for action in hand_data['actions'])
            valid_types = {'ante', 'small_blind', 'big_blind', 'fold'}
            return action_types.issubset(valid_types)
        return False
    
    def _calculate_preflop_walk_profits(self, hand_data: Dict[str, Any]) -> None:
        """
        Calculate net profits for a preflop walk scenario.
        
        In a preflop walk:
        - Small blind loses ante + small blind
        - Big blind wins the pot minus their contribution
        - All other players lose only their ante
        
        Args:
            hand_data: Hand data dictionary to update.
        """
        logger.info("Calculating profits for preflop walk scenario")
        
        # Find players by position
        small_blind = next((p for p in hand_data['participants'] if p.get('is_small_blind')), None)
        big_blind = next((p for p in hand_data['participants'] if p.get('is_big_blind')), None)
        regular_players = [p for p in hand_data['participants'] 
                          if not (p.get('is_small_blind') or p.get('is_big_blind'))]
        
        # Find ante amount (assume all antes are the same)
        ante_amount = 0
        for action in hand_data['actions']:
            if action['action_type'] == 'ante':
                ante_amount = action.get('amount', 0)
                break
        
        # Calculate profits
        if small_blind:
            # Small blind loses ante + small blind
            small_blind_amount = hand_data.get('small_blind', 0)
            small_blind['net_profit'] = -(ante_amount + small_blind_amount)
            logger.info(f"Small blind {small_blind['name']} net profit: {small_blind['net_profit']}")
        
        # Regular players lose only their ante
        for player in regular_players:
            player['net_profit'] = -ante_amount
            logger.info(f"Regular player {player['name']} net profit: {player['net_profit']}")
        
        if big_blind:
            # Big blind wins the pot minus their contribution
            big_blind_amount = hand_data.get('big_blind', 0)
            pot_amount = hand_data.get('pot', 0)
            # The big blind contributes ante + big blind, but wins the entire pot
            big_blind_contribution = ante_amount + big_blind_amount
            big_blind['net_profit'] = pot_amount - big_blind_contribution
            logger.info(f"Big blind {big_blind['name']} net profit: {big_blind['net_profit']}")
        
        # Verify the sum of all net profits is zero (no rake)
        total_net_profit = sum(p['net_profit'] for p in hand_data['participants'])
        if abs(total_net_profit) > 0.01:
            logger.warning(f"Preflop walk profit calculation may be incorrect: total={total_net_profit}, expected=0")
    
    def _calculate_standard_profits(self, hand_data: Dict[str, Any]) -> None:
        """
        Calculate net profits for standard scenarios (non-preflop walks).
        
        Args:
            hand_data: Hand data dictionary to update.
        """
        # Initialize a dictionary to track money put into the pot by each player
        player_investments = {participant['name']: 0 for participant in hand_data['participants']}
        
        # Track money put into the pot through actions
        for action in hand_data['actions']:
            if action['action_type'] in ['ante', 'small_blind', 'big_blind', 'call', 'bet', 'raise', 'all-in']:
                if 'amount' in action:
                    player_investments[action['player_name']] += action['amount']
        
        # Calculate winnings for each player
        player_winnings = {participant['name']: 0 for participant in hand_data['participants']}
        
        # Add pot winnings from winners list
        for winner in hand_data['winners']:
            player_name = winner['player_name']
            amount = winner['amount']
            player_winnings[player_name] += amount
        
        # Add returned bets (uncalled bets)
        # These are bets that were returned to the player and weren't part of the pot
        for returned_bet in hand_data.get('returned_bets', []):
            player_name = returned_bet['player_name']
            amount = returned_bet['amount']
            # For net profit calculation, returned bets should be treated as if they were never bet
            player_investments[player_name] -= amount
        
        # Calculate net profit (winnings - investments)
        for participant in hand_data['participants']:
            player_name = participant['name']
            investment = player_investments.get(player_name, 0)
            winnings = player_winnings.get(player_name, 0)
            participant['net_profit'] = winnings - investment
        
        # Verify that the sum of all net profits is close to negative rake
        # This is a sanity check to ensure our calculations are correct
        total_net_profit = sum(p['net_profit'] for p in hand_data['participants'])
        expected_net_profit = -hand_data.get('rake', 0)
        
        # If there's a significant discrepancy, log a warning
        if abs(total_net_profit - expected_net_profit) > 0.01:
            logger.warning(f"Net profit calculation may be incorrect: total={total_net_profit}, expected={expected_net_profit}")
    
    def to_database_models(self, hand_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert parsed hand data to database models.
        
        Args:
            hand_data: Dictionary containing parsed hand data.
            
        Returns:
            Dictionary containing database model instances.
        """
        # Create or get Tournament
        tournament = Tournament(
            tournament_id=hand_data['tournament_id'],
            game_type=hand_data['game_type'],
            max_players_per_table=hand_data['max_players']
        )
        
        # Create Hand
        hand = Hand(
            hand_id=hand_data['hand_id'],
            tournament=tournament,
            small_blind=hand_data['small_blind'],
            big_blind=hand_data['big_blind'],
            ante=0,  # Will be updated from actions
            pot=hand_data['pot'],
            rake=hand_data['rake'],
            board=' '.join(hand_data['board']) if hand_data['board'] else None,
            button_seat=hand_data['button_seat'],
            table_name=hand_data['table_name'],
            date_time=hand_data['date_time']
        )
        
        # Create Players and HandParticipants
        players = {}
        participants = []
        
        for participant_data in hand_data['participants']:
            # Create or get Player
            player_name = participant_data['name']
            if player_name not in players:
                players[player_name] = Player(name=player_name)
            
            # Create HandParticipant
            participant = HandParticipant(
                hand=hand,
                player=players[player_name],
                seat=participant_data['seat'],
                stack=participant_data['stack'],
                cards=' '.join(participant_data['cards']) if participant_data['cards'] else None,
                is_button=participant_data['is_button'],
                is_small_blind=participant_data['is_small_blind'],
                is_big_blind=participant_data['is_big_blind'],
                showed_cards=participant_data['showed_cards'],
                net_profit=participant_data['net_profit']
            )
            participants.append(participant)
        
        # Create Pots and PotWinners
        pots = []
        pot_winners = []
        
        for pot_data in hand_data['pots']:
            pot = Pot(
                hand=hand,
                pot_type=pot_data['pot_type'],
                amount=pot_data['amount']
            )
            pots.append(pot)
            
            for winner_data in pot_data['winners']:
                player_name = winner_data['player_name']
                # Find the participant for this player
                participant = next((p for p in participants if p.player.name == player_name), None)
                if participant:
                    pot_winner = PotWinner(
                        pot=pot,
                        participant=participant,
                        amount=winner_data['amount']
                    )
                    pot_winners.append(pot_winner)
        
        # Create Actions
        actions = []
        
        for action_data in hand_data['actions']:
            player_name = action_data['player_name']
            # Find the participant for this player
            participant = next((p for p in participants if p.player.name == player_name), None)
            if participant:
                action = Action(
                    hand=hand,
                    participant=participant,
                    street=action_data['street'],
                    action_type=action_data['action_type'],
                    amount=action_data.get('amount'),
                    sequence=action_data['sequence'],
                    is_all_in=action_data.get('is_all_in', False)
                )
                actions.append(action)
                
                # Update ante amount in hand if this is an ante action
                if action_data['action_type'] == 'ante' and action_data.get('amount', 0) > hand.ante:
                    hand.ante = action_data['amount']
        
        return {
            'tournament': tournament,
            'hand': hand,
            'players': list(players.values()),
            'participants': participants,
            'pots': pots,
            'pot_winners': pot_winners,
            'actions': actions
        }
