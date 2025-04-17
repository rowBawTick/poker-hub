"""
Tests for the tournament parser component.
"""
import unittest
from pathlib import Path

from backend.parser.components.tournament_parser import TournamentParser


class TestTournamentParser(unittest.TestCase):
    """Test cases for the tournament parser component."""
    
    def setUp(self):
        """Set up the test environment."""
        self.parser = TournamentParser()
        self.example_hands_dir = Path(__file__).parent.parent.parent / "example_hands"
    
    def test_parse_hand_lines_basic(self):
        """Test parsing tournament data from basic hand lines."""
        # Define test variables
        hand_id = "224162543163"
        tournament_id = "3333333333"
        game_type = "Hold'em No Limit"
        small_blind = 10
        big_blind = 20
        table_name = f"{tournament_id} 1"
        max_players = 9
        button_seat = 5
        date = "2025/01/01"
        time = "12:00:00"
        
        # Create test hand lines using the variables
        lines = [
            f"PokerStars Hand #{hand_id}: Tournament #{tournament_id}, $0.25+$0.00 USD {game_type} - Level I ({small_blind}/{big_blind}) - {date} {time} ET",
            f"Table '{table_name}' {max_players}-max Seat #{button_seat} is the button",
            "Seat 1: Player1 (1500 in chips)",
            "Seat 2: Player2 (1500 in chips)"
        ]
        
        result = self.parser.parse_tournament_info_lines(lines)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['hand_id'], hand_id)
        self.assertEqual(result['tournament_id'], tournament_id)
        self.assertEqual(result['game_type'], game_type)
        self.assertEqual(result['small_blind'], float(small_blind))
        self.assertEqual(result['big_blind'], float(big_blind))
        self.assertEqual(result['table_name'], table_name)
        self.assertEqual(result['max_players'], max_players)
        self.assertEqual(result['button_seat'], button_seat)
        
        # Verify remaining lines are returned
        self.assertIn('remaining_lines', result)
        self.assertEqual(len(result['remaining_lines']), 2)  # The two seat lines
    
    def test_parse_from_file(self):
        """Test parsing tournament data from an actual hand history file."""
        # Find a preflop walk example file
        preflop_walk_file = self.example_hands_dir / "preflop-walk.txt"
        
        if not preflop_walk_file.exists():
            self.skipTest(f"Example file {preflop_walk_file} not found")
        
        # Read the file and get the first hand
        with open(preflop_walk_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into hands and take the first one
        import re
        hands = re.split(r'\n\n+', content)
        first_hand = hands[0] if hands else ""
        
        if not first_hand:
            self.skipTest("No hands found in example file")
        
        # Parse the hand
        lines = first_hand.strip().split('\n')
        result = self.parser.parse_tournament_info_lines(lines)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('hand_id', result)
        self.assertIn('tournament_id', result)
        self.assertIn('game_type', result)
        self.assertIn('small_blind', result)
        self.assertIn('big_blind', result)
        self.assertIn('table_name', result)
        self.assertIn('max_players', result)
        self.assertIn('button_seat', result)
        self.assertIn('remaining_lines', result)


if __name__ == '__main__':
    unittest.main()
