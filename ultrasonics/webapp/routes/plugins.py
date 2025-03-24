#!/usr/bin/env python3

"""
plugins
Blueprint for plugin-related routes.

Original work by XDGFX, 2020
Updated and modernized by McLain Cronin, 2025
"""

from flask import Blueprint, render_template, request
from ..utils.socket import socketio

from ultrasonics import database, logs, plugins

log = logs.create_log(__name__)
bp = Blueprint('plugins', __name__)

@bp.route('/select_plugin')
def select_plugin():
    """Select plugin page."""
    component = request.args['component']

    if not component:
        log.error("Component not supplied as argument")
        raise RuntimeError

    handshakes = plugins.handshakes
    selected_handshakes = list()

    for handshake in handshakes:
        if component in handshake["type"]:  # and mode in handshake["mode"]:
            selected_handshakes.append(handshake)

    return render_template('plugins/select_plugin.html', handshakes=selected_handshakes, component=component)

@bp.route('/configure_plugin', methods=['GET', 'POST'])
def configure_plugin():
    """Settings page for each instance of a plugin."""
    global_settings = database.Core().load(raw=True)

    # Data received is to update persistent plugin settings
    if request.form.get('action') in ['add', 'test']:
        plugin = request.form.get('plugin')
        version = request.form.get('version')
        component = request.form.get('component')
        new_data = {key: value for key, value in request.form.to_dict().items() if key not in [
            'action', 'plugin', 'version', 'component'] and value != ""}

        # Merge new settings with existing database settings
        data = plugins.plugin_load(plugin, version)

        if data is None:
            data = new_data
        else:
            data.update(new_data)

        persistent = False

        if request.form.get('action') == 'test':
            response = plugins.plugin_test(plugin, version, data, component)
            socketio.emit("plugin_test", response)
            return '', 204
        else:
            plugins.plugin_update(plugin, version, data)

    else:
        plugin = request.args.get('plugin')
        version = request.args.get('version')
        component = request.args.get('component')
        persistent = request.args.get('persistent') != '0'

    # Get persistent settings for the plugin
    for item in plugins.handshakes:
        if item["name"] == plugin and item["version"] == version:
            persistent_settings = item["settings"]

    # If persistent settings are supplied
    try:
        if persistent_settings:
            settings = plugins.plugin_build(plugin, version, component)

            # Force redirect to persistent settings if manually requested through url parameters, or if plugin has not been configured
            persistent = persistent or settings is None

            if persistent:
                settings = persistent_settings

        else:
            # No persistent settings exist
            settings = plugins.plugin_build(
                plugin, version, component, force=True)

            persistent = -1

    except Exception as e:
        log.error(
            "Could not build plugin! Check your database settings are correct.", e)
        return render_template('applets/index.html')

    # Check if any settings are custom html strings
    custom_html = any([isinstance(setting, str) for setting in settings])

    test_exists = plugins.plugin_test(plugin, version, component=component)

    return render_template('plugins/configure_plugin.html', settings=settings, plugin=plugin, version=version, component=component, persistent=persistent, custom_html=custom_html, test_exists=test_exists, global_settings=global_settings) 