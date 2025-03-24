#!/usr/bin/env python3

"""
plugins
Handles all functions for interacting with plugins and applets.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

import importlib
import json
import os
import re
from itertools import chain
from typing import Dict, Any, Optional, List

from ultrasonics import database, logs, scheduler

log = logs.create_log(__name__)

# Initialise variables
found_plugins = {}
handshakes = []

# Prefix for all plugins in plugins folder, up stands for ultrasonics plugin ;)
prefix = "up_"

# Setup databases
dba = database.Applet()
dbc = database.Core()
dbp = database.Plugin()

# Possible plugin locations
paths = ("./plugins", "./ultrasonics/official_plugins")


try:
    os.mkdir("plugins")
except FileExistsError:
    # Folder already exists
    pass


async def plugin_gather():
    """
    Used to find all modules within the plugins directories, and saves them to the 'found_plugins' dictionary.
    """
    for _, _, items in chain.from_iterable(os.walk(path) for path in paths):
        for item in items:
            # Check if file has .py extension
            if re.match(prefix + "([\w\W]+)\.py$", item):
                # Extract name of file excluding extension
                title = re.search(prefix + "([\w\W]+)\.py$", item)[1]

                if title == "skeleton":
                    # Skip the included skeleton plugin.
                    continue

                try:
                    # First try to import from official plugins
                    plugin_path = f"ultrasonics.official_plugins.{prefix + title}"
                    plugin = importlib.import_module(plugin_path, ".")
                except ModuleNotFoundError:
                    # Then try to import from installed plugins
                    plugin_path = f"plugins.{prefix + title}"
                    plugin = importlib.import_module(plugin_path, ".")

                for key in ["name", "description"]:
                    plugin.handshake[key] = plugin.handshake[key].lower().strip(" .,")

                handshake_name = plugin.handshake["name"]
                handshake_version = plugin.handshake["version"]

                # Verify that the name in the plugin handshake matches the filename
                if handshake_name != title:
                    log.error("Plugin name must match the filename!")
                    log.error(plugin)
                    continue

                # Add the plugin handshake to the list of handshakes, and the plugin to the list of found plugins
                handshakes.append(plugin.handshake)
                found_plugins[title] = plugin
                found_plugins[title].plugin_logs_path = plugin_path.replace(
                    "ultrasonics.", "").replace("official_plugins.up_", "🎧 ").replace("plugins.up_", "🎤 ")

                log.info(f"Found plugin: {plugin}")

                # Check if plugin exists in database
                plugin_data = await dbp.get(title)
                if not plugin_data:
                    # Create new entry
                    await dbp.new(title, handshake_version)
                    log.info(f"Created new database entry for plugin {title} v{handshake_version}")


async def plugin_load(name: str, version: str) -> Optional[Dict[str, Any]]:
    """
    Load plugin persistent settings.
    """
    return await dbp.get(name)


async def plugin_build(name: str, version: str, component: str, force: bool = False) -> Optional[Dict[str, Any]]:
    """
    Find the required settings for a plugin when building an applet.
    """
    database = await dbp.get(name)
    global_settings = await dbc.load(raw=True)

    # Plugin has not yet been configured
    if not database and not force:
        return None

    settings_dict = found_plugins[name].builder(
        database=database, global_settings=global_settings, component=component)
    return settings_dict


async def plugin_update(name: str, version: str, settings: Dict[str, Any]) -> None:
    """
    Send updated persistent plugin settings to the database.
    """
    await dbp.set(name, version, settings)


async def plugin_run(name: str, version: str, settings_dict: Dict[str, Any], 
                    component: Optional[str] = None, applet_id: Optional[str] = None, 
                    songs_dict: Optional[Dict[str, Any]] = None) -> Any:
    """
    Run a specific plugin.

    INPUTS
    name:            name of plugin
    version:         version of plugin
    settings_dict:   settings to run this specific instance of the plugin, taken from the applet
    songs_dict:      passed to the plugin if not an input

    OUTPUTS
    response:        either a success message, or the new songs_dict
    """
    log.debug(f"Running plugin {name} v{version}")
    plugin_settings = await dbp.get(name)
    global_settings = await dbc.load(raw=True)

    response = found_plugins[name].run(
        settings_dict, database=plugin_settings, global_settings=global_settings, 
        component=component, applet_id=applet_id, songs_dict=songs_dict)

    return response


async def plugin_test(name: str, version: str, database: Optional[Dict[str, Any]] = None, 
                     component: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the test function from a specified plugin.
    If settings_dict is None, will check if a test function exists for the plugin, returning True or False.
    Otherwise, settings_dict contains the persistent settings (in standard database format) to validate.
    Plugin test function should return True or False for pass and fail respectively.
    """
    if getattr(found_plugins[name], 'test', None) is None:
        log.info(f"{name} does not have a test function.")
        return {"response": False, "logs": "ERROR   - No test function found!"}

    elif database == {}:
        return {"response": False, "logs": "ERROR   - No database values were received!"}

    elif database:
        logs_name = found_plugins[name].plugin_logs_path
        plugin_log = logs.start_capture(logs_name)

        plugin_log.debug(f"Running settings test for plugin {name} v{version}")

        try:
            global_settings = await dbc.load(raw=True)
            found_plugins[name].test(database, global_settings=global_settings)
            logs_string = logs.stop_capture(logs_name)
            return {"response": True, "logs": logs_string}

        except Exception as e:
            plugin_log.error("Plugin test failed.")
            plugin_log.error(e)
            logs_string = logs.stop_capture(logs_name)
            return {"response": False, "logs": logs_string}

    else:
        return {"response": True, "logs": "Plugin has a test function."}


