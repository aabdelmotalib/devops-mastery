# Module 2: HTTP/HTTPS Protocol

## What HTTP Actually Does

HTTP is just **a way to format messages over TCP**.

Your Flask app doesn't send random bytes. It sends messages formatted according to HTTP rules. The client expects this format and knows how to parse it.

```
TCP Connection (from Module 1)
    ↓
HTTP Protocol (formatting rules)
    ↓
Your app processes and responds
    ↓
HTTP formatted response back
    ↓
Client understands response
```

HTTP solved a problem: "How do we describe what we want from a web server?"

## HTTP Request/Response Lifecycle

### Step-by-Step Flow

```
1. Client creates TCP connection
   Client: connect to 203.0.113.45:80

2. Client sends HTTP request
   Client: "GET /api/users HTTP/1.1"
           "Host: example.com"
           "..."

3. Server receives entire request
   Server: Reading from socket

4. Server parses request
   Server: Method=GET, Path=/api/users, ...

5. Server processes
   Server: Finds users, formats JSON

6. Server sends HTTP response
   Server: "HTTP/1.1 200 OK"
           "Content-Type: application/json"
           "[{\"id\": 1, ...}]"

7. Client receives and parses
   Client: Status 200, Content-Type json, body parsed

8. Connection closes (usually)
   Both sides close TCP connection
```

## Anatomy of an HTTP Request

### Basic Structure

```
GET /api/users HTTP/1.1
Host: example.com
User-Agent: curl/7.64.1
Accept: application/json

```

Breaking it down:

```
GET                  = HTTP Method (verb)
/api/users           = Path (resource being requested)
HTTP/1.1             = Protocol version

[blank line]
Headers              = Additional metadata

[blank line]
Body                 = Optional (GET requests usually have no body)
```

### Real Example with Python Requests

```python
import requests

response = requests.get(
    'https://api.example.com/api/users',
    headers={
        'Authorization': 'Bearer token123',
        'Accept': 'application/json'
    }
)

# What actually gets sent over TCP:
# GET /api/users HTTP/1.1
# Host: api.example.com
# User-Agent: python-requests/2.28.0
# Accept: application/json
# Authorization: Bearer token123
# 
# (blank line, no body for GET)
```

### Raw HTTP Request (Real)

```bash
# Send raw HTTP request using netcat
(
  echo -ne "GET /api/users HTTP/1.1\r\n"
  echo -ne "Host: 192.168.1.100:5000\r\n"
  echo -ne "Connection: close\r\n"
  echo -ne "\r\n"
) | nc 192.168.1.100 5000

# Output:
# HTTP/1.1 200 OK
# Content-Type: application/json
# Content-Length: 42
# 
# [{"id": 1, "name": "Alice"}, ...]
```

## HTTP Methods (Verbs)

HTTP methods describe what action you want to perform.

### Core Methods (CRUD)

| Method | Action | Has Body? | Idempotent? | Use When |
|--------|--------|-----------|-------------|----------|
| GET | Retrieve | No | Yes | Want to read data |
| POST | Create | Yes | No | Want to create new resource |
| PUT | Replace | Yes | Yes | Want to replace entire resource |
| PATCH | Modify | Yes | No | Want to update part of resource |
| DELETE | Remove | No | Yes | Want to delete resource |

### Idempotent Explained

**Idempotent**: Calling multiple times = calling once

```
GET /api/users
GET /api/users (again)
GET /api/users (again)

Result: Same response all three times (idempotent)

DELETE /api/users/123
DELETE /api/users/123 (again, already deleted)

Result: First time 204 No Content, second time 404 Not Found
(NOT idempotent - different results)
```

### Real Backend Examples

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

# GET: Retrieve
@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Database query to get user
    return jsonify({'id': user_id, 'name': 'Alice'})

# POST: Create
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    # Database insert new user
    return jsonify({'id': new_id, 'name': data['name']}), 201

# PUT: Replace entire resource
@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.json
    # Delete old user, insert with new data
    return jsonify({'id': user_id, 'name': data['name']})

# PATCH: Update part of resource
@app.route('/api/users/<int:user_id>', methods=['PATCH'])
def patch_user(user_id):
    data = request.json
    # Update only the fields provided
    return jsonify({'id': user_id, 'name': data.get('name')})

# DELETE: Remove
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Delete from database
    return '', 204
