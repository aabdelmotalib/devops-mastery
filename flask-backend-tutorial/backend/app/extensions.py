"""
Flask extensions initialization
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# Create extension instances
# These are initialized in the application factory with init_app()
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
