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

    def search_track(self, track_name, artist_name, access_token):
        """
        Search for a track on Spotify by name and artist, and return its metadata.
        Useful for fetching album images for GPT-recommended songs.
        """
        import requests
        import urllib.parse

        query = f"track:{track_name} artist:{artist_name}"
        encoded_query = urllib.parse.quote(query)

        url = f"https://api.spotify.com/v1/search?q={encoded_query}&type=track&limit=1"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"[SpotifyAPI] Search failed: {response.status_code} – {response.text}")
            return None

        data = response.json()
        items = data.get("tracks", {}).get("items", [])
        if not items:
            return None

        # Return the first matching track
        return {
            "name": items[0]["name"],
            "artist": items[0]["artists"][0]["name"],
            "album": {
                "name": items[0]["album"]["name"],
                "images": items[0]["album"]["images"]  # contains URLs
            },
            "id": items[0]["id"]
        }

