#!/usr/bin/env python3
"""
XML utilities for poker notes management.

This module provides utilities for parsing and generating XML files for poker notes.
"""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_xml_file(file_path: str) -> Tuple[Dict[int, Dict], List[Dict]]:
    """
    Parse an XML notes file.
    
    Args:
        file_path: Path to the XML file.
        
    Returns:
        Tuple of (labels_dict, notes_list).
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Parse labels
        labels = {}
        labels_elem = root.find("labels")
        if labels_elem is not None:
            for label_elem in labels_elem.findall("label"):
                label_id = int(label_elem.get("id", "-1"))
                color = label_elem.get("color", "")
                name = label_elem.text or f"Label {label_id}"
                labels[label_id] = {
                    "id": label_id,
                    "color": color,
                    "name": name
                }
        
        # Parse notes
        notes = []
        for note_elem in root.findall("note"):
            player = note_elem.get("player", "")
            label_id_str = note_elem.get("label", "-1")
            label_id = int(label_id_str) if label_id_str.isdigit() else -1
            update_str = note_elem.get("update", "0")
            update_timestamp = int(update_str) if update_str.isdigit() else 0
            
            # Convert timestamp to datetime
            update_datetime = datetime.fromtimestamp(update_timestamp)
            
            content = note_elem.text or ""
            
            notes.append({
                "player": player,
                "label_id": label_id,
                "content": content,
                "updated": update_datetime,
                "source_file": file_path
            })
        
        logger.info(f"Parsed {len(notes)} notes and {len(labels)} labels from {file_path}")
        return labels, notes
        
    except Exception as e:
        logger.error(f"Error parsing XML file {file_path}: {e}")
        return {}, []


def generate_xml(username: str, labels: List[Dict], notes: List[Dict]) -> ET.Element:
    """
    Generate XML for poker notes in the exact format PokerStars expects.
    
    Args:
        username: Username for the notes.
        labels: List of label dictionaries.
        notes: List of note dictionaries.
        
    Returns:
        XML Element tree root.
    """
    # Create root element with version attribute
    root = ET.Element("notes")
    root.set("version", "1")
    
    # Use the exact PokerStars default labels
    default_labels = [
        {"label_id": 0, "color": "30DBFF", "name": "Conservative"},
        {"label_id": 1, "color": "30FF97", "name": "Solid"},
        {"label_id": 2, "color": "E1FF80", "name": "Neutral"},
        {"label_id": 3, "color": "FF9B30", "name": "Custom Label 4"},
        {"label_id": 4, "color": "FF304E", "name": "Bad player"},
        {"label_id": 5, "color": "FF30D7", "name": "Aggressive"},
        {"label_id": 6, "color": "303EFF", "name": "Reckless"},
        {"label_id": 7, "color": "1985FF", "name": "Loose"}
    ]
    
    # Add labels
    labels_elem = ET.SubElement(root, "labels")
    for label in default_labels:
        label_elem = ET.SubElement(labels_elem, "label")
        label_elem.set("id", str(label["label_id"]))
        label_elem.set("color", label["color"])
        label_elem.text = label["name"]
    
    # Add notes
    for note in notes:
        # Get player name and handle special cases
        player_name = note["player_name"]
        
        # Skip notes with empty player names
        if not player_name or player_name.strip() == "":
            continue
            
        # Create note element
        note_elem = ET.SubElement(root, "note")
        
        # PokerStars handles these special characters in player names differently
        # We need to ensure they're preserved exactly as they appear
        # Characters like #, !, +, (, ), -, spaces, etc. should be kept as-is
        # We don't encode these special characters in player names
        note_elem.set("player", player_name)
        
        # Set label ID, defaulting to 2 (Neutral) if not specified
        label_id = note["label_id"]
        if label_id is not None and label_id != -1:
            # Ensure label ID is within valid range (0-7)
            if 0 <= label_id <= 7:
                note_elem.set("label", str(label_id))
            else:
                note_elem.set("label", "2")  # Default to Neutral
        else:
            note_elem.set("label", "2")  # Default to Neutral
        
        # Convert datetime to timestamp
        timestamp = int(note["last_updated"].timestamp())
        note_elem.set("update", str(timestamp))
        
        # Handle content with proper encoding
        if note["content"]:
            # Clean and encode the content for PokerStars compatibility
            content = note["content"]
            # Replace apostrophes
            content = content.replace("'", "&apos;")
            # Replace ampersands
            content = content.replace("&", "&amp;")
            # Replace less than/greater than
            content = content.replace("<", "&lt;").replace(">", "&gt;")
            # Replace quotes
            content = content.replace('"', "&quot;")
            
            note_elem.text = content
        else:
            note_elem.text = ""
    
    return root


def write_xml_to_file(root: ET.Element, file_path: str) -> bool:
    """
    Write XML to file in the exact format PokerStars expects.
    
    Args:
        root: XML Element tree root.
        file_path: Path to write the XML file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        # Create the XML declaration exactly as PokerStars expects
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        # Convert the ElementTree to a string manually to ensure proper formatting
        xml_lines = [xml_declaration]
        xml_lines.append('<notes version="1">\n')
        
        # Add labels section
        xml_lines.append('\t<labels>\n')
        for label_elem in root.find('labels').findall('label'):
            label_id = label_elem.get('id')
            color = label_elem.get('color')
            name = label_elem.text or f"Label {label_id}"
            xml_lines.append(f'\t\t<label id="{label_id}" color="{color}">{name}</label>\n')
        xml_lines.append('\t</labels>\n')
        
        # Add notes section
        for note_elem in root.findall('note'):
            player = note_elem.get('player')
            label = note_elem.get('label', '2')
            update = note_elem.get('update', '0')
            content = note_elem.text or ""
            
            # Ensure player name is preserved exactly as-is
            # PokerStars expects these special characters to be unencoded in the XML
            # Start note tag
            note_line = f'\t<note player="{player}" label="{label}" update="{update}"'
            
            # If content is empty, use self-closing tag format that PokerStars expects
            if not content.strip():
                note_line += "></note>\n"
            else:
                note_line += f">{content}</note>\n"
                
            xml_lines.append(note_line)
        
        # Close notes tag
        xml_lines.append('</notes>\n')
        
        # Join all lines to create the final XML
        xml_content = ''.join(xml_lines)
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        logger.info(f"Successfully wrote XML to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing XML to {file_path}: {e}")
        return False
