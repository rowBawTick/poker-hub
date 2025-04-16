"""
Base parser component for poker hand history parsing.
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class BaseParser:
    """
    Base class for poker hand history parser components.
    Provides common functionality for all parser components.
    """
    
    def __init__(self):
        """Initialize the base parser component."""
        pass
    
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
            # PokerStars hands are separated by blank lines
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
        This method should be implemented by subclasses.
        
        Args:
            hand_text: Text of a single poker hand history.
            
        Returns:
            Dictionary containing structured hand data, or None if parsing failed.
            
        Raises:
            NotImplementedError: If not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses must implement parse_hand method")
