# Module 3: Routing and Views

## Route Decorators

Routes map URLs to Python functions. Flask provides the `@app.route()` decorator for this purpose.

### Basic Routing

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    """Root endpoint"""
    return {'message': 'Welcome to the API'}

@app.route('/about')
def about():
    """About endpoint"""
    return {'version': '1.0.0', 'name': 'My API'}
```

### HTTP Methods

By default, routes only respond to GET requests. Specify methods explicitly:

```python
from flask import request

@app.route('/users', methods=['GET'])
def list_users():
    """List all users"""
    return {'users': []}

@app.route('/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.get_json()
    return {'id': 1, 'email': data['email']}, 201

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Update existing user"""
    data = request.get_json()
    return {'id': user_id, 'updated': True}

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete user"""
    return '', 204
```

### Multiple Methods on One Route

```python
@app.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
def user_detail(user_id):
    """Handle multiple methods on same endpoint"""
    if request.method == 'GET':
        return {'id': user_id, 'email': 'user@example.com'}
    
    elif request.method == 'PUT':
        data = request.get_json()
        return {'id': user_id, 'updated': True}
    
    elif request.method == 'DELETE':
        return '', 204
```

**When to use:**
- RESTful resource endpoints
- Reduces code duplication for shared logic

**When NOT to use:**
- When methods have significantly different logic
- Makes code harder to test
- Better to use separate routes with blueprints

## URL Parameters and Converters

### Path Parameters

```python
@app.route('/users/<user_id>')
def get_user(user_id):
    """user_id is a string by default"""
    return {'id': user_id, 'type': type(user_id).__name__}
    # Returns: {'id': '123', 'type': 'str'}
```

### Built-in Converters

Flask provides several URL converters:

```python
@app.route('/users/<int:user_id>')
def get_user(user_id):
    """user_id is converted to integer"""
    return {'id': user_id, 'type': type(user_id).__name__}
    # Returns: {'id': 123, 'type': 'int'}

@app.route('/posts/<int:post_id>/comments/<int:comment_id>')
def get_comment(post_id, comment_id):
    """Multiple parameters"""
    return {'post_id': post_id, 'comment_id': comment_id}

@app.route('/files/<path:filepath>')
def get_file(filepath):
    """Path converter accepts slashes"""
    # /files/documents/2024/report.pdf
    # filepath = 'documents/2024/report.pdf'
    return {'filepath': filepath}

@app.route('/tags/<uuid:tag_id>')
def get_tag(tag_id):
    """UUID converter validates UUID format"""
    return {'tag_id': str(tag_id)}

@app.route('/percentage/<float:value>')
def calculate(value):
    """Float converter"""
    return {'value': value, 'doubled': value * 2}
```

**Available converters:**
- `string`: Default, accepts any text without slashes
- `int`: Accepts positive integers
- `float`: Accepts floating point values
- `path`: Like string but accepts slashes
- `uuid`: Accepts UUID strings

### Custom Converters

```python
from werkzeug.routing import BaseConverter

class SlugConverter(BaseConverter):
    """Custom converter for URL slugs"""
    regex = r'[a-z0-9]+(?:-[a-z0-9]+)*'

# Register converter
app.url_map.converters['slug'] = SlugConverter

@app.route('/posts/<slug:post_slug>')
def get_post_by_slug(post_slug):
    """Only accepts valid slugs: my-post-title"""
    return {'slug': post_slug}
```

**Real-world use case:**

```python
class DateConverter(BaseConverter):
    """Convert YYYY-MM-DD to date object"""
    regex = r'\d{4}-\d{2}-\d{2}'
    
    def to_python(self, value):
        from datetime import datetime
        return datetime.strptime(value, '%Y-%m-%d').date()
    
    def to_url(self, value):
        return value.strftime('%Y-%m-%d')

app.url_map.converters['date'] = DateConverter

@app.route('/reports/<date:start_date>/<date:end_date>')
def get_reports(start_date, end_date):
    """Automatically converts to date objects"""
    # start_date and end_date are datetime.date objects
    days = (end_date - start_date).days
    return {'start': str(start_date), 'end': str(end_date), 'days': days}
```

### Query Parameters

Query parameters are accessed via `request.args`:

```python
from flask import request

@app.route('/search')
def search():
    """
    /search?q=flask&page=2&limit=20
    """
    query = request.args.get('q', '')  # Default to empty string
    page = request.args.get('page', 1, type=int)  # Convert to int
    limit = request.args.get('limit', 10, type=int)
    
    return {
        'query': query,
        'page': page,
        'limit': limit,
        'results': []
    }

@app.route('/filter')
def filter_items():
    """
    /filter?tags=python&tags=flask&tags=api
    """
    tags = request.args.getlist('tags')  # Get list of values
    return {'tags': tags}
```

## RESTful Routing Patterns

### Resource-Based URLs

RESTful APIs organize endpoints around resources:

```python
# Users resource
GET    /api/users           # List all users
POST   /api/users           # Create user
GET    /api/users/123       # Get specific user
PUT    /api/users/123       # Update user (full)
PATCH  /api/users/123       # Update user (partial)
DELETE /api/users/123       # Delete user

# Nested resources
GET    /api/users/123/posts        # Get user's posts
POST   /api/users/123/posts        # Create post for user
GET    /api/users/123/posts/456    # Get specific post
DELETE /api/users/123/posts/456    # Delete user's post
```

### Implementation Example

```python
from flask import Blueprint, request, jsonify

# Create blueprint for users resource
users_bp = Blueprint('users', __name__, url_prefix='/api/users')

@users_bp.route('', methods=['GET'])
def list_users():
    """GET /api/users"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    
    # Pagination logic here
    users = []  # Fetch from database
    
    return jsonify({
        'users': users,
        'page': page,
        'total': 0
    })

@users_bp.route('', methods=['POST'])
def create_user():
    """POST /api/users"""
    data = request.get_json()
    
    # Validation and creation logic
    user = {'id': 1, 'email': data['email']}
    
    return jsonify(user), 201

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """GET /api/users/123"""
    # Fetch user from database
    user = {'id': user_id, 'email': 'user@example.com'}
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user)

@users_bp.route('/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """PUT /api/users/123"""
    data = request.get_json()
    
    # Update logic
    user = {'id': user_id, 'email': data['email']}
    
    return jsonify(user)

@users_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """DELETE /api/users/123"""
    # Delete logic
    return '', 204

# Nested resource: user posts
@users_bp.route('/<int:user_id>/posts', methods=['GET'])
def get_user_posts(user_id):
    """GET /api/users/123/posts"""
    posts = []  # Fetch user's posts
    return jsonify({'posts': posts})

@users_bp.route('/<int:user_id>/posts', methods=['POST'])
def create_user_post(user_id):
    """POST /api/users/123/posts"""
    data = request.get_json()
    post = {'id': 1, 'user_id': user_id, 'title': data['title']}
    return jsonify(post), 201
```

### URL Design Best Practices

**Good:**
```
GET    /api/users
GET    /api/users/123
POST   /api/users
GET    /api/users/123/orders
```

**Bad:**
```
GET    /api/getUsers           # Don't use verbs
GET    /api/user/123           # Use plural
POST   /api/createUser         # HTTP method defines action
GET    /api/users/123/getOrders # Redundant verb
```

## Route Organization with Blueprints

### Why Blueprints?

As applications grow, organizing routes becomes critical. Blueprints provide:

1. **Modular structure**: Group related routes
2. **URL prefixes**: Namespace your API
3. **Reusability**: Register same blueprint multiple times
4. **Team collaboration**: Different developers work on different blueprints

### Blueprint Structure

```python
# app/routes/users.py
from flask import Blueprint, request, jsonify

bp = Blueprint('users', __name__)

@bp.route('', methods=['GET'])
def list_users():
    return jsonify({'users': []})

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify({'id': user_id})

# app/__init__.py
def create_app():
    app = Flask(__name__)
    
    from app.routes.users import bp as users_bp
    app.register_blueprint(users_bp, url_prefix='/api/users')
    
    return app
```

**Result:**
- `GET /api/users` → `list_users()`
- `GET /api/users/123` → `get_user(123)`

### Multiple Blueprints

```python
# app/routes/auth.py
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    return {'token': 'abc123'}

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return {'message': 'Logged out'}

# app/routes/products.py
from flask import Blueprint

products_bp = Blueprint('products', __name__)

@products_bp.route('', methods=['GET'])
def list_products():
    return {'products': []}

# app/__init__.py
def create_app():
    app = Flask(__name__)
    
    from app.routes.auth import auth_bp
    from app.routes.products import products_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(products_bp, url_prefix='/api/products')
    
    return app
```

**Result:**
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/products`

## Advanced Routing Techniques

### Dynamic URL Building

```python
from flask import url_for

@app.route('/users/<int:user_id>')
def get_user(user_id):
    return {'id': user_id}

# Build URLs programmatically
with app.test_request_context():
    url = url_for('get_user', user_id=123)
    # Returns: '/users/123'
    
    url = url_for('get_user', user_id=123, _external=True)
    # Returns: 'http://localhost:5000/users/123'
```

**Why use `url_for`:**
- URLs change? Update route, not every hardcoded URL
- Automatic URL encoding
- Works with blueprints

### Trailing Slashes

```python
@app.route('/users/')  # WITH trailing slash
def list_users():
    return {'users': []}

# /users/ → 200 OK
# /users  → 308 Redirect to /users/

@app.route('/about')  # WITHOUT trailing slash
def about():
    return {'version': '1.0'}

# /about  → 200 OK
# /about/ → 404 Not Found
```

**Best practice for APIs:**
- Be consistent
- Prefer WITHOUT trailing slash for APIs
- WITH trailing slash for web pages (traditional)

### Subdomain Routing

```python
app.config['SERVER_NAME'] = 'example.com'

@app.route('/', subdomain='api')
def api_index():
    """Responds to api.example.com"""
    return {'message': 'API v1'}

@app.route('/', subdomain='admin')
def admin_index():
    """Responds to admin.example.com"""
    return {'message': 'Admin panel'}
```

### Route Registration Order

```python
# Order matters!

@app.route('/users/me')  # Specific route first
def get_current_user():
    return {'id': 'current'}

@app.route('/users/<username>')  # Generic route after
def get_user(username):
    return {'username': username}

# /users/me → get_current_user()
# /users/john → get_user('john')
```

**If reversed:**
```python
@app.route('/users/<username>')  # This catches everything
def get_user(username):
    return {'username': username}

@app.route('/users/me')  # Never reached!
def get_current_user():
    return {'id': 'current'}

# /users/me → get_user('me')  # Wrong!
```

## Common Routing Mistakes

### Mistake 1: Not Specifying Methods

```python
# BAD - Accepts all methods
@app.route('/users')
def list_users():
    return {'users': []}

# POST /users → 200 OK (should be 405)
```

**Fix:**
```python
@app.route('/users', methods=['GET'])
def list_users():
    return {'users': []}

# POST /users → 405 Method Not Allowed
```

### Mistake 2: Inconsistent URL Patterns

```python
# BAD - Inconsistent
GET  /getUsers
POST /user/create
GET  /user-detail/123
```

**Fix:**
```python
# GOOD - RESTful
GET  /users
POST /users
GET  /users/123
```

### Mistake 3: Overly Nested Resources

```python
# BAD - Too deep
GET /api/v1/companies/123/departments/456/teams/789/members/012
```

**Fix:**
```python
# GOOD - Flatten when possible
GET /api/v1/team-members/012
GET /api/v1/teams/789/members  # If context needed
```

### Mistake 4: Using Verbs in URLs

```python
# BAD
POST /api/createUser
GET  /api/deleteUser/123
```

**Fix:**
```python
# GOOD - HTTP method is the verb
POST   /api/users
DELETE /api/users/123
```

## Summary

Flask routing provides flexible URL mapping with:
- Route decorators for simple cases
- URL converters for type safety
- Blueprints for modular organization
- RESTful patterns for API design

**Key principles:**
- Use HTTP methods correctly (GET, POST, PUT, DELETE)
- Design resource-based URLs
- Organize routes with blueprints
- Be consistent with URL patterns
- Avoid verbs in URLs (use HTTP methods instead)

---

## Practice Exercises

### Multiple Choice Questions

1. What happens when you access `/users` if the route is defined as `@app.route('/users/')`?
   a) 404 Not Found
   b) 200 OK
   c) 308 Permanent Redirect to /users/
   d) 500 Internal Server Error

2. Which URL converter should you use for `/posts/my-first-post-title`?
   a) `<string:slug>`
   b) `<path:slug>`
   c) Custom converter with regex
   d) `<slug:slug>` (built-in)

3. In RESTful API design, which HTTP method should be used to partially update a resource?
   a) POST
   b) PUT
   c) PATCH
   d) UPDATE

4. What is the correct way to get multiple values for the same query parameter (`?tags=python&tags=flask`)?
   a) `request.args.get('tags')`
   b) `request.args.getlist('tags')`
   c) `request.args['tags']`
   d) `request.query_params.get('tags')`

5. Why should specific routes be registered before generic ones?
   a) Performance optimization
   b) Flask matches routes in order, first match wins
   c) Required by HTTP specification
   d) Better for debugging

### Practical Tasks

**Task 1: Build a RESTful API**

Create a complete RESTful API for a blog system with:

1. **Posts resource:**
   - List posts (with pagination: `?page=1&limit=10`)
   - Create post
   - Get single post
   - Update post
   - Delete post

2. **Comments resource (nested under posts):**
   - List comments for a post
   - Create comment on a post
   - Delete comment

3. **Search endpoint:**
   - Search posts by title: `/api/search?q=flask`
   - Filter by tags: `/api/search?tags=python&tags=api`

Use blueprints to organize routes.

**Task 2: Custom Converter**

Create a custom URL converter for semantic versioning:
- Pattern: `v1.2.3` or `v2.0.0-beta`
- Route: `/api/<semver:version>/users`
- The converter should parse the version into a dictionary: `{'major': 1, 'minor': 2, 'patch': 3, 'prerelease': None}`

### Debugging Scenario

You've built a Flask API with the following routes:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/users/<user_id>')
def get_user(user_id):
    return {'id': user_id, 'name': 'John'}

@app.route('/api/users/me')
def get_current_user():
    return {'id': 'current', 'name': 'Current User'}

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.get_json()
    return {'id': 1, 'email': data['email']}, 201
```

**Problems reported:**

1. `GET /api/users/me` returns `{'id': 'me', 'name': 'John'}` instead of current user
2. `POST /api/users` returns 405 Method Not Allowed
3. `GET /api/users/123` works but `GET /api/users/abc` also works (should only accept integers)

**Questions:**
1. What causes each problem?
2. How would you fix each issue?
3. What Flask routing concepts are violated?
4. Provide the corrected code.

---

**Next Module**: [Request Handling](04-request-handling.md)
