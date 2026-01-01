# Module 9: Authentication & Authorization

## Session vs Token-Based Authentication

Understanding the difference is crucial for API design.

### Session-Based Authentication

**How it works:**
1. User logs in with credentials
2. Server creates session, stores in database/Redis
3. Server sends session ID in cookie
4. Client sends cookie with each request
5. Server validates session ID

**Characteristics:**
- Stateful (server stores session data)
- Cookie-based
- Good for traditional web apps
- Not ideal for APIs (mobile, SPAs)

```python
from flask import session

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = authenticate(data['email'], data['password'])
    
    if user:
        session['user_id'] = user.id
        return jsonify({'message': 'Logged in'})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.get(session['user_id'])
    return jsonify(user.to_dict())
```

### Token-Based Authentication (JWT)

**How it works:**
1. User logs in with credentials
2. Server generates JWT token
3. Client stores token (localStorage, memory)
4. Client sends token in Authorization header
5. Server validates token signature

**Characteristics:**
- Stateless (no server-side storage)
- Header-based
- Perfect for APIs
- Scalable (no session storage needed)

```python
import jwt
from datetime import datetime, timedelta

SECRET_KEY = 'your-secret-key'

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = authenticate(data['email'], data['password'])
    
    if user:
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, SECRET_KEY, algorithm='HS256')
        
        return jsonify({'token': token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/profile')
def profile():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        return jsonify(user.to_dict())
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
```

**For APIs: Use JWT (token-based)**

## JWT Implementation

### Installing Dependencies

```bash
pip install PyJWT
```

### JWT Service

```python
# app/services/auth_service.py
import jwt
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.security import check_password_hash
from app.models import User

def create_token(user):
    """Generate JWT token for user"""
    payload = {
        'user_id': user.id,
        'email': user.email,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

def verify_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token

def authenticate_user(email, password):
    """Authenticate user with email and password"""
    user = User.query.filter_by(email=email).first()
    
    if user and check_password_hash(user.password, password):
        return user
    
    return None
```

### Authentication Routes

```python
# app/routes/auth.py
from flask import Blueprint, request, jsonify
from app.services.auth_service import create_token, authenticate_user
from app.models import User
from app.extensions import db
from werkzeug.security import generate_password_hash

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    # Validation
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create user
    user = User(
        email=data['email'],
        password=generate_password_hash(data['password']),
        name=data.get('name', '')
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Generate token
    token = create_token(user)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name
        }
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    """Login user"""
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    # Authenticate
    user = authenticate_user(data['email'], data['password'])
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Generate token
    token = create_token(user)
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.id,
            'email': user.email,
            'name': user.name
        }
    })

@bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh JWT token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    from app.services.auth_service import verify_token
    payload = verify_token(token)
    
    if not payload:
        return jsonify({'error': 'Invalid or expired token'}), 401
    
    # Get user and create new token
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    new_token = create_token(user)
    
    return jsonify({'token': new_token})
```

## Password Hashing

**NEVER store passwords in plain text!**

### Using Werkzeug

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hashing password
hashed = generate_password_hash('user_password')
# Result: pbkdf2:sha256:260000$...

# Verifying password
is_valid = check_password_hash(hashed, 'user_password')
# Result: True
```

### User Model with Password Hashing

```python
# app/models/user.py
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def set_password(self, password):
        """Hash and set password"""
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password, password)
    
    def to_dict(self):
        """Convert to dictionary (exclude password!)"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat()
        }
```

## Route Protection with Decorators

### Authentication Decorator

```python
# app/utils/auth.py
from functools import wraps
from flask import request, jsonify, g
from app.services.auth_service import verify_token
from app.models import User

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401
        
        # Extract token
        try:
            token = auth_header.split(' ')[1]  # "Bearer <token>"
        except IndexError:
            return jsonify({'error': 'Invalid authorization header'}), 401
        
        # Verify token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Store user in g for access in route
        g.current_user = user
        
        return f(*args, **kwargs)
    
    return decorated_function
```

### Using the Decorator

```python
# app/routes/users.py
from flask import Blueprint, jsonify, g
from app.utils.auth import require_auth

bp = Blueprint('users', __name__)

@bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user"""
    return jsonify(g.current_user.to_dict())

@bp.route('/me', methods=['PUT'])
@require_auth
def update_current_user():
    """Update current user"""
    data = request.get_json()
    
    if 'name' in data:
        g.current_user.name = data['name']
    
    db.session.commit()
    
    return jsonify(g.current_user.to_dict())
