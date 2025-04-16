"""
Tests for the player parser component.
"""
import unittest
from pathlib import Path

from backend.parser.components.player_parser import PlayerParser


class TestPlayerParser(unittest.TestCase):
    """Test cases for the player parser component."""
    
    def setUp(self):
        """Set up the test environment."""
        self.parser = PlayerParser()
        self.example_hands_dir = Path(__file__).parent.parent.parent / "example_hands"
    
    def test_parse_hand_lines_basic(self):
        """Test parsing player data from basic hand lines."""
        # Define test variables
        player1_name = "Player1"
        player1_seat = 1
        player1_stack = 1500.0
        player1_bounty = 5.25
        
        player2_name = "Player2"
        player2_seat = 2
        player2_stack = 2000.0
        
        player3_name = "Player3"
        player3_seat = 3
        player3_stack = 1800.0
        player3_cards = ["Ah", "Kh"]
        
        # Create test hand lines using the variables
        lines = [
            "PokerStars Hand #224162543163: Tournament #3333333333, $0.25+$0.00 USD Hold'em No Limit - Level I (10/20) - 2025/01/01 12:00:00 ET",
            "Table '3333333333 1' 9-max Seat #5 is the button",
            f"Seat {player1_seat}: {player1_name} ({player1_stack} in chips, ${player1_bounty} bounty)",
            f"Seat {player2_seat}: {player2_name} ({player2_stack} in chips)",
            f"Seat {player3_seat}: {player3_name} ({player3_stack} in chips)",
            f"Dealt to {player3_name} [{player3_cards[0]} {player3_cards[1]}]",
            "*** HOLE CARDS ***",
            "Player1: folds",
            "Player2: calls 20",
            "Player3: raises 40 to 60",
            "Player2: folds",
            "*** FLOP ***",
            "*** TURN ***",
            "*** RIVER ***",
            "*** SHOW DOWN ***",
            f"{player3_name}: shows [{player3_cards[0]} {player3_cards[1]}]",
            "*** SUMMARY ***"
        ]
        
        result = self.parser.parse_hand_participant_lines(lines)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('players', result)
        self.assertEqual(len(result['players']), 3)
        
        # Check player 1 details
        player1 = next((p for p in result['players'] if p['name'] == player1_name), None)
        self.assertIsNotNone(player1)
        self.assertEqual(player1['seat'], player1_seat)
        self.assertEqual(player1['stack'], player1_stack)
        self.assertEqual(player1['bounty'], player1_bounty)
        self.assertIsNone(player1['cards'])
        self.assertFalse(player1['showed_cards'])
        
        # Check player 2 details
        player2 = next((p for p in result['players'] if p['name'] == player2_name), None)
        self.assertIsNotNone(player2)
        self.assertEqual(player2['seat'], player2_seat)
        self.assertEqual(player2['stack'], player2_stack)
        self.assertIsNone(player2['bounty'])
        self.assertIsNone(player2['cards'])
        self.assertFalse(player2['showed_cards'])
        
        # Check player 3 details (with cards)
        player3 = next((p for p in result['players'] if p['name'] == player3_name), None)
        self.assertIsNotNone(player3)
        self.assertEqual(player3['seat'], player3_seat)
        self.assertEqual(player3['stack'], player3_stack)
        self.assertIsNotNone(player3['cards'])
        self.assertEqual(player3['cards'], player3_cards)
        self.assertTrue(player3['showed_cards'])
        
        # Verify remaining lines are returned
        self.assertIn('remaining_lines', result)
    
    def test_parse_from_file(self):
        """Test parsing player data from an actual hand history file."""
        # Find a preflop walk example file
        preflop_walk_file = self.example_hands_dir / "preflop-walk_anon.txt"
        
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
        result = self.parser.parse_hand_participant_lines(lines)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('players', result)
        self.assertGreater(len(result['players']), 0)
        
        # Check some basic properties of the first player
        first_player = result['players'][0]
        self.assertIn('name', first_player)
        self.assertIn('seat', first_player)
        self.assertIn('stack', first_player)
        self.assertIn('cards', first_player)
        
        # Verify remaining lines are returned
        self.assertIn('remaining_lines', result)


if __name__ == '__main__':
    unittest.main()
