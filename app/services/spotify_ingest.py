# app/services/spotify_ingest.py

from collections import Counter
from datetime import datetime
from app.models import db, User, Track, AudioFeatures
from app.utils.spotify import SpotifyAPI
from sqlalchemy.exc import IntegrityError

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
            
            track_id = item['id']
            artist_id = item['artists'][0]['id']
            artist_ids.append(artist_id)

            try:
                existing_track = Track.query.filter_by(
                    id=track_id,
                    user_id=user.id,
                    time_range=time_range
                ).first()

                if existing_track:
                    existing_track.rank = i + 1
                    existing_track.popularity = item['popularity']
                    existing_track.created_at = datetime.utcnow()
                    print(f"✅ Updated track: {item['name']} ({track_id})")
                else:
                    new_track = Track(
                        id=track_id,
                        user_id=user.id,
                        name=item['name'],
                        artist=item['artists'][0]['name'],
                        album=item['album']['name'],
                        album_image_url=item['album']['images'][0]['url'] if item['album']['images'] else None,
                        popularity=item['popularity'],
                        time_range=time_range,
                        rank=i + 1,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(new_track)
                    print(f"➕ Added new track: {item['name']} ({track_id})")

                track_ids.append(track_id)

            except IntegrityError as e:
                db.session.rollback()
                print(f"⚠️ IntegrityError for track {track_id}: {str(e)}")
                continue

        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            print(f"❌ Commit failed: {str(e)}")


        # Fetch audio features in batches
        fetch_audio_features(track_ids, user.access_token, spotify_api)

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
# Fetch Audio Features Helper Function
# ----------------------------------------------------------
def fetch_audio_features(track_ids, access_token, spotify_api):
    print(f"[DEBUG] Fetching audio features for {len(track_ids)} tracks")
    # Use the unified SpotifyAPI class
    features_map = spotify_api.get_audio_features(access_token, track_ids)
    print(f"[DEBUG] Received features for {len(features_map)} tracks")

    for track_id in track_ids:
        features = features_map.get(track_id)

        if not features:
            continue
        
        # Check if it's a fallback feature due to 403
        if features.get("mood") == "Unavailable":
            print(f"⚠️ Skipping track {track_id}: Premium-only feature access.")
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