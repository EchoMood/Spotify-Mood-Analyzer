from app import db
from datetime import datetime

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spotify_id = db.Column(db.String(255), unique=True, nullable=False)  # Spotify user ID
    access_token = db.Column(db.String(255), nullable=False)
    refresh_token = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    tracks = db.relationship('Track', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.spotify_id}>'

    def add_user(self, spotify_id, access_token, refresh_token):
        self.spotify_id = spotify_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        db.session.add(self)
        db.session.commit()

    def update_tokens(self, access_token, refresh_token):
        self.access_token = access_token
        self.refresh_token = refresh_token
        db.session.commit()

    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.commit()

    @staticmethod
    def user_exists(spotify_id):
        return db.session.query(User).filter_by(spotify_id=spotify_id).first() is not None

class Track(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    track_name = db.Column(db.String(255), nullable=False)
    artist_name = db.Column(db.String(255), nullable=False)
    track_uri = db.Column(db.String(255), unique=True, nullable=False)
    rank = db.Column(db.Integer, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    audio_features = db.relationship('AudioFeatures', backref='track', lazy=True)

    def __repr__(self):
        return f'<Track {self.track_name} by {self.artist_name}>'

    @staticmethod
    def store_tracks(user_id, tracks):
        for track in tracks:
            existing_track = Track.query.filter_by(track_uri=track['uri'], user_id=user_id).first()
            if existing_track:
                existing_track.rank = track['rank']
            else:
                new_track = Track(
                    track_name=track['name'],
                    artist_name=track['artist'],
                    track_uri=track['uri'],
                    rank=track['rank'],
                    user_id=user_id
                )
                db.session.add(new_track)
        db.session.commit()

    @staticmethod
    def get_top_tracks(user_id, time_range='medium_term'):
        # Retrieve a user's top tracks by time range (short, medium, long)
        return Track.query.filter_by(user_id=user_id).order_by(Track.rank).all()

    def update_track_rank(self, rank):
        self.rank = rank
        db.session.commit()

class AudioFeatures(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    danceability = db.Column(db.Float, nullable=False)
    energy = db.Column(db.Float, nullable=False)
    key = db.Column(db.Integer, nullable=False)
    loudness = db.Column(db.Float, nullable=False)
    mode = db.Column(db.Integer, nullable=False)
    speechiness = db.Column(db.Float, nullable=False)
    acousticness = db.Column(db.Float, nullable=False)
    instrumentalness = db.Column(db.Float, nullable=False)
    liveness = db.Column(db.Float, nullable=False)
    valence = db.Column(db.Float, nullable=False)
    tempo = db.Column(db.Float, nullable=False)
    track_id = db.Column(db.Integer, db.ForeignKey('track.id'), nullable=False)

    def __repr__(self):
        return f'<AudioFeatures for Track {self.track_id}>'

    @staticmethod
    def store_audio_features(track_id, features):
        audio_features = AudioFeatures(
            danceability=features['danceability'],
            energy=features['energy'],
            key=features['key'],
            loudness=features['loudness'],
            mode=features['mode'],
            speechiness=features['speechiness'],
            acousticness=features['acousticness'],
            instrumentalness=features['instrumentalness'],
            liveness=features['liveness'],
            valence=features['valence'],
            tempo=features['tempo'],
            track_id=track_id
        )
        db.session.add(audio_features)
        db.session.commit()

    @staticmethod
    def get_audio_features(track_id):
        return AudioFeatures.query.filter_by(track_id=track_id).first()

    @staticmethod
    def bulk_retrieve_features(track_ids):
        return AudioFeatures.query.filter(AudioFeatures.track_id.in_(track_ids)).all()


