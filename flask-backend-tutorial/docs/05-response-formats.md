# Module 5: Response Formats

## Introduction to Response Formatting

A response is what your Flask application sends back to the client after processing a request. It consists of:
- **Status code** (200, 404, 500, etc.)
- **Headers** (metadata about the response)
- **Body** (the actual data)

The format you use depends on your client's needs:
- **JSON**: for API endpoints (most common)
- **HTML**: for web pages
- **XML**: for legacy systems
- **CSV/Text**: for downloads and reports
- **Binary**: for images, files

This module focuses on JSON responses, which is the standard for modern web APIs.

### Why JSON?

✅ **Human-readable**: Easy to understand when viewing
✅ **Machine-parseable**: Easy for code to parse
✅ **Language-independent**: Works with any programming language
✅ **Lightweight**: Smaller than XML
✅ **Web standard**: Supported natively by browsers and APIs

---

## JSON Responses: The Standard

JSON is the standard response format for modern APIs. Flask provides the `jsonify()` function for creating JSON responses with proper headers.

### Basic JSON Responses

```python
from flask import jsonify

@app.route('/users/<int:user_id>')
def get_user(user_id):
    """Return a single user as JSON"""
    user = {
        'id': user_id,
        'email': 'user@example.com',
        'name': 'John Doe',
        'active': True
    }
    return jsonify(user)
```

**What jsonify() does:**
1. Takes a Python dictionary
2. Converts it to JSON string
3. Sets `Content-Type: application/json` header
4. Sets proper response status code (200 by default)
5. Returns a Flask Response object

**Testing:**

```bash
curl http://localhost:5000/users/1
# Response headers:
# Content-Type: application/json
# 
# Response body:
# {"id":1,"email":"user@example.com","name":"John Doe","active":true}
```

### jsonify() vs Returning Dict Directly

Modern Flask (2.2+) is smart about responses:

```python
# Both of these work identically:

@app.route('/data1')
def data1():
    return {'key': 'value'}  # Flask auto-converts to JSON

@app.route('/data2')
def data2():
    return jsonify({'key': 'value'})  # Explicit JSON response
```

**When to use what:**

```python
# ✅ Use jsonify() when:
# - You want to be explicit about JSON format
# - You need fine-grained control
# - Working with older Flask (< 2.2)
# - Your team values consistency

@app.route('/api/v1/users')
def get_users():
    return jsonify({'users': []})

# ✅ Use dict return when:
# - Quick prototyping
# - Simple endpoints
# - Working with Flask 2.2+

@app.route('/api/v2/users')
def get_users_v2():
    return {'users': []}
```

**Best practice:** Use `jsonify()` for clarity and consistency.

### Complex JSON Structures

Real API responses often have nested data and multiple fields:

```python
from flask import jsonify
from datetime import datetime

@app.route('/api/dashboard')
def dashboard():
    """
    Return complex nested JSON with multiple data types.
    This demonstrates a typical API response structure.
    """
    return jsonify({
        'status': 'success',  # String
        'timestamp': datetime.now().isoformat(),  # DateTime string
        'user': {  # Nested object
            'id': 1,
            'email': 'user@example.com',
            'profile': {  # Doubly nested
                'name': 'John Doe',
                'avatar': 'https://example.com/avatar.jpg',
                'verified': True  # Boolean
            },
            'created_at': '2024-01-01T10:00:00Z'
        },
        'posts': [  # Array of objects
            {
                'id': 101,
                'title': 'First Post',
                'views': 1250  # Integer
            },
            {
                'id': 102,
                'title': 'Second Post',
                'views': 3400
            }
        ],
        'statistics': {  # Numbers
            'total_posts': 2,
            'total_views': 4650,
            'average_views': 2325.5  # Float
        },
        'metadata': {  # Additional info
            'page': 1,
            'page_size': 10,
            'total_pages': 1
        }
    })
```

**Testing complex response:**

