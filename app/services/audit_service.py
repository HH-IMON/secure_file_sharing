from flask import request
from app.models.audit_log import AuditLog
from app.models.user import User
from app.models.file import File
from app.models.share import FileShare
from app.extensions import db

def log_event(action: str, user_id: int = None, resource_type: str = None, resource_id: str = None, status: str = 'success', details: str = None) -> AuditLog:
    """Log an audit event."""
    ip_address = None
    user_agent = None
    if request:
        try:
            ip_address = request.remote_addr
            user_agent = request.user_agent.string
        except Exception:
            pass
            
    import json
    if isinstance(details, dict):
        details = json.dumps(details)
        
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=ip_address,
        user_agent=user_agent,
        status=status,
        details=details
    )
    db.session.add(log_entry)
    db.session.commit()
    return log_entry

def get_user_activity(user_id: int, limit: int = 50) -> list[AuditLog]:
    """Get recent user activity."""
    return AuditLog.query.filter_by(user_id=user_id).order_by(AuditLog.created_at.desc()).limit(limit).all()

def get_all_logs(page: int = 1, per_page: int = 50):
    """Retrieve all logs with pagination."""
    return AuditLog.query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

def get_security_events(limit: int = 10) -> list[AuditLog]:
    """Retrieve potential security issues."""
    return AuditLog.query.filter(
        db.or_(
            AuditLog.action.ilike('%fail%'),
            AuditLog.action.ilike('%denied%'),
            AuditLog.action.ilike('%error%'),
            AuditLog.status == 'failure'
        )
    ).order_by(AuditLog.created_at.desc()).limit(limit).all()

def get_system_stats() -> dict:
    """Retrieve system statistics."""
    return {
        'total_users': User.query.count(),
        'total_files': File.query.count(),
        'total_shares': FileShare.query.count(),
        'recent_security_events': len(get_security_events(limit=50))
    }
