# Module 4: Request Handling

## Introduction to Request Handling

Request handling is the heart of any web application. Every time a client sends an HTTP request to your Flask application, Flask creates a `request` object that encapsulates all the information about that incoming request. Understanding how to access, parse, and validate this request data is fundamental to building robust and secure web applications.

In this module, you'll learn:
- How to access and inspect HTTP request data
- Working with headers for authentication and metadata
- Parsing different types of request data (JSON, forms, files)
- Implementing comprehensive input validation
- Best practices for security and error handling

---

## The Request Object

The `request` object is a global proxy object in Flask that contains all information about the incoming HTTP request. It's automatically available in your request context (inside route handlers, before/after request functions, etc.).

### Why is the Request Object Important?

The request object is your gateway to understanding what the client is sending:
- **HTTP method**: What action the client wants to perform (GET, POST, PUT, DELETE, etc.)
- **URL information**: The path, query parameters, and full URL
- **Headers**: Metadata like authentication tokens, content type, and custom headers
- **Body data**: The actual data the client is sending (JSON, form data, files)
- **Client information**: IP address, user agent, and connection details

### Basic Request Inspection

Let's start by examining the request object itself:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/debug')
def debug_request():
    """Inspect the incoming HTTP request"""
    return {
        'method': request.method,              # HTTP method used (GET, POST, etc.)
        'path': request.path,                  # The URL path (e.g., /debug)
        'url': request.url,                    # Complete URL with query string
        'base_url': request.base_url,          # URL without query string
        'remote_addr': request.remote_addr,    # Client's IP address
        'user_agent': request.headers.get('User-Agent')  # Client's browser/app info
    }
```

**To test this endpoint:**

```bash
# Using curl, which is a command-line tool for making HTTP requests
# The -X flag specifies the HTTP method (default is GET)
curl -X GET "http://localhost:5000/debug"

# Response might look like:
# {
#   "method": "GET",
#   "path": "/debug",
#   "url": "http://localhost:5000/debug",
#   "base_url": "http://localhost:5000/",
#   "remote_addr": "127.0.0.1",
#   "user_agent": "curl/7.68.0"
# }
```

### Request Properties Reference

The Flask request object provides many useful properties for examining incoming requests:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/info')
def request_info():
    """Comprehensive request information inspection"""
    return {
        # ============= URL INFORMATION =============
        # These properties help you understand where the request is going
        'url': request.url,                    
        # Full URL with all components
        # Example: http://example.com:5000/info?key=value
        
        'base_url': request.base_url,          
        # Base URL without query parameters
        # Example: http://example.com:5000/
        
        'path': request.path,                  
        # Just the path component
        # Example: /info
        
        'full_path': request.full_path,        
        # Path including query string
        # Example: /info?key=value
        
        'script_root': request.script_root,    
        # Where your Flask app is mounted (usually empty on root)
        # Example: /api (if app is mounted at /api)
        
        'host': request.host,                  
        # The hostname and port
        # Example: localhost:5000
        
        # ============= HTTP METHOD =============
        # Tells you what action the client wants to perform
        'method': request.method,              
        # GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS, etc.
        
        # ============= CLIENT INFORMATION =============
        # Details about the client making the request
        'remote_addr': request.remote_addr,    
        # Client's IP address (may be proxy IP in production)
        
        'remote_user': request.remote_user,    
        # Username if HTTP authentication is used
        
        'scheme': request.scheme,              
        # Protocol being used: http or https
        
        # ============= REQUEST METADATA =============
        # Information about how the data is formatted
        'is_json': request.is_json,            
        # True if Content-Type is application/json
        
        'is_secure': request.is_secure,        
        # True if using HTTPS (secure connection)
        
        'content_type': request.content_type,  
        # Tells what format the body data is in
        # Examples: application/json, text/plain, multipart/form-data
        
        'content_length': request.content_length,  
        # Size of the request body in bytes
    }
```

**Understanding URL Components:**

```bash
# If you make this request:
curl "http://example.com:5000/api/users/123?role=admin&status=active"

# Then:
# request.scheme       = "http"
# request.host         = "example.com:5000"
# request.path         = "/api/users/123"
# request.full_path    = "/api/users/123?role=admin&status=active"
# request.base_url     = "http://example.com:5000/"
# request.url          = "http://example.com:5000/api/users/123?role=admin&status=active"
```

---

## Handling Headers

HTTP headers are crucial metadata that travel with every HTTP request and response. They provide context about the request—authentication information, data format, client identification, and custom application-specific metadata. Understanding how to read and validate headers is essential for building secure and well-integrated APIs.

### Understanding Headers

Headers are key-value pairs that look like this:

```
Authorization: Bearer eyJhbGc... (authentication token)
Content-Type: application/json (format of request body)
User-Agent: Mozilla/5.0... (client's browser/app)
X-Request-ID: abc-123-def (unique request identifier)
Accept: application/json (format client wants in response)
```

Headers are case-insensitive (the server treats `Content-Type` and `content-type` the same way), but by convention they use Title-Case.

### Reading Headers

In Flask, you access headers through the `request.headers` object:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/headers')
def show_headers():
    """
    Demonstrate reading individual headers from a request.
    
    Headers can be accessed using .get() which returns None if not present,
    or you can access them directly like a dictionary.
    """
    
    # Get specific headers - use .get() to safely access (returns None if missing)
    auth = request.headers.get('Authorization')
    # Authorization header typically contains: "Bearer <token>" or "Basic <credentials>"
    
    content_type = request.headers.get('Content-Type')
    # Content-Type tells us how to interpret the request body
    # Examples: application/json, text/plain, multipart/form-data
    
    user_agent = request.headers.get('User-Agent')
    # User-Agent identifies the client application
    # Examples: Mozilla/5.0 (Firefox), curl/7.68.0, PostmanRuntime/7.26.8
    
    # Get all headers as a dictionary
    all_headers = dict(request.headers)
    # This converts the headers object to a regular Python dictionary
    
    return {
        'authorization': auth,
        'content_type': content_type,
        'user_agent': user_agent,
        'all_headers': all_headers,
        'total_headers': len(all_headers)
    }
```

**Testing header reading:**

```bash
# Using curl with the -H flag to add custom headers
curl -X GET http://localhost:5000/headers \
  -H "Authorization: Bearer my-secret-token" \
  -H "User-Agent: Custom-Client/1.0" \
  -H "X-Custom-Header: custom-value"

# Response:
# {
#   "authorization": "Bearer my-secret-token",
#   "user_agent": "Custom-Client/1.0",
#   "all_headers": {
#     "Authorization": "Bearer my-secret-token",
#     "User-Agent": "Custom-Client/1.0",
#     "X-Custom-Header": "custom-value",
#     ...
#   }
# }
```

### Common Headers in APIs

Every API uses headers differently, but certain headers are nearly universal. Let's build a practical example that handles the most common patterns:

```python
@app.route('/api/data')
def get_data():
    """
    Real-world example showing how to handle common API headers.
    
    This demonstrates authentication, versioning, and content negotiation—
    three critical header-based patterns in modern APIs.
    """
    
    # ============= AUTHENTICATION =============
    # The Authorization header is how clients prove their identity
    token = request.headers.get('Authorization')
    
    # Authorization header format: "Bearer <token>"
    # We need to validate that:
    # 1. The header exists
    # 2. It starts with "Bearer "
    # 3. A token is present after "Bearer "
    
    if not token or not token.startswith('Bearer '):
        return {
            'error': 'Missing or invalid Authorization header',
            'expected_format': 'Authorization: Bearer <your-token>'
        }, 401  # 401 Unauthorized - credentials missing or invalid
    
    # Extract the actual token by removing "Bearer " prefix
    actual_token = token[7:]  # Skip first 7 characters ("Bearer ")
    
    # ============= API VERSIONING =============
    # Many APIs use X-API-Version header to support multiple API versions
    # Clients can request specific versions for backward compatibility
    api_version = request.headers.get('X-API-Version', '1.0')
    # If the header isn't provided, default to version 1.0
    
    if api_version not in ['1.0', '2.0', '3.0']:
        return {
            'error': 'Unsupported API version',
            'supported_versions': ['1.0', '2.0', '3.0']
        }, 400  # 400 Bad Request
    
    # ============= CONTENT NEGOTIATION =============
    # The Accept header tells us what format the client wants the response in
    # This allows a single endpoint to return different formats
    accept = request.headers.get('Accept', 'application/json')
    # Defaults to JSON if not specified
    
    if accept not in ['application/json', 'application/xml', 'text/csv']:
        return {
            'error': 'Unsupported content type in Accept header',
            'supported_types': ['application/json', 'application/xml', 'text/csv']
        }, 406  # 406 Not Acceptable
    
    # ============= REQUEST TRACKING =============
    # X-Request-ID helps trace a request through multiple systems
    # This is invaluable for debugging and monitoring
    request_id = request.headers.get('X-Request-ID')
    
    # If not provided, you could generate one:
    if not request_id:
        import uuid
        request_id = str(uuid.uuid4())
    
    return {
        'data': ['item1', 'item2', 'item3'],
        'version': api_version,
        'content_type': accept,
        'request_id': request_id,
        'authenticated': True
    }
