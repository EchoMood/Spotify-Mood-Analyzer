import os
from dotenv import load_dotenv

load_dotenv()
# Base configuration shared by all environments
class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('dev_secret_key')
    print("secret: ", SECRET_KEY)
    DEBUG = False
    TESTING = False

    # Spotify API configuration
    SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', 'your-client-id')
    SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', 'your-client-secret')
    REDIRECT_URI = os.environ.get('REDIRECT_URI')
    print("URI is: ", REDIRECT_URI)
    AUTH_URL = 'https://accounts.spotify.com/authorize'
    TOKEN_URL = 'https://accounts.spotify.com/api/token'
    API_BASE_URL = 'https://api.spotify.com/v1/'
    USING_NGROK = True # set to false in prod


# Development environment configuration
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///spotify_mood.db'  # SQLite database for development


# Testing environment configuration
class TestingConfig(Config):
    TESTING = True
    DEBUG = True


# Production environment configuration
class ProductionConfig(Config):
    # Production-specific configurations can go here
    pass


# Dictionary with configurations for different environments
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    # Default configuration
    'default': DevelopmentConfig
}