```

## HTTP Status Codes (Understanding Them)

Status codes are 3-digit numbers that tell the client what happened.

### 2xx Success

```
200 OK              Request succeeded, response has body
201 Created         Resource was created (POST usually)
204 No Content      Request succeeded, no response body (DELETE usually)
```

### 3xx Redirection

```
301 Moved Permanently   Resource moved, client should use new URL forever
302 Found               Temporary redirect, try this URL but remember original
304 Not Modified        Client has cached version, it's still valid
```

### 4xx Client Error

```
400 Bad Request         Request is malformed/invalid
401 Unauthorized        Missing authentication (no login credentials)
403 Forbidden           Authenticated but not allowed (permission denied)
404 Not Found           Resource doesn't exist
409 Conflict            Request conflicts with current state
429 Too Many Requests   Rate limiting hit
```

### 5xx Server Error

```
500 Internal Server Error   Unhandled exception in your code
502 Bad Gateway             Proxy can't reach backend
503 Service Unavailable     Server is down/overloaded
```

### Correct Usage in Your Code

```python
from flask import Flask, jsonify

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    
    # Validate input
    if not data.get('email'):
        return jsonify({'error': 'email required'}), 400  # Bad Request
    
    # Check if already exists
    existing = User.query.filter_by(email=data['email']).first()
    if existing:
        return jsonify({'error': 'email already exists'}), 409  # Conflict
    
    try:
        # Create in database
        user = User(email=data['email'], name=data['name'])
        db.session.add(user)
        db.session.commit()
        return jsonify({'id': user.id}), 201  # Created
    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Internal Server Error
```

## HTTP Headers (The Metadata)

Headers provide information about the request/response, not the actual data.

### Common Request Headers

```
Host: example.com
        Who you're talking to (required in HTTP/1.1)

Content-Type: application/json
        Format of body data

Authorization: Bearer token123
        Authentication credentials

Accept: application/json
        What format the client wants in response

User-Agent: curl/7.64.1
        What software is making the request

Cache-Control: no-cache
        Caching instructions

X-Custom-Header: value
        Custom headers (usually start with X-)
```

### Common Response Headers

```
Content-Type: application/json
        Format of response body

Content-Length: 1234
        Size of response body in bytes

Set-Cookie: session=abc123
        Tells client to remember a cookie

Cache-Control: max-age=3600
        How long client can cache this

X-RateLimit-Remaining: 99
        Custom headers from your app
```

### Backend Use: Setting Headers in Flask

```python
from flask import Flask, make_response

@app.route('/api/data')
def get_data():
    response = make_response({'message': 'hello'})
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'max-age=3600'
    response.headers['X-RateLimit-Remaining'] = '99'
    return response
```

## HTTP Versioning

### HTTP/1.1 (Current Standard)

Most common. What you're probably using.

```
GET /api/users HTTP/1.1

Pros:
- Well understood
- Works everywhere
- Simple debugging

Cons:
- One request at a time per connection
- Need multiple connections for performance
```

### HTTP/2 (Modern)

Binary protocol, multiplexing.

```
GET /api/users HTTP/2

Pros:
- Multiple requests on single connection
- Better performance
- Header compression

Cons:
- Harder to debug (binary)
- Older systems don't support it
```

### HTTP/3 (Newest)

Over UDP instead of TCP.

```
Pros:
- Even faster
- Works with packet loss better

Cons:
- Very new
- Not widely used yet for backends
```

**For backends**: HTTP/1.1 is fine. Nginx/reverse proxies handle the version translation.

## HTTPS: HTTP + TLS Encryption

HTTPS is just HTTP sent through an encrypted tunnel (TLS).

### Without HTTPS

```
Client                                      Server
  |                                           |
  | --- Hello, I want to talk to bank.com -->|
  | (visible on internet)                    |
  |                                           |
  | <--- Here's my password: 12345 --------- |
  | (visible on internet)                    |
  |                                           |
  | (Hacker intercepts and steals password)  |
```

### With HTTPS

```
Client                                      Server
  |                                           |
  | --- Let's establish secure tunnel ------>|
  |     (TLS handshake)                      |
  |                                           |
  | <--- Here's my certificate, let's use  --|
  |     this encryption key                  |
  |                                           |
  | [Encrypted tunnel established]           |
  |                                           |
  | --- 🔒 encrypted password 🔒 ----------->|
  |     (only visible as gibberish)          |
  |                                           |
```

### What HTTPS Changes

```
Before HTTPS:
Client connects to example.com:80
Sends: GET /secret HTTP/1.1
Traffic visible: GET /secret

