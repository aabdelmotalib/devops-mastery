# Module 5: Docker Networking

## Container Networking Fundamentals

Containers need to communicate: with each other, with the host, with external services. Docker provides networking to enable this.

### Default Behavior: Network Namespace Isolation

Each container has its own network namespace, isolated from:
- The host's network
- Other containers (by default)
- External services (needs port mapping)

```bash
# Container has isolated IP
docker run ubuntu hostname -I
# Returns: 172.17.0.2 (internal IP, not on host network)

# Host doesn't see this IP
ifconfig
# Only shows host IPs, not 172.17.0.2

# Container can't access host by host's IP
docker run ubuntu ping 192.168.1.10  # Host IP
# Times out (can't reach it)
```

### Network Drivers

Docker uses different drivers for different network types:

- **bridge**: Default, isolated containers connected to docker0 bridge
- **host**: Container uses host's network directly
- **overlay**: For swarm, containers across hosts
- **macvlan**: Container appears as physical device on network
- **none**: No networking

## Default Bridge Network

When you run a container without specifying a network, it uses the default `bridge`.

```
Container A         Container B         Container C
IP: 172.17.0.2      IP: 172.17.0.3      IP: 172.17.0.4
  │                   │                   │
  └───────────────────┼───────────────────┘
                      │
                  docker0 bridge
                  IP: 172.17.0.1
                      │
                 Host eth0
              (192.168.1.10)
                      │
                   External
                   Network
```

### Bridge Network Characteristics

```bash
# View default bridge
docker network inspect bridge

# Output shows:
# "Name": "bridge"
# "Driver": "bridge"
# "Containers": { "container-id": { "IPv4Address": "172.17.0.2" } }
```

**Limitations of default bridge:**
- No DNS resolution between containers (must use IP)
- No network aliases
- Limited control

```bash
# Two containers on default bridge
docker run -d --name app1 ubuntu sleep 1000
docker run -d --name app2 ubuntu sleep 1000

# app2 cannot resolve app1 by name
docker exec app2 ping app1
# ping: unknown host app1 (FAILS)

# Must use IP
docker inspect -f '{{.NetworkSettings.IPAddress}}' app1
# 172.17.0.2

docker exec app2 ping 172.17.0.2
# Works (uses IP)
```

## User-Defined Networks

Create custom networks with better features.

```bash
# Create bridge network
docker network create mynet

# Run containers on it
docker run -d --network mynet --name app1 ubuntu sleep 1000
docker run -d --network mynet --name app2 ubuntu sleep 1000

# Now DNS works!
docker exec app2 ping app1
# Works! Docker provides DNS resolution
```

### User-Defined vs Default Bridge

| Feature | Default Bridge | User-Defined |
|---------|---------------|--------------|
| DNS | IP only | Hostname resolution |
| Aliases | No | Yes |
| Isolation | Shared | Separate |
| Control | Limited | Full |
| Production | Avoid | Recommended |

**Why user-defined networks are better:**
```bash
# User-defined: containers discover each other automatically
docker network create production
docker run --network production --name db ubuntu sleep 1000
docker run --network production --name api ubuntu sleep 1000

# Inside api:
docker exec api ping db
# Works without knowing db's IP

# Default bridge: need to manage IPs
docker run --name db ubuntu sleep 1000
docker run --link db:db --name api ubuntu sleep 1000
# Must use --link (deprecated)
```

## Port Mapping: Accessing Container Services

Containers listen on their internal IP. Port mapping exposes them to the host.

```
Host (192.168.1.10)
    │
    └─── port 8080
         │
         └─ (internal mapping)
            │
            └─ Container (172.17.0.2:8000)
```

### Syntax: Host Port → Container Port

```bash
# Map host 8080 to container 8000
docker run -p 8080:8000 ubuntu nc -l 8000
# Host can access: curl localhost:8080
# Container listens on: 0.0.0.0:8000 (all interfaces)

# Map specific host interface
docker run -p 192.168.1.10:8080:8000 ubuntu nc -l 8000
# Only accessible from 192.168.1.10

# Map multiple ports
docker run -p 8080:8000 -p 9000:9000 ubuntu nc -l 8000

# Dynamic port mapping (OS chooses host port)
docker run -p 8000 ubuntu nc -l 8000
# docker ps shows: 0.0.0.0:random_port->8000/tcp

# UDP port
docker run -p 5353:53/udp ubuntu nc -ul 53
```

