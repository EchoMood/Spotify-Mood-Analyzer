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

    time_ranges = ['short_term', 'medium_term', 'long_term']
    mood_counts = Counter()

    for time_range in time_ranges:
        # 🎧 Get user's top tracks for each time range
        tracks_data = spotify_api.get_top_tracks(user.access_token, time_range)
        if not tracks_data:
            continue

        track_ids = []

        for i, item in enumerate(tracks_data['items']):
            track_id = item['id']
            artist_name = item['artists'][0]['name']
            track_name = item['name']
            album_name = item['album']['name']

            # Check if track already exists for this user and time_range
            existing_track = Track.query.filter_by(
                id=track_id,
                user_id=user.id,
                time_range=time_range
            ).first()

            # Only call GPT if genre or mood is missing or marked Unavailable
            genre = existing_track.genre if existing_track and existing_track.genre else gpt.classify_genre(track_name, artist_name, album_name)
            if not existing_track or not existing_track.genre:
                print(f"[GPT] Genre for '{track_name}' by {artist_name}: {genre}")

            #features = spotify_api.get_audio_features(user.access_token, [track_id]).get(track_id, {})
            mood_input = f"{track_name} by {artist_name}" #with valence {features.get('valence')} and energy {features.get('energy')}"
            mood = existing_track.mood if existing_track and existing_track.mood and existing_track.mood != "Unavailable" else gpt.analyze_mood(mood_input)
            if not existing_track or not existing_track.mood or existing_track.mood == "Unavailable":
                print(f"[GPT] Mood for '{track_name}': {mood}")

            try:
                if existing_track:
                    # Update essential fields
                    existing_track.rank = i + 1
                    existing_track.popularity = item['popularity']
                    existing_track.created_at = datetime.utcnow()

                    if not existing_track.genre:
                        existing_track.genre = genre
                    if not existing_track.mood or existing_track.mood == "Unavailable":
                        existing_track.mood = mood

                    print(f"✅ Updated track: {track_name} ({track_id})")

                else:
                    # Add new track
                    new_track = Track(
                        id=track_id,
                        user_id=user.id,
                        name=track_name,
                        artist=artist_name,
                        album=album_name,
                        album_image_url=item['album']['images'][0]['url'] if item['album']['images'] else None,
                        popularity=item['popularity'],
                        time_range=time_range,
                        rank=i + 1,
                        created_at=datetime.utcnow(),
                        genre=genre,
                        mood=mood
                    )
                    db.session.add(new_track)
                    print(f"➕ Added new track: {track_name} ({track_id})")

                track_ids.append(track_id)

            except IntegrityError as e:
                db.session.rollback()
                print(f"⚠️ IntegrityError for track {track_id}: {str(e)}")

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            print(f"❌ Commit failed for time range {time_range}: {str(e)}")

        # Fetch and update audio features (optional but still useful)
        #fetch_audio_features(track_ids, user.access_token, spotify_api)

    # Aggregate mood counts from Track table (not AudioFeatures)
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