```

**Complete curl example with all headers:**

```bash
curl -X GET http://localhost:5000/api/data \
  -H "Authorization: Bearer secret-token-12345" \
  -H "X-API-Version: 2.0" \
  -H "Accept: application/json" \
  -H "X-Request-ID: req-uuid-12345"

# Response:
# {
#   "data": ["item1", "item2", "item3"],
#   "version": "2.0",
#   "content_type": "application/json",
#   "request_id": "req-uuid-12345",
#   "authenticated": true
# }
```

### Custom Headers

Beyond standard headers, APIs often define custom headers prefixed with `X-` to handle application-specific requirements:

```python
@app.route('/custom')
def custom_headers():
    """
    Handle custom application headers.
    
    Custom headers typically start with X- to distinguish them from 
    standard HTTP headers. Examples: X-Tenant-ID, X-User-Role, X-API-Key
    """
    
    # Multi-tenant applications use X-Tenant-ID to identify the organization
    tenant_id = request.headers.get('X-Tenant-ID')
    
    if not tenant_id:
        return {
            'error': 'X-Tenant-ID header is required',
            'reason': 'This API operates in multi-tenant mode and needs to know which tenant you are'
        }, 400
    
    # Correlation ID for distributed systems
    # Used to track a request across multiple microservices
    correlation_id = request.headers.get('X-Correlation-ID')
    
    # If not provided, generate one
    if not correlation_id:
        import uuid
        correlation_id = str(uuid.uuid4())
    
    # API Key for authentication (simpler than Bearer tokens)
    api_key = request.headers.get('X-API-Key')
    
    # Rate limiting based on custom headers
    rate_limit = request.headers.get('X-Rate-Limit', 100, type=int)
    # type=int converts the string to an integer
    
    return {
        'tenant_id': tenant_id,
        'correlation_id': correlation_id,
        'has_api_key': api_key is not None,
        'rate_limit': rate_limit,
        'message': f'Processing request for tenant {tenant_id}'
    }
```

**Testing custom headers:**

```bash
curl -X POST http://localhost:5000/custom \
  -H "X-Tenant-ID: company-acme" \
  -H "X-Correlation-ID: corr-id-abc123" \
  -H "X-API-Key: sk_live_abc123xyz" \
  -H "X-Rate-Limit: 500"
```

---

## Handling JSON Data

JSON (JavaScript Object Notation) has become the de facto standard for API communication. It's human-readable, language-independent, and hierarchical. Nearly all modern APIs use JSON for both requests and responses.

### Understanding JSON in HTTP Requests

When you send JSON data in an HTTP request:

```
POST /api/users HTTP/1.1
Content-Type: application/json
Content-Length: 67

{"name":"John Doe","email":"john@example.com","age":30}
```

The `Content-Type: application/json` header tells the server "the request body is JSON-formatted data". The `Content-Length` header tells the server how many bytes to expect.

### Reading JSON Data

Here's how to safely parse and handle JSON in Flask:

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/users', methods=['POST'])
def create_user():
    """
    Create a new user from JSON data.
    
    Expected JSON body:
    {
        "email": "user@example.com",
        "password": "secure-password",
        "name": "John Doe"
    }
    """
    
    # Step 1: Verify that the request contains JSON
    # The request.is_json property checks if Content-Type is application/json
    if not request.is_json:
        return {
            'error': 'Invalid Content-Type',
            'message': 'Content-Type header must be application/json',
            'received': request.content_type
        }, 400  # 400 Bad Request
    
    # Step 2: Parse the JSON data
    # request.get_json() converts the JSON string to a Python dictionary
    data = request.get_json()
    
    # Step 3: Safely access the data
    # Use .get() to avoid KeyError if a field is missing
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    # Step 4: Return the created resource
    # In real apps, you'd save to database and return the created object
    return {
        'id': 1,
        'email': email,
        'name': name,
        'created_at': '2024-01-11T10:00:00Z'
    }, 201  # 201 Created
```

**Testing with curl:**

```bash
# Send JSON data with proper Content-Type header
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "MySecure123!",
    "name": "John Doe"
  }'

# The -d flag sends the data as the request body
# -H flag sets the Content-Type header

# Response (201 Created):
# {
#   "id": 1,
#   "email": "john@example.com",
#   "name": "John Doe",
#   "created_at": "2024-01-11T10:00:00Z"
# }
```

### JSON Validation Strategies

Real-world applications always validate incoming JSON data before using it. Here's a comprehensive example:

```python
@app.route('/users', methods=['POST'])
def create_user_with_validation():
    """
    Create a user with thorough validation.
    
    This demonstrates best practices for JSON validation:
    1. Check Content-Type
    2. Verify required fields
    3. Validate data types
    4. Implement business logic validation
    """
    
    # Validate Content-Type
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400
    
    data = request.get_json()
    
    # ============= REQUIRED FIELDS VALIDATION =============
    # Define which fields are mandatory
    required_fields = ['email', 'password', 'name']
    
    # Check if all required fields are present
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return {
            'error': 'Missing required fields',
            'missing_fields': missing_fields,
            'required_fields': required_fields
        }, 400
    
    # ============= TYPE VALIDATION =============
    # Ensure fields are the correct data types
    if not isinstance(data['email'], str):
        return {
            'error': 'Invalid data type',
            'field': 'email',
            'expected': 'string',
            'received': type(data['email']).__name__
        }, 400
    
    if not isinstance(data['password'], str):
        return {'error': 'Password must be a string'}, 400
    
    if not isinstance(data['name'], str):
        return {'error': 'Name must be a string'}, 400
    
    # ============= BUSINESS LOGIC VALIDATION =============
    # Validate according to your application's rules
    
    # Email validation
    if '@' not in data['email'] or '.' not in data['email']:
        return {
            'error': 'Invalid email format',
            'example': 'user@example.com'
        }, 400
    
    # Password strength validation
    password = data['password']
    if len(password) < 8:
        return {
            'error': 'Password too short',
            'minimum_length': 8,
            'provided_length': len(password)
        }, 400
    
    if not any(c.isupper() for c in password):
        return {'error': 'Password must contain at least one uppercase letter'}, 400
    
    if not any(c.isdigit() for c in password):
        return {'error': 'Password must contain at least one digit'}, 400
    
    # Name validation
    name = data['name'].strip()  # Remove leading/trailing whitespace
    if len(name) < 2:
        return {'error': 'Name must be at least 2 characters'}, 400
    
    if len(name) > 100:
        return {'error': 'Name cannot exceed 100 characters'}, 400
    
    # All validation passed!
    return {
        'id': 1,
        'email': data['email'],
        'name': name,
        'status': 'User created successfully'
    }, 201
```

**Test cases:**