### How Port Mapping Works

```bash
# Inside container, process listens on port 8000
docker run -d -p 8080:8000 --name web ubuntu nc -l 8000

# Host has iptables rule that forwards traffic
sudo iptables -t nat -L -n | grep 8080
# Shows NAT rule: 0.0.0.0:8080 -> 172.17.0.x:8000

# Traffic flow:
# Host receives: curl localhost:8080
# iptables NAT: converts to 172.17.0.x:8000
# Container receives on 8000
# Response reversed through same NAT

# This is why containers must listen on 0.0.0.0, not just 127.0.0.1
# If container listens only on 127.0.0.1:8000, port mapping fails
```

### Common Mistake: Binding to localhost

```dockerfile
# BAD: Binds only to 127.0.0.1
FROM python:3.11
RUN echo 'from http.server import HTTPServer, BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
    def do_GET(self): 
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")
HTTPServer(("127.0.0.1", 8000), Handler).serve_forever()' > /app/server.py

CMD ["python3", "/app/server.py"]
```

```bash
docker run -p 8080:8000 badimage
# Port mapping fails - container only listens on 127.0.0.1:8000
# External connections can't reach it

# GOOD: Binds to all interfaces
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
# Now port mapping works
```

## Host Network

Container uses host's network directly (no isolation).

```bash
docker run --network host ubuntu hostname -I
# Shows host's IP, not container IP

docker run --network host -p 8080:8000 ubuntu nc -l 8000
# No port mapping needed, port 8000 is directly on host
# Dangerous if multiple containers use same port
```

**When to use host network:**
- Performance-critical applications (no bridge overhead)
- Tools that need raw network access
- Rare in practice

**Limitations:**
- Containers can conflict on ports
- No network isolation
- Different IPs on different hosts (not portable)

```bash
# Host network is not portable
docker run --network host ubuntu hostname -I
# Shows one IP on this host

# On different host:
docker run --network host ubuntu hostname -I
# Shows different IP (breaks distributed systems)
```

## Container DNS

Containers need to resolve hostnames (external services, other containers).

### DNS Configuration

```bash
# Default DNS (from host's /etc/resolv.conf)
docker run ubuntu cat /etc/resolv.conf
# Shows nameservers

# Custom DNS
docker run --dns 8.8.8.8 ubuntu cat /etc/resolv.conf
# Uses Google's DNS

# Multiple DNS servers
docker run --dns 8.8.8.8 --dns 1.1.1.1 ubuntu nslookup google.com
```

### Container-to-Container DNS (User-Defined Networks)

Docker provides built-in DNS for user-defined networks.

```bash
# Create network
docker network create app-net

# Run database container
docker run -d --network app-net --name database ubuntu sleep 1000

# Run app container
docker run -d --network app-net --name app ubuntu sleep 1000

# Inside app, can resolve database
docker exec app nslookup database
# Returns database's IP

# This is how Docker enables service discovery
# Containers find each other by name
```

**How it works:**
```bash
# When container starts on user-defined network:
# 1. Docker registers its name with DNS
# 2. Docker's embedded DNS server resolves names
# 3. Default nameserver in /etc/resolv.conf points to Docker daemon
docker exec app cat /etc/resolv.conf
# Shows: nameserver 127.0.0.11:53
# (Docker's embedded DNS server)
```

## Network Connectivity: Practical Examples

### Two Containers Communicating

```bash
# Create network
docker network create backend

# Start database
docker run -d \
  --network backend \
  --name postgres \
  ubuntu nc -l 5432

# Start application
docker run -d \
  --network backend \
  --name api \
  ubuntu sleep 1000

# From api, connect to postgres
docker exec api nc postgres 5432
# Works! Can resolve postgres by name and connect

# If using default bridge, would need:
docker run -d --name postgres ubuntu nc -l 5432
docker run -d --link postgres ubuntu \
  bash -c 'nc postgres 5432'
# More complex, deprecated
```

### Exposing to External Network

