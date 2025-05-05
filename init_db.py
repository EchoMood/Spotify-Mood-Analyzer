from run import app
from models import db

with app.app_context():
    db.drop_all() # Remove this line
    db.create_all()
    print("✅ Database initialized successfully!")
