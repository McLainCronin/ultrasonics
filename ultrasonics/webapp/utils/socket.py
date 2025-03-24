#!/usr/bin/env python3

"""
socket
WebSocket manager for real-time communication.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

from typing import List, Dict, Any
from fastapi import WebSocket
from ultrasonics import logs

log = logs.create_log(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        log.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        self.active_connections.remove(websocket)
        # Remove from all subscriptions
        for topic in self.subscriptions:
            if websocket in self.subscriptions[topic]:
                self.subscriptions[topic].remove(websocket)
        log.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def subscribe(self, websocket: WebSocket, topic: str):
        """Subscribe a client to a specific topic."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(websocket)
        log.info(f"Client subscribed to topic: {topic}")

    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """Unsubscribe a client from a specific topic."""
        if topic in self.subscriptions and websocket in self.subscriptions[topic]:
            self.subscriptions[topic].remove(websocket)
            log.info(f"Client unsubscribed from topic: {topic}")

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                log.error(f"Error broadcasting message: {e}")
                await self.disconnect(connection)

    async def broadcast_to_topic(self, topic: str, message: str):
        """Broadcast a message to all clients subscribed to a specific topic."""
        if topic in self.subscriptions:
            for connection in self.subscriptions[topic]:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    log.error(f"Error broadcasting to topic {topic}: {e}")
                    await self.disconnect(connection)

    async def send_json(self, websocket: WebSocket, data: Dict[str, Any]):
        """Send JSON data to a specific client."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            log.error(f"Error sending JSON: {e}")
            await self.disconnect(websocket)

# Create a global instance of the connection manager
socket_manager = ConnectionManager() 