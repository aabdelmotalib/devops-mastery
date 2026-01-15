# Module 7: Flask Blueprints

## Introduction: Organizing Large Applications

As your Flask application grows, putting all routes and logic in a single file becomes unmanageable. Flask Blueprints are the solution—they allow you to organize your application into logical modules (auth, users, products, etc.) with separate files and folders.

Think of blueprints like this:
- **Without blueprints**: One gigantic phone book with all numbers mixed together
- **With blueprints**: Organized phone book with separate sections (businesses, residences, services)

Blueprints enable:
- **Modularity**: Each feature in its own file
- **Team collaboration**: Different developers work on different features
- **Reusability**: Blueprints can be used in multiple apps
- **Testing**: Test each blueprint independently
- **Scalability**: Easy to add new features without touching existing code

---

## Why Blueprints Are Essential in Real Apps

As Flask applications grow, organizing code becomes critical. Blueprints provide modular structure and separation of concerns.

### The Problem: Monolithic app.py

```python
# ❌ BAD - Everything in one file (grows to 500+ lines)
# app.py
from flask import Flask, request, jsonify

app = Flask(__name__)

# Auth routes (10 functions)
@app.route('/auth/login', methods=['POST'])
def login():
    pass

@app.route('/auth/logout', methods=['POST'])
def logout():
    pass

# User routes (8 functions)
@app.route('/users', methods=['GET'])
def list_users():
    pass

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    pass

# Product routes (12 functions)
@app.route('/products', methods=['GET'])
def list_products():
    pass

# ... 150 more lines ...
# This file grows unmaintainable
```

**Problems:**
- Single file with 200+ lines of code
- Hard to find specific endpoints
- Changes in one feature might break others
- Impossible for team to work in parallel
- Testing specific features is difficult
- Mixing concerns (auth, users, products all together)

### The Solution: Blueprints

```python
# ✅ GOOD - Organized with blueprints

# Directory structure
app/
├── __init__.py              # App factory
├── blueprints/
│   ├── auth.py              # Authentication routes
│   ├── users.py             # User management routes
│   └── products.py          # Product routes
└── models/
    ├── user.py
    └── product.py
```

**auth.py - Authentication blueprint:**

```python
from flask import Blueprint, request, jsonify

# Create a blueprint (like a mini Flask app)
auth_bp = Blueprint(
    'auth',              # Blueprint name (for url_for)
    __name__,            # Module name
    url_prefix='/auth'   # All routes prefixed with /auth
)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    # Validate credentials...
    return jsonify({'token': 'abc123'}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    # Invalidate token...
    return jsonify({'message': 'Logged out'}), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    # Issue new token...
    return jsonify({'token': 'new123'}), 200
```

**users.py - Users blueprint:**

```python
from flask import Blueprint, request, jsonify

users_bp = Blueprint(
    'users',
    __name__,
    url_prefix='/users'
)

@users_bp.route('', methods=['GET'])
def list_users():
    users = fetch_users()
    return jsonify({'users': users})

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = fetch_user(user_id)
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(user)

@users_bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    user = save_user(data)
    return jsonify(user), 201
```

**products.py - Products blueprint:**

```python
from flask import Blueprint, request, jsonify

products_bp = Blueprint(
    'products',
    __name__,
    url_prefix='/api/products'
)

@products_bp.route('', methods=['GET'])
def list_products():
    products = fetch_products()
    return jsonify({'products': products})

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = fetch_product(product_id)
    if not product:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(product)
```

**__init__.py - App factory:**

```python
from flask import Flask
from app.blueprints import auth, users, products

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(auth.auth_bp)
    app.register_blueprint(users.users_bp)
    app.register_blueprint(products.products_bp)
    
    return app
```

**Results:**
- Each feature is in its own file
- Easy to navigate to specific feature
- No dependencies between features
- Team can work on features in parallel
- Easy to test each blueprint independently

**Routes created:**

```
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
GET    /users
GET    /users/123
POST   /users
GET    /api/products
GET    /api/products/123
```
    pass

# Product routes
@app.route('/products', methods=['GET'])
def list_products():
    pass

