# Module 1: Flask Fundamentals

## What is Flask?

Flask is a **micro web framework** written in Python for building web applications. The term "micro" is often misunderstood—it doesn't mean Flask is limited or only for small projects. Rather, it means Flask keeps the core lightweight and doesn't make unnecessary decisions for you.

### The Philosophy Behind Flask

Flask was created by Armin Ronacher with a simple philosophy: **"Give you what you need, nothing more, nothing less."** This means:

- **You have control**: Choose your database (SQLAlchemy, Peewee, PyMongo, etc.)
- **You decide the structure**: Organize your project however makes sense
- **You pick the tools**: Use any authentication, validation, or templating library
- **You stay flexible**: Easy to switch components as needs change

### Key Characteristics

- **Lightweight**: Minimal core dependencies (~10 MB installed)
  - Not burdened with unused features you'll never need
  - Starts up fast (hundreds of milliseconds)
  - Runs efficiently on modest hardware
  - Perfect for containerized deployments

- **WSGI-based**: Follows the Web Server Gateway Interface standard
  - Industry-standard Python web server interface
  - Can run on any WSGI-compatible server (Gunicorn, uWSGI, etc.)
  - Allows swapping servers without changing code
  - Part of the Python ecosystem standard

- **Unopinionated**: Doesn't force specific tools or libraries
  - You decide your project structure
  - Choose your own ORM, authentication, testing framework
  - No "Flask way" of doing things, just best practices
  - Great for learning because you understand every piece

- **Extensible**: Rich ecosystem of Flask extensions
  - Flask-SQLAlchemy for databases
  - Flask-Login for authentication
  - Flask-Cors for cross-origin requests
  - Flask-Caching for performance
  - Hundreds of others available on PyPI

### What Flask is NOT

- **Not a full-stack framework**: Unlike Django, Flask doesn't include:
  - Built-in ORM (Object-Relational Mapping)
  - Admin panel with CRUD interface
  - Automatic form validation
  - User authentication system
  - **Why?** Because not every project needs these. Flask lets you add only what you need.

- **Not for beginners who want magic**: Flask requires you to understand:
  - What HTTP is and how it works
  - How requests and responses flow
  - What you're actually building
  - **Why?** This understanding makes you a better developer.

- **Not the best choice for every project**:
  - Large enterprise app with admin panel? → Use Django
  - Real-time WebSocket app? → Use FastAPI or aiohttp
  - Machine learning API? → Use FastAPI
  - Traditional multi-page website? → Use Django or Flask + Jinja2
  - **Lesson**: The best tool depends on your specific needs.


---

## Understanding WSGI: The Bridge Between Web Servers and Python

WSGI (Web Server Gateway Interface) is the standard Python interface that allows web servers to communicate with Python web applications. Understanding WSGI is crucial for deploying Flask to production.

### The Problem WSGI Solves

**Before WSGI (chaos):**
- Django apps had one interface
- Zope apps had another interface
- TurboGears had yet another
- Developers had to learn new interfaces for each framework
- Web servers couldn't easily switch between Python apps

**After WSGI (standardized):**
- All Python web applications speak the same language
- Web servers can run any WSGI app
- Developers can swap frameworks without rewriting deployment code
- Plugins and middleware work across different frameworks

### The WSGI Flow in Production

```
User Request → Web Server → WSGI Server → Flask App → Response
                (nginx)     (Gunicorn)   (Your code)

Time: 1ms          50ms           10-100ms          1-10ms
```

Let's break down each layer:

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENT/USER BROWSER                  │
│           Makes HTTP request to example.com             │
└─────────────────────┬───────────────────────────────────┘
                      │ Port 80/443
                      ▼
┌─────────────────────────────────────────────────────────┐
│               WEB SERVER (nginx/Apache)                  │
│  • Handles SSL/TLS encryption                           │
│  • Serves static files (images, CSS, JS)                │
│  • Load balancing                                        │
│  • Caching                                               │
│  Routes dynamic requests to WSGI server                 │
└──────────────────────┬──────────────────────────────────┘
                       │ Unix socket or port
                       ▼
