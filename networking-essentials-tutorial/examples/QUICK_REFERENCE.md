# Networking Essentials - Quick Reference Guide

A condensed reference for networking concepts learned in this tutorial.

## Module 1: Networking Fundamentals

### IP Addresses
```
IPv4 format: 192.168.1.100 (four octets, 0-255 each)

Important ranges:
  127.0.0.1          Localhost (loopback)
  192.168.0.0/16     Private network
  10.0.0.0/8         Private network
  172.16.0.0/12      Private network (Docker default)
```

### Ports
```
0-1023:        Privileged (need root)
1024-49151:    Registered
49152-65535:   Dynamic/private

Common:
  22      SSH
  80      HTTP
  443     HTTPS
  5000    Flask
  5432    PostgreSQL
  6379    Redis
```

### TCP vs UDP
```
TCP:  Reliable, ordered, slower (HTTP, databases)
UDP:  Fast, unreliable (DNS, video streaming)
```

### Check Ports
```bash
netstat -tlnp          # View listening ports
ss -tan                # Modern syntax
lsof -i :5000          # What's using port 5000
curl -v http://localhost:5000  # Test connection
```

---

## Module 2: HTTP/HTTPS

### HTTP Methods
```
GET     Retrieve data
POST    Create data
PUT     Replace entire resource
PATCH   Update part of resource
DELETE  Remove data
```

### Status Codes
```
2xx     Success (200 OK, 201 Created, 204 No Content)
3xx     Redirect (301 Moved, 302 Found)
4xx     Client error (400 Bad Request, 404 Not Found, 429 Rate Limit)
5xx     Server error (500, 502 Bad Gateway, 503 Service Unavailable)
```

### HTTPS
```
HTTPS = HTTP + TLS encryption

TLS Handshake:
1. Client: "Let's encrypt"
2. Server: "Here's my certificate"
3. Client: "Here's encryption key"
4. Both: Encrypted communication starts
```

---

## Module 3: REST API Design

### Resource Naming
```
Right:
  GET /users
  POST /users
  GET /users/123
  PATCH /users/123
  DELETE /users/123

Wrong:
  GET /getUsers
  POST /createUser
  DELETE /deleteUser?id=123
```

### Pagination & Filtering
```
GET /users?page=1&limit=10
GET /products?category=electronics&price_min=100
GET /posts?sort=-created_at&sort=title
```

### Response Format
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "pages": 10
  }
}
```

### Idempotency
```
Idempotent (same result if repeated):
  GET /users/123      ✓
  PUT /users/123      ✓
  DELETE /users/123   ✓

Non-idempotent:
  POST /users         ✗ Creates multiple
```

---

## Module 4: WebSockets

### When to Use
```
HTTP:       One request → one response
WebSocket:  Bidirectional, server can push anytime

Use WebSocket for:
  Chat applications
  Real-time notifications
  Live collaboration
  Stock price updates
```

### Flask-SocketIO Example
```python
from flask_socketio import SocketIO, emit

socketio = SocketIO(app)

@socketio.on('message')
def handle_message(data):
    emit('message', {'data': data}, broadcast=True)
```

### Scaling WebSockets
```
One server → ~10,000 concurrent connections

Multiple servers:
  Use Redis message broker
  All servers publish/subscribe through Redis
```

---

## Module 5: Load Balancing

### Algorithms
```
Round-robin:      Next server in rotation
Least-conn:       Server with fewest connections
IP hash:          Same client → same server (sticky)
Weighted:         Powerful servers get more traffic
```

### Nginx Config
```nginx
upstream backend {
    least_conn;
    server 127.0.0.1:5001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    location / {
        proxy_pass http://backend;
    }
}
```

### Health Checks
```bash
# Check endpoint must be lightweight
@app.route('/health')
def health():
    return {'status': 'ok'}, 200
```

---

## Module 6: Reverse Proxy (Nginx)

### Why
```
1. Hide backend IP
2. TLS termination
3. Load balancing
4. Caching
5. Rate limiting
6. Security layer
```

### Basic Setup
```nginx
server {
    listen 443 ssl;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

### Caching
```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=cache:10m;

location /api/ {
    proxy_cache cache;
    proxy_cache_valid 200 5m;
    proxy_pass http://backend;
}
```

### Rate Limiting
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}
```

---

## Module 7: DNS

### Record Types
```
A      Domain → IPv4 (example.com → 203.0.113.45)
AAAA   Domain → IPv6
CNAME  Alias (www → example.com)
MX     Mail exchange (for email)
TXT    Custom text (SPF, DKIM, DMARC)
NS     Nameserver
```

### TTL (Time To Live)
```
TTL=300      Cache for 5 minutes
TTL=3600     Cache for 1 hour
TTL=86400    Cache for 1 day

