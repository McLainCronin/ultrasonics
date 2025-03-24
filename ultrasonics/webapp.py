#!/usr/bin/env python3

"""
webapp
Main entry point for the web application.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

import os
from ultrasonics.webapp import create_app
from ultrasonics.webapp.utils.socket import socketio

def server_start():
    """Start the webserver."""
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=8080, debug=os.environ.get('FLASK_DEBUG') == "True" or False)
