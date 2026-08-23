from uuid import uuid4
from sqlalchemy.sql import func
from flask_login import UserMixin
from app.extensions import db

class User(db.Model, UserMixin):
    """User model representing system users."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    public_key = db.Column(db.Text, nullable=True)
    encrypted_private_key = db.Column(db.Text, nullable=True)
    private_key_salt = db.Column(db.String(64), nullable=True)
    private_key_nonce = db.Column(db.String(64), nullable=True)
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    files = db.relationship('File', backref='owner', lazy='dynamic')
    sent_shares = db.relationship('FileShare', foreign_keys='FileShare.sender_id', backref='sender', lazy='dynamic')
    received_shares = db.relationship('FileShare', foreign_keys='FileShare.recipient_id', backref='recipient', lazy='dynamic')
    file_keys = db.relationship('FileKey', backref='recipient', lazy='dynamic')
    audit_logs = db.relationship('AuditLog', backref='user', lazy='dynamic')

    @property
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == 'admin'

    def __repr__(self) -> str:
        return f"<User {self.email}>"
