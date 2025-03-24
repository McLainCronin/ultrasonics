#!/usr/bin/env python3

"""
Ultrasonics - A modern music automation platform

XDGFX, 2020, updated 2025
"""

import os
from flask import Flask
from flask_socketio import SocketIO

from ultrasonics import database, logs, plugins, scheduler

# Initialize extensions
socketio = SocketIO()

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load config
    if test_config is None:
        app.config.from_object('ultrasonics.config.Config')
    else:
        app.config.update(test_config)
    
    # Initialize extensions
    socketio.init_app(app, async_mode='threading')
    
    # Initialize database
    database.Core().connect()
    
    # Register blueprints
    from ultrasonics.webapp import main
    app.register_blueprint(main.bp)
    
    # Initialize plugins
    plugins.plugin_gather()
    
    # Start scheduler
    scheduler.scheduler_start()
    
    return app

def create_socketio(app):
    """Create and configure SocketIO."""
    return socketio.init_app(app, async_mode='threading')

# Version information
__version__ = '1.0.0-rc.1' 