```

## Authorization (Role-Based Access Control)

### User Model with Roles

```python
# app/models/user.py
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    role = db.Column(db.String(20), default='user')  # user, admin, moderator
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    def has_role(self, role):
        """Check if user has specific role"""
        return self.role == role
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
```

### Role-Based Decorators

```python
# app/utils/auth.py
def require_role(role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        @require_auth  # Also requires authentication
        def decorated_function(*args, **kwargs):
            if not g.current_user.has_role(role):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        if not g.current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function
```

### Using Role-Based Authorization

```python
# app/routes/admin.py
from flask import Blueprint, jsonify
from app.utils.auth import require_admin
from app.models import User

bp = Blueprint('admin', __name__)

@bp.route('/users', methods=['GET'])
@require_admin
def list_all_users():
    """Admin-only: List all users"""
    users = User.query.all()
    return jsonify({'users': [u.to_dict() for u in users]})

@bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """Admin-only: Delete user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return '', 204
```

## Refresh Tokens

For better security, use short-lived access tokens with refresh tokens.

### Implementation

```python
# app/services/auth_service.py
def create_tokens(user):
    """Create access and refresh tokens"""
    access_token = jwt.encode({
        'user_id': user.id,
        'type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=15)  # Short-lived
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    refresh_token = jwt.encode({
        'user_id': user.id,
        'type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=30)  # Long-lived
    }, current_app.config['SECRET_KEY'], algorithm='HS256')
    
    return access_token, refresh_token

@bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token using refresh token"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400
    
    try:
        payload = jwt.decode(
            refresh_token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        
        if payload.get('type') != 'refresh':
            return jsonify({'error': 'Invalid token type'}), 401
        
        user = User.query.get(payload['user_id'])
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Create new access token
        access_token = create_token(user)
        
        return jsonify({'access_token': access_token})
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Refresh token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid refresh token'}), 401
```

## Security Best Practices

### 1. Use HTTPS in Production

```python
# Force HTTPS
@app.before_request
def before_request():
    if not request.is_secure and not app.debug:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)
```

### 2. Secure Secret Keys

```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable not set")
```

### 3. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login logic
    pass
```

### 4. Token Blacklisting (for logout)

```python
# Store blacklisted tokens in Redis
import redis

redis_client = redis.Redis()

def blacklist_token(token):
    """Add token to blacklist"""
    payload = verify_token(token)
    if payload:
        exp = payload['exp']
        ttl = exp - int(datetime.utcnow().timestamp())
        redis_client.setex(f"blacklist:{token}", ttl, "1")

def is_token_blacklisted(token):
    """Check if token is blacklisted"""
    return redis_client.exists(f"blacklist:{token}")

@bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """Logout user"""
    token = request.headers.get('Authorization').split(' ')[1]
    blacklist_token(token)
    return jsonify({'message': 'Logged out successfully'})
```

## Summary

Authentication and authorization are critical for API security:
- Use JWT for stateless, scalable authentication
- Always hash passwords with werkzeug
- Protect routes with decorators
- Implement role-based access control
- Use refresh tokens for better security
- Follow security best practices (HTTPS, rate limiting, etc.)

**Key principles:**
- Never store plain text passwords
- Use short-lived access tokens
- Validate tokens on every protected request
- Implement proper authorization (not just authentication)
- Use HTTPS in production

---

## Practice Exercises

### Multiple Choice Questions

1. What's the main advantage of JWT over session-based auth for APIs?
   a) More secure
   b) Stateless (no server-side storage)
   c) Faster
   d) Easier to implement

2. What should you use to hash passwords in Flask?
   a) hashlib.md5()
   b) base64.encode()
   c) werkzeug.security.generate_password_hash()
   d) jwt.encode()

3. Where should JWT tokens be sent in API requests?
   a) Query parameter
   b) Request body
   c) Authorization header
   d) Cookie

4. What's the difference between authentication and authorization?
   a) No difference
   b) Authentication = who you are, Authorization = what you can do
   c) Authorization = who you are, Authentication = what you can do
   d) Authentication is for APIs, Authorization is for web apps

5. Why use refresh tokens?
   a) To make tokens longer
   b) To allow short-lived access tokens with long-lived refresh tokens
   c) To encrypt tokens
   d) To store tokens in database

### Practical Tasks

**Task 1: Complete Auth System**

Build a complete authentication system:

1. User registration with email/password
2. Login endpoint returning JWT
3. Password reset functionality
4. Email verification
5. Refresh token implementation
6. Logout with token blacklisting
7. Protected routes using decorators
8. Role-based access control (user, admin)

**Task 2: Secure API**

Implement security features:

1. Rate limiting on login endpoint
2. Password strength validation
3. Account lockout after failed attempts
4. HTTPS enforcement
5. CORS configuration
6. Security headers
7. Token expiration handling

### Debugging Scenario

Your authentication system has security issues:

```python
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.password == data['password']:
        token = jwt.encode({'user_id': user.id}, 'secret', algorithm='HS256')
        return jsonify({'token': token})
    
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin/users')
def admin_users():
    token = request.args.get('token')
    payload = jwt.decode(token, 'secret', algorithms=['HS256'])
    
    users = User.query.all()
    return jsonify({'users': [u.__dict__ for u in users]})
```

**Security issues:**

1. Passwords stored in plain text
2. Hardcoded secret key
3. No token expiration
4. Token sent in query parameter
5. No authorization check
6. Password exposed in response

**Questions:**
1. Identify all security vulnerabilities
2. How would you fix each issue?
3. What authentication best practices are violated?
4. Provide corrected, secure code

---

**Next Module**: [Flask Extensions](10-flask-extensions.md)
