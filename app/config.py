"""Application configuration."""
import os
from datetime import timedelta


class Config:
    """Application configuration loaded from environment variables."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key-change-me')

    # Database – accept both DATABASE_URL and SQLALCHEMY_DATABASE_URI env vars
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'SQLALCHEMY_DATABASE_URI',
        os.environ.get('DATABASE_URL', 'sqlite:///secure_file_sharing.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload settings
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 52428800))
    FILE_STORAGE_PATH = os.environ.get('FILE_STORAGE_PATH', 'storage/encrypted')
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif',
        'doc', 'docx', 'xls', 'xlsx', 'pptx', 'csv', 'zip',
    }
    MAX_FILE_SIZE = MAX_CONTENT_LENGTH

    # Session settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    # CSRF – allow override via env for testing
    WTF_CSRF_ENABLED = os.environ.get('WTF_CSRF_ENABLED', 'True').lower() != 'false'
    WTF_CSRF_TIME_LIMIT = 3600

    # Rate limiting – allow override via env for testing
    RATELIMIT_ENABLED = os.environ.get('RATELIMIT_ENABLED', 'True').lower() != 'false'

    # Testing flag
    TESTING = os.environ.get('TESTING', 'False').lower() == 'true'
