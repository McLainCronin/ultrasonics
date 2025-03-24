#!/usr/bin/env python3

"""
app
Main ultrasonics entrypoint. Run this to start ultrasonics.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

import os

from ultrasonics import database, plugins, scheduler
from ultrasonics.webapp import server_start

_ultrasonics = {
    "version": "1.0.0-rc.1",
    "config_dir": os.path.join(os.path.dirname(__file__), "config")
}

database.Core().connect()
plugins.plugin_gather()
scheduler.scheduler_start()
server_start()