async def applet_gather() -> List[Dict[str, Any]]:
    """
    Gather the list of existing applets.
    """
    applet_list = await dba.get_all()
    return applet_list


async def applet_load(applet_id: str) -> Optional[Dict[str, Any]]:
    """
    Load an existing applet to be edited.
    """
    applet_plans = await dba.get(applet_id)
    if applet_plans:
        applet_plans["applet_id"] = applet_id
    return applet_plans


async def applet_build(applet_plans: Dict[str, Any]) -> None:
    """
    Function which takes input data from the frontend to build a new applet. 
    If the applet ID matches an existing one, it will be updated.
    """
    applet_id = applet_plans["applet_id"]
    applet_plans.pop("applet_id")

    await dba.update(applet_id, applet_plans)
    await scheduler.applet_submit(applet_id)


async def applet_delete(applet_id: str) -> None:
    """
    Remove an applet from the database.
    """
    await dba.delete(applet_id)


async def applet_run(applet_id: str) -> None:
    """
    Run the requested applet in full.
    """
    from datetime import datetime
    runtime = datetime.now()

    log.info(f"Running applet: {applet_id}")

    try:
        applet_plans = await dba.get(applet_id)

        if not applet_plans["inputs"] or not applet_plans["outputs"]:
            raise Exception(
                f"An input or output plugin is missing for applet {applet_id} - will not run.")

        else:
            songs_dict = []

            def get_info(plugin):
                name = plugin["plugin"]
                version = plugin["version"]
                data = plugin["data"]

                return name, version, data

            "Inputs"
            # Get new songs from input, append to songs list
            for plugin in applet_plans["inputs"]:
                for item in await plugin_run(*get_info(plugin), component="inputs", applet_id=applet_id):
                    songs_dict.append(item)

            "Modifiers"
            # Replace songs with output from modifier plugin
            for plugin in applet_plans["modifiers"]:
                songs_dict = await plugin_run(
                    *get_info(plugin), songs_dict=songs_dict, component="modifiers", applet_id=applet_id)

            "Outputs"
            # Submit songs dict to output plugin
            for plugin in applet_plans["outputs"]:
                await plugin_run(*get_info(plugin), component="outputs",
                           applet_id=applet_id, songs_dict=songs_dict)

            success = True

    except Exception as e:
        log.error(e, exc_info=True)

        success = False

    if success:
        log.info(
            f"Applet {applet_id} completed successfully in {datetime.now() - runtime}")
    else:
        log.warning(
            f"Applet {applet_id} failed in {datetime.now() - runtime}")

    lastrun = {
        "time": runtime.strftime("%d-%m-%Y %H:%M"),
        "result": success
    }

    await dba.lastrun(applet_id, lastrun)


async def applet_trigger_run(applet_id: str) -> None:
    """
    Run the trigger function from the requested applet.
    """
    applet_plans = await dba.get(applet_id)

    if not applet_plans["triggers"]:
        log.error(
            f"No trigger is supplied for applet {applet_id} - will not run automatically.")
        raise Exception

    # This needs to be fixed, currently both triggers must activate before the applet runs (AND not OR)
    for trigger in applet_plans["triggers"]:
        name = trigger["plugin"]
        version = trigger["version"]
        data = trigger["data"]

        await plugin_run(name, version, data, applet_id=applet_id)
