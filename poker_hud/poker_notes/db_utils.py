#!/usr/bin/env python3
"""
Database utilities for poker notes management.

This module provides database models and utilities for storing and retrieving poker notes.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session

import os
import sys
from pathlib import Path

# Get the configuration
try:
    # Try relative import first
    from ..config import DATABASE_URL
except ImportError:
    # Fall back to direct import if run as script
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
        from poker_hud.config import DATABASE_URL
    except ImportError:
        # Default if all else fails
        DATABASE_URL = 'sqlite:///./poker_hud.db'
        print(f"Could not import config, using default: {DATABASE_URL}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()


class User(Base):
    """SQLAlchemy model for users."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    labels = relationship("Label", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")


class Label(Base):
    """SQLAlchemy model for note labels."""
    __tablename__ = "labels"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    label_id = Column(Integer)  # Original label ID from XML
    color = Column(String)
    name = Column(String)
    
    # Relationships
    user = relationship("User", back_populates="labels")
    notes = relationship("Note", back_populates="label")


class Note(Base):
    """SQLAlchemy model for player notes."""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    label_id = Column(Integer, ForeignKey("labels.id"), nullable=True)
    player_name = Column(String, index=True)
    content = Column(Text)
    last_updated = Column(DateTime)
    source_file = Column(String)  # Original XML file
    
    # Relationships
    user = relationship("User", back_populates="notes")
    label = relationship("Label", back_populates="notes")


def get_database_session(database_url: str = DATABASE_URL) -> Tuple[Session, sessionmaker]:
    """
    Create and return a database session.
    
    Args:
        database_url: The database URL to connect to.
        
    Returns:
        A tuple containing the session and session maker.
    """
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    return SessionLocal(), SessionLocal


def get_or_create_user(session: Session, username: str) -> User:
    """
    Get an existing user or create a new one.
    
    Args:
        session: Database session.
        username: Username.
        
    Returns:
        User object.
    """
    user = session.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username)
        session.add(user)
        session.commit()
        logger.info(f"Created new user: {username}")
    return user
