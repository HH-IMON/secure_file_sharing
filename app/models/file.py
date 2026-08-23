from uuid import uuid4
from sqlalchemy.sql import func
from app.extensions import db

class File(db.Model):
    """Model representing an uploaded, encrypted file."""
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False, unique=True)
    mime_type = db.Column(db.String(100))
    file_size = db.Column(db.BigInteger)
    encrypted_size = db.Column(db.BigInteger)
    nonce = db.Column(db.LargeBinary(16))
    auth_tag = db.Column(db.LargeBinary(16))
    plaintext_hash = db.Column(db.String(128))
    ciphertext_hash = db.Column(db.String(128))
    signature = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    keys = db.relationship('FileKey', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    shares = db.relationship('FileShare', backref='file', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self) -> str:
        return f"<File {self.original_filename} (owner_id={self.owner_id})>"
