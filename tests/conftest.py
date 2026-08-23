"""Pytest configuration and fixtures for the secure file sharing tests."""
import os
import tempfile
import shutil
import pytest
from app import create_app
from app.extensions import db as _db
from app.models.user import User
from app.models.file import File
from app.models.file_key import FileKey
from app.models.share import FileShare
from app.models.audit_log import AuditLog
from app.models.login_attempt import LoginAttempt
from app.services.auth_service import hash_password
from app.services.key_service import generate_rsa_key_pair, encrypt_private_key


@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the test session."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test.db')

    os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'
    os.environ['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['WTF_CSRF_ENABLED'] = 'False'
    os.environ['RATELIMIT_ENABLED'] = 'False'
    os.environ['TESTING'] = 'True'
    os.environ['FILE_STORAGE_PATH'] = os.path.join(temp_dir, 'storage')
    os.makedirs(os.path.join(temp_dir, 'storage'), exist_ok=True)

    application = create_app()

    # Disable limiter for testing
    from app.extensions import limiter
    limiter.enabled = False

    # Force these configs on the app object just in case
    application.config['TESTING'] = True
    application.config['WTF_CSRF_ENABLED'] = False
    application.config['RATELIMIT_ENABLED'] = False
    application.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    yield application

    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope='function')
def db(app):
    """Provide a clean database for each test function."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """A test client for the app (with clean DB)."""
    return app.test_client()


def create_test_user(name: str, email: str, password: str) -> dict:
    """Helper to create a complete user with RSA keys and return it as dict."""
    pwd_hash = hash_password(password)
    priv_pem, pub_pem = generate_rsa_key_pair(2048)
    enc_priv = encrypt_private_key(priv_pem, password)

    user = User(
        name=name,
        email=email,
        password_hash=pwd_hash,
        public_key=pub_pem.decode('utf-8'),
        encrypted_private_key=enc_priv['encrypted_key'],
        private_key_salt=enc_priv['salt'],
        private_key_nonce=enc_priv['nonce'],
        role='user',
        is_active=True,
    )
    _db.session.add(user)
    _db.session.commit()
    
    # Return basic info to avoid DetachedInstanceError
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email
    }


@pytest.fixture
def auth_client(app, db):
    """Return a test client logged in as Alice."""
    password = 'TestPass@123'
    create_test_user('Alice', 'alice@example.com', password)

    client = app.test_client()
    client.post('/auth/login', data={
        'email': 'alice@example.com',
        'password': password,
    })
    return client


@pytest.fixture
def two_users(app, db):
    """Create Alice and Bob, return (alice, bob)."""
    alice = create_test_user('Alice', 'alice@example.com', 'TestPass@123')
    bob = create_test_user('Bob', 'bob@example.com', 'TestPass@123')
    return alice, bob
