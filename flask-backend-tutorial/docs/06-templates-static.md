# Module 6: Templates and Static Files

## Introduction: Templates in Modern Backend

Templates are HTML files with embedded Python logic that Flask renders on the server before sending to clients. Jinja2 is Flask's default templating engine.

### When Templates Are Useful (and When They're Not)

**✅ Use templates for:**
- HTML emails (welcome emails, notifications, password resets)
- Admin dashboards and internal tools
- API documentation websites
- Server-side rendered pages (less common in modern APIs)
- Error pages and status pages

**❌ Don't use templates for:**
- REST APIs (return JSON instead)
- Single Page Applications (use React/Vue, not templates)
- Mobile app backends (return JSON, not HTML)
- Production web apps (usually use frontend frameworks)

---

## Rendering Templates with Jinja2

Jinja2 is Flask's default template engine. It's a powerful system for generating HTML dynamically.

### Basic Template Rendering

**Python code (view function):**

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """
    Render user profile page using template.
    
    The render_template function:
    1. Finds the template file in templates/ folder
    2. Passes data as variables to the template
    3. Executes Python code in the template
    4. Returns rendered HTML string
    """
    
    # Get user data from database (or create for example)
    user = {
        'id': user_id,
        'name': 'Alice Johnson',
        'email': 'alice@example.com',
        'created_at': '2024-01-01',
        'premium': True,
        'posts_count': 15
    }
    
    # render_template(filename, **variables)
    # Variables become available in the template
    return render_template('user/profile.html', user=user)
