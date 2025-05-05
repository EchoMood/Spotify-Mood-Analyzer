# app.py – EchoMood Flask Application with DB + Hashed Login + Test User

import os
from flask import Flask, render_template, redirect, flash, url_for, session
from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, StringField
from wtforms.validators import DataRequired, Email, Optional
from flask_wtf.csrf import CSRFProtect

# Import SQLAlchemy ORM and password hashing utilities
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm, SignupStepOneForm, SignupStepTwoForm

# ----------------------------------------------------------
# Flask App Configuration
# ----------------------------------------------------------
app = Flask(__name__)

# Secret key for CSRF protection and session management
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-me-for-production')

# SQLite database URI (stored in a local file)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CSRF protection
csrf = CSRFProtect(app)
# Initialize SQLAlchemy for ORM/database interaction
db = SQLAlchemy(app)

# ----------------------------------------------------------
# User Model
# ----------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50))
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

# ----------------------------------------------------------
# LoginForm – Handles form validation for user login
# ----------------------------------------------------------
class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])            # Email input field
    password = PasswordField('Password', validators=[DataRequired()])            # Password input field
    submit = SubmitField('Login')                                                # Form submission


# ----------------------------------------------------------
# Index Route – Landing page for EchoMood
# ----------------------------------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# ----------------------------------------------------------
# Step 1: Basic Info
# ----------------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupStepOneForm()
    if form.validate_on_submit():
        session['first_name'] = form.first_name.data
        session['last_name'] = form.last_name.data
        session['age'] = form.age.data
        return redirect(url_for('signup_login_credentials'))
    return render_template('signup.html', form=form)

# ----------------------------------------------------------
# Step 2: Login Credentials
# ----------------------------------------------------------
@app.route('/signup/login_credentials', methods=['GET', 'POST'])
def signup_login_credentials():
    form = SignupStepTwoForm()

    # Prevent direct access to Step 2 if Step 1 not done
    if not session.get('first_name'):
        flash('Please complete Step 1 first.', 'warning')
        return redirect(url_for('signup'))

    # Check if the form is submitted and valid
    if form.validate_on_submit():
        # Retrieve values from session (Step 1)
        first_name = session.get('first_name')
        last_name = session.get('last_name')
        age = session.get('age')
        email = form.email.data

        # ❗ Check if the email already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists. Please proceed to the login page.', 'danger')
            return render_template('signup_cred.html', form=form)

        # ✅ If not, proceed to create user
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(
            first_name=first_name,
            last_name=last_name,
            age=age,
            email=email,
            password=hashed_pw
        )
        db.session.add(new_user)
        db.session.commit()

        # Clear session data and redirect
        session.clear()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))

    return render_template('signup_cred.html', form=form)
# ----------------------------------------------------------
# Login Route – Handles user authentication
# ----------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        # Extract form data
        email = form.email.data
        password = form.password.data

        # Query database for matching email
        user = User.query.filter_by(email=email).first()

        # Validate password against stored hash
        if user and check_password_hash(user.password, password):
            flash('Login successful!', 'success')
            # After successful login
            session['user_email'] = user.email
            session['first_name'] = user.first_name  # 👈 Store first name
            return redirect(url_for('visualise', email=user.email))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('login.html', form=form)

# ----------------------------------------------------------
# OAuth Placeholders – Routes for Spotify and Apple Music
# ----------------------------------------------------------
@app.route('/oauth/spotify')
def oauth_spotify():
    # Placeholder for Spotify OAuth implementation
    return redirect('https://accounts.spotify.com/authorize?...')

@app.route('/oauth/apple')
def oauth_apple():
    # Placeholder for Apple Music OAuth implementation
    return redirect('https://appleid.apple.com/auth/authorize?...')

# ----------------------------------------------------------
# Route: Personalized Visualisation Page – Secured by Session
# ----------------------------------------------------------
@app.route('/visualise/<email>')
def visualise(email):
    # Check if user is logged in and matches the email in the session
    if 'user_email' not in session or session['user_email'] != email:
        flash('Please log in to view your visualisation.', 'warning')
        return redirect(url_for('login'))
    
    return render_template('visualise.html', email=email, first_name=session.get('first_name'))
# ================================
# Route: Admin View User Table
# ================================
@app.route('/admin/users')
def admin_view_users():
    """Displays all users stored in the database via HTML table."""
    all_users = User.query.all()  # Retrieve all user records
    return render_template('admin_users.html', users=all_users)

# ----------------------------------------------------------
# Main Application Entry Point
# ----------------------------------------------------------
if __name__ == '__main__':
    with app.app_context():
        # Create all DB tables if they do not exist
        db.create_all()

        # --------------------------------------------------------
        # Insert dummy user only if it doesn't already exist
        # --------------------------------------------------------
        dummy_email = 'admin@example.com'
        user = User.query.filter_by(email=dummy_email).first()

        if not user:
            dummy_user = User(
                first_name='Admin',
                last_name='User',
                age=30,
                email=dummy_email,
                password=generate_password_hash('adminpass')
            )
            db.session.add(dummy_user)
            db.session.commit()
            print(f"✅ Dummy user '{dummy_email}' was added.")
        else:
            print(f"✅ Dummy user '{dummy_email}' already exists.")

    # Start the Flask development server
    app.run(debug=True)