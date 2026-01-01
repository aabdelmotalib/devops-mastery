# Getting Started with Networking Essentials Tutorial

## Quick Start (5 minutes)

### 1. Read the Tutorial

Start with the README and then each module in order:

```bash
# Start here
cat README.md

# Then Module 1
less docs/01-networking-fundamentals.md

# Continue through all 9 modules
# Each module is self-contained but builds on previous concepts
```

### 2. Run the Examples

Set up the complete system with Docker Compose:

```bash
cd examples

# Generate self-signed certificate for testing
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj "/CN=localhost"

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f
```

### 3. Test the API

```bash
# Get products
curl http://localhost/api/v1/products

# Create product (requires login first)
# 1. Login
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}' | jq -r '.access_token')

# 2. Create product
curl -X POST http://localhost/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Laptop", "price": 999.99, "inventory": 10}'

# List products
curl http://localhost/api/v1/products?page=1&limit=10
```

## Detailed Setup

### Prerequisites

- Docker & Docker Compose installed
- curl for testing
- A Linux/Mac terminal (or WSL2 on Windows)
- ~2GB RAM available

### Installation Steps

#### 1. Get the Repository

```bash
# If cloned
cd networking-essentials-tutorial

# Or just use the directory structure as-is
```

#### 2. Set Up Self-Signed Certificate (for local testing)

```bash
cd examples

# Generate certificate valid for 365 days
mkdir -p certs
openssl req -x509 -newkey rsa:2048 \
  -keyout certs/key.pem \
  -out certs/cert.pem \
  -days 365 -nodes \
  -subj "/CN=localhost"

# Verify certificate
openssl x509 -in certs/cert.pem -text -noout
```

#### 3. Start All Services

```bash
# From examples directory
docker-compose up -d

# Wait for services to be healthy (~30 seconds)
docker-compose ps

# Check backend service health
docker-compose logs app1 | grep "health"
```

#### 4. Verify Setup

```bash
# Check Nginx is running
curl -k https://localhost/lb-health

# Check backend is responding
curl -s http://localhost/api/v1/products | jq .

# Check database connection
docker-compose exec app1 curl http://localhost:5001/health
```

### Running Individual Modules

#### Module 1: Networking Fundamentals

```bash
# Understand ports
ss -tan | grep LISTEN

# Docker container networking
docker network inspect bridge | grep Containers

# Verify each backend on different port
for port in 5001 5002 5003 5004; do
  echo "Port $port:"
  curl -s http://localhost:$port/health
done
```

#### Module 2: HTTP/HTTPS

```bash
# Test HTTP methods
curl -X GET http://localhost/api/v1/products
curl -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}'

# Inspect response headers
curl -i http://localhost/api/v1/products

# Test HTTPS (ignore self-signed)
curl -k -i https://localhost/api/v1/products
```

#### Module 3: REST API Design

```bash
# Create resource
TOKEN=$(curl -s -X POST http://localhost/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "password123"}' | jq -r '.access_token')

# POST (create)
curl -X POST http://localhost/api/v1/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Mouse", "price": 29.99}'

# PATCH (update)
curl -X PATCH http://localhost/api/v1/products/1 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"price": 34.99}'

# DELETE
curl -X DELETE http://localhost/api/v1/products/1 \
  -H "Authorization: Bearer $TOKEN"
```

#### Module 4: WebSockets

WebSocket support shown conceptually. To test with live WebSocket:

```bash
# Install websocat
cargo install websocat

# Or use Python
python3 -c "
import websocket
ws = websocket.create_connection('ws://localhost/ws')
ws.send('hello')
print(ws.recv())
"
```

#### Module 5: Load Balancing

```bash
# Test round-robin load balancing
# Send requests, check which instance handles them
for i in {1..10}; do
  curl -s http://localhost/api/v1/health | jq '.instance_id'
done

# Should see different instance IDs

# Test server failure handling
docker-compose stop app1

# Requests still work (routed to other servers)
curl -s http://localhost/api/v1/products

# Restart
docker-compose start app1
```

#### Module 6: Reverse Proxy (Nginx)

