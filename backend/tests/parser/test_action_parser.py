"""
Tests for the player action parser component.
"""
import unittest
from pathlib import Path

from backend.parser.components.action_parser import PlayerActionParser


class TestPlayerActionParser(unittest.TestCase):
    """Test cases for the player action parser component."""
    
    def setUp(self):
        """Set up the test environment."""
        self.parser = PlayerActionParser()
        self.example_hands_dir = Path(__file__).parent.parent.parent / "example_hands"
    
    def test_parse_action_lines_basic(self):
        """Test parsing action data from basic hand lines."""
        # Define test variables
        player1_name = "Player1"
        player2_name = "Player2"
        player3_name = "Player3"
        
        ante_amount = 2
        small_blind = 10
        big_blind = 20
        call_amount = 20
        raise_amount = 60
        
        # Create test hand lines using the variables
        lines = [
            f"{player1_name}: posts the ante {ante_amount}",
            f"{player2_name}: posts the ante {ante_amount}",
            f"{player3_name}: posts the ante {ante_amount}",
            f"{player1_name}: posts small blind {small_blind}",
            f"{player2_name}: posts big blind {big_blind}",
            "*** HOLE CARDS ***",
            f"{player3_name}: folds",
            f"{player1_name}: calls {call_amount}",
            f"{player2_name}: checks",
            "*** FLOP *** [Jh 7d 4s]",
            f"{player1_name}: checks",
            f"{player2_name}: bets {big_blind}",
            f"{player1_name}: raises {raise_amount} to {raise_amount + big_blind}",
            f"{player2_name}: calls {raise_amount}",
            "*** TURN *** [Jh 7d 4s] [2c]",
            f"{player1_name}: checks",
            f"{player2_name}: checks",
            "*** RIVER *** [Jh 7d 4s 2c] [Ah]",
            f"{player1_name}: bets {big_blind * 2}",
            f"{player2_name}: raises {big_blind * 6} to {big_blind * 8} and is all-in",
            f"{player1_name}: calls {big_blind * 6}",
            "*** SHOW DOWN ***",
            "*** SUMMARY ***"
        ]
        
        result = self.parser.parse_action_lines(lines)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('actions', result)
        
        actions = result['actions']
        self.assertGreater(len(actions), 0)
        
        # Check ante actions
        ante_actions = [a for a in actions if a['action_type'] == 'ante']
        self.assertEqual(len(ante_actions), 3)
        for action in ante_actions:
            self.assertEqual(action['amount'], ante_amount)
            self.assertEqual(action['street'], 'preflop')
            self.assertFalse(action['is_all_in'])
        
        # Check small blind action
        sb_actions = [a for a in actions if a['action_type'] == 'small_blind']
        self.assertEqual(len(sb_actions), 1)
        self.assertEqual(sb_actions[0]['player_name'], player1_name)
        self.assertEqual(sb_actions[0]['amount'], small_blind)
        
        # Check big blind action
        bb_actions = [a for a in actions if a['action_type'] == 'big_blind']
        self.assertEqual(len(bb_actions), 1)
        self.assertEqual(bb_actions[0]['player_name'], player2_name)
        self.assertEqual(bb_actions[0]['amount'], big_blind)
        
        # Check fold action
        fold_actions = [a for a in actions if a['action_type'] == 'fold']
        self.assertEqual(len(fold_actions), 1)
        self.assertEqual(fold_actions[0]['player_name'], player3_name)
        self.assertEqual(fold_actions[0]['street'], 'preflop')
        
        # Check call actions
        call_actions = [a for a in actions if a['action_type'] == 'call']
        self.assertGreaterEqual(len(call_actions), 2)
        
        # Check raise actions
        raise_actions = [a for a in actions if a['action_type'] == 'raise']
        self.assertGreaterEqual(len(raise_actions), 1)
        
        # Check all-in action
        all_in_actions = [a for a in actions if a['is_all_in']]
        self.assertEqual(len(all_in_actions), 1)
        self.assertEqual(all_in_actions[0]['player_name'], player2_name)
        
        # Verify remaining lines are returned
        self.assertIn('remaining_lines', result)
        
    def test_parse_from_file(self):
        """Test parsing action data from an actual hand history file."""
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
        result = self.parser.parse_action_lines(lines)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertIn('actions', result)
        self.assertGreater(len(result['actions']), 0)
        
        # Check that we have the expected action types
        action_types = set(action['action_type'] for action in result['actions'])
        expected_types = {'ante', 'small_blind', 'big_blind', 'fold', 'call', 'check', 'bet', 'raise'}
        self.assertTrue(action_types.issubset(expected_types))
        
        # Verify remaining lines are returned
        self.assertIn('remaining_lines', result)


if __name__ == '__main__':
    unittest.main()
