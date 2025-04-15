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
    
    # Default PokerStars labels if none are provided
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
    
    # Use provided labels or defaults
    if labels and len(labels) > 0:
        for label in labels:
            label_elem = ET.SubElement(labels_elem, "label")
            label_elem.set("id", str(label["label_id"]))
            label_elem.set("color", label["color"])
            label_elem.text = label["name"]
    else:
        # Use default labels
        for label in default_labels:
            label_elem = ET.SubElement(labels_elem, "label")
            label_elem.set("id", str(label["label_id"]))
            label_elem.set("color", label["color"])
            label_elem.text = label["name"]
    
    # Add notes
    for note in notes:
        note_elem = ET.SubElement(root, "note")
        note_elem.set("player", note["player_name"])
        
        if note["label_id"] is not None and note["label_id"] != -1:
            note_elem.set("label", str(note["label_id"]))
        
        # Convert datetime to timestamp
        timestamp = int(note["last_updated"].timestamp())
        note_elem.set("update", str(timestamp))
        
        # For empty notes, still include the closing tag instead of self-closing tag
        if note["content"]:
            # Escape apostrophes as &apos; for PokerStars compatibility
            content = note["content"].replace("'", "&apos;")
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
        # Create a custom XML string with proper formatting
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>\n'
        
        # Convert the ElementTree to a string
        rough_string = ET.tostring(root, 'utf-8')
        
        # Parse with minidom to get pretty formatting
        import xml.dom.minidom
        reparsed = xml.dom.minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent='\t')
        
        # Remove extra blank lines that minidom adds
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        pretty_xml = '\n'.join(lines)
        
        # Replace self-closing tags with explicit closing tags
        pretty_xml = pretty_xml.replace('/>', "></note>")
        
        # Replace the XML declaration with our custom one
        if pretty_xml.startswith('<?xml'):
            pretty_xml = xml_declaration + pretty_xml[pretty_xml.find('?>') + 2:]
        else:
            pretty_xml = xml_declaration + pretty_xml
            
        # Make sure ampersands in content are properly encoded
        pretty_xml = pretty_xml.replace("&amp;", "&amp;amp;")
        
        # Make sure apostrophes are properly encoded
        pretty_xml = pretty_xml.replace("'", "&apos;")
        
        # Write to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        logger.info(f"Successfully wrote XML to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing XML to {file_path}: {e}")
        return False
