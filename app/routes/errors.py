"""Error handlers for the application."""
from flask import render_template, request, flash, redirect, url_for
from app.services.audit_service import log_event

def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        flash('Bad Request', 'danger')
        return render_template('errors/404.html'), 400

    @app.errorhandler(403)
    def forbidden_error(error):
        from flask_login import current_user
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        log_event('access_denied', user_id=user_id, details={'path': request.path})
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        flash('File too large. Please upload a smaller file.', 'danger')
        return redirect(url_for('files.upload'))

    @app.errorhandler(429)
    def ratelimit_handler(error):
        flash('Too many requests. Please try again later.', 'warning')
        return render_template('errors/500.html', error=error), 429

    @app.errorhandler(500)
    def internal_error(error):
        from flask_login import current_user
        user_id = current_user.id if current_user and current_user.is_authenticated else None
        log_event('server_error', user_id=user_id, details={'path': request.path})
        from app.extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500
