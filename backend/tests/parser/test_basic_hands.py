"""
Tests for basic hand parsing scenarios using the new modular hand parser.
"""
import unittest
from pathlib import Path

from backend.parser.new_hand_parser import HandParser


class TestBasicHandParsing(unittest.TestCase):
    """Test class for basic hand parsing scenarios."""
    
    def setUp(self):
        """Set up the test environment."""
        self.parser = HandParser()
        self.example_hands_dir = Path(__file__).parent.parent.parent / "example_hands"
    
    def test_preflop_walk(self):
        """
        Test parsing a preflop walk hand where everyone folds to the big blind.
        
        This tests:
        1. The big blind player wins the pot
        2. Each player's net_profit is calculated correctly
        3. The sum of all players' net_profit equals zero (since there's no rake)
        """
        # Parse the hand
        hand_file = self.example_hands_dir / "preflop-walk.txt"
        hands = self.parser.parse_file(hand_file)
        
        # Verify we got exactly one hand
        self.assertEqual(len(hands), 1, "Should parse exactly one hand")
        
        hand = hands[0]
        
        # Verify basic hand information
        self.assertEqual(hand['hand_id'], "255510109389")
        self.assertEqual(hand['tournament_id'], "3872576931")
        self.assertEqual(hand['small_blind'], 1500)
        self.assertEqual(hand['big_blind'], 3000)
        self.assertEqual(hand['pot'], 7000)
        self.assertEqual(hand['rake'], 0)
        
        # Verify participants
        self.assertEqual(len(hand['participants']), 8, "Should have 8 participants")
        
        # Find players by position
        small_blind = next(player for player in hand['participants'] if player['is_small_blind'])
        big_blind = next(player for player in hand['participants'] if player['is_big_blind'])
        regular_players = [
            player for player in hand['participants'] if not (player['is_small_blind'] or player['is_big_blind'])
        ]
        
        # Verify player names
        self.assertEqual(small_blind['name'], "Player1")
        self.assertEqual(big_blind['name'], "Player2")
        
        # Verify net profit calculations
        # Small blind should lose ante + small blind
        self.assertEqual(small_blind['net_profit'], -2000)  # -500 (ante) - 1500 (small blind)
        
        # Big blind should win the pot and returned bets minus their investments
        # The calculation is: - investments (-500 ante -3000 BB) + bet returned (1500) + winnings/pot (7000)
        expected_big_blind_profit = - 3500 + 1500 + 7000
        self.assertEqual(big_blind['net_profit'], expected_big_blind_profit)
        
        # Regular players should only lose their ante
        for player in regular_players:
            self.assertEqual(player['net_profit'], -500, f"{player['name']} should lose only the ante")
        
        # Verify the sum of all net profits is zero (no rake)
        total_net_profit = sum(participant['net_profit'] for participant in hand['participants'])
        self.assertEqual(total_net_profit, 0, "Sum of all net profits should be zero when there's no rake")
        
        # Verify the winner
        self.assertEqual(len(hand['winners']), 1, "Should have exactly one winner")
        self.assertEqual(hand['winners'][0]['player_name'], "Player2")
        self.assertEqual(hand['winners'][0]['amount'], 7000)
        
        # Verify pots
        self.assertEqual(len(hand['pots']), 1, "Should have exactly one pot")
        self.assertEqual(hand['pots'][0]['pot_type'], "main")
        self.assertEqual(hand['pots'][0]['amount'], 7000)
        self.assertEqual(len(hand['pots'][0]['winners']), 1)
        self.assertEqual(hand['pots'][0]['winners'][0]['player_name'], "Player2")
        self.assertEqual(hand['pots'][0]['winners'][0]['amount'], 7000)


if __name__ == '__main__':
    unittest.main()
