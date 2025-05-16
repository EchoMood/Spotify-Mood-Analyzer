# app/routes/visualisation_routes.py

from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from collections import Counter

from app.models import User, Track, AudioFeatures

visual_bp = Blueprint('visual', __name__)

@visual_bp.route('/visualise')
def visualise():
    print("Access Token from session:", session.get('access_token'))

    # Ensure user is logged in
    if 'user_id' not in session:
        flash('Please log in to view your visualisation.', 'warning')
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    user = User.query.get(user_id)

    if not user:
        flash('User not found. Please log in again.', 'warning')
        session.clear()
        return redirect(url_for('user.login'))

    # Get selected time range (default to medium_term)
    time_range = request.args.get('time_range', 'medium_term')

    # Get mood count data from session (used for pie chart or % breakdowns)
    mood_counts = session.get('mood_counts', {})
    print("🔍 mood_counts:", mood_counts)

    total = sum(mood_counts.values()) or 1  # avoid division by zero

    # Create mood breakdown structure for rendering mood cards
    mood_data = {
        mood.lower(): {
            "percentage": round(100 * count / total),
            "top_track": None,             # Future enhancement: fetch top track by mood
            "recommended_tracks": []       # Future enhancement: fetch recs by mood
        }
        for mood, count in mood_counts.items()
    }

    # Simple fallback personality data (you can update this dynamically later)
    personality_data = {
        "mbti": "INTJ",
        "summary": "Strategic, independent, and insightful. You're a deep thinker who appreciates complex musical compositions and meaningful lyrics.",
        "related_songs": [
            {
                "name": "Lateralus",
                "artist": "Tool",
                "image": "https://i.scdn.co/image/ab67616d0000b2739b2c7c8dd5136c2fa101da20"
            }
        ]
    }

    # ChatGPT-generated mood & personality summary
    mood_summary = session.get('mood_summary', 'We couldn’t generate your mood summary at this time.')

    # Recommended songs by mood (future: filled using ChatGPT or your logic)
    recommended_songs = session.get('recommended_tracks_by_mood', {})

    return render_template(
        'visualise.html',
        first_name=session.get('first_name', 'User'),
        time_range=time_range,
        mood_data=mood_data,
        personality=personality_data,
        mood_summary=mood_summary,
        mood_counts=mood_counts,
        recommended_songs=recommended_songs
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
