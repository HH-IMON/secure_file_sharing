"""Dashboard routes for the application."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import File, FileShare
from app.services.audit_service import get_user_activity, get_security_events


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    user_files = File.query.filter_by(owner_id=current_user.id, status='active').all()
    total_files = len(user_files)
    storage_used = sum(f.file_size or 0 for f in user_files)

    # Format storage
    if storage_used < 1024:
        formatted_storage = f"{storage_used} B"
    elif storage_used < 1024 * 1024:
        formatted_storage = f"{storage_used / 1024:.1f} KB"
    else:
        formatted_storage = f"{storage_used / (1024 * 1024):.1f} MB"

    storage_percent = min((storage_used / (50 * 1024 * 1024)) * 100, 100)  # 50MB cap

    shared_files = FileShare.query.filter_by(sender_id=current_user.id).count()
    received_files = FileShare.query.filter_by(recipient_id=current_user.id).count()

    recent_logs = get_user_activity(current_user.id, limit=10)
    security_events_count = len(get_security_events(limit=50)) if current_user.is_admin else 0

    return render_template('dashboard/index.html',
                           total_files=total_files,
                           shared_files=shared_files,
                           received_files=received_files,
                           formatted_storage=formatted_storage,
                           storage_percent=storage_percent,
                           recent_logs=recent_logs,
                           security_events=security_events_count)