```bash
curl http://localhost:5000/api/dashboard | python -m json.tool
# -m json.tool: Pretty-print the JSON output

# Output:
# {
#   "status": "success",
#   "timestamp": "2024-01-11T15:45:23.123456",
#   "user": {
#     "id": 1,
#     "email": "user@example.com",
#     ...
#   },
#   ...
# }
```

### Handling Special Data Types in JSON

JSON has limited data types. Python has more. Here's how to handle them:

```python
from flask import jsonify
from datetime import datetime, date
from decimal import Decimal
import json

class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for non-standard types"""
    
    def default(self, obj):
        # Handle datetime objects
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # Handle Decimal (for precise money values)
        if isinstance(obj, Decimal):
            return float(obj)
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        # Fallback to default encoder
        return super().default(obj)

# Configure Flask to use custom encoder
app.json_encoder = CustomJSONEncoder

@app.route('/products/<int:product_id>')
def get_product(product_id):
    """Example with special data types"""
    return jsonify({
        'id': product_id,
        'name': 'Widget',
        'price': Decimal('19.99'),  # Custom encoder handles this
        'created': datetime.now(),   # Custom encoder handles this
        'tags': {'featured', 'new'}, # Set converted to list
        'available': True
    })
```

---

## Status Codes: Communicating Success or Failure

HTTP status codes tell the client what happened with their request:

```
1xx - Information (rare in APIs)
2xx - Success (request succeeded)
3xx - Redirection (resource moved)
4xx - Client Error (client did something wrong)
5xx - Server Error (server did something wrong)
```

### Setting Status Codes

```python
from flask import jsonify

# ============= 2xx Success Responses =============

# 200 OK - Default, used for successful GET, PUT, PATCH
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    return jsonify({'id': user_id, 'name': 'Alice'})  # 200 by default

# 201 Created - Used for successful POST (resource created)
@app.route('/users', methods=['POST'])
def create_user():
    new_user = {'id': 123, 'name': 'Bob'}
    return jsonify(new_user), 201

# 204 No Content - Used for successful DELETE
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    return '', 204  # No body for 204

# ============= 4xx Client Error Responses =============

# 400 Bad Request - Invalid request data
@app.route('/users', methods=['POST'])
def create_user_validated():
    data = request.get_json()
    if not data.get('email'):
        return jsonify({'error': 'Email is required'}), 400
    return jsonify(data), 201

# 401 Unauthorized - Authentication failed
@app.route('/admin/users')
def admin_users():
    auth = request.headers.get('Authorization')
    if not auth or not validate_token(auth):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify({'users': []})

# 403 Forbidden - Authenticated but not allowed
@app.route('/admin/settings')
def admin_settings():
    user = get_current_user()  # Authenticated
    if user.role != 'admin':  # But not admin
        return jsonify({'error': 'Forbidden'}), 403
    return jsonify({'settings': {}})

# 404 Not Found - Resource doesn't exist
@app.route('/users/<int:user_id>')
def get_user_safe(user_id):
    user = find_user_in_db(user_id)
    if not user:
        return jsonify({'error': f'User {user_id} not found'}), 404
    return jsonify(user)

# 409 Conflict - Resource conflict (e.g., duplicate)
@app.route('/users', methods=['POST'])
def create_user_unique():
    data = request.get_json()
    if user_exists_by_email(data['email']):
        return jsonify({'error': 'Email already exists'}), 409
    return jsonify(data), 201

# 422 Unprocessable Entity - Valid format, but logic error
@app.route('/transfers', methods=['POST'])
def transfer_money():
    data = request.get_json()
    if data['amount'] > account_balance():
        return jsonify({'error': 'Insufficient funds'}), 422
    return jsonify({'transferred': True}), 200

# ============= 5xx Server Error Responses =============

# 500 Internal Server Error - Server crashed/exception
@app.route('/buggy')
def buggy_endpoint():
    result = 1 / 0  # ❌ Oops! Division by zero
    # Returns 500 with error message

# 503 Service Unavailable - Server down or overloaded
@app.route('/health')
def health_check():
    if database_is_down():
        return jsonify({'error': 'Database unavailable'}), 503
    return jsonify({'status': 'healthy'})
```

