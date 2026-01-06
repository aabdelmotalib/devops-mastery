"""
Flask Backend Tutorial - Application Factory
"""
from flask import Flask
from app.config import config
from app.extensions import db, migrate, cors

def create_app(config_name='development'):
    """
    Application factory function
    
    Args:
        config_name: Configuration to use (development, testing, production)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize configuration-specific setup
    if hasattr(config[config_name], 'init_app'):
        config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        """Health check endpoint"""
        return {'status': 'healthy', 'version': '1.0.0'}, 200
    
    return app

def register_blueprints(app):
    """Register all application blueprints"""
    from app.routes.auth import bp as auth_bp
    from app.routes.users import bp as users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
