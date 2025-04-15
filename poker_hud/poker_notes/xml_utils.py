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
    Generate XML for poker notes.
    
    Args:
        username: Username for the notes.
        labels: List of label dictionaries.
        notes: List of note dictionaries.
        
    Returns:
        XML Element tree root.
    """
    # Create root element
    root = ET.Element("notes")
    
    # Add labels
    if labels:
        labels_elem = ET.SubElement(root, "labels")
        for label in labels:
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
        
        note_elem.text = note["content"]
    
    return root


def write_xml_to_file(root: ET.Element, file_path: str) -> bool:
    """
    Write XML to file.
    
    Args:
        root: XML Element tree root.
        file_path: Path to write the XML file.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        logger.info(f"Successfully wrote XML to {file_path}")
        return True
    except Exception as e:
        logger.error(f"Error writing XML to {file_path}: {e}")
        return False