### Common Status Code Patterns

```python
# ============= List Endpoint =============
@app.route('/products')
def list_products():
    """
    GET /products
    Return: 200 OK with list
    """
    products = get_all_products()  # Could be empty list
    return jsonify({
        'products': products,
        'total': len(products)
    }), 200

# ============= Get Single Resource =============
@app.route('/products/<int:product_id>')
def get_product(product_id):
    """
    GET /products/123
    Return: 200 OK if found, 404 if not found
    """
    product = find_product(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product), 200

# ============= Create Resource =============
@app.route('/products', methods=['POST'])
def create_product():
    """
    POST /products with product data
    Return: 201 Created if successful, 400 if invalid
    """
    data = request.get_json()
    
    errors = validate_product_data(data)
    if errors:
        return jsonify({'errors': errors}), 400
    
    product = save_product_to_db(data)
    return jsonify(product), 201

# ============= Update Resource =============
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """
    PUT /products/123 with updated data
    Return: 200 OK if updated, 404 if not found
    """
    product = find_product(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.get_json()
    updated = update_product_in_db(product_id, data)
    return jsonify(updated), 200

# ============= Delete Resource =============
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """
    DELETE /products/123
    Return: 204 No Content if deleted, 404 if not found
    """
    product = find_product(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    delete_product_from_db(product_id)
    return '', 204  # 204 No Content
```

---

## Response Envelopes: Wrapping Your Data

Some APIs wrap responses in a standard envelope for consistency:

```python
# Without envelope (simple)
{
    "id": 1,
    "name": "Alice"
}

# With envelope (more structure)
{
    "success": true,
    "data": {
        "id": 1,
        "name": "Alice"
    },
    "timestamp": "2024-01-11T15:45:00Z"
}
```

**Implementation:**

```python
from flask import jsonify
from datetime import datetime

@app.route('/api/v1/users/<int:user_id>')
def get_user_enveloped(user_id):
    """Return response with standard envelope"""
    user = find_user(user_id)
    
    if not user:
        return jsonify({
            'success': False,
            'error': f'User {user_id} not found',
            'timestamp': datetime.now().isoformat()
        }), 404
    
    return jsonify({
        'success': True,
        'data': user,
        'timestamp': datetime.now().isoformat()
    }), 200
```

**Advantages:**
- Consistent structure for all responses
- Always have error field for failures
- Can add metadata (timestamp, request ID)

**Disadvantages:**
- Extra nesting (one more level to parse)
- Not standard REST (increases API complexity)

**Modern best practice:** Use status codes instead of success envelope. Status codes already tell you if it succeeded.
        },
        'stats': {
            'posts': 42,
            'followers': 150,
            'following': 89
        },
        'recent_activity': [
            {'type': 'post', 'timestamp': '2024-01-15T10:30:00Z'},
            {'type': 'comment', 'timestamp': '2024-01-15T09:15:00Z'}
        ]
    })
```

## HTTP Status Codes

Status codes communicate the result of a request. Using them correctly is crucial for API design.

### Success Codes (2xx)

```python
@app.route('/users', methods=['GET'])
def list_users():
    """200 OK - Standard success response"""
    return jsonify({'users': []}), 200

@app.route('/users', methods=['POST'])
def create_user():
    """201 Created - Resource created successfully"""
    user = {'id': 1, 'email': 'new@example.com'}
    return jsonify(user), 201

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """200 OK - Resource updated"""
    return jsonify({'id': user_id, 'updated': True}), 200

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """204 No Content - Deleted successfully, no body"""
    return '', 204

