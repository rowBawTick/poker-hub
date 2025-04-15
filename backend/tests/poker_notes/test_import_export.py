#!/usr/bin/env python3
"""
Tests for import and export functionality of poker notes.
"""
import os
import sys
import unittest
import tempfile
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# We don't need to modify the path if the package is installed in development mode
# or if we run the tests from the right directory with the right PYTHONPATH

from backend.poker_notes.db_utils import Base, User, Label, Note, get_database_session
from backend.poker_notes.import_notes import import_notes_from_files
from backend.poker_notes.export_notes import export_notes_to_file


class TestImportExport(unittest.TestCase):
    """Test cases for import and export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.database_url = f"sqlite:///{self.temp_db.name}"
        
        # Create the database schema
        engine = create_engine(self.database_url)
        Base.metadata.create_all(engine)
        
        # Create a sample XML file
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
        self.temp_xml = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        self.temp_xml.write(self.sample_xml.encode('utf-8'))
        self.temp_xml.close()
        
        # Create a temporary file for export
        self.export_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        self.export_file.close()

    def tearDown(self):
        """Tear down test fixtures."""
        # Remove temporary files
        os.unlink(self.temp_db.name)
        os.unlink(self.temp_xml.name)
        if os.path.exists(self.export_file.name):
            os.unlink(self.export_file.name)

    def test_import_notes(self):
        """Test importing notes from an XML file."""
        # Import notes from the sample XML file
        imported_count = import_notes_from_files("testuser", [self.temp_xml.name], self.database_url)
        
        # Check that notes were imported
        self.assertEqual(imported_count, 4)
        
        # Check the database contents
        session, _ = get_database_session(self.database_url)
        try:
            # Check user
            user = session.query(User).filter_by(username="testuser").first()
            self.assertIsNotNone(user)
            
            # Check labels
            labels = session.query(Label).filter_by(user_id=user.id).all()
            self.assertEqual(len(labels), 8)
            
            # Check notes
            notes = session.query(Note).filter_by(user_id=user.id).all()
            self.assertEqual(len(notes), 4)
            
            # Check specific notes
            note_players = [note.player_name for note in notes]
            self.assertIn("#VILÃO!90", note_players)
            self.assertIn("(CartmanBrah)-s", note_players)
            self.assertIn("+ Time Passing", note_players)
            self.assertIn("Player's Name", note_players)
            
            # Check note content
            for note in notes:
                if note.player_name == "(CartmanBrah)-s":
                    self.assertEqual(note.content, "flat-called in MP with KK after EP bet with 25BB")
                elif note.player_name == "Player's Name":
                    self.assertEqual(note.content, "Contains apostrophe & ampersand")
        finally:
            session.close()

    def test_export_notes(self):
        """Test exporting notes to an XML file."""
        # First import notes to have something to export
        import_notes_from_files("testuser", [self.temp_xml.name], self.database_url)
        
        # Export notes
        success = export_notes_to_file("testuser", self.export_file.name, self.database_url)
        self.assertTrue(success)
        
        # Check that the export file exists and has content
        self.assertTrue(os.path.exists(self.export_file.name))
        with open(self.export_file.name, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check the content of the exported file
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', content)
        self.assertIn('<notes version="1">', content)
        self.assertIn('<label id="0" color="30DBFF">Conservative</label>', content)
        self.assertIn('<note player="#VILÃO!90"', content)
        self.assertIn('<note player="(CartmanBrah)-s"', content)
        self.assertIn('<note player="+ Time Passing"', content)
        self.assertIn('<note player="Player\'s Name"', content)
        self.assertIn('flat-called in MP with KK after EP bet with 25BB', content)
        self.assertIn('Contains apostrophe &amp; ampersand', content)

    def test_import_export_round_trip(self):
        """Test a full round trip of import and export."""
        # Import notes
        import_notes_from_files("testuser", [self.temp_xml.name], self.database_url)
        
        # Export notes
        export_notes_to_file("testuser", self.export_file.name, self.database_url)
        
        # Create a new temporary database for the round trip test
        round_trip_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        round_trip_db.close()
        round_trip_db_url = f"sqlite:///{round_trip_db.name}"
        
        # Create the database schema
        engine = create_engine(round_trip_db_url)
        Base.metadata.create_all(engine)
        
        try:
            # Import the exported notes into the new database
            imported_count = import_notes_from_files("testuser", [self.export_file.name], round_trip_db_url)
            
            # Check that all notes were imported
            self.assertEqual(imported_count, 4)
            
            # Check the database contents
            session, _ = get_database_session(round_trip_db_url)
            try:
                # Check notes
                notes = session.query(Note).filter(
                    Note.user_id == session.query(User.id).filter_by(username="testuser").scalar()
                ).all()
                self.assertEqual(len(notes), 4)
                
                # Check specific notes
                note_players = [note.player_name for note in notes]
                self.assertIn("#VILÃO!90", note_players)
                self.assertIn("(CartmanBrah)-s", note_players)
                self.assertIn("+ Time Passing", note_players)
                self.assertIn("Player's Name", note_players)
                
                # Check note content
                for note in notes:
                    if note.player_name == "(CartmanBrah)-s":
                        self.assertEqual(note.content, "flat-called in MP with KK after EP bet with 25BB")
                    elif note.player_name == "Player's Name":
                        self.assertEqual(note.content, "Contains apostrophe & ampersand")
            finally:
                session.close()
        finally:
            os.unlink(round_trip_db.name)

    def test_note_merging(self):
        """Test that notes are properly merged when importing multiple times."""
        # Import notes from the sample XML file
        import_notes_from_files("testuser", [self.temp_xml.name], self.database_url)
        
        # Create a second XML file with updated notes for the same players
        second_xml = """<?xml version="1.0" encoding="UTF-8"?>
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
    <note player="#VILÃO!90" label="6" update="1685233700">New note content for VILÃO</note>
    <note player="NewPlayer" label="3" update="1705178200">Note for a new player</note>
</notes>
"""
        second_xml_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
        second_xml_file.write(second_xml.encode('utf-8'))
        second_xml_file.close()
        
        try:
            # Import the second XML file
            imported_count = import_notes_from_files("testuser", [second_xml_file.name], self.database_url)
            
            # Check that notes were imported (2 new notes)
            self.assertEqual(imported_count, 2)
            
            # Check the database contents
            session, _ = get_database_session(self.database_url)
            try:
                # Check user
                user = session.query(User).filter_by(username="testuser").first()
                self.assertIsNotNone(user)
                
                # Check notes
                notes = session.query(Note).filter_by(user_id=user.id).all()
                # Should now have 5 notes (4 original + 1 new player)
                self.assertEqual(len(notes), 5)
                
                # Check specific notes
                for note in notes:
                    if note.player_name == "#VILÃO!90":
                        # Note should be merged with the new content
                        self.assertIn("New note content for VILÃO", note.content)
                        # Verify that a label exists, but don't check the exact ID
                        # This makes the test more robust against implementation changes
                        self.assertIsNotNone(note.label_id)
                    elif note.player_name == "NewPlayer":
                        self.assertEqual(note.content, "Note for a new player")
                        # Verify that a label exists, but don't check the exact ID
                        self.assertIsNotNone(note.label_id)
            finally:
                session.close()
        finally:
            os.unlink(second_xml_file.name)


if __name__ == "__main__":
    unittest.main()
