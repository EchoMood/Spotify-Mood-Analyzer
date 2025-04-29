#!/usr/bin/env python3
"""
Main application entry point for the Spotify Mood Analysis application.
"""

import os

try:
    from .config import config
    from . import create_app
except ImportError:
    # Allow running as a standalone script during development
    from config import config
    from __init__ import create_app


def main():
    """
    Run the application using the configuration from environment variables.
    """
    try:
        # Get configuration from environment variable or use default
        config_name = os.environ.get('FLASK_CONFIG', 'development')

        # Create app with the proper configuration
        app = create_app(config_name)

        # Run with debugging enabled or disabled based on configuration
        app.run(debug=app.config['DEBUG'])
    except ImportError:
        print("\nMissing required packages! Please run:")
        print("   pip install -r requirements.txt\n")
        exit(1)


if __name__ == '__main__':
    main()