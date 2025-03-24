#!/usr/bin/env python3

"""
config
Configuration settings for the Flask application.

XDGFX, 2020, updated 2025
"""

import os

class Config:
    """Base configuration."""
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev'
    DEBUG = os.environ.get('FLASK_DEBUG') == 'True'
    
    # Server settings
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT') or 8080)
    
    # Database settings
    DATABASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'ultrasonics.db')
    
    # Plugin settings
    PLUGIN_DIRS = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'plugins'),
        os.path.join(os.path.dirname(__file__), 'official_plugins')
    ]
    
    # Scheduler settings
    TRIGGER_POLL = int(os.environ.get('TRIGGER_POLL') or 120)
    
    # API settings
    API_URL = os.environ.get('API_URL') or 'http://localhost:3000/api/' 