#!/usr/bin/env python3

"""
webapp
Main entry point for the web application.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocket
from uvicorn import Server, Config

from ultrasonics.webapp.routes import api, web
from ultrasonics.webapp.utils.socket import socket_manager

app = FastAPI(title="Ultrasonics API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="ultrasonics/webapp/static"), name="static")

# Include routers
app.include_router(api.router, prefix="/api")
app.include_router(web.router)

# WebSocket connection manager
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await socket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await socket_manager.broadcast(data)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await socket_manager.disconnect(websocket)

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )

async def server_start():
    """Start the webserver."""
    config = Config(
        app,
        host="0.0.0.0",
        port=8080,
        debug=os.environ.get('FLASK_DEBUG') == "True",
        log_level="info"
    )
    server = Server(config)
    await server.serve()
