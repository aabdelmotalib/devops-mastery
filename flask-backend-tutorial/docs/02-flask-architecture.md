# Module 2: Flask Architecture

## The Application Factory Pattern

The application factory is a function that creates and configures a Flask application instance. This is the **standard pattern** for production Flask applications.

### Why Application Factory?

**Without Factory (Bad for Production):**

```python
# app.py - DON'T DO THIS
from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret'

@app.route('/')
def index():
    return 'Hello'

if __name__ == '__main__':
    app.run()
```

**Problems:**
1. **Cannot create multiple instances** (needed for testing)
2. **Configuration is fixed** at import time
3. **Extensions initialize immediately**, before configuration
4. **Circular imports** become common as app grows

**With Factory (Production Standard):**

```python
# app/__init__.py
from flask import Flask
from app.config import config

def create_app(config_name='development'):
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    from app.extensions import db, migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    from app.routes import auth, users
    app.register_blueprint(auth.bp)
    app.register_blueprint(users.bp)
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    return app
```

**Benefits:**
1. **Multiple instances**: Different configs for dev/test/prod
2. **Delayed configuration**: Set at runtime, not import time
3. **Testability**: Create isolated app instances for tests
4. **Extension management**: Initialize after configuration
5. **Avoid circular imports**: Import blueprints inside function

## Understanding Flask Contexts

Flask has two types of contexts that are crucial to understand for production applications.

### Application Context

The application context keeps track of application-level data during a request.

**When it exists:**
- During a request
- When explicitly created with `app.app_context()`

**What it provides:**
- `current_app`: Proxy to the active application
- `g`: Object for storing data during a request

**Real-world use case:**

```python
# app/services/database.py
from flask import current_app, g
import psycopg2

def get_db():
    """Get database connection for current request"""
    if 'db' not in g:
        g.db = psycopg2.connect(
            current_app.config['DATABASE_URL']
        )
    return g.db

def close_db(error=None):
    """Close database connection after request"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Register teardown
def init_app(app):
    app.teardown_appcontext(close_db)
```

**Why this matters:**
- `current_app` lets you access config without passing `app` everywhere
- `g` is request-scoped storage (cleared after each request)
- Teardown functions clean up resources automatically

### Request Context

The request context keeps track of request-level data.

**When it exists:**
- During an HTTP request
- When explicitly created with `app.test_request_context()`

**What it provides:**
- `request`: Current HTTP request object
- `session`: User session data

**Context hierarchy:**

```
Application Context (app-level)
    └── Request Context (request-level)
            ├── request object
            └── session object
```

### Practical Example: Background Tasks

```python
# app/tasks/email.py
from flask import current_app
from threading import Thread

def send_async_email(app, msg):
    """Send email in background thread"""
    # Need application context for config access
    with app.app_context():
        # Now current_app works
        mail_server = current_app.config['MAIL_SERVER']
        # Send email logic here
        print(f"Sending email via {mail_server}")

def send_email(subject, recipients, body):
    """Queue email for background sending"""
    from flask import current_app
    app = current_app._get_current_object()
    
    msg = {'subject': subject, 'recipients': recipients, 'body': body}
    
    # Spawn background thread
    Thread(target=send_async_email, args=(app, msg)).start()
```

**Why we need `app._get_current_object()`:**
- `current_app` is a proxy, not the real app object
- Background threads don't have automatic context
- We pass the real app object and create context manually

### Common Context Errors

**Error 1: Working Outside Application Context**

```python
# BAD
from app import create_app
from flask import current_app

app = create_app()
print(current_app.config['SECRET_KEY'])  # RuntimeError!
```

**Fix:**

```python
# GOOD
from app import create_app

app = create_app()
with app.app_context():
    from flask import current_app
    print(current_app.config['SECRET_KEY'])  # Works!
```

**Error 2: Accessing Request Outside Request Context**

```python
# BAD
from flask import request

def some_utility_function():
    user_agent = request.headers.get('User-Agent')  # RuntimeError!
```

**Fix:**