```bash
# Test 1: Missing Content-Type header
curl -X POST http://localhost:5000/users \
  -d '{"email":"test@example.com"}'
# Error: Content-Type must be application/json

# Test 2: Missing required fields
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'
# Error: Missing required fields - ['password', 'name']

# Test 3: Invalid email format
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid-email","password":"Pass123","name":"John"}'
# Error: Invalid email format

# Test 4: Password too short
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Pass1","name":"John"}'
# Error: Password too short (minimum is 8 characters)

# Test 5: Successful creation
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"SecurePass123","name":"John Doe"}'
# Success: 201 Created
```

### Handling Invalid JSON

Sometimes the client sends malformed JSON (invalid syntax). Flask automatically handles this, but you should be aware of it:

```python
from flask import request
import json

@app.route('/data', methods=['POST'])
def receive_data():
    """
    Handle potentially malformed JSON gracefully.
    
    The force=True parameter tells Flask to parse the body as JSON
    even if Content-Type header is missing.
    """
    
    try:
        # Attempt to parse JSON
        # force=True tries to parse even without proper Content-Type
        data = request.get_json(force=True)
        
        if data is None:
            return {'error': 'Request body is empty'}, 400
        
        return {
            'received': data,
            'status': 'success'
        }
    
    except (json.JSONDecodeError, TypeError) as e:
        # JSONDecodeError: Invalid JSON syntax
        # TypeError: Body is not JSON-like at all
        return {
            'error': 'Invalid JSON in request body',
            'message': str(e),
            'tips': [
                'Ensure JSON syntax is valid (check for missing commas, quotes)',
                'Set Content-Type: application/json header',
                'Use a JSON validator at jsonlint.com'
            ]
        }, 400

```

**Testing invalid JSON:**

```bash
# Test with invalid JSON (missing quotes)
curl -X POST http://localhost:5000/data \
  -H "Content-Type: application/json" \
  -d '{name: "John"}'
# Error: Invalid JSON in request body

# Test with valid JSON
curl -X POST http://localhost:5000/data \
  -H "Content-Type: application/json" \
  -d '{"name":"John"}'
# Success: received = {"name":"John"}

# Test with empty body
curl -X POST http://localhost:5000/data \
  -H "Content-Type: application/json" \
  -d ''
# Error: Request body is empty
```

---

## Handling Form Data

While JSON dominates modern APIs, traditional HTML forms remain important for web applications. Flask provides robust support for two types of form data:

1. **URL-Encoded Forms** (`application/x-www-form-urlencoded`) - Simple key-value pairs
2. **Multipart Forms** (`multipart/form-data`) - Used for file uploads

### URL-Encoded Form Data

HTML forms typically use URL encoding, where data is formatted as query strings in the request body:

```
POST /login HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: 40

email=user%40example.com&password=secret&remember=on
```

Here's how to handle it in Flask:

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    """
    Handle traditional HTML form login.
    
    The request.form object works like request.args (query parameters),
    but gets data from the request body instead of the URL.
    """
    
    # Access form fields using .get() to safely handle missing values
    email = request.form.get('email')
    password = request.form.get('password')
    
    # Convert checkbox/boolean values
    # Checkboxes send "on" if checked, or are absent if unchecked
    remember = request.form.get('remember', type=bool)
    
    # In HTML forms: <input type="checkbox" name="remember">
    # If checked, it sends remember=on
    # If unchecked, the field isn't sent at all
    # type=bool converts "on" to True, missing to False
    
    return {
        'email': email,
        'password': password,
        'remember': remember,
        'message': f'Login attempt for {email}'
    }
```

**Testing with curl:**

```bash
# Simulate HTML form submission
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "email=john@example.com" \
  --data-urlencode "password=MyPassword123" \
  --data-urlencode "remember=on"

# Or equivalently:
curl -X POST http://localhost:5000/login \
  -d "email=john@example.com&password=MyPassword123&remember=on"

# Response:
# {
#   "email": "john@example.com",
#   "password": "MyPassword123",
#   "remember": true,
#   "message": "Login attempt for john@example.com"
# }
```

### Multipart Form Data (File Uploads)

File uploads use `multipart/form-data` encoding, which is more complex but handles binary data:

```
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary
Content-Length: 1234

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="document.pdf"
Content-Type: application/pdf

<binary PDF data here>
------WebKitFormBoundary--
```

Here's how to handle file uploads:

```python
from flask import Flask, request
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handle single file upload.
    
    werkzeug.utils.secure_filename is CRITICAL for security.
    It prevents path traversal attacks like "../../etc/passwd"
    """
    
    # ============= CHECK FOR FILE PRESENCE =============
    # request.files is a dictionary-like object containing uploaded files
    if 'file' not in request.files:
        return {
            'error': 'No file provided',
            'message': 'Please include a file with form field name "file"'
        }, 400
    
    file = request.files['file']
    
    # ============= CHECK FOR EMPTY FILENAME =============
    # A file entry with empty filename means nothing was selected in the form
    if file.filename == '':
        return {
            'error': 'No file selected',
            'message': 'Please select a file before uploading'
        }, 400
    
    # ============= SECURE THE FILENAME =============
    # secure_filename() removes/escapes dangerous characters
    # Examples of what it prevents:
    # "../../etc/passwd" -> "etcpasswd"
    # "file<name>.txt" -> "filename.txt"
    # "CON" (Windows reserved) -> "CON"
    filename = secure_filename(file.filename)
    
    # ============= CREATE UPLOAD DIRECTORY =============
    upload_folder = '/tmp/uploads'
    os.makedirs(upload_folder, exist_ok=True)
    # exist_ok=True means "don't error if directory already exists"
    
    # ============= SAVE FILE =============
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    # At this point, the file is saved to disk
    
    # ============= GET FILE INFO =============
    file_size = os.path.getsize(filepath)  # Size in bytes
    
    return {
        'message': 'File uploaded successfully',
        'filename': filename,
        'size_bytes': file_size,
        'size_mb': round(file_size / (1024 * 1024), 2),
        'saved_path': filepath
    }, 201
```

**Testing file upload with curl:**

```bash
# Upload a file using -F (multipart form) flag
curl -X POST http://localhost:5000/upload \
  -F "file=@/path/to/document.pdf"

# The @ symbol tells curl to upload the actual file
# Without it, curl would just send the filename as text

# Response (201 Created):
# {
#   "message": "File uploaded successfully",
#   "filename": "document.pdf",
#   "size_bytes": 12345,
#   "size_mb": 0.01,
#   "saved_path": "/tmp/uploads/document.pdf"
# }

# Upload multiple files (if endpoint handles it):
curl -X POST http://localhost:5000/upload \
  -F "files=@file1.pdf" \
  -F "files=@file2.pdf" \
  -F "description=My documents"
```

### File Upload with Comprehensive Validation

Real-world file uploads require extensive validation for security and functionality:

```python
import os
from flask import Flask, request
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration constants
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes

def allowed_file(filename):
    """
    Check if filename has an allowed extension.
    
    Returns True if file extension is in ALLOWED_EXTENSIONS list.
    The filename.rsplit('.', 1) splits the filename into [name, extension]
    [1] gets the extension, .lower() makes it case-insensitive.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file_validated():
    """
    Upload file with security validations.
    
    Validates:
    1. File presence
    2. Filename not empty
    3. File extension allowed
    4. File size within limits
    """
    
    # ============= VALIDATION 1: FILE PRESENCE =============
    if 'file' not in request.files:
        return {'error': 'No file provided in form field "file"'}, 400
    
    file = request.files['file']
    
    # ============= VALIDATION 2: FILENAME =============
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    
    # ============= VALIDATION 3: FILE EXTENSION =============
    # Always check file extension to prevent executable uploads
    if not allowed_file(file.filename):
        return {
            'error': 'File type not allowed',
            'your_extension': file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'unknown',
            'allowed_extensions': list(ALLOWED_EXTENSIONS)
        }, 400
    
    # ============= VALIDATION 4: FILE SIZE =============
    # File size check - prevents disk space exhaustion attacks
    # We need to read to end of file to get size
    file.seek(0, os.SEEK_END)  # Seek to end of file
    size = file.tell()  # Get current position (= file size)
    file.seek(0)  # Seek back to beginning for processing
    
    if size == 0:
        return {'error': 'File is empty'}, 400
    
    if size > MAX_FILE_SIZE:
        return {
            'error': 'File too large',
            'max_size_bytes': MAX_FILE_SIZE,
            'max_size_mb': MAX_FILE_SIZE / (1024 * 1024),
            'your_size_bytes': size,
            'your_size_mb': round(size / (1024 * 1024), 2)
        }, 413  # 413 Payload Too Large
    
    # ============= ALL VALIDATIONS PASSED =============
    filename = secure_filename(file.filename)
    
    # Add timestamp to filename to avoid collisions
    import time
    timestamp = int(time.time())
    name, ext = filename.rsplit('.', 1)
    filename = f"{name}_{timestamp}.{ext}"
    
    # Save file
    upload_folder = '/tmp/uploads'
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return {
        'message': 'File uploaded and validated successfully',
        'filename': filename,
        'size_bytes': size,
        'size_mb': round(size / (1024 * 1024), 2),
        'upload_path': filepath
    }, 201