# ... hundreds more routes
```

**Problems:**
- Single file becomes thousands of lines
- Hard to navigate and maintain
- Team conflicts (everyone editing same file)
- No logical grouping
- Difficult to test individual modules

### Solution: Blueprints

Blueprints organize routes into logical modules:

```
app/routes/
├── __init__.py
├── auth.py        # Authentication routes
├── users.py       # User management
├── products.py    # Product catalog
└── orders.py      # Order processing
```

## Creating Blueprints

### Basic Blueprint

```python
# app/routes/users.py
from flask import Blueprint, jsonify, request

# Create blueprint
bp = Blueprint('users', __name__)

@bp.route('', methods=['GET'])
def list_users():
    """GET /api/users"""
    return jsonify({'users': []})

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """GET /api/users/123"""
    return jsonify({'id': user_id})

@bp.route('', methods=['POST'])
def create_user():
    """POST /api/users"""
    data = request.get_json()
    return jsonify({'id': 1}), 201
```

### Registering Blueprints

```python
# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    from app.routes.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    
    return app
```

**Result:**
- `/api/users` → `list_users()`
- `/api/users/123` → `get_user(123)`
- `/api/auth/login` → `login()`

## Blueprint Organization Patterns

### Pattern 1: Resource-Based

Organize by data resources:

```python
# app/routes/users.py
bp = Blueprint('users', __name__)

@bp.route('', methods=['GET', 'POST'])
@bp.route('/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def user_routes(user_id=None):
    pass

# app/routes/products.py
bp = Blueprint('products', __name__)

@bp.route('', methods=['GET', 'POST'])
@bp.route('/<int:product_id>', methods=['GET', 'PUT', 'DELETE'])
def product_routes(product_id=None):
    pass
```

### Pattern 2: Feature-Based

Organize by application features:

```python
# app/routes/auth.py - Authentication feature
bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    pass

@bp.route('/logout', methods=['POST'])
def logout():
    pass

@bp.route('/refresh', methods=['POST'])
def refresh_token():
    pass

# app/routes/profile.py - User profile feature
bp = Blueprint('profile', __name__)

@bp.route('/me', methods=['GET'])
def get_profile():
    pass

@bp.route('/me', methods=['PUT'])
def update_profile():
    pass

@bp.route('/me/avatar', methods=['POST'])
def upload_avatar():
    pass
```

### Pattern 3: API Versioning

Organize by API version:

```python
# app/routes/v1/__init__.py
from flask import Blueprint

v1_bp = Blueprint('api_v1', __name__)

from app.routes.v1 import users, products

# app/routes/v2/__init__.py
from flask import Blueprint

v2_bp = Blueprint('api_v2', __name__)

from app.routes.v2 import users, products

# app/__init__.py
def create_app():
    app = Flask(__name__)
    
    from app.routes.v1 import v1_bp
    from app.routes.v2 import v2_bp
    
    app.register_blueprint(v1_bp, url_prefix='/api/v1')
    app.register_blueprint(v2_bp, url_prefix='/api/v2')
    
    return app
```

## Advanced Blueprint Features

### Blueprint-Specific Error Handlers

```python
# app/routes/users.py
from flask import Blueprint, jsonify

bp = Blueprint('users', __name__)

@bp.errorhandler(404)
def user_not_found(error):
    """Handle 404 errors in users blueprint"""
    return jsonify({'error': 'User not found'}), 404

@bp.errorhandler(ValueError)
def handle_value_error(error):
    """Handle ValueError in users blueprint"""
    return jsonify({'error': str(error)}), 400

@bp.route('/<int:user_id>')
def get_user(user_id):
    if user_id < 0:
        raise ValueError('Invalid user ID')
    # Fetch user...
```

### Blueprint Before/After Request Hooks

```python
# app/routes/admin.py
from flask import Blueprint, g, request
import time

bp = Blueprint('admin', __name__)

@bp.before_request
def before_admin_request():
    """Run before each admin request"""
    g.start_time = time.time()
    
    # Check admin authentication
    if not is_admin(request.headers.get('Authorization')):
        return jsonify({'error': 'Admin access required'}), 403

@bp.after_request
def after_admin_request(response):
    """Run after each admin request"""
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        response.headers['X-Admin-Response-Time'] = f"{elapsed:.3f}s"
    return response

@bp.route('/users')
def admin_users():
    """Only accessible to admins"""
    return jsonify({'users': []})
```

### Blueprint URL Processors

```python
# app/routes/tenants.py
from flask import Blueprint, g

bp = Blueprint('tenants', __name__, url_prefix='/<tenant_id>')

@bp.url_value_preprocessor
def get_tenant(endpoint, values):
    """Extract tenant_id from URL"""
    g.tenant_id = values.pop('tenant_id', None)

@bp.route('/users')
def list_tenant_users():
    """GET /acme-corp/users"""
    tenant_id = g.tenant_id
    # Fetch users for this tenant
    return jsonify({'tenant': tenant_id, 'users': []})

@bp.route('/settings')
def tenant_settings():
    """GET /acme-corp/settings"""
    tenant_id = g.tenant_id
    return jsonify({'tenant': tenant_id, 'settings': {}})
```

## Real-World Blueprint Structure

### Complete Example

```python
# app/routes/auth.py
from flask import Blueprint, request, jsonify
from app.services.auth_service import authenticate_user, create_token
from app.models import User

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    data = request.get_json()
    
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Email and password required'}), 400
    
    user = authenticate_user(data['email'], data['password'])
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = create_token(user)
    return jsonify({'token': token, 'user': user.to_dict()}), 200

@bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.get_json()
    
    # Validation
    required = ['email', 'password', 'name']
    if not all(field in data for field in required):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    
    # Create user
    from app.services.user_service import create_user
    user = create_user(data)
    
    return jsonify({'id': user.id, 'email': user.email}), 201

@bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (client should discard token)"""
    # With JWT, logout is client-side
    # Optionally, add token to blacklist
    return jsonify({'message': 'Logged out successfully'}), 200
```

```python
# app/routes/users.py
from flask import Blueprint, request, jsonify
from app.services.user_service import get_all_users, get_user_by_id, update_user, delete_user
from app.utils.auth import require_auth

bp = Blueprint('users', __name__)

@bp.route('', methods=['GET'])
@require_auth
def list_users():
    """List all users with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    users, total = get_all_users(page, per_page)
    
    return jsonify({
        'users': [u.to_dict() for u in users],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total
        }
    })

