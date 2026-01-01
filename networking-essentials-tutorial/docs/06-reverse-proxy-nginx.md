# Module 6: Reverse Proxy (Nginx)

## What a Reverse Proxy Actually Does

A reverse proxy sits between your users and your backend services.

```
Client → Nginx (Reverse Proxy) → Backend Service (Flask/FastAPI)
```

The client thinks it's talking to Nginx. Nginx talks to the backend and relays responses.

## Why Reverse Proxy?

### 1. Hide Your Backend

Clients never connect directly to Flask. They connect to Nginx.

```
Benefit: Backend IP is never exposed
Attack surface: Only Nginx is public-facing
Backend: Can be behind firewall, internal network only
```

### 2. Security Layer

Nginx can:

- Reject malicious requests before they reach your app
- Block DDoS attacks
- Rate limit per IP
- Hide server details (Apache, Flask version, etc.)

### 3. TLS Termination

Nginx handles HTTPS encryption. Backend communicates plain HTTP (internal).

```
Client (HTTPS) ──→ Nginx (decrypts) ──→ Flask (HTTP)

Why?
- Nginx is fast at TLS
- Flask shouldn't do TLS
- One place to manage certificates
- Easy to update certificates without restarting Flask
```

### 4. Load Balancing

Distribute traffic across multiple backends (covered in Module 5).

### 5. Caching

Nginx can cache responses, reducing backend load.

```
Client request → Nginx → Check cache → If hit, return cached response
                       → If miss, request backend, cache response, return
```

### 6. Compression

Nginx compresses responses, reducing bandwidth.

```
Backend returns 1MB JSON
Nginx compresses to 100KB
Client receives 100KB (10% of original)
```

## Basic Reverse Proxy Configuration

### Simplest Setup

```nginx
# /etc/nginx/nginx.conf

upstream backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name example.com;
    
    location / {
        proxy_pass http://backend;
    }
}
```

### What This Does

```
Client: GET http://example.com/api/users

Nginx:
1. Receives GET /api/users
2. Checks upstream backend
3. Sends GET /api/users to 127.0.0.1:5000
4. Receives response from Flask
5. Sends response back to client
```

Terminal verification:

```bash
# Start backend
python app.py  # Runs on localhost:5000

# Configure Nginx to proxy
sudo systemctl restart nginx

# Test
curl http://example.com/api/users
# Works! Nginx proxied it to your Flask app
```

## Important Headers

When Nginx proxies, it must forward certain headers so the backend knows about the original client.

### Without Headers

```python
# Flask sees request from Nginx (127.0.0.1)
@app.route('/user-ip')
def get_ip():
    return {'ip': request.remote_addr}  # Returns 127.0.0.1 (wrong!)
```

### With Headers

```nginx
# Forward important headers
location / {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

What each header means:

```
Host: original.com
  What hostname was requested?
  Important for multi-domain setups

X-Real-IP: 203.0.113.45
  Client's actual IP address

X-Forwarded-For: 203.0.113.45, 10.0.0.1
  Chain of IPs (client, then any proxies)

X-Forwarded-Proto: https
  Was original request HTTP or HTTPS?
  Important for app to know if it should send secure cookies
```

Backend code:

```python
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,        # Trust 1 proxy for X-Forwarded-For
    x_proto=1,      # Trust proxy for protocol
    x_host=1,       # Trust proxy for host
    x_port=1        # Trust proxy for port
)

@app.route('/client-info')
def client_info():
    return {
        'ip': request.remote_addr,           # Now correct IP
        'protocol': request.scheme,           # http or https
        'host': request.host,                 # example.com
    }
```

## TLS Termination (HTTPS)

Nginx handles HTTPS. Backend runs plain HTTP internally.

### Setup

```nginx
server {
    listen 443 ssl;
    server_name example.com;
    
    # Certificate from Let's Encrypt or other CA
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    # Security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    location / {
        proxy_pass http://backend;
        
        # Important: Tell backend original was HTTPS
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}
```

### Obtaining Certificate

```bash
# Install Let's Encrypt certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --standalone -d example.com

