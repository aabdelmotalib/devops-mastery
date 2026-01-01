# Module 4: Request Handling

## The Request Object

The `request` object contains all information about the incoming HTTP request. It's available in the request context.

```python
from flask import request

@app.route('/debug')
def debug_request():
    return {
        'method': request.method,
        'path': request.path,
        'url': request.url,
        'base_url': request.base_url,
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent')
    }
```

### Request Properties

```python
from flask import request

@app.route('/info')
def request_info():
    return {
        # URL information
        'url': request.url,                    # Full URL
        'base_url': request.base_url,          # URL without query string
        'path': request.path,                  # Path only: /info
        'full_path': request.full_path,        # Path + query: /info?key=value
        'script_root': request.script_root,    # Application mount point
        
        # HTTP method
        'method': request.method,              # GET, POST, PUT, DELETE, etc.
        
        # Client information
        'remote_addr': request.remote_addr,    # Client IP
        'scheme': request.scheme,              # http or https
        
        # Request metadata
        'is_json': request.is_json,            # Content-Type: application/json?
        'is_secure': request.is_secure,        # HTTPS?
    }
```

## Handling Headers

Headers contain metadata about the request.

### Reading Headers

```python
from flask import request

@app.route('/headers')
def show_headers():
    # Get specific header
    auth = request.headers.get('Authorization')
    content_type = request.headers.get('Content-Type')
    user_agent = request.headers.get('User-Agent')
    
    # Get all headers
    all_headers = dict(request.headers)
    
    return {
        'authorization': auth,
        'content_type': content_type,
        'user_agent': user_agent,
        'all_headers': all_headers
    }
```

### Common Headers in APIs

```python
@app.route('/api/data')
def get_data():
    # Authentication
    token = request.headers.get('Authorization')
    if not token or not token.startswith('Bearer '):
        return {'error': 'Missing or invalid token'}, 401
    
    # API versioning
    api_version = request.headers.get('X-API-Version', '1.0')
    
    # Content negotiation
    accept = request.headers.get('Accept', 'application/json')
    
    # Request ID for tracing
    request_id = request.headers.get('X-Request-ID')
    
    return {
        'data': [],
        'version': api_version,
        'request_id': request_id
    }
```

### Custom Headers

```python
@app.route('/custom')
def custom_headers():
    # Custom headers typically prefixed with X-
    tenant_id = request.headers.get('X-Tenant-ID')
    correlation_id = request.headers.get('X-Correlation-ID')
    
    if not tenant_id:
        return {'error': 'X-Tenant-ID header required'}, 400
    
    return {
        'tenant_id': tenant_id,
        'correlation_id': correlation_id
    }
```

## Handling JSON Data

JSON is the standard format for API communication.

### Reading JSON

```python
from flask import request, jsonify

@app.route('/users', methods=['POST'])
def create_user():
    # Check if request contains JSON
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400
    
    # Get JSON data
    data = request.get_json()
    
    # Access fields
    email = data.get('email')
    password = data.get('password')
    
    return {'id': 1, 'email': email}, 201
```

### JSON with Validation

```python
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Manual validation
    required_fields = ['email', 'password', 'name']
    missing = [field for field in required_fields if field not in data]
    
    if missing:
        return {
            'error': 'Missing required fields',
            'missing': missing
        }, 400
    
    # Type validation
    if not isinstance(data['email'], str):
        return {'error': 'Email must be a string'}, 400
    
    # Business validation
    if len(data['password']) < 8:
        return {'error': 'Password must be at least 8 characters'}, 400
    
    return {'id': 1, 'email': data['email']}, 201
```

### Handling Invalid JSON

```python
from flask import request
from json import JSONDecodeError

@app.route('/data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json(force=True)  # Parse even without Content-Type
    except (JSONDecodeError, TypeError):
        return {'error': 'Invalid JSON'}, 400
    
    return {'received': data}
```

## Handling Form Data

Form data is used for traditional HTML forms and file uploads.

### URL-Encoded Forms

```python
from flask import request

@app.route('/login', methods=['POST'])
def login():
    # Content-Type: application/x-www-form-urlencoded
    email = request.form.get('email')
    password = request.form.get('password')
    remember = request.form.get('remember', type=bool)
    
    return {
        'email': email,
        'remember': remember
    }
```

### Multipart Form Data (File Uploads)

```python
from flask import request
from werkzeug.utils import secure_filename
import os

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file is present
    if 'file' not in request.files:
        return {'error': 'No file provided'}, 400
    
    file = request.files['file']
    
    # Check if filename is empty
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    
    # Secure the filename
    filename = secure_filename(file.filename)
    
    # Save file
    upload_folder = '/tmp/uploads'
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return {
        'filename': filename,
        'size': os.path.getsize(filepath)
    }, 201
```

### File Upload with Validation

