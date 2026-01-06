import os
from app import create_app

# Determine environment from environment variable
config_name = os.environ.get('FLASK_ENV', 'development')

# Create application instance
app = create_app(config_name)

if __name__ == '__main__':
    # Development server only
    # In production, use Gunicorn: gunicorn -w 4 -b 0.0.0.0:8000 "run:app"
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', False)
    )