# Certificate location
/etc/letsencrypt/live/example.com/fullchain.pem
/etc/letsencrypt/live/example.com/privkey.pem

# Auto-renewal (runs periodically)
sudo certbot renew
```

### Backend Code (Handling HTTPS)

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/api/auth')
def auth():
    # Check if original request was HTTPS
    if request.scheme != 'https':
        return {'error': 'HTTPS required'}, 400
    
    # Set secure cookie (only sent over HTTPS)
    response = make_response({'status': 'logged in'})
    response.set_cookie(
        'session_token',
        'token123',
        secure=True,      # Only sent over HTTPS
        httponly=True,    # Not accessible from JavaScript
        samesite='Strict' # CSRF protection
    )
    return response
```

## Caching Responses

Nginx can cache responses, reducing backend load.

### Configuration

```nginx
# Define cache zone (in http block)
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=my_cache:10m max_size=1g inactive=60m;

server {
    location / {
        proxy_cache my_cache;
        
        # Cache successful responses for 1 hour
        proxy_cache_valid 200 1h;
        
        # Cache 404s for 5 minutes
        proxy_cache_valid 404 5m;
        
        # Don't cache if Set-Cookie header present
        proxy_cache_bypass $http_set_cookie;
        
        # Show cache status in response
        add_header X-Cache-Status $upstream_cache_status;
        
        proxy_pass http://backend;
    }
}
```

Check cache status:

```bash
curl -i http://example.com/api/users

# Response headers:
# X-Cache-Status: MISS     (first request, not cached)
# X-Cache-Status: HIT      (subsequent requests, from cache)
# X-Cache-Status: BYPASS   (not cached due to Set-Cookie)
```

### Smart Caching

```nginx
# Cache static assets longer
location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
    proxy_cache my_cache;
    proxy_cache_valid 200 30d;
    add_header Cache-Control "public, max-age=2592000";
}

# Don't cache API endpoints that change often
location /api/ {
    proxy_cache my_cache;
    proxy_cache_valid 200 5s;  # Very short TTL
}

# Don't cache authenticated endpoints
location /api/user/profile {
    proxy_cache off;  # No caching
    proxy_pass http://backend;
}
```

## Compression

Nginx compresses responses to reduce bandwidth.

### Configuration

```nginx
server {
    # Enable gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    
    # Compress these types
    gzip_types text/plain text/css application/json application/javascript;
    
    # Compression level (1-9, higher = more CPU)
    gzip_comp_level 6;
    
    location / {
        proxy_pass http://backend;
    }
}
```

### Verification

```bash
# Without compression
curl -I http://example.com/api/data
# Content-Length: 1000000

# With compression
curl -I http://example.com/api/data
# Content-Encoding: gzip
# Content-Length: 100000  (10% of original)
```

## Rate Limiting

Prevent clients from overwhelming your backend.

### Configuration

```nginx
# Define rate limit zone (in http block)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/m;
limit_req_zone $http_x_api_key zone=api_key_limit:10m rate=1000r/m;

server {
    # Limit unauthenticated requests
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://backend;
    }
    
    # Limit by API key
    location /api/v2/ {
        limit_req zone=api_key_limit burst=50 nodelay;
        proxy_pass http://backend;
    }
}
```

What this does:

```
limit_req_zone $binary_remote_addr
  → Track per client IP

zone=api_limit:10m
  → Zone name and memory size

rate=100r/m
  → 100 requests per minute

burst=20
  → Allow up to 20 extra requests (temporary burst)

nodelay
  → Immediately reject excess requests
     (vs queueing them)
```

Check rate limit status:

