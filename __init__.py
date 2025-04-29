"""
Main application module for Spotify Mood Analysis.
Initializes the Flask application and defines routes.
"""

from datetime import datetime, timedelta
import uuid
import os

from flask import Flask, render_template, request, session, url_for, redirect, jsonify
from utils.spotify import SpotifyAPI
from models import User, Track, AudioFeatures
#from mood_analysis import MoodAnalyzer
from config import config


def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    app_config = config[config_name]
    app.config.from_object(app_config)

    # Secret key for session
    app.secret_key = app.config.get('SECRET_KEY', 'dev_secret_key')

    # Session configuration for cross-domain (important for ngrok)
    # Only enable in production if using HTTPS
    if app.config.get('USING_NGROK', False):
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'None'

    from models import db
    # Initialize database
    db.init_app(app)

    # Initialize Spotify API helper
    spotify_api = SpotifyAPI()
    spotify_api.init_app(app)

    @app.route('/')
    def index():
        """Render the home page."""
        return render_template('index.html')

    @app.route('/login')
    def login():
        """
        Redirect to Spotify authorization page.
        Initiates the OAuth flow.
        """
        # Generate state for CSRF protection
        state = str(uuid.uuid4())
        session['state'] = state

        # Define scopes needed for the application
        scope = 'user-top-read user-read-email user-read-private'

        # Get authorization URL from Spotify API utility
        auth_url = spotify_api.get_auth_url(state, scope)

        return redirect(auth_url)

    @app.route('/callback')
    def callback():
        """
        Handle the callback from Spotify OAuth.
        Exchange authorization code for access tokens.
        """
        # Verify state to prevent CSRF attacks
        if request.args.get('state') != session.get('state'):
            print("CSRF ATTACK ERROR")
            return redirect(url_for('index'))

        # Check for errors in the callback
        if request.args.get('error'):
            return redirect(url_for('index'))

        # Get the authorization code
        code = request.args.get('code')

        # Exchange code for access token using Spotify API utility
        print("Code: ", code)
        token_data = spotify_api.get_access_token(code)
        print("Token data: ", token_data)


        if not token_data:
            print("DEBUG no token data, redirecting to index\n")
            return redirect(url_for('index'))

        # Extract token information
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        expires_in = token_data['expires_in']
        token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

        # Get user profile using Spotify API utility
        user_data = spotify_api.get_user_profile(access_token)
        print("User data: ", user_data)
        session['access_token'] = access_token


        if not user_data:
            return redirect(url_for('index'))

        #todo: implement logic for database stuff
        # # Save or update user in database
        # user = User.query.filter_by(id=user_data['id']).first()
        #
        # if user:
        #     # Update existing user
        #     user.access_token = access_token
        #     user.refresh_token = refresh_token
        #     user.token_expiry = token_expiry
        #     user.last_login = datetime.utcnow()
        # else:
        #     # Create new user
        #     user = User(
        #         id=user_data['id'],
        #         email=user_data.get('email', ''),
        #         display_name=user_data.get('display_name', ''),
        #         access_token=access_token,
        #         refresh_token=refresh_token,
        #         token_expiry=token_expiry
        #     )
        #     db.session.add(user)
        #
        # db.session.commit()
        #
        # # Store user ID in session
        # session['user_id'] = user.id
        #
        # # Start data collection process
        # fetch_and_store_user_data(user.id, spotify_api)

        # Redirect to visualization page
        return redirect(url_for('visualise'))

    @app.route('/visualise')
    def visualise():
        """Render the visualization page with mood analysis."""
        if 'access_token' not in session:
            print("ERROR returning to index: no access_token in session\n")
            return redirect(url_for('index'))

        # Get default time range (medium_term if not specified)
        time_range = request.args.get('time_range', 'medium_term')

        #todo: checking if user not logged in properly
        # # Load user data for visualization
        # user_id = session.get('user_id')
        # user = User.query.get(user_id)
        #
        # if not user:
        #
        #     return redirect(url_for('index'))

        # Initialize data structures
        mood_data = {
            'Happy': {'percentage': 40, 'top_song': {'name': 'Sample Song', 'artist': 'Sample Artist'}},
            'Sad': {'percentage': 20, 'top_song': {'name': 'Sample Song 2', 'artist': 'Sample Artist 2'}},
            'Chill': {'percentage': 15, 'top_song': {'name': 'Sample Song 3', 'artist': 'Sample Artist 3'}},
            'Energetic': {'percentage': 15, 'top_song': {'name': 'Sample Song 4', 'artist': 'Sample Artist 4'}},
            'Nostalgic': {'percentage': 10, 'top_song': {'name': 'Sample Song 5', 'artist': 'Sample Artist 5'}}
        }

        personality_data = {
            'type': 'INTJ',
            'description': 'Strategic, independent, and insightful.',
            'related_songs': [
                {'name': 'Sample Song 1', 'artist': 'Sample Artist 1'},
                {'name': 'Sample Song 2', 'artist': 'Sample Artist 2'},
                {'name': 'Sample Song 3', 'artist': 'Sample Artist 3'}
            ]
        }

        # # Try to get tracks and features if user is authenticated
        # try:
        #     tracks = Track.query.filter_by(user_id=user_id, time_range=time_range).all()
        #     track_ids = [track.id for track in tracks]
        #     features = AudioFeatures.query.filter(AudioFeatures.track_id.in_(track_ids)).all()
        #
        #     # If we have real data, use it instead of the placeholders
        #     if tracks and features:
        #         # You can uncomment and implement this when ready
        #         # analyzer = MoodAnalyzer(tracks, features)
        #         # mood_data = analyzer.analyze_moods()
        #         # personality_data = analyzer.determine_personality()
        #         pass
        # except Exception as e:
        #     print(f"Error retrieving track data: {e}")
        #     # Continue with default data

        return render_template(
            'visualise.html',
            user="user", #todo: implement this in frontend
            mood_data=mood_data,
            personality_data=personality_data, #todo: implement this in frontend
            time_range=time_range
        )

    @app.route('/api/mood-data')
    def api_mood_data():
        """API endpoint to get mood data."""
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        time_range = request.args.get('time_range', 'medium_term')
        user_id = session['user_id']

        # Get tracks and features
        tracks = Track.query.filter_by(user_id=user_id, time_range=time_range).all()
        track_ids = [track.id for track in tracks]
        features = AudioFeatures.query.filter(AudioFeatures.track_id.in_(track_ids)).all()

        # Use the mood analyzer
        # analyzer = MoodAnalyzer(tracks, features)
        # mood_data = analyzer.analyze_moods()
        #
        # return jsonify(mood_data)

    @app.route('/api/personality-data')
    def api_personality_data():
        """API endpoint to get personality data."""
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        time_range = request.args.get('time_range', 'medium_term')
        user_id = session['user_id']

        # Get tracks and features
        tracks = Track.query.filter_by(user_id=user_id, time_range=time_range).all()
        track_ids = [track.id for track in tracks]
        features = AudioFeatures.query.filter(AudioFeatures.track_id.in_(track_ids)).all()

        # Use the mood analyzer
        # analyzer = MoodAnalyzer(tracks, features)
        # personality_data = analyzer.determine_personality()

        # return jsonify(personality_data)

    @app.route('/upload')
    def upload():
        """Render the upload page."""
        return render_template('upload.html')

    @app.route('/share')
    def share():
        """Render the share page."""
        return render_template('share.html')

    @app.route('/logout')
    def logout():
        """Log out the user by clearing the session."""
        session.pop('user_id', None)
        session.pop('state', None)
        return redirect(url_for('index'))

    return app