@app.route('/users/<int:user_id>/activate', methods=['POST'])
def activate_user(user_id):
    """202 Accepted - Request accepted, processing asynchronously"""
    return jsonify({'message': 'Activation queued'}), 202
```

### Client Error Codes (4xx)

```python
@app.route('/users/<int:user_id>')
def get_user(user_id):
    """404 Not Found - Resource doesn't exist"""
    user = None  # Fetch from database
    if not user:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(user)

@app.route('/admin/users')
def admin_users():
    """401 Unauthorized - Authentication required"""
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'error': 'Authentication required'}), 401
    
    # Validate token...
    return jsonify({'users': []})

@app.route('/admin/settings')
def admin_settings():
    """403 Forbidden - Authenticated but not authorized"""
    user_role = 'user'  # Get from token
    if user_role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    
    return jsonify({'settings': {}})

@app.route('/users', methods=['POST'])
def create_user():
    """400 Bad Request - Invalid input"""
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400
    
    return jsonify({'id': 1}), 201

@app.route('/api/v1/old-endpoint')
def old_endpoint():
    """410 Gone - Resource permanently removed"""
    return jsonify({
        'error': 'This endpoint has been removed',
        'message': 'Use /api/v2/new-endpoint instead'
    }), 410

@app.route('/users', methods=['PATCH'])
def patch_user():
    """422 Unprocessable Entity - Validation failed"""
    data = request.get_json()
    errors = validate_user(data)
    if errors:
        return jsonify({'errors': errors}), 422
    
    return jsonify({'updated': True})

@app.route('/rate-limited')
def rate_limited():
    """429 Too Many Requests - Rate limit exceeded"""
    # Check rate limit
    if exceeded_rate_limit():
        return jsonify({
            'error': 'Rate limit exceeded',
            'retry_after': 60
        }), 429
    
    return jsonify({'data': []})
