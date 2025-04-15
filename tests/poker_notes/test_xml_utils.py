#!/usr/bin/env python3
"""
Tests for XML utilities for poker notes management.
"""
import os
import sys
import unittest
import tempfile
from datetime import datetime
from pathlib import Path

# Add parent directory to path to make imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.poker_notes.xml_utils import parse_xml_file, generate_xml, write_xml_to_file


class TestXmlUtils(unittest.TestCase):
    """Test cases for XML utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<notes version="1">
    <labels>
        <label id="0" color="30DBFF">Conservative</label>
        <label id="1" color="30FF97">Solid</label>
        <label id="2" color="E1FF80">Neutral</label>
        <label id="3" color="FF9B30">Custom Label 4</label>
        <label id="4" color="FF304E">Bad player</label>
        <label id="5" color="FF30D7">Aggressive</label>
        <label id="6" color="303EFF">Reckless</label>
        <label id="7" color="1985FF">Loose</label>
    </labels>
    <note player="#VILÃO!90" label="6" update="1685233626"></note>
    <note player="(CartmanBrah)-s" label="0" update="1705178160">flat-called in MP with KK after EP bet with 25BB</note>
    <note player="+ Time Passing" label="6" update="1743283440">Reckless. Limper. Aggressive. 
Willing to triple barrel bluff and get it all in on river (over-betting pot)</note>
    <note player="Player&apos;s Name" label="4" update="1705699680">Contains apostrophe &amp; ampersand</note>
</notes>
"""
        # Create a temporary file with the sample XML
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        self.temp_file.write(self.sample_xml.encode('utf-8'))
        self.temp_file.close()

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove the temporary file
        os.unlink(self.temp_file.name)

    def test_parse_xml_file(self):
        """Test parsing an XML file."""
        labels, notes = parse_xml_file(self.temp_file.name)
        
        # Check labels
        self.assertEqual(len(labels), 8)
        self.assertEqual(labels[0]["name"], "Conservative")
        self.assertEqual(labels[0]["color"], "30DBFF")
        
        # Check notes
        self.assertEqual(len(notes), 4)
        self.assertEqual(notes[0]["player"], "#VILÃO!90")
        self.assertEqual(notes[0]["label_id"], 6)
        self.assertEqual(notes[1]["player"], "(CartmanBrah)-s")
        self.assertEqual(notes[1]["content"], "flat-called in MP with KK after EP bet with 25BB")
        self.assertEqual(notes[2]["player"], "+ Time Passing")
        self.assertEqual(notes[3]["player"], "Player's Name")
        self.assertEqual(notes[3]["content"], "Contains apostrophe & ampersand")

    def test_generate_xml(self):
        """Test generating XML from data."""
        labels = [
            {"label_id": 0, "color": "30DBFF", "name": "Conservative"},
            {"label_id": 1, "color": "30FF97", "name": "Solid"}
        ]
        
        notes = [
            {
                "player_name": "#VILÃO!90",
                "label_id": 6,
                "content": "",
                "last_updated": datetime.fromtimestamp(1685233626)
            },
            {
                "player_name": "(CartmanBrah)-s",
                "label_id": 0,
                "content": "flat-called in MP with KK after EP bet with 25BB",
                "last_updated": datetime.fromtimestamp(1705178160)
            }
        ]
        
        root = generate_xml("testuser", labels, notes)
        
        # Check that the root element has the correct attributes
        self.assertEqual(root.tag, "notes")
        self.assertEqual(root.get("version"), "1")
        
        # Check labels
        labels_elem = root.find("labels")
        self.assertIsNotNone(labels_elem)
        label_elems = labels_elem.findall("label")
        # Should have 8 labels (default set) even though we only provided 2
        self.assertEqual(len(label_elems), 8)
        
        # Check notes
        note_elems = root.findall("note")
        self.assertEqual(len(note_elems), 2)
        self.assertEqual(note_elems[0].get("player"), "#VILÃO!90")
        self.assertEqual(note_elems[0].get("label"), "6")
        self.assertEqual(note_elems[1].get("player"), "(CartmanBrah)-s")
        self.assertEqual(note_elems[1].text, "flat-called in MP with KK after EP bet with 25BB")

    def test_write_xml_to_file(self):
        """Test writing XML to a file."""
        labels = [
            {"label_id": 0, "color": "30DBFF", "name": "Conservative"},
            {"label_id": 1, "color": "30FF97", "name": "Solid"}
        ]
        
        notes = [
            {
                "player_name": "#VILÃO!90",
                "label_id": 6,
                "content": "",
                "last_updated": datetime.fromtimestamp(1685233626)
            },
            {
                "player_name": "Player's Name",
                "label_id": 4,
                "content": "Contains apostrophe & ampersand",
                "last_updated": datetime.fromtimestamp(1705699680)
            }
        ]
        
        root = generate_xml("testuser", labels, notes)
        
        # Create a temporary file for the output
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        output_file.close()
        
        # Write the XML to the file
        success = write_xml_to_file(root, output_file.name)
        self.assertTrue(success)
        
        # Read the file and check its contents
        with open(output_file.name, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that the file contains the expected content
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', content)
        self.assertIn('<notes version="1">', content)
        self.assertIn('<label id="0" color="30DBFF">Conservative</label>', content)
        self.assertIn('<note player="#VILÃO!90" label="6" update="1685233626"></note>', content)
        self.assertIn('Contains apostrophe &apos; ampersand', content)
        
        # Clean up
        os.unlink(output_file.name)

    def test_special_characters_handling(self):
        """Test handling of special characters in player names and note content."""
        labels = []
        
        notes = [
            {
                "player_name": "#VILÃO!90",
                "label_id": 6,
                "content": "",
                "last_updated": datetime.fromtimestamp(1685233626)
            },
            {
                "player_name": "(CartmanBrah)-s",
                "label_id": 0,
                "content": "flat-called in MP with KK after EP bet with 25BB",
                "last_updated": datetime.fromtimestamp(1705178160)
            },
            {
                "player_name": "+ Time Passing",
                "label_id": 6,
                "content": "Reckless. Limper. Aggressive.",
                "last_updated": datetime.fromtimestamp(1743283440)
            },
            {
                "player_name": "Player's Name",
                "label_id": 4,
                "content": "Contains apostrophe & ampersand < > \"quotes\"",
                "last_updated": datetime.fromtimestamp(1705699680)
            }
        ]
        
        root = generate_xml("testuser", labels, notes)
        
        # Create a temporary file for the output
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        output_file.close()
        
        # Write the XML to the file
        write_xml_to_file(root, output_file.name)
        
        # Read the file and check its contents
        with open(output_file.name, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check that special characters in player names are preserved
        self.assertIn('<note player="#VILÃO!90"', content)
        self.assertIn('<note player="(CartmanBrah)-s"', content)
        self.assertIn('<note player="+ Time Passing"', content)
        self.assertIn('<note player="Player\'s Name"', content)
        
        # Check that special characters in content are properly encoded
        self.assertIn('Contains apostrophe &apos; ampersand &amp; &lt; &gt; &quot;quotes&quot;', content)
        
        # Clean up
        os.unlink(output_file.name)


if __name__ == "__main__":
    unittest.main()
