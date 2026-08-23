"""Authentication tests."""
import pytest
from app.models.user import User


def test_register_success(client, db):
    response = client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!',
    }, follow_redirects=True)
    assert response.status_code == 200
    user = User.query.filter_by(email='test@example.com').first()
    assert user is not None
    assert user.name == 'Test User'


def test_register_duplicate_email(client, db):
    client.post('/auth/register', data={
        'name': 'User 1',
        'email': 'dup@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!',
    })
    response = client.post('/auth/register', data={
        'name': 'User 2',
        'email': 'dup@example.com',
        'password': 'AnotherPassword123!',
        'confirm_password': 'AnotherPassword123!',
    }, follow_redirects=True)
    assert b'already registered' in response.data.lower() or b'error' in response.data.lower()


def test_register_weak_password(client, db):
    response = client.post('/auth/register', data={
        'name': 'Weak User',
        'email': 'weak@example.com',
        'password': 'weak',
        'confirm_password': 'weak',
    }, follow_redirects=True)
    # Weak password should be rejected (form validation min length 8)
    user = User.query.filter_by(email='weak@example.com').first()
    assert user is None


def test_login_success(client, db):
    # Register first
    client.post('/auth/register', data={
        'name': 'Login User',
        'email': 'login@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!',
    })
    # Now login
    response = client.post('/auth/login', data={
        'email': 'login@example.com',
        'password': 'StrongPassword123!',
    }, follow_redirects=True)
    assert response.status_code == 200


def test_login_invalid_credentials(client, db):
    client.post('/auth/register', data={
        'name': 'Login User',
        'email': 'login2@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!',
    })
    response = client.post('/auth/login', data={
        'email': 'login2@example.com',
        'password': 'WrongPassword123!',
    }, follow_redirects=True)
    assert b'invalid' in response.data.lower() or b'error' in response.data.lower()


def test_login_nonexistent_user(client, db):
    response = client.post('/auth/login', data={
        'email': 'nobody@example.com',
        'password': 'SomePassword123!',
    }, follow_redirects=True)
    assert b'invalid' in response.data.lower() or b'error' in response.data.lower()


def test_logout(auth_client, db):
    response = auth_client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200


def test_protected_route_requires_login(client, db):
    response = client.get('/dashboard/', follow_redirects=True)
    # Should redirect to login page
    assert b'login' in response.data.lower() or b'log in' in response.data.lower()


def test_session_contains_pk_key(client, db):
    client.post('/auth/register', data={
        'name': 'Session User',
        'email': 'sess@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!',
    })
    client.post('/auth/login', data={
        'email': 'sess@example.com',
        'password': 'StrongPassword123!',
    })
    with client.session_transaction() as sess:
        assert '_pk_key' in sess
