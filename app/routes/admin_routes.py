# app/routes/admin_routes.py

from flask import Blueprint, render_template, current_app
from app.models import db, User, Friend, Track, AudioFeatures

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# Add a temporary admin route (REMOVE BEFORE PRODUCTION)
@admin_bp.route('/admin/reset_user_password/<user_id>', methods=['POST'])
def admin_reset_password(user_id):
    if not current_app.debug:
        return "Not available in production", 403

    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    temp_password = "temporary123"  # Or generate a random one
    user.set_password(temp_password)
    db.session.commit()

    return f"Password reset to: {temp_password}"

@admin_bp.route('/inspect-db/<secret_token>', methods=['GET'])
def inspect_db(secret_token):
    if secret_token != current_app.config.get('SECRET_KEY', ''):
        print("key: ", current_app.config.get('SECRET_KEY', ''))
        return "Unauthorized", 401

    users = User.query.all()
    friends = Friend.query.all()

    # Get friendship details
    friendship_details = []
    for f in friends:
        user = User.query.get(f.user_id)
        friend = User.query.get(f.friend_id)
        friendship_details.append({
            'id': f.id,
            'user_name': user.display_name or f"{user.first_name} {user.last_name}".strip() if user else "Unknown",
            'user_id': f.user_id,
            'friend_name': friend.display_name or f"{friend.first_name} {friend.last_name}".strip() if friend else "Unknown",
            'friend_id': f.friend_id,
            'status': f.status,
            'share_data': f.share_data,
            'created_at': f.created_at
        })

    tracks_by_user = {}
    for user in users:
        user_tracks = Track.query.filter_by(user_id=user.id).all()
        if user_tracks:
            for track in user_tracks:
                track.features = AudioFeatures.query.filter_by(track_id=track.id).first()

            tracks_by_user[user.id] = {
                'user_name': user.display_name or f"{user.first_name} {user.last_name}".strip(),
                'tracks': user_tracks
            }

    stats = {
        'users': User.query.count(),
        'friends_pending': Friend.query.filter_by(status='pending').count(),
        'friends_accepted': Friend.query.filter_by(status='accepted').count(),
        'friends_rejected': Friend.query.filter_by(status='rejected').count(),
        'tracks': Track.query.count()
    }

    return render_template('admin_inspect.html',
                           users=users,
                           friends=friends,
                           friendship_details=friendship_details,
                           tracks_by_user=tracks_by_user,
                           stats=stats)
