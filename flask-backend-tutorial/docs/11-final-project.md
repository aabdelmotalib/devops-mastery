# Final Project: RESTful User Management API

## Introduction: Bringing It All Together

You've learned the fundamental concepts of Flask—routing, request handling, responses, authentication, extensions, and error handling. Now it's time to apply everything together in a real-world scenario: building a production-ready User Management API.

This capstone project integrates every concept from Modules 0-10:

**What You'll Build**: A complete RESTful API that manages user accounts with secure authentication, role-based access control, and production-quality code organization. This is the kind of API you'd deploy to production for a real application.

**Key Learning Outcomes**:
1. **Architecture**: How to structure a Flask application for maintainability and scalability using blueprints
2. **Database Integration**: Using SQLAlchemy ORM with migrations for data persistence
3. **Authentication**: Implementing JWT-based authentication with token refresh strategies
4. **Authorization**: Building role-based access control (RBAC) to enforce security policies
5. **Validation**: Properly validating input data before processing
6. **Error Handling**: Consistent error responses with proper HTTP status codes
7. **Testing**: Writing comprehensive tests for API endpoints
8. **Deployment**: Preparing your application for production deployment
9. **Monitoring**: Adding logging and observability to production systems
10. **Best Practices**: Security, performance, and maintainability patterns

**Project Structure Preview**:
```
user-management-api/
├── config.py              # Environment-based configuration
├── requirements.txt       # Python dependencies
├── migrations/            # Database schema changes
├── tests/                 # Comprehensive test suite
├── app/
│   ├── __init__.py       # Application factory
│   ├── models.py         # Database models (User, Role)
│   ├── extensions.py     # Initialized extensions (db, jwt, etc.)
│   ├── auth/
│   │   ├── routes.py     # Login, register, token refresh
│   │   └── decorators.py # Authentication/authorization helpers
│   ├── users/
│   │   ├── routes.py     # CRUD operations
│   │   └── utils.py      # User-related utilities
│   ├── errors/
│   │   └── handlers.py   # Centralized error handling
│   └── utils/
│       └── validators.py # Input validation
└── run.py               # Application entry point
```

This structure demonstrates the production patterns you'll use in real companies. It's modular, testable, and scales as your application grows.

**Time Estimate**: 6-8 hours to complete all requirements
**Difficulty**: Intermediate (assumes solid understanding of preceding modules)
**Prerequisites**: Complete understanding of Modules 0-10

Let's build something professional.

## Project Overview

Create a user management API with:
- JWT authentication
- User CRUD operations
- Role-based authorization
- Error handling
- Modular blueprint architecture
- Database migrations
- Production-ready configuration

## Requirements

### Functional Requirements

1. **Authentication**
   - User registration
   - User login (returns JWT)
   - Token refresh
   - Logout (token blacklisting)

2. **User Management**
   - List users (paginated, admin only)
   - Get user profile (own profile or admin)
   - Update user (own profile or admin)
   - Delete user (admin only)

3. **Authorization**
   - Regular users can only access their own data
   - Admins can access all user data
   - Proper 401/403 responses

4. **Error Handling**
   - Consistent error response format
   - Proper HTTP status codes
   - Request ID tracking
   - Logging

### Technical Requirements

- Application factory pattern
- Blueprint organization
- Service layer for business logic
- SQLAlchemy models
- Database migrations
- Environment-based configuration
- Input validation
- Password hashing
- Production logging

## Project Structure

```
backend/
├── app/
│   ├── __init__.py              # Application factory
│   ├── config.py                # Configuration classes
│   ├── extensions.py            # Extension instances
│   ├── exceptions.py            # Custom exceptions
│   ├── errors.py                # Error handlers
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py              # User model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              # Authentication routes
│   │   └── users.py             # User management routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Auth business logic
│   │   └── user_service.py      # User business logic
│   └── utils/
│       ├── __init__.py
│       ├── auth.py              # Auth decorators
│       └── responses.py         # Response helpers
├── migrations/                   # Database migrations
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_users.py
├── run.py                        # Application entry point
├── requirements.txt              # Dependencies
├── .env.example                  # Environment variables template
└── README.md                     # Project documentation
```

## Implementation Guide

### Step 1: Project Setup

```bash
# Create project directory
mkdir -p backend/app/{models,routes,services,utils}
mkdir -p backend/tests
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Create requirements.txt
cat > requirements.txt << EOF
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
Flask-CORS==4.0.0
PyJWT==2.8.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
EOF

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

```python
# app/config.py
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://localhost/flask_dev'
    SQLALCHEMY_ECHO = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'postgresql://localhost/flask_test'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    @classmethod
    def init_app(cls, app):
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

### Step 3: Extensions

```python
# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS

db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
```

### Step 4: Models

```python
# app/models/user.py
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

# app/models/__init__.py
from app.models.user import User

__all__ = ['User']
```

### Step 5: Services