┌─────────────────────────────────────────────────────────┐
│          WSGI SERVER (Gunicorn/uWSGI)                   │
│  • Manages Python processes                             │
│  • Spawns worker threads/processes                      │
│  • Load distributes requests                            │
│  • Converts HTTP to WSGI format                         │
└──────────────────────┬──────────────────────────────────┘
                       │ WSGI interface
                       ▼
┌─────────────────────────────────────────────────────────┐
│              FLASK APPLICATION                          │
│  • Routes requests to handlers                          │
│  • Processes business logic                             │
│  • Queries databases                                     │
│  • Generates responses                                   │
└─────────────────────────────────────────────────────────┘
```

### Why This Matters

**Development vs. Production:**

```bash
# DEVELOPMENT (quick and easy)
$ python app.py
# Uses Flask's built-in server
# Single-threaded, slow, not scalable
# Perfect for testing locally

# PRODUCTION (robust and fast)
$ gunicorn -w 4 -b 0.0.0.0:8000 app:app
# Gunicorn runs 4 worker processes
# Can handle 4 requests concurrently
# Proper error handling and logging
# Much faster response times
```

### The WSGI Interface: What Actually Happens

At its core, WSGI is simple. Every WSGI application is a callable that takes two arguments:

```python
def application(environ, start_response):
    """
    Every WSGI app is a function with this signature.
    
    Args:
        environ (dict): Contains all request information
                       - environ['REQUEST_METHOD'] = 'GET'
                       - environ['PATH_INFO'] = '/api/users'
                       - environ['QUERY_STRING'] = 'page=1'
                       - environ['HTTP_AUTHORIZATION'] = 'Bearer token...'
                       - Plus ~30 other variables
        
        start_response (callable): Function to set response status and headers
                                  start_response('200 OK', [('Content-Type', 'text/plain')])
    
    Returns:
        iterable: Response body as bytes (often a list with one item)
    """
    
    # Example: respond to GET /hello with "Hello, World!"
    status = '200 OK'  # HTTP status line
    headers = [('Content-Type', 'text/plain')]  # Response headers
    
    start_response(status, headers)
    
    return [b'Hello, World!']  # Response body
```

**Real example showing what's in environ:**

```python
def debug_app(environ, start_response):
    # Extract common request information
    method = environ['REQUEST_METHOD']              # 'GET', 'POST', etc.
    path = environ['PATH_INFO']                     # '/api/users/123'
    query = environ.get('QUERY_STRING', '')         # 'page=1&limit=20'
    remote_addr = environ.get('REMOTE_ADDR')        # '192.168.1.100'
    user_agent = environ.get('HTTP_USER_AGENT', '')  # Browser/client info
    auth = environ.get('HTTP_AUTHORIZATION', '')    # Auth header value
    
    # Build response
    body = f"""
    Method: {method}
    Path: {path}
    Query: {query}
    Client IP: {remote_addr}
    User Agent: {user_agent}
    Authorization: {auth}
    """.encode()
    
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [body]
```

### Flask as a WSGI Application

When you create a Flask app, you're creating a WSGI application:

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Flask'

# Behind the scenes, Flask's 'app' object is callable
# It has a __call__ method that implements the WSGI interface
# So this works:
# gunicorn app:app  ← passes the WSGI app to Gunicorn
```

**What Flask does:**
1. Receives `environ` and `start_response` from Gunicorn
2. Parses the HTTP information from `environ`
3. Matches the path to a route handler
4. Runs your route function
5. Captures the return value
6. Calls `start_response` with status and headers
7. Returns the response body

### WSGI Middleware: Adding Functionality

WSGI middleware allows you to wrap your app and add functionality:

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello'

# Example: CORS middleware
class CORSMiddleware:
    def __init__(self, app):
        self.app = app  # Wrap the Flask app
    
    def __call__(self, environ, start_response):
        # Define custom start_response that adds CORS headers
        def cors_start_response(status, headers):
            headers.append(('Access-Control-Allow-Origin', '*'))
            headers.append(('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE'))
            return start_response(status, headers)
        
        # Call the wrapped Flask app
        return self.app(environ, cors_start_response)

