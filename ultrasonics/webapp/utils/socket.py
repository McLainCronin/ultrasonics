#!/usr/bin/env python3

"""
socket
SocketIO utilities for the web application.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

from flask_socketio import SocketIO, emit

# Initialize SocketIO instance
socketio = SocketIO()

def send(event, data):
    """Send data to connected clients over websocket."""
    socketio.emit(str(event), {'data': data}) 