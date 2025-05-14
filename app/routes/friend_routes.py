# app/routes/friend_routes.py

from flask import Blueprint, render_template, redirect, request, flash, session, jsonify, url_for
from app.models import db, User, Friend, Track, AudioFeatures
from collections import Counter

friend_bp = Blueprint('friend', __name__)

@friend_bp.route('/friends')
def friends():
    if 'user_id' not in session:
        flash('Please log in to view your friends.', 'warning')
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    friends_sent = Friend.query.filter_by(user_id=user_id, status='accepted').all()
    friends_received = Friend.query.filter_by(friend_id=user_id, status='accepted').all()
    pending_requests = Friend.query.filter_by(friend_id=user_id, status='pending').all()

    friends_list = []
    for f in friends_sent + friends_received:
        friend_user = User.query.get(f.friend_id if f.user_id == user_id else f.user_id)
        if friend_user:
            friends_list.append({
                'id': friend_user.id,
                'name': friend_user.display_name or f"{friend_user.first_name} {friend_user.last_name}".strip(),
                'share_data': f.share_data
            })

    pending_list = []
    for req in pending_requests:
        requester = User.query.get(req.user_id)
        if requester:
            pending_list.append({
                'id': req.id,
                'user_id': requester.id,
                'name': requester.display_name or f"{requester.first_name} {requester.last_name}".strip()
            })

    return render_template('friends.html', friends=friends_list, pending_requests=pending_list)


@friend_bp.route('/friends/search', methods=['GET', 'POST'])
def search_friends():
    if 'user_id' not in session:
        flash('Please log in to search for friends.', 'warning')
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    query = request.args.get('query', '')

    if not query:
        return render_template('friend_search.html', results=[], query='')

    results = User.query.filter(
        User.id != user_id,
        db.or_(
            User.display_name.ilike(f'%{query}%'),
            User.first_name.ilike(f'%{query}%'),
            User.last_name.ilike(f'%{query}%'),
            User.email.ilike(f'%{query}%')
        )
    ).all()

    processed_results = []
    for user in results:
        friendship_sent = Friend.query.filter_by(user_id=user_id, friend_id=user.id).first()
        friendship_received = Friend.query.filter_by(user_id=user.id, friend_id=user_id).first()
        status = friendship_sent.status if friendship_sent else friendship_received.status if friendship_received else 'none'
        processed_results.append({
            'id': user.id,
            'name': user.display_name or f"{user.first_name} {user.last_name}".strip(),
            'email': user.email,
            'status': status
        })

    return render_template('friend_search.html', results=processed_results, query=query)


@friend_bp.route('/friends/add', methods=['POST'])
def add_friend():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    friend_id = request.form.get('friend_id')

    if not friend_id or user_id == friend_id:
        flash('Invalid friend request.', 'danger')
        return redirect(url_for('friend.friends'))

    existing = Friend.query.filter_by(user_id=user_id, friend_id=friend_id).first()
    if existing:
        flash('Friend request already sent.', 'info')
        return redirect(url_for('friend.friends'))

    reverse = Friend.query.filter_by(user_id=friend_id, friend_id=user_id).first()
    if reverse and reverse.status == 'pending':
        reverse.status = 'accepted'
        db.session.commit()
        flash('Friend request accepted!', 'success')
        return redirect(url_for('friend.friends'))

    new_request = Friend(user_id=user_id, friend_id=friend_id, status='pending')
    db.session.add(new_request)
    db.session.commit()

    flash('Friend request sent!', 'success')
    return redirect(url_for('friend.friends'))


@friend_bp.route('/friends/accept', methods=['POST'])
def accept_friend():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    request_id = request.form.get('request_id')
    friend_request = Friend.query.filter_by(id=request_id, friend_id=user_id, status='pending').first()

    if not friend_request:
        flash('Friend request not found.', 'danger')
        return redirect(url_for('friend.friends'))

    friend_request.status = 'accepted'
    db.session.commit()

    flash('Friend request accepted!', 'success')
    return redirect(url_for('friend.friends'))


@friend_bp.route('/friends/reject', methods=['POST'])
def reject_friend():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    request_id = request.form.get('request_id')
    friend_request = Friend.query.filter_by(id=request_id, friend_id=user_id, status='pending').first()

    if not friend_request:
        flash('Friend request not found.', 'danger')
        return redirect(url_for('friend.friends'))

    friend_request.status = 'rejected'
    db.session.commit()

    flash('Friend request rejected.', 'info')
    return redirect(url_for('friend.friends'))


@friend_bp.route('/friends/toggle-share', methods=['POST'])
def toggle_share():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    user_id = session['user_id']
    friend_id = request.form.get('friend_id')

    friendship = Friend.query.filter_by(user_id=user_id, friend_id=friend_id, status='accepted').first()
    if not friendship:
        friendship = Friend.query.filter_by(user_id=friend_id, friend_id=user_id, status='accepted').first()

    if not friendship:
        return jsonify({'error': 'Friendship not found'}), 404

    friendship.share_data = not friendship.share_data
    db.session.commit()

    return jsonify({'success': True, 'sharing': friendship.share_data})


@friend_bp.route('/friends/<friend_id>/visualise')
def friend_visualise(friend_id):
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('user.login'))

    user_id = session['user_id']
    shared = Friend.query.filter_by(user_id=user_id, friend_id=friend_id, status='accepted', share_data=True).first() or \
             Friend.query.filter_by(user_id=friend_id, friend_id=user_id, status='accepted', share_data=True).first()

    if not shared:
        flash('You do not have permission to view this data.', 'warning')
        return redirect(url_for('friend.friends'))

    friend = User.query.get(friend_id)
    if not friend:
        flash('Friend not found.', 'danger')
        return redirect(url_for('friend.friends'))

    time_range = request.args.get('time_range', 'medium_term')

    all_features = AudioFeatures.query.join(Track, AudioFeatures.track_id == Track.id).filter(
        Track.user_id == friend_id
    ).all()

    mood_counts = Counter(f.mood for f in all_features if f.mood)
    total = sum(mood_counts.values()) or 1

    mood_data = {
        mood.lower(): {
            "percentage": round(100 * count / total),
            "top_track": None,
            "recommended_tracks": []
        }
        for mood, count in mood_counts.items()
    }

    personality_data = {
        "mbti": "INTJ",
        "summary": "Strategic, independent, and insightful.",
        "related_songs": []
    }

    friend_name = friend.display_name or f"{friend.first_name} {friend.last_name}".strip()

    return render_template('visualise.html',
                           first_name=friend_name,
                           time_range=time_range,
                           mood_data=mood_data,
                           personality=personality_data,
                           is_friend_view=True,
                           friend_id=friend_id)
