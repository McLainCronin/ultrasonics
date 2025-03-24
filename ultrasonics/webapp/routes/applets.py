#!/usr/bin/env python3

"""
applets
Blueprint for applet-related routes.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

import copy
import uuid
from flask import Blueprint, redirect, render_template, request
from flask_socketio import emit

from ultrasonics import database, logs, plugins
from ultrasonics.tools import random_words
from ..utils.socket import socketio

log = logs.create_log(__name__)
bp = Blueprint('applets', __name__)

class Applet:
    default_plans = {
        "applet_name": "",
        "applet_id": "",
        "inputs": [],
        "modifiers": [],
        "outputs": [],
        "triggers": []
    }

    current_plans = copy.deepcopy(default_plans)

@bp.route('/')
def index():
    """Homepage showing list of applets."""
    action = request.args.get("action")

    # Catch statement if nothing was changed, and action is build
    if action in ['build'] and (Applet.current_plans == Applet.default_plans):
        log.warning(
            "At request to submit applet plans was received, but the plans were not changed from defaults.")
        return redirect(request.path, code=302)

    if action == 'build':
        # Send applet plans to builder and reset to default
        Applet.current_plans["applet_name"] = request.args.get(
            'applet_name') or random_words.name()

        plugins.applet_build(Applet.current_plans)
        Applet.current_plans = copy.deepcopy(Applet.default_plans)
        return redirect(request.path, code=302)

    elif action == 'modify':
        applet_id = request.args.get('applet_id')
        # Load database plans into current plans
        Applet.current_plans = plugins.applet_load(applet_id)
        return redirect("/new_applet", code=302)

    elif action == 'clear':
        Applet.current_plans = copy.deepcopy(Applet.default_plans)
        return redirect(request.path, code=302)

    elif action == 'remove':
        applet_id = request.args.get('applet_id')
        plugins.applet_delete(applet_id)
        return redirect(request.path, code=302)

    elif action == 'run':
        from ultrasonics.scheduler import pool
        applet_id = request.args.get('applet_id')
        pool.submit(plugins.applet_run, applet_id)
        return redirect(request.path, code=302)

    elif action == 'new_install':
        database.Core().new_install(update=True)
        return redirect(request.path, code=302)

    elif database.Core().new_install():
        return redirect("/welcome", code=302)

    else:
        # Clear applet plans anyway
        Applet.current_plans = copy.deepcopy(Applet.default_plans)
        applet_list = plugins.applet_gather()
        return render_template('applets/index.html', applet_list=applet_list)

@bp.route('/new_applet', methods=['GET', 'POST'])
def new_applet():
    """Create new applet page."""
    # Applet has not been created on the backend
    if Applet.current_plans["applet_id"] == "":
        # If opening the page for the first time, generate a new applet
        applet_id = str(uuid.uuid1())
        Applet.current_plans["applet_id"] = applet_id
        return redirect(request.path, code=302)

    # A request to add a component - use 'form' not 'args' because this is a POST request
    elif request.form.get('action') == 'add':
        component = {
            "plugin": request.form.get('plugin'),
            "version": request.form.get('version'),
            "data": {key: value for key, value in request.form.to_dict().items() if key not in [
                'action', 'plugin', 'version', 'component']}
        }

        Applet.current_plans[request.form.get('component')].append(component)
        return redirect(request.path, code=302)

    elif request.args.get('action') == 'remove':
        import ast
        component = ast.literal_eval(request.args.get('component'))
        component_type = request.args.get('component_type')

        Applet.current_plans[component_type].remove(component)
        return redirect(request.path, code=302)

    return render_template('applets/new_applet.html', current_plans=Applet.current_plans) 