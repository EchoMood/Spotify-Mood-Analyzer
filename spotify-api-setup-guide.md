# Spotify API Setup Guide

This guide will walk you through the process of setting up your Spotify API credentials and configuring your local development environment for the Spotify Mood Analysis project.

## 1. Creating a Spotify Developer Account

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Log in with your Spotify account (or create one if you don't have it)
3. Accept the Developer Terms of Service if prompted

## 2. Creating a Spotify App

1. Once logged in to the dashboard, click the **Create An App** button
2. Fill in the required information:
   - **App name**: Spotify Mood Analysis
   - **App description**: An application that analyzes mood based on Spotify listening habits
   - **Website**: You can leave this blank or put a placeholder URL
   - **Redirect URI**: (We'll set this up after configuring ngrok)
3. Check the Developer Terms of Service checkbox
4. Click **Create**

## 3. Getting Your Credentials

After creating your app, you'll be taken to your app's dashboard. Here you'll find:

1. **Client ID**: This is displayed prominently at the top of the page
2. **Client Secret**: Click "Show Client Secret" to reveal this value

Both of these values need to be added to your `.env` file:

```
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
```

## 4. Setting Up ngrok for Local Development

Spotify's OAuth requires a public URL for redirects, but we're developing locally. We'll use ngrok to create a temporary public URL that forwards to our local server.

### Installing ngrok

1. Go to [ngrok.com](https://ngrok.com/) and sign up for a free account
2. Download the appropriate version for your operating system
3. Extract the downloaded file to a location of your choice
4. Follow the setup instructions, including authenticating with your auth token:

```bash
./ngrok authtoken your_ngrok_auth_token
```

### Starting ngrok

1. Start your Flask application first (make sure it's running on port 5000):
```bash
flask run
```

2. In a new terminal window, start ngrok to create a tunnel to your local server:
```bash
./ngrok http 5000
```

3. Look for the forwarding URL in the ngrok output. It will look something like:
```
Forwarding https://a1b2c3d4e5.ngrok.io -> http://localhost:5000
```

4. Copy the HTTPS URL (e.g., `https://a1b2c3d4e5.ngrok.io`)

## 5. Configuring Redirect URIs

Now that you have your ngrok URL, you need to set it as the redirect URI in:

### A. Your Spotify App Dashboard

1. Go back to your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
2. Select your app
3. Click **Edit Settings**
4. Under **Redirect URIs**, add your ngrok URL followed by `/callback`:
   ```
   https://a1b2c3d4e5.ngrok.io/callback
   ```
5. Click **Save**

### B. Your .env File

Add the same redirect URI to your `.env` file:

```
SPOTIFY_REDIRECT_URI=https://a1b2c3d4e5.ngrok.io/callback
```

## 6. Testing the Authentication Flow

1. Make sure both your Flask application and ngrok are running
2. Navigate to your ngrok URL in a browser
3. Click "Get Started" to initiate the login process
4. You should be redirected to Spotify's login page
5. After logging in, you'll be asked to authorize your app
6. After authorization, you should be redirected back to your application

## Important Notes

1. **ngrok URL Changes**: Every time you restart ngrok, you'll get a new URL. When this happens, you'll need to:
   - Update the redirect URI in your Spotify Developer Dashboard
   - Update the `SPOTIFY_REDIRECT_URI` in your `.env` file

2. **Required Scopes**: Our application uses the following scopes, which are already configured in the code:
   - `user-read-private`: Access user profile information
   - `user-read-email`: Access user email
   - `user-top-read`: Access user's top artists and tracks
   - `user-read-recently-played`: Access user's recently played tracks
   - `playlist-read-private`: Access user's private playlists

3. **Session Management**: Make sure your Flask application has a secret key set for session management:
   ```
   SECRET_KEY=your_random_secret_key
   ```

## Troubleshooting

### "Invalid Redirect URI" Error

This error occurs when the redirect URI in your request doesn't match any of the redirect URIs you've registered in your Spotify Developer Dashboard.

1. Double-check that the URI in your `.env` file exactly matches what's in your Spotify Dashboard
2. Ensure ngrok is running and the URL is current
3. Check that the path (`/callback`) is included and spelled correctly

### "Invalid Client Secret" Error

1. Verify that you've copied the Client Secret correctly
2. Make sure there are no trailing spaces or line breaks

### No Redirect After Login

1. Check your Flask application logs for any errors
2. Verify that the `/callback` route is correctly implemented
3. Make sure your session configuration is working properly

## Next Steps

Once you've successfully tested the authentication flow, you can:

1. Explore the Spotify API response data
2. Debug and improve the API handler (`utils/spotify.py`)
3. Implement data analysis based on the retrieved Spotify data

If you encounter any issues that aren't covered in this guide, please check the [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api/) or reach out to the project lead.
