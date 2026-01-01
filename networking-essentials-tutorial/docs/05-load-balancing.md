# Module 5: Load Balancing

## Why Load Balancing Exists

One server can only handle so much traffic.

```
Client 1 ──┐
Client 2 ──┤
Client 3 ──┤──→ Single Server (10,000 requests/sec max)
Client 4 ──┤
...        │
Client 10K┘

If traffic exceeds 10,000 req/sec, requests queue and fail.
```

Solution: **Distribute traffic across multiple servers.**

```
            ┌──→ Server 1 (5,000 req/sec)
Client ─→ Load Balancer ─┼──→ Server 2 (5,000 req/sec)
            └──→ Server 3 (5,000 req/sec)

Now can handle 15,000 req/sec total
```

## Load Balancing Fundamentals

### Two Layers: L4 vs L7

#### L4 (Transport Layer) Load Balancing

Works at TCP/UDP level. Routes packets based on:

- Source IP
- Destination IP
- Port numbers

**Characteristics:**

- Very fast (no need to read request content)
- Lower CPU usage
- Can't see what's inside the request (HTTP path, headers, etc.)

```
Client → [L4 LB checks: src IP, dst IP, port] → Server
         Forwards entire TCP stream

LB doesn't care if it's HTTP, HTTPS, SSH, etc.
Just distributes based on IPs and ports
```

#### L7 (Application Layer) Load Balancing

Works at HTTP/HTTPS level. Routes based on:

- HTTP path (`/api/users` vs `/api/products`)
- Hostname/domain
- HTTP headers
- Cookie values

**Characteristics:**

- Can read full request
- Smart routing decisions
- Higher CPU usage (needs to parse HTTP)

```
Client → [L7 LB reads: GET /api/users HTTP/1.1] → Server A
         [L7 LB reads: POST /images HTTP/1.1] → Server B
         [L7 LB reads: GET /api/products HTTP/1.1] → Server C

Different URLs go to different servers
```

### L4 vs L7 Decision Table

| Aspect | L4 | L7 |
|--------|----|----|
| Performance | Fast | Slower |
| CPU Usage | Low | High |
| Can inspect HTTP | No | Yes |
| Smart routing | No | Yes |
| Cost | Cheap | Expensive |
| Use case | High traffic, simple | Complex routing |

**Common choice:** L7 for web apps (need smart routing), L4 for databases/cache.

## Load Balancing Algorithms

### 1. Round-Robin

Send each request to next server in list.

```
Requests:  1   2   3   4   5   6
Servers:   A → B → C → A → B → C

Pros:
- Simple
- Fair distribution

Cons:
- Doesn't consider server load
- Doesn't consider request size
```

```nginx
upstream backend {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;  # Default is round-robin
    }
}
```

### 2. Least Connections

Send request to server with fewest active connections.

```
Server A: 50 connections
Server B: 10 connections
Server C: 30 connections

New request → Server B (fewest connections)

Pros:
- Better load distribution
- Accounts for connection count

Cons:
- Assumes all connections equal
- Slower connections block others
```

```nginx
upstream backend {
    least_conn;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}
```

### 3. Weighted Round-Robin

Some servers are more powerful. Give them more traffic.

```
Server A (powerful):   weight=3
Server B (weak):       weight=1
Server C (medium):     weight=2

Requests: A → A → A → B → C → C → (repeat)

3 requests to A, 1 to B, 2 to C per cycle
```

```nginx
upstream backend {
    server 127.0.0.1:5001 weight=3;  # Most traffic
    server 127.0.0.1:5002 weight=1;  # Least traffic
    server 127.0.0.1:5003 weight=2;  # Medium traffic
}
```

### 4. IP Hash

Route based on client's IP address. Same client always goes to same server.

