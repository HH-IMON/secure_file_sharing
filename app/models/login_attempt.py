from sqlalchemy.sql import func
from app.extensions import db

class LoginAttempt(db.Model):
    """Model representing a login attempt for security tracking."""
    __tablename__ = 'login_attempts'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<LoginAttempt email={self.email} success={self.success}>"
