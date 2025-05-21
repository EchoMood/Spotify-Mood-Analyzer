# app/routes/visualisation_routes.py

from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from collections import Counter, defaultdict

from app.models import User, Track, AudioFeatures

visual_bp = Blueprint('visual', __name__)


@visual_bp.route('/visualise')
def visualise():
    print("Access Token from session:", session.get('access_token'))

    # # Ensure user is logged in
    # if 'user_id' not in session:
    #     flash('Please log in to view your visualisation.', 'warning')
    #     return redirect(url_for('user.login'))
    #
    # user_id = session['user_id']
    # user = User.query.get(user_id)
    #
    # if not user:
    #     flash('User not found. Please log in again.', 'warning')
    #     session.clear()
    #     return redirect(url_for('user.login'))

    # Get selected time range (default to medium_term)
    time_range = request.args.get('time_range', 'medium_term')

    # Get mood count data from session (used for pie chart or % breakdowns)
    mood_counts = session.get('mood_counts', {})
    print("🔍 mood_counts:", mood_counts)

    total = sum(mood_counts.values()) or 1  # avoid division by zero

    # Define mood time ranges
    mood_time_ranges = session.get('mood_time_ranges', {})

    # # Fetch user's tracks from DB
    # tracks = Track.query.filter_by(user_id=user_id, time_range=time_range).all()
    tracks = Track.query.all()

    # Organize tracks by mood
    grouped_tracks = defaultdict(list)
    for track in tracks:
        if track.mood:
            grouped_tracks[track.mood.lower()].append(track)

    # Aggregate genre data - FIX: This should be outside the track loop
    genre_counts = Counter()
    for track in tracks:
        if track.genre and track.genre != "Unknown":
            genre_counts[track.genre] += 1

    # Get top genres (limit to top 8 for chart readability)
    top_genres = dict(genre_counts.most_common(8))

    # If there are other genres beyond the top 8, group them as "Other"
    if len(genre_counts) > 8:
        other_count = sum(count for genre, count in genre_counts.most_common()[8:])
        if other_count > 0:
            top_genres["Other"] = other_count

    # Build mood data dictionary
    mood_data = {}
    for mood, count in mood_counts.items():
        mood_key = mood.lower()
        mood_tracks = grouped_tracks.get(mood_key, [])
        mood_tracks_sorted = sorted(mood_tracks, key=lambda x: (-x.popularity, x.rank or 9999))

        top_track = mood_tracks_sorted[0] if mood_tracks_sorted else None
        mood_data[mood_key] = {
            "percentage": round(100 * count / total),
            "top_track": {
                "name": top_track.name if top_track else "Top Song",
                "artist": top_track.artist if top_track else "Top Artist",
                "image": top_track.album_image_url or url_for('static',
                                                              filename='images/sample-album.jpg') if top_track else url_for(
                    'static', filename='images/sample-album.jpg')
            } if top_track else None,
            "recommended_tracks": [],  # will be filled using session below
            "time_range": mood_time_ranges.get(mood.capitalize(), "Night (8pm–11pm)")  # ⏰ AI-enhanced
        }

    # Load GPT-recommended songs
    recommended_songs = session.get('recommended_tracks_by_mood', {})
    for mood in mood_data:
        mood_data[mood]["recommended_tracks"] = recommended_songs.get(mood.capitalize(), [])

    # Mood/personality summary
    mood_summary = session.get('mood_summary', "Sorry we couldn't retrieve your mood summary :(")

    # Get top 6 tracks based on popularity (and then rank)
    top_6_tracks = sorted(tracks, key=lambda x: (-x.popularity, x.rank or 9999))[:6]
    related_songs = [
        {
            "name": t.name,
            "artist": t.artist,
            "image": t.album_image_url or url_for('static', filename='images/sample-album.jpg')
        }
        for t in top_6_tracks
    ]

    # Pull MBTI and summary directly from session
    personality_data = {
        "mbti": session.get("mbti_type", "INTJ"),
        "summary": session.get("mbti_summary", "..."),
        "image": session.get("personality_image_url", url_for('static', filename='images/virtual-pet.png')),
        "related_songs": related_songs
    }

    return render_template(
        'visualise.html',
        first_name=session.get('first_name', 'User'),
        time_range=time_range,
        mood_data=mood_data,
        personality=personality_data,
        mood_summary=mood_summary,
        mood_counts=mood_counts,
        recommended_songs=recommended_songs,
        genre_data=top_genres  # Fix: Pass the correct variable
    )


@visual_bp.route('/api/mood-data')
def mood_data_api():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    time_range = request.args.get('time_range', 'medium_term')
    user_id = session['user_id']

    # TODO: Add logic here if needed to compute mood_data from DB
    mood_data = {}

    return jsonify(mood_data)