def fetch_and_store_user_data(user_id, spotify_api):
    from models import db
    """
    Fetch and store user's top tracks and audio features.

    Args:
        user_id: The user's ID
        spotify_api: Instance of SpotifyAPI
    """
    user = User.query.get(user_id)

    if not user:
        return False

    # Check if token is expired and refresh if needed
    if user.token_expiry <= datetime.utcnow():
        if not refresh_token(user, spotify_api):
            return False

    # Time ranges to fetch
    time_ranges = ['short_term', 'medium_term', 'long_term']

    for time_range in time_ranges:
        # Fetch top tracks for this time range using Spotify API utility
        tracks_data = spotify_api.get_top_tracks(user.access_token, time_range)

        if not tracks_data:
            continue

        # Store track information
        track_ids = []
        for i, item in enumerate(tracks_data['items']):
            track = Track.query.filter_by(id=item['id'], user_id=user.id, time_range=time_range).first()

            if not track:
                track = Track(
                    id=item['id'],
                    user_id=user.id,
                    name=item['name'],
                    artist=item['artists'][0]['name'],
                    album=item['album']['name'],
                    album_image_url=item['album']['images'][0]['url'] if item['album']['images'] else None,
                    popularity=item['popularity'],
                    time_range=time_range,
                    rank=i + 1
                )
                db.session.add(track)
            else:
                track.rank = i + 1
                track.popularity = item['popularity']
                track.created_at = datetime.utcnow()

            track_ids.append(item['id'])

        db.session.commit()

        # Fetch audio features in batches
        fetch_audio_features(track_ids, user.access_token)

    return True


