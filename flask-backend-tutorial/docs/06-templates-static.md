# Module 6: Templates and Static Files

## When to Use Templates in Backend Services

Templates in Flask are primarily for server-side rendering (SSR). In modern backend development, their use is limited.

### Appropriate Use Cases

**1. Admin Dashboards and Internal Tools**
```python
@app.route('/admin/dashboard')
def admin_dashboard():
    """Internal monitoring dashboard"""
    stats = {
        'users': 1250,
        'active_sessions': 42,
        'errors_today': 3
    }
    return render_template('admin/dashboard.html', stats=stats)
```

**2. Email Templates**
```python
from flask import render_template
from flask_mail import Message

def send_welcome_email(user):
    """Send HTML email using template"""
    html_body = render_template('emails/welcome.html', user=user)
    text_body = render_template('emails/welcome.txt', user=user)
    
    msg = Message(
        subject='Welcome to Our Service',
        recipients=[user.email],
        html=html_body,
        body=text_body
    )
    # Send email...
```

**3. API Documentation Pages**
```python
@app.route('/docs')
def api_docs():
    """Serve API documentation"""
    return render_template('docs/api.html')
```

**4. Health Check Pages**
```python
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