@bp.route('/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    """Get specific user"""
    user = get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict())

@bp.route('/<int:user_id>', methods=['PUT'])
@require_auth
def update_user_route(user_id):
    """Update user"""
    data = request.get_json()
    user = update_user(user_id, data)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict())

@bp.route('/<int:user_id>', methods=['DELETE'])
@require_auth
def delete_user_route(user_id):
    """Delete user"""
    success = delete_user(user_id)
    if not success:
        return jsonify({'error': 'User not found'}), 404
    
    return '', 204
```

### Registration in Application Factory

```python
# app/__init__.py
from flask import Flask

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Load config
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    from app.extensions import db, migrate, cors
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    return app

def register_blueprints(app):
    """Register all blueprints"""
    from app.routes.auth import bp as auth_bp
    from app.routes.users import bp as users_bp
    from app.routes.products import bp as products_bp
    from app.routes.orders import bp as orders_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    app.register_blueprint(orders_bp, url_prefix='/api/orders')
```

## Blueprint Best Practices

### 1. One Blueprint Per File

```python
# GOOD
# app/routes/users.py - Only user routes
# app/routes/products.py - Only product routes

# BAD
# app/routes/api.py - All routes mixed together
```

### 2. Use URL Prefixes

```python
# GOOD
app.register_blueprint(users_bp, url_prefix='/api/users')

# BAD - Repeat prefix in every route
@bp.route('/api/users')
@bp.route('/api/users/<int:user_id>')
```

### 3. Keep Routes Thin

```python
# GOOD - Delegate to service layer
@bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    user = user_service.create(data)
    return jsonify(user.to_dict()), 201

# BAD - Business logic in route
@bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    # Validation logic
    # Password hashing
    # Database operations
    # Email sending
    # All in route handler - BAD!
```

### 4. Consistent Naming

```python
# Blueprint name
bp = Blueprint('users', __name__)

# File name: users.py
# URL prefix: /api/users
# Service: user_service.py
# Model: user.py
```

## Common Blueprint Mistakes

### Mistake 1: Circular Imports

```python
# BAD
# app/__init__.py
from app.routes.users import bp

