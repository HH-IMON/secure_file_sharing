import os
from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager, csrf, limiter

def create_app(config_class=Config) -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))

    # Register blueprints safely
    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except ImportError:
        pass
        
    try:
        from app.routes.dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    except ImportError:
        pass
        
    try:
        from app.routes.files import files_bp
        app.register_blueprint(files_bp, url_prefix='/files')
    except ImportError:
        pass
        
    try:
        from app.routes.sharing import sharing_bp
        app.register_blueprint(sharing_bp, url_prefix='/sharing')
    except ImportError:
        pass
        
    try:
        from app.routes.profile import profile_bp
        app.register_blueprint(profile_bp, url_prefix='/profile')
    except ImportError:
        pass
        
    try:
        from app.routes.admin import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        pass
        
    try:
        from app.routes.education import education_bp
        app.register_blueprint(education_bp, url_prefix='/education')
    except ImportError:
        pass

    # Register error handlers
    try:
        from app.routes.errors import register_error_handlers
        register_error_handlers(app)
    except ImportError:
        pass

    # Security headers
    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; font-src 'self' cdn.jsdelivr.net; img-src 'self' data:"
        return response

    # Create storage directory
    os.makedirs(app.config['FILE_STORAGE_PATH'], exist_ok=True)

    return app
