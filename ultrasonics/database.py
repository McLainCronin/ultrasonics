#!/usr/bin/env python3

"""
database
Handles all connections with the ultrasonics MySQL database.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update, insert, delete
from dotenv import load_dotenv

from ultrasonics import logs
from ultrasonics.models import Base, User, Playlist, Song, Plugin

log = logs.create_log(__name__)

# Load environment variables
load_dotenv()

# Database configuration
DB_USER = os.getenv("DB_USER", "ultrasonics")
DB_PASSWORD = os.getenv("DB_PASSWORD", "ultrasonics2025G%%")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "ultrasonics")

# Create async engine
DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Core:
    """
    Core ultrasonics database functions.
    """

    # Global settings builder for the frontend settings page.
    # Values here are defaults, but will be overridden with database values if they exist.
    settings = [
        {
            "type": "string",
            "value": "Many plugins utilise third party apis, which often require sensitive api keys 🔑 to access (Spotify, Last.fm, Deezer, etc). The ultrasonics-api program acts as a proxy server for these apis, while keeping secret api keys... secret."
        },
        {
            "type": "string",
            "value": "You can host this yourself alongside ultrasonics, and set up all the required api keys for the services you want to use. Alternatively, use the official hosted server for faster setup."
        },
        {
            "type": "string",
            "value": "If you don't need / want to use any of these services, just leave the url empty 😊."
        },
        {
            "type": "link",
            "value": "https://github.com/XDGFX/ultrasonics-api"
        },
        {
            "type": "text",
            "label": "ultrasonics-api URL",
            "name": "api_url",
            "value": "http://localhost:3000/api/"
        },
        {
            "type": "string",
            "value": "While applets are waiting on triggers, ultrasonics will poll them at a specified interval 🕗 to check if they have triggered or not. Higher values are less resource intensive, but mean a larger delay between a trigger activating and the applet running."
        },
        {
            "type": "string",
            "value": "Once an applet has triggered, it cannot be triggered again until this interval has passed."
        },
        {
            "type": "text",
            "label": "Trigger Update Polling Interval (s)",
            "name": "trigger_poll",
            "value": "120"
        }
    ]

    async def connect(self):
        """
        Initial connection to database to create tables.
        """
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            log.info("Database connection successful")

            if await self.new_install():
                from app import _ultrasonics
                _ultrasonics["new_install"] = True

                # Create tuple with default settings
                global_settings_database = [(item["name"], item["value"])
                                         for item in self.settings if item["type"] in ["text", "radio", "select"]]

                # Insert initial settings
                for key, value in list(_ultrasonics.items()) + global_settings_database:
                    await conn.execute(
                        insert(User).values(username=key, email=value)
                    )

                await conn.commit()

            # Version check
            result = await conn.execute(
                select(User.email).where(User.username == 'version')
            )
            version = result.scalar()

            if version != _ultrasonics["version"]:
                log.warning(
                    "Installed ultrasonics version does not match database version! Proceed with caution.")

    async def new_install(self, update: bool = False) -> bool:
        """
        Check if this is a new installation of ultrasonics.
        """
        async with engine.begin() as conn:
            if update:
                await conn.execute(
                    update(User).where(User.username == 'new_install').values(email='0')
                )
                await conn.commit()
                log.info("Welcome to ultrasonics! 🔊")
                return False
            else:
                # Check if database exists
                result = await conn.execute(
                    select(User).where(User.username == 'new_install')
                )
                row = result.first()
                return row is None

    async def load(self, raw: bool = False) -> Dict[str, Any]:
        """
        Return all the current global settings in full dict format.
        If raw, return only key: value dict
        """
        async with engine.begin() as conn:
            result = await conn.execute(select(User))
            rows = result.fetchall()

            if raw:
                return {row.username: row.email for row in rows}
            else:
                data = self.settings.copy()
                db_compatible_settings = [
                    item["name"] for item in data if item["type"] in ["text", "radio", "select"]]

                for row in rows:
                    if row.username in db_compatible_settings:
                        for i, item in enumerate(data):
                            if "name" in item and item["name"] == row.username:
                                item["value"] = row.email
                                data[i] = item
                return data

    async def save(self, settings: Dict[str, Any]) -> None:
        """
        Save a list of global settings to the database.
        """
        # Add trailing slash to auth url
        if settings["api_url"][-1] != "/":
            settings["api_url"] = settings["api_url"] + "/"

        async with engine.begin() as conn:
            for key, value in settings.items():
                if key != "action":
                    await conn.execute(
                        update(User)
                        .where(User.username == key)
                        .values(email=value)
                    )
            await conn.commit()
            log.info("Settings database updated")

    async def get(self, key: str) -> Optional[str]:
        """
        Get a specific value from the ultrasonics core database.
        """
        async with engine.begin() as conn:
            result = await conn.execute(
                select(User.email).where(User.username == key)
            )
            row = result.first()
            return row[0] if row else None


class Plugin:
    """
    Functions specific to plugin data.
    """

    async def new(self, name: str, version: str) -> None:
        """
        Create a database entry for a given plugin.
        """
        async with engine.begin() as conn:
            await conn.execute(
                insert(Plugin).values(
                    name=name,
                    version=version,
                    enabled=True,
                    config={}
                )
            )
            await conn.commit()
            log.info("Plugin database entry created")

    async def set(self, name: str, version: str, settings: Dict[str, Any]) -> None:
        """
        Update an existing plugin entry in the database.
        """
        async with engine.begin() as conn:
            await conn.execute(
                update(Plugin)
                .where(Plugin.name == name)
                .values(
                    version=version,
                    config=settings
                )
            )
            await conn.commit()
            log.info("Plugin database entry updated")

    async def get(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get plugin settings from the database.
        """
        async with engine.begin() as conn:
            result = await conn.execute(
                select(Plugin).where(Plugin.name == name)
            )
            plugin = result.first()
            return plugin.config if plugin else None

    async def delete(self, name: str) -> None:
        """
        Delete a plugin from the database.
        """
        async with engine.begin() as conn:
            await conn.execute(
                delete(Plugin).where(Plugin.name == name)
            )
            await conn.commit()
            log.info("Plugin database entry deleted")


class Applet:
    """
    Functions specific to applet data.
    """

    async def new(self, applet_id: str, data: Dict[str, Any]) -> None:
        """
        Create a new applet in the database.
        """
        async with engine.begin() as conn:
            await conn.execute(
                insert(Playlist).values(
                    name=applet_id,
                    description="Applet",
                    extra_data=data
                )
            )
            await conn.commit()
            log.info("Applet database entry created")

    async def update(self, applet_id: str, data: Dict[str, Any]) -> None:
        """
        Update an existing applet in the database.
        """
        async with engine.begin() as conn:
            await conn.execute(
                update(Playlist)
                .where(Playlist.name == applet_id)
                .values(extra_data=data)
            )
            await conn.commit()
            log.info("Applet database entry updated")

    async def get(self, applet_id: str) -> Optional[Dict[str, Any]]:
        """
        Get applet data from the database.
        """
        async with engine.begin() as conn:
            result = await conn.execute(
                select(Playlist).where(Playlist.name == applet_id)
            )
            applet = result.first()
            return applet.extra_data if applet else None

    async def delete(self, applet_id: str) -> None:
        """
        Delete an applet from the database.
        """
        async with engine.begin() as conn:
            await conn.execute(
                delete(Playlist).where(Playlist.name == applet_id)
            )
            await conn.commit()
            log.info("Applet database entry deleted")
