# Module 1: Networking Fundamentals

## What Networking Actually Solves

Before studying packets and protocols, understand the problem:

**Backend systems need to send messages to other computers.**

That's it. Everything else is a solution to one of these problems:

1. How do we find the right computer? (DNS, routing)
2. How do we send reliable messages? (TCP)
3. How do we send fast messages? (UDP)
4. How do we prevent eavesdropping? (TLS/SSL)
5. How do we prevent one service from overloading? (Load balancing)

Networking is about **moving data from Point A to Point B reliably, securely, and at scale**.

## The Backend Perspective

Your Flask app lives on a server with an IP address. A client (browser, mobile app, another service) wants to talk to it.

```
Your Flask App: 192.168.1.100:5000

Client wants to reach it:
1. Client asks DNS: "Where is example.com?"
2. DNS replies: "192.168.1.100"
3. Client connects to 192.168.1.100:5000
4. Client sends HTTP request
5. Your app processes it
6. App sends back response
```

Each step involves networking. Let's understand each layer.

## The OSI Model (Backend Engineer Edition)

The full OSI model has 7 layers. Backend engineers care about 4:

| Layer | Name | Your Job | Example |
|-------|------|----------|---------|
| 3 | Network | Understand | IP addresses, routing |
| 4 | Transport | Know well | TCP, UDP, ports |
| 5 | Session | Mostly ignore | Session management (app handles) |
| 7 | Application | Master | HTTP, WebSockets, gRPC |

Ignore layer 1-2 (physical/link) unless you're doing something weird with Docker networking.

## IP Addresses (Version 4)

An IP address identifies a computer on a network.

### IPv4 Basics

```
Format: 192.168.1.100
       [octet].[octet].[octet].[octet]

Each octet: 0-255 (8 bits)
```

### Common Ranges (Important for Backends)

```
0.0.0.0 - 255.255.255.255     Entire IPv4 space

127.0.0.1                      Localhost (your own machine)
127.0.0.2 - 127.255.255.255    Also localhost (loopback)

192.168.0.0 - 192.168.255.255  Private (home/office networks)
10.0.0.0 - 10.255.255.255      Private (corporate/cloud)
172.16.0.0 - 172.31.255.255    Private (Docker default)

224.0.0.0 - 239.255.255.255    Multicast (for broadcasting)
```

### Subnets (CIDR Notation)

CIDR tells you which part of an IP is the network and which is the host.

```
192.168.1.0/24

/24 means: first 24 bits are network, last 8 bits are host
          256 possible IPs (192.168.1.0 to 192.168.1.255)
          254 usable (exclude .0 and .255)

10.0.0.0/8

/8 means: first 8 bits are network, last 24 bits are host
         16,777,216 possible IPs
```

### Backend Use: Container Networking

```bash
# Docker containers get private IPs from the default subnet
docker run --name my-app busybox
docker inspect my-app | grep IPAddress

# Your app: 172.17.0.2
# Another container: 172.17.0.3
# They can talk directly (both on same subnet)
```

## Ports (Understanding Communication)

An IP address alone isn't enough. A server has many services running:

```
192.168.1.100:22    SSH
192.168.1.100:80    HTTP
192.168.1.100:5000  Flask app
192.168.1.100:5432  PostgreSQL
```

The **port** number (0-65535) identifies which service receives the message.

### Common Backend Ports

```
22      SSH (admin access)
53      DNS (name resolution)
80      HTTP (insecure web)
443     HTTPS (secure web)
5000    Flask default
8000    FastAPI/Gunicorn common
5432    PostgreSQL
6379    Redis
3306    MySQL
27017   MongoDB
```

### Port Ranges

```
0-1023      Privileged (need root/sudo to bind)
1024-49151  Registered (IANA assigned)
49152-65535 Dynamic/private (use for custom services)
```

### Backend Use: Binding Your Flask App

```python
# Flask app running on port 5000
from flask import Flask
app = Flask(__name__)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# Now accessible at:
# http://localhost:5000           (local machine)
# http://192.168.1.100:5000       (from network)
# http://app.example.com:5000     (with DNS)
```

Terminal verification:

```bash
# Check which port Flask is listening on
netstat -tlnp | grep LISTEN
# or newer syntax:
ss -tlnp | grep LISTEN

# Output shows:
# LISTEN 0.0.0.0:5000 (0.0.0.0 means listen on all interfaces)
```

## Sockets (The Operating System Abstraction)

A socket is your application's connection endpoint. It's how your code actually sends/receives data.

