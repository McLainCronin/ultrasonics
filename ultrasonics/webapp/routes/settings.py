#!/usr/bin/env python3

"""
settings
Blueprint for settings and welcome routes.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

from flask import Blueprint, redirect, render_template, request
from ..utils.socket import socketio

from ultrasonics import database, logs
from ..routes.applets import Applet

log = logs.create_log(__name__)
bp = Blueprint('settings', __name__)

@bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """Global ultrasonics settings page."""
    if request.form.get('action') == "save":
        database.Core().save(request.form.to_dict())
        return redirect("/", code=302)

    settings = database.Core().load()
    return render_template("settings/settings.html", settings=settings)

@bp.route('/welcome')
def welcome():
    """Welcome page for new installations."""
    return render_template('settings/welcome.html')

# --- WEBSOCKET ROUTES ---

@socketio.on('connect')
def connect():
    """Handle client websocket connection."""
    log.info("Client connected over websocket")

@socketio.on('applet_update_name')
def applet_update_name(applet_name):
    """Update the plugin name in Applet.current_plans."""
    log.debug(f"Updating applet name to {applet_name}")
    Applet.current_plans["applet_name"] = applet_name 