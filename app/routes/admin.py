"""Admin routes."""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.utils.decorators import admin_required
from app.models import User, AuditLog
from app.extensions import db
from app.services.audit_service import get_all_logs, get_system_stats, log_event

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@login_required
@admin_required
def index():
    stats = get_system_stats()
    recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    security_score = 100
    return render_template('admin/dashboard.html', 
                           total_users=stats['total_users'],
                           total_files=stats['total_files'],
                           total_shares=stats['total_shares'],
                           security_events=stats['recent_security_events'],
                           recent_logs=recent_logs, 
                           security_score=security_score)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    all_users = User.query.all()
    return render_template('admin/users.html', users=all_users)

@admin_bp.route('/users/<uuid>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_user(uuid):
    try:
        user = User.query.filter_by(uuid=uuid).first_or_404()
        if user.id == current_user.id:
            flash("Cannot toggle your own account status.", "danger")
        else:
            user.is_active = not user.is_active
            db.session.commit()
            log_event('user_toggled', user_id=current_user.id, resource_type='user', resource_id=user.id, details={'new_status': user.is_active})
            flash(f"User {user.email} is now {'active' if user.is_active else 'inactive'}.", "success")
    except Exception as e:
        flash(f"Error toggling user status: {str(e)}", "danger")
    return redirect(url_for('admin.users'))

@admin_bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    page = request.args.get('page', 1, type=int)
    pagination = get_all_logs(page=page, per_page=50)
    return render_template('admin/audit_logs.html', pagination=pagination)
