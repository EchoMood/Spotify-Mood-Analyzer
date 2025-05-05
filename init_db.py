from run import app
from models import db

with app.app_context():
    db.create_all()
    print("✅ Database initialized successfully!")