```bash
# Container serves HTTP internally
docker run -d \
  --network backend \
  --name web \
  ubuntu nc -l 8000

# Map port to host
docker run -d \
  --network backend \
  --name web \
  -p 8080:8000 \
  ubuntu nc -l 8000

# External clients access via host port
curl localhost:8080
# Reaches container on 8000

# Inside container, still only knows port 8000
docker exec web netstat -tlnp
# Shows: LISTEN :::8000
```

## Network Troubleshooting

### Common Failures

**Container can't reach another container by name:**
```bash
docker run --name app1 ubuntu sleep 1000
docker run --name app2 ubuntu bash -c 'ping app1'
# ping: unknown host app1

# Solution: Use user-defined network
docker network create mynet
docker run --network mynet --name app1 ubuntu sleep 1000
docker run --network mynet --name app2 ubuntu bash -c 'ping app1'
# Works
```

**Container can't reach external network:**
```bash
docker run ubuntu ping 8.8.8.8
# Times out

# Debugging:
docker run ubuntu ip route
# Shows: default via 172.17.0.1

docker run ubuntu ping 172.17.0.1
# Can reach gateway

# Problem: likely host firewall blocking
# Solution: check host firewall rules, or verify connectivity works

# Inside container, DNS might fail
docker run ubuntu ping google.com
# Can't resolve google.com

# Check DNS
docker run ubuntu cat /etc/resolv.conf
docker run ubuntu nslookup google.com
# Verify nameserver is accessible
```

**Container can't expose port:**
```bash
docker run -p 8080:8000 ubuntu nc -l 8000
# Port mapping fails: Address already in use

# Debugging:
sudo netstat -tlnp | grep 8080
# Shows what's using port 8080

# Solution: Use different port or kill process
docker run -p 8081:8000 ubuntu nc -l 8000
```

### Debugging Tools

```bash
# Inspect network
docker network inspect mynet
# Shows all containers on network and their IPs

# Check container's network from inside
docker exec myapp ip addr show
docker exec myapp ip route show
docker exec myapp iptables -L
docker exec myapp iptables -t nat -L

# Network stats
docker exec myapp ifconfig
docker exec myapp netstat -tlnp
docker exec myapp ss -tlnp

# From host
docker inspect -f '{{.NetworkSettings}}' myapp
# Shows detailed network info
```

## Production Networking Patterns

### Service Discovery

```docker-compose
version: '3'
services:
  database:
    image: postgres
    networks:
      - backend
  api:
    image: myapi
    depends_on:
      - database
    environment:
      DATABASE_URL: postgresql://database:5432/mydb
    networks:
      - backend
  reverse-proxy:
    image: nginx
    ports:
      - "80:80"
    networks:
      - frontend
      - backend

networks:
  frontend:
  backend:
```

Key points:
- Containers discover each other by name
- Environment variables pass connection strings
- Networks can be separate (frontend vs backend)
- Port exposure happens at reverse proxy

### Network Separation

```bash
# Create front-end network (exposed)
docker network create frontend

# Create back-end network (internal)
docker network create backend

# Database only on backend
docker run --network backend --name db postgres

# API on both networks (bridges them)
docker run --network backend --network frontend --name api myapi

# Reverse proxy only on frontend
docker run --network frontend -p 80:80 nginx

# External traffic: external -> nginx:80 -> api -> db:5432
# API can reach both: frontend (nginx) and backend (db)
# Database isolated from external access
```

---

## Practice: Exam Questions

1. **What is the primary limitation of the default bridge network?**
   - A) It's slower than user-defined networks
   - B) Containers can't communicate at all
   - C) DNS resolution between containers doesn't work
   - D) It doesn't support port mapping

2. **In the command `docker run -p 8080:8000 myimage`, which port is on the host?**
   - A) 8000
   - B) 8080
   - C) Both
   - D) Neither

3. **What does Docker's embedded DNS server do on user-defined networks?**
   - A) Routes all traffic to a central DNS
   - B) Resolves container names to their IPs
   - C) Provides encryption for DNS queries
   - D) Creates domain names for containers

4. **Why should a containerized web server listen on 0.0.0.0 instead of 127.0.0.1?**
   - A) It's faster
   - B) 127.0.0.1 doesn't exist in containers
   - C) Port mapping relies on listening on all interfaces
   - D) 0.0.0.0 is more secure