```bash
# First 100 requests per minute: OK
curl http://example.com/api/users  # 200 OK

# Request 101 in same minute: Rejected
curl http://example.com/api/users  # 429 Too Many Requests
```

## Request Routing

Route different URLs to different backends.

### Example: API + Static Content

```nginx
upstream api_backend {
    server 127.0.0.1:5000;
}

upstream static_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    
    # Static files
    location /static/ {
        proxy_pass http://static_backend;
    }
    
    # API requests
    location /api/ {
        proxy_pass http://api_backend;
    }
    
    # Default
    location / {
        return 404;
    }
}
```

### Example: Service Routing

```nginx
upstream users_service {
    server 127.0.0.1:5001;
}

upstream orders_service {
    server 127.0.0.1:5002;
}

upstream products_service {
    server 127.0.0.1:5003;
}

server {
    listen 80;
    
    location /users/ {
        proxy_pass http://users_service;
        rewrite ^/users/(.*) /$1 break;
    }
    
    location /orders/ {
        proxy_pass http://orders_service;
        rewrite ^/orders/(.*) /$1 break;
    }
    
    location /products/ {
        proxy_pass http://products_service;
        rewrite ^/products/(.*) /$1 break;
    }
}
```

Request flow:

```
GET /users/123              → Routed to users_service:5001
GET /orders/456             → Routed to orders_service:5002
GET /products/789           → Routed to products_service:5003
```

## Security Features

### Hiding Backend Details

```nginx
server {
    location / {
        proxy_pass http://backend;
        
        # Remove server header (hides Flask, Django, etc.)
        proxy_pass_header Server;
        proxy_hide_header Server;
        
        # Remove X-Powered-By header
        proxy_hide_header X-Powered-By;
        proxy_hide_header X-AspNet-Version;
    }
}
```

### Preventing Dangerous Methods

```nginx
server {
    location / {
        # Only allow GET, POST, PUT, DELETE, PATCH
        limit_except GET POST PUT DELETE PATCH {
            deny all;
        }
        proxy_pass http://backend;
    }
}
```

### IP Whitelisting

```nginx
server {
    location /admin/ {
        allow 203.0.113.0/24;    # Company office
        allow 127.0.0.1;         # Localhost
        deny all;                # Deny everyone else
        
        proxy_pass http://backend;
    }
}
```

### DDoS Protection

```nginx
# Limit connections per IP
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

server {
    location / {
        # Max 10 simultaneous connections per IP
        limit_conn conn_limit 10;
        
        proxy_pass http://backend;
    }
}
```

## Debugging Reverse Proxy Issues

### Issue: Backend Returns 502 Bad Gateway

```
Error: 502 Bad Gateway
```

Meaning: Nginx couldn't reach the backend.

Debug:

```bash
# Check if backend is running
curl http://127.0.0.1:5000/

# Check Nginx logs
tail -f /var/log/nginx/error.log

# Verify backend in upstream is correct
grep "upstream" /etc/nginx/nginx.conf

# Restart Nginx
sudo systemctl restart nginx

# Check Nginx syntax
sudo nginx -t
```

### Issue: Infinite Redirect

```
Error: Redirect loop detected
```

Often caused by rewrite rules:

```nginx
# Wrong: Redirects client to itself
location / {
    return 301 https://$server_name$request_uri;
}

location / {
    return 301 https://$server_name$request_uri;
}
```

### Issue: CORS Errors

```
Error: Access to XMLHttpRequest blocked by CORS policy
```

Backend needs to return CORS headers:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=['https://example.com'])

# Or manually:
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://example.com'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE'
    return response
```

Nginx can also add headers:

```nginx
location / {
    proxy_pass http://backend;
    
    # Add CORS headers if backend doesn't
    add_header 'Access-Control-Allow-Origin' 'https://example.com' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE' always;
}
```

## Complete Production Config

```nginx
# /etc/nginx/sites-available/example.com