```bash
# Test caching
curl -i http://localhost/api/v1/products | grep X-Cache-Status
# First request: MISS
# Second request: HIT (same within 5 minutes)

# Test rate limiting
for i in {1..150}; do
  curl -s http://localhost/api/v1/products > /dev/null
done
# Should see some return 429 (Too Many Requests)

# Check Nginx status
curl http://127.0.0.1:8080/nginx_status
```

#### Module 7: DNS

```bash
# Check what IP Docker resolved
docker-compose exec app1 nslookup postgres

# Check service names
docker-compose exec app1 getent hosts redis

# Simulate DNS change
docker-compose exec app1 ping postgres
```

#### Module 8: SSL/TLS

```bash
# View certificate details
openssl x509 -in examples/certs/cert.pem -text -noout

# Test HTTPS connection
curl -k -v https://localhost/api/v1/products

# Check certificate chain
openssl s_client -connect localhost:443 < /dev/null

# Verify HSTS header
curl -k -i https://localhost/ | grep Strict-Transport
```

#### Module 9: Final Project

This entire setup IS the final project! 

All components are included:
- ✓ Domain with DNS (Docker service names)
- ✓ HTTPS with TLS (nginx with self-signed cert)
- ✓ Reverse Proxy (nginx load balancing)
- ✓ Load-balanced backend services (4 Flask instances)
- ✓ Secure API exposure (rate limiting, auth)
- ✓ Monitoring (health checks, logs)

## Understanding the Architecture

```
Request Flow:

Client → DNS ("where is example.com?") → 127.0.0.1:80/443
           ↓
       Nginx Load Balancer
       - TLS Termination
       - Routing
       - Rate Limiting
       - Caching
           ↓
       ┌───┬───┬───┬───┐
       ↓   ↓   ↓   ↓
      App1 App2 App3 App4  (Flask instances)
       ↓   ↓   ↓   ↓
       └───┴───┴───┴───┘
           ↓
       PostgreSQL Database
       Redis Cache
```

## Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs nginx
docker-compose logs app1

# Rebuild containers
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Port already in use

```bash
# Find what's using port 80
lsof -i :80

# Kill process or use different port
# Edit docker-compose.yml and change port mapping
```

### Backend not responding

```bash
# Check backend is healthy
docker-compose exec app1 curl http://localhost:5001/health

# Check database connection
docker-compose exec postgres psql -U app -d appdb -c "SELECT 1"

# Check logs
docker-compose logs app1 | tail -50
```

### HTTPS certificate error

```bash
# Certificate is self-signed, so browsers warn
# Add exception or use --insecure with curl

# For production, use Let's Encrypt
# See Module 8 for details
```

## Next Steps

1. **Complete all 9 modules** - Each builds on previous knowledge
2. **Run the examples** - Hands-on learning is more effective
3. **Modify the code** - Try changing API endpoints, add features
4. **Deploy to production** - Use real certificate, configure firewall, monitor logs
5. **Study the configurations** - Understand every line in nginx.conf
6. **Build your own** - Create your own service from scratch

## Learning Path

```
Start Here ↓
Documentation (README.md)
    ↓
Module 1: Fundamentals (IP, ports, TCP)
    ↓
Module 2: HTTP/HTTPS (protocols)
    ↓
Module 3: REST API (endpoints)
    ↓
Module 4: WebSockets (real-time)
    ↓
Module 5: Load Balancing (distribution)
    ↓
Module 6: Reverse Proxy (Nginx)
    ↓
Module 7: DNS (domains)
    ↓
Module 8: TLS Certificates (security)
    ↓
Module 9: Final Project (integration)
    ↓
Build Your Own System
```

## Resources

- **Official Documentation**: Nginx, Flask, Docker
- **Tools**: curl, dig, netstat, tcpdump
- **Online**: MDN HTTP docs, RFC specifications
- **Quick Reference**: See examples/QUICK_REFERENCE.md

## Support

If something doesn't work:

1. Check logs: `docker-compose logs`
2. Test connectivity: `curl http://localhost/api/v1/health`
3. Verify configuration: Read the Nginx config
4. Rebuild: `docker-compose down -v && docker-compose up`

## Remember

> "Networks are just how computers talk to each other."

Everything you're learning is about facilitating that communication reliably, securely, and efficiently.

Good luck! 🚀