### Types of Sockets

```
AF_INET + SOCK_STREAM  = TCP socket (reliable, ordered)
AF_INET + SOCK_DGRAM   = UDP socket (fast, unreliable)
AF_UNIX                = Local socket (same machine only)
```

### Backend Use: Python Requests

```python
import socket
import requests

# When you do this:
response = requests.get('http://192.168.1.100:5000/api/users')

# Python library does internally:
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('192.168.1.100', 5000))
sock.sendall(b'GET /api/users HTTP/1.1\r\n...')
data = sock.recv(4096)
sock.close()
```

You don't create sockets directly in modern code, but understanding them helps debug connection issues.

### Creating Raw Sockets (Debugging)

```bash
# Connect to a service using netcat (creates a socket)
nc -zv 192.168.1.100 5000

# -z: scan mode (don't send data)
# -v: verbose (show if open/closed)

# Output: Connection to 192.168.1.100 5000 port [tcp/*] succeeded!
```

### Socket States

```bash
# View all sockets on your machine
ss -tan

# Common states:
LISTEN      = waiting for incoming connections (your Flask app)
ESTABLISHED = active connection in progress
TIME_WAIT   = connection closed, waiting before cleanup
CLOSE_WAIT  = peer closed, waiting for you to close
```

Real example:

```bash
$ ss -tan | grep 5000
LISTEN   0   128   0.0.0.0:5000   0.0.0.0:*
```

This shows Flask listening on port 5000, accepting 128 queued connections.

## TCP vs UDP: When to Care

### TCP (Transmission Control Protocol)

**Use for**: Everything in backends (HTTP, databases, SSH)

```
Guarantees:
✓ Data arrives
✓ Data arrives in order
✓ No duplicates
✗ Slower (acknowledgment overhead)

Connection-oriented:
Three-way handshake to establish connection
Four-way handshake to close
```

### TCP Handshake Visualized

```
Client                          Server
  |                               |
  | -- SYN (seq=100) ---------->  |
  |                               |
  |  <-- SYN-ACK (ack=101) ------ |
  |                               |
  | -- ACK (seq=101) ---------->  |
  |                               |
  | (connection established)      |
  |                               |
  | -- data ---------->           |
  |                               |
```

This is why TCP is slower: 3 packets before you send real data.

### UDP (User Datagram Protocol)

**Use for**: Real-time audio/video, DNS queries, gaming, monitoring

```
Characteristics:
✓ Fast (no handshake)
✗ No guarantee delivery
✗ No ordering guarantee
✗ Possible duplicates
```

**When backends use UDP:**

1. DNS queries (fast, one-off requests)
2. Streaming video to users
3. Monitoring metrics (some loss acceptable)

**Very rarely your main API protocol**

### Backend Use: When Does This Matter?

```python
# Your Flask app uses TCP automatically
from flask import Flask
app = Flask(__name__)

# Your database connection uses TCP
import psycopg2
conn = psycopg2.connect("dbname=mydb user=postgres")

# Even your Docker containers use TCP for HTTP
docker run my-api
# Listens on TCP port 5000
```

You rarely choose TCP vs UDP as a backend engineer. It's chosen for you by the protocol (HTTP=TCP, DNS=UDP).

## Port Forwarding (Local Development)

You have a Docker container or VM with your backend, but you're developing on your laptop.

```
Your Laptop          SSH tunnel      Container
Port 5000 ---------> Port 22 ------> Port 5000 Flask
```

### SSH Local Port Forward

```bash
# Forward local port 5000 to container port 5000 via SSH
ssh -L 5000:localhost:5000 user@backend-server

# Now on your laptop:
curl http://localhost:5000/api/health

# The request goes:
# Your curl -> SSH tunnel -> remote server:5000
```

### Docker Port Mapping

```bash
# Map container port 5000 to host port 8000
docker run -p 8000:5000 my-flask-app

# Access on your machine: http://localhost:8000
# But internally container is port 5000
```

## The Client-Server Model

Everything in backend networking follows this:

```
Client                                      Server
(initiates)                                (waits)

Wants data -----> Opens socket
                 Connects to Server:Port
                 Sends request
                              Server receives
                              Processes
                              Sends response
                 <---- Receives response
Close connection
```

**Key insight**: Server never initiates connection to client (usually). Client always initiates.

### Backend Example: Your Flask App

```
Flask App (Server):
  - Listens on 0.0.0.0:5000
  - Waits for client connections
  - Receives request
  - Processes
  - Sends response

Client (Browser):
  - Wants http://example.com/api/users
  - Creates socket
  - Connects to server
  - Sends HTTP GET request
  - Receives response
  - Closes connection
```

