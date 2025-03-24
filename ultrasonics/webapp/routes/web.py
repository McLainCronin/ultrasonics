#!/usr/bin/env python3

"""
web
Web routes for the web application.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from ultrasonics import logs

router = APIRouter()
log = logs.create_log(__name__)

# Initialize templates
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main application page."""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "Ultrasonics"}
    )

@router.get("/applets", response_class=HTMLResponse)
async def applets(request: Request):
    """Render the applets management page."""
    return templates.TemplateResponse(
        "applets.html",
        {"request": request, "title": "Applets - Ultrasonics"}
    )

@router.get("/plugins", response_class=HTMLResponse)
async def plugins(request: Request):
    """Render the plugins management page."""
    return templates.TemplateResponse(
        "plugins.html",
        {"request": request, "title": "Plugins - Ultrasonics"}
    )

@router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Render the settings page."""
    return templates.TemplateResponse(
        "settings.html",
        {"request": request, "title": "Settings - Ultrasonics"}
    )

@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Render the logs page."""
    return templates.TemplateResponse(
        "logs.html",
        {"request": request, "title": "Logs - Ultrasonics"}
    ) 