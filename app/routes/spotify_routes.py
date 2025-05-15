# app/routes/spotify_routes.py

from flask import Blueprint, request, session, redirect, url_for, flash, render_template
from datetime import datetime, timedelta
import uuid

from app import spotify_api
from app.models import db, User
from app.services.spotify_ingest import fetch_and_store_user_data

from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired, EqualTo

spotify_bp = Blueprint('spotify', __name__)

@spotify_bp.route('/oauth/spotify')
def oauth_spotify():
    state = str(uuid.uuid4())
    session['state'] = state
    scope = 'user-top-read user-read-private user-read-recently-played user-read-email'
    auth_url = spotify_api.get_auth_url(state, scope)
    return redirect(auth_url)


@spotify_bp.route('/callback')
def callback():
    if request.args.get('state') != session.get('state'):
        flash('Authentication error. Please try again.', 'danger')
        return redirect(url_for('user.index'))

    if request.args.get('error'):
        flash('Authentication was denied.', 'warning')
        return redirect(url_for('user.index'))

    code = request.args.get('code')
    if not code:
        flash('Authentication error. Please try again.', 'danger')
        return redirect(url_for('user.index'))

    token_data = spotify_api.get_access_token(code)
    if not token_data:
        flash('Failed to authenticate with Spotify.', 'danger')
        return redirect(url_for('user.index'))

    access_token = token_data['access_token']
    refresh_token = token_data['refresh_token']
    expires_in = token_data['expires_in']
    token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
    session['access_token'] = access_token

    user_data = spotify_api.get_user_profile(access_token)

    if user_data is None:
            # Failed to get user data from Spotify
            flash('Failed to retrieve user information from Spotify. Please try again.', 'danger')
            return redirect(url_for('user.index'))

    linking = session.pop('linking', False)
    if linking and 'user_id' in session:
        existing_user = User.query.get(session['user_id'])
        if existing_user:
            existing_user.access_token = access_token
            existing_user.refresh_token = refresh_token
            existing_user.token_expiry = token_expiry
            existing_user.spotify_id = user_data['id']
            db.session.commit()
            flash('Spotify account linked successfully!', 'success')
            return redirect(url_for('user.dashboard'))

    if not user_data:
        flash('Failed to retrieve user information.', 'danger')
        return redirect(url_for('user.index'))

    user = User.query.filter_by(id=user_data['id']).first()
    if not user and user_data.get('email'):
        user = User.query.filter_by(email=user_data['email']).first()

    if user:
        user.access_token = access_token
        user.refresh_token = refresh_token
        user.token_expiry = token_expiry
        if not user.id.startswith('spotify:'):
            user.spotify_id = user_data['id']
        user.last_login = datetime.utcnow()
    else:
        if not user_data.get('email'):
            session['spotify_user_id'] = user_data['id']
            session['display_name'] = user_data.get('display_name', '')
            session['access_token'] = access_token
            session['refresh_token'] = refresh_token
            session['token_expiry'] = token_expiry.isoformat()
            session['spotify_login_pending'] = True
            flash("We couldn't retrieve your email from Spotify. Please complete your signup.", 'warning')
            return redirect(url_for('user.signup_login_credentials'))

        display_name = user_data.get('display_name', '')
        first_name = display_name.split()[0] if display_name else ''
        last_name = ' '.join(display_name.split()[1:]) if len(display_name.split()) > 1 else ''

        user = User(
            id=user_data['id'],
            spotify_id=user_data['id'],
            email=user_data.get('email', ''),
            display_name=display_name,
            first_name=first_name,
            last_name=last_name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expiry=token_expiry,
            registration_method='spotify',
            last_login=datetime.utcnow()
        )
        db.session.add(user)

    db.session.commit()

    session['user_id'] = user.id
    session['user_email'] = user.email
    session['first_name'] = user.first_name or user.display_name.split()[0] if user.display_name else 'User'

    try:
        mood_counts = fetch_and_store_user_data(user.id, spotify_api)
        print("✅ Imported Spotify data for user", user.id)
        print("🎵 Mood breakdown:", mood_counts)
    except Exception as e:
        print("❌ Error while importing Spotify data:", str(e))


    if user.registration_method == 'spotify' and not user.password:
        flash('Please complete your account setup by setting a password.', 'info')
        return redirect(url_for('spotify.complete_account'))

    return redirect(url_for('visual.visualise'))


@spotify_bp.route('/complete_account', methods=['GET', 'POST'])
def complete_account():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('user.login'))

    if user.password:
        return redirect(url_for('visual.visualise'))

    class CompleteAccountForm(FlaskForm):
        password = PasswordField('Password', validators=[DataRequired()])
        confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
        submit = SubmitField('Complete Account')

    form = CompleteAccountForm()

    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Account setup completed!', 'success')
        return redirect(url_for('visual.visualise'))

    return render_template('complete_account.html', form=form, user=user)


@spotify_bp.route('/link/spotify')
def link_spotify():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    state = str(uuid.uuid4())
    session['state'] = state
    session['linking'] = True
    auth_url = spotify_api.get_auth_url(state)
    return redirect(auth_url)


@spotify_bp.route('/unlink/spotify', methods=['POST'])
def unlink_spotify():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('user.login'))

    user.access_token = None
    user.refresh_token = None
    user.token_expiry = None
    db.session.commit()

    flash('Spotify account unlinked successfully.', 'success')
    return redirect(url_for('user.dashboard'))