## Common Misconceptions

### Misconception 1: "Port 80 vs 443"

Wrong: "Port 443 is encrypted"

Right: "HTTPS uses TLS encryption, and port 443 is the convention for it"

```
You can:
- Run HTTP on port 443 (unusual, no encryption)
- Run HTTPS on port 80 (unusual, encrypted but everyone assumes it isn't)
```

The port number doesn't encrypt. The protocol does (TLS).

### Misconception 2: "Localhost is 127.0.0.1"

True, but incomplete: `localhost` resolves to 127.0.0.1 by convention.

```bash
# On most Linux machines:
grep localhost /etc/hosts
# 127.0.0.1   localhost

# But you can change it, or use 127.0.0.2
python3 -m http.server 8000 --bind 127.0.0.2

curl http://127.0.0.1:8000  # Won't work
curl http://127.0.0.2:8000  # Works
```

### Misconception 3: "0.0.0.0 is an address I can connect to"

Wrong: 0.0.0.0 means "listen on all interfaces" for servers

```python
# When you do this:
app.run(host='0.0.0.0', port=5000)

# It means: "Listen on all network interfaces"
# But clients CANNOT connect to 0.0.0.0:5000

# They connect to:
# - 127.0.0.1:5000 (localhost)
# - 192.168.1.100:5000 (actual IP)
# - app.example.com:5000 (domain name)
```

### Misconception 4: "Private IPs are less secure"

Wrong: Private IPs just mean "not routable on public internet"

```
10.0.0.0/8 (private)

Private doesn't mean unencrypted.
Private doesn't mean unauthenticated.

You can:
- Run unsecured HTTP on public IPs
- Run encrypted HTTPS on private IPs
```

Security is about TLS/authentication, not IP address privacy.

## Networks at Different Scales

### 1. Loopback (127.0.0.0/8)

```
Your laptop: 127.0.0.1
Your Flask: 127.0.0.1:5000

docker run my-app
can't reach localhost:5000
(Docker container is different network)
```

### 2. Docker Container Network

```
docker network create backend-net

Container A: 172.17.0.2
Container B: 172.17.0.3

Both on same /16 subnet
Can talk directly: curl http://172.17.0.3:5000
```

### 3. LAN (Local Area Network)

```
Your office/home network: 192.168.1.0/24

Laptop:     192.168.1.10
Server:     192.168.1.100
NAS:        192.168.1.200

All on same subnet
Can talk directly
```

### 4. WAN (Wide Area Network)

```
Your server: 203.0.113.45 (public IP)
Your laptop: (private IP behind ISP router)

Server needs public IP (routable on internet)
Your laptop hidden behind NAT (Network Address Translation)
```

## Routing: Getting Packets to the Right Network

Your machine decides how to send data based on routing tables:

```bash
# View routing table
route -n
# or
ip route show

# Output example:
# Destination     Gateway         Genmask         Iface
# 0.0.0.0         192.168.1.1     0.0.0.0         eth0
# 127.0.0.0       127.0.0.1       255.0.0.0       lo
# 192.168.1.0     0.0.0.0         255.255.255.0   eth0
```

This means:

```
Sending to 127.x.x.x?  Use loopback (lo) interface
Sending to 192.168.1.x? Use eth0 directly
Sending to anything else? Use gateway 192.168.1.1
```

### Backend Use: Docker Networks

```bash
# Docker containers get automatic routing
docker network create backend-net
docker run --network backend-net --name api myapi
docker run --network backend-net --name db mydb

# Inside api container:
# curl http://db:5432/
# Docker's network driver provides routing
```

## Firewalls (Blocking Unwanted Connections)

A firewall blocks traffic based on rules.

```bash
# View firewall status
sudo ufw status
# or
sudo firewall-cmd --list-all

# Allow port 80 (HTTP)
sudo ufw allow 80/tcp

# Deny port 3306 (MySQL) from external
sudo ufw allow 3306/tcp comment "MySQL" from 192.168.1.0/24
sudo ufw deny 3306/tcp

# Block everything except what's allowed
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### Backend Use: Securing Your Services

```bash
# Your production server
sudo ufw default deny incoming
sudo ufw allow 22/tcp      # SSH (admin)
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS

# Database only accessible from app servers
sudo ufw allow 5432/tcp from 10.0.1.0/24