@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_files():
    """
    Handle multiple file uploads at once.
    
    HTML form needs: <input type="file" name="files" multiple>
    """
    
    if 'files' not in request.files:
        return {'error': 'No files provided'}, 400
    
    # getlist('files') gets ALL files with form field name "files"
    files = request.files.getlist('files')
    
    if not files:
        return {'error': 'No files selected'}, 400
    
    uploaded = []
    errors = []
    
    for file in files:
        if file.filename == '':
            errors.append({'filename': 'unknown', 'error': 'Empty filename'})
            continue
        
        if not allowed_file(file.filename):
            errors.append({
                'filename': file.filename,
                'error': f'Extension not allowed (allowed: {list(ALLOWED_EXTENSIONS)})'
            })
            continue
        
        # Size check
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_FILE_SIZE:
            errors.append({
                'filename': file.filename,
                'error': f'File too large ({size / (1024*1024):.1f}MB > {MAX_FILE_SIZE / (1024*1024):.1f}MB)'
            })
            continue
        
        # Save file
        filename = secure_filename(file.filename)
        upload_folder = '/tmp/uploads'
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        uploaded.append({
            'filename': filename,
            'size_bytes': size,
            'size_mb': round(size / (1024 * 1024), 2)
        })
    
    return {
        'uploaded': len(uploaded),
        'failed': len(errors),
        'files': uploaded,
        'errors': errors
    }, 201 if not errors else 206  # 206 Partial Content if some failed
```

**Testing multiple file uploads:**

```bash
# Upload multiple files at once
curl -X POST http://localhost:5000/upload-multiple \
  -F "files=@document1.pdf" \
  -F "files=@image1.jpg" \
  -F "files=@image2.png"

# Response:
# {
#   "uploaded": 3,
#   "failed": 0,
#   "files": [
#     {"filename": "document1.pdf", "size_bytes": 5000, "size_mb": 0.01},
#     {"filename": "image1.jpg", "size_bytes": 50000, "size_mb": 0.05},
#     {"filename": "image2.png", "size_bytes": 75000, "size_mb": 0.07}
#   ],
#   "errors": []
# }
```

---

## Input Validation Strategies

Input validation is arguably the most important security practice in web development. Every piece of user input is potentially dangerous if not properly validated. Let's explore multiple validation strategies from simple to sophisticated.

### Strategy 1: Manual Validation (Simple but Verbose)

Manual validation gives you complete control but requires more code:

```python
def validate_user_data(data):
    """
    Validate user data manually, field by field.
    
    Returns a dictionary of validation errors.
    If empty dict is returned, data is valid.
    """
    errors = {}
    
    # ============= EMAIL VALIDATION =============
    if not data.get('email'):
        # Check if field exists and is truthy (not empty string)
        errors['email'] = 'Email is required'
    elif '@' not in data['email']:
        # Basic email validation (full validation is complex)
        errors['email'] = 'Email must contain @ symbol'
    elif '.' not in data['email'].split('@')[1]:
        # Check that domain has a dot (e.g., example.com)
        errors['email'] = 'Email domain must be valid (e.g., example.com)'
    
    # ============= PASSWORD VALIDATION =============
    if not data.get('password'):
        errors['password'] = 'Password is required'
    elif len(data['password']) < 8:
        errors['password'] = 'Password must be at least 8 characters'
    elif len(data['password']) > 128:
        errors['password'] = 'Password cannot exceed 128 characters'
    elif not any(c.isupper() for c in data['password']):
        # Check if password contains at least one uppercase letter
        errors['password'] = 'Password must contain at least one uppercase letter'
    elif not any(c.isdigit() for c in data['password']):
        # Check if password contains at least one digit
        errors['password'] = 'Password must contain at least one digit'
    elif not any(c in '!@#$%^&*' for c in data['password']):
        # Check for special characters
        errors['password'] = 'Password must contain special character (!@#$%^&*)'
    
    # ============= AGE VALIDATION (OPTIONAL FIELD) =============
    if 'age' in data:
        try:
            age = int(data['age'])  # Try to convert to integer
            if age < 0:
                errors['age'] = 'Age cannot be negative'
            elif age > 150:
                errors['age'] = 'Age seems unrealistic (> 150)'
        except (ValueError, TypeError):
            # Conversion failed - not a valid integer
            errors['age'] = f'Age must be a number, received: {type(data.get("age")).__name__}'
    
    return errors

@app.route('/users', methods=['POST'])
def create_user():
    """Use the validation function in a route handler"""
    data = request.get_json()
    
    errors = validate_user_data(data)
    
    if errors:
        return {
            'error': 'Validation failed',
            'details': errors,
            'received_fields': list(data.keys()) if data else None
        }, 400
    
    # All validation passed - process the user creation
    # In real app: user = User.create(**data)
    return {
        'id': 1,
        'email': data['email'],
        'name': data.get('name'),
        'created_at': '2024-01-11T10:00:00Z'
    }, 201
```

**Testing manual validation:**

```bash
# Test 1: Missing email
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"password":"Pass123","age":25}'
# Error: email is required

# Test 2: Invalid email
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"invalid","password":"Pass123"}'
# Error: Email must contain @ symbol

# Test 3: Weak password
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"weak"}'
# Error: Password must be at least 8 characters

# Test 4: Valid data
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"john@example.com","password":"SecurePass123!","age":30}'
# Success: 201 Created
```

### Strategy 2: Decorator-Based Validation (DRY - Don't Repeat Yourself)

Use decorators to reduce validation code repetition across multiple routes:

```python
from functools import wraps
from flask import request, jsonify

def validate_json(*expected_fields):
    """
    Decorator to validate that JSON request contains required fields.
    
    Usage:
    @app.route('/users', methods=['POST'])
    @validate_json('email', 'password', 'name')
    def create_user():
        # If we reach here, 'email', 'password', 'name' are guaranteed to exist
        data = request.get_json()
        ...
    """
    def decorator(f):
        @wraps(f)  # Preserve the original function's metadata
        def wrapper(*args, **kwargs):
            # Check Content-Type
            if not request.is_json:
                return {
                    'error': 'Invalid Content-Type',
                    'expected': 'application/json'
                }, 400
            
            data = request.get_json()
            
            # Check for required fields
            missing = [field for field in expected_fields if field not in data]
            
            if missing:
                return {
                    'error': 'Missing required fields',
                    'missing_fields': missing,
                    'expected_fields': list(expected_fields)
                }, 400
            
            # All checks passed, call the original function
            return f(*args, **kwargs)
        
        return wrapper
    return decorator

# Usage examples
@app.route('/users', methods=['POST'])
@validate_json('email', 'password', 'name')
def create_user():
    """
    Creates a new user.
    
    Required fields: email, password, name
    (The decorator ensures these exist before this function is called)
    """
    data = request.get_json()
    return {
        'id': 1,
        'email': data['email'],
        'name': data['name']
    }, 201

@app.route('/posts', methods=['POST'])
@validate_json('title', 'content', 'author_id')
def create_post():
    """
    Creates a new post.
    
    Required fields: title, content, author_id
    (The decorator ensures these exist)
    """
    data = request.get_json()
    return {
        'id': 1,
        'title': data['title'],
        'content': data['content']
    }, 201
