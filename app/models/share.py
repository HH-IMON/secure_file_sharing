from uuid import uuid4
from datetime import datetime
from sqlalchemy.sql import func
from app.extensions import db

class FileShare(db.Model):
    """Model representing a shared file relationship."""
    __tablename__ = 'file_shares'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission = db.Column(db.String(20), default='download')
    message = db.Column(db.Text, nullable=True)
    one_time_download = db.Column(db.Boolean, default=False)
    downloaded = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=func.now())

    @property
    def is_expired(self) -> bool:
        """Check if the share has expired."""
        return self.expires_at is not None and self.expires_at < datetime.utcnow()

    @property
    def is_revoked(self) -> bool:
        """Check if the share has been revoked."""
        return self.revoked_at is not None

    @property
    def is_active(self) -> bool:
        """Check if the share is currently active."""
        return not self.is_expired and not self.is_revoked and not (self.one_time_download and self.downloaded)

    def __repr__(self) -> str:
        return f"<FileShare {self.uuid} from {self.sender_id} to {self.recipient_id}>"
