import os
from dotenv import load_dotenv

load_dotenv()
# Base configuration shared by all environments
class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY')
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    print("secret: ", SECRET_KEY)
    DEBUG = False
    TESTING = False

    # Spotify API configuration
    SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', 'your-client-id')
    SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', 'your-client-secret')
    REDIRECT_URI = os.environ.get("REDIRECT_URI")
    print("URI is: ", REDIRECT_URI)
    AUTH_URL = 'https://accounts.spotify.com/authorize'
    TOKEN_URL = 'https://accounts.spotify.com/api/token'
    API_BASE_URL = 'https://api.spotify.com/v1/'
    USING_NGROK = True # set to false in prod
    
    # OPENAI API configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    OPENAI_API_URL = os.environ.get('OPENAI_API_URL', 'https://api.openai.com/v1/chat/completions')
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')

    # database stuff
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')  # SQLite database for development, actual for prod
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)



# Development environment configuration
class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get('dev_secret_key')
    WTF_CSRF_SECRET_KEY = SECRET_KEY


# Testing environment configuration
class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SECRET_KEY = 'test-secret'
    WTF_CSRF_SECRET_KEY = SECRET_KEY
    WTF_CSRF_ENABLED = False  # Disable CSRF protection for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory SQLite database for testing



# Production environment configuration
class ProductionConfig(Config):
    # Production-specific configurations can go here
    SECRET_KEY = os.environ.get('SECRET_KEY')

    pass


# Dictionary with configurations for different environments
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,

    # Default configuration
    'default': DevelopmentConfig
}

