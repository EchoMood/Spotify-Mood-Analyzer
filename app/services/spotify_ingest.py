# app/services/spotify_ingest.py

from collections import Counter
from datetime import datetime
from app.models import db, User, Track, AudioFeatures
from app.utils.spotify import SpotifyAPI

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


def fetch_and_store_user_data(user_id, spotify_api):
    user = User.query.get(user_id)
    if not user or not user.access_token:
        return False

    if user.token_expiry and user.token_expiry <= datetime.utcnow():
        if not refresh_token(user, spotify_api):
            return False

    time_ranges = ['short_term', 'medium_term', 'long_term']
    mood_counts = Counter()

    for time_range in time_ranges:
        tracks_data = spotify_api.get_top_tracks(user.access_token, time_range)
        if not tracks_data:
            continue

        track_ids = []
        artist_ids = []

        for i, item in enumerate(tracks_data['items']):
            existing_track = Track.query.filter_by(
                id=item['id'], user_id=user.id, time_range=time_range
            ).first()

            artist_id = item['artists'][0]['id']
            artist_ids.append(artist_id)

            if existing_track:
                existing_track.rank = i + 1
                existing_track.popularity = item['popularity']
                existing_track.created_at = datetime.utcnow()
            else:
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