"""
Utility functions for interacting with the Spotify API.
"""

import base64
import requests
from urllib.parse import urlencode


class SpotifyAPI:
    """
    Class to handle interactions with the Spotify API.
    """

    def __init__(self, app=None):
        """
        Initialize the Spotify API helper.

        Args:
            app: Flask application instance (optional)
        """
        self.client_id = None
        self.client_secret = None
        self.redirect_uri = None
        self.auth_url = None
        self.token_url = None
        self.api_base_url = None

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialize with a Flask application.

        Args:
            app: Flask application instance
        """
        self.client_id = app.config['SPOTIFY_CLIENT_ID']
        self.client_secret = app.config['SPOTIFY_CLIENT_SECRET']
        self.redirect_uri = app.config['REDIRECT_URI']
        self.auth_url = app.config['AUTH_URL']
        self.token_url = app.config['TOKEN_URL']
        self.api_base_url = app.config['API_BASE_URL']

    def get_auth_url(self, state, scope=None):
        """
        Generate the Spotify authorization URL.

        Args:
            state: Random state string for security
            scope: Permission scopes to request

        Returns:
            Authorization URL for Spotify login
        """
        if scope is None:
            scope = 'user-read-private user-read-email user-top-read'

        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': scope,
            'state': state
        }

        auth_url = f"{self.auth_url}?{urlencode(params)}"
        
        # ✅ Add this debug print
        print(f"🔍 Generated Spotify Auth URL: {auth_url}")
        return auth_url

    def get_access_token(self, code):
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Spotify callback

        Returns:
            Dictionary containing access token and other info
        """
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')

        headers = {
            'Authorization': f'Basic {auth_base64}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': self.redirect_uri
        }

        print("\n🔑 [DEBUG] Sending token request to Spotify:")
        print("🔸 client_id:", self.client_id)
        print("🔸 client_secret:",self.client_secret)
        print("🔸 redirect_uri:", self.redirect_uri)
        print("🔸 token_url:", self.token_url)
        print("🔸 code:", code[:10] + "..." if code else "None")  # mask long code
        print("🔸 headers:", headers)
        print("🔸 data:", data)

        try:
            response = requests.post(self.token_url, headers=headers, data=data)
            print("📡 Response status:", response.status_code)
            print("📡 Response body:", response.text)

            if response.status_code == 200:
                return response.json()
            else:
                print("❌ Failed to exchange code. Spotify error:", response.json())
                return None
        except Exception as e:
            print("🚨 Exception during token request:", str(e))
            return None

    def get_user_profile(self, access_token):
        """
        Get user profile information from Spotify.

        Args:
            access_token: Valid access token

        Returns:
            User profile information
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        print(f"{self.api_base_url}me", "headers= ", headers)

        response = requests.get(f"{self.api_base_url}me", headers=headers)
        if response.status_code == 200:
            print("DEBUG successful call to spotify apii, response= ", response.json())
            return response.json()
        else:
            print("DEBUG call was not successful")
            return None

    def get_top_tracks(self, access_token, time_range='medium_term', limit=50):
        """
        Get user's top tracks from Spotify.

        Args:
            access_token: Valid access token
            time_range: Time range (short_term, medium_term, or long_term)
            limit: Number of tracks to return (maximum 50)

        Returns:
            User's top tracks information
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        params = {
            'time_range': time_range,
            'limit': limit
        }

        response = requests.get(
            f"{self.api_base_url}me/top/tracks",
            headers=headers,
            params=params
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
        
    def get_audio_features(self, access_token, track_ids):
        """
        Retrieve audio features for a list of track IDs.

        Args:
            access_token (str): Valid Spotify access token.
            track_ids (list): List of Spotify track IDs.

        Returns:
            dict: Mapping of track ID to its audio features dictionary.
        """
        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        features_map = {}

        # Spotify allows up to 100 track IDs per request
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            ids_param = ",".join(batch)
            
            
            # Debugging output
            print(f"🔍 Fetching audio features for track IDs: {ids_param}")
            response = requests.get(
                f"{self.api_base_url}audio-features",
                headers=headers,
                params={'ids': ids_param}
            )

            if response.status_code == 200:
                data = response.json().get('audio_features', [])
                for item in data:
                    if item:
                        features_map[item['id']] = item
                        
            elif response.status_code == 403:
                print("Access to audio features denied. Likely due to Spotify Free account.")
                for tid in batch:
                    features_map[tid] = {
                        "mood": "Unavailable",
                        "note": "Upgrade to Spotify Premium to unlock full mood analysis."
                    }
            else:
                print("Failed to fetch audio features:", response.text)

        return features_map

    @staticmethod
    def analyze_mood_from_features(features):
        """
        Analyze mood from audio feature data.

        Args:
            features (dict): Audio features of a track.

        Returns:
            str: Estimated mood category.
        """
        if not features:
            return "Unknown"

        if features['valence'] > 0.7 and features['energy'] > 0.6:
            return "Happy"
        elif features['valence'] < 0.3 and features['acousticness'] > 0.5:
            return "Sad"
        elif features['danceability'] > 0.4 and features['energy'] < 0.4:
            return "Chill"
        elif features['energy'] > 0.8 and features['valence'] < 0.4:
            return "Angry"
        elif features['instrumentalness'] > 0.7 and features['speechiness'] < 0.2:
            return "Focused"
        else:
            return "Mixed"
        
    def get_artists_genres(self, access_token, artist_ids):
        """
        Get genres for a list of artist IDs.

        Returns:
            dict: {artist_id: [genres]}
        """
        headers = {'Authorization': f'Bearer {access_token}'}
        genres_map = {}

        for i in range(0, len(artist_ids), 50):
            batch = artist_ids[i:i + 50]
            response = requests.get(
                f"{self.api_base_url}artists",
                headers=headers,
                params={"ids": ",".join(batch)}
            )
            if response.status_code == 200:
                artists = response.json().get("artists", [])
                for artist in artists:
                    genres_map[artist['id']] = artist.get('genres', [])
            else:
                print("Failed to fetch artist genres:", response.text)

        return genres_map
