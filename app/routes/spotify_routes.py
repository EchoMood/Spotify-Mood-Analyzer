# app/routes/spotify_routes.py

from flask import Blueprint, request, session, redirect, url_for, flash, render_template, current_app, jsonify
from datetime import datetime, timedelta
import uuid


from app import spotify_api
from app import gpt
from app.models import db, User, Track, AudioFeatures
from app.services.spotify_ingest import refresh_token, fetch_and_store_user_data, fetch_audio_features, enrich_recommended_tracks_with_album_art

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo

spotify_bp = Blueprint('spotify', __name__)

# ----------------------------------------------------------
# Spotify OAuth Login
# ----------------------------------------------------------
@spotify_bp.route('/oauth/spotify')
def oauth_spotify():
    # Generate a unique state parameter to prevent CSRF attacks
    state = str(uuid.uuid4())
    session['state'] = state
    
    # Define the scope of access you want to request
    # This example requests access to the user's top tracks, private data, recently played tracks, and email
    # You can adjust the scope based on your application's needs
    scope = 'user-top-read user-read-private user-read-recently-played user-read-email playlist-read-private'
    
    # Generate the authorization URL
    auth_url = spotify_api.get_auth_url(state, scope)
    
    return redirect(auth_url)
@spotify_bp.route('/ajax/spotify-logo')
def ajax_spotify_logo():
    # Return the Spotify logo URL as JSON
    return jsonify({
        'logo_url': 'https://storage.googleapis.com/pr-newsroom-wp/1/2023/05/Spotify_Primary_Logo_RGB_Green.png',
        'timestamp': datetime.utcnow().isoformat()
    })