```python
# app/services/auth_service.py
import jwt
from datetime import datetime, timedelta
from flask import current_app
from app.models import User

def create_token(user):
    payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def authenticate_user(email, password):
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        return user
    return None

# app/services/user_service.py
from app.models import User
from app.extensions import db

def get_all_users(page=1, per_page=20):
    pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
    return pagination.items, pagination.total

def get_user_by_id(user_id):
    return User.query.get(user_id)

def create_user(data):
    user = User(email=data['email'], name=data.get('name', ''))
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return user

def update_user(user_id, data):
    user = User.query.get(user_id)
    if not user:
        return None
    
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        user.email = data['email']
    
    db.session.commit()
    return user

def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return False
    
    db.session.delete(user)
    db.session.commit()
    return True
```

### Step 6: Authentication Utilities

```python
# app/utils/auth.py
from functools import wraps
from flask import request, jsonify, g
from app.services.auth_service import verify_token
from app.models import User

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function

def require_admin(f):
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        if g.current_user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated_function
```

### Step 7: Routes

```python
# app/routes/auth.py
from flask import Blueprint, request, jsonify
from app.services.auth_service import create_token, authenticate_user
from app.services.user_service import create_user
from app.models import User

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    user = create_user(data)
    token = create_token(user)
    
    return jsonify({'token': token, 'user': user.to_dict()}), 201

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = authenticate_user(data['email'], data['password'])
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = create_token(user)
    return jsonify({'token': token, 'user': user.to_dict()})

# app/routes/users.py
from flask import Blueprint, request, jsonify, g
from app.utils.auth import require_auth, require_admin
from app.services.user_service import get_all_users, get_user_by_id, update_user, delete_user

bp = Blueprint('users', __name__)

@bp.route('', methods=['GET'])
@require_admin
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users, total = get_all_users(page, per_page)
    
    return jsonify({
        'users': [u.to_dict() for u in users],
        'pagination': {'page': page, 'per_page': per_page, 'total': total}
    })

@bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    return jsonify(g.current_user.to_dict())

@bp.route('/me', methods=['PUT'])
@require_auth
def update_current_user():
    data = request.get_json()
    user = update_user(g.current_user.id, data)
    return jsonify(user.to_dict())

@bp.route('/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    if g.current_user.role != 'admin' and g.current_user.id != user_id:
        return jsonify({'error': 'Forbidden'}), 403
    
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict())

@bp.route('/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user_route(user_id):
    if not delete_user(user_id):
        return jsonify({'error': 'User not found'}), 404
    
    return '', 204
```

### Step 8: Application Factory

```python
# app/__init__.py
from flask import Flask
from app.config import config
from app.extensions import db, migrate, cors

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.users import bp as users_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    # Health check
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    return app
```

### Step 9: Entry Point

```python
# run.py
import os
from app import create_app

config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
```

### Step 10: Environment Variables

```bash
# .env.example
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEV_DATABASE_URL=postgresql://localhost/flask_dev
DATABASE_URL=postgresql://localhost/flask_prod
```

## Running the Project

```bash
# Set up database
createdb flask_dev

# Initialize migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run development server
python run.py

# Or use Flask CLI
export FLASK_APP=run.py
flask run
```

## Testing the API

```bash
# Register user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","name":"John Doe"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Get current user (requires token)
curl -X GET http://localhost:5000/api/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Update current user
curl -X PUT http://localhost:5000/api/users/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe"}'
```

## Production Deployment

### Using Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

### Docker Ready

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:create_app('production')"]
```

## Success Criteria

Your project is complete when:

- ✅ All authentication endpoints work
- ✅ JWT tokens are generated and validated
- ✅ Users can only access their own data
- ✅ Admins can access all data
- ✅ Passwords are hashed
- ✅ Proper error responses with status codes
- ✅ Database migrations work
- ✅ Code follows clean architecture (routes → services → models)
- ✅ Environment-based configuration works
- ✅ Application runs with Gunicorn

## Extensions

After completing the base project, add:

1. **Email verification** on registration
2. **Password reset** functionality
3. **Rate limiting** on login endpoint
4. **Refresh tokens** for better security
5. **User profiles** with additional fields
6. **Pagination** for user list
7. **Filtering and sorting** for user list
8. **Unit tests** for all endpoints
9. **API documentation** (Swagger/OpenAPI)
10. **Docker Compose** setup with PostgreSQL

## Conclusion

This final project integrates everything learned:
- Flask fundamentals and architecture
- Routing and request/response handling
- Blueprints for modular organization
- Error handling and logging
- JWT authentication and authorization
- Flask extensions (SQLAlchemy, Migrate, CORS)

**You now have a production-ready Flask backend foundation!**

---

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [JWT.io](https://jwt.io/)
- [RESTful API Design](https://restfulapi.net/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

**Congratulations on completing the Flask Backend Tutorial!**