```

### Server Error Codes (5xx)

```python
@app.route('/data')
def get_data():
    """500 Internal Server Error - Unexpected error"""
    try:
        # Some operation that might fail
        result = risky_operation()
        return jsonify(result)
    except Exception as e:
        app.logger.error(f"Error in get_data: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/external-api')
def proxy_external():
    """502 Bad Gateway - Upstream service failed"""
    try:
        response = requests.get('https://external-api.com/data', timeout=5)
        return jsonify(response.json())
    except requests.RequestException:
        return jsonify({'error': 'External service unavailable'}), 502

@app.route('/maintenance')
def maintenance():
    """503 Service Unavailable - Temporary downtime"""
    if app.config.get('MAINTENANCE_MODE'):
        return jsonify({
            'error': 'Service temporarily unavailable',
            'message': 'Scheduled maintenance in progress'
        }), 503
    
    return jsonify({'status': 'ok'})
```

### Status Code Reference

| Code | Meaning | When to Use |
|------|---------|-------------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid input, malformed request |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Authenticated but not authorized |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict (e.g., duplicate email) |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 502 | Bad Gateway | Upstream service failed |
| 503 | Service Unavailable | Temporary downtime |

## Error Response Standardization

Consistent error responses improve API usability.

### Standard Error Format

```python
def error_response(message, status_code, details=None):
    """Standard error response format"""
    payload = {
        'error': {
            'message': message,
            'status_code': status_code
        }
    }
    
    if details:
        payload['error']['details'] = details
    
    return jsonify(payload), status_code

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    if not data:
        return error_response('Request body is required', 400)
    
    if 'email' not in data:
        return error_response(
            'Validation failed',
            422,
            details={'email': 'Email is required'}
        )
    
    return jsonify({'id': 1}), 201
```

### Validation Error Format

```python
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    errors = {}
    
    if not data.get('email'):
        errors['email'] = 'Email is required'
    elif '@' not in data['email']:
        errors['email'] = 'Invalid email format'
    
    if not data.get('password'):
        errors['password'] = 'Password is required'
    elif len(data['password']) < 8:
        errors['password'] = 'Password must be at least 8 characters'
    
    if errors:
        return jsonify({
            'error': 'Validation failed',
            'fields': errors
        }), 422
    
    return jsonify({'id': 1}), 201
```

### Error Response with Request ID

```python
import uuid
from flask import g

@app.before_request
def before_request():
    g.request_id = str(uuid.uuid4())

def error_response(message, status_code, details=None):
    payload = {
        'error': {
            'message': message,
            'status_code': status_code,
            'request_id': g.request_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    }
    
    if details:
        payload['error']['details'] = details
    
    return jsonify(payload), status_code
```

## Response Headers

Headers provide metadata about the response.

### Common Response Headers

```python
from flask import make_response

@app.route('/data')
def get_data():
    data = {'key': 'value'}
    response = make_response(jsonify(data))
    
    # Caching
    response.headers['Cache-Control'] = 'public, max-age=3600'
    
    # CORS
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    # Security
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Custom headers
    response.headers['X-API-Version'] = '1.0'
    response.headers['X-Request-ID'] = g.request_id
    
    return response
```

### Setting Headers with after_request

```python
@app.after_request
def after_request(response):
    """Add headers to all responses"""
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # API version
    response.headers['X-API-Version'] = '1.0'
    
    # Request ID for tracing
    if hasattr(g, 'request_id'):
        response.headers['X-Request-ID'] = g.request_id
    
    return response
```

### Content Negotiation

```python
@app.route('/data')
def get_data():
    data = {'key': 'value'}
    
    # Check Accept header
    accept = request.headers.get('Accept', 'application/json')
    
    if 'application/json' in accept:
        return jsonify(data)
    elif 'text/csv' in accept:
        # Return CSV format
        return 'key,value\nkey,value\n', 200, {'Content-Type': 'text/csv'}
    else:
        return jsonify({'error': 'Unsupported media type'}), 415
```

## Pagination Responses

Standard pagination format for list endpoints.

### Offset-Based Pagination

```python
@app.route('/users')
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Validate
    if page < 1 or per_page < 1 or per_page > 100:
        return jsonify({'error': 'Invalid pagination parameters'}), 400
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Fetch data (pseudo-code)
    # users = User.query.limit(per_page).offset(offset).all()
    # total = User.query.count()
    users = []
    total = 0
    
    return jsonify({
        'data': users,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page
        }
    })
```

### Cursor-Based Pagination

```python
@app.route('/posts')
def list_posts():
    cursor = request.args.get('cursor')
    limit = request.args.get('limit', 20, type=int)
    
    # Fetch data after cursor
    # posts = Post.query.filter(Post.id > cursor).limit(limit + 1).all()
    posts = []
    
    has_more = len(posts) > limit
    if has_more:
        posts = posts[:limit]
    
    next_cursor = posts[-1]['id'] if posts and has_more else None
    
    return jsonify({
        'data': posts,
        'pagination': {
            'next_cursor': next_cursor,
            'has_more': has_more
        }
    })
```

## Response Formatting Best Practices

### Consistent Field Naming

```python
# GOOD - snake_case
{
    "user_id": 1,
    "first_name": "John",
    "created_at": "2024-01-15T10:30:00Z"
}

# BAD - Mixed conventions
{
    "userId": 1,
    "first_name": "John",
    "CreatedAt": "2024-01-15T10:30:00Z"
}
```

### Timestamp Format

```python
from datetime import datetime

@app.route('/posts/<int:post_id>')
def get_post(post_id):
    return jsonify({
        'id': post_id,
        'title': 'My Post',
        'created_at': datetime.utcnow().isoformat() + 'Z',  # ISO 8601
        'updated_at': '2024-01-15T10:30:00Z'
    })
```

### Null vs Missing Fields

```python
# GOOD - Omit null fields
{
    "id": 1,
    "email": "user@example.com"
    # No "phone" field if null
}

# ACCEPTABLE - Include null for optional fields
{
    "id": 1,
    "email": "user@example.com",
    "phone": null
}

# BAD - Empty strings for null
{
    "id": 1,
    "email": "user@example.com",
    "phone": ""
}
```

### Envelope Pattern

```python
# With envelope (consistent structure)
@app.route('/users/<int:user_id>')
def get_user(user_id):
    return jsonify({
        'success': True,
        'data': {
            'id': user_id,
            'email': 'user@example.com'
        }
    })

# Without envelope (simpler, preferred for REST)
@app.route('/users/<int:user_id>')
def get_user(user_id):
    return jsonify({
        'id': user_id,
        'email': 'user@example.com'
    })
```

**Recommendation:** Skip envelope for REST APIs, use HTTP status codes instead.

## Summary

Response formatting is critical for API usability:
- Use JSON as the standard format
- Apply HTTP status codes correctly
- Standardize error response format
- Include appropriate headers
- Implement consistent pagination
- Follow naming conventions

**Key principles:**
- Be consistent across all endpoints
- Use appropriate status codes
- Provide clear error messages
- Include request IDs for debugging
- Document your response formats

---

## Practice Exercises

### Multiple Choice Questions

1. What HTTP status code should be returned when a resource is successfully created?
   a) 200 OK
   b) 201 Created
   c) 204 No Content
   d) 202 Accepted

2. What's the difference between 401 and 403 status codes?
   a) No difference, both mean unauthorized
   b) 401 = not authenticated, 403 = not authorized
   c) 401 = client error, 403 = server error
   d) 403 = not authenticated, 401 = not authorized

3. Which status code should be used for validation errors?
   a) 400 Bad Request
   b) 422 Unprocessable Entity
   c) 500 Internal Server Error
   d) 409 Conflict

4. What should be returned when a DELETE request succeeds?
   a) 200 OK with deleted resource
   b) 201 Created
   c) 204 No Content
   d) 202 Accepted

5. What's the recommended timestamp format for JSON APIs?
   a) Unix timestamp (1234567890)
   b) ISO 8601 (2024-01-15T10:30:00Z)
   c) Human readable (Jan 15, 2024)
   d) MM/DD/YYYY HH:MM:SS

### Practical Tasks

**Task 1: Standardize Error Responses**

Create a comprehensive error handling system:

1. Define a standard error response format that includes:
   - Error message
   - Status code
   - Request ID
   - Timestamp
   - Field-level validation errors (when applicable)

2. Create helper functions for common error scenarios:
   - `not_found(resource_name)`
   - `validation_error(field_errors)`
   - `unauthorized()`
   - `forbidden()`
   - `internal_error()`

3. Implement these in a sample API with user CRUD operations

**Task 2: Implement Pagination**

Create a `/products` endpoint with:

1. Offset-based pagination (page, per_page)
2. Response includes:
   - Data array
   - Pagination metadata (page, per_page, total, pages)
   - Links to next/previous pages
3. Validate pagination parameters
4. Handle edge cases (page beyond total, negative values)

### Debugging Scenario

You've built an API that returns inconsistent responses:

```python
@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        return {'id': user.id, 'email': user.email}
    return {'error': 'Not found'}

@app.route('/posts/<int:post_id>')
def get_post(post_id):
    post = Post.query.get(post_id)
    if not post:
        return jsonify({'message': 'Post not found'}), 404
    return jsonify(post.to_dict()), 200
```

**Problems:**

1. Client reports: "When user doesn't exist, I get 200 status but error message"
2. Error response format is inconsistent between endpoints
3. No way to trace errors (no request ID)
4. Timestamps in responses are in different formats

**Questions:**
1. What's wrong with the `get_user` endpoint?
2. How would you standardize error responses?
3. How would you add request tracing?
4. Provide corrected code with consistent response format

---

**Next Module**: [Templates and Static Files](06-templates-static.md)
