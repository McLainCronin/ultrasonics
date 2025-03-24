#!/usr/bin/env python3

"""
models
SQLAlchemy models for the ultrasonics database.

McLain Cronin, 2025
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    """User model for authentication and preferences."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON)

    playlists = relationship("Playlist", back_populates="user")

class Playlist(Base):
    """Playlist model for storing user playlists."""
    __tablename__ = 'playlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    extra_data = Column(JSON)
    
    user = relationship("User", back_populates="playlists")
    songs = relationship("Song", back_populates="playlist")

class Song(Base):
    """Song model for storing track information."""
    __tablename__ = 'songs'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    artist = Column(String(200))
    album = Column(String(200))
    duration = Column(Integer)  # Duration in seconds
    playlist_id = Column(Integer, ForeignKey('playlists.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON)
    
    playlist = relationship("Playlist", back_populates="songs")

class Plugin(Base):
    """Plugin model for storing plugin configurations."""
    __tablename__ = 'plugins'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    version = Column(String(20))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = Column(JSON) 