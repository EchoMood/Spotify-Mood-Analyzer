# app.py – Integrated EchoMood Flask Application
import os
import uuid
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, flash, url_for, session, request, jsonify
from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, StringField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, EqualTo, NumberRange
from flask_wtf.csrf import CSRFProtect

from models import db, User, Track, AudioFeatures
from utils.spotify import SpotifyAPI


# ----------------------------------------------------------
# Form Classes
# ----------------------------------------------------------
class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class SignupStepOneForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[Optional()])
    age = IntegerField('Age',
                       validators=[DataRequired(), NumberRange(min=13, message="You must be at least 13 years old")])
    continue_button = SubmitField('Continue')


class SignupStepTwoForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        # Add password strength requirements if needed
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Sign Up')


# ----------------------------------------------------------
# Flask App Configuration and Initialization
# ----------------------------------------------------------
def create_app(config_name='development'):
    app = Flask(__name__)

    # Load configuration from environment or config file
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-for-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///echomood.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Spotify API credentials
    app.config['SPOTIFY_CLIENT_ID'] = os.getenv('SPOTIFY_CLIENT_ID', '')
    app.config['SPOTIFY_CLIENT_SECRET'] = os.getenv('SPOTIFY_CLIENT_SECRET', '')
    app.config['REDIRECT_URI'] = os.getenv('REDIRECT_URI', 'http://localhost:5000/callback')
    app.config['TOKEN_URL'] = 'https://accounts.spotify.com/api/token'

    # Enable CSRF protection
    csrf = CSRFProtect(app)

    # Initialize database
    db.init_app(app)

    # Initialize Spotify API helper
    spotify_api = SpotifyAPI()
    spotify_api.init_app(app)

    # ----------------------------------------------------------
    # Index Route – Landing page for EchoMood
    # ----------------------------------------------------------
    @app.route('/')
    def index():
        return render_template('index.html')

    # ----------------------------------------------------------
    # Step 1: Basic Info for Traditional Signup
    # ----------------------------------------------------------
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        form = SignupStepOneForm()
        if form.validate_on_submit():
            session['first_name'] = form.first_name.data
            session['last_name'] = form.last_name.data
            session['age'] = form.age.data
            return redirect(url_for('signup_login_credentials'))
        return render_template('signup.html', form=form)

    # ----------------------------------------------------------
    # Step 2: Login Credentials for Traditional Signup
    # ----------------------------------------------------------
    @app.route('/signup/login_credentials', methods=['GET', 'POST'])
    def signup_login_credentials():
        form = SignupStepTwoForm()

        # Prevent direct access to Step 2 if Step 1 not done
        if not session.get('first_name'):
            flash('Please complete Step 1 first.', 'warning')
            return redirect(url_for('signup'))

        # Check if the form is submitted and valid
        if form.validate_on_submit():
            # Retrieve values from session (Step 1)
            first_name = session.get('first_name')
            last_name = session.get('last_name')
            age = session.get('age')
            email = form.email.data

            # Check if the email already exists in the database
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('An account with this email already exists. Please proceed to the login page.', 'danger')
                return render_template('signup_cred.html', form=form)

            # Create a new user with a generated ID (since Spotify users have IDs from the service)
            user_id = f"local_{str(uuid.uuid4())}"
            new_user = User(
                id=user_id,
                first_name=first_name,
                last_name=last_name,
                age=age,
                email=email,
                display_name=f"{first_name} {last_name}".strip()
            )
            new_user.set_password(form.password.data)

            db.session.add(new_user)
            db.session.commit()

            # Clear session data and redirect
            session.clear()
            flash('Account created successfully!', 'success')
            return redirect(url_for('login'))

        return render_template('signup_cred.html', form=form)

    # ----------------------------------------------------------
    # Traditional Login Route
    # ----------------------------------------------------------
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        form = LoginForm()

        if form.validate_on_submit():
            # Extract form data
            email = form.email.data
            password = form.password.data

            # Query database for matching email
            user = User.query.filter_by(email=email).first()

            # Validate password
            if user and user.check_password(password):
                flash('Login successful!', 'success')
                # Store user info in session
                session['user_id'] = user.id
                session['user_email'] = user.email
                session['first_name'] = user.first_name

                # Redirect to visualization
                return redirect(url_for('visualise'))
            else:
                flash('Invalid email or password. Please try again.', 'danger')

        return render_template('login.html', form=form)

    # ----------------------------------------------------------
    # Spotify OAuth Login
    # ----------------------------------------------------------
    @app.route('/oauth/spotify')
    def oauth_spotify():
        # Generate state for CSRF protection
        state = str(uuid.uuid4())
        session['state'] = state

        # Define scopes needed for the application
        scope = 'user-top-read user-read-private user-read-recently-played'

        # Get authorization URL from Spotify API utility
        auth_url = spotify_api.get_auth_url(state, scope)

        return redirect(auth_url)

    # ----------------------------------------------------------
    # Spotify OAuth Callback
    # ----------------------------------------------------------
    @app.route('/callback')
    def callback():
        # Verify state to prevent CSRF attacks
        if request.args.get('state') != session.get('state'):
            flash('Authentication error. Please try again.', 'danger')
            return redirect(url_for('index'))

        # Check for errors in the callback
        if request.args.get('error'):
            flash('Authentication was denied.', 'warning')
            return redirect(url_for('index'))

        # Get the authorization code
        code = request.args.get('code')

        if not code:
            flash('Authentication error. Please try again.', 'danger')
            return redirect(url_for('index'))

        # Exchange code for access token
        token_data = spotify_api.get_access_token(code)

        if not token_data:
            flash('Failed to authenticate with Spotify.', 'danger')
            return redirect(url_for('index'))

        # Extract token information
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        expires_in = token_data['expires_in']
        token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)

        # Get user profile
        user_data = spotify_api.get_user_profile(access_token)

        if not user_data:
            flash('Failed to retrieve user information.', 'danger')
            return redirect(url_for('index'))

        # Save or update user in database
        user = User.query.filter_by(id=user_data['id']).first()

        if user:
            # Update existing user
            user.access_token = access_token
            user.refresh_token = refresh_token
            user.token_expiry = token_expiry
            user.last_login = datetime.utcnow()
            # If existing user logged in through Spotify but didn't have an email yet
            if not user.email and 'email' in user_data:
                user.email = user_data.get('email')
        else:
            # Create new user from Spotify data
            user = User(
                id=user_data['id'],
                email=user_data.get('email', ''),
                display_name=user_data.get('display_name', ''),
                first_name=user_data.get('display_name', '').split()[0] if user_data.get('display_name') else '',
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
                last_login=datetime.utcnow()
            )
            db.session.add(user)

        db.session.commit()

        # Store user info in session
        session['user_id'] = user.id
        session['user_email'] = user.email
        if user.first_name:
            session['first_name'] = user.first_name
        else:
            session['first_name'] = user.display_name.split()[0] if user.display_name else 'User'

        # Fetch user's Spotify data
        fetch_and_store_user_data(user.id, spotify_api)

        # Redirect to visualization
        return redirect(url_for('visualise'))

    # ----------------------------------------------------------
    # Visualization Route
    # ----------------------------------------------------------
    @app.route('/visualise')
    def visualise():
        # Check if user is logged in
        if 'user_id' not in session:
            flash('Please log in to view your visualisation.', 'warning')
            return redirect(url_for('login'))

        user_id = session['user_id']
        user = User.query.get(user_id)

        if not user:
            flash('User not found. Please log in again.', 'warning')
            session.clear()
            return redirect(url_for('login'))

        # Get time range from query parameters (default to medium_term)
        time_range = request.args.get('time_range', 'medium_term')

        # Generate or fetch mood data
        # In a real app, this would come from your database or Spotify API
        mood_data = {
            "happy": {
                "percentage": 35,
                "top_track": {
                    "name": "Good Feeling",
                    "artist": "Flo Rida",
                    "image": "https://i.scdn.co/image/ab67616d0000b273c8f96a1b8bfcf4d821fbbb3a"
                },
                "recommended_tracks": [
                    {
                        "name": "Happy",
                        "artist": "Pharrell Williams",
                        "image": "https://i.scdn.co/image/ab67616d0000b2734c55ac0c5e7be8c6394d7a21"
                    },
                    {
                        "name": "Can't Stop the Feeling!",
                        "artist": "Justin Timberlake",
                        "image": "https://i.scdn.co/image/ab67616d0000b273a4547d2fb82a280be3ddba55"
                    },
                    {
                        "name": "Uptown Funk",
                        "artist": "Mark Ronson ft. Bruno Mars",
                        "image": "https://i.scdn.co/image/ab67616d0000b2736b3d4c74ca886c9803af48e0"
                    }
                ]
            },
            # ... (rest of the mood data remains the same)
        }

        # Generate or fetch personality data
        personality_data = {
            "mbti": "INTJ",
            "summary": "Strategic, independent, and insightful. You're a deep thinker who appreciates complex musical compositions and meaningful lyrics.",
            "related_songs": [
                {
                    "name": "Lateralus",
                    "artist": "Tool",
                    "image": "https://i.scdn.co/image/ab67616d0000b2739b2c7c8dd5136c2fa101da20"
                },
                # ... (rest of the personality data remains the same)
            ]
        }

        return render_template('visualise.html',
                               first_name=session.get('first_name', 'User'),
                               time_range=time_range,
                               mood_data=mood_data,
                               personality=personality_data)

    # ----------------------------------------------------------
    # API Endpoint for Mood Data (AJAX)
    # ----------------------------------------------------------
    @app.route('/api/mood-data')
    def mood_data_api():
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        time_range = request.args.get('time_range', 'medium_term')
        user_id = session['user_id']

        # In a real app, generate or fetch mood data based on the time range
        # Simplified example data
        mood_data = {
            # Similar structure as above, but modified based on time_range
        }

        return jsonify(mood_data)

    # ----------------------------------------------------------
    # Fetch and Store User's Spotify Data
    # ----------------------------------------------------------
    def fetch_and_store_user_data(user_id, spotify_api):
        user = User.query.get(user_id)

        if not user or not user.access_token:
            return False

        # Check if token is expired and refresh if needed
        if user.token_expiry and user.token_expiry <= datetime.utcnow():
            if not refresh_token(user, spotify_api):
                return False

        # Time ranges to fetch
        time_ranges = ['short_term', 'medium_term', 'long_term']

        for time_range in time_ranges:
            # Fetch top tracks for this time range
            tracks_data = spotify_api.get_top_tracks(user.access_token, time_range)

            if not tracks_data:
                continue

            # Store track information
            track_ids = []

            for i, item in enumerate(tracks_data['items']):
                existing_track = Track.query.filter_by(
                    id=item['id'],
                    user_id=user.id,
                    time_range=time_range
                ).first()

                if existing_track:
                    # Update existing track
                    existing_track.rank = i + 1
                    existing_track.popularity = item['popularity']
                    existing_track.created_at = datetime.utcnow()
                else:
                    # Create new track
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

                track_ids.append(item['id'])

            db.session.commit()

            # Fetch audio features in batches
            fetch_audio_features(track_ids, user.access_token)

        return True

    # ----------------------------------------------------------
    # Refresh Token Helper Function
    # ----------------------------------------------------------
    def refresh_token(user, spotify_api):
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

    # ----------------------------------------------------------
    # Fetch Audio Features Helper Function
    # ----------------------------------------------------------
    def fetch_audio_features(track_ids, access_token):
        import requests

        # Process in batches of 100 (Spotify API limit)
        for i in range(0, len(track_ids), 100):
            batch_ids = track_ids[i:i + 100]
            ids_param = ','.join(batch_ids)

            headers = {
                'Authorization': f'Bearer {access_token}'
            }

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

    # ----------------------------------------------------------
    # Logout Route
    # ----------------------------------------------------------
    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    # ----------------------------------------------------------
    # Admin View Users Route (kept from original app.py)
    # ----------------------------------------------------------
    @app.route('/admin/users')
    def admin_view_users():
        """Displays all users stored in the database via HTML table."""
        all_users = User.query.all()
        return render_template('admin_users.html', users=all_users)

    # Create database tables on startup if they don't exist
    with app.app_context():
        db.create_all()

        # Add dummy admin user if it doesn't exist
        dummy_email = 'admin@example.com'
        user = User.query.filter_by(email=dummy_email).first()

        if not user:
            dummy_user = User(
                id='admin_user',
                first_name='Admin',
                last_name='User',
                age=30,
                email=dummy_email,
                display_name='Admin User'
            )
            dummy_user.set_password('adminpass')

            db.session.add(dummy_user)
            db.session.commit()
            print(f"✅ Dummy user '{dummy_email}' was added.")
        else:
            print(f"✅ Dummy user '{dummy_email}' already exists.")

    return app


# Create app instance for running directly
app = create_app()

# Main Application Entry Point
if __name__ == '__main__':
    app.run(debug=True)