Lower TTL before changing DNS records
```

### Commands
```bash
dig example.com              # Full query
dig example.com A            # A records only
dig example.com MX           # Mail records
nslookup example.com         # Simple lookup
host example.com             # Short form
```

### Common Mistakes
```
✗ Wrong nameservers at registrar
✗ TTL too high when changing IP
✗ Missing www subdomain
✗ Forgetting MX records
✗ Not waiting for propagation
```

---

## Module 8: SSL/TLS Certificates

### Let's Encrypt
```bash
sudo apt install certbot

# Get certificate
sudo certbot certonly --standalone -d example.com

# Auto-renewal
sudo certbot renew
```

### Certificate Files
```
/etc/letsencrypt/live/example.com/
  ├── fullchain.pem      (cert + chain)
  ├── privkey.pem        (private key)
  ├── cert.pem           (your certificate)
  └── chain.pem          (intermediate chain)
```

### Nginx TLS
```nginx
server {
    listen 443 ssl;
    
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### HSTS Header
```
Strict-Transport-Security: max-age=31536000

Tells browsers: Always use HTTPS for next year
```

### Secure Cookies
```python
response.set_cookie(
    'session',
    'value',
    secure=True,      # HTTPS only
    httponly=True,    # Not accessible from JS
    samesite='Strict' # CSRF protection
)
```

---

## Common Errors & Solutions

### 502 Bad Gateway
```
Cause:  Nginx can't reach backend

Check:
  1. Backend running? docker ps
  2. Firewall allows it? sudo ufw status
  3. Nginx config correct? sudo nginx -t
  4. Backend health? curl http://backend:5000/health
```

### 404 Not Found
```
Cause:  Route doesn't exist

Check:
  1. Is endpoint implemented?
  2. Is path correct? (typo in URL?)
  3. Is method right? (GET vs POST?)
```

### HTTPS Certificate Error
```
Cause:  Certificate doesn't match domain

Check:
  1. Certificate includes domain? openssl x509 -in cert.pem -text
  2. Domain matches? grep "example.com" certificate
  3. Certificate expired? date compare
```

### Connection Refused
```
Cause:  Can't reach server

Check:
  1. Server running? docker ps
  2. Port correct? netstat -tlnp
  3. Firewall blocking? sudo ufw status
  4. Network reachable? ping hostname
```

### Rate Limit Blocking
```
Cause:  Too many requests per IP

Fix:
  1. Increase limit in Nginx
  2. Use API key with higher limit
  3. Whitelist IP: allow 203.0.113.0/24
```

---

## Architecture Template

```
                  Domain
                 (example.com)
                     ↓
                  DNS Resolver
                     ↓
              Nginx LB (Port 80/443)
                     ↓
         ┌────────┬────────┬────────┐
         ↓        ↓        ↓        ↓
       App1     App2     App3     App4
      :5001    :5002    :5003    :5004
         ↓        ↓        ↓        ↓
         └────────┼────────┼────────┘
                  ↓
             PostgreSQL
             Redis Cache
```

---

## Testing Commands

```bash
# Test HTTP endpoint
curl -v http://localhost/api/users

# Test HTTPS
curl -i https://localhost/ --insecure

# Test with headers
curl -H "Authorization: Bearer token" \
     -H "Content-Type: application/json" \
     -d '{"name": "test"}' \
     http://localhost/api/users

# Test rate limiting (150 requests)
for i in {1..150}; do curl http://localhost/api/; done

# Monitor load balancing
watch -n 1 'curl -s http://localhost/info | grep server'

# Check DNS
dig example.com
nslookup example.com

# Monitor ports
watch -n 1 'ss -tan | grep LISTEN'

# View Nginx status
curl http://127.0.0.1:8080/nginx_status
```

---

## Configuration Files Location

```
Nginx:           /etc/nginx/nginx.conf
                 /etc/nginx/sites-available/
                 /etc/nginx/sites-enabled/

Let's Encrypt:   /etc/letsencrypt/live/domain/
                 /etc/letsencrypt/renewal/

Logs:            /var/log/nginx/access.log
                 /var/log/nginx/error.log
                 /var/log/syslog

Cache:           /var/cache/nginx/
```

---

## Quick Troubleshooting Flowchart

```
Issue: Site not reachable

1. DNS resolves? → No: Check DNS records
                → Yes: Continue

2. Can ping IP? → No: Check firewall
               → Yes: Continue

3. Port responding? → No: Check if service running
                   → Yes: Continue

4. Nginx running? → No: Start Nginx
                 → Yes: Continue

5. Backend reachable? → No: Check backend config
                      → Yes: Continue

6. TLS error? → Yes: Check certificate
             → No: Check Nginx config

7. Still broken? Check logs:
   - /var/log/nginx/error.log
   - Backend application logs
```

---

## Remember

- Networks are just how computers talk to each other
- Start simple, add complexity when needed
- Always secure production systems
- Monitor everything
- Test failure scenarios
- Document your setup
- Automate certificate renewal
- Keep systems simple and maintainable

Good luck with your networking journey!