# app/routes/users.py
from app import app  # Circular import!
```

**Fix:** Use application factory pattern (shown earlier).

### Mistake 2: Not Using URL Prefixes

```python
# BAD
@bp.route('/api/users')
@bp.route('/api/users/<int:user_id>')

# GOOD
# Register with prefix
app.register_blueprint(bp, url_prefix='/api/users')

# Routes
@bp.route('')
@bp.route('/<int:user_id>')
```

### Mistake 3: Mixing Concerns

```python
# BAD - Auth and users in same blueprint
bp = Blueprint('api', __name__)

@bp.route('/login')
def login():
    pass

@bp.route('/users')
def list_users():
    pass

# GOOD - Separate blueprints
auth_bp = Blueprint('auth', __name__)
users_bp = Blueprint('users', __name__)
```

## Summary

Blueprints are essential for production Flask applications:
- Organize routes into logical modules
- Enable team collaboration
- Improve code maintainability
- Support API versioning
- Provide modular error handling

**Key principles:**
- One blueprint per feature/resource
- Use URL prefixes
- Keep routes thin (delegate to services)
- Follow consistent naming conventions
- Use application factory pattern

---

## Practice Exercises

### Multiple Choice Questions

1. What is the primary purpose of Flask blueprints?
   a) Improve application performance
   b) Organize routes into modular components
   c) Enable database migrations
   d) Handle authentication

2. Where should business logic be placed?
   a) In blueprint route handlers
   b) In service layer
   c) In models
   d) In __init__.py

3. How do you register a blueprint with a URL prefix?
   a) `@bp.route('/api/users')`
   b) `bp.url_prefix = '/api/users'`
   c) `app.register_blueprint(bp, url_prefix='/api/users')`
   d) `Blueprint('users', url_prefix='/api/users')`

4. What runs before each request to a specific blueprint?
   a) `@app.before_request`
   b) `@bp.before_request`
   c) `@bp.before_app_request`
   d) `@bp.pre_request`

5. Which blueprint organization pattern is best for API versioning?
   a) Resource-based
   b) Feature-based
   c) Version-based (v1, v2 blueprints)
   d) File-based

### Practical Tasks

**Task 1: Build Modular API**

Create a complete API with blueprints:

1. **Auth blueprint** (`/api/auth`):
   - POST /login
   - POST /register
   - POST /logout

2. **Users blueprint** (`/api/users`):
   - GET / (list with pagination)
   - POST / (create)
   - GET /<id>
   - PUT /<id>
   - DELETE /<id>

3. **Posts blueprint** (`/api/posts`):
   - GET / (list)
   - POST / (create)
   - GET /<id>
   - PUT /<id>
   - DELETE /<id>

Use service layer for business logic, proper error handling, and authentication decorators.

**Task 2: Multi-Tenant API**

Create a multi-tenant API where each tenant has isolated data:

- URL pattern: `/<tenant_id>/users`, `/<tenant_id>/products`
- Use `url_value_preprocessor` to extract tenant_id
- Store tenant_id in `g` object
- Ensure all queries filter by tenant

### Debugging Scenario

You've organized your Flask app with blueprints but encountering issues:

```python
# app/__init__.py
from flask import Flask
from app.routes.users import bp as users_bp
from app.routes.products import bp as products_bp

app = Flask(__name__)
app.register_blueprint(users_bp)
app.register_blueprint(products_bp)

# app/routes/users.py
from flask import Blueprint
from app import app  # Import app

bp = Blueprint('users', __name__)

@bp.route('/users')
def list_users():
    return {'users': []}

# app/routes/products.py
from flask import Blueprint

bp = Blueprint('products', __name__)

@bp.route('/products')
def list_products():
    return {'products': []}
```

**Problems:**

1. ImportError: cannot import name 'app' from partially initialized module
2. Routes `/users` and `/products` return 404
3. Want to add `/api` prefix to all routes
4. Need to add authentication check to all user routes

**Questions:**
1. What causes the ImportError?
2. Why do routes return 404?
3. How would you add `/api` prefix?
4. How would you add authentication to user routes only?
5. Provide corrected code using application factory pattern.

---

**Next Module**: [Error Handling](08-error-handling.md)
