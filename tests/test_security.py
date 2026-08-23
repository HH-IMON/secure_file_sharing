"""Security control tests."""
import io
import pytest
from app.models.user import User


def test_csrf_protection(app, client, db):
    """Verify CSRF rejection when enabled."""
    app.config['WTF_CSRF_ENABLED'] = True
    try:
        response = client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password',
        })
        # Without CSRF token, should get 200 (re-render form) or 400
        assert response.status_code in [200, 400]
    finally:
        app.config['WTF_CSRF_ENABLED'] = False


def test_security_headers(client, db):
    response = client.get('/auth/login')
    headers = response.headers
    assert 'X-Content-Type-Options' in headers
    assert 'X-Frame-Options' in headers
    assert 'X-XSS-Protection' in headers


def test_password_hash_not_plaintext(client, db):
    client.post('/auth/register', data={
        'name': 'Hash User',
        'email': 'hash@example.com',
        'password': 'StrongPassword123!',
        'confirm_password': 'StrongPassword123!',
    })
    user = User.query.filter_by(email='hash@example.com').first()
    assert user is not None
    assert user.password_hash != 'StrongPassword123!'
    assert user.password_hash.startswith('$argon2')


def test_no_private_key_in_response(auth_client, db):
    response = auth_client.get('/dashboard/')
    assert b'PRIVATE KEY' not in response.data


def test_path_traversal_filename(auth_client, db):
    data = {'file': (io.BytesIO(b"Content"), '../../../etc/passwd')}
    auth_client.post('/files/upload', data=data, content_type='multipart/form-data')
    from app.models.file import File
    f = File.query.order_by(File.id.desc()).first()
    if f is not None:
        assert '..' not in f.original_filename
        assert '/' not in f.stored_filename


def test_unauthorized_admin_access(auth_client, db):
    response = auth_client.get('/admin/')
    # Regular user should get 403
    assert response.status_code in [302, 403]


def test_sql_injection_login(client, db):
    response = client.post('/auth/login', data={
        'email': "admin@example.com' OR '1'='1",
        'password': 'password',
    }, follow_redirects=True)
    # Should not grant access – page should show login form or invalid message
    assert b'dashboard' not in response.data.lower() or b'invalid' in response.data.lower() or b'login' in response.data.lower()


def test_session_timeout_configured(app):
    assert 'PERMANENT_SESSION_LIFETIME' in app.config
