# app/services/spotify_ingest.py

from collections import Counter
from datetime import datetime
from app.models import db, User, Track, AudioFeatures
from app.utils.spotify import SpotifyAPI
from app.utils.chatgpt import ChatGPT
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

def refresh_token(user, spotify_api):
    import base64
    import requests

    if not user.refresh_token:
        print("❌ No refresh token available.")
        return False

    # Spotify token endpoint
    token_url = "https://accounts.spotify.com/api/token"

    auth_string = f"{spotify_api.client_id}:{spotify_api.client_secret}"
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

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code != 200:
        print("❌ Failed to refresh token:", response.text)
        return False

    token_data = response.json()
    user.access_token = token_data['access_token']

    if 'refresh_token' in token_data:
        user.refresh_token = token_data['refresh_token']
    from datetime import datetime, timedelta
    user.token_expiry = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))

    from app import db
    db.session.commit()
    print("✅ Refreshed Spotify token for user:", user.id)
    return True


# ----------------------------------------------------------
# Fetch and Store User's Spotify Data
# ----------------------------------------------------------
def fetch_and_store_user_data(user_id, spotify_api, gpt):
    """
    Fetches and stores Spotify data (tracks and audio features) for a given user,
    enriches each track with mood and ChatGPT-derived genre information,
    and stores it in the database.

    Parameters:
        user_id (str): Spotify user ID (same as primary key in User table).
        spotify_api (SpotifyAPI): Instance of SpotifyAPI wrapper for making Spotify requests.
        gpt (ChatGPT): Instance of ChatGPT class to call OpenAI API for genre classification.

    Returns:
        dict: A dictionary containing mood counts inferred from genres.
    """
    user = User.query.get(user_id)

    # 🔒 Validate user and access token
    if not user or not user.access_token:
        return False

    # 🔄 Refresh token if expired
    if user.token_expiry and user.token_expiry <= datetime.utcnow():
        if not refresh_token(user, spotify_api):
            return False

    time_range = 'short_term'
    mood_counts = Counter()

    # 🎧 Get user's top tracks for the time range
    tracks_data = spotify_api.get_top_tracks(user.access_token, time_range)
    if not tracks_data or 'items' not in tracks_data:
        print("❌ No track data returned from Spotify API")
        return mood_counts

    print(f"✅ Retrieved {len(tracks_data['items'])} tracks from Spotify")

    # Prepare for batch processing
    tracks_to_classify = []
    track_map = {}
    track_ids = []

    # First pass: collect data and identify tracks needing classification
    for i, item in enumerate(tracks_data['items']):
        track_id = item['id']
        artist_name = item['artists'][0]['name']
        track_name = item['name']
        album_name = item['album']['name']
        album_image = item['album']['images'][0]['url'] if item['album']['images'] else None
        popularity = item.get('popularity', 50)  # Default to 50 if not available

        # Store track info for later use
        track_map[track_name] = {
            'id': track_id,
            'artist': artist_name,
            'album': album_name,
            'image': album_image,
            'popularity': popularity,
            'rank': i + 1  # Use loop index + 1 for rank
        }

        # Check if track already exists
        existing_track = Track.query.filter_by(
            id=track_id,
            user_id=user.id,
            time_range=time_range
        ).first()

        if existing_track and existing_track.genre and existing_track.mood:
            # Track exists with genre and mood, just update rank and popularity
            existing_track.rank = i + 1
            existing_track.popularity = popularity
            existing_track.created_at = datetime.utcnow()
            print(f"🔄 Updated existing track: {track_name}")
        else:
            # New track or missing genre/mood, add to classification list
            tracks_to_classify.append({
                'name': track_name,
                'artist': artist_name,
                'album': album_name
            })
            track_ids.append(track_id)

    # Commit updates to existing tracks
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error updating existing tracks: {str(e)}")

    # If we have tracks to classify
    if tracks_to_classify:
        try:
            # Batch classify genres
            print(f"🧠 Classifying genres for {len(tracks_to_classify)} tracks")
            genre_results = gpt.classify_genres_batch(tracks_to_classify)

            # Batch classify moods
            print(f"🧠 Classifying moods for {len(tracks_to_classify)} tracks")
            mood_results = gpt.classify_moods_batch(tracks_to_classify)

            # Add new tracks with classification results
            for track_data in tracks_to_classify:
                track_name = track_data['name']

                if track_name not in track_map:
                    print(f"⚠️ Track '{track_name}' not found in track map, skipping")
                    continue

                track_info = track_map[track_name]

                genre = genre_results.get(track_name, "Unknown")
                mood = mood_results.get(track_name, "Chill")  # Default to "Chill" if not classified

                # Check again if track exists (in case it was added in a different session)
                existing_track = Track.query.filter_by(
                    id=track_info['id'],
                    user_id=user.id,
                    time_range=time_range
                ).first()

                if existing_track:
                    # Update existing track
                    if not existing_track.genre:
                        existing_track.genre = genre
                    if not existing_track.mood:
                        existing_track.mood = mood
                    existing_track.rank = track_info['rank']
                    existing_track.popularity = track_info['popularity']
                    existing_track.created_at = datetime.utcnow()
                    print(f"🔄 Updated track with classifications: {track_name}")
                else:
                    # Create new track
                    new_track = Track(
                        id=track_info['id'],
                        user_id=user.id,
                        name=track_name,
                        artist=track_info['artist'],
                        album=track_info['album'],
                        album_image_url=track_info['image'],
                        popularity=track_info['popularity'],
                        time_range=time_range,
                        rank=track_info['rank'],
                        created_at=datetime.utcnow(),
                        genre=genre,
                        mood=mood
                    )
                    db.session.add(new_track)
                    print(f"➕ Added new track: {track_name}")

            # Commit all new tracks
            db.session.commit()
            print("✅ Successfully saved all track data")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during track classification and saving: {str(e)}")

    # Aggregate mood counts from Track table
    track_moods = (
        db.session.query(Track.mood, func.count(Track.mood))
        .filter(Track.user_id == user.id)
        .group_by(Track.mood)
        .all()
    )
    mood_counts = {mood: count for mood, count in track_moods if mood and mood != "Unavailable"}

    return mood_counts
# ----------------------------------------------------------
# Fetch Audio Features Helper Function
# ----------------------------------------------------------
def fetch_audio_features(track_ids, access_token, spotify_api):
    print(f"[DEBUG] Fetching audio features for {len(track_ids)} tracks")
    # Use the unified SpotifyAPI class
    #features_map = spotify_api.get_audio_features(access_token, track_ids)
    pass
    
def enrich_recommended_tracks_with_album_art(gpt_recs_by_mood, access_token, spotify_api):
    """
    Takes GPT-generated song recommendations (dict by mood),
    enriches them with album cover URLs using Spotify Search API.

    Args:
        gpt_recs_by_mood (dict): e.g. { "Happy": [{"name": "X", "artist": "Y"}, ...], ... }
        access_token (str): Spotify access token for searching.
        spotify_api (SpotifyAPI): Instance to make API calls.

    Returns:
        dict: Same structure but with album image included.
    """
    enriched = {}

    for mood, tracks in gpt_recs_by_mood.items():
        enriched[mood] = []
        for track in tracks:
            result = spotify_api.search_track(track['name'], track['artist'], access_token)
            if result:
                enriched[mood].append({
                    "name": result["name"],
                    "artist": result["artist"],
                    "image_url": result["album"]["images"][0]["url"] if result["album"]["images"] else None
                })

    return enriched