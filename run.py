#!/usr/bin/env python3

import os
os.environ['FLASK_PORT'] = "8080"  # Set environment variable for port

# Import the normal app
from app import *

# Import and run the webapp with our custom port
from ultrasonics import webapp
if __name__ == "__main__":
    webapp.app.run(host='0.0.0.0', port=8080, debug=False)
