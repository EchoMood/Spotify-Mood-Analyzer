# """
# Main application module for Spotify Mood Analysis.
# Initializes the Flask application and defines routes.
# """
#
# from datetime import datetime, timedelta
# import uuid
# import os
# from flask import Flask, render_template, request, session, url_for, redirect, jsonify
# from utils.spotify import SpotifyAPI
# from models import User, Track, AudioFeatures
# #from mood_analysis import MoodAnalyzer
# from config import config
#
# from flask_migrate import Migrate
#
# def create_app(config_name='development'):
#     """Create and configure the Flask application."""
#
#     app = Flask(__name__)
#
#     # Load configuration
#     app_config = config[config_name]
#     app.config.from_object(app_config)
#
#     # Secret key for session
#     app.secret_key = app.config.get('SECRET_KEY')
#     print("app.secret_key: {}".format(app.secret_key))
#
#     # Session configuration for cross-domain (important for ngrok)
#     # Only enable in production if using HTTPS
#     if app.config.get('USING_NGROK', False):
#         app.config['SESSION_COOKIE_SECURE'] = True
#         app.config['SESSION_COOKIE_SAMESITE'] = 'None'
#
#     from models import db
#     # Initialize database
#     db.init_app(app)
#     migrate = Migrate(app, db)
#
#     # Initialize Spotify API helper
#     spotify_api = SpotifyAPI()
#     spotify_api.init_app(app)
#
#     @app.route('/')
#     def index():
#         """Render the home page."""
#         return render_template('index.html')
#
#     @app.route('/login')
#     def login():
#         """
#         Redirect to Spotify authorization page.
#         Initiates the OAuth flow.
#         """
#         # Generate state for CSRF protection
#         state = str(uuid.uuid4())
#         session['state'] = state
#
#         # Define scopes needed for the application
#         scope = 'user-top-read user-read-private user-read-recently-played'
#
#         # Get authorization URL from Spotify API utility
#         auth_url = spotify_api.get_auth_url(state, scope)
#
#         print("🟢 Using redirect_uri:", app.config.get("REDIRECT_URI"))
#
#         return redirect(auth_url)
#
#     @app.route('/callback')
#     def callback():
#         """
#         Handle the callback from Spotify OAuth.
#         Exchange authorization code for access tokens.
#         """
#         # Verify state to prevent CSRF attacks
#         if request.args.get('state') != session.get('state'):
#             print("CSRF ATTACK ERROR")
#             return redirect(url_for('index'))
#
#         # Check for errors in the callback
#         if request.args.get('error'):
#             return redirect(url_for('index'))
#
#         # Get the authorization code
#         code = request.args.get('code')
#
#         # Exchange code for access token using Spotify API utility
#         print("Code: ", code)
#
#         if not code:
#             print("DEBUG no code in header")
#             return redirect(url_for('index'))
#
#         #TODO: make a call to spotify API
#         token_data = spotify_api.get_access_token(code)
#         print("Token data: ", token_data)
#
#
#         if not token_data:
#             print("DEBUG no token data, redirecting to index\n")
#             return redirect(url_for('index'))
#
#         # Extract token information
#         access_token = token_data['access_token']
#         refresh_token = token_data['refresh_token']
#         expires_in = token_data['expires_in']
#         token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
#
#         # Get user profile using Spotify API utility
#         user_data = spotify_api.get_user_profile(access_token)
#         print("User data: ", user_data)
#         # session['access_token'] = access_token
#
#         # if not user_data:
#         #     return redirect(url_for('index'))
#
#         #TODO: implement logic for database stuff
#         # Save or update user in database
#         user = User.query.filter_by(id=user_data['id']).first()
#
#         if user:
#             # Update existing user
#             user.access_token = access_token
#             user.refresh_token = refresh_token
#             user.token_expiry = token_expiry
#             user.last_login = datetime.utcnow()
#         else:
#             # Create new user
#             user = User(
#                 id=user_data['id'],
#                 email=user_data.get('email', ''),
#                 display_name=user_data.get('display_name', ''),
#                 access_token=access_token,
#                 refresh_token=refresh_token,
#                 token_expiry=token_expiry
#             )
#             db.session.add(user)
#
#         db.session.commit()
#
#         # Store user ID in session
#         session['user_id'] = user.id
#
#         # Start data collection process
#         fetch_and_store_user_data(user.id, spotify_api)
#
#         # Redirect to visualization page
#         return redirect(url_for('visualise'))
#
#     @app.route('/visualise')
#     def visualise():
#         """Render the visualization page with mood analysis."""
#         if 'access_token' not in session:
#             print("ERROR returning to index: no access_token in session\n")
#             return redirect(url_for('index'))
#
#         # Get default time range (medium_term if not specified)
#         time_range = request.args.get('time_range', 'medium_term')
#
#         #TODO: checking if user not logged in properly
#         # # Load user data for visualization
#         # user_id = session.get('user_id')
#         # user = User.query.get(user_id)
#         #
#         # if not user:
#         #
#         #     return redirect(url_for('index'))
#
#         # Initialize data structures
#         mood_data = {
#             'Happy': {'percentage': 40, 'top_song': {'name': 'Sample Song', 'artist': 'Sample Artist'}},
#             'Sad': {'percentage': 20, 'top_song': {'name': 'Sample Song 2', 'artist': 'Sample Artist 2'}},
#             'Chill': {'percentage': 15, 'top_song': {'name': 'Sample Song 3', 'artist': 'Sample Artist 3'}},
#             'Energetic': {'percentage': 15, 'top_song': {'name': 'Sample Song 4', 'artist': 'Sample Artist 4'}},
#             'Nostalgic': {'percentage': 10, 'top_song': {'name': 'Sample Song 5', 'artist': 'Sample Artist 5'}}
#         }
#
#         personality_data = {
#             'type': 'INTJ',
#             'description': 'Strategic, independent, and insightful.',
#             'related_songs': [
#                 {'name': 'Sample Song 1', 'artist': 'Sample Artist 1'},
#                 {'name': 'Sample Song 2', 'artist': 'Sample Artist 2'},
#                 {'name': 'Sample Song 3', 'artist': 'Sample Artist 3'}
#             ]
#         }
#
#         # # Try to get tracks and features if user is authenticated
#         # try:
#         #     tracks = Track.query.filter_by(user_id=user_id, time_range=time_range).all()
#         #     track_ids = [track.id for track in tracks]
#         #     features = AudioFeatures.query.filter(AudioFeatures.track_id.in_(track_ids)).all()
#         #
#         #     # If we have real data, use it instead of the placeholders
#         #     if tracks and features:
#         #         # You can uncomment and implement this when ready
#         #         # analyzer = MoodAnalyzer(tracks, features)
#         #         # mood_data = analyzer.analyze_moods()
#         #         # personality_data = analyzer.determine_personality()
#         #         pass
#         # except Exception as e:
#         #     print(f"Error retrieving track data: {e}")
#         #     # Continue with default data
#
#         return render_template(
#             'visualise.html',
#             user="user", #todo: implement this in frontend
#             mood_data=mood_data,
#             personality_data=personality_data, #todo: implement this in frontend
#             time_range=time_range
#         )
#
#     @app.route('/api/mood-data')
#     def api_mood_data():
#         """API endpoint to get mood data."""
#         if 'user_id' not in session:
#             return jsonify({'error': 'Not authenticated'}), 401
#
#         time_range = request.args.get('time_range', 'medium_term')
#         user_id = session['user_id']
#
#         # Get tracks and features
#         tracks = Track.query.filter_by(user_id=user_id, time_range=time_range).all()
#         track_ids = [track.id for track in tracks]
#         features = AudioFeatures.query.filter(AudioFeatures.track_id.in_(track_ids)).all()
#
#         # Use the mood analyzer
#         # analyzer = MoodAnalyzer(tracks, features)
#         # mood_data = analyzer.analyze_moods()
#         #
#         # return jsonify(mood_data)
#
#     # ----------------------------------------------------------
#     # Friends Routes
#     # ----------------------------------------------------------
#     @app.route('/friends')
#     def friends():
#         """View friends list and manage friend requests"""
#         if 'user_id' not in session:
#             flash('Please log in to view your friends.', 'warning')
#             return redirect(url_for('login'))
#
#         user_id = session['user_id']
#
#         # Get accepted friends
#         friends_sent = Friend.query.filter_by(user_id=user_id, status='accepted').all()
#         friends_received = Friend.query.filter_by(friend_id=user_id, status='accepted').all()
#
#         # Get pending requests
#         pending_requests = Friend.query.filter_by(friend_id=user_id, status='pending').all()
#
#         # Combine friends from both directions
#         friends_list = []
#         for f in friends_sent:
#             friend_user = User.query.get(f.friend_id)
#             if friend_user:
#                 friends_list.append({
#                     'id': friend_user.id,
#                     'name': friend_user.display_name or f"{friend_user.first_name} {friend_user.last_name}".strip(),
#                     'share_data': f.share_data
#                 })
#
#         for f in friends_received:
#             friend_user = User.query.get(f.user_id)
#             if friend_user:
#                 friends_list.append({
#                     'id': friend_user.id,
#                     'name': friend_user.display_name or f"{friend_user.first_name} {friend_user.last_name}".strip(),
#                     'share_data': f.share_data
#                 })
#
#         # Process pending requests
#         pending_list = []
#         for req in pending_requests:
#             requester = User.query.get(req.user_id)
#             if requester:
#                 pending_list.append({
#                     'id': req.id,
#                     'user_id': requester.id,
#                     'name': requester.display_name or f"{requester.first_name} {requester.last_name}".strip()
#                 })
#
#         return render_template('friends.html',
#                                friends=friends_list,
#                                pending_requests=pending_list)
#
#     @app.route('/friends/search', methods=['GET', 'POST'])
#     def search_friends():
#         """Search for users to add as friends"""
#         if 'user_id' not in session:
#             flash('Please log in to search for friends.', 'warning')
#             return redirect(url_for('login'))
#
#         user_id = session['user_id']
#         query = request.args.get('query', '')
#
#         if not query:
#             return render_template('friend_search.html', results=[], query='')
#
#         # Search for users by name or email
#         results = User.query.filter(
#             User.id != user_id,
#             db.or_(
#                 User.display_name.ilike(f'%{query}%'),
#                 User.first_name.ilike(f'%{query}%'),
#                 User.last_name.ilike(f'%{query}%'),
#                 User.email.ilike(f'%{query}%')
#             )
#         ).all()
#
#         # Check existing friendship status
#         processed_results = []
#         for user in results:
#             # Check if already friends or request pending
#             friendship_sent = Friend.query.filter_by(user_id=user_id, friend_id=user.id).first()
#             friendship_received = Friend.query.filter_by(user_id=user.id, friend_id=user_id).first()
#
#             status = 'none'
#             if friendship_sent:
#                 status = friendship_sent.status
#             elif friendship_received:
#                 status = friendship_received.status
#
#             processed_results.append({
#                 'id': user.id,
#                 'name': user.display_name or f"{user.first_name} {user.last_name}".strip(),
#                 'email': user.email,
#                 'status': status
#             })
#
#         return render_template('friend_search.html', results=processed_results, query=query)
#
#     @app.route('/friends/add', methods=['POST'])
#     def add_friend():
#         """Send a friend request"""
#         if 'user_id' not in session:
#             return jsonify({'error': 'Not authenticated'}), 401
#
#         user_id = session['user_id']
#         friend_id = request.form.get('friend_id')
#
#         if not friend_id:
#             flash('Invalid friend request.', 'danger')
#             return redirect(url_for('friends'))
#
#         if user_id == friend_id:
#             flash('You cannot add yourself as a friend.', 'warning')
#             return redirect(url_for('friends'))
#
#         # Check if friend request already exists
#         existing = Friend.query.filter_by(user_id=user_id, friend_id=friend_id).first()
#         if existing:
#             flash('Friend request already sent.', 'info')
#             return redirect(url_for('friends'))
#
#         # Check if they sent you a request first
#         existing = Friend.query.filter_by(user_id=friend_id, friend_id=user_id).first()
#         if existing:
#             if existing.status == 'pending':
#                 # Auto-accept if they sent you a request
#                 existing.status = 'accepted'
#                 db.session.commit()
#                 flash('Friend request accepted!', 'success')
#                 return redirect(url_for('friends'))
#
#         # Create new friend request
#         new_request = Friend(user_id=user_id, friend_id=friend_id, status='pending')
#         db.session.add(new_request)
#         db.session.commit()
#
#         flash('Friend request sent!', 'success')
#         return redirect(url_for('friends'))
#
#     @app.route('/friends/accept', methods=['POST'])
#     def accept_friend():
#         """Accept a friend request"""
#         if 'user_id' not in session:
#             return jsonify({'error': 'Not authenticated'}), 401
#
#         user_id = session['user_id']
#         request_id = request.form.get('request_id')
#
#         friend_request = Friend.query.filter_by(id=request_id, friend_id=user_id, status='pending').first()
#
#         if not friend_request:
#             flash('Friend request not found.', 'danger')
#             return redirect(url_for('friends'))
#
#         friend_request.status = 'accepted'
#         db.session.commit()
#
#         flash('Friend request accepted!', 'success')
#         return redirect(url_for('friends'))
#
#     @app.route('/friends/reject', methods=['POST'])
#     def reject_friend():
#         """Reject a friend request"""
#         if 'user_id' not in session:
#             return jsonify({'error': 'Not authenticated'}), 401
#
#         user_id = session['user_id']
#         request_id = request.form.get('request_id')
#
#         friend_request = Friend.query.filter_by(id=request_id, friend_id=user_id, status='pending').first()
#
#         if not friend_request:
#             flash('Friend request not found.', 'danger')
#             return redirect(url_for('friends'))
#
#         friend_request.status = 'rejected'
#         db.session.commit()
#
#         flash('Friend request rejected.', 'info')
#         return redirect(url_for('friends'))
#
#     @app.route('/friends/toggle-share', methods=['POST'])
#     def toggle_share():
#         """Toggle data sharing with a friend"""
#         if 'user_id' not in session:
#             return jsonify({'error': 'Not authenticated'}), 401
#
#         user_id = session['user_id']
#         friend_id = request.form.get('friend_id')
#
#         # Check both directions of friendship
#         friendship = Friend.query.filter_by(user_id=user_id, friend_id=friend_id, status='accepted').first()
#         if not friendship:
#             friendship = Friend.query.filter_by(user_id=friend_id, friend_id=user_id, status='accepted').first()
#
#         if not friendship:
#             return jsonify({'error': 'Friendship not found'}), 404
#
#         # Toggle share status
#         friendship.share_data = not friendship.share_data
#         db.session.commit()
#
#         return jsonify({'success': True, 'sharing': friendship.share_data})
#
#     @app.route('/friends/<friend_id>/visualise')
#     def friend_visualise(friend_id):
#         """View a friend's visualisation data"""
#         if 'user_id' not in session:
#             flash('Please log in first.', 'warning')
#             return redirect(url_for('login'))
#
#         user_id = session['user_id']
#
#         # Check if friends with sharing enabled
#         friendship1 = Friend.query.filter_by(user_id=user_id, friend_id=friend_id, status='accepted',
#                                              share_data=True).first()
#         friendship2 = Friend.query.filter_by(user_id=friend_id, friend_id=user_id, status='accepted',
#                                              share_data=True).first()
#
#         if not friendship1 and not friendship2:
#             flash('You do not have permission to view this data.', 'warning')
#             return redirect(url_for('friends'))
#
#         friend = User.query.get(friend_id)
#         if not friend:
#             flash('Friend not found.', 'danger')
#             return redirect(url_for('friends'))
#
#         # Get time range from query parameters (default to medium_term)
#         time_range = request.args.get('time_range', 'medium_term')
#
#         # Get friend's mood data - similar logic as in the visualise route
#         # Fetch all mood labels for this friend from the AudioFeatures table
#         all_features = AudioFeatures.query.join(Track, AudioFeatures.track_id == Track.id).filter(
#             Track.user_id == friend_id
#         ).all()
#
#         # Count how many times each mood appears
#         from collections import Counter
#         mood_counts = Counter(f.mood for f in all_features)
#         total = sum(mood_counts.values()) or 1  # avoid division by zero
#
#         # Build mood_data with percentage breakdown
#         mood_data = {}
#         for mood, count in mood_counts.items():
#             # Skip if mood is None
#             if not mood:
#                 continue
#
#             mood_data[mood.lower()] = {
#                 "percentage": round(100 * count / total),  # Convert to percentage
#                 "top_track": None,  # You can populate this if you have the data
#                 "recommended_tracks": []  # You can populate this if you have the data
#             }
#
#         # Generate or fetch personality data
#         personality_data = {
#             "mbti": "INTJ",  # This should be fetched from the database if available
#             "summary": "Strategic, independent, and insightful.",
#             "related_songs": []  # You can populate this if you have the data
#         }
#
#         # Pass friend's name to the template
#         friend_name = friend.display_name or f"{friend.first_name} {friend.last_name}".strip()
#
#         return render_template('visualise.html',
#                                first_name=friend_name,
#                                time_range=time_range,
#                                mood_data=mood_data,
#                                personality=personality_data,
#                                is_friend_view=True,
#                                friend_id=friend_id)
#
#     @app.route('/api/personality-data')
#     def api_personality_data():
#         """API endpoint to get personality data."""
#         if 'user_id' not in session:
#             return jsonify({'error': 'Not authenticated'}), 401
#
#         time_range = request.args.get('time_range', 'medium_term')
#         user_id = session['user_id']
#
#         # Get tracks and features
#         tracks = Track.query.filter_by(user_id=user_id, time_range=time_range).all()
#         track_ids = [track.id for track in tracks]
#         features = AudioFeatures.query.filter(AudioFeatures.track_id.in_(track_ids)).all()
#
#         # Use the mood analyzer
#         # analyzer = MoodAnalyzer(tracks, features)
#         # personality_data = analyzer.determine_personality()
#
#         # return jsonify(personality_data)
#
#     @app.route('/upload')
#     def upload():
#         """Render the upload page."""
#         return render_template('upload.html')
#
#     @app.route('/share')
#     def share():
#         """Render the share page."""
#         return render_template('share.html')
#
#     @app.route('/logout')
#     def logout():
#         """Log out the user by clearing the session."""
#         session.pop('user_id', None)
#         session.pop('state', None)
#         return redirect(url_for('index'))
#
#     return app
#
# def fetch_and_store_user_data(user_id, spotify_api):
#     from models import db
#     """
#     Fetch and store user's top tracks and audio features.
#
#     Args:
#         user_id: The user's ID
#         spotify_api: Instance of SpotifyAPI
#     """
#     user = User.query.get(user_id)
#
#     if not user:
#         return False
#
#     # Check if token is expired and refresh if needed
#     if user.token_expiry <= datetime.utcnow():
#         if not refresh_token(user, spotify_api):
#             return False
#
#     # Time ranges to fetch
#     time_ranges = ['short_term', 'medium_term', 'long_term']
#
#     for time_range in time_ranges:
#         # Fetch top tracks for this time range using Spotify API utility
#         tracks_data = spotify_api.get_top_tracks(user.access_token, time_range)
#
#         if not tracks_data:
#             continue
#
#         # Store track information
#         track_ids = []
#
#         for i, item in enumerate(tracks_data['items']):
#             existing_track = Track.query.filter_by(
#                 id=item['id'],
#                 user_id=user.id,
#                 time_range=time_range
#             ).first()
#
#             if existing_track:
#                 # if the track already exists, update its rank and popularity
#                 existing_track.rank = i + 1
#                 existing_track.popularity = item['popularity']
#                 existing_track.created_at = datetime.utcnow()
#             else:
#                 # if the track doesn't exist, create a new one
#                 track = Track(
#                     id=item['id'],
#                     user_id=user.id,
#                     name=item['name'],
#                     artist=item['artists'][0]['name'],
#                     album=item['album']['name'],
#                     album_image_url=item['album']['images'][0]['url'] if item['album']['images'] else None,
#                     popularity=item['popularity'],
#                     time_range=time_range,
#                     rank=i + 1
#                 )
#                 db.session.add(track)
#
#             track_ids.append(item['id'])
#
#         db.session.commit()
#
#         # # Previous code
#         # for i, item in enumerate(tracks_data['items']):
#         #     track = Track.query.filter_by(id=item['id'], user_id=user.id, time_range=time_range).first()
#
#         #     if not track:
#         #         track = Track(
#         #             id=item['id'],
#         #             user_id=user.id,
#         #             name=item['name'],
#         #             artist=item['artists'][0]['name'],
#         #             album=item['album']['name'],
#         #             album_image_url=item['album']['images'][0]['url'] if item['album']['images'] else None,
#         #             popularity=item['popularity'],
#         #             time_range=time_range,
#         #             rank=i + 1
#         #         )
#         #         db.session.add(track)
#         #     else:
#         #         track.rank = i + 1
#         #         track.popularity = item['popularity']
#         #         track.created_at = datetime.utcnow()
#
#         #     track_ids.append(item['id'])
#
#         # db.session.commit()
#
#         # Fetch audio features in batches
#         fetch_audio_features(track_ids, user.access_token)
#
#     return True
#
#
# #todo: put into helper file
# def fetch_audio_features(track_ids, access_token):
#     from models import db
#     """
#     Fetch audio features for a list of tracks.
#
#     Args:
#         track_ids: List of track IDs
#         access_token: Valid access token
#     """
#     # Process in batches of 100 (Spotify API limit)
#     for i in range(0, len(track_ids), 100):
#         batch_ids = track_ids[i:i + 100]
#         ids_param = ','.join(batch_ids)
#
#         headers = {
#             'Authorization': f'Bearer {access_token}'
#         }
#
#         # Direct API call for audio features (not in SpotifyAPI class yet)
#         import requests
#         features_response = requests.get(
#             f"https://api.spotify.com/v1/audio-features?ids={ids_param}",
#             headers=headers
#         )
#
#         if not features_response.ok:
#             continue
#
#         features_data = features_response.json()
#
#         for feature in features_data['audio_features']:
#             if not feature:
#                 continue
#
#             audio_feature = AudioFeatures.query.filter_by(id=feature['id']).first()
#
#
#             if not audio_feature:
#                 audio_feature = AudioFeatures(
#                     id=feature['id'],
#                     track_id=feature['id'],
#                     danceability=feature['danceability'],
#                     energy=feature['energy'],
#                     key=feature['key'],
#                     loudness=feature['loudness'],
#                     mode=feature['mode'],
#                     speechiness=feature['speechiness'],
#                     acousticness=feature['acousticness'],
#                     instrumentalness=feature['instrumentalness'],
#                     liveness=feature['liveness'],
#                     valence=feature['valence'],
#                     tempo=feature['tempo'],
#                     duration_ms=feature['duration_ms'],
#                     time_signature=feature['time_signature']
#                 )
#                 db.session.add(audio_feature)
#             else:
#                 # Update existing features
#                 audio_feature.danceability = feature['danceability']
#                 audio_feature.energy = feature['energy']
#                 audio_feature.key = feature['key']
#                 audio_feature.loudness = feature['loudness']
#                 audio_feature.mode = feature['mode']
#                 audio_feature.speechiness = feature['speechiness']
#                 audio_feature.acousticness = feature['acousticness']
#                 audio_feature.instrumentalness = feature['instrumentalness']
#                 audio_feature.liveness = feature['liveness']
#                 audio_feature.valence = feature['valence']
#                 audio_feature.tempo = feature['tempo']
#                 audio_feature.duration_ms = feature['duration_ms']
#                 audio_feature.time_signature = feature['time_signature']
#
#         db.session.commit()
#
#
# def refresh_token(user, spotify_api):
#     from models import db
#     """
#     Refresh access token using refresh token.
#
#     Args:
#         user: User object
#         spotify_api: SpotifyAPI instance
#
#     Returns:
#         bool: Success status
#     """
#     # This function would need to be added to the SpotifyAPI class
#     # For now, we'll implement it here
#     import requests
#     import base64
#
#     auth_string = f"{app.config['SPOTIFY_CLIENT_ID']}:{app.config['SPOTIFY_CLIENT_SECRET']}"
#     auth_bytes = auth_string.encode('utf-8')
#     auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')
#
#     headers = {
#         'Authorization': f'Basic {auth_base64}',
#         'Content-Type': 'application/x-www-form-urlencoded'
#     }
#
#     data = {
#         'grant_type': 'refresh_token',
#         'refresh_token': user.refresh_token
#     }
#
#     response = requests.post(app.config['TOKEN_URL'], headers=headers, data=data)
#
#     if not response.ok:
#         return False
#
#     token_data = response.json()
#
#     # Update user's access token and expiry
#     user.access_token = token_data['access_token']
#
#     # Refresh token is only provided if it has changed
#     if 'refresh_token' in token_data:
#         user.refresh_token = token_data['refresh_token']
#
#     user.token_expiry = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
#     db.session.commit()
#
#     return True
#
#
# # # Create a Flask application instance
# # app = create_app()
# #
# # # When running this file directly
# # if __name__ == '__main__':
# #     from models import db
# #     db.init_app(app)
# #     with app.app_context():
# #         db.create_all()
# #     app.run(debug=True)