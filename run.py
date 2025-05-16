# run.py

import os
import sys
import socket

from app.models import db

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app import create_app

# Load config name from env, default to 'development'
config_name = os.getenv('FLASK_CONFIG', 'development')
app = create_app(config_name)

# ----------------------------------------------------------
# Helper Function to Find Free Port
# ----------------------------------------------------------
def find_free_port(default=5000, max_tries=10):
    port = default
    for _ in range(max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('127.0.0.1', port)) != 0:
                return port
            port += 1
    raise OSError("No available port found.")

# Create app instance for running directly
app = create_app()

# Main Application Entry Point
if __name__ == '__main__':
    # for production
    port = int(os.environ.get('PORT', find_free_port()))
    # for local testing
    app.run(host='0.0.0.0', port=port, debug=False)