# app.py – Integrated EchoMood Flask Application
import socket
import os
import uuid
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, flash, url_for, session, request, jsonify
from flask_wtf import FlaskForm
from collections import Counter

from wtforms import EmailField, PasswordField, SubmitField, StringField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, EqualTo, NumberRange
from flask_wtf.csrf import CSRFProtect

from models import db, User, Track, AudioFeatures, Friend
from utils.spotify import SpotifyAPI
from config import config

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

    # Load configuration
    app_config = config[config_name]

    # app_config = config#[config_name]
    app.config.from_object(app_config)

    # Secret key
    app.secret_key = app.config.get('SECRET_KEY')
    print("app.secret_key", app.secret_key)

    from flask_migrate import Migrate
    migrate = Migrate(app, db)

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

    ## ADMIN ROUTE -- inspect database
    #/admin/inspect-db/fixed-dev_secret_key
    @app.route('/admin/inspect-db/<secret_token>', methods=['GET'])
    def inspect_db(secret_token):
        # Simple security check - use a long, random string in production
        if secret_token != app.config.get('SECRET_KEY', ''):
            print("key: ", app.config.get('SECRET_KEY', ''))
            return "Unauthorized", 401

        # Get all tables
        users = User.query.all()

        friends = Friend.query.all()
        # Get friendship details with names
        friendship_details = []
        for f in friends:
            user = User.query.get(f.user_id)
            friend = User.query.get(f.friend_id)
            friendship_details.append({
                'id': f.id,
                'user_name': user.display_name or f"{user.first_name} {user.last_name}".strip() if user else "Unknown",
                'user_id': f.user_id,
                'friend_name': friend.display_name or f"{friend.first_name} {friend.last_name}".strip() if friend else "Unknown",
                'friend_id': f.friend_id,
                'status': f.status,
                'share_data': f.share_data,
                'created_at': f.created_at
            })

        # Get basic statistics
        stats = {
            'users': User.query.count(),
            'friends_pending': Friend.query.filter_by(status='pending').count(),
            'friends_accepted': Friend.query.filter_by(status='accepted').count(),
            'friends_rejected': Friend.query.filter_by(status='rejected').count(),
        }

        return render_template('admin_inspect.html',
                               users=users,
                               friends=friends,
                               friendship_details=friendship_details,
                               stats=stats)

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
            # Store user info in session for login
            session['user_id'] = new_user.id
            session['user_email'] = new_user.email
            session['first_name'] = new_user.first_name

            flash('Account created successfully! Connect your Spotify account to unlock all features.', 'success')
            # new dashboard with connect via spotify option
            return redirect(url_for('dashboard'))
        
        # Handle Spotify signup continuation
        if 'spotify_user_id' in session:
            # Spotify signup continuation
            user_id = session['spotify_user_id']
            display_name = session.get('display_name', '')
            access_token = session.get('access_token')
            refresh_token = session.get('refresh_token')
            token_expiry = datetime.fromisoformat(session.get('token_expiry'))

            new_user = User(
                id=user_id,
                email=form.email.data,
                display_name=display_name,
                first_name=display_name.split()[0] if display_name else '',
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
                last_login=datetime.utcnow()
            )
            new_user.set_password(form.password.data)

            db.session.add(new_user)
            db.session.commit()
            session.clear()
            flash("Account created successfully!", "success")
            return redirect(url_for('login'))

        return render_template('signup_cred.html', form=form)

    # new dashboard with connect via spotify option
    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('login'))

        # Get friends
        friends_sent = Friend.query.filter_by(user_id=user.id, status='accepted').all()
        friends_received = Friend.query.filter_by(friend_id=user.id, status='accepted').all()

        # Get pending requests
        pending_requests = Friend.query.filter_by(friend_id=user.id, status='pending').all()

        # Process friends list
        friends_list = []
        for f in friends_sent:
            friend_user = User.query.get(f.friend_id)
            if friend_user:
                friends_list.append({
                    'id': friend_user.id,
                    'name': friend_user.display_name or f"{friend_user.first_name} {friend_user.last_name}".strip(),
                    'share_data': f.share_data
                })

        for f in friends_received:
            friend_user = User.query.get(f.user_id)
            if friend_user:
                friends_list.append({
                    'id': friend_user.id,
                    'name': friend_user.display_name or f"{friend_user.first_name} {friend_user.last_name}".strip(),
                    'share_data': f.share_data
                })

        # Process pending requests
        pending_list = []
        for req in pending_requests:
            requester = User.query.get(req.user_id)
            if requester:
                pending_list.append({
                    'id': req.id,
                    'user_id': requester.id,
                    'name': requester.display_name or f"{requester.first_name} {requester.last_name}".strip()
                })

        return render_template('dashboard.html',
                               user=user,
                               friends=friends_list,
                               pending_requests=pending_list)
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

                # Redirect to dashboard
                return redirect(url_for('dashboard'))
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
        scope = 'user-top-read user-read-private user-read-recently-played user-read-email'

        # Get authorization URL from Spotify API utility
        auth_url = spotify_api.get_auth_url(state, scope)
        print("AUTH URL", auth_url)

        return redirect(auth_url)

    # ----------------------------------------------------------
    # Spotify OAuth Callback
    # ----------------------------------------------------------
    @app.route('/callback')
    def callback():
        # Verify state to prevent CSRF attacks
        print("State from request:", request.args.get('state'))
        if request.args.get('state') != session.get('state'):
            flash('Authentication error. Please try again.', 'danger')
            return redirect(url_for('index'))
        print("State verified successfully.")
        
        # Check for errors in the callback
        if request.args.get('error'):
            flash('Authentication was denied.', 'warning')
            return redirect(url_for('index'))
        print("No error in callback.")
        
        # Check if the code is present in the callback
        print("Code from request:", request.args.get('code'))
        # Get the authorization code
        code = request.args.get('code')

        if not code:
            flash('Authentication error. Please try again.', 'danger')
            return redirect(url_for('index'))

        # Exchange code for access token
        token_data = spotify_api.get_access_token(code)
        print("Token data:", token_data)
        
        # Check if token data is valid
        if not token_data:
            print("❌ Failed to get access token. Response:", token_data)
            flash('Failed to authenticate with Spotify.', 'danger')
            return redirect(url_for('index'))

        # Extract token information
        access_token = token_data['access_token']
        refresh_token = token_data['refresh_token']
        expires_in = token_data['expires_in']
        token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
        session['access_token'] = access_token

        # Get user profile using Spotify API
        user_data = spotify_api.get_user_profile(access_token)
        print("User data:", user_data)

        # Check if we're linking an existing account
        linking = session.pop('linking', False)
        if linking and 'user_id' in session:
            # User is already logged in, just link the Spotify account
            existing_user = User.query.get(session['user_id'])

            if existing_user:
                existing_user.access_token = access_token
                existing_user.refresh_token = refresh_token
                existing_user.token_expiry = token_expiry
                existing_user.spotify_id = user_data['id']
                db.session.commit()

                flash('Spotify account linked successfully!', 'success')
                return redirect(url_for('dashboard'))

        # Check if user data is valid
        if not user_data:
            flash('Failed to retrieve user information.', 'danger')
            return redirect(url_for('index'))

        # First check if a user with this Spotify ID exists
        user = User.query.filter_by(id=user_data['id']).first()

        # If not, check if a user with this email exists
        if not user and 'email' in user_data and user_data['email']:
            user = User.query.filter_by(email=user_data['email']).first()

        if user:
            # Update existing user with Spotify data
            user.access_token = access_token
            user.refresh_token = refresh_token
            user.token_expiry = token_expiry

            # If this was an email-only user before, add the Spotify ID
            if not user.id.startswith('spotify:'):
                # We can't change the primary key, so we'll link via other fields
                user.spotify_id = user_data['id']

            user.last_login = datetime.utcnow()
        else:
            # Check if email is returned by Spotify
            if not user_data.get('email'):
                # Store Spotify data in session and redirect to signup credential page
                session['spotify_id'] = user_data['id']
                session['display_name'] = user_data.get('display_name', '')
                session['access_token'] = access_token
                session['refresh_token'] = refresh_token
                session['token_expiry'] = token_expiry.isoformat()  # Store as string for JSON compatibility
                session['spotify_login_pending'] = True  # flag to signal pending signup

                flash("We couldn't retrieve your email from Spotify. Please complete your signup.", 'warning')
                return redirect(url_for('signup_login_credentials'))

            # Create new user from Spotify data
            display_name = user_data.get('display_name', '')
            first_name = display_name.split()[0] if display_name else ''
            last_name = ' '.join(display_name.split()[1:]) if len(display_name.split()) > 1 else ''

            user = User(
                id=user_data['id'],
                spotify_id=user_data['id'],
                email=user_data.get('email', ''),
                display_name=display_name,
                first_name=first_name,
                last_name=last_name,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
                registration_method='spotify',
                last_login=datetime.utcnow()
            )
            db.session.add(user)
            
        db.session.commit()

        # Store user info in session
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['first_name'] = user.first_name or user.display_name.split()[0] if user.display_name else 'User'

        # If user doesn't have a password (Spotify-only registration), redirect to set one
        if user.registration_method == 'spotify' and not user.password:
            flash('Please complete your account setup by setting a password.', 'info')
            return redirect(url_for('complete_account'))

        # Otherwise proceed to visualization
        return redirect(url_for('visualise'))

    # users need to complete account if they haven't connected spotify but have made an account
    @app.route('/complete_account', methods=['GET', 'POST'])
    def complete_account():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('login'))

        # If user already has a password, redirect
        if user.password:
            return redirect(url_for('visualise'))

        # Create a form for password
        class CompleteAccountForm(FlaskForm):
            password = PasswordField('Password', validators=[
                DataRequired(),
                # Add password strength requirements if needed
            ])
            confirm_password = PasswordField('Confirm Password', validators=[
                DataRequired(),
                EqualTo('password', message='Passwords must match')
            ])
            submit = SubmitField('Complete Account')

        form = CompleteAccountForm()

        if form.validate_on_submit():
            user.set_password(form.password.data)
            db.session.commit()
            flash('Account setup completed! You can now log in using either Spotify or your email and password.',
                  'success')
            return redirect(url_for('visualise'))

        return render_template('complete_account.html', form=form, user=user)

    # ----------------------------------------------------------
    # Visualization Route
    # ----------------------------------------------------------
    @app.route('/visualise')
    def visualise():
        print("Access Token from session:", session.get('access_token'))

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

        # # Fetch all mood labels for this user from the AudioFeatures table
        # all_features = AudioFeatures.query.join(Track, AudioFeatures.track_id == Track.id).filter(
        #     Track.user_id == user_id
        # ).all()

        # # Count how many times each mood appears
        # mood_counts = Counter(f.mood for f in all_features)

        # ✅ Replace old audio_features logic with this:
        mood_counts = session.get('mood_counts', {})
        print("🔍 mood_counts:", mood_counts)

        total = sum(mood_counts.values()) or 1  # avoid division by zero

        # Build mood_data with percentage breakdown
        mood_data = {}
        for mood, count in mood_counts.items():
            mood_data[mood.lower()] = {
                "percentage": round(100 * count / total),  # Convert to percentage
                "top_track": None,  # TODO: You can add top track per mood here
                "recommended_tracks": []  # TODO: You can add recommendations here
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

    # route to link spotify account
    @app.route('/link/spotify')
    def link_spotify():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        # Generate state for CSRF protection
        state = str(uuid.uuid4())
        session['state'] = state
        session['linking'] = True  # Flag to indicate we're linking accounts

        # Define scopes needed for the application
        scope = 'user-top-read user-read-private user-read-recently-played'

        # Get authorization URL from Spotify API utility
        auth_url = spotify_api.get_auth_url(state, scope)

        return redirect(auth_url)

    # route to unlink spotify account
    @app.route('/unlink/spotify', methods=['POST'])
    def unlink_spotify():
        if 'user_id' not in session:
            return redirect(url_for('login'))

        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            return redirect(url_for('login'))

        # Reset Spotify-related fields
        user.access_token = None
        user.refresh_token = None
        user.token_expiry = None
        db.session.commit()

        flash('Spotify account unlinked successfully.', 'success')
        return redirect(url_for('dashboard'))

    # ----------------------------------------------------------
    # Friends Routes
    # ----------------------------------------------------------
    @app.route('/friends')
    def friends():
        """View friends list and manage friend requests"""
        if 'user_id' not in session:
            flash('Please log in to view your friends.', 'warning')
            return redirect(url_for('login'))

        user_id = session['user_id']

        # Get accepted friends
        friends_sent = Friend.query.filter_by(user_id=user_id, status='accepted').all()
        friends_received = Friend.query.filter_by(friend_id=user_id, status='accepted').all()

        # Get pending requests
        pending_requests = Friend.query.filter_by(friend_id=user_id, status='pending').all()

        # Combine friends from both directions
        friends_list = []
        for f in friends_sent:
            friend_user = User.query.get(f.friend_id)
            if friend_user:
                friends_list.append({
                    'id': friend_user.id,
                    'name': friend_user.display_name or f"{friend_user.first_name} {friend_user.last_name}".strip(),
                    'share_data': f.share_data
                })

        for f in friends_received:
            friend_user = User.query.get(f.user_id)
            if friend_user:
                friends_list.append({
                    'id': friend_user.id,
                    'name': friend_user.display_name or f"{friend_user.first_name} {friend_user.last_name}".strip(),
                    'share_data': f.share_data
                })

        # Process pending requests
        pending_list = []
        for req in pending_requests:
            requester = User.query.get(req.user_id)
            if requester:
                pending_list.append({
                    'id': req.id,
                    'user_id': requester.id,
                    'name': requester.display_name or f"{requester.first_name} {requester.last_name}".strip()
                })

        return render_template('friends.html',
                               friends=friends_list,
                               pending_requests=pending_list)

    @app.route('/friends/search', methods=['GET', 'POST'])
    def search_friends():
        """Search for users to add as friends"""
        if 'user_id' not in session:
            flash('Please log in to search for friends.', 'warning')
            return redirect(url_for('login'))

        user_id = session['user_id']
        query = request.args.get('query', '')

        if not query:
            return render_template('friend_search.html', results=[], query='')

        # Search for users by name or email
        results = User.query.filter(
            User.id != user_id,
            db.or_(
                User.display_name.ilike(f'%{query}%'),
                User.first_name.ilike(f'%{query}%'),
                User.last_name.ilike(f'%{query}%'),
                User.email.ilike(f'%{query}%')
            )
        ).all()

        # Check existing friendship status
        processed_results = []
        for user in results:
            # Check if already friends or request pending
            friendship_sent = Friend.query.filter_by(user_id=user_id, friend_id=user.id).first()
            friendship_received = Friend.query.filter_by(user_id=user.id, friend_id=user_id).first()

            status = 'none'
            if friendship_sent:
                status = friendship_sent.status
            elif friendship_received:
                status = friendship_received.status

            processed_results.append({
                'id': user.id,
                'name': user.display_name or f"{user.first_name} {user.last_name}".strip(),
                'email': user.email,
                'status': status
            })

        return render_template('friend_search.html', results=processed_results, query=query)

    @app.route('/friends/add', methods=['POST'])
    def add_friend():
        """Send a friend request"""
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = session['user_id']
        friend_id = request.form.get('friend_id')

        if not friend_id:
            flash('Invalid friend request.', 'danger')
            return redirect(url_for('friends'))

        if user_id == friend_id:
            flash('You cannot add yourself as a friend.', 'warning')
            return redirect(url_for('friends'))

        # Check if friend request already exists
        existing = Friend.query.filter_by(user_id=user_id, friend_id=friend_id).first()
        if existing:
            flash('Friend request already sent.', 'info')
            return redirect(url_for('friends'))

        # Check if they sent you a request first
        existing = Friend.query.filter_by(user_id=friend_id, friend_id=user_id).first()
        if existing:
            if existing.status == 'pending':
                # Auto-accept if they sent you a request
                existing.status = 'accepted'
                db.session.commit()
                flash('Friend request accepted!', 'success')
                return redirect(url_for('friends'))

        # Create new friend request
        new_request = Friend(user_id=user_id, friend_id=friend_id, status='pending')
        db.session.add(new_request)
        db.session.commit()

        flash('Friend request sent!', 'success')
        return redirect(url_for('friends'))

    @app.route('/friends/accept', methods=['POST'])
    def accept_friend():
        """Accept a friend request"""
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = session['user_id']
        request_id = request.form.get('request_id')

        friend_request = Friend.query.filter_by(id=request_id, friend_id=user_id, status='pending').first()

        if not friend_request:
            flash('Friend request not found.', 'danger')
            return redirect(url_for('friends'))

        friend_request.status = 'accepted'
        db.session.commit()

        flash('Friend request accepted!', 'success')
        return redirect(url_for('friends'))

    @app.route('/friends/reject', methods=['POST'])
    def reject_friend():
        """Reject a friend request"""
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = session['user_id']
        request_id = request.form.get('request_id')

        friend_request = Friend.query.filter_by(id=request_id, friend_id=user_id, status='pending').first()

        if not friend_request:
            flash('Friend request not found.', 'danger')
            return redirect(url_for('friends'))

        friend_request.status = 'rejected'
        db.session.commit()

        flash('Friend request rejected.', 'info')
        return redirect(url_for('friends'))

    @app.route('/friends/toggle-share', methods=['POST'])
    def toggle_share():
        """Toggle data sharing with a friend"""
        if 'user_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401

        user_id = session['user_id']
        friend_id = request.form.get('friend_id')

        # Check both directions of friendship
        friendship = Friend.query.filter_by(user_id=user_id, friend_id=friend_id, status='accepted').first()
        if not friendship:
            friendship = Friend.query.filter_by(user_id=friend_id, friend_id=user_id, status='accepted').first()

        if not friendship:
            return jsonify({'error': 'Friendship not found'}), 404

        # Toggle share status
        friendship.share_data = not friendship.share_data
        db.session.commit()

        return jsonify({'success': True, 'sharing': friendship.share_data})

    @app.route('/friends/<friend_id>/visualise')
    def friend_visualise(friend_id):
        """View a friend's visualisation data"""
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))

        user_id = session['user_id']

        # Check if friends with sharing enabled
        friendship1 = Friend.query.filter_by(user_id=user_id, friend_id=friend_id, status='accepted',
                                             share_data=True).first()
        friendship2 = Friend.query.filter_by(user_id=friend_id, friend_id=user_id, status='accepted',
                                             share_data=True).first()

        if not friendship1 and not friendship2:
            flash('You do not have permission to view this data.', 'warning')
            return redirect(url_for('friends'))

        friend = User.query.get(friend_id)
        if not friend:
            flash('Friend not found.', 'danger')
            return redirect(url_for('friends'))

        # Get time range from query parameters (default to medium_term)
        time_range = request.args.get('time_range', 'medium_term')

        # Get friend's mood data - similar logic as in the visualise route
        # Fetch all mood labels for this friend from the AudioFeatures table
        all_features = AudioFeatures.query.join(Track, AudioFeatures.track_id == Track.id).filter(
            Track.user_id == friend_id
        ).all()

        # Count how many times each mood appears
        from collections import Counter
        mood_counts = Counter(f.mood for f in all_features)
        total = sum(mood_counts.values()) or 1  # avoid division by zero

        # Build mood_data with percentage breakdown
        mood_data = {}
        for mood, count in mood_counts.items():
            # Skip if mood is None
            if not mood:
                continue

            mood_data[mood.lower()] = {
                "percentage": round(100 * count / total),  # Convert to percentage
                "top_track": None,  # You can populate this if you have the data
                "recommended_tracks": []  # You can populate this if you have the data
            }

        # Generate or fetch personality data
        personality_data = {
            "mbti": "INTJ",  # This should be fetched from the database if available
            "summary": "Strategic, independent, and insightful.",
            "related_songs": []  # You can populate this if you have the data
        }

        # Pass friend's name to the template
        friend_name = friend.display_name or f"{friend.first_name} {friend.last_name}".strip()

        return render_template('visualise.html',
                               first_name=friend_name,
                               time_range=time_range,
                               mood_data=mood_data,
                               personality=personality_data,
                               is_friend_view=True,
                               friend_id=friend_id)

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

        mood_counts = Counter()

        for time_range in time_ranges:
            # Fetch top tracks for this time range
            tracks_data = spotify_api.get_top_tracks(user.access_token, time_range)

            if not tracks_data:
                continue

            # Store track information
            track_ids = []
            artist_ids = []


            for i, item in enumerate(tracks_data['items']):
                
                existing_track = Track.query.filter_by(
                    id=item['id'],
                    user_id=user.id,
                    time_range=time_range
                ).first()

                artist_id = item['artists'][0]['id']
                artist_ids.append(artist_id)

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

            # After storing tracks and features, fetch artist genres
            genre_map = spotify_api.get_artists_genres(user.access_token, artist_ids)

            print(f"[DEBUG] artist_ids: {artist_ids}")
            print(f"[DEBUG] genre_map: {genre_map}")

            GENRE_TO_MOOD = {
                'pop': 'Happy',
                'dance pop': 'Happy',
                'sad indie': 'Sad',
                'emo': 'Sad',
                'chillwave': 'Chill',
                'ambient': 'Chill',
                'metal': 'Angry',
                'rap': 'Focused',
                'classical': 'Focused',
                'hip hop': 'Focused',
                'rock': 'Happy',
                'trap': 'Angry'
            }

            for artist_id in artist_ids:
                genres = genre_map.get(artist_id, [])
                matched = False
                for genre in genres:
                    for key in GENRE_TO_MOOD:
                        if key in genre:
                            mood = GENRE_TO_MOOD[key]
                            mood_counts[mood] += 1
                            matched = True
                            break
                    if matched:
                        break

        return dict(mood_counts)

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
        print(f"[DEBUG] Fetching audio features for {len(track_ids)} tracks")
        # Use the unified SpotifyAPI class
        features_map = spotify_api.get_audio_features(access_token, track_ids)
        print(f"[DEBUG] Received features for {len(features_map)} tracks")

        for track_id in track_ids:
            features = features_map.get(track_id)

            if not features:
                continue

            audio_feature = AudioFeatures.query.filter_by(id=track_id).first()

            if not audio_feature:
                audio_feature = AudioFeatures(
                    id=track_id,
                    track_id=track_id,
                    danceability=features['danceability'],
                    energy=features['energy'],
                    key=features['key'],
                    loudness=features['loudness'],
                    mode=features['mode'],
                    speechiness=features['speechiness'],
                    acousticness=features['acousticness'],
                    instrumentalness=features['instrumentalness'],
                    liveness=features['liveness'],
                    valence=features['valence'],
                    tempo=features['tempo'],
                    duration_ms=features['duration_ms'],
                    time_signature=features['time_signature'],
                    mood=SpotifyAPI.analyze_mood_from_features(features)
                )
                db.session.add(audio_feature)
            else:
                audio_feature.danceability = features['danceability']
                audio_feature.energy = features['energy']
                audio_feature.key = features['key']
                audio_feature.loudness = features['loudness']
                audio_feature.mode = features['mode']
                audio_feature.speechiness = features['speechiness']
                audio_feature.acousticness = features['acousticness']
                audio_feature.instrumentalness = features['instrumentalness']
                audio_feature.liveness = features['liveness']
                audio_feature.valence = features['valence']
                audio_feature.tempo = features['tempo']
                audio_feature.duration_ms = features['duration_ms']
                audio_feature.time_signature = features['time_signature']
                audio_feature.mood = SpotifyAPI.analyze_mood_from_features(features)

        db.session.commit()

    # ----------------------------------------------------------
    # Logout Route
    # ----------------------------------------------------------
    @app.route('/logout', methods=['POST'])
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