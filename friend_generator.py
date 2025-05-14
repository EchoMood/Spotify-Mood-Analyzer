# test_data.py
from app import create_app
from app.models import db, User, Friend

from datetime import datetime
import uuid
import random


def generate_test_data(num_users=5):
    """Generate test users and friendships"""
    app = create_app()

    with app.app_context():
        # Get your user ID from the database or specify it here
        your_user_id = None  # We'll find it dynamically

        # Find your user ID
        your_email = input("Enter your email to find your user ID: ")
        your_user = User.query.filter_by(email=your_email).first()

        if not your_user:
            print(f"No user found with email {your_email}. Please enter a valid email.")
            return

        your_user_id = your_user.id
        print(f"Found your user with ID: {your_user_id}")

        # Create dummy users
        new_users = []
        for i in range(num_users):
            user_id = f"test_user_{uuid.uuid4().hex[:8]}"
            email = f"test{i}@example.com"

            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"User {email} already exists, using existing user.")
                new_users.append(existing_user)
                continue

            # Create new user
            new_user = User(
                id=user_id,
                email=email,
                first_name=f"Test{i}",
                last_name=f"User{i}",
                display_name=f"Test User {i}",
                age=random.randint(18, 65)
            )
            new_user.set_password("password123")

            db.session.add(new_user)
            new_users.append(new_user)
            print(f"Created user: {email} with ID: {user_id}")

        db.session.commit()

        # Create various friendship states
        for i, user in enumerate(new_users):
            # Skip some users to create variety
            # Create pending friend request FROM this user TO you
            friend_request = Friend(
                    user_id=user.id,
                    friend_id=your_user_id,
                    status='pending'
            )
            db.session.add(friend_request)
            print(f"Created incoming friend request from {user.email}")

        # Create one accepted friendship
        if new_users:
            accepted_friend = Friend(
                user_id=your_user_id,
                friend_id=new_users[0].id,
                status='accepted',
                share_data=True
            )
            db.session.add(accepted_friend)
            print(f"Created accepted friendship with {new_users[0].email}")

        db.session.commit()
        print("✅ Test data generation complete!")


if __name__ == "__main__":
    generate_test_data()