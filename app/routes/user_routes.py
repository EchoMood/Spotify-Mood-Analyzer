# app/routes/user_routes.py

from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from datetime import datetime
import uuid

from app.models import db, User, Friend, Track, AudioFeatures
from app.forms import SignupStepOneForm, SignupStepTwoForm, LoginForm

user_bp = Blueprint('user', __name__)

# ----------------------------------------------------------
# Index Route – Landing page for EchoMood
# ----------------------------------------------------------
@user_bp.route('/')
def index():
    return render_template('index.html')

# ----------------------------------------------------------
# Step 1: Basic Info for Traditional Signup
# ----------------------------------------------------------
@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupStepOneForm()
    if form.validate_on_submit():
        session['first_name'] = form.first_name.data
        session['last_name'] = form.last_name.data
        session['age'] = form.age.data
        return redirect(url_for('user.signup_login_credentials'))
    return render_template('signup.html', form=form)

# ----------------------------------------------------------
# Step 2: Login Credentials for Traditional Signup
# ----------------------------------------------------------
# This route handles both traditional signup and Spotify signup continuation
# If the user is coming from Spotify login, they will be redirected here
# to complete their account creation.
# If the user is coming from the traditional signup, they will be redirected here
# to complete their account creation.
@user_bp.route('/signup/login_credentials', methods=['GET', 'POST'])
def signup_login_credentials():
    form = SignupStepTwoForm()

    if not session.get('first_name'):
        flash('Please complete Step 1 first.', 'warning')
        return redirect(url_for('user.signup'))

    if 'spotify_user_id' in session and request.method == 'POST':
            # If the user is coming from Spotify login and has already provided their email
            # Spotify signup continuation
            user_id = session['spotify_user_id']
            display_name = session.get('display_name', '')
            access_token = session.get('access_token')
            refresh_token = session.get('refresh_token')
            token_expiry = datetime.fromisoformat(session.get('token_expiry'))

            new_user = User(
                id=user_id,
                email=form.email.data,
                display_name=display_name,
                first_name=display_name.split()[0] if display_name else '',
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=token_expiry,
                last_login=datetime.utcnow()
            )
            new_user.set_password(form.password.data)

            db.session.add(new_user)
            db.session.commit()
            session.clear()
            flash("Account created successfully!", "success")
            return redirect(url_for('login'))
    
    # If the user is not coming from Spotify login
    # Check if the form is submitted and valid    
    if form.validate_on_submit():
        # Retrieve values from session (Step 1)
        first_name = session.get('first_name')
        last_name = session.get('last_name')
        age = session.get('age')
        email = form.email.data
        
        # Check if the email already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists. Please proceed to the login page.', 'danger')
            return render_template('signup_cred.html', form=form)
           
        # Create a new user with a generated ID (since Spotify users have IDs from the service)
        user_id = f"local_{uuid.uuid4()}"
        new_user = User(
            id=user_id,
            first_name=first_name,
            last_name=last_name,
            age=age,
            email=email,
            display_name=f"{first_name} {last_name}".strip()
        )
        new_user.set_password(form.password.data)

        db.session.add(new_user)
        db.session.commit()
        
        # Clear the session and set user details
        # to avoid conflicts with the next login
        session.clear()
        session['user_id'] = new_user.id
        session['user_email'] = new_user.email
        session['first_name'] = new_user.first_name

        flash('Account created successfully! Connect your Spotify account to unlock all features.', 'success')
        return redirect(url_for('user.dashboard'))

    return render_template('signup_cred.html', form=form)

# ----------------------------------------------------------
# Login Route
# ----------------------------------------------------------
# This route handles both traditional login and Spotify login continuation
@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        #Extract the email and password from the form
        email = form.email.data
        password = form.password.data
        
        #Query the database for the user with the provided email
        user = User.query.filter_by(email=email).first()
        
        #Check if the user exists and if the password is correct
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['first_name'] = user.first_name
            flash('Login successful!', 'success')
            
            # Redirect to the dashboard
            return redirect(url_for('user.dashboard'))
        else:
            # If the user does not exist or the password is incorrect
            flash('Invalid email or password. Please try again.', 'danger')
    return render_template('login.html', form=form)

# ----------------------------------------------------------
# Logout Route
# ----------------------------------------------------------
@user_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('user.index'))

# ----------------------------------------------------------
# Dashboard Route
# ----------------------------------------------------------
@user_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('user.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('user.login'))

    friends_sent = Friend.query.filter_by(user_id=user.id, status='accepted').all()
    friends_received = Friend.query.filter_by(friend_id=user.id, status='accepted').all()
    pending_requests = Friend.query.filter_by(friend_id=user.id, status='pending').all()

    friends_list = []
    for f in friends_sent + friends_received:
        friend_user = User.query.get(f.friend_id if f.user_id == user.id else f.user_id)
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

    return render_template('dashboard.html',
                           user=user,
                           friends=friends_list,
                           pending_requests=pending_list)
