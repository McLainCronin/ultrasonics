#!/usr/bin/env python3

"""
api
API routes for the web application.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ultrasonics import database, plugins, logs
from ultrasonics.webapp.utils.socket import socket_manager

router = APIRouter()
log = logs.create_log(__name__)

# Pydantic models for request/response validation
class AppletCreate(BaseModel):
    applet_id: str
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    modifiers: List[Dict[str, Any]] = []
    triggers: List[Dict[str, Any]] = []

class PluginSettings(BaseModel):
    name: str
    version: str
    settings: Dict[str, Any]

class GlobalSettings(BaseModel):
    settings: Dict[str, Any]

# API endpoints
@router.get("/plugins")
async def get_plugins() -> List[Dict[str, Any]]:
    """Get all available plugins."""
    return plugins.handshakes

@router.get("/applets")
async def get_applets() -> List[Dict[str, Any]]:
    """Get all applets."""
    return await plugins.applet_gather()

@router.post("/applets")
async def create_applet(applet: AppletCreate) -> Dict[str, Any]:
    """Create a new applet."""
    try:
        await plugins.applet_build(applet.dict())
        return {"status": "success", "message": "Applet created successfully"}
    except Exception as e:
        log.error(f"Error creating applet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applets/{applet_id}")
async def get_applet(applet_id: str) -> Dict[str, Any]:
    """Get a specific applet."""
    applet = await plugins.applet_load(applet_id)
    if not applet:
        raise HTTPException(status_code=404, detail="Applet not found")
    return applet

@router.delete("/applets/{applet_id}")
async def delete_applet(applet_id: str) -> Dict[str, Any]:
    """Delete an applet."""
    try:
        await plugins.applet_delete(applet_id)
        return {"status": "success", "message": "Applet deleted successfully"}
    except Exception as e:
        log.error(f"Error deleting applet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/applets/{applet_id}/run")
async def run_applet(applet_id: str) -> Dict[str, Any]:
    """Run a specific applet."""
    try:
        await plugins.applet_run(applet_id)
        return {"status": "success", "message": "Applet started successfully"}
    except Exception as e:
        log.error(f"Error running applet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plugins/{name}/settings")
async def get_plugin_settings(name: str) -> Dict[str, Any]:
    """Get settings for a specific plugin."""
    settings = await plugins.plugin_load(name, "latest")
    if not settings:
        raise HTTPException(status_code=404, detail="Plugin settings not found")
    return settings

@router.post("/plugins/{name}/settings")
async def update_plugin_settings(name: str, settings: PluginSettings) -> Dict[str, Any]:
    """Update settings for a specific plugin."""
    try:
        await plugins.plugin_update(name, settings.version, settings.settings)
        return {"status": "success", "message": "Plugin settings updated successfully"}
    except Exception as e:
        log.error(f"Error updating plugin settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_global_settings() -> Dict[str, Any]:
    """Get global settings."""
    return await database.Core().load()

@router.post("/settings")
async def update_global_settings(settings: GlobalSettings) -> Dict[str, Any]:
    """Update global settings."""
    try:
        await database.Core().save(settings.settings)
        return {"status": "success", "message": "Global settings updated successfully"}
    except Exception as e:
        log.error(f"Error updating global settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/plugins/{name}/test")
async def test_plugin(name: str, settings: PluginSettings) -> Dict[str, Any]:
    """Test a plugin with specific settings."""
    result = await plugins.plugin_test(name, settings.version, settings.settings)
    return result 