```python
# GOOD - pass request data explicitly
def some_utility_function(user_agent):
    # Use passed parameter
    return user_agent

# In route
@app.route('/')
def index():
    result = some_utility_function(request.headers.get('User-Agent'))
```

## Project Structure Deep Dive

### The Standard Structure

```
backend/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration classes
│   ├── extensions.py        # Extension instances
│   ├── models/              # Database models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── post.py
│   ├── routes/              # Blueprints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── users.py
│   ├── services/            # Business logic
│   │   ├── __init__.py
│   │   └── auth_service.py
│   ├── templates/           # Jinja2 templates
│   ├── static/              # CSS, JS, images
│   └── errors.py            # Error handlers
├── migrations/              # Database migrations
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   └── test_auth.py
├── run.py                   # Application entry point
├── requirements.txt         # Dependencies
└── .env                     # Environment variables (not in git)
```

### Why This Structure?

**Separation of Concerns:**

1. **`app/__init__.py`**: Application creation only
2. **`app/config.py`**: All configuration in one place
3. **`app/extensions.py`**: Extension instances (avoid circular imports)
4. **`app/models/`**: Data layer
5. **`app/routes/`**: HTTP layer (thin controllers)
6. **`app/services/`**: Business logic (thick services)
7. **`app/errors.py`**: Centralized error handling

### File-by-File Breakdown

#### `app/__init__.py` - Application Factory

```python
from flask import Flask

def create_app(config_name='development'):
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    from app.extensions import db, migrate, cors
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.users import bp as users_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    return app
```

#### `app/config.py` - Configuration Management

```python
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://localhost/flask_dev'
    SQLALCHEMY_ECHO = True  # Log SQL queries

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/flask_test'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Production-specific settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @classmethod
    def init_app(cls, app):
        """Production-specific initialization"""
        # Log to syslog or external service
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

**Why separate configs:**
- Different database URLs for dev/test/prod
- Different debug settings
- Different security settings
- Environment-specific initialization

#### `app/extensions.py` - Extension Initialization

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

# Create extension instances
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()

# Extensions are initialized in create_app() with init_app()
```

**Why separate file:**
- Avoid circular imports
- Import extensions anywhere without importing app
- Clean separation of concerns

#### `run.py` - Application Entry Point

```python
import os
from app import create_app

# Determine environment
config_name = os.environ.get('FLASK_ENV', 'development')

# Create application
app = create_app(config_name)

if __name__ == '__main__':
    # Development server only
    # In production, use Gunicorn: gunicorn "app:create_app()"
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )
```

## Why `__init__.py` Matters

### Package Initialization

`__init__.py` makes a directory a Python package and controls what's exposed.

**Example:**

```python
# app/models/__init__.py
from app.models.user import User
from app.models.post import Post

__all__ = ['User', 'Post']
```

**Now you can:**

```python
# Instead of:
from app.models.user import User
from app.models.post import Post

# You can:
from app.models import User, Post
```

### Controlling Imports

```python
# app/routes/__init__.py
from app.routes.auth import bp as auth_bp
from app.routes.users import bp as users_bp

def register_blueprints(app):
    """Register all blueprints"""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
```

## Common Architectural Mistakes

### Mistake 1: Circular Imports

**Bad:**

```python
# app/__init__.py
from flask import Flask
from app.routes import auth  # Imports auth blueprint

app = Flask(__name__)
app.register_blueprint(auth.bp)

# app/routes/auth.py
from app import app  # Circular import!
from app.models import User  # This might import app too
```

**Fix: Use Application Factory**

```python
# app/__init__.py
def create_app():
    app = Flask(__name__)
    from app.routes import auth
    app.register_blueprint(auth.bp)
    return app

# app/routes/auth.py
from flask import Blueprint
from app.models import User  # No circular import

bp = Blueprint('auth', __name__)
```

### Mistake 2: Business Logic in Routes

**Bad:**

```python
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Validation logic in route
    if not data.get('email'):
        return {'error': 'Email required'}, 400
    
    # Business logic in route
    if User.query.filter_by(email=data['email']).first():
        return {'error': 'Email exists'}, 400
    
    # Password hashing in route
    hashed = generate_password_hash(data['password'])
    
    # Database logic in route
    user = User(email=data['email'], password=hashed)
    db.session.add(user)
    db.session.commit()
    
    return {'id': user.id}, 201
```

