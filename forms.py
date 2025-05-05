# ----------------------------------------------------------
# forms.py – Flask-WTF form definitions for EchoMood Login
# ----------------------------------------------------------

# Importing FlaskForm as the base class for all forms
from flask_wtf import FlaskForm

# Importing field types used in the login form
from wtforms import StringField, PasswordField, SubmitField, EmailField, IntegerField, SelectField

# Importing validators to enforce input constraints
from wtforms.validators import DataRequired, Email, Optional, NumberRange, EqualTo

# ----------------------------------------------------------
# SignupStepOneForm - Collects name, age, and gender
# ----------------------------------------------------------
class SignupStepOneForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[Optional()])
    age = IntegerField('Age', validators=[DataRequired(), NumberRange(min=1, max=120)])
    continue_button = SubmitField('Continue')

# ----------------------------------------------------------
# SignupStepTwoForm - Collects credentials
# ----------------------------------------------------------
class SignupStepTwoForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Sign Up')


# ----------------------------------------------------------
# LoginForm – used for user login via email and password
# ----------------------------------------------------------
class LoginForm(FlaskForm):
    # Email input field
    # - Label: 'Email'
    # - Validators: Required + must be a valid email format
    email = StringField(
        'Email',
        validators=[DataRequired(message="Email is required."), Email(message="Enter a valid email address.")]
    )

    # Password input field
    # - Label: 'Password'
    # - Validators: Required only
    password = PasswordField(
        'Password',
        validators=[DataRequired(message="Password is required.")]
    )

    # Submit button to submit the form
    # - Label on the button: 'Sign in'
    submit = SubmitField('Sign in')