# Wrap the app with middleware
app = CORSMiddleware(app)

# Now all responses include CORS headers!
```

In practice, Flask extensions handle this. Example with Flask-CORS:

```python
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Much simpler!

@app.route('/')
def hello():
    return 'Hello'
```

---

## When to Choose Flask: Decision Framework

Choosing the right tool for the job is crucial. Here's how to decide if Flask is right for your project.

### Use Flask When:

#### 1. **Building RESTful APIs and Microservices** ⭐ Flask's Strength

**Why Flask excels:**
- Minimal overhead makes it perfect for microservices
- Easy to create endpoints in any structure
- Lightweight for containerization (small Docker images)
- Low memory footprint even under load

**Example: JSON API Service**
```python
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    # Just return JSON, Flask handles the rest
    return jsonify({
        'id': user_id,
        'name': 'Alice',
        'email': 'alice@example.com'
    })

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    # Validate, save to database...
    return jsonify({'id': 1}), 201
```

**Deployment in Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

The slim Python image + Flask = ~200MB Docker image (vs. ~500MB+ with Django)

#### 2. **You Need Flexibility and Control** 🎛️ Flask's Philosophy

**Scenarios:**
- Custom authentication (not just username/password)
- Specific database (MongoDB, DynamoDB, custom store)
- Non-standard project structure
- Integration with legacy systems
- Hybrid app (REST API + some HTML pages + WebSockets)

**Example: Custom Multi-Auth Service**
```python
from flask import Flask, request, jsonify
from functools import wraps
import hashlib
import hmac

app = Flask(__name__)

def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check multiple auth methods
        auth_header = request.headers.get('Authorization')
        api_key = request.headers.get('X-API-Key')
        
        if auth_header and auth_header.startswith('Bearer '):
            # OAuth token
            token = auth_header[7:]
            if validate_oauth_token(token):
                return f(*args, **kwargs)
        
        elif api_key:
            # API key auth
            if validate_api_key(api_key):
                return f(*args, **kwargs)
        
        elif request.json and 'hmac' in request.json:
            # HMAC signature auth (Stripe-style)
            if validate_hmac_signature(request.json):
                return f(*args, **kwargs)
        
        return {'error': 'Unauthorized'}, 401
    
    return decorated

@app.route('/protected', methods=['POST'])
@auth_required
def protected_endpoint():
    return {'message': 'Access granted'}
```

With Django, you'd have to fight against its opinionated auth system. With Flask, it's your choice.

#### 3. **Learning Backend Fundamentals** 📚 Educational Value

**Why Flask is better for learning:**
- Less "magic" than Django - you see what's happening
- Understand HTTP requests and responses directly
- Learn about middleware, decorators, design patterns
- No hidden ORM complexity
- Easier to debug (fewer abstraction layers)

**Compare request handling:**

Django (abstracts too much):
```python
# Django makes assumptions about your data flow
def user_detail(request, user_id):
    user = User.objects.get(id=user_id)  # Magic ORM
    return render(request, 'user.html', {'user': user})  # Magic templating
```

Flask (you understand each step):
```python
@app.route('/users/<int:user_id>')
def user_detail(user_id):
    # You explicitly handle everything
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {'error': 'Not found'}, 404
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email
    })
```

#### 4. **Rapid Prototyping and MVPs** 🚀 Time to Market

**Why Flask is fast:**
- Minimal boilerplate
- No database migrations, admin setup needed
- Use in-memory data structures for prototype
- Easy to add real database later

**Prototype → Production Path:**
```python
# Day 1: Prototype (in-memory storage)
from flask import Flask, jsonify

app = Flask(__name__)
users = [{'id': 1, 'name': 'Alice'}]  # Just a list!

@app.route('/users')
def get_users():
    return jsonify(users)

# Day 2-3: Add real database
# Just swap the data source, keep endpoints the same!

