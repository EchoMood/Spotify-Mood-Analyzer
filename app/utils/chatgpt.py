# ----------------------------------------------------------
# chatgpt.py – GPT-based Mood Analysis Module
# ----------------------------------------------------------

import openai
import os
import requests

# ----------------------------------------------------------
# ChatGPT – GPT interface class for music mood inference
# ----------------------------------------------------------
class ChatGPT:
    def __init__(self, app=None):
        """
        Optional Flask app initialization. If provided, will extract
        OpenAI credentials from the app config object.
        """
        self.api_key = None
        self.api_url = None
        self.model = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """
        Extract API configuration values from the Flask app context.
        This mirrors the pattern used in other utility classes like SpotifyAPI.
        """
        self.api_key = app.config.get("OPENAI_API_KEY")
        self.api_url = app.config.get("OPENAI_API_URL")
        self.model = app.config.get("OPENAI_MODEL")

        # Validate configuration presence
        if not all([self.api_key, self.api_url, self.model]):
            raise RuntimeError("Missing OpenAI configuration in app config")

    def analyze_mood(self, tracks):
        """
        Accepts a list or string of track details (e.g., name, valence, energy),
        sends it to OpenAI, and returns a single-word mood label.
        """

        # Prepare message payload for OpenAI
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a music mood analysis assistant. "
                    "Given a list of tracks and their features, infer the overall mood. "
                    "Return only one mood label: Happy, Sad, Angry, Chill, or Focused."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Here is the track data:\n{tracks}\n\n"
                    "Based on this data, what is the overall mood?"
                )
            }
        ]

        # Format request body
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        # HTTP request headers with API key
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Send request to OpenAI API
        response = requests.post(self.api_url, headers=headers, json=data)

        # Check if request succeeded
        if response.ok:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        # Raise error if something went wrong
        raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text}")
    
    def analyze_user_tracks(self, tracks):
        """
        Accepts a list of dictionaries containing track info and audio features.
        Returns a ChatGPT-generated mood and personality summary based on the data.
        """

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a music psychologist assistant. "
                    "Given a list of songs with audio features like valence, energy, danceability, tempo, and mood, "
                    "generate a short mood and personality summary of the user's music taste. "
                    "Be insightful, emotionally expressive, and avoid listing the individual tracks."
                )
            },
            {
                "role": "user",
                "content": f"Here is the user's listening data:\n{tracks}"
            }
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.8
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(self.api_url, headers=headers, json=data)

        if response.ok:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

        raise RuntimeError(f"OpenAI API error {response.status_code}: {response.text}")
    
    def classify_genre(self, track_name, artist, album):
        """
        Get the genre of a track using ChatGPT based on track name, artist, and album.
        """
        prompt = (
            f"What is the most appropriate genre label for the song "
            f"'{track_name}' by '{artist}' from the album '{album}'? "
            "Reply with only one genre name, no extra explanation."
        )

        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.ok:
                return response.json()["choices"][0]["message"]["content"].strip()
            else:
                raise RuntimeError(f"OpenAI genre API error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[ERROR] Genre fetch failed: {e}")
            return None