# app/__init__.py

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate

from app.models import db
from app.utils.spotify import SpotifyAPI
from config import config

# Initialize extensions globally
csrf = CSRFProtect()
migrate = Migrate()
spotify_api = SpotifyAPI()

def create_app(config_name='development'):
    """
    Factory function to create and configure the Flask application.
    """

    import os
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    app.config.from_object(config[config_name])

    # Secret key
    app.secret_key = app.config.get('SECRET_KEY')
    print("app.secret_key:", app.secret_key)

    # Initialize Flask extensions
    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    spotify_api.init_app(app)

    # Register blueprints
    from app.routes.user_routes import user_bp
    app.register_blueprint(user_bp)

    from app.routes.spotify_routes import spotify_bp
    app.register_blueprint(spotify_bp)

    from app.routes.friend_routes import friend_bp
    app.register_blueprint(friend_bp)

    from app.routes.visualisation_routes import visual_bp
    app.register_blueprint(visual_bp)


    return app
