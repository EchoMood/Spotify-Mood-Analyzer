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
        Accepts a list of dictionaries containing track metadata (name, artist, album, genre, mood).
        Returns a ChatGPT-generated mood and personality summary based on the user's music taste.
        """

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a music psychologist assistant. "
                    "Given a list of songs, each with name, artist, album, genre, and mood, "
                    "analyze the overall mood and personality of the user. "
                    "Be expressive and insightful in your summary. "
                    "Do not list individual tracks. Focus on patterns and emotional themes."
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
        
    def recommend_tracks_by_mood(self, tracks):
        """
        Accepts a list of tracks with name, artist, genre, and mood.
        Asks GPT to generate 3 recommended songs per mood category.
        
        Returns:
            dict: { "Happy": [{"name": ..., "artist": ...}, ...], ... }
        """

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a music recommendation assistant. "
                    "Based on the user's listening history, recommend 3 different songs for each unique mood present in the data. "
                    "Use the existing mood categories: Happy, Sad, Angry, Chill, Focused. "
                    "Do NOT include duplicates from the user's history. "
                    "Format the response as a JSON dictionary mapping moods to a list of 3 song recommendations. "
                    "Each recommended song should have a 'name' and 'artist' field. "
                    "Only include mood categories that appear in the user's data."
                )
            },
            {
                "role": "user",
                "content": f"Here are the user's recent songs:\n{tracks}\n\nPlease recommend songs accordingly."
            }
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.75
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.ok:
                raw = response.json()["choices"][0]["message"]["content"]
                import json
                # Try parsing raw JSON block from response
                recommendations = json.loads(raw)
                return recommendations
            else:
                raise RuntimeError(f"OpenAI recommendation error {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[ERROR] Mood recommendation failed: {e}")
            return {}
        
    def infer_mbti_type(self, tracks):
        """
        Infers the MBTI (Myers-Briggs Type Indicator) personality type based on a user's music listening history.

        This method uses the OpenAI ChatGPT model to analyze the user's track-level data, including
        song name, artist, genre, and mood, and returns the inferred MBTI type.

        Parameters:
            tracks (list of dict): A list of dictionaries where each dictionary represents a track and includes:
                - name (str): Track name
                - artist (str): Artist name
                - album (str): Album name
                - genre (str): Genre label
                - mood (str): Mood label

        Returns:
            str: The inferred MBTI type (e.g., "INFP", "ENTJ", etc.). Falls back to "INTJ" on failure.
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a music personality analyst. Based on a list of songs with artist, genre, and mood, "
                    "infer only the MBTI personality type of the user. Do not explain or provide anything else."
                )
            },
            {
                "role": "user",
                "content": f"Here is the user's listening data:\n{tracks}\n\nWhat is their MBTI type?"
            }
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.ok:
                result = response.json()["choices"][0]["message"]["content"].strip()
                return result if result else "INTJ"
        except Exception as e:
            print(f"[GPT ERROR] MBTI type inference failed: {e}")

        return "INTJ"  # default fallback
    
    
    def infer_mbti_summary(self, tracks):
        """
        Infers a very concise one-line MBTI-based music personality summary 
        (max 5 words) based on the user's music listening data.

        Parameters:
            tracks (list): A list of track dictionaries with name, artist, genre, and mood.

        Returns:
            str: A single short summary string (e.g., "Calm and introspective listener")
        """
        # Define prompt with strict length requirement
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a music psychologist. Given a list of songs with metadata, "
                    "summarize the user's musical personality in a maximum of **5 words only**. "
                    "Avoid punctuation or extra explanation. Respond only with the summary."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Here is the user's music data:\n{tracks}\n\n"
                    "Please give a 5-word (or fewer) summary of their music personality."
                )
            }
        ]

        # Request payload
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.6
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.ok:
                return response.json()["choices"][0]["message"]["content"].strip()
            raise RuntimeError(f"GPT MBTI summary failed: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"[GPT ERROR] MBTI summary failed: {e}")
            return "Calm and introspective listener"
            

    def generate_personality_image_url(self, mbti, mood):
        """
        Generates an AI-powered image representing the user's personality, based on MBTI type and mood.

        Parameters:
            mbti (str): MBTI personality type (e.g., ENTP, ISFP).
            mood (str): Dominant mood inferred from the user's music history.

        Returns:
            str: URL to the DALL·E-generated image, or None if generation failed.
        """

        # Prompt DALL·E to create a fantasy portrait inspired by MBTI and emotional tone
        prompt = (
            f"A digital fantasy portrait of a person with MBTI type {mbti}, "
            f"visually inspired by the emotional tone of '{mood}' mood. "
            f"Portrait style, soft lighting, centered composition, aesthetic symbolism."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Call DALL·E 3 image generation endpoint
        try:
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers=headers,
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024"
                }
            )

            if response.ok:
                # Return the URL of the generated image
                return response.json()["data"][0]["url"]

            # Raise exception if image generation failed
            raise RuntimeError(f"DALL-E API error {response.status_code}: {response.text}")

        except Exception as e:
            print(f"[DALL·E ERROR] Image generation failed: {e}")
            return None
        
    def infer_mood_time_ranges(self, tracks):
        """
        Given a list of track metadata, return a mapping from mood to time of day
        (e.g., "Morning (6am–9am)", "Afternoon (12pm–4pm)", etc.).
        """
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a music mood and time-of-day analysis assistant. "
                    "Given a list of songs with associated moods, infer the time of day each mood is most commonly felt. "
                    "Return a JSON object mapping moods to a time window. Keep responses concise, e.g., "
                    '{"Chill": "Night (8pm–11pm)", "Happy": "Morning (9am–12pm)"}'
                )
            },
            {
                "role": "user",
                "content": f"Here is the user's track data:\n{tracks}"
            }
        ]

        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            if response.ok:
                import json
                return json.loads(response.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"[GPT ERROR] Time range inference failed: {e}")
            return {}