After HTTPS:
Client connects to example.com:443
TLS handshake (encryption keys exchanged)
Sends: [ENCRYPTED: GET /secret]
Traffic visible: Encrypted gibberish
Server sees: decrypted GET /secret
```

The HTTP request format is identical. Only the encryption wrapper changed.

## TLS Handshake (High Level)

Don't memorize the details, but understand the steps:

```
1. Client: "Hello, let's talk securely"
2. Server: "OK, here's my certificate (proves I'm who I say I am)"
3. Client: "I verified your certificate. Here's an encryption key"
4. Server: "Confirmed, we're now encrypted"
5. Client: GET /api/users (now encrypted)
6. Server: [response] (now encrypted)
```

This adds ~100ms to connection time, which is why:

- We use HTTP/2 multiplexing (reuse one connection)
- We use caching (avoid repeated requests)

### Backend Use: When Your App Needs HTTPS

```python
# Your Flask app doesn't need to know about HTTPS details
from flask import Flask
app = Flask(__name__)

@app.route('/api/users')
def get_users():
    return {'users': [...]}

if __name__ == '__main__':
    # Don't run Flask with HTTPS directly (slow)
    # Instead, let a reverse proxy (Nginx) handle TLS
    app.run(host='0.0.0.0', port=5000)  # Plain HTTP
```

Then Nginx handles:

```
Client (HTTPS) -> Nginx (decrypts) -> Flask (HTTP)
```

Why not Flask directly?

1. Nginx is faster at TLS
2. Flask shouldn't handle production HTTPS
3. Load balancers need to see headers

## Connection Management

### Keep-Alive (Reusing Connections)

Without keep-alive:

```
Request 1: Open connection -> Send request -> Receive -> Close
Request 2: Open connection -> Send request -> Receive -> Close
Request 3: Open connection -> Send request -> Receive -> Close

Problem: Opening/closing TCP connections is expensive
```

With keep-alive:

```
Request 1: Open connection -> Send request -> Receive
Request 2: [reuse connection] -> Send request -> Receive
Request 3: [reuse connection] -> Send request -> Receive
           Close connection

Benefit: 10-100x faster for multiple requests
```

### Backend Use

```python
# Flask uses keep-alive by default
# Nginx uses keep-alive by default
# Most HTTP clients use it

# You don't need to do anything special
response = requests.get(url)  # Uses keep-alive
```

### Session Reuse

Keep-alive reconnects on the same TCP socket. But creating the TLS tunnel for each new connection is also expensive.

```
Without session reuse:
Request 1: TCP connect + TLS handshake + request = 150ms
Request 2: TCP connect + TLS handshake + request = 150ms

With session reuse:
Request 1: TCP connect + TLS handshake + request = 150ms
Request 2: [reuse TLS session] + request = 50ms
```

Handled automatically by HTTP clients and browsers. You don't control it.

## Common Mistakes

### Mistake 1: Wrong Status Code

```python
# Wrong
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 200  # WRONG: 200 means success

    db.session.delete(user)
    db.session.commit()
    return {'message': 'deleted'}, 200  # Should be 204

# Right
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return {'error': 'not found'}, 404  # 404: Not Found

    db.session.delete(user)
    db.session.commit()
    return '', 204  # 204: No Content (resource deleted)
```

### Mistake 2: Sending Body on GET

```python
# Wrong: GET request with body
response = requests.get(
    'https://api.example.com/search',
    json={'query': 'users'}  # GET shouldn't have body
)

# Right: Use query parameters
response = requests.get(
    'https://api.example.com/search?query=users'
)

# Or use POST if you need complex body
response = requests.post(
    'https://api.example.com/search',
    json={'query': 'users', 'filters': {...}}
)
```

### Mistake 3: Not Setting Content-Type

```python
# Wrong: Client doesn't know it's JSON
@app.route('/api/users')
def get_users():
    import json
    return json.dumps({'users': [...]})  # Missing Content-Type header

# Right: Use jsonify or set header
@app.route('/api/users')
def get_users():
    return jsonify({'users': [...]})  # Flask sets Content-Type

# Or explicitly:
@app.route('/api/users')
def get_users():
    response = make_response(json.dumps({'users': [...]}))
    response.headers['Content-Type'] = 'application/json'
    return response
```

### Mistake 4: Ignoring Client Errors (4xx)

```python
# Wrong: Accept any input without validation
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    # If email is missing, this crashes (500)
    user = User(email=data['email'], name=data['name'])
    return jsonify(user.to_dict()), 201

# Right: Validate and return 400
@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    
    if not data or not data.get('email') or not data.get('name'):
        return jsonify({'error': 'email and name required'}), 400
    
    user = User(email=data['email'], name=data['name'])
    return jsonify(user.to_dict()), 201
