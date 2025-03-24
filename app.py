#!/usr/bin/env python3

"""
app
Main ultrasonics entrypoint. Run this to start ultrasonics.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

import os
import asyncio

from ultrasonics import database, plugins, scheduler
from ultrasonics.webapp import server_start

_ultrasonics = {
    "version": "1.0.0-rc.1",
    "config_dir": os.path.join(os.path.dirname(__file__), "config")
}

async def main():
    """Main async entry point."""
    # Initialize database
    await database.Core().connect()
    
    # Initialize plugins
    await plugins.plugin_gather()
    
    # Start scheduler
    await scheduler.scheduler_start()
    
    # Start web server
    await server_start()

if __name__ == "__main__":
    asyncio.run(main())
