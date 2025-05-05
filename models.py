from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

# Database models
class User(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    email = db.Column(db.String(100), unique=True)
    display_name = db.Column(db.String(100))
    access_token = db.Column(db.String(200))
    refresh_token = db.Column(db.String(200))
    token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

class Track(db.Model):
    __tablename__ = 'track'

    id = db.Column(db.String(50))
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'))
    time_range = db.Column(db.String(20))  # short_term, medium_term, long_term

    name = db.Column(db.String(200))
    artist = db.Column(db.String(200))
    album = db.Column(db.String(200))
    album_image_url = db.Column(db.String(200))
    popularity = db.Column(db.Integer)
    rank = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.PrimaryKeyConstraint('id', 'user_id', 'time_range'),
    )

# Previous code
# class Track(db.Model):
#     id = db.Column(db.String(50), primary_key=True)
#     user_id = db.Column(db.String(50), db.ForeignKey('user.id'))
#     name = db.Column(db.String(200))
#     artist = db.Column(db.String(200))
#     album = db.Column(db.String(200))
#     album_image_url = db.Column(db.String(200))
#     popularity = db.Column(db.Integer)
#     time_range = db.Column(db.String(20))  # short_term, medium_term, long_term
#     rank = db.Column(db.Integer)  # Position in the user's top tracks
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AudioFeatures(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    track_id = db.Column(db.String(50), db.ForeignKey('track.id'))
    danceability = db.Column(db.Float)
    energy = db.Column(db.Float)
    key = db.Column(db.Integer)
    loudness = db.Column(db.Float)
    mode = db.Column(db.Integer)
    speechiness = db.Column(db.Float)
    acousticness = db.Column(db.Float)
    instrumentalness = db.Column(db.Float)
    liveness = db.Column(db.Float)
    valence = db.Column(db.Float)
    tempo = db.Column(db.Float)
    duration_ms = db.Column(db.Integer)
    time_signature = db.Column(db.Integer)

