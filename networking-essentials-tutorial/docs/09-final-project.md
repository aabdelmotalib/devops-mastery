# Module 9: Final Project - Production Networking Setup

## Objective

Design and implement a **complete, production-ready networking infrastructure** that brings together all concepts from Modules 1-8.

## Requirements

Your system must include:

1. **Domain with DNS**
   - A registered domain (or use local DNS)
   - Proper DNS records (A, CNAME, MX)
   - TTL configured appropriately

2. **HTTPS/TLS**
   - Valid certificate (Let's Encrypt)
   - Nginx TLS termination
   - Automatic renewal

3. **Reverse Proxy (Nginx)**
   - Request routing
   - Load balancing across backends
   - Caching for static content
   - Rate limiting
   - Security headers

4. **Load-Balanced Backend Services**
   - Multiple Flask/FastAPI instances
   - Health checks
   - Proper error handling
   - REST API design
   - Stateless or Redis-based sessions

5. **Secure API Exposure**
   - No backend IP exposed
   - Proper header forwarding
   - Authentication/Authorization
   - Input validation
   - Rate limiting per API key

6. **Monitoring & Observability**
   - Health check endpoints
   - Metrics collection
   - Logging with proper context
   - Request tracing

## Architecture

```
                    DNS
                     |
          (resolve example.com to IP)
                     |
        ┌────────────┴────────────┐
        |                         |
    Nginx (Port 80/443)       Nginx (Backup)
    (TLS Termination,         (HA Setup)
     Load Balancer)
        |
        ├──────┬──────┬──────┐
        |      |      |      |
       App1   App2   App3   App4
      :5001  :5002  :5003  :5004
        |      |      |      |
        └──────┼──────┼──────┘
               |      |
             Redis   PostgreSQL
            (cache)  (persistent data)
```

## Phase 1: Infrastructure Setup

### 1.1 Start with Docker Compose (Recommended for Testing)

```bash
cd final-project
docker-compose up -d
# Creates: multiple backends, Nginx, Redis, PostgreSQL
```

Or manual setup on Linux VMs/servers.

### 1.2 Backend Services

Create 4 identical Flask instances with different ports:

```bash
# Backend 1
python app.py --port 5001 --instance "app-1"

# Backend 2
python app.py --port 5002 --instance "app-2"

# Backend 3
python app.py --port 5003 --instance "app-3"

# Backend 4
python app.py --port 5004 --instance "app-4"
```

### 1.3 Configure Nginx

Nginx serves on port 80/443, load balances to backends, handles TLS.

## Phase 2: Implement REST API

Implement a simple e-commerce API with:

### Endpoints

```
POST /api/v1/products               Create product
GET /api/v1/products                List products (paginated, filterable)
GET /api/v1/products/:id            Get product details
PATCH /api/v1/products/:id          Update product
DELETE /api/v1/products/:id         Delete product

POST /api/v1/orders                 Create order
GET /api/v1/orders                  List user's orders
GET /api/v1/orders/:id              Get order details

POST /api/v1/auth/login             Login
POST /api/v1/auth/logout            Logout
GET /api/v1/auth/profile            Get user profile
```

### Database

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10, 2),
    inventory INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total_price DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Phase 3: Implement Required Features

### 3.1 Authentication

```python
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return {'error': 'Invalid credentials'}, 401
    
    access_token = create_access_token(identity=user.id)
    return {'access_token': access_token}, 200

@app.route('/api/v1/orders', methods=['POST'])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    # Create order for authenticated user
    pass
```

### 3.2 Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/v1/orders', methods=['POST'])
@limiter.limit("10 per minute")  # 10 orders per minute per IP
def create_order():
    pass
```

### 3.3 Health Check Endpoint

```python
@app.route('/health')
def health_check():
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check cache connection
        redis.ping()
        
        return {
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok',
            'timestamp': datetime.now().isoformat()
        }, 200
    except Exception as e:
        return {
            'status': 'unhealthy',
            'error': str(e)
        }, 503

@app.route('/ready')
def readiness_check():
    # Check if ready to receive traffic
    if db.session.execute('SELECT 1'):
        return {'status': 'ready'}, 200
    return {'status': 'not ready'}, 503