**Good: Use Service Layer**

```python
# app/routes/users.py
from app.services.user_service import create_user

@bp.route('/users', methods=['POST'])
def create_user_route():
    """Thin controller - delegates to service"""
    data = request.get_json()
    user, error = create_user(data)
    
    if error:
        return {'error': error}, 400
    
    return {'id': user.id}, 201

# app/services/user_service.py
from app.models import User
from app.extensions import db
from werkzeug.security import generate_password_hash

def create_user(data):
    """Business logic for user creation"""
    # Validation
    if not data.get('email'):
        return None, 'Email required'
    
    # Check uniqueness
    if User.query.filter_by(email=data['email']).first():
        return None, 'Email already exists'
    
    # Create user
    user = User(
        email=data['email'],
        password=generate_password_hash(data['password'])
    )
    
    db.session.add(user)
    db.session.commit()
    
    return user, None
```

### Mistake 3: Hardcoded Configuration

**Bad:**

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/mydb'
app.config['SECRET_KEY'] = 'my-secret-key'
```

**Good:**

```python
# Use environment variables
import os

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# Or use config classes (shown earlier)
```

## Summary

The application factory pattern is mandatory for production Flask applications. It enables:
- Multiple application instances (dev/test/prod)
- Proper extension initialization
- Avoiding circular imports
- Testability

Understanding contexts is crucial:
- **Application context**: App-level data (`current_app`, `g`)
- **Request context**: Request-level data (`request`, `session`)

Project structure should enforce separation of concerns:
- Routes are thin controllers
- Services contain business logic
- Models are data layer only
- Configuration is environment-aware

---

## Practice Exercises

### Multiple Choice Questions

1. What is the primary benefit of the application factory pattern?
   a) Faster application startup
   b) Ability to create multiple app instances with different configs
   c) Automatic error handling
   d) Built-in authentication

2. When does the application context exist?
   a) Only during HTTP requests
   b) During requests and when explicitly created
   c) Always, from application startup
   d) Only in production mode

3. What is stored in the `g` object?
   a) Global application configuration
   b) Request-scoped data that's cleared after each request
   c) Database connection pool
   d) User session data

4. Why do we use `app/extensions.py`?
   a) To make the app load faster
   b) To avoid circular imports when using extensions
   c) It's required by Flask
   d) To enable debugging

5. Where should business logic be placed?
   a) In route handlers
   b) In models
   c) In service layer
   d) In `__init__.py`

### Practical Tasks

**Task 1: Build Application Factory**

Create a complete application factory setup:
1. Create `app/__init__.py` with `create_app()` function
2. Create `app/config.py` with Development, Testing, and Production configs
3. Create `app/extensions.py` with Flask-SQLAlchemy
4. Create `run.py` that uses the factory
5. Verify you can create multiple app instances with different configs

**Task 2: Context Management**

Create a utility function that:
1. Runs outside of a request (e.g., CLI command or background task)
2. Needs to access application configuration
3. Needs to query the database
4. Properly manages application context

Example: A script that sends daily summary emails to all users.

### Debugging Scenario

You've structured your Flask app with an application factory, but you're getting this error:

```
RuntimeError: Working outside of request context
```

**Your code:**

```python
# app/__init__.py
def create_app():
    app = Flask(__name__)
    
    from app.extensions import db
    db.init_app(app)
    
    from app.routes.users import bp
    app.register_blueprint(bp)
    
    return app

# app/routes/users.py
from flask import Blueprint, request
from app.models import User

bp = Blueprint('users', __name__)

# This runs at import time!
current_user_agent = request.headers.get('User-Agent')

@bp.route('/users')
def list_users():
    users = User.query.all()
    return {'users': [u.to_dict() for u in users]}
```

**Questions:**
1. What line is causing the error?
2. Why does this error occur?
3. How would you fix it?
4. What Flask concept does this violate?

---

**Next Module**: [Routing and Views](03-routing-and-views.md)
