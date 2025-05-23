from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# Combined user model
class User(db.Model):
    __tablename__ = 'user'

    # Primary key from Spotify model (Spotify user ID)
    id = db.Column(db.String(50), primary_key=True)

    # Fields from traditional login
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256))  # Optional for OAuth users
    spotify_id = db.Column(db.String(50), unique=True, nullable=True)

    # Fields from Spotify model
    display_name = db.Column(db.String(100))
    access_token = db.Column(db.String(500))
    refresh_token = db.Column(db.String(500))
    token_expiry = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    registration_method = db.Column(db.String(20), default='traditional')  # 'traditional' or 'spotify'

    friends = db.relationship('Friend',
                              primaryjoin="and_(User.id==Friend.user_id, Friend.status=='accepted')",
                              backref='user_friend', lazy='dynamic',
                              overlaps="friend_requests_sent")
    # Authentication methods
    @property
    def has_spotify_connected(self):
        """Check if user has connected their Spotify account."""
        return self.access_token is not None

    # @property
    # def is_oauth_user(self):
    #     """Check if user was created through OAuth."""
    #     return self.access_token is not None

    def set_password(self, password):
        """Hash and set password for traditional login."""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Verify password for traditional login."""
        if not self.password:
            return False
        return check_password_hash(self.password, password)


# Keep existing Track and AudioFeatures models as they are
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
    genre = db.Column(db.String(100))
    mood = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.PrimaryKeyConstraint('id', 'user_id', 'time_range'),
    )


class Friend(db.Model):
    __tablename__ = 'friend'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    friend_id = db.Column(db.String(50), db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'accepted', 'rejected'
    share_data = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id],
                           backref=db.backref('friend_requests_sent',
                                              lazy='dynamic',
                                              overlaps="user_friend"),
                           overlaps="friends,user_friend")

    __table_args__ = (
        db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
    )

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
    mood = db.Column(db.String(20))