```
Client IP 192.168.1.10  → hash → Server A (always)
Client IP 192.168.1.20  → hash → Server B (always)
Client IP 192.168.1.30  → hash → Server C (always)

Pros:
- Session consistency (no need to share session state)
- Good for stateful apps

Cons:
- Uneven distribution (depends on client IPs)
- One server goes down = many clients affected
```

```nginx
upstream backend {
    ip_hash;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}
```

### 5. Consistent Hashing

Advanced algorithm that handles server failures better than IP hash.

When server fails:

```
IP Hash:
  Old: IPs 1-100 → Server A, 101-200 → Server B
  Server A fails
  New: IPs 1-100 → Server B (100 clients suddenly reconnect)
  Problem: Server B overloaded, Storm of reconnections

Consistent Hash:
  Old: IPs distributed via hash
  Server A fails
  New: Only IPs that hashed to A reassigned (smooth)
  Problem: More distributed, less thundering herd
```

## Sticky Sessions (Session Affinity)

If you store session state on servers, you need sticky sessions.

```
User logs in → Server A (stores session data)
User makes request → Load Balancer
  Should route to Server A (has their session)
  NOT to Server B or C
```

### Using Cookies (L7 Load Balancer)

```nginx
upstream backend {
    server 127.0.0.1:5001 route=app1;
    server 127.0.0.1:5002 route=app2;
    server 127.0.0.1:5003 route=app3;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
        proxy_cookie_path ~^(?P<path>/.*)$ "$path; Route=route";
        proxy_cookie_flags ~ secure httponly samesite=lax;
    }
}
```

Or simpler with IP hash (makes all requests from same client go to same server):

```nginx
upstream backend {
    ip_hash;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}
```

### Better: Store Sessions in Redis (Stateless)

Don't store sessions on servers. Store in Redis (shared).

```python
# Flask with Redis sessions
from flask import Flask, session
from flask_session import Session
from redis import Redis

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = Redis(host='redis.local', port=6379)

Session(app)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = authenticate_user(data['username'], data['password'])
    
    # Store in Redis (shared, not server-local)
    session['user_id'] = user.id
    session['username'] = user.username
    
    return {'message': 'logged in'}

@app.route('/profile')
def profile():
    # Session retrieved from Redis, works on any server
    user_id = session.get('user_id')
    user = User.query.get(user_id)
    return jsonify(user.to_dict())

if __name__ == '__main__':
    app.run()
```

Architecture:

```
Client request → Load Balancer → Server A (may be any)
                                   ↓
                            Reads session from Redis
                                   ↓
                            Responds to client

Client's next request → Load Balancer → Server B (doesn't matter)
                                           ↓
                                    Reads session from Redis
                                           ↓
                                    Responds to client
```

## Health Checks (Knowing When Servers Are Down)

Load balancer must detect failed servers and stop routing to them.

### How Health Checks Work

```
Load Balancer (every 5 seconds):
  GET http://server1:5000/health → 200 OK (healthy)
  GET http://server2:5000/health → TIMEOUT (dead)
  GET http://server3:5000/health → 200 OK (healthy)

Route new requests only to servers 1 and 3
Keep trying server 2 (for recovery)
```

### Implementing Health Check Endpoint

```python
from flask import Flask

app = Flask(__name__)

@app.route('/health')
def health_check():
    try:
        # Check if database is reachable
        db.session.execute('SELECT 1')
        
        # Check if dependencies are reachable
        requests.get('http://redis:6379/', timeout=2)
        
        return {'status': 'healthy', 'database': 'ok'}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### Nginx Health Check Configuration

```nginx
upstream backend {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
    
    # Check health every 5 seconds
    zone backend_zone 64k;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}

# In HTTP block for status check
match health_check {
    status 200;
}

