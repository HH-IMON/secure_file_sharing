from sqlalchemy.sql import func
from app.extensions import db

class FileKey(db.Model):
    """Model representing a user's encrypted access key to a file."""
    __tablename__ = 'file_keys'
    __table_args__ = (
        db.UniqueConstraint('file_id', 'recipient_id', name='uq_file_recipient'),
    )

    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    encrypted_aes_key = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=func.now())

    def __repr__(self) -> str:
        return f"<FileKey file_id={self.file_id} recipient_id={self.recipient_id}>"