```

## Production Notes

### 1. Always Use HTTPS in Production

```bash
# Certificate from Let's Encrypt (free)
sudo apt install certbot
sudo certbot certonly --standalone -d example.com

# Nginx configuration
server {
    listen 443 ssl;
    server_name example.com;
    
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
    }
}
```

### 2. Set Security Headers

```python
@app.after_request
def set_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response
```

### 3. Proper CORS Headers

```python
from flask_cors import CORS

# Allow specific origins only
CORS(app, resources={
    r"/api/*": {"origins": ["https://example.com", "https://app.example.com"]}
})

# Not this (allows everything):
CORS(app)
```

### 4. Connection Limits

```nginx
# In Nginx reverse proxy
upstream backend {
    server 127.0.0.1:5000 max_conns=100;
}

server {
    listen 443 ssl;
    
    # Limit requests per second per IP
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    
    location /api/ {
        limit_req zone=api burst=20;
        proxy_pass http://backend;
    }
}
```

## Summary Table

| Aspect | What to Know |
|--------|--------------|
| Request Format | Method, Path, Version, Headers, Body |
| Response Format | Status Code, Headers, Body |
| HTTP Methods | GET (read), POST (create), PUT (replace), PATCH (update), DELETE (remove) |
| Status Codes | 2xx success, 3xx redirect, 4xx client error, 5xx server error |
| Headers | Metadata about request/response (Content-Type, Authorization, etc.) |
| HTTP vs HTTPS | HTTPS adds TLS encryption layer, same HTTP format inside |
| Keep-Alive | Reuse TCP connection for multiple requests |
| Your Code | Doesn't need to think about TLS details, reverse proxy handles it |

---

## Module 2 Assessment

### Practice Questions (MCQ - No Answers Provided)

1. A client sends a request but never sends a request body. Which HTTP method most likely?
   a) POST
   b) PUT
   c) GET
   d) PATCH

2. Your API endpoint returns status 200 OK with body `{"error": "user not found"}`. What's the problem?
   a) Should return 404 Not Found instead
   b) Should return 500 Internal Server Error instead
   c) Response format is invalid
   d) Client can't parse the error message

3. HTTP keep-alive improves performance by:
   a) Sending encrypted data
   b) Reusing TCP connection for multiple requests
   c) Compressing response headers
   d) Caching responses on the client

4. Your Flask app needs to accept HTTPS traffic. Which is the recommended approach?
   a) Configure Flask with `ssl_context` parameter
   b) Use a reverse proxy (Nginx) to handle TLS termination
   c) Enable HTTPS on the development server
   d) Use `requests.post()` with `verify=False`

5. A response includes `Content-Type: text/html` but the body is JSON data. What will happen?
   a) Browser will automatically parse as JSON
   b) Client will try to interpret as HTML, likely fail
   c) Server must send correct Content-Type
   d) No problem, Content-Type is just metadata

### Practical Networking Tasks

**Task 1: Inspect HTTP Requests**

- Start a simple web server: `python3 -m http.server 8080`
- Use curl with verbose flag to see request/response: `curl -v http://localhost:8080`
- Note the HTTP method, headers sent, response code, response headers
- Make requests with different methods: POST, GET, HEAD
- Document what changes between requests

**Task 2: HTTP Status Codes**

- Create a simple Flask app with multiple endpoints:
  - GET endpoint that returns 200 OK
  - POST endpoint that returns 201 Created
  - DELETE endpoint that returns 204 No Content
  - GET endpoint for non-existent resource that returns 404
  - POST endpoint that validates input and returns 400 Bad Request
- Use curl to test each: `curl -X POST -H "Content-Type: application/json" -d '{}' http://localhost:5000/endpoint`
- Verify correct status codes are returned

### Production Incident Scenario

**Incident**: Your API is returning status 500 Internal Server Error for POST requests, but GET requests work fine.

```
GET /api/users         → 200 OK (works)
POST /api/users        → 500 Internal Server Error (broken)
```

The logs show:

```
TypeError: 'NoneType' object is not subscriptable
  File "app.py", line 42, in create_user
    email = data['email']
```

Questions:

1. What's likely happening? (Hint: POST usually has JSON body)
2. How would you verify that the request body is being sent?
3. What's the minimal fix needed in the code?
4. What should you return if the request is missing required fields?
5. How would you prevent this error in the future?

---

**Next**: [Module 3: REST API Design](03-rest-api-design.md)