# This prevents direct access to database from internet
```

## Network Interfaces

Your computer has one or more network interfaces.

```bash
# List all interfaces
ip link show
# or
ifconfig

# Output:
# lo       (loopback - localhost)
# eth0     (ethernet)
# docker0  (Docker bridge)
```

### Common Scenarios

```bash
# Laptop with WiFi
ip addr show
# wlan0 (WiFi adapter)
# lo    (loopback)

# Server in datacenter
ip addr show
# eth0 (primary network)
# eth1 (secondary network, maybe)
# lo   (loopback)

# Docker host
ip addr show
# eth0    (host network)
# docker0 (Docker bridge)
# veth... (virtual interfaces for containers)
```

### Backend Use: Binding to Specific Interface

```python
# Bind Flask to only localhost (security)
app.run(host='127.0.0.1', port=5000)

# Bind to all interfaces (for Docker)
app.run(host='0.0.0.0', port=5000)

# Bind to specific interface
app.run(host='192.168.1.100', port=5000)
```

## Summary: What You Need to Remember

| Concept | Why It Matters | For Backend Engineers |
|---------|----------------|----------------------|
| IP Address | Identifies a computer | Know how Docker/Kubernetes assign IPs |
| Port | Identifies a service | Bind your app to correct port |
| TCP | Reliable delivery | Your protocols use it (HTTP, databases) |
| UDP | Fast, unreliable | DNS uses it, rarely your concern |
| Socket | Connection endpoint | Understand for debugging, high-level code abstracts it |
| Subnet/CIDR | Groups of IPs | Important for container networking |
| Routing | Packets reach destination | Docker/K8s handle it, know it exists |
| Firewall | Blocks unwanted traffic | Essential for production security |
| Port Forwarding | Access remote services | Development technique |

## What's Next

You understand the networking foundation. In Module 2, you'll see how applications actually use these concepts through HTTP and HTTPS.

---

## Module 1 Assessment

### Practice Questions (MCQ - No Answers Provided)

1. You run a Flask app with `app.run(host='0.0.0.0', port=5000)`. A client tries to connect to `0.0.0.0:5000`. What happens?
   a) Connection succeeds
   b) Connection fails, can't route to 0.0.0.0
   c) Flask accepts connection if client is on same network
   d) Depends on firewall settings

2. Your Docker container has IP `172.17.0.2` and your host machine is `192.168.1.100`. The container tries to reach `192.168.1.100:3306`. What does it depend on?
   a) Nothing, containers always have network access
   b) Host network configuration and firewall rules
   c) Docker daemon permissions
   d) The container being in privileged mode

3. Which port number requires root/sudo to bind a listening service?
   a) 1024
   b) 65535
   c) 8000
   d) 49152

4. TCP takes longer than UDP because:
   a) TCP uses encryption
   b) TCP has handshake overhead for reliability
   c) TCP packets are larger
   d) TCP is deprecated

5. A backend engineer sees "TIME_WAIT" sockets on their server using `ss -tan`. This most likely means:
   a) Connections are stalled
   b) Server is not responding
   c) Recent connections closed normally, waiting for cleanup
   d) Network is misconfigured

### Practical Networking Tasks

**Task 1: Verify Port Listening**

- Start a simple Python HTTP server: `python3 -m http.server 8080`
- In another terminal, check what ports are listening: `ss -tlnp`
- Identify which process is listening on 8080
- Try connecting: `curl http://localhost:8080`
- Bonus: From another machine on your network, try `curl http://<your-ip>:8080`
- Document what works and what doesn't

**Task 2: Docker Port Mapping**

- Run a Docker container with Flask/FastAPI on port 5000 internally
- Map it to port 9000 on your host: `docker run -p 9000:5000 <image>`
- Verify it's reachable: `curl http://localhost:9000`
- Check the routing with `docker network inspect bridge`
- Stop the container and verify the port is released

### Production Incident Scenario

**Incident**: Your Flask app is running, you can reach it from localhost, but other machines on the network can't reach it.

```
Your machine:      192.168.1.10
Flask app:         Bound to 127.0.0.1:5000
Another machine:   192.168.1.20
They try:          curl http://192.168.1.10:5000
Result:            Cannot connect
```

Questions:

1. What's the root cause? (Hint: look at the IP Flask is bound to)
2. What command would you run to verify the binding?
3. How would you fix it?
4. After fixing, what would you verify to ensure it works?
5. Why does localhost work but 192.168.1.10 doesn't?

---

**Next**: [Module 2: HTTP/HTTPS Protocol](02-http-https-protocol.md)
