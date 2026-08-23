from functools import wraps
from flask import abort
from flask_login import current_user

def admin_required(f):
    """Decorator that checks current_user.is_admin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def active_required(f):
    """Decorator that checks current_user.is_active."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_active', False):
            abort(403, description='Account disabled')
        return f(*args, **kwargs)
    return decorated_function
