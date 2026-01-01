# Module 1: Flask Fundamentals

## What is Flask?

Flask is a **micro web framework** written in Python. The term "micro" doesn't mean Flask lacks functionality—it means Flask keeps the core simple and extensible.

### Key Characteristics

- **Lightweight**: Minimal dependencies out of the box
- **WSGI-based**: Follows the Web Server Gateway Interface standard
- **Unopinionated**: Doesn't force specific tools or libraries
- **Extensible**: Rich ecosystem of extensions

### What Flask is NOT

- **Not a full-stack framework**: Unlike Django, Flask doesn't include an ORM, admin panel, or form validation by default
- **Not for beginners who want magic**: Flask requires you to understand what you're doing
- **Not the best choice for every project**: Sometimes Django, FastAPI, or other frameworks are better suited

## Understanding WSGI

WSGI (Web Server Gateway Interface) is the Python standard for web servers to communicate with web applications.

### The WSGI Flow

```
Client Request → Web Server (nginx/Apache) → WSGI Server (Gunicorn/uWSGI) → Flask App → Response
```

### Why This Matters

In production, you NEVER run Flask's development server. Instead:

1. **Web Server** (nginx): Handles static files, SSL, load balancing
2. **WSGI Server** (Gunicorn): Manages Python processes and worker threads
3. **Flask App**: Your application code

### Simple WSGI Example

```python
# wsgi_example.py
def application(environ, start_response):
    """
    environ: Dictionary containing request information
    start_response: Callable to set response status and headers
    """
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    
    return [b'Hello from WSGI']
```

This is what happens under the hood. Flask abstracts this complexity.

### Flask as WSGI Application

```python
# app.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Flask'

# app is a WSGI application
# You can pass it to any WSGI server
```

## When to Choose Flask

### Use Flask When:

1. **Building APIs**: RESTful services, microservices
   - Lightweight, fast startup
   - Easy to structure as you need
   - Great for containerized deployments

2. **You need flexibility**: Custom architecture, specific libraries
   - Choose your own ORM (SQLAlchemy, Peewee, etc.)
   - Pick your authentication method
   - Structure your project your way

3. **Learning backend fundamentals**: Understanding how web frameworks work
   - Less abstraction = better understanding
   - You see what's happening
   - Easier to debug

4. **Prototyping**: Quick MVPs, proof of concepts
   - Fast to set up
   - Minimal boilerplate
   - Easy to iterate

### Don't Use Flask When:

1. **You need batteries included**: Admin panels, built-in auth, form handling
   - Use Django instead
   - Less setup time for standard features

2. **High-performance async required**: WebSockets, real-time features
   - Use FastAPI or aiohttp
   - Flask is synchronous by default

3. **Team prefers opinionated structure**: Standardized project layout
   - Django enforces structure
   - Flask requires discipline

4. **Complex frontend rendering**: Server-side template-heavy apps
   - Django's template system is more robust
   - Modern approach: Flask API + React/Vue frontend

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
