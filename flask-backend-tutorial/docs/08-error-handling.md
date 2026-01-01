# Module 8: Error Handling

## Custom Error Handlers

Proper error handling is crucial for production APIs. Flask provides decorators to handle errors globally.

### Basic Error Handlers

```python
from flask import jsonify

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    app.logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors"""
    return jsonify({'error': 'Access forbidden'}), 403
```

### Exception-Based Error Handlers

```python
@app.errorhandler(ValueError)
def handle_value_error(error):
    """Handle ValueError exceptions"""
    return jsonify({'error': str(error)}), 400

@app.errorhandler(KeyError)
def handle_key_error(error):
    """Handle KeyError exceptions"""
    return jsonify({'error': f'Missing key: {str(error)}'}), 400

from werkzeug.exceptions import BadRequest

@app.errorhandler(BadRequest)
def handle_bad_request(error):
    """Handle bad request errors"""
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400
```

## Global Exception Handling

### Centralized Error Handler

```python
# app/errors.py
from flask import jsonify
from werkzeug.exceptions import HTTPException
import traceback

def register_error_handlers(app):
    """Register all error handlers"""
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle all HTTP exceptions"""
        response = {
            'error': error.name,
            'message': error.description,
            'status_code': error.code
        }
        return jsonify(response), error.code
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all uncaught exceptions"""
        app.logger.error(f"Unhandled exception: {error}")
        app.logger.error(traceback.format_exc())
        
        # Don't expose internal errors in production
        if app.config['DEBUG']:
            response = {
                'error': 'Internal Server Error',
                'message': str(error),
                'traceback': traceback.format_exc()
            }
        else:
            response = {
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred'
            }
        
        return jsonify(response), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({'error': 'Unprocessable Entity', 'message': str(error)}), 422
```

### Using Error Handlers

```python
# app/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    return app
```

## Custom Exception Classes

Define custom exceptions for specific error scenarios.

### Basic Custom Exceptions

```python
# app/exceptions.py
class APIException(Exception):
    """Base exception for API errors"""
    status_code = 500
    
    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        rv['status_code'] = self.status_code
        return rv

class ValidationError(APIException):
    """Validation error"""
    status_code = 422

class NotFoundError(APIException):
    """Resource not found"""
    status_code = 404

class UnauthorizedError(APIException):
    """Authentication required"""
    status_code = 401

class ForbiddenError(APIException):
    """Access forbidden"""
    status_code = 403

class ConflictError(APIException):
    """Resource conflict"""
    status_code = 409
```

### Registering Custom Exception Handlers

```python
# app/errors.py
from app.exceptions import APIException

def register_error_handlers(app):
    @app.errorhandler(APIException)
    def handle_api_exception(error):
        """Handle custom API exceptions"""
        response = error.to_dict()
        return jsonify(response), error.status_code
```

### Using Custom Exceptions

```python
# app/routes/users.py
from app.exceptions import NotFoundError, ValidationError, ConflictError
from app.models import User

@bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        raise NotFoundError(f'User {user_id} not found')
    
    return jsonify(user.to_dict())

@bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Validation
    if not data.get('email'):
        raise ValidationError('Email is required')
    
    # Check for duplicates
    if User.query.filter_by(email=data['email']).first():
        raise ConflictError('Email already exists')
    
    # Create user
    user = User(**data)
    db.session.add(user)
    db.session.commit()
    
    return jsonify(user.to_dict()), 201
```

## Production Logging

Logging is essential for debugging production issues.

### Basic Logging Setup

```python
# app/__init__.py
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app():
    app = Flask(__name__)
    
    # Configure logging
    if not app.debug:
        # Create logs directory
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # File handler
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')
    
    return app
```

### Structured Logging

```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

# Usage
handler = RotatingFileHandler('logs/app.json', maxBytes=10240000, backupCount=10)
handler.setFormatter(JSONFormatter())
app.logger.addHandler(handler)
```

### Request Logging

```python
from flask import request, g
import time
import uuid

@app.before_request
def before_request():
    """Log request start"""
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()
    
    app.logger.info(f"Request started: {request.method} {request.path}", extra={
        'request_id': g.request_id,
        'method': request.method,
        'path': request.path,
        'remote_addr': request.remote_addr
    })

@app.after_request
def after_request(response):
    """Log request completion"""
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        
        app.logger.info(f"Request completed: {response.status_code}", extra={
            'request_id': g.request_id,
            'status_code': response.status_code,
            'duration': elapsed
        })
        
        response.headers['X-Request-ID'] = g.request_id
    
    return response
```

### Error Logging

```python
@app.errorhandler(Exception)
def handle_exception(error):
    """Log and handle all exceptions"""
    app.logger.error(
        f"Unhandled exception: {error}",
        extra={
            'request_id': getattr(g, 'request_id', 'unknown'),
            'path': request.path,
            'method': request.method,
            'remote_addr': request.remote_addr
        },
        exc_info=True  # Include traceback
    )
    
    return jsonify({'error': 'Internal server error'}), 500
```

## Error Response Patterns

### Consistent Error Format