#todo: put into helper file
def fetch_audio_features(track_ids, access_token):
    from models import db
    """
    Fetch audio features for a list of tracks.

    Args:
        track_ids: List of track IDs
        access_token: Valid access token
    """
    # Process in batches of 100 (Spotify API limit)
    for i in range(0, len(track_ids), 100):
        batch_ids = track_ids[i:i + 100]
        ids_param = ','.join(batch_ids)

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        # Direct API call for audio features (not in SpotifyAPI class yet)
        import requests
        features_response = requests.get(
            f"https://api.spotify.com/v1/audio-features?ids={ids_param}",
            headers=headers
        )

        if not features_response.ok:
            continue

        features_data = features_response.json()

        for feature in features_data['audio_features']:
            if not feature:
                continue

            audio_feature = AudioFeatures.query.filter_by(id=feature['id']).first()

            if not audio_feature:
                audio_feature = AudioFeatures(
                    id=feature['id'],
                    track_id=feature['id'],
                    danceability=feature['danceability'],
                    energy=feature['energy'],
                    key=feature['key'],
                    loudness=feature['loudness'],
                    mode=feature['mode'],
                    speechiness=feature['speechiness'],
                    acousticness=feature['acousticness'],
                    instrumentalness=feature['instrumentalness'],
                    liveness=feature['liveness'],
                    valence=feature['valence'],
                    tempo=feature['tempo'],
                    duration_ms=feature['duration_ms'],
                    time_signature=feature['time_signature']
                )
                db.session.add(audio_feature)
            else:
                # Update existing features
                audio_feature.danceability = feature['danceability']
                audio_feature.energy = feature['energy']
                audio_feature.key = feature['key']
                audio_feature.loudness = feature['loudness']
                audio_feature.mode = feature['mode']
                audio_feature.speechiness = feature['speechiness']
                audio_feature.acousticness = feature['acousticness']
                audio_feature.instrumentalness = feature['instrumentalness']
                audio_feature.liveness = feature['liveness']
                audio_feature.valence = feature['valence']
                audio_feature.tempo = feature['tempo']
                audio_feature.duration_ms = feature['duration_ms']
                audio_feature.time_signature = feature['time_signature']

        db.session.commit()


def refresh_token(user, spotify_api):
    from models import db
    """
    Refresh access token using refresh token.

    Args:
        user: User object
        spotify_api: SpotifyAPI instance

    Returns:
        bool: Success status
    """
    # This function would need to be added to the SpotifyAPI class
    # For now, we'll implement it here
    import requests
    import base64

    auth_string = f"{app.config['SPOTIFY_CLIENT_ID']}:{app.config['SPOTIFY_CLIENT_SECRET']}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')

    headers = {
        'Authorization': f'Basic {auth_base64}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': user.refresh_token
    }

    response = requests.post(app.config['TOKEN_URL'], headers=headers, data=data)

    if not response.ok:
        return False

    token_data = response.json()

    # Update user's access token and expiry
    user.access_token = token_data['access_token']

    # Refresh token is only provided if it has changed
    if 'refresh_token' in token_data:
        user.refresh_token = token_data['refresh_token']

    user.token_expiry = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
    db.session.commit()

    return True


# Create a Flask application instance
app = create_app()

# When running this file directly
if __name__ == '__main__':
    from models import db
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(debug=True)