# Day 4+: Scale with production database
# Same Flask app works with PostgreSQL, MongoDB, etc.
```

### Don't Use Flask When:

#### 1. **You Need Built-in Admin Panel and ORM** 📊 Use Django

**Scenario:**
- Content management system
- Business app with lots of database tables
- Non-technical admin panel needed
- Quick CRUD interfaces

**Example (Django is better):**
```python
# Django gives you admin panel for free
# With just:
from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'created_at']
    list_filter = ['created_at', 'status']
    search_fields = ['title', 'content']
    
# Visit /admin and get fully functional interface
# Flask would require you to build this
```

#### 2. **Real-time WebSocket Features Required** 🔄 Use FastAPI or aiohttp

**Scenario:**
- Chat application
- Live notifications
- Collaborative editing
- Real-time dashboards

**Why:**
- Flask is synchronous (handles one request at a time)
- FastAPI is async-native (handles thousands of concurrent connections)
- WebSockets need persistent connections (Flask not designed for this)

Flask with WebSockets:
```python
# Possible but clunky
from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

@socketio.on('message')
def handle_message(data):
    emit('response', {'data': data})
```

FastAPI with WebSockets:
```python
# Native, clean, performant
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Echo: {data}")
```

#### 3. **High-Performance Requirements Under Heavy Load** ⚡ Use FastAPI

**Scenario:**
- Millions of requests per day
- Complex CPU-intensive operations
- Real-time processing

**Performance comparison (simple endpoint):**

```bash
# Flask with Gunicorn (4 workers)
$ ab -n 10000 -c 100 http://localhost:5000/
Requests per second: 2000 req/s

# FastAPI with Uvicorn (4 workers)
$ ab -n 10000 -c 100 http://localhost:8000/
Requests per second: 5000+ req/s
```

FastAPI has built-in async/await support, Flask doesn't.

#### 4. **Team Prefers Opinionated Structure** 🏛️ Use Django

**Scenario:**
- Large team
- Need consistency across projects
- Junior developers (structure provides guardrails)
- Enterprise environment

**Structure:**
```
# Django enforces this structure
my_project/
├── manage.py
├── my_project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── app_name/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── tests.py
│   └── admin.py
```

With Flask, you can organize however you want (good and bad)

## Real-World Use Cases

### Microservices Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Auth      │     │   Users     │     │  Payments   │
│   Service   │────▶│   Service   │────▶│   Service   │
│   (Flask)   │     │   (Flask)   │     │   (Flask)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

Each service is a small Flask app, independently deployable.

### API Gateway Pattern

```python
# api_gateway.py
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

SERVICES = {
    'users': 'http://users-service:5000',
    'orders': 'http://orders-service:5000'
}

@app.route('/api/<service>/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy(service, endpoint):
    """Route requests to appropriate microservice"""
    if service not in SERVICES:
        return jsonify({'error': 'Service not found'}), 404
    
    url = f"{SERVICES[service]}/{endpoint}"
    response = requests.request(
        method=request.method,
        url=url,
        json=request.get_json(),
        headers=request.headers
    )
    
    return response.json(), response.status_code
```

### Internal Tools and Dashboards

```python
# monitoring_dashboard.py
from flask import Flask, render_template
import psutil

app = Flask(__name__)

@app.route('/health')
def health_check():
    """System health metrics"""
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent
    }

@app.route('/dashboard')
def dashboard():
    """Simple monitoring dashboard"""
    return render_template('dashboard.html')
```

## Flask vs Alternatives

| Feature | Flask | Django | FastAPI |
|---------|-------|--------|---------|
| Learning Curve | Moderate | Steep | Moderate |
| Performance | Good | Good | Excellent |
| Async Support | Limited | Yes (3.1+) | Native |
| ORM Included | No | Yes | No |
| Admin Panel | No | Yes | No |
| API Development | Excellent | Good | Excellent |
| Flexibility | High | Low | High |
| Production Ready | Yes | Yes | Yes |

## Common Misconceptions

### "Flask is only for small apps"

**False**. Flask powers production applications at scale. Examples:
- Pinterest (initially)
- LinkedIn (some services)
- Netflix (internal tools)

The key is proper architecture, not framework size.

### "Flask is easier than Django"

**Partially true**. Flask is easier to start, but requires more decisions:
- Which ORM?
- How to structure?
- Which extensions?

Django makes these decisions for you.

### "Flask is not production-ready"

**False**. Flask is production-ready when:
- Deployed with proper WSGI server (Gunicorn)
- Behind a reverse proxy (nginx)
- With proper logging and monitoring
- Using production-grade database

## Best Practices from the Start

### 1. Never Use Debug Mode in Production

```python
# BAD
if __name__ == '__main__':
    app.run(debug=True)  # NEVER in production

