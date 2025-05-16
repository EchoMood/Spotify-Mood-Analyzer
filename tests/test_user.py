import sys
print("PYTHONPATH:", sys.path)

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

# Test: Simulate a user completing the second step of signup
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
