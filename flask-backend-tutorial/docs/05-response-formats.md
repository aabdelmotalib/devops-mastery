# Module 5: Response Formats

## JSON Responses

JSON is the standard response format for modern APIs. Flask provides `jsonify()` for creating JSON responses.

### Basic JSON Responses

```python
from flask import jsonify

@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = {'id': user_id, 'email': 'user@example.com', 'name': 'John Doe'}
    return jsonify(user)
```

### jsonify() vs dict

```python
# Modern Flask (2.2+) - Both work
@app.route('/data1')
def data1():
    return {'key': 'value'}  # Automatically converted to JSON

@app.route('/data2')
def data2():
    return jsonify({'key': 'value'})  # Explicit JSON response
```

**Differences:**
- `jsonify()` sets `Content-Type: application/json` header
- `jsonify()` handles edge cases (dates, decimals) better
- Dict return is convenient but `jsonify()` is more explicit

**Best practice:** Use `jsonify()` for consistency and clarity.

### Complex JSON Structures

```python
@app.route('/api/dashboard')
def dashboard():
    return jsonify({
        'user': {
            'id': 1,
            'email': 'user@example.com',
            'profile': {
                'name': 'John Doe',
                'avatar': 'https://example.com/avatar.jpg'
            }
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