upstream backend_status {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
    
    check interval=5000 rise=2 fall=3 timeout=2000 type=http;
    check_http_send "GET /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}
```

## Failure Scenarios

### Scenario 1: Server Goes Down

```
Before:
  LB routes to: A (healthy), B (healthy), C (healthy)

Server C crashes
  
LB detects C is unhealthy (health check fails)
  
After:
  LB routes to: A, B
  Requests that were going to C are now distributed to A, B
  C is removed from pool
```

### Scenario 2: All Servers Down

```
All servers fail

LB has no healthy servers

Options:
1. Return 503 Service Unavailable
2. Route to last known server (stale)
3. Queue requests and wait for recovery
```

Flask example:

```python
@app.route('/')
def index():
    try:
        # Try to reach a dependency
        requests.get('http://db:5432', timeout=2)
        return {'data': 'normal response'}, 200
    except:
        # Dependency down, return 503
        return {'error': 'service unavailable'}, 503
```

### Scenario 3: Partial Failure (One Region Down)

```
Load Balancer in Region 1:
  Server A (health check ok)
  Server B (health check fails)

Requests queue up on Server A
Server A gets overloaded
Response time increases
More requests timeout

Solution: Have LB in multiple regions
Request to Region 1 LB that can fail over to Region 2 LB
```

## Nginx as Load Balancer

### Simple Configuration

```nginx
# /etc/nginx/nginx.conf

upstream backend {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 80;
    server_name api.example.com;
    
    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### With Health Checks

```nginx
upstream backend {
    least_conn;
    server 127.0.0.1:5001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5002 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5003 max_fails=3 fail_timeout=30s;
    
    # max_fails: disable server after 3 failed attempts
    # fail_timeout: disable for 30 seconds before retrying
}

server {
    listen 80;
    
    location / {
        proxy_pass http://backend;
        
        # Important headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Health check endpoint (expose LB status)
    location /lb-health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### With Rate Limiting

```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

upstream backend {
    least_conn;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    listen 80;
    
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend;
    }
}
```

## Common Mistakes

### Mistake 1: Lost Client IP

Without proper headers, backend sees LB IP, not client IP.

```nginx
# Wrong: No headers forwarded
location / {
    proxy_pass http://backend;
}

# Right: Pass client IP
location / {
    proxy_pass http://backend;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Backend code:

```python
from flask import request

@app.route('/user-ip')
def get_user_ip():
    # Wrong: Gets LB IP
    ip = request.remote_addr  # 127.0.0.1 (LB)
    
    # Right: Gets client IP
    ip = request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
    # or use trusted_hosts
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)
    ip = request.remote_addr  # Client's actual IP
    
    return {'your_ip': ip}
```

### Mistake 2: No Health Checks

Server dies, LB keeps routing to it.

```nginx
# Wrong: No health check
upstream backend {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

# Right: With health checks
upstream backend {
    server 127.0.0.1:5001 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:5002 max_fails=3 fail_timeout=30s;
}
```

### Mistake 3: Wrong Algorithm for Stateful Apps

```python
# Stateful app (stores session on server)
@app.before_request
def login_required():
    session_data = session.get('user_id')  # Stored locally
    if not session_data:
        return {'error': 'not authenticated'}, 401

# Wrong LB config: round-robin
# User logs into Server A (session stored on A)
# Next request goes to Server B (no session data)
# "not authenticated" error

# Right LB config: ip_hash or sticky sessions
upstream backend {
    ip_hash;  # Same client always → same server
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

# Best: Store sessions in Redis (stateless app)
app.config['SESSION_TYPE'] = 'redis'
```

### Mistake 4: Health Check Endpoint Too Heavy

```python
# Wrong: Health check does too much
@app.route('/health')
def health():
    db.session.query(User).count()  # Heavy query
    return {'status': 'ok'}

# Health checks every 5 seconds
# This query runs 100+ times per minute
# Wastes database connections

# Right: Lightweight health check
@app.route('/health')
def health():
    try:
        db.session.execute('SELECT 1')  # Lightweight
        return {'status': 'ok'}, 200
    except:
        return {'status': 'down'}, 503
```

## Production Notes

### 1. Multiple Load Balancers (HA)

Single LB is single point of failure:

```
        ┌────── LB 1 ──────┐
        │                  │
    Client                 Server 1
        │                  │
        └────── LB 2 ──────┘

Both LBs route to same servers
Client connects to either LB (via DNS round-robin or VIP)
```

### 2. Connection Draining (Graceful Shutdown)

When taking a server down, don't close active connections:

```nginx
upstream backend {
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
    server 127.0.0.1:5003;
}

server {
    location / {
        proxy_pass http://backend;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Process:

```
1. Mark server as "draining" (no new requests)
2. Let existing connections finish
3. After timeout, close remaining connections
4. Restart/update server
```

### 3. Metrics and Monitoring

```nginx
# In Nginx status module
location /lb-stats {
    stub_status on;
    access_log off;
}

# Output:
# active connections: 100
# server accepts handled requests
# 1000 1000 10000
# Reading: 10 Writing: 20 Waiting: 70
```

Backend monitoring:

```python
from prometheus_client import Counter, Histogram

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
        endpoint=request.endpoint
    ).inc()
    request_duration.observe(duration)
    return response

@app.route('/metrics')
def metrics():
    from prometheus_client import generate_latest
    return generate_latest()
```

---

## Module 5 Assessment

### Practice Questions (MCQ - No Answers Provided)

1. An L7 load balancer can route based on HTTP path, while L4 cannot. Why?
   a) L7 is more powerful
   b) L4 doesn't have CPU power to parse HTTP
   c) L4 operates at TCP layer before HTTP layer
   d) HTTP is not reliable

2. You have 3 equally powerful servers. Which algorithm distributes load fairest?
   a) Round-robin
   b) Least connections
   c) IP hash
   d) Weighted round-robin

3. User logs in → Server A (session stored locally). LB uses round-robin. Next request likely goes to:
   a) Always Server A
   b) Could be Server A, B, or C (random)
   c) Server B (next in round-robin)
   d) Whichever has least connections

4. Nginx health check on Server B fails 3 times. What happens?
   a) Server B is permanently disabled
   b) Server B is disabled for the configured timeout period
   c) New requests immediately start failing
   d) LB stops all requests

5. Backend server gets X-Real-IP: 10.0.0.1 but should get client's actual IP. Root cause?
   a) Client IP is hidden
   b) LB not forwarding X-Real-IP header
   c) Server IP is private
   d) HTTPS is encrypting IP

### Practical Networking Tasks

**Task 1: Set Up Load Balancing with Nginx**

- Create 3 simple Flask/FastAPI backends on ports 5001, 5002, 5003
- Each returns its own identifier: `{"server": "backend1"}`
- Configure Nginx as load balancer:
  - Round-robin algorithm
  - Health checks
  - Proper header forwarding
- Test with curl in a loop:
  ```bash
  for i in {1..10}; do curl http://localhost/; done
  ```
- Verify requests distribute across all 3 servers

**Task 2: Test Failure Scenarios**

- With the setup above:
  - Stop one backend server
  - Make requests - verify LB stops routing to dead server
  - Restart server - verify LB resumes routing to it
  - Monitor with:
    ```bash
    watch -n 1 'curl -s http://localhost/ && echo'
    ```

### Production Incident Scenario

**Incident**: Users report "sometimes logged out" errors. Investigation shows:

- Load balancer configured with round-robin
- User logs in successfully
- User makes next request → Different server (has no session data)
- App returns "not authenticated"
- User must log in again

Questions:

1. Why is this happening? (Describe the flow)
2. What's wrong with the current load balancing setup?
3. What are two ways to fix this?
4. If you choose sticky sessions, what header should LB use?
5. If you choose stateless sessions, where should session data live?

---

**Next**: [Module 6: Reverse Proxy (Nginx)](06-reverse-proxy-nginx.md)