```python
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return {'error': 'No file provided'}, 400
    
    file = request.files['file']
    
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    
    # Validate file extension
    if not allowed_file(file.filename):
        return {
            'error': 'Invalid file type',
            'allowed': list(ALLOWED_EXTENSIONS)
        }, 400
    
    # Validate file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        return {
            'error': 'File too large',
            'max_size_mb': MAX_FILE_SIZE / (1024 * 1024)
        }, 400
    
    # Process file
    filename = secure_filename(file.filename)
    # Save or process file...
    
    return {'filename': filename, 'size': size}, 201
```

## Input Validation Strategies

### Manual Validation

```python
def validate_user_data(data):
    """Validate user creation data"""
    errors = {}
    
    # Required fields
    if not data.get('email'):
        errors['email'] = 'Email is required'
    elif '@' not in data['email']:
        errors['email'] = 'Invalid email format'
    
    if not data.get('password'):
        errors['password'] = 'Password is required'
    elif len(data['password']) < 8:
        errors['password'] = 'Password must be at least 8 characters'
    
    # Optional fields with validation
    if 'age' in data:
        try:
            age = int(data['age'])
            if age < 0 or age > 150:
                errors['age'] = 'Invalid age'
        except ValueError:
            errors['age'] = 'Age must be a number'
    
    return errors

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    errors = validate_user_data(data)
    if errors:
        return {'errors': errors}, 400
    
    # Create user...
    return {'id': 1, 'email': data['email']}, 201
```

### Validation with Decorators

```python
from functools import wraps
from flask import request

def validate_json(*expected_fields):
    """Decorator to validate JSON request data"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return {'error': 'Content-Type must be application/json'}, 400
            
            data = request.get_json()
            missing = [field for field in expected_fields if field not in data]
            
            if missing:
                return {
                    'error': 'Missing required fields',
                    'missing': missing
                }, 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route('/users', methods=['POST'])
@validate_json('email', 'password', 'name')
def create_user():
    data = request.get_json()
    # Data is guaranteed to have email, password, name
    return {'id': 1, 'email': data['email']}, 201
```

### Schema-Based Validation

```python
from typing import Dict, Any

class UserSchema:
    """Simple schema for user validation"""
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> tuple[bool, Dict[str, str]]:
        errors = {}
        
        # Email validation
        email = data.get('email', '').strip()
        if not email:
            errors['email'] = 'Email is required'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'Invalid email format'
        
        # Password validation
        password = data.get('password', '')
        if not password:
            errors['password'] = 'Password is required'
        elif len(password) < 8:
            errors['password'] = 'Password must be at least 8 characters'
        elif not any(c.isupper() for c in password):
            errors['password'] = 'Password must contain uppercase letter'
        elif not any(c.isdigit() for c in password):
            errors['password'] = 'Password must contain a number'
        
        # Name validation
        name = data.get('name', '').strip()
        if not name:
            errors['name'] = 'Name is required'
        elif len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters'
        
        return len(errors) == 0, errors

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    valid, errors = UserSchema.validate(data)
    if not valid:
        return {'errors': errors}, 400
    
    # Data is valid, create user
    return {'id': 1, 'email': data['email']}, 201
```

## Query String Parameters

### Basic Query Parameters

```python
from flask import request

@app.route('/search')
def search():
    # /search?q=flask&category=tutorial&page=2
    query = request.args.get('q', '')
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    
    return {
        'query': query,
        'category': category,
        'page': page
    }
```

### Multiple Values

```python
@app.route('/filter')
def filter_items():
    # /filter?tags=python&tags=flask&tags=api
    tags = request.args.getlist('tags')
    
    # /filter?ids=1&ids=2&ids=3
    ids = request.args.getlist('ids', type=int)
    
    return {
        'tags': tags,
        'ids': ids
    }
```

### Pagination Pattern

```python
@app.route('/items')
def list_items():
    # Default pagination values
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Validate pagination
    if page < 1:
        return {'error': 'Page must be >= 1'}, 400
    
    if per_page < 1 or per_page > 100:
        return {'error': 'per_page must be between 1 and 100'}, 400
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Fetch data (pseudo-code)
    # items = db.query().limit(per_page).offset(offset).all()
    items = []
    total = 0
    
    return {
        'items': items,
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page
    }
```

### Filtering and Sorting

```python
@app.route('/products')
def list_products():
    # Filtering
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    in_stock = request.args.get('in_stock', type=bool)
    
    # Sorting
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    
    # Validate sort parameters
    allowed_sort_fields = ['name', 'price', 'created_at']
    if sort_by not in allowed_sort_fields:
        return {
            'error': 'Invalid sort_by field',
            'allowed': allowed_sort_fields
        }, 400
    
    if order not in ['asc', 'desc']:
        return {'error': 'order must be asc or desc'}, 400
    
    # Build query (pseudo-code)
    filters = {
        'category': category,
        'min_price': min_price,
        'max_price': max_price,
        'in_stock': in_stock
    }
    
    return {
        'products': [],
        'filters': {k: v for k, v in filters.items() if v is not None},
        'sort': {'by': sort_by, 'order': order}
    }
```

## Request Lifecycle

Understanding the request lifecycle helps debug issues:

