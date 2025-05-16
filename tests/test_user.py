import pytest
from app import create_app, db

# Fixture that provides a clean test client for each test
@pytest.fixture
def client():
    app = create_app('testing')

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client

# Test 1: Simulate a user completing the second step of signup
def test_signup_step_two(client):
    # Step 1: Preload session with first-step signup info
    with client.session_transaction() as session:
        session['first_name'] = 'Test'
        session['last_name'] = 'User'
        session['age'] = 21

    # Step 2: Submit step two form with email and password
    response = client.post('/signup/login_credentials', data={
        'email': 'testuser@example.com',
        'password': '12345678',
        'confirm_password': '12345678'
    }, follow_redirects=False)

    # Assert the server redirects to /dashboard after successful signup
    assert response.status_code == 302
    assert '/dashboard' in response.headers['Location']

# Test 2: After user registration, the admin inspection page should display the user data
def test_admin_inspect_shows_registered_user(client):
    # Step 1: Simulate step one session data
    with client.session_transaction() as session:
        session['first_name'] = 'AdminTest'
        session['last_name'] = 'User'
        session['age'] = 30

    # Step 2: Register the user
    client.post('/signup/login_credentials', data={
        'email': 'admintest@example.com',
        'password': 'securepass',
        'confirm_password': 'securepass'
    }, follow_redirects=True)

    # Step 3: Access the admin inspect page with correct secret token
    from flask import current_app
    app = create_app('testing')
    with app.app_context():
        secret_key = app.config['SECRET_KEY']

    response = client.get(f'/admin/inspect-db/{secret_key}')
    
    # Step 4: Verify response
    assert response.status_code == 200
    assert b'AdminTest' in response.data or b'Users' in response.data


# Test 3: Linking a Spotify account should redirect to Spotify's authorization page
def test_link_spotify_redirects(client):
    # Step 1: Simulate user login by adding user_id to session
    with client.session_transaction() as session:
        session['user_id'] = 'test-user-id'

    # Step 2: Access the /link/spotify route
    response = client.get('/link/spotify', follow_redirects=False)

    # Step 3: Assert redirection to Spotify authorization URL
    assert response.status_code == 302
    assert 'https://accounts.spotify.com/authorize' in response.headers['Location']


# Test 4: Adding a friend should insert a pending friend request into the database
def test_add_friend_creates_request(client):
    from app.models import User, Friend

    # Step 1: Create two users in the test database
    user1 = User(id='user-1', email='user1@example.com', first_name='User', last_name='One')
    user1.set_password('password123')
    user2 = User(id='user-2', email='user2@example.com', first_name='User', last_name='Two')
    user2.set_password('password456')

    with client.application.app_context():
        from app import db
        db.session.add_all([user1, user2])
        db.session.commit()

    # Step 2: Log in as user1
    with client.session_transaction() as session:
        session['user_id'] = 'user-1'

    # Step 3: Send POST request to add user2 as a friend
    response = client.post('/friends/add', data={'friend_id': 'user-2'}, follow_redirects=False)

    # Step 4: Verify redirect and database update
    assert response.status_code == 302
    assert '/friends' in response.headers['Location']

    with client.application.app_context():
        friend_request = Friend.query.filter_by(user_id='user-1', friend_id='user-2').first()
        assert friend_request is not None
        assert friend_request.status == 'pending'


# Test: Accepting a friend request should update its status to 'accepted'
def test_accept_friend_request(client):
    from app.models import User, Friend

    # Step 1: Create requester and recipient users
    user1 = User(id='user-1', email='user1@example.com', first_name='User', last_name='One')
    user1.set_password('password123')
    user2 = User(id='user-2', email='user2@example.com', first_name='User', last_name='Two')
    user2.set_password('password456')

    with client.application.app_context():
        from app import db
        db.session.add_all([user1, user2])
        db.session.commit()

        # Step 2: Create a pending friend request from user1 to user2
        friend_request = Friend(user_id='user-1', friend_id='user-2', status='pending')
        db.session.add(friend_request)
        db.session.commit()
        request_id = friend_request.id  # Save for use in test

    # Step 3: Simulate login as user2
    with client.session_transaction() as session:
        session['user_id'] = 'user-2'

    # Step 4: Accept the friend request
    response = client.post('/friends/accept', data={'request_id': request_id}, follow_redirects=False)

    # Step 5: Verify redirect and DB update
    assert response.status_code == 302
    assert '/friends' in response.headers['Location']

    with client.application.app_context():
        updated_request = Friend.query.get(request_id)
        assert updated_request.status == 'accepted'




