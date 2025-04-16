"""
Unit tests for the pot parser component.
"""
import unittest
from typing import Dict, Any, List

from backend.parser.components.pot_parser import PotParser


class TestPotParser(unittest.TestCase):
    """Test cases for the PotParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.pot_parser = PotParser()
    
    def test_real_showdown_hand(self):
        """Test parsing a real showdown hand from PokerStars."""
        hand_text = """
*** SUMMARY ***
Total pot 2775 | Rake 0
Board [Tc 3c Qd Js Jh]
Seat 3: Player1 (small blind) showed [3d Ad] and won (2775) with two pair, Jacks and Threes
Seat 4: Player2 (big blind) folded before Flop
Seat 5: Player3 folded before Flop (didn't bet)
Seat 6: Player4 folded before Flop (didn't bet)
Seat 7: Player5 folded before Flop (didn't bet)
Seat 8: Player6 folded before Flop (didn't bet)
Seat 9: Player7 (button) mucked [Ac 4h]
"""
        
        # Parse the hand
        result = self.pot_parser.parse_hand(hand_text)
        
        # Verify the basic pot information
        self.assertEqual(result['pot'], 2775.0)
        self.assertEqual(result['rake'], 0.0)
        
        # Verify the pot structure
        self.assertEqual(len(result['pots']), 1)
        main_pot = result['pots'][0]
        self.assertEqual(main_pot['pot_type'], 'main')
        self.assertEqual(main_pot['amount'], 2775.0)
        
        # Verify the board cards
        self.assertEqual(result['board'], ['Tc', '3c', 'Qd', 'Js', 'Jh'])
        
        # Check if the winner is correctly identified from the 'won' text
        # Note: In this test, we're not checking pot_collections since there's no explicit 'collected' line
        winner_from_seat = next((w for w in result['winners'] if w['player_name'] == 'Player1'), None)
        self.assertIsNotNone(winner_from_seat, "Winner should be identified from seat line with 'won' text")
        if winner_from_seat:
            self.assertEqual(winner_from_seat['amount'], 2775.0)
    
    def test_real_preflop_walk(self):
        """Test parsing a real preflop walk hand from PokerStars."""
        hand_text = """
*** SUMMARY ***
Total pot 7000 | Rake 0
Seat 1: Player1 (small blind) folded before Flop
Seat 2: Player2 (big blind) collected (7000)
Seat 3: Player3 folded before Flop (didn't bet)
Seat 4: Player4 folded before Flop (didn't bet)
Seat 5: Player5 folded before Flop (didn't bet)
Seat 6: Player6 folded before Flop (didn't bet)
Seat 7: Player7 folded before Flop (didn't bet)
Seat 8: Player8 (button) folded before Flop (didn't bet)
"""
        
        # Parse the hand
        result = self.pot_parser.parse_hand(hand_text)
        
        # Verify the pot information
        self.assertEqual(result['pot'], 7000.0)
        self.assertEqual(result['rake'], 0.0)
        
        # Check if the winner is correctly identified from the 'collected' text
        # This is a case where there's no explicit 'Player collected X from pot' line
        # but instead 'Seat X: Player (big blind) collected (amount)'
        winner_from_seat = next((w for w in result['winners'] if w['player_name'] == 'Player2'), None)
        self.assertIsNotNone(winner_from_seat, "Winner should be identified from seat line with 'collected' text")
        if winner_from_seat:
            self.assertEqual(winner_from_seat['amount'], 7000.0)
    
    def test_uncalled_bet_returned(self):
        """Test parsing a hand where an uncalled bet is returned to a player."""
        hand_text = """
*** SUMMARY ***
Total pot 150 | Rake 0
Board [Ah Kd Qc Js Th]
Seat 1: Player1 (button) folded before Flop (didn't bet)
Seat 2: Player2 (small blind) folded before Flop
Seat 3: Player3 (big blind) folded on the Flop
Seat 4: Player4 showed [Ad Kh] and won (100) with a straight, Ace to Ten
Uncalled bet (50) returned to Player4
"""
        
        # Parse the hand
        result = self.pot_parser.parse_hand(hand_text)
        
        # Verify the pot information
        self.assertEqual(result['pot'], 150.0)
        self.assertEqual(result['rake'], 0.0)
        
        # Verify the winner information from the 'won' text
        winner_from_seat = next((w for w in result['winners'] if w['player_name'] == 'Player4'), None)
        self.assertIsNotNone(winner_from_seat, "Winner should be identified from seat line with 'won' text")
        if winner_from_seat:
            self.assertEqual(winner_from_seat['amount'], 100.0)
        
        # Verify the returned bet
        self.assertEqual(len(result['returned_bets']), 1)
        returned_bet = result['returned_bets'][0]
        self.assertEqual(returned_bet['player_name'], 'Player4')
        self.assertEqual(returned_bet['amount'], 50.0)
    
    def test_multiple_winners(self):
        """Test parsing a hand with multiple winners (split pot)."""
        hand_text = """
*** SUMMARY ***
Total pot 200 | Rake 0
Board [Ah Kd Qc Js Th]
Seat 1: Player1 (button) folded before Flop (didn't bet)
Seat 2: Player2 (small blind) showed [Ad Qh] and won (100) with a straight, Ace to Ten
Seat 3: Player3 (big blind) showed [Ac Qs] and won (100) with a straight, Ace to Ten
Seat 4: Player4 folded on the Turn
"""
        
        # Parse the hand
        result = self.pot_parser.parse_hand(hand_text)
        
        # Verify the pot information
        self.assertEqual(result['pot'], 200.0)
        
        # Verify the winner information from the 'won' text
        self.assertEqual(len(result['winners']), 2)
        
        # First winner
        winner1 = next((w for w in result['winners'] if w['player_name'] == 'Player2'), None)
        self.assertIsNotNone(winner1, "First winner should be identified")
        if winner1:
            self.assertEqual(winner1['amount'], 100.0)
        
        # Second winner
        winner2 = next((w for w in result['winners'] if w['player_name'] == 'Player3'), None)
        self.assertIsNotNone(winner2, "Second winner should be identified")
        if winner2:
            self.assertEqual(winner2['amount'], 100.0)
    
    def test_side_pot(self):
        """Test parsing a hand with a main pot and a side pot."""
        hand_text = """
*** SUMMARY ***
Total pot 300 Main pot 200. Side pot 100. | Rake 0
Board [Ah Kd Qc Js Th]
Seat 1: Player1 (button) folded before Flop (didn't bet)
Seat 2: Player2 (small blind) showed [Ad Qh] and won (200) from main pot
Seat 3: Player3 (big blind) showed [Ac Qs] and won (100) from side pot-1
Seat 4: Player4 folded on the Turn
"""
        
        # Parse the hand
        result = self.pot_parser.parse_hand(hand_text)
        
        # Verify the pot information
        self.assertEqual(result['pot'], 300.0)
        
        # Verify the pot structure
        self.assertEqual(len(result['pots']), 2)
        
        # Main pot
        main_pot = result['pots'][0]
        self.assertEqual(main_pot['pot_type'], 'main')
        self.assertEqual(main_pot['amount'], 200.0)
        
        # Side pot
        side_pot = result['pots'][1]
        self.assertEqual(side_pot['pot_type'], 'side-1')
        self.assertEqual(side_pot['amount'], 100.0)
        
        # Verify winners from 'won from main/side pot' text
        winner1 = next((w for w in result['winners'] if w['player_name'] == 'Player2'), None)
        self.assertIsNotNone(winner1, "Main pot winner should be identified")
        if winner1:
            self.assertEqual(winner1['amount'], 200.0)
            
        winner2 = next((w for w in result['winners'] if w['player_name'] == 'Player3'), None)
        self.assertIsNotNone(winner2, "Side pot winner should be identified")
        if winner2:
            self.assertEqual(winner2['amount'], 100.0)


if __name__ == '__main__':
    unittest.main()