```
1. Client sends HTTP request
2. Web server (nginx) receives request
3. WSGI server (Gunicorn) creates environ dict
4. Flask creates request context
5. Before-request handlers run
6. Route handler executes
7. After-request handlers run
8. Response sent to client
9. Request context torn down
10. Teardown handlers run
```

### Before and After Request Hooks

```python
from flask import g
import time

@app.before_request
def before_request():
    """Runs before each request"""
    g.start_time = time.time()
    g.request_id = request.headers.get('X-Request-ID', 'unknown')

@app.after_request
def after_request(response):
    """Runs after each request"""
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
        response.headers['X-Request-ID'] = g.request_id
    
    return response

@app.teardown_request
def teardown_request(exception=None):
    """Runs after response is sent"""
    if exception:
        # Log exception
        app.logger.error(f"Request failed: {exception}")
```

## Common Request Handling Mistakes

### Mistake 1: Not Checking Content-Type

```python
# BAD
@app.route('/data', methods=['POST'])
def receive_data():
    data = request.get_json()  # May be None if not JSON
    email = data['email']  # TypeError if data is None
```

**Fix:**
```python
# GOOD
@app.route('/data', methods=['POST'])
def receive_data():
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400
    
    data = request.get_json()
    if not data:
        return {'error': 'Empty request body'}, 400
    
    email = data.get('email')
    if not email:
        return {'error': 'Email is required'}, 400
    
    return {'email': email}
```

### Mistake 2: Trusting User Input

```python
# BAD - SQL injection risk
@app.route('/users/<username>')
def get_user(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    # Execute query...
```

**Fix:**
```python
# GOOD - Use parameterized queries
@app.route('/users/<username>')
def get_user(username):
    user = User.query.filter_by(username=username).first()
    # ORM handles escaping
```

### Mistake 3: Not Validating File Uploads

```python
# BAD
@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    file.save(f'/uploads/{file.filename}')  # Path traversal risk!
```

**Fix:**
```python
# GOOD
from werkzeug.utils import secure_filename

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    if not file:
        return {'error': 'No file'}, 400
    
    filename = secure_filename(file.filename)
    file.save(f'/uploads/{filename}')
```

## Summary

Request handling in Flask involves:
- Understanding the `request` object and its properties
- Reading headers for authentication, versioning, and metadata
- Handling JSON data with proper validation
- Processing form data and file uploads securely
- Implementing robust input validation strategies
- Using query parameters for filtering and pagination

**Key principles:**
- Always validate input
- Never trust user data
- Check Content-Type before parsing
- Use secure_filename for file uploads
- Implement proper error handling

---

## Practice Exercises

### Multiple Choice Questions

1. What does `request.get_json()` return if Content-Type is not application/json?
   a) Empty dictionary {}
   b) None
   c) Raises exception
   d) Empty string ""

2. Which method should you use to get multiple values for the same query parameter?
   a) `request.args.get()`
   b) `request.args.getlist()`
   c) `request.args.all()`
   d) `request.query_params.get()`

3. What is the purpose of `secure_filename()`?
   a) Encrypt the filename
   b) Prevent path traversal attacks
   c) Validate file extension
   d) Generate unique filename

4. When do `@app.before_request` handlers run?
   a) Before Flask starts
   b) Before each request, before route handler
   c) After each request
   d) Only on first request

5. What should you check before calling `request.get_json()`?
   a) `request.method == 'POST'`
   b) `request.is_json`
   c) `request.content_type`
   d) Both b and c

### Practical Tasks

**Task 1: Build a File Upload API**

Create an endpoint that:
1. Accepts file uploads (images only: jpg, png, gif)
2. Validates file size (max 5MB)
3. Generates unique filename (UUID + original extension)
4. Stores file metadata in a dictionary
5. Returns file URL and metadata

Include proper error handling for all edge cases.

**Task 2: Implement Advanced Filtering**

Create a `/products` endpoint that supports:
1. Pagination (`?page=1&per_page=20`)
2. Filtering by multiple fields (`?category=electronics&min_price=100&max_price=500`)
3. Sorting (`?sort_by=price&order=asc`)
4. Search (`?q=laptop`)
5. Multiple category filter (`?categories=electronics&categories=computers`)

Return results with metadata (total count, pages, applied filters).

### Debugging Scenario

You've built an API endpoint that accepts JSON data:

```python
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    
    items = data['items']
    total = sum(item['price'] * item['quantity'] for item in items)
    
    order = {
        'id': 1,
        'items': items,
        'total': total
    }
    
    return order, 201
```

**Problems reported:**

1. Sometimes returns 500 error with "TypeError: 'NoneType' object is not subscriptable"
2. When sending `Content-Type: text/plain`, returns 500 error
3. When sending empty items array, returns 500 error
4. When items have missing 'price' or 'quantity', returns 500 error

**Questions:**
1. What causes each error?
2. How would you fix each issue?
3. What validation should be added?
4. Provide the corrected, production-ready code.

---

**Next Module**: [Response Formats](05-response-formats.md)
