#!/usr/bin/env python3

"""
webapp
Flask application factory and configuration.

McLain Cronin, 2025
"""

import os
from flask import Flask
from flask_socketio import SocketIO

# Initialize SocketIO
socketio = SocketIO()

def create_app(test_config=None):
    """
    Create and configure the Flask application.
    
    Args:
        test_config: Optional test configuration dictionary
        
    Returns:
        Flask application instance
    """
    # Create Flask app with correct template and static folders
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
                static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
    
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY='dev',  # Change this in production
        DEBUG=os.environ.get('FLASK_DEBUG', 'False') == 'True'
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.update(test_config)

    # Initialize SocketIO with the app
    socketio.init_app(app, async_mode='threading')

    # Register blueprints
    from .routes import applets, plugins, settings
    app.register_blueprint(applets.bp)
    app.register_blueprint(plugins.bp)
    app.register_blueprint(settings.bp)

    return app

def server_start():
    """Start the webserver."""
    app = create_app()
    socketio.run(app, host="0.0.0.0", port=8080, debug=os.environ.get('FLASK_DEBUG') == "True" or False) 