```

### Strategy 3: Schema-Based Validation (Professional Grade)

For larger applications, schema-based validation provides structure and reusability:

```python
from typing import Dict, Any, Tuple

class UserSchema:
    """
    Schema for validating user creation data.
    
    This class encapsulates all user validation logic in one place,
    making it easy to reuse across different routes and test independently.
    """
    
    # Define constraints as class attributes for easy modification
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 100
    
    @staticmethod
    def validate(data: Dict[str, Any]) -> Tuple[bool, Dict[str, str]]:
        """
        Validate user data.
        
        Returns tuple of (is_valid: bool, errors: dict)
        If is_valid is True, errors dict will be empty.
        If is_valid is False, errors dict contains all validation errors.
        """
        errors = {}
        
        # ============= EMAIL VALIDATION =============
        email = data.get('email', '').strip()
        
        if not email:
            errors['email'] = 'Email is required'
        elif not UserSchema._is_valid_email(email):
            errors['email'] = 'Invalid email format (must be user@example.com)'
        
        # ============= PASSWORD VALIDATION =============
        password = data.get('password', '')
        
        if not password:
            errors['password'] = 'Password is required'
        else:
            password_error = UserSchema._validate_password(password)
            if password_error:
                errors['password'] = password_error
        
        # ============= NAME VALIDATION =============
        name = data.get('name', '').strip()
        
        if not name:
            errors['name'] = 'Name is required'
        elif len(name) < UserSchema.MIN_NAME_LENGTH:
            errors['name'] = f'Name must be at least {UserSchema.MIN_NAME_LENGTH} characters'
        elif len(name) > UserSchema.MAX_NAME_LENGTH:
            errors['name'] = f'Name cannot exceed {UserSchema.MAX_NAME_LENGTH} characters'
        
        # ============= OPTIONAL FIELDS =============
        if 'age' in data and data['age'] is not None:
            age_error = UserSchema._validate_age(data['age'])
            if age_error:
                errors['age'] = age_error
        
        return len(errors) == 0, errors
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Simple email validation (production would use regex library)"""
        return '@' in email and '.' in email.split('@')[1]
    
    @staticmethod
    def _validate_password(password: str) -> str:
        """
        Validate password strength.
        
        Returns empty string if valid, or error message if invalid.
        """
        if len(password) < UserSchema.MIN_PASSWORD_LENGTH:
            return f'Password must be at least {UserSchema.MIN_PASSWORD_LENGTH} characters'
        
        if len(password) > UserSchema.MAX_PASSWORD_LENGTH:
            return f'Password cannot exceed {UserSchema.MAX_PASSWORD_LENGTH} characters'
        
        if not any(c.isupper() for c in password):
            return 'Password must contain at least one uppercase letter'
        
        if not any(c.islower() for c in password):
            return 'Password must contain at least one lowercase letter'
        
        if not any(c.isdigit() for c in password):
            return 'Password must contain at least one digit'
        
        return ''  # Empty string means no error
    
    @staticmethod
    def _validate_age(age: Any) -> str:
        """Validate age field"""
        try:
            age_int = int(age)
        except (ValueError, TypeError):
            return f'Age must be a number, received {type(age).__name__}'
        
        if age_int < 0:
            return 'Age cannot be negative'
        
        if age_int > 150:
            return 'Age seems unrealistic (> 150 years)'
        
        return ''

@app.route('/users', methods=['POST'])
def create_user_with_schema():
    """Create user with schema-based validation"""
    data = request.get_json()
    
    valid, errors = UserSchema.validate(data)
    
    if not valid:
        return {
            'error': 'Validation failed',
            'details': errors
        }, 400
    
    # Data is validated, proceed with creation
    return {
        'id': 1,
        'email': data['email'],
        'name': data['name'],
        'status': 'created'
    }, 201
```

---

## Query String Parameters

Query parameters are key-value pairs appended to the URL after a `?` symbol. They're used for filtering, sorting, pagination, and search functionality. Unlike request body data, query parameters are visible in the URL and should never contain sensitive information.

### Understanding Query Parameters

URL structure with query parameters:

```
https://example.com/api/products?category=electronics&min_price=100&page=2
                                 ↑
                                 All parameters after the ? are query parameters

Breaking it down:
- category=electronics    → filter by electronics category
- min_price=100          → filter by minimum price of 100
- page=2                 → return page 2 of results
```

### Basic Query Parameters

Flask provides the `request.args` object to access query parameters (very similar to `request.form`):

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/search')
def search():
    """
    Search for products with query parameters.
    
    URL example: GET /search?q=flask&category=tutorial&page=2
    """
    
    # Get individual parameters using .get()
    # .get() returns None if parameter not provided (safe, no KeyError)
    query = request.args.get('q', '')  # Default to empty string if missing
    category = request.args.get('category')  # Returns None if missing
    
    # Type conversion - convert string to integer
    # If conversion fails, returns None (3rd parameter provides default)
    page = request.args.get('page', 1, type=int)
    # If URL has page=abc (non-numeric), this would return 1 (default)
    
    # Access all query parameters as a dictionary
    all_params = request.args.to_dict()
    
    return {
        'query': query,
        'category': category,
        'page': page,
        'all_parameters': all_params
    }
```

**Testing basic query parameters:**

```bash
# Simple query parameter
curl "http://localhost:5000/search?q=flask"
# Response: {"query":"flask","category":null,"page":1,"all_parameters":{"q":"flask"}}

# Multiple parameters
curl "http://localhost:5000/search?q=flask&category=tutorial&page=2"
# Response: {"query":"flask","category":"tutorial","page":2,...}

# Parameter with special characters (URL-encoded)
curl "http://localhost:5000/search?q=flask%20tutorial"
# %20 is URL-encoding for space
# Response: {"query":"flask tutorial",...}

# Missing parameter uses default
curl "http://localhost:5000/search?q=flask"
# page isn't provided, so it uses default value of 1
# Response: {"page":1,...}
```

### Multiple Values for Same Parameter

Sometimes you need multiple values for the same parameter (e.g., multiple categories):

```python
@app.route('/filter')
def filter_items():
    """
    Handle multiple values for the same query parameter.
    
    URLs like: /filter?tags=python&tags=flask&tags=api
    """
    
    # getlist() returns a list of all values for a parameter
    # If parameter doesn't exist, returns empty list []
    tags = request.args.getlist('tags')
    # tags = ['python', 'flask', 'api']
    
    # getlist() can also do type conversion
    ids = request.args.getlist('ids', type=int)
    # URL: /filter?ids=1&ids=2&ids=3
    # ids = [1, 2, 3]
    
    # getlist() for float values
    prices = request.args.getlist('prices', type=float)
    
    return {
        'tags': tags,
        'tag_count': len(tags),
        'ids': ids,
        'prices': prices
    }
```

**Testing multiple values:**

```bash
# Multiple tags
curl "http://localhost:5000/filter?tags=python&tags=flask&tags=api"
# Response: {"tags":["python","flask","api"],"tag_count":3,...}

# Multiple numeric IDs
curl "http://localhost:5000/filter?ids=1&ids=2&ids=3&ids=5"
# Response: {"ids":[1,2,3,5],...}

# Mixed parameters
curl "http://localhost:5000/filter?tags=python&tags=django&ids=10&ids=20"
```

### Pagination Pattern

Pagination is crucial for handling large datasets efficiently:

```python
@app.route('/items')
def list_items():
    """
    Implement proper pagination for large result sets.
    
    Query parameters:
    - page: Which page (1-indexed, default 1)
    - per_page: Items per page (default 20, max 100)
    """
    
    # ============= GET PAGINATION PARAMETERS =============
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # ============= VALIDATE PAGINATION PARAMETERS =============
    # Protect against invalid pagination requests
    if page < 1:
        return {
            'error': 'Invalid page number',
            'message': 'Page must be >= 1',
            'received': page
        }, 400
    
    if per_page < 1 or per_page > 100:
        return {
            'error': 'Invalid per_page value',
            'message': 'per_page must be between 1 and 100',
            'received': per_page
        }, 400
    
    # ============= CALCULATE DATABASE OFFSET =============
    # Convert page number to database offset
    # Page 1 = offset 0, Page 2 = offset 20, etc.
    offset = (page - 1) * per_page
    
    # ============= FETCH DATA FROM DATABASE =============
    # Pseudo-code - would use actual database
    # items = db.query(Item).limit(per_page).offset(offset).all()
    # total = db.query(Item).count()
    
    # For demo purposes:
    items = [
        {'id': i, 'name': f'Item {i}'}
        for i in range(offset + 1, offset + per_page + 1)
    ]
    total = 250  # Pretend we have 250 items total
    
    # ============= CALCULATE PAGINATION METADATA =============
    total_pages = (total + per_page - 1) // per_page  # Ceiling division
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': has_next,
            'has_prev': has_prev,
            'next_page': page + 1 if has_next else None,
            'prev_page': page - 1 if has_prev else None
        }
    }
```

**Testing pagination:**

```bash
# Get first page (default 20 items)
curl "http://localhost:5000/items"
# Response: {"items":[...20 items...],"pagination":{"page":1,...,"total":250,"total_pages":13,...}}

# Get page 2 with 10 items per page
curl "http://localhost:5000/items?page=2&per_page=10"
# Response: pagination shows page 2, items 11-20

# Invalid page number
curl "http://localhost:5000/items?page=-1"
# Error: Page must be >= 1

# Invalid per_page
curl "http://localhost:5000/items?per_page=1000"
# Error: per_page must be between 1 and 100
```

### Filtering and Sorting

Combine filtering and sorting for powerful search capabilities:

```python
@app.route('/products')
def list_products():
    """
    List products with filtering, sorting, and pagination.
    
    Query parameters:
    - Filtering: category, min_price, max_price, in_stock
    - Sorting: sort_by, order (asc/desc)
    - Pagination: page, per_page
    """
    
    # ============= FILTERING PARAMETERS =============
    category = request.args.get('category')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    in_stock = request.args.get('in_stock', type=bool)
    
    # ============= SORTING PARAMETERS =============
    sort_by = request.args.get('sort_by', 'created_at')
    order = request.args.get('order', 'desc')
    
    # ============= PAGINATION PARAMETERS =============
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # ============= VALIDATE SORTING =============
    # Only allow sorting by whitelisted fields (security)
    # Don't allow users to sort by fields they shouldn't access
    allowed_sort_fields = ['name', 'price', 'rating', 'created_at', 'views']
    
    if sort_by not in allowed_sort_fields:
        return {
            'error': 'Invalid sort_by field',
            'received': sort_by,
            'allowed_fields': allowed_sort_fields
        }, 400
    
    if order not in ['asc', 'desc']:
        return {
            'error': 'Invalid order - must be "asc" or "desc"',
            'received': order
        }, 400
    
    # ============= BUILD QUERY FILTER =============
    # In real app, would use these to build database query
    filters = {}
    if category:
        filters['category'] = category
    if min_price is not None:
        filters['min_price'] = min_price
    if max_price is not None:
        filters['max_price'] = max_price
    if in_stock is not None:
        filters['in_stock'] = in_stock
    
    # Pseudo-code for database query:
    # query = db.query(Product)
    # if category: query = query.filter_by(category=category)
    # if min_price: query = query.filter(Product.price >= min_price)
    # if max_price: query = query.filter(Product.price <= max_price)
    # if in_stock: query = query.filter_by(in_stock=True)
    # products = query.order_by(sort_by, order).limit(per_page).offset(offset).all()
    
    return {
        'products': [],  # Would contain actual products
        'filters': {k: v for k, v in filters.items() if v is not None},
        'sort': {
            'by': sort_by,
            'order': order
        },
        'pagination': {
            'page': page,
            'per_page': per_page
        }
    }
```

**Testing complex queries:**

```bash
# Simple filter
curl "http://localhost:5000/products?category=electronics"

# Multiple filters
curl "http://localhost:5000/products?category=electronics&min_price=100&max_price=500&in_stock=true"

# With sorting
curl "http://localhost:5000/products?category=electronics&sort_by=price&order=asc"

# Full complex query
curl "http://localhost:5000/products?category=electronics&min_price=100&max_price=500&in_stock=true&sort_by=price&order=asc&page=1&per_page=50"

# Invalid sort field
curl "http://localhost:5000/products?sort_by=secret_field"
# Error: Invalid sort_by field - only allowed fields can be used
```

---

## Request Lifecycle

Understanding how Flask processes a request is essential for debugging and implementing hooks properly. Every request goes through several stages:

### The Complete Request Lifecycle Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      REQUEST LIFECYCLE                          │
└─────────────────────────────────────────────────────────────────┘

1. CLIENT SENDS REQUEST
   └─> HTTP request created with method, URL, headers, body

2. WEB SERVER (nginx/Apache) RECEIVES REQUEST
   └─> Receives raw HTTP request from network

3. WSGI SERVER (Gunicorn/uWSGI) CREATES ENVIRON
   └─> Creates environ dictionary with CGI variables
   └─> environ['REQUEST_METHOD'], environ['PATH_INFO'], etc.

4. FLASK CREATES REQUEST CONTEXT
   └─> Pushes application and request contexts
   └─> Makes request object available to route handlers
   └─> g object created for storing request-specific data

5. @app.before_request HANDLERS RUN
   └─> Authentication checks
   └─> Logging/tracing setup
   └─> Request validation
   └─> Can return response to short-circuit request

6. URL ROUTING MATCHES PATH
   └─> Flask matches URL to route handler function
   └─> Extracts URL parameters (if any)

7. ROUTE HANDLER EXECUTES
   └─> Your function runs
   └─> Accesses request, g, sessions, etc.
   └─> Returns response data

8. @app.after_request HANDLERS RUN
   └─> Add response headers
   └─> Logging
   └─> Modification of response before sending
   └─> Response object available

9. RESPONSE SENT TO CLIENT
   └─> Flask sends HTTP response with status, headers, body

10. @app.teardown_request HANDLERS RUN
    └─> Cleanup database connections
    └─> Cleanup temporary files
    └─> Logging
    └─> Runs even if exception occurred

11. REQUEST CONTEXT TORN DOWN
    └─> g object destroyed
    └─> Request object destroyed
    └─> Application context destroyed
```

### Using Before and After Request Hooks

These hooks allow you to run code at specific points in the request lifecycle:

```python
from flask import Flask, request, g
import time
import uuid
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

# ============= BEFORE REQUEST =============
@app.before_request
def before_request():
    """
    Runs before each request (before route handler).
    
    This is where you typically do:
    - Request timing (start time)
    - Request tracing (generate request ID)
    - Authentication (check token)
    - Rate limiting checks
    - Database connection setup
    """
    
    # Record request start time
    g.start_time = time.time()
    # Store in g object - available throughout this request only
    
    # Generate or get request ID for distributed tracing
    g.request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
    # Each request gets unique ID for tracing through logs
    
    # Log request details
    logger.info(f'[{g.request_id}] {request.method} {request.path}')
    
    # Example: Authenticate user (simplified)
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]  # Remove "Bearer " prefix
        # In real app: user = authenticate_token(token)
        # g.user = user

@app.after_request
def after_request(response):
    """
    Runs after request handler, before response is sent to client.
    
    This is where you:
    - Add response headers
    - Log response status
    - Calculate response time
    - CORS headers
    - Security headers
    """
    
    # Add request ID to response headers for correlation
    response.headers['X-Request-ID'] = g.get('request_id', 'unknown')
    
    # Calculate request time
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        response.headers['X-Response-Time'] = f"{elapsed:.3f}s"
        # Format: "0.234s" (3 decimal places)
        
        # Log response with timing
        logger.info(
            f'[{g.request_id}] Response: {response.status_code} '
            f'in {elapsed:.3f}s'
        )
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Add CORS headers (if needed)
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    return response
    # Must return the response object

@app.teardown_request
def teardown_request(exception=None):
    """
    Runs after request is sent to client (cleanup phase).
    
    Runs even if exception occurred!
    
    This is where you:
    - Close database connections
    - Clean temporary files
    - Shutdown resource pools
    - Final logging
    """
    
    request_id = g.get('request_id', 'unknown')
    
    # Log if exception occurred
    if exception:
        logger.error(
            f'[{request_id}] Request failed with exception: {exception}',
            exc_info=True
        )
    
    # Example: Close database connection
    # db = g.pop('db', None)
    # if db is not None:
    #     db.close()
    
    logger.debug(f'[{request_id}] Teardown complete')

@app.route('/api/data')
def get_data():
    """
    Example route showing how lifecycle hooks provide context.
    """
    return {
        'request_id': g.get('request_id'),
        'elapsed_so_far': time.time() - g.start_time,
        'authenticated': hasattr(g, 'user'),
        'message': 'This route executed successfully'
    }
```

**Testing the lifecycle hooks:**

```bash
# Make a request and observe the headers
curl -X GET http://localhost:5000/api/data \
  -H "X-Request-ID: my-trace-id-123"

# Response headers will include:
# X-Request-ID: my-trace-id-123
# X-Response-Time: 0.045s
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY

# Logs would show:
# [my-trace-id-123] GET /api/data
# [my-trace-id-123] Response: 200 in 0.045s
```

---

## Common Request Handling Mistakes and How to Fix Them

Learning from common mistakes helps you avoid security vulnerabilities and runtime errors. Let's examine real-world problems and solutions.

### Mistake 1: Not Checking Content-Type Before Parsing JSON

**Problem:** The application crashes when clients don't send proper Content-Type headers.

```python
# ❌ BAD - UNSAFE
@app.route('/data', methods=['POST'])
def receive_data():
    """This will crash if Content-Type isn't application/json"""
    data = request.get_json()  # May return None if Content-Type is wrong
    
    # Assuming data is a dict, but it might be None
    email = data['email']  # ❌ TypeError: 'NoneType' object is not subscriptable
    # This crashes if data is None!
```

**Why this fails:**
- `request.get_json()` returns `None` if Content-Type is not `application/json`
- Trying to access `data['email']` when `data` is `None` causes a TypeError
- The API crashes with a 500 error instead of returning a helpful 400 error

**Fix:**

```python
# ✅ GOOD - SAFE
@app.route('/data', methods=['POST'])
def receive_data():
    """This handles missing or wrong Content-Type gracefully"""
    
    # Step 1: Verify Content-Type header
    if not request.is_json:
        return {
            'error': 'Invalid Content-Type',
            'message': 'Content-Type header must be "application/json"',
            'received': request.content_type
        }, 400  # 400 Bad Request (client's fault)
    
    # Step 2: Parse JSON
    data = request.get_json()
    
    # Step 3: Check if body is empty
    if data is None:
        return {'error': 'Request body cannot be empty'}, 400
    
    # Now we can safely access data
    email = data.get('email')  # Safe - returns None if not present
    
    if not email:
        return {'error': 'Email field is required'}, 400
    
    return {'email': email}
```

### Mistake 2: Trusting User Input Without Validation

**Problem:** Security vulnerability allowing SQL injection, path traversal, and data corruption.

```python
# ❌ BAD - DANGEROUS!
@app.route('/users/<username>')
def get_user(username):
    """
    This is vulnerable to SQL injection!
    If username = "admin' OR '1'='1", the query becomes:
    SELECT * FROM users WHERE username = 'admin' OR '1'='1'
    Which returns ALL users!
    """
    from your_db import db
    query = f"SELECT * FROM users WHERE username = '{username}'"
    user = db.execute(query)
    return user

# ❌ BAD - Path traversal vulnerability!
@app.route('/download/<filename>')
def download_file(filename):
    """
    If filename = "../../etc/passwd", user can download system files!
    """
    filepath = f'/uploads/{filename}'
    return send_file(filepath)
```

**Why this is dangerous:**
- Unvalidated user input is the #1 source of security vulnerabilities
- SQL injection allows attackers to modify/delete database records
- Path traversal allows attackers to access files they shouldn't

**Fix:**

```python
# ✅ GOOD - SAFE
from flask import send_file
from werkzeug.utils import secure_filename
import os

@app.route('/users/<username>')
def get_user(username):
    """
    Use ORM or parameterized queries, NOT string interpolation.
    The ORM (or database driver) handles escaping dangerous characters.
    """
    from your_db import User, db
    
    # ORM handles SQL escaping automatically
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return {'error': 'User not found'}, 404
    
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email
    }

@app.route('/download/<filename>')
def download_file(filename):
    """
    Use secure_filename to prevent path traversal.
    secure_filename removes "..", "/", and other dangerous characters.
    """
    
    # secure_filename prevents path traversal attacks
    safe_filename = secure_filename(filename)
    
    # Verify file exists in allowed directory
    upload_folder = '/uploads'
    filepath = os.path.join(upload_folder, safe_filename)
    
    # Extra safety: ensure resolved path is still in upload folder
    resolved = os.path.realpath(filepath)
    if not resolved.startswith(os.path.realpath(upload_folder)):
        return {'error': 'Access denied'}, 403
    
    if not os.path.exists(filepath):
        return {'error': 'File not found'}, 404
    
    return send_file(filepath)
```

### Mistake 3: Not Validating File Uploads

**Problem:** User uploads malicious files that:
- Consume all disk space (DoS attack)
- Execute code on the server (RCE attack)
- Overwrite existing files

```python
# ❌ BAD - DANGEROUS!
@app.route('/upload', methods=['POST'])
def upload():
    """
    This endpoint has multiple security problems.
    """
    file = request.files['file']
    
    # ❌ Problem 1: No validation - user can upload anything
    # ❌ Problem 2: Path traversal - filename could be "../../evil.exe"
    # ❌ Problem 3: No size limit - user could upload 1GB file
    file.save(f'/uploads/{file.filename}')
    
    return {'uploaded': True}
```

**Why this is dangerous:**
- No file type validation - user uploads .exe, .sh, .bat
- Path traversal - filename = "../../../../tmp/bomb.zip"
- No size limits - user uploads terabyte file, crashes server

**Fix:**

```python
# ✅ GOOD - VALIDATED
import os
from werkzeug.utils import secure_filename
from datetime import datetime

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

@app.route('/upload', methods=['POST'])
def upload():
    """
    File upload with proper security validations.
    """
    
    # ============ VALIDATION 1: FILE PRESENCE ============
    if 'file' not in request.files:
        return {'error': 'No file provided'}, 400
    
    file = request.files['file']
    
    # ============ VALIDATION 2: FILENAME NOT EMPTY ============
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    
    # ============ VALIDATION 3: FILE EXTENSION ============
    # Extract and validate extension
    if '.' not in file.filename:
        return {'error': 'File must have an extension'}, 400
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    
    if extension not in ALLOWED_EXTENSIONS:
        return {
            'error': f'File type not allowed',
            'allowed': list(ALLOWED_EXTENSIONS),
            'received': extension
        }, 400
    
    # ============ VALIDATION 4: FILE SIZE ============
    file.seek(0, os.SEEK_END)  # Seek to end
    size = file.tell()  # Get position (= size)
    file.seek(0)  # Seek back to start
    
    if size == 0:
        return {'error': 'File is empty'}, 400
    
    if size > MAX_FILE_SIZE:
        return {
            'error': 'File too large',
            'max_mb': MAX_FILE_SIZE / (1024 * 1024),
            'your_mb': size / (1024 * 1024)
        }, 413
    
    # ============ SECURE FILENAME ============
    # This removes/escapes dangerous characters
    safe_filename = secure_filename(file.filename)
    
    # Add timestamp to avoid collisions
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    final_filename = f'{timestamp}_{safe_filename}'
    
    # ============ SAVE FILE ============
    upload_folder = '/tmp/uploads'
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, final_filename)
    file.save(filepath)
    
    return {
        'message': 'File uploaded successfully',
        'filename': final_filename,
        'size_mb': round(size / (1024 * 1024), 2)
    }, 201
