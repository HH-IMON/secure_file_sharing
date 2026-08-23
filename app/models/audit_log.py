from sqlalchemy.sql import func
from app.extensions import db

class AuditLog(db.Model):
    """Model representing an audit log entry for system actions."""
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.String(50), nullable=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    status = db.Column(db.String(20), default='success')
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user_id={self.user_id}>"
