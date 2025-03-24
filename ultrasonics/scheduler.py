#!/usr/bin/env python3

"""
scheduler
Handles scheduling and execution of applets.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

import asyncio
from typing import Dict, Optional
from datetime import datetime

from ultrasonics import database, logs, plugins

log = logs.create_log(__name__)

# Each applet has its own key, where the value is True if applet should be running, or False if it needs to restart.
applets_running: Dict[str, bool] = {}


async def scheduler_start():
    """
    Sets up task scheduling for all applets currently in the database.
    """
    applets = await plugins.applet_gather()
    for applet in applets:
        applet_id = applet["applet_id"]
        await applet_submit(applet_id)


async def applet_submit(applet_id: str):
    """
    Submits an applet to the scheduler if it doesn't already exist.
    """
    if applet_id in applets_running:
        # Signal that trigger should exit
        applets_running[applet_id] = False

        # Resubmit with a delay to allow the applet to exit
        await asyncio.sleep(await trigger_poll())
        asyncio.create_task(scheduler_applet_loop(applet_id))
    else:
        asyncio.create_task(scheduler_applet_loop(applet_id))


async def scheduler_applet_loop(applet_id: str):
    """
    Creates the main applet scheduler run loop.
    """
    log.debug(f"Submitted applet '{applet_id}' to scheduler")
    applets_running[applet_id] = True

    while applets_running[applet_id]:
        try:
            # Run trigger
            await plugins.applet_trigger_run(applet_id)
            
            # Check if applet still exists in the database
            applet_data = await database.Applet().get(applet_id)
            if applet_data is None:
                break
                
            # Run applet
            await plugins.applet_run(applet_id)
            
            # Wait for next trigger
            await asyncio.sleep(await trigger_poll())
            
        except Exception as e:
            # An error has occurred
            log.error(e, exc_info=True)
            applets_running[applet_id] = False
            break


async def trigger_poll() -> int:
    """
    Gets the trigger_poll value from the ultrasonics database.
    """
    trigger_poll = await database.Core().get("trigger_poll")
    return int(trigger_poll)