# ----------------------------------------------------------
# Spotify OAuth Callback
# ----------------------------------------------------------
@spotify_bp.route('/callback')
def callback():
    # Verify state to prevent CSRF attacks
    print("State from request:", request.args.get('state'))
    if request.args.get('state') != session.get('state'):
        flash('Authentication error. Please try again.', 'danger')
        return redirect(url_for('user.index'))
    print("State verified successfully.")

    # Check for error in the callback
    if request.args.get('error'):
        flash('Authentication was denied.', 'warning')
        return redirect(url_for('user.index'))
    print("No error in callback.")
    
    # Check if the code is present in the callback
    code = request.args.get('code')
    if not code:
        flash('Authentication error. Please try again.', 'danger')
        return redirect(url_for('user.index'))
    print("Code received:", code)
    
    # Exchange the code for an access token
    # This is where you would typically make a request to Spotify's token endpoint
    # to exchange the code for an access token
    token_data = spotify_api.get_access_token(code)
    print("Token data received:", token_data)
    # Check if the token data is valid
    if not token_data:
        flash('Failed to authenticate with Spotify.', 'danger')
        return redirect(url_for('user.index'))

    # Extract the access token and other relevant data from the response
    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']
    expires_in = token_data['expires_in']
    token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
    session['access_token'] = access_token

    # Get user profile data
    user_data = spotify_api.get_user_profile(access_token)

    # Check if user data is valid
    if user_data is None:
            # Failed to get user data from Spotify
            flash('Failed to retrieve user information from Spotify. Please try again.', 'danger')
            return redirect(url_for('user.index'))

    linking = session.pop('linking', False)
    if linking and 'user_id' in session:
        existing_user = User.query.get(session['user_id'])
        if existing_user:
            existing_user.access_token = access_token
            existing_user.refresh_token = refresh_token
            existing_user.token_expiry = token_expiry
            existing_user.spotify_id = user_data['id']
            db.session.commit()
            flash('Spotify account linked successfully!', 'success')
            return redirect(url_for('user.dashboard'))

    if not user_data:
        flash('Failed to retrieve user information.', 'danger')
        return redirect(url_for('user.index'))
    

    # STEP: Check if the Spotify email matches a local user
    if 'email' in user_data and user_data['email']:
        existing_local_user = User.query.filter_by(email=user_data['email']).first()

        if existing_local_user and existing_local_user.id.startswith("local_"):
            print(f"🎯 Overwriting local user ID {existing_local_user.id} with Spotify ID {user_data['id']}")

            old_id = existing_local_user.id
            existing_local_user.id = user_data['id']
            existing_local_user.display_name = user_data.get('display_name', '')
            existing_local_user.first_name = user_data.get('display_name', '').split()[0] if user_data.get('display_name') else ''
            existing_local_user.access_token = access_token
            existing_local_user.refresh_token = refresh_token
            existing_local_user.token_expiry = token_expiry
            existing_local_user.last_login = datetime.utcnow()

            # Migrate foreign keys (e.g. Track, AudioFeatures)
            Track.query.filter_by(user_id=old_id).update({'user_id': user_data['id']})
            db.session.commit()

            session['user_id'] = user_data['id']
            session['user_email'] = existing_local_user.email
            session['first_name'] = existing_local_user.first_name

            # Fetch mood data and ChatGPT summary
            mood_counts = fetch_and_store_user_data(existing_local_user.id, spotify_api, gpt)
            session['mood_counts'] = mood_counts

            tracks = Track.query.filter_by(user_id=existing_local_user.id).all()

            gpt_input = []
            for track in tracks:
                gpt_input.append({
                    "name": track.name,
                    "artist": track.artist,
                    "album": track.album,
                    "genre": track.genre or "Unknown",
                    "mood": track.mood or "Unknown"
                })

            # 🧠 Generate mood summary
            mood_summary = gpt.analyze_user_tracks(gpt_input)
            session['mood_summary'] = mood_summary

            # 💬 Generate GPT-based mood-based song recommendations
            gpt_recs_by_mood = gpt.recommend_tracks_by_mood(gpt_input)

            # 🧬 Infer MBTI type (e.g., "INTJ")
            session['mbti_type'] = gpt.infer_mbti_type(gpt_input)

            # 🧠 Generate one-line personality summary
            session['mbti_summary'] = gpt.infer_mbti_summary(gpt_input)

            # 🎨 Generate MBTI + mood-based personality image
            dominant_mood = max(mood_counts, key=mood_counts.get, default="Chill")
            personality_image_url = gpt.generate_personality_image_url(session['mbti_type'], dominant_mood)
            session['personality_image_url'] = personality_image_url
            
            # ⏰ NEW: Infer mood-wise usual time of day
            mood_time_ranges = gpt.infer_mood_time_ranges(gpt_input)
            session['mood_time_ranges'] = mood_time_ranges

            # 🎵 Enrich GPT recommendations with album art
            recommended_tracks = enrich_recommended_tracks_with_album_art(gpt_recs_by_mood, access_token, spotify_api)
            session['recommended_tracks_by_mood'] = recommended_tracks

            return redirect(url_for('visual.visualise'))
    
    
    # save user data to the database
    user = User.query.filter_by(id=user_data['id']).first()
    if not user and user_data.get('email'):
        user = User.query.filter_by(email=user_data['email']).first()

    if user:
        # Update existing user
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.token_expiry = token_expiry
        if not user.id.startswith('spotify:'):
            user.spotify_id = user_data['id']
        user.last_login = datetime.utcnow()
        # If existing user logged in through Spotify but didn't have an email yet
        if not user.email and 'email' in user_data:
            user.email = user_data.get('email')
    else:
        # Check if email is retrieved from Spotify
        if not user_data.get('email'):
            # Check if user already exists using Spotify user ID
            existing_user = User.query.filter_by(id=user_data['id']).first()
            if existing_user:
                # Log the user in instead of asking to complete signup
                existing_user.access_token = access_token
                existing_user.refresh_token = refresh_token
                existing_user.token_expiry = token_expiry
                existing_user.last_login = datetime.utcnow()
                db.session.commit()

                # Store user info in session
                session['user_id'] = existing_user.id
                session['user_email'] = existing_user.email or ''
                session['first_name'] = existing_user.first_name or existing_user.display_name.split()[0]

                # Fetch mood data again
                mood_counts = fetch_and_store_user_data(existing_user.id, spotify_api, gpt)
                session['mood_counts'] = mood_counts
                
                # NEW: Generate ChatGPT mood summary based on updated DB

                # Fetch tracks and audio features from DB
                tracks = Track.query.filter_by(user_id=user.id).all()

                # Prepare track data for GPT
                gpt_input = []
                for track in tracks:
                    gpt_input.append({
                        "name": track.name,
                        "artist": track.artist,
                        "album": track.album,
                        "genre": track.genre or "Unknown",
                        "mood": track.mood or "Unknown"
                    })

                # 🧠 Generate mood summary
                mood_summary = gpt.analyze_user_tracks(gpt_input)
                session['mood_summary'] = mood_summary

                # 💬 Generate GPT-based mood-based song recommendations
                gpt_recs_by_mood = gpt.recommend_tracks_by_mood(gpt_input)

                # 🧬 Infer MBTI type (e.g., "INTJ")
                session['mbti_type'] = gpt.infer_mbti_type(gpt_input)

                # 🧠 Generate one-line personality summary
                session['mbti_summary'] = gpt.infer_mbti_summary(gpt_input)

                # 🎨 Generate MBTI + mood-based personality image
                dominant_mood = max(mood_counts, key=mood_counts.get, default="Chill")
                personality_image_url = gpt.generate_personality_image_url(session['mbti_type'], dominant_mood)
                session['personality_image_url'] = personality_image_url
                
                # ⏰ NEW: Infer mood-wise usual time of day
                mood_time_ranges = gpt.infer_mood_time_ranges(gpt_input)
                session['mood_time_ranges'] = mood_time_ranges

                # 🎵 Enrich GPT recommendations with album art
                recommended_tracks = enrich_recommended_tracks_with_album_art(gpt_recs_by_mood, access_token, spotify_api)
                session['recommended_tracks_by_mood'] = recommended_tracks

                return redirect(url_for('visual.visualise'))
                
            else:    
                session['spotify_user_id'] = user_data['id']
                session['display_name'] = user_data.get('display_name', '')
                session['access_token'] = access_token
                session['refresh_token'] = refresh_token
                session['token_expiry'] = token_expiry.isoformat()
                session['spotify_login_pending'] = True
                flash("We couldn't retrieve your email from Spotify. Please complete your signup.", 'warning')
                return redirect(url_for('user.signup_login_credentials'))

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

    session['user_id'] = user.id
    session['user_email'] = user.email
    if user.first_name:
        session['first_name'] = user.first_name
    else:
        session['first_name'] = user.display_name.split()[0] if user.display_name else 'User'

    try:
        mood_counts = fetch_and_store_user_data(user.id, spotify_api, gpt)
        print("✅ Imported Spotify data for user", user.id)
        print("🎵 Mood breakdown:", mood_counts)
        session['mood_counts'] = mood_counts

        # Fetch tracks and audio features from DB
        tracks = Track.query.filter_by(user_id=user.id).all()

        # Prepare track data for GPT
        gpt_input = []
        for track in tracks:
            gpt_input.append({
                "name": track.name,
                "artist": track.artist,
                "album": track.album,
                "genre": track.genre or "Unknown",
                "mood": track.mood or "Unknown"
            })

        # 🧠 Generate mood summary
        mood_summary = gpt.analyze_user_tracks(gpt_input)
        session['mood_summary'] = mood_summary

        # 💬 Generate GPT-based mood-based song recommendations
        gpt_recs_by_mood = gpt.recommend_tracks_by_mood(gpt_input)

        # 🧬 Infer MBTI type (e.g., "INTJ")
        session['mbti_type'] = gpt.infer_mbti_type(gpt_input)

        # 🧠 Generate one-line personality summary
        session['mbti_summary'] = gpt.infer_mbti_summary(gpt_input)

        # 🎨 Generate MBTI + mood-based personality image
        dominant_mood = max(mood_counts, key=mood_counts.get, default="Chill")
        personality_image_url = gpt.generate_personality_image_url(session['mbti_type'], dominant_mood)
        session['personality_image_url'] = personality_image_url
        
        # ⏰ NEW: Infer mood-wise usual time of day
        mood_time_ranges = gpt.infer_mood_time_ranges(gpt_input)
        session['mood_time_ranges'] = mood_time_ranges
        
        # 🎵 Enrich GPT recommendations with album art
        recommended_tracks = enrich_recommended_tracks_with_album_art(gpt_recs_by_mood, access_token, spotify_api)
        session['recommended_tracks_by_mood'] = recommended_tracks

    except Exception as e:
        print("❌ Error while importing Spotify data:", str(e))


    if user.registration_method == 'spotify' and not user.password:
        flash('Please complete your account setup by setting a password.', 'info')
        return redirect(url_for('spotify.complete_account'))

    return redirect(url_for('visual.visualise'))


@spotify_bp.route('/complete_account', methods=['GET', 'POST'])
def complete_account():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('user.login'))

    if user.password:
        return redirect(url_for('visual.visualise'))

    class CompleteAccountForm(FlaskForm):
        password = PasswordField('Password', validators=[DataRequired()])
        confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
        submit = SubmitField('Complete Account')

    form = CompleteAccountForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Account setup completed!', 'success')
        return redirect(url_for('visual.visualise'))

    return render_template('complete_account.html', form=form, user=user)


@spotify_bp.route('/link/spotify')
def link_spotify():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    state = str(uuid.uuid4())
    session['state'] = state
    session['linking'] = True
    auth_url = spotify_api.get_auth_url(state)
    return redirect(auth_url)


@spotify_bp.route('/unlink/spotify', methods=['POST'])
def unlink_spotify():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('user.login'))

    user.access_token = None
    user.refresh_token = None
    user.token_expiry = None
    db.session.commit()

    flash('Spotify account unlinked successfully.', 'success')
    return redirect(url_for('user.dashboard'))