5. **What network driver should you use for a production application?**
   - A) Default bridge (always)
   - B) Host network (always)
   - C) User-defined bridge (usually)
   - D) Overlay (only for multi-host)

---

## Hands-On Labs

### Lab 1: User-Defined Networks and Service Discovery

**Objective:** Experience automatic service discovery.

```bash
# Create custom network
docker network create lab-net

# Run MySQL container
docker run -d \
  --network lab-net \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=password \
  --health-cmd="mysqladmin ping -u root -ppassword" \
  mysql:8.0

# Run application that connects to MySQL
docker run -d \
  --network lab-net \
  --name webapp \
  -e DB_HOST=mysql \
  -e DB_USER=root \
  -e DB_PASS=password \
  ubuntu sleep 1000

# Inside webapp, verify connectivity
docker exec webapp cat /etc/hosts
# Note: no entry for mysql (not in /etc/hosts)

docker exec webapp nslookup mysql
# Resolves to mysql's IP (via Docker's DNS)

docker exec webapp nc -zv mysql 3306
# Connects to mysql on port 3306

# Inspect network
docker network inspect lab-net
# Shows both containers with their IPs

# Clean up
docker stop mysql webapp
docker network rm lab-net
```

**What you're observing:**
- Containers on user-defined network can resolve each other by name
- DNS resolution is handled by Docker's embedded server
- No /etc/hosts entries needed

### Lab 2: Port Mapping and Exposure

**Objective:** Understand port mapping mechanics.

```bash
# Create simple HTTP server
cat > server.py << 'EOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Hello from container")
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
EOF

# Dockerfile
cat > Dockerfile.web << 'EOF'
FROM python:3.11-slim
COPY server.py /app/
WORKDIR /app
CMD ["python3", "server.py"]
EOF

# Build
docker build -t web-server:1.0 -f Dockerfile.web .

# Run with port mapping
docker run -d --name web -p 8080:8000 web-server:1.0

# Access from host
curl localhost:8080
# Returns: Hello from container

# View port mapping
docker port web
# Shows: 8000/tcp -> 0.0.0.0:8080

# Inside container, it still listens on 8000
docker exec web netstat -tlnp
# Shows: 0.0.0.0:8000

# Without port mapping, can't reach from host
docker run -d --name web2 web-server:1.0

docker exec web2 netstat -tlnp
# Shows: 0.0.0.0:8000

curl localhost:8000
# Fails (no port mapping)

# Clean up
docker stop web web2
docker rm web web2
```

**What you're observing:**
- Port mapping creates host-accessible port
- Container still listens on internal port
- Without mapping, port is inaccessible from host

---

## Failure Scenario: DNS Doesn't Resolve in Production

**Scenario:**
Your containerized application works perfectly in docker-compose locally, but fails in production when run individually. Error: "Can't resolve database hostname"

**Debugging:**
```bash
# Local (docker-compose): works
docker-compose up

# Production (manual docker run): fails
docker run myapp
# Error: Can't resolve database.default.svc.cluster.local

# Check DNS in container
docker exec myapp cat /etc/resolv.conf
# nameserver 127.0.0.11:53 (Docker embedded DNS)

docker exec myapp nslookup database
# NXDOMAIN error
```

**Root cause:**
In docker-compose, containers are on a custom network (service discovery works). In production, you're using default bridge network (no DNS resolution).

**Solution:**
```bash
# Option 1: Use custom network
docker network create prod-net

docker run --network prod-net --name database mydb
docker run --network prod-net --name app \
  -e DATABASE_HOST=database \
  myapp

# Option 2: Use --link (deprecated, but works)
docker run --name database mydb
docker run --link database --name app myapp

# Option 3: Pass IP explicitly
docker run --name database mydb
docker inspect -f '{{.NetworkSettings.IPAddress}}' database
# 172.17.0.2

docker run -e DATABASE_HOST=172.17.0.2 myapp
# Works, but fragile (IP changes if container restarts)
```

**Prevention:**
Always use custom networks for multi-container applications. Never rely on default bridge for production.

---

Next: [Module 6: Docker Volumes & Storage](06-docker-volumes-storage.md)