upstream backend {
    least_conn;
    server 127.0.0.1:5001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5002 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5003 max_fails=3 fail_timeout=30s;
}

# Cache zone
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=backend_cache:50m max_size=10g inactive=60m;

# Rate limit zones
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/m;
limit_req_zone $binary_remote_addr zone=api:10m rate=1000r/m;

server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;
    
    # SSL
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Gzip
    gzip on;
    gzip_types text/plain application/json application/javascript;
    gzip_comp_level 6;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    
    # API endpoints
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        
        proxy_pass http://backend;
        proxy_cache backend_cache;
        proxy_cache_valid 200 5m;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        
        add_header X-Cache-Status $upstream_cache_status;
    }
    
    # Static files
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        proxy_pass http://backend;
        proxy_cache backend_cache;
        proxy_cache_valid 200 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Health check
    location /health {
        access_log off;
        proxy_pass http://backend;
    }
}
```

Enable:

```bash
sudo ln -s /etc/nginx/sites-available/example.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Module 6 Assessment

### Practice Questions (MCQ - No Answers Provided)

1. Why does Nginx need to set X-Forwarded-For header when proxying?
   a) Required by HTTP specification
   b) Backend needs to know client's actual IP
   c) Nginx is hiding its own IP
   d) For logging purposes only

2. TLS termination at Nginx means:
   a) Nginx uses HTTP, backend uses HTTPS
   b) Nginx decrypts HTTPS, backend receives HTTP
   c) Both use HTTPS
   d) Neither uses encryption

3. Nginx response header X-Cache-Status: BYPASS most likely means:
   a) Cache is disabled
   b) Response had Set-Cookie or similar header preventing cache
   c) Client explicitly disabled cache
   d) Cache was empty

4. You configure `limit_req rate=100r/m burst=20`. What happens on request 121 in same minute?
   a) Request succeeds (burst allows it)
   b) Request is queued (waits for slot)
   c) Request returns 429 Too Many Requests
   d) Request is redirected

5. Your Flask app receives request from 127.0.0.1 instead of actual client IP. Why?
   a) Client IP is hidden by ISP
   b) Nginx not forwarding X-Forwarded-For
   c) Backend not configured to trust proxy
   d) All of the above

### Practical Networking Tasks

**Task 1: Set Up Complete Reverse Proxy**

- Create Flask backend on port 5000
- Configure Nginx as reverse proxy:
  - Listen on port 80
  - Proxy to Flask backend
  - Forward X-Real-IP and X-Forwarded-For headers
  - Add cache for static content
  - Add rate limiting (100 req/min)
- Test:
  ```bash
  for i in {1..150}; do curl http://localhost/; done
  # 100 should succeed, 50 should get 429
  ```

**Task 2: Set Up HTTPS**

- Use certbot to get Let's Encrypt certificate (or self-signed for testing)
- Configure Nginx:
  - Listen on 443 with SSL
  - TLS termination (backend stays HTTP)
  - Redirect HTTP to HTTPS
- Verify:
  ```bash
  curl https://localhost/  # Works
  curl http://localhost/   # Redirects to https
  ```

### Production Incident Scenario

**Incident**: Users report their IP appears as 127.0.0.1 in your logs. Also, secure cookies aren't being sent.

Your setup:
- Nginx reverse proxy on port 80/443
- Flask backend on port 5000
- Flask receiving requests

Investigation shows:

```python
@app.route('/info')
def info():
    return {
        'client_ip': request.remote_addr,  # Returns 127.0.0.1
        'scheme': request.scheme,          # Returns http (not https)
    }
```

Questions:

1. Why is client_ip showing 127.0.0.1?
2. Why is scheme showing http when users accessed via https?
3. What headers should Nginx be forwarding?
4. How do you fix this in Flask?
5. Why does scheme matter for secure cookies?

---

**Next**: [Module 7: DNS and Domain Management](07-dns-domain-management.md)