```

### 3.4 Logging with Context

```python
import logging
import uuid

# Add request ID for tracing
@app.before_request
def add_request_id():
    request.id = str(uuid.uuid4())
    app.logger.info(f"Request {request.method} {request.path}", extra={
        'request_id': request.id,
        'client_ip': request.remote_addr
    })

@app.route('/api/v1/products')
def list_products():
    app.logger.info("Fetching products", extra={
        'request_id': request.id
    })
    products = Product.query.all()
    return jsonify(products)
```

## Phase 4: Nginx Configuration

See examples/nginx-production.conf for complete configuration.

Key features:

```nginx
# TLS termination
listen 443 ssl http2;
ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

# Load balancing with health checks
upstream backend {
    least_conn;
    server app-1:5001 max_fails=3 fail_timeout=30s;
    server app-2:5002 max_fails=3 fail_timeout=30s;
    server app-3:5003 max_fails=3 fail_timeout=30s;
    server app-4:5004 max_fails=3 fail_timeout=30s;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
limit_req_zone $http_x_api_key zone=api_key:10m rate=1000r/m;

# Caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=cache:100m;

server {
    listen 443 ssl;
    
    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20;
        
        proxy_pass http://backend;
        proxy_cache cache;
        proxy_cache_valid 200 5m;
        
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}
```

## Phase 5: Testing

### 5.1 Test REST API

```bash
# Get products
curl http://localhost/api/v1/products

# Create product (requires auth)
curl -X POST http://localhost/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Laptop", "price": 999.99}'

# List products with pagination
curl 'http://localhost/api/v1/products?page=1&limit=10'

# Filter products
curl 'http://localhost/api/v1/products?min_price=100&max_price=500'
```

### 5.2 Test Load Balancing

```bash
# Send multiple requests, verify different instances handle them
for i in {1..10}; do
  curl -i http://localhost/api/v1/health | grep "Server:"
done

# Should see different server IDs
```

### 5.3 Test TLS

```bash
# Verify HTTPS works
curl -v https://localhost/

# Test cert validity
openssl s_client -connect localhost:443

# Check security headers
curl -i https://localhost/ | grep -i "Strict-Transport"
```

### 5.4 Test Rate Limiting

```bash
# Send 150 requests per minute
for i in {1..150}; do
  curl http://localhost/api/v1/products
done

# Some should return 429 Too Many Requests
```

### 5.5 Test Health Checks

```bash
# Verify health endpoint
curl http://localhost/health

# Verify readiness
curl http://localhost/ready

# Verify Nginx recognizes unhealthy backend
curl http://localhost/api/v1/products  # Should work
docker stop app-1  # Kill one backend
curl http://localhost/api/v1/products  # Should still work
docker start app-1
```

## Phase 6: Monitoring

### 6.1 Metrics Collection

```python
from prometheus_client import Counter, Histogram, generate_latest

request_count = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.before_request
def start_timer():
    request.start_time = time.time()

@app.after_request
def record_metrics(response):
    duration = time.time() - request.start_time
    request_count.labels(
        method=request.method,
        endpoint=request.endpoint or 'unknown'
    ).inc()
    request_duration.observe(duration)
    return response

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### 6.2 Log Aggregation

All instances should log to same place:

```python
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.FileHandler('/var/log/app/app.log')
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
app.logger.addHandler(logHandler)
```

## Phase 7: Documentation

Create documentation:

### 7.1 API Documentation

```markdown
# API Documentation

## Authentication

All protected endpoints require JWT token:

```
Authorization: Bearer {token}
```

## Endpoints

### POST /api/v1/auth/login

Login user and receive access token.

**Request:**
```json
{
  "username": "john",
  "password": "secret123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGc..."
}
```
```

### 7.2 Deployment Guide

```markdown
# Deployment Guide

## Prerequisites
- Docker and Docker Compose
- Domain with DNS configured
- Let's Encrypt certificate

## Installation

1. Clone repository
2. Configure environment variables
3. Run `docker-compose up -d`
4. Verify with `curl https://your-domain.com/health`

## Scaling

To add more backend instances:
- Add service in docker-compose.yml
- Update Nginx upstream servers
- Reload Nginx: `docker exec nginx nginx -s reload`
```

### 7.3 Troubleshooting Guide

```markdown
# Troubleshooting

## 502 Bad Gateway

Nginx can't reach backend.

Check:
1. Backend is running: `docker ps`
2. Firewall allows connection
3. Nginx config has correct backend address
4. Backend health endpoint works

## HTTPS Certificate Error

Certificate doesn't match domain.

Check:
1. Certificate includes correct domains
2. Certificate not expired
3. Browser has correct domain

## Rate Limit Blocking Legitimate Traffic

Rate limit too strict.

Solution:
1. Increase rate limit in Nginx
2. Use API key with higher limit
3. Whitelist specific IPs
```

## Evaluation Criteria

Your implementation will be evaluated on:

- **Functionality**: All endpoints work correctly
- **Performance**: Load balancing distributes requests evenly
- **Security**: HTTPS enforced, auth required, rate limiting works
- **Reliability**: Health checks detect failures, graceful degradation
- **Observability**: Metrics, logs, request IDs for tracing
- **Documentation**: Clear, complete, accurate
- **Code Quality**: Clean, readable, well-structured
- **Production-Readiness**: Handles errors, graceful shutdown, auto-recovery

## Bonus Features (Optional)

Implement additional features for deeper learning:

- [ ] Distributed caching with Redis
- [ ] Database connection pooling
- [ ] Request/response compression
- [ ] CORS with proper configuration
- [ ] Database migrations with Alembic
- [ ] Structured logging with request IDs
- [ ] Distributed tracing with Jaeger
- [ ] Metrics with Prometheus and Grafana
- [ ] API rate limiting per API key (not just IP)
- [ ] Graceful shutdown and connection draining
- [ ] Circuit breaker pattern for backend failures
- [ ] Database backup and recovery procedures
- [ ] Multi-region failover (conceptual)
- [ ] WebSocket support for real-time updates
- [ ] GraphQL endpoint alongside REST

## Submission Checklist

- [ ] Code committed to git repository
- [ ] All endpoints implemented and tested
- [ ] Nginx configuration optimized
- [ ] TLS configured correctly
- [ ] DNS configured (or /etc/hosts for local)
- [ ] Health checks passing
- [ ] Load balancing working
- [ ] Rate limiting enforced
- [ ] Logging with context (request ID)
- [ ] Documentation complete
- [ ] Tested in "production-like" environment
- [ ] Security considerations addressed
- [ ] Performance benchmarked

## Common Pitfalls to Avoid

1. **Hardcoding IPs**: Use hostnames, DNS, or service discovery
2. **No health checks**: Nginx will route to dead backends
3. **Tight rate limits**: Legitimate traffic gets blocked
4. **Missing headers**: Backend doesn't know real client IP
5. **No logging**: Can't debug issues
6. **Self-signed certs**: Use Let's Encrypt
7. **No monitoring**: No visibility into system
8. **Single point of failure**: Use multiple backends/LBs
9. **No error handling**: Crashes go unexplained
10. **Not testing failure scenarios**: Works until it doesn't

## Timeline Suggestion

- **Day 1**: Set up infrastructure (Nginx, backends, database)
- **Day 2**: Implement core REST API endpoints
- **Day 3**: Add authentication, rate limiting, health checks
- **Day 4**: Set up TLS, DNS, monitoring
- **Day 5**: Testing, documentation, bug fixes

---

## What You'll Have Built

A complete, production-grade networking setup that demonstrates:

- DNS fundamentals (domain → IP)
- HTTP/REST API design
- Load balancing across multiple instances
- TLS/HTTPS encryption
- Reverse proxy (Nginx) handling requests
- Authentication and security
- Monitoring and observability
- Real-world networking patterns

This is the kind of system you'll maintain in real production environments. All the pieces (Nginx, load balancing, TLS, monitoring) are exactly what large companies use, just smaller scale.

---

**Congratulations!** You've completed the Networking Essentials Tutorial.

You can now:
- Understand how networks actually work
- Deploy real systems with proper architecture
- Debug networking issues systematically
- Design scalable backend systems
- Secure applications with HTTPS
- Monitor and maintain production systems

Keep learning, keep building, and always remember: **networks are just how computers talk to each other.**