```

**Template file (templates/user/profile.html):**

```html
<!DOCTYPE html>
<html>
<head>
    <title>User Profile</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        .profile { background: #f5f5f5; padding: 20px; border-radius: 8px; }
        .badge { background: #4CAF50; color: white; padding: 5px 10px; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="profile">
        <!-- Simple variable interpolation -->
        <h1>{{ user.name }}</h1>
        <p>Email: {{ user.email }}</p>
        <p>Member since: {{ user.created_at }}</p>
        
        <!-- Conditional rendering (if statement) -->
        {% if user.premium %}
            <span class="badge">Premium Member</span>
        {% else %}
            <p>Upgrade to premium for more features</p>
        {% endif %}
        
        <!-- Variable logic -->
        <p>Posts: {{ user.posts_count }}</p>
    </div>
</body>
</html>
```

**Testing:**

```bash
curl http://localhost:5000/user/1
# Returns HTML page with user data filled in
```

### Template Inheritance: Creating Base Templates

Instead of repeating HTML in every template, use inheritance:

**Base template (templates/base.html):**

```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}My Site{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <!-- Navigation (same on every page) -->
    <nav>
        <a href="{{ url_for('home') }}">Home</a>
        <a href="{{ url_for('about') }}">About</a>
        <a href="{{ url_for('contact') }}">Contact</a>
    </nav>
    
    <!-- Main content (different for each page) -->
    <main>
        {% block content %}
        <!-- Child templates override this block -->
        {% endblock %}
    </main>
    
    <!-- Footer (same on every page) -->
    <footer>
        <p>&copy; 2024 My Company. All rights reserved.</p>
    </footer>
</body>
</html>
```

**Child template (templates/home.html):**

```html
{% extends "base.html" %}

{% block title %}Home - My Site{% endblock %}

{% block content %}
    <h1>Welcome Home</h1>
    <p>This is the home page content.</p>
{% endblock %}
```

**Benefits:**
- DRY (Don't Repeat Yourself) - write HTML once
- Consistent navigation and layout across site
- Easy to change design (modify base.html)
- Easy to add new pages (just create child template)

### Jinja2 Control Structures

**If/Else statements:**

```html
{% if user.role == 'admin' %}
    <button>Delete User</button>
{% elif user.role == 'moderator' %}
    <button>Edit User</button>
{% else %}
    <p>View only</p>
{% endif %}
```

**For loops:**

```html
<h2>Recent Posts</h2>
<ul>
    {% for post in posts %}
        <li>
            <a href="{{ url_for('view_post', post_id=post.id) }}">
                {{ post.title }}
            </a>
            <small>by {{ post.author }} on {{ post.date }}</small>
        </li>
    {% else %}
        <li>No posts yet.</li>
    {% endfor %}
</ul>
```

**Filters (transform data):**

```html
<!-- String filters -->
<p>{{ 'hello world' | upper }}</p>          <!-- HELLO WORLD -->
<p>{{ 'HELLO' | lower }}</p>                <!-- hello -->
<p>{{ 'hello world' | capitalize }}</p>     <!-- Hello world -->
<p>{{ 'hello world' | title }}</p>          <!-- Hello World -->

<!-- Length -->
<p>{{ items | length }} items</p>           <!-- 3 items -->

<!-- Default values -->
<p>{{ user.bio | default('No bio provided') }}</p>

<!-- List filters -->
<p>{{ [3, 1, 2] | sort }}</p>               <!-- [1, 2, 3] -->
<p>{{ [1, 2, 3, 2, 1] | unique }}</p>       <!-- [1, 2, 3] -->

<!-- Date formatting -->
<p>{{ user.created_at | strftime('%Y-%m-%d') }}</p>
```

### When to Use Templates: Practical Examples

#### Example 1: HTML Email

```python
from flask import render_template
from flask_mail import Mail, Message

mail = Mail(app)

def send_password_reset_email(user, reset_token):
    """Send password reset email using template"""
    
    # Render both HTML and plain text versions
    html = render_template(
        'emails/password_reset.html',
        user=user,
        reset_token=reset_token,
        reset_url=f'https://myapp.com/reset/{reset_token}'
    )
    
    text = render_template(
        'emails/password_reset.txt',
        user=user,
        reset_url=f'https://myapp.com/reset/{reset_token}'
    )
    
    # Create and send email
    msg = Message(
        subject='Password Reset Request',
        recipients=[user.email],
        html=html,
        body=text
    )
    
    mail.send(msg)
```

**Email template (templates/emails/password_reset.html):**

```html
<html>
<body>
    <h2>Reset Your Password</h2>
    <p>Hi {{ user.name }},</p>
    <p>We received a request to reset your password. Click the link below to create a new password:</p>
    <p>
        <a href="{{ reset_url }}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
            Reset Password
        </a>
    </p>
    <p>This link expires in 1 hour.</p>
    <p>If you didn't request a password reset, ignore this email.</p>
</body>
</html>
```

#### Example 2: Admin Dashboard

```python
from flask import render_template
from functools import wraps

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or user.role != 'admin':
            return 'Unauthorized', 401
        return f(*args, **kwargs)
    return decorated

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Render admin dashboard with system stats"""
    
    stats = {
        'total_users': 1250,
        'active_today': 342,
        'new_signups': 23,
        'errors': 5,
        'uptime': '99.8%'
    }
    
    recent_users = [
        {'id': 1, 'name': 'Alice', 'email': 'alice@example.com', 'joined': '2024-01-10'},
        {'id': 2, 'name': 'Bob', 'email': 'bob@example.com', 'joined': '2024-01-11'},
    ]
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_users=recent_users
    )
```

---

## Static Files: CSS, JavaScript, Images

Static files are files that don't change (CSS, JavaScript, images) served directly without processing.

### Folder Structure

```
my-flask-app/
├── app.py
├── templates/
│   ├── base.html
│   └── user/
│       └── profile.html
└── static/               # ← All static files go here
    ├── css/
    │   ├── style.css
    │   └── admin.css
    ├── js/
    │   ├── app.js
    │   └── utils.js
    └── images/
        ├── logo.png
        └── favicon.ico
```

### Using Static Files in Templates

**In Jinja2 templates, use `url_for('static', ...)`:**

```html
<!DOCTYPE html>
<html>
<head>
    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <link rel="icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
</head>
<body>
    <!-- Images -->
    <img src="{{ url_for('static', filename='images/logo.png') }}" alt="Logo">
    
    <!-- JavaScript -->
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
```

**Why use `url_for()`?**
- Works with different deployment setups
- Handles CDNs automatically
- Cache busting (add version to URL)
- Auto-generates correct paths

### Serving Static Files in Flask

Flask automatically serves files from the `static/` folder:

```
GET /static/css/style.css  → Returns static/css/style.css
GET /static/js/app.js      → Returns static/js/app.js
GET /static/images/logo.png → Returns static/images/logo.png
```

**Behind the scenes:**

```python
# Flask automatically registers this route
@app.route('/static/<path:filename>')
def static_files(filename):
    """Flask handles this for you"""
    return send_from_directory('static', filename)
```

### Organizing Static Files

**Good organization:**

```
static/
├── css/
│   ├── style.css          # Main styles
│   ├── admin.css          # Admin dashboard styles
│   └── responsive.css     # Mobile/responsive styles
├── js/
│   ├── app.js             # Main app logic
│   ├── utils.js           # Helper functions
│   └── vendor/            # Third-party libraries
│       ├── jquery.js
│       └── bootstrap.js
├── images/
│   ├── logo.png
│   ├── icons/
│   │   ├── user.png
│   │   └── settings.png
│   └── uploads/           # User-uploaded files
└── docs/
    └── API.html
```

### Production Considerations for Static Files

**In production, don't use Flask to serve static files:**

```bash
# Development (fine for testing)
python app.py
# Flask serves static files itself

# Production (proper way)
gunicorn -w 4 app:app
# Use nginx to serve static files separately
# Flask handles only dynamic API requests
```

**nginx configuration for production:**

```nginx
server {
    listen 80;
    server_name api.example.com;
    
    # Serve static files directly (fast!)
    location /static {
        alias /var/www/myapp/static;
        expires 30d;  # Browser caching
    }
    
    # Forward API requests to Flask/Gunicorn
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

**Why this matters:**
- nginx serves static files 100x faster than Flask
- Frees Flask workers for actual API logic
- Enables CDN integration
- Better caching strategies
@app.route('/health')
def health_check():
    """Visual health check page for ops team"""
    status = {
        'database': check_database(),
        'redis': check_redis(),
        'external_api': check_external_api()
    }
    return render_template('health.html', status=status)
```

### When NOT to Use Templates

**Don't use templates for:**
- Public-facing web applications (use React/Vue/Angular + Flask API)
- Mobile app backends (return JSON, not HTML)
- Microservices (APIs only)
- Modern SPAs (single page applications)

**Modern architecture:**
```
Frontend (React/Vue) ←→ Flask API (JSON)
     ↓                        ↓
  Browser                 Database
```

## Jinja2 Essentials

Jinja2 is Flask's template engine. Learn the basics for internal tools and emails.

### Template Basics

```html
<!-- templates/user.html -->
<!DOCTYPE html>
<html>
<head>
    <title>User Profile</title>
</head>
<body>
    <h1>{{ user.name }}</h1>
    <p>Email: {{ user.email }}</p>
    <p>Joined: {{ user.created_at }}</p>
</body>
</html>
```

```python
from flask import render_template

@app.route('/users/<int:user_id>')
def user_profile(user_id):
    user = {'id': user_id, 'name': 'John', 'email': 'john@example.com'}
    return render_template('user.html', user=user)
```

### Variables and Expressions

```html
<!-- Variable output -->
<h1>{{ title }}</h1>
<p>{{ user.email }}</p>

<!-- Expressions -->
<p>Total: {{ price * quantity }}</p>
<p>Uppercase: {{ name.upper() }}</p>

<!-- Filters -->
<p>{{ text|capitalize }}</p>
<p>{{ date|datetimeformat }}</p>
<p>{{ items|length }} items</p>

<!-- Default values -->
<p>{{ user.phone|default('N/A') }}</p>
```

### Control Structures

```html
<!-- If statements -->
{% if user.is_admin %}
    <a href="/admin">Admin Panel</a>
{% elif user.is_moderator %}
    <a href="/moderate">Moderate</a>
{% else %}
    <p>Regular user</p>
{% endif %}

<!-- For loops -->
<ul>
{% for item in items %}
    <li>{{ item.name }} - ${{ item.price }}</li>
{% endfor %}
</ul>

<!-- Loop with empty check -->
<ul>
{% for user in users %}
    <li>{{ user.name }}</li>
{% else %}
    <li>No users found</li>
{% endfor %}
</ul>

<!-- Loop variables -->
{% for item in items %}
    <p>{{ loop.index }}. {{ item.name }}</p>
    {% if loop.first %}<p>First item!</p>{% endif %}
    {% if loop.last %}<p>Last item!</p>{% endif %}
{% endfor %}
```

### Template Inheritance

**Base template:**
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Default Title{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <nav>
        <a href="/">Home</a>
        <a href="/about">About</a>
    </nav>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>&copy; 2024 My App</p>
    </footer>
</body>
</html>
```

**Child template:**
```html
<!-- templates/dashboard.html -->
{% extends "base.html" %}

{% block title %}Dashboard{% endblock %}

{% block content %}
    <h1>Dashboard</h1>
    <p>Welcome, {{ user.name }}!</p>
{% endblock %}
```

### Macros (Reusable Components)

```html
<!-- templates/macros.html -->
{% macro render_field(field, label) %}
    <div class="form-group">
        <label>{{ label }}</label>
        <input type="text" name="{{ field }}" value="{{ value }}">
    </div>
{% endmacro %}

{% macro render_alert(message, type='info') %}
    <div class="alert alert-{{ type }}">
        {{ message }}
    </div>
{% endmacro %}
```

**Using macros:**
```html
<!-- templates/form.html -->
{% from 'macros.html' import render_field, render_alert %}

{{ render_alert('Form submitted successfully!', 'success') }}

<form>
    {{ render_field('email', 'Email Address') }}
    {{ render_field('name', 'Full Name') }}
</form>
```

### Email Template Example

```html
<!-- templates/emails/welcome.html -->
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { background: #007bff; color: white; padding: 20px; }
        .content { padding: 20px; }
        .button { background: #28a745; color: white; padding: 10px 20px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Welcome to {{ app_name }}!</h1>
    </div>
    <div class="content">
        <p>Hi {{ user.name }},</p>
        <p>Thank you for joining {{ app_name }}. We're excited to have you!</p>
        <p>
            <a href="{{ activation_url }}" class="button">Activate Your Account</a>
        </p>
        <p>If you didn't create this account, please ignore this email.</p>
    </div>
</body>
</html>
```

```python
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    user = create_user(data)
    
    # Send welcome email
    activation_url = url_for('activate', token=user.activation_token, _external=True)
    html = render_template(
        'emails/welcome.html',
        user=user,
        app_name='My App',
        activation_url=activation_url
    )
    
    send_email(user.email, 'Welcome!', html)
    return jsonify({'id': user.id}), 201
```

## Static File Management

Static files (CSS, JavaScript, images) are served directly without processing.

### Static File Structure

```
app/
├── static/
│   ├── css/
│   │   ├── style.css
│   │   └── admin.css
│   ├── js/
│   │   ├── main.js
│   │   └── dashboard.js
│   ├── images/
│   │   ├── logo.png
│   │   └── favicon.ico
│   └── uploads/
│       └── user_avatars/
```

### Serving Static Files

```html
<!-- In templates -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
<img src="{{ url_for('static', filename='images/logo.png') }}" alt="Logo">
```

### Static File Configuration

```python
# app/__init__.py
app = Flask(
    __name__,
    static_folder='static',
    static_url_path='/static'
)

# Custom static folder
app = Flask(
    __name__,
    static_folder='assets',
    static_url_path='/assets'
)
```

### Serving User Uploads

```python
from flask import send_from_directory
import os

UPLOAD_FOLDER = '/var/www/uploads'

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/uploads/<user_id>/<filename>')
def user_file(user_id, filename):
    """Serve user-specific files with access control"""
    # Check if user has access
    if not has_access(current_user, user_id):
        return jsonify({'error': 'Forbidden'}), 403
    
    filepath = os.path.join(UPLOAD_FOLDER, user_id, filename)
    return send_from_directory(os.path.dirname(filepath), os.path.basename(filepath))
```

### Production Static File Serving

**Development:**
```python
# Flask serves static files
app.run(debug=True)
```

**Production:**
```nginx
# nginx.conf - nginx serves static files directly
location /static {
    alias /var/www/app/static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location / {
    proxy_pass http://127.0.0.1:8000;  # Gunicorn
}
```

**Why:** nginx is much faster at serving static files than Python.

### Cache Busting

```python
# app/__init__.py
import hashlib
import os

def get_file_hash(filepath):
    """Generate hash for cache busting"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()[:8]

@app.context_processor
def utility_processor():
    """Add utility functions to templates"""
    def static_url(filename):
        filepath = os.path.join(app.static_folder, filename)
        if os.path.exists(filepath):
            file_hash = get_file_hash(filepath)
            return url_for('static', filename=filename, v=file_hash)
        return url_for('static', filename=filename)
    
    return dict(static_url=static_url)
```

```html
<!-- In template -->
<link rel="stylesheet" href="{{ static_url('css/style.css') }}">
<!-- Renders: /static/css/style.css?v=a1b2c3d4 -->
```

## Security Considerations

### Auto-Escaping

Jinja2 auto-escapes variables to prevent XSS:

```html
<!-- Safe - auto-escaped -->
<p>{{ user_input }}</p>
<!-- If user_input = "<script>alert('XSS')</script>" -->
<!-- Renders: &lt;script&gt;alert('XSS')&lt;/script&gt; -->

<!-- Unsafe - manual HTML -->
<p>{{ user_input|safe }}</p>
<!-- Renders: <script>alert('XSS')</script> - DANGEROUS! -->
```

**Never use `|safe` with user input!**

### Serving Files Securely

```python
from werkzeug.utils import secure_filename
import os

@app.route('/download/<filename>')
def download_file(filename):
    # BAD - Path traversal vulnerability
    # filename could be "../../etc/passwd"
    return send_from_directory('/uploads', filename)

@app.route('/download/<filename>')
def download_file(filename):
    # GOOD - Secure filename
    safe_name = secure_filename(filename)
    return send_from_directory('/uploads', safe_name)
```

## Summary

Templates in Flask are useful for:
- Internal admin dashboards
- Email templates
- API documentation pages
- Health check interfaces

For public-facing applications, use Flask as an API backend with a separate frontend framework.

Static files should be served by nginx in production for performance.

**Key principles:**
- Use templates sparingly in modern backends
- Never use `|safe` with user input
- Serve static files with nginx in production
- Use `secure_filename()` for file uploads
- Implement cache busting for static assets

---

## Practice Exercises

### Multiple Choice Questions

1. When should you use Flask templates for a production application?
   a) For all web pages
   b) For internal tools and email templates
   c) Never, always use React
   d) Only for mobile apps

2. What does Jinja2's auto-escaping prevent?
   a) SQL injection
   b) XSS (Cross-Site Scripting)
   c) CSRF attacks
   d) DDoS attacks

3. In production, who should serve static files?
   a) Flask development server
   b) Gunicorn
   c) nginx
   d) Python's http.server

4. What does `secure_filename()` do?
   a) Encrypts the filename
   b) Prevents path traversal attacks
   c) Validates file extension
   d) Generates unique filename

5. What's the purpose of cache busting?
   a) Clear browser cache
   b) Force browsers to load new versions of static files
   c) Improve server performance
   d) Reduce bandwidth usage

### Practical Tasks

**Task 1: Email Template System**

Create an email template system with:

1. Base email template with consistent styling
2. Welcome email template
3. Password reset email template
4. Weekly digest email template
5. Python functions to render and send each email type

Include proper HTML/CSS for email clients.

**Task 2: Admin Dashboard**

Build a simple admin dashboard that displays:

1. System health metrics (CPU, memory, disk)
2. Recent user registrations (table)
3. Error logs (last 10 errors)
4. Quick actions (buttons to clear cache, restart services)

Use template inheritance and serve static CSS/JS files.

### Debugging Scenario

You've built an admin dashboard with file upload functionality:

```python
@app.route('/admin/upload', methods=['POST'])
def upload_report():
    file = request.files['file']
    filename = file.filename
    file.save(f'/var/www/uploads/{filename}')
    return render_template('admin/success.html', filename=filename)
```

```html
<!-- templates/admin/success.html -->
<h1>File Uploaded</h1>
<p>File saved: {{ filename }}</p>
<p>User comment: {{ comment|safe }}</p>
```

**Problems:**

1. Security team reports path traversal vulnerability
2. XSS vulnerability in comment display
3. Files are being overwritten (same filename)
4. No file type validation

**Questions:**
1. What's the path traversal vulnerability?
2. What's the XSS vulnerability?
3. How would you prevent file overwrites?
4. How would you add file type validation?
5. Provide corrected, secure code.

---

**Next Module**: [Flask Blueprints](07-flask-blueprints.md)