# GOOD
if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'])
```

### 2. Use Environment Variables

```python
# BAD
app.config['SECRET_KEY'] = 'hardcoded-secret'

# GOOD
import os
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
```

### 3. Separate Configuration from Code

```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

### 4. Use Application Factory Pattern

We'll cover this in detail in Module 2, but always structure for scalability:

```python
# app/__init__.py
def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config_name)
    return app
```

## Summary

Flask is a powerful, flexible micro-framework ideal for:
- RESTful APIs and microservices
- Custom backend architectures
- Learning web development fundamentals
- Rapid prototyping

It requires more architectural decisions than Django but offers greater flexibility. Understanding WSGI is crucial for production deployment, where Flask runs behind Gunicorn and nginx.

**Key Takeaway**: Flask gives you control and flexibility. With that comes responsibility to make good architectural decisions from the start.

---

## Practice Exercises

### Multiple Choice Questions

1. What does WSGI stand for and what is its primary purpose?
   a) Web Service Gateway Interface - for API communication
   b) Web Server Gateway Interface - for Python web server/app communication
   c) Web Socket Gateway Interface - for real-time communication
   d) Web Security Gateway Interface - for authentication

2. In a production Flask deployment, which component should handle SSL termination?
   a) Flask development server
   b) Gunicorn WSGI server
   c) nginx reverse proxy
   d) Python's built-in SSL module

3. When is Flask NOT the best choice?
   a) Building a RESTful API
   b) Creating a microservice
   c) Needing built-in admin panel and ORM
   d) Rapid prototyping

4. What makes Flask a "micro" framework?
   a) It can only handle small applications
   b) It has minimal core with extensible architecture
   c) It uses less memory than other frameworks
   d) It's written in fewer lines of code

5. Which deployment setup is correct for production?
   a) Flask development server directly exposed to internet
   b) nginx → Flask development server
   c) nginx → Gunicorn → Flask app
   d) Gunicorn → nginx → Flask app

### Practical Tasks

**Task 1: WSGI Deep Dive**

Create a pure WSGI application (without Flask) that:
- Responds to GET requests at `/status` with JSON: `{"status": "ok"}`
- Returns 404 for all other paths
- Sets appropriate Content-Type headers

Test it with a WSGI server like Gunicorn.

**Task 2: Framework Comparison**

Create the same simple API endpoint in Flask, Django, and FastAPI:
- Endpoint: `POST /calculate`
- Accepts JSON: `{"numbers": [1, 2, 3, 4, 5]}`
- Returns JSON: `{"sum": 15, "average": 3.0}`

Compare:
- Lines of code required
- Setup complexity
- Performance (use `ab` or `wrk` for benchmarking)

### Debugging Scenario

You've deployed a Flask application to production. Users report intermittent 500 errors, but your local development environment works perfectly.

**Symptoms:**
- Error occurs randomly, about 10% of requests
- Error message: "RuntimeError: Working outside of application context"
- Happens only under load (multiple concurrent requests)

**Your code:**
```python
from flask import Flask
import redis

app = Flask(__name__)
redis_client = redis.Redis(host='localhost', port=6379)

@app.route('/counter')
def counter():
    count = redis_client.incr('visit_count')
    return {'count': count}

if __name__ == '__main__':
    app.run()
```

**Questions:**
1. What is the root cause of this error?
2. Why does it only happen in production, not development?
3. How would you fix it?
4. What production deployment practice would have prevented this?

---

**Next Module**: [Flask Architecture](02-flask-architecture.md)