```python
# app/utils/responses.py
from flask import jsonify, g

def error_response(message, status_code, details=None):
    """Standard error response"""
    payload = {
        'error': {
            'message': message,
            'status_code': status_code,
            'request_id': getattr(g, 'request_id', None)
        }
    }
    
    if details:
        payload['error']['details'] = details
    
    return jsonify(payload), status_code

def validation_error_response(errors):
    """Validation error response"""
    return error_response(
        'Validation failed',
        422,
        details={'fields': errors}
    )
```

### Usage in Routes

```python
from app.utils.responses import error_response, validation_error_response

@bp.route('', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Validate
    errors = {}
    if not data.get('email'):
        errors['email'] = 'Email is required'
    if not data.get('password'):
        errors['password'] = 'Password is required'
    
    if errors:
        return validation_error_response(errors)
    
    # Create user...
    return jsonify({'id': 1}), 201
```

## Monitoring and Alerting

### Health Check Endpoint

```python
from flask import jsonify
from app.extensions import db
import redis

@app.route('/health')
def health_check():
    """System health check"""
    health = {
        'status': 'healthy',
        'checks': {}
    }
    
    # Check database
    try:
        db.session.execute('SELECT 1')
        health['checks']['database'] = 'ok'
    except Exception as e:
        health['checks']['database'] = 'error'
        health['status'] = 'unhealthy'
        app.logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    try:
        r = redis.Redis()
        r.ping()
        health['checks']['redis'] = 'ok'
    except Exception as e:
        health['checks']['redis'] = 'error'
        health['status'] = 'unhealthy'
        app.logger.error(f"Redis health check failed: {e}")
    
    status_code = 200 if health['status'] == 'healthy' else 503
    return jsonify(health), status_code
```

### Error Rate Monitoring

```python
from collections import defaultdict
from datetime import datetime, timedelta

error_counts = defaultdict(int)
error_window = timedelta(minutes=5)

@app.after_request
def monitor_errors(response):
    """Track error rates"""
    if response.status_code >= 500:
        now = datetime.utcnow()
        error_counts[now.replace(second=0, microsecond=0)] += 1
        
        # Check if error rate is too high
        recent_errors = sum(
            count for timestamp, count in error_counts.items()
            if now - timestamp < error_window
        )
        
        if recent_errors > 100:  # Threshold
            app.logger.critical(f"High error rate: {recent_errors} errors in 5 minutes")
            # Send alert (email, Slack, PagerDuty, etc.)
    
    return response
```

## Summary

Production error handling requires:
- Global exception handlers for all error types
- Custom exception classes for specific scenarios
- Comprehensive logging (requests, errors, performance)
- Consistent error response format
- Health check endpoints
- Error monitoring and alerting

**Key principles:**
- Never expose internal errors to clients
- Log all errors with context (request ID, user, etc.)
- Use structured logging for easy parsing
- Implement health checks for dependencies
- Monitor error rates and alert on anomalies

---

## Practice Exercises

### Multiple Choice Questions

1. What should you return in production when an unhandled exception occurs?
   a) Full stack trace
   b) Generic error message
   c) Database error details
   d) User's input data

2. What's the purpose of request IDs in error logging?
   a) Security
   b) Tracing requests across logs
   c) Rate limiting
   d) Caching

3. Which HTTP status code should be used for validation errors?
   a) 400
   b) 422
   c) 500
   d) 409

4. What's the benefit of custom exception classes?
   a) Faster execution
   b) Better type safety and error handling
   c) Smaller code size
   d) Automatic error recovery

5. Where should error handlers be registered?
   a) In each blueprint
   b) In routes
   c) Globally in app factory
   d) In models

### Practical Tasks

**Task 1: Complete Error Handling System**

Build a comprehensive error handling system:

1. Create custom exception classes:
   - `ValidationError` (422)
   - `NotFoundError` (404)
   - `UnauthorizedError` (401)
   - `ForbiddenError` (403)
   - `ConflictError` (409)

2. Implement global error handlers

3. Add structured JSON logging

4. Create error response helpers

5. Implement request/response logging with request IDs

6. Build health check endpoint

**Task 2: Error Monitoring**

Implement error monitoring:

1. Track error rates (errors per minute)
2. Alert when error rate exceeds threshold
3. Log slow requests (> 1 second)
4. Create `/metrics` endpoint showing:
   - Total requests
   - Error count by status code
   - Average response time
   - Slow request count

### Debugging Scenario

Your API is experiencing issues in production:

```python
@app.route('/users/<int:user_id>')
def get_user(user_id):
    user = User.query.get(user_id)
    return jsonify(user.to_dict())

@app.route('/process', methods=['POST'])
def process_data():
    data = request.get_json()
    result = expensive_operation(data['items'])
    return jsonify(result)
```

**Problems reported:**

1. When user doesn't exist, API returns 500 error
2. No way to trace errors across logs
3. When `expensive_operation()` fails, full stack trace is exposed to clients
4. No visibility into which endpoints are slow
5. Can't correlate errors with specific requests

**Questions:**
1. Why does missing user return 500 instead of 404?
2. How would you add request tracing?
3. How would you prevent exposing stack traces?
4. How would you log slow requests?
5. Provide corrected code with proper error handling and logging.

---

**Next Module**: [Authentication & Authorization](09-authentication-authorization.md)