```

### Mistake 4: Accessing Missing Dictionary Keys

**Problem:** Application crashes when expected JSON field is missing.

```python
# ❌ BAD - CRASHES
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # If 'email' is missing, this raises KeyError
    email = data['email']  # ❌ KeyError if 'email' not in data
```

**Fix:**

```python
# ✅ GOOD - SAFE
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Method 1: Use .get() to handle missing keys
    email = data.get('email')  # Returns None if not present
    
    # Method 2: Use .get() with default
    role = data.get('role', 'user')  # Returns 'user' if not present
    
    # Method 3: Validate presence first
    if 'email' not in data:
        return {'error': 'Email field required'}, 400
    
    email = data['email']
```

### Mistake 5: Not Handling Empty Request Bodies

**Problem:** Application crashes when request body is empty.

```python
# ❌ BAD
@app.route('/data', methods=['POST'])
def receive():
    data = request.get_json()  # Returns None if body is empty
    name = data['name']  # ❌ TypeError if data is None
```

**Fix:**

```python
# ✅ GOOD
@app.route('/data', methods=['POST'])
def receive():
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400
    
    data = request.get_json()
    
    if not data:  # data is None or empty dict
        return {'error': 'Request body cannot be empty'}, 400
    
    name = data.get('name')
    if not name:
        return {'error': 'Name field required'}, 400
    
    return {'name': name}
```

---

## Summary

Request handling is one of the most critical aspects of web development. A single security oversight or validation error can compromise your entire application. Let's recap the key concepts:

### Core Concepts Covered

**The Request Object**
- Flask's `request` object provides access to all information about incoming HTTP requests
- Contains properties for URL info, HTTP method, client details, and metadata
- Always available within request context (route handlers, before/after hooks)

**Headers**
- Crucial metadata about the request
- Used for authentication, versioning, content negotiation, and custom data
- Always validate and never trust header values

**JSON Handling**
- Check `request.is_json` before parsing
- Always validate JSON data structure and types
- Handle malformed JSON gracefully with try-except

**Form Data**
- URL-encoded forms for traditional HTML submissions
- Multipart forms for file uploads
- Always use `secure_filename()` for uploaded files

**File Uploads**
- Validate file extensions against a whitelist
- Enforce file size limits
- Check file existence before accessing
- Use `secure_filename()` to prevent path traversal

**Input Validation**
- CRITICAL: Never trust user input
- Implement validation at multiple levels:
  1. Type validation (is it the right data type?)
  2. Format validation (does it match expected pattern?)
  3. Business logic validation (does it make sense for our app?)
- Return clear error messages with specific field names

**Query Parameters**
- Use `request.args.get()` for single values
- Use `request.args.getlist()` for multiple values
- Always validate and whitelist allowed parameters
- Implement proper pagination for large datasets

### Best Practices Summary

```
✅ DO:
├─ Check Content-Type before parsing request body
├─ Validate ALL user input
├─ Use parameterized queries to prevent SQL injection
├─ Use secure_filename() for file uploads
├─ Implement rate limiting for file uploads
├─ Return clear error messages with status codes
├─ Use decorators to reduce validation code repetition
├─ Check file existence and permissions
├─ Whitelist allowed file extensions
├─ Implement pagination for large result sets
└─ Log security-relevant events (failed auth, suspicious uploads)

❌ DON'T:
├─ Trust user input
├─ Build SQL queries with string concatenation
├─ Allow arbitrary file extensions
├─ Accept unlimited file sizes
├─ Expose sensitive data in error messages
├─ Skip validation of optional fields
├─ Allow path traversal in file operations
├─ Mix Content-Type assumptions with code
├─ Store uploaded files with original filename
└─ Forget to handle empty request bodies
```

### Request Handling Security Checklist

```python
@app.route('/api/endpoint', methods=['POST'])
def secure_endpoint():
    """Template for secure request handling"""
    
    # 1. Content-Type validation
    if not request.is_json:
        return {'error': 'Content-Type must be application/json'}, 400
    
    # 2. Parse request
    data = request.get_json()
    
    # 3. Check for empty body
    if not data:
        return {'error': 'Request body cannot be empty'}, 400
    
    # 4. Validate presence of required fields
    required_fields = ['field1', 'field2']
    missing = [f for f in required_fields if f not in data]
    if missing:
        return {'error': 'Missing required fields', 'missing': missing}, 400
    
    # 5. Validate field types
    if not isinstance(data.get('field1'), str):
        return {'error': 'field1 must be a string'}, 400
    
    # 6. Implement business logic validation
    # (check for valid email, password strength, etc.)
    
    # 7. Sanitize data (strip whitespace, lowercase, etc.)
    field1 = data['field1'].strip().lower()
    
    # 8. Process request
    # (create database record, call external API, etc.)
    
    # 9. Return appropriate response
    return {'id': 1, 'status': 'created'}, 201
```

### Key Takeaways

1. **Security First**: Every piece of user input is a potential attack vector. Always validate.

2. **Fail Fast**: Return errors early with helpful messages and correct HTTP status codes.

3. **Defense in Depth**: Implement validation at multiple layers:
   - Client side (UX)
   - API input validation
   - Database constraints
   - Business logic

4. **Clear Error Messages**: Help clients understand what went wrong:
   ```python
   # GOOD
   {'error': 'Email format invalid', 'field': 'email', 'example': 'user@example.com'}
   
   # BAD
   {'error': 'Invalid input'}
   ```

5. **HTTP Status Codes Matter**:
   - 400 Bad Request - client's fault (invalid input)
   - 401 Unauthorized - authentication failed
   - 403 Forbidden - authenticated but not allowed
   - 404 Not Found - resource doesn't exist
   - 413 Payload Too Large - file too big
   - 500 Internal Server Error - server's fault

6. **Test Your Validation**: Write tests for all validation paths:
   ```python
   def test_missing_email():
       """Test that missing email returns 400"""
       resp = client.post('/users', json={'password': 'test'})
       assert resp.status_code == 400
       assert 'email' in resp.json['error']
   ```

---

## Practice Exercises

### Exercise 1: Complete API Endpoint

Build a `/products` endpoint that demonstrates all request handling concepts:

```
Requirements:
1. Accept POST requests with JSON body
2. Required fields: name, price, category, stock_quantity
3. Validate:
   - All fields present
   - name is string (2-100 chars)
   - price is number (>0)
   - category is one of: electronics, clothing, books
   - stock_quantity is integer (>=0)
4. Return 201 Created with product details
5. Return 400 with clear errors on validation failure
6. Log successful creation
```

### Exercise 2: File Upload API

Build a `/upload` endpoint with comprehensive validation:

```
Requirements:
1. Accept multipart form data with file
2. Allowed types: jpg, png, pdf
3. Max size: 10MB
4. Return error if:
   - No file provided
   - Wrong type
   - Too large
5. Save with secure filename
6. Return upload details (filename, size, URL)
```

### Exercise 3: Search API

Build a `/search` endpoint with query parameters:

```
Requirements:
1. Accept GET requests with query parameters
2. Parameters:
   - q: search query (required)
   - category: filter by category (optional)
   - sort_by: sort field (optional, whitelist: name, date)
   - page: pagination (default 1)
   - per_page: items per page (default 20, max 100)
3. Validate all parameters
4. Return results with metadata
5. Include pagination info
```

### Debugging Scenario

You have this endpoint that's getting reports of 500 errors:

```python
@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    items = data['items']  # Line X
    total = sum(item['price'] * item['quantity'] for item in items)  # Line Y
    return {'total': total}, 201
```

**Reported Issues:**
1. "Sometimes returns TypeError: 'NoneType' object is not subscriptable"
2. "Sometimes returns TypeError: unsupported operand type(s)"
3. "Sometimes returns KeyError: 'price' or 'quantity'"
4. "Sometimes returns 500 without clear error message"

**Your Tasks:**
1. Identify what causes each error
2. Write a production-ready version with proper validation
3. Explain what error messages the client should receive
4. List all edge cases that need testing

---

**Next Module**: [Response Formats](05-response-formats.md)
