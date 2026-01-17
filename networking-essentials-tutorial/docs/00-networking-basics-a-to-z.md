# Networking Basics: A-to-Z Premodule

**Duration:** 2-3 hours | **Level:** Beginner | **Prerequisites:** None

> **What This Module Is:** A complete A-to-Z introduction to networking concepts for backend engineers. If you're completely new to networking or need a refresher, start here before Module 1.

## Table of Contents (A-Z)

- [A: Addressing & IP](#a-addressing--ip)
- [B: Bandwidth & Bytes](#b-bandwidth--bytes)
- [C: Clients & Connections](#c-clients--connections)
- [D: Datagrams & DNS](#d-datagrams--dns)
- [E: Ethernet & Encapsulation](#e-ethernet--encapsulation)
- [F: Firewalls & Flow](#f-firewalls--flow)
- [G: Gateways & Routing](#g-gateways--routing)
- [H: Headers & Hops](#h-headers--hops)
- [I: Internet & Interfaces](#i-internet--interfaces)
- [J: Jumbo Frames (Jumbograms)](#j-jumbo-frames-jumbograms)
- [K: Keyed Sockets (Keying)](#k-keyed-sockets-keying)
- [L: Latency & Layers](#l-latency--layers)
- [M: MAC & Multiplexing](#m-mac--multiplexing)
- [N: Networks & Namespaces](#n-networks--namespaces)
- [O: Open Systems & OSI Model](#o-open-systems--osi-model)
- [P: Ports & Protocols](#p-ports--protocols)
- [Q: QoS & Queue](#q-qos--queue)
- [R: Routing & Requests](#r-routing--requests)
- [S: Sockets & Servers](#s-sockets--servers)
- [T: TCP/IP & Transport](#t-tcpip--transport)
- [U: UDP & User Data](#u-udp--user-data)
- [V: Virtual & VLAN](#v-virtual--vlan)
- [W: Wireshark & Web](#w-wireshark--web)
- [X: X.509 (Certificates)](#x-x509-certificates)
- [Y: Yet Another Protocol (Standards)](#y-yet-another-protocol-standards)
- [Z: Zero-Knowledge (Security Basics)](#z-zero-knowledge-security-basics)

---

## A: Addressing & IP

### IPv4 Addresses

An IPv4 address is a 32-bit number written as 4 decimal numbers (0-255) separated by dots.

```
192.168.1.1
  ↑   ↑  ↑  ↑
  |   |  |  └── Host (0-255)
  |   |  └───── Subnet (0-255)
  |   └──────── Network (0-255)
  └──────────── Class (0-255)
```

**Public vs Private:**
- **Public IPs:** Routable on the internet (e.g., 8.8.8.8)
- **Private IPs:** Not routable (only within local networks)
  - 10.0.0.0 - 10.255.255.255
  - 172.16.0.0 - 172.31.255.255
  - 192.168.0.0 - 192.168.255.255

### IPv6 Addresses

Modern replacement for IPv4. 128-bit address written in hexadecimal.

```
2001:0db8:85a3:0000:0000:8a2e:0370:7334
```

**Why it matters for backends:** Your server likely has both IPv4 and IPv6. Most apps still use IPv4.

```bash
# See your machine's addresses
ip addr show

# Output:
# 2: eth0: ...
#     inet 192.168.1.100/24 scope global
#     inet6 fe80::1/64 scope link
```

### CIDR Notation

Shorthand for IP ranges. `/24` means "first 24 bits are the network, last 8 bits are hosts."

```
192.168.1.0/24 = all IPs from 192.168.1.0 to 192.168.1.255
10.0.0.0/8 = all IPs from 10.0.0.0 to 10.255.255.255
172.16.0.0/12 = all IPs from 172.16.0.0 to 172.31.255.255
```

**Why this matters:** VPCs, subnets, and firewall rules use CIDR notation.

---

## B: Bandwidth & Bytes

### Bandwidth

The maximum data rate a connection can handle.

```
1 Mbps (megabit/second) = 1,000,000 bits/second = 125 KB/second
1 Gbps = 1,000 Mbps = 125 MB/second
```

### Throughput

Actual data transferred (always less than bandwidth due to overhead).

### Latency

Time for data to travel from A to B (measured in milliseconds or microseconds).

```
Localhost: < 1 ms
Same data center: 1-5 ms
Same region (AWS): 5-50 ms
Across continents: 100-300 ms
```

### Practical Example for Backend

```
If you call an API across the world:
- Latency adds 150 ms (one-way)
- 300 KB response / 50 Mbps bandwidth = 48 ms transfer
- Total: ~150 + 48 = 200+ ms before your backend gets the response
```

---

## C: Clients & Connections

### Clients

Any device initiating a network request (your web browser, mobile app, or another backend service).

```
Your Flask Server Perspective:
- A client connects to your server
- Sends: GET /api/users HTTP/1.1
- Receives: 200 OK with JSON
- Connection closes (or stays open for HTTP/1.1 keep-alive)
```

### Connection States

```
CLOSED → SYN_SENT (client sends) → SYN_RECEIVED (server receives)
→ ESTABLISHED (both sides ready) → FIN_WAIT/CLOSE_WAIT (closing)
→ CLOSED
```

### Connection Limits

Every server has limits:

```bash
# Check max open files (connections)
ulimit -n
# Output: 1024 (on many Linux systems)

# See current connections
netstat -an | grep ESTABLISHED | wc -l
```

**Why this matters:** If you have 10,000 users, you need more than 1024 file descriptors.

---

## D: Datagrams & DNS

### Datagrams

Individual packets of data (used by UDP). Unlike TCP, they're sent independently and may arrive out of order or not at all.

```
UDP Datagram = Header (8 bytes) + Payload (up to 65,527 bytes)
```

### DNS (Domain Name System)

Translates human-readable names to IP addresses.

```
www.example.com → 93.184.216.34
```

**DNS Query Process:**
```
1. Browser: "What IP is example.com?"
2. Resolver (ISP): "Let me ask root nameserver"
3. Root: "Ask TLD server for .com"
4. TLD: "Ask authoritative nameserver for example.com"
5. Authoritative: "93.184.216.34"
6. Browser gets IP and connects
```

**Common DNS Records:**

| Type | Purpose | Example |
|------|---------|---------|
| A | IPv4 address | example.com → 93.184.216.34 |
| AAAA | IPv6 address | example.com → 2001:db8::1 |
| CNAME | Alias | www.example.com → example.com |
| MX | Mail server | Mail goes to mail.example.com |
| NS | Nameserver | Points to authoritative nameserver |
| TXT | Text record | For SPF, DKIM, verification |

```bash
# Check DNS records
nslookup example.com
dig example.com
dig example.com A      # IPv4
dig example.com AAAA   # IPv6
dig example.com MX     # Mail servers
```

---

## E: Ethernet & Encapsulation

### Ethernet

The physical/link layer protocol for LANs (local area networks).

```
Your server talks to other servers on the same network via Ethernet.
```

### Encapsulation (Layering)

Data wraps through layers, each adding headers:

```
Application Layer (HTTP)
    ↓ (Add HTTP headers)
Transport Layer (TCP)
    ↓ (Add TCP headers: source/dest port, sequence numbers)
Network Layer (IP)
    ↓ (Add IP headers: source/dest IP address)
Link Layer (Ethernet)
    ↓ (Add MAC headers: source/dest MAC address)
Physical (Copper cable, fiber)
```

**When you send HTTP request:**
```
[HTTP headers][HTTP body]
    ↓ TCP wraps it
[TCP header][HTTP headers][HTTP body]
    ↓ IP wraps it
[IP header][TCP header][HTTP headers][HTTP body]
    ↓ Ethernet wraps it
[Ethernet][IP header][TCP header][HTTP headers][HTTP body][Checksum]
    ↓ Sent on wire
```

**Unwrapping on receive:**
```
Receiver removes Ethernet → IP → TCP → gets HTTP message
```

---

## F: Firewalls & Flow

### Firewalls

Software or hardware that controls traffic based on rules.

```
Inbound Rules: What traffic is allowed INTO your server
Outbound Rules: What traffic is allowed OUT of your server
```

**Example:**
```
Allow port 80 (HTTP) from anywhere
Allow port 443 (HTTPS) from anywhere
Allow port 3306 (MySQL) only from 10.0.0.0/8
Block everything else
```

### Firewall Tools on Linux

```bash
# Check firewall status
sudo ufw status    # On Ubuntu/Debian
sudo firewall-cmd --list-all  # On RHEL/CentOS

# Open a port
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Close a port
sudo ufw deny 3306/tcp

# See active connections
netstat -an
ss -an              # Modern replacement for netstat
```

### Connection Tracking

Stateful firewalls remember connections:

```
Outbound traffic:
Your server → External API (port 443)
    ↓
Firewall remembers this connection
    ↓
Return traffic from API → Your server is ALLOWED
(Without this, you couldn't receive responses!)
```

---

## G: Gateways & Routing

### Gateways

Entry/exit points for networks.

```
Your home network gateway = your WiFi router
In AWS, NAT Gateway = how private subnet servers reach internet
```

### Routing

How packets find their way from source to destination.

```
Step 1: Check routing table
        "Is destination on my local network? YES → send directly via Ethernet"
        "Is destination NOT local? NO → send to gateway/router"

Step 2: Router checks its routing table
        "I know how to reach that destination → forward"

Step 3: Repeat until destination reached
```

**Check your routing table:**

```bash
route -n     # Simple view
ip route     # Modern view

# Output example:
# default via 192.168.1.1 dev eth0     (default gateway)
# 192.168.1.0/24 dev eth0              (local network)
# 172.17.0.0/16 dev docker0            (Docker bridge)
```

**Interpretation:**
```
"If destination is 192.168.1.x → use eth0 directly (local)"
"Otherwise → send to 192.168.1.1 (my router)"
```

---

## H: Headers & Hops

### Headers

Metadata added by each layer.

```
HTTP Header example:
GET /api/users HTTP/1.1
Host: example.com
Content-Length: 42
Authorization: Bearer token123

TCP Header contains:
- Source port: 54321
- Destination port: 443
- Sequence number: 1000
- Acknowledgment number: 2000
- Flags: SYN, ACK, FIN, etc.

IP Header contains:
- Source IP: 192.168.1.100
- Destination IP: 8.8.8.8
- TTL (Time To Live): 64
```

### Hops

Each router the packet passes through = 1 hop.

```bash
# See the path from your machine to google.com
traceroute google.com

# Output:
#  1  router.home (192.168.1.1) 1ms
#  2  isp-gateway (203.0.113.1) 15ms
#  3  backbone1 (198.51.100.1) 20ms
#  4  google-router (172.217.0.1) 25ms
#  5  google.com (142.251.41.14) 25ms
```

**Default hop limit (TTL):** 64 on Linux, 128 on Windows. Each hop decrements by 1. When TTL reaches 0, packet is discarded (prevents infinite loops).

---

## I: Internet & Interfaces

### Internet

Global system of interconnected networks. The "network of networks."

```
Your server is connected to the internet through:
ISP → Backbone → Regional routes → Local networks → Your server
```

### Network Interfaces

Virtual or physical connections to networks.

```bash
# See all interfaces
ip link show
ifconfig

# Output:
# lo: loopback (127.0.0.1)        [purely local, not on internet]
# eth0: ethernet (192.168.1.100)   [actual network connection]
# docker0: bridge (172.17.0.1)     [Docker's virtual network]
# veth1234: virtual eth            [Docker container interface]
```

**Important:** A server can have multiple interfaces, each with its own IP.

```bash
# Server with multiple IPs
ip addr show eth0

# Output:
# inet 192.168.1.100/24           (primary)
# inet 192.168.1.101/24           (secondary)
# inet 10.0.0.50/24               (on different network)
```

---

## J: Jumbo Frames (Jumbograms)

### Standard Frame Size

Normal Ethernet frame: 1,500 bytes (MTU = Maximum Transmission Unit)

### Jumbo Frames

Larger frames: 9,000+ bytes for high-performance networks (data centers).

**Why it matters:**
```
With 1,500 byte frames:
  100 MB file = 66,667 packets

With 9,000 byte frames:
  100 MB file = 11,112 packets

Fewer packets = less overhead, faster transfer
But: Requires all equipment to support jumbo frames
```

**Check your MTU:**

```bash
ip link show eth0
# Output: ... mtu 1500 ...

# Change MTU (for high-speed local networks)
sudo ip link set dev eth0 mtu 9000
```

**When you need this:** Data warehouse transfers, HPC (high-performance computing), not for typical web backends.

---

## K: Keyed Sockets (Keying)

### Socket Pairs

A connection is uniquely identified by a 4-tuple (5-tuple including protocol):

```
(Source IP, Source Port, Destination IP, Destination Port)

Example:
(192.168.1.100, 54321, 93.184.216.34, 443)

This identifies ONE conversation between client and server
```

### Why This Matters

```bash
# Multiple connections to same server are tracked separately
netstat -an | grep :443
# Shows all connections to port 443
# Each has different source port (54321, 54322, 54323, ...)
```

### Maximum Connections

```
Per source IP to destination IP:port combo: 65,535 ports available
(Ports 0-65535, but 1-1023 are reserved)

So: One client IP can have ~64,000 simultaneous connections to one server port

If you have 1,000 clients: 1,000 × 64,000 = 64 million possible connections
(But servers rarely need more than 100,000 connections)
```

---

## L: Latency & Layers

### Latency

Time for data to travel from A to B (or round trip RTT = round trip time).

```
Local network: 1 ms
Same AWS region: 1-10 ms
Different AWS region: 50-150 ms
Intercontinental: 150-300 ms
```

### Layers (OSI Model)

7 layers of networking:

```
Layer 7: Application (HTTP, DNS, SMTP)
Layer 6: Presentation (Encryption, compression)
Layer 5: Session (Establishing/maintaining connection)
Layer 4: Transport (TCP, UDP)
Layer 3: Network (IP routing)
Layer 2: Link/Data (Ethernet, MAC addresses)
Layer 1: Physical (Cables, signals)
```

**Backend engineers usually care about:**
- **Layer 4 (TCP/UDP):** Connection type
- **Layer 3 (IP):** Routing, network configuration
- **Layer 7 (HTTP/HTTPS):** APIs, protocols

---

## M: MAC & Multiplexing

### MAC Addresses

Media Access Control: physical hardware address (48-bit).

```
Format: 00:1a:2b:3c:4d:5e
        ↑  ↑  ↑  ↑  ↑  ↑
        Vendor Unique per device
```

**Use:** Identifying devices on the same local network.

```bash
# See your MAC address
ip link show
# OR
ifconfig

# See other devices' MAC addresses
arp -a  # ARP table (IP ↔ MAC mapping)

# Output example:
# 192.168.1.1 at 00:11:22:33:44:55 [ether]
```

**Difference from IP:**
```
IP address: "Where to send it" (global, routable)
MAC address: "Who to send to directly" (local, physical)

Analogy:
IP = mailing address (route through postal system)
MAC = person's name (when you're talking face-to-face)
```

### Multiplexing

Multiple conversations sharing one connection.

```
HTTP/1.1 Keep-Alive:
Request 1: GET /api/users
Response 1: [JSON]
Request 2: GET /api/posts
Response 2: [JSON]
[All over same TCP connection]

HTTP/2:
Multiple requests/responses simultaneously on same connection
```

---

## N: Networks & Namespaces

### Networks

Logically grouped computers connected together.

```
Your home WiFi network: 192.168.1.0/24
Your office network: 10.0.0.0/8
AWS VPC: 172.31.0.0/16
```

### Namespaces (Linux)

Isolation mechanism so containers/processes have their own:
- Network interfaces
- IP addresses
- Routing tables
- Firewall rules

```bash
# See namespaces
ip netns list

# Execute command in namespace
sudo ip netns exec <namespace> ip addr show

# Docker containers use namespaces for isolation
docker inspect <container> | grep -i namespace
```

**Why it matters:** Docker containers use network namespaces so each can have its own IP address and network configuration.

---

## O: Open Systems & OSI Model

### Open Systems

Systems that follow published standards (interoperable).

```
OSI model = Open Systems Interconnection

A standard model for how networking should work, enabling different vendors' equipment to talk to each other.
```

### OSI Recap

| Layer | Name | Protocol Examples | What Backend Engineers Use |
|-------|------|-------------------|----------------------------|
| 7 | Application | HTTP, HTTPS, DNS, SSH, SMTP | APIs, protocols |
| 6 | Presentation | TLS/SSL, JPEG, MP4 | Encryption |
| 5 | Session | HTTP/HTTPS sessions | Connection state |
| 4 | Transport | TCP, UDP | Sockets, connection type |
| 3 | Network | IP, ICMP, routing | Addresses, routing |
| 2 | Link | Ethernet, ARP, MAC | Physical network, switching |
| 1 | Physical | Fiber, copper, WiFi | Hardware |

---

## P: Ports & Protocols

### Ports

Virtual "endpoints" on a server (0-65535).

```
Port 0-1023: Well-known (reserved for system processes)
  - Port 80: HTTP
  - Port 443: HTTPS
  - Port 22: SSH
  - Port 3306: MySQL
  - Port 5432: PostgreSQL

Port 1024-49151: Registered (less reserved)
  - Port 3000: Node.js dev server
  - Port 5000: Flask dev server
  - Port 8000: Django dev server

Port 49152-65535: Dynamic (temporary, used by clients)
```

**Why both source and destination ports matter:**

```
Client connects to Server:
Client: 192.168.1.100:54321 → Server: 93.184.216.34:443
                    ↑
            Dynamic source port (assigned automatically)

Server knows to send response back to:
93.184.216.34:443 → 192.168.1.100:54321
```

### Protocols

Rules for communication.

```
HTTP:  Request-response, stateless, text-based
HTTPS: HTTP + encryption (TLS/SSL)
TCP:   Reliable, ordered delivery (most common)
UDP:   Fast, unreliable (video streaming, online games)
ICMP:  Diagnostic (ping, traceroute)
```

---

## Q: QoS & Queue

### QoS (Quality of Service)

Prioritizing certain traffic over others.

```
Example:
Video streaming: LOW priority (can be buffered)
VOIP/Calls: HIGH priority (must be real-time)
Database queries: MEDIUM priority
```

### Queues

Packets waiting to be sent/received.

```bash
# See queue depth
netstat -s | grep "segments retransmitted"

# If high retransmissions = network congestion
```

**Backpressure:**

```
When queue fills up:
1. New packets are dropped
2. Sender doesn't get acknowledgment
3. Sender retransmits
4. Network is congested
5. Latency increases
```

---

## R: Routing & Requests

### Routing

How packets find their way.

```bash
# Linux routing table
route -n
ip route show

# Find path to destination
traceroute 8.8.8.8
```

### Routing Types

```
Direct routing: Destination is on my local network → send directly
Indirect routing: Destination is NOT local → send to gateway
Default route: "If you don't know, send to this gateway"
Static routing: Administrator sets routes manually
Dynamic routing: Routers learn routes from each other (OSPF, BGP)
```

### Requests (HTTP)

```
Request = Client asking server for something

HTTP Methods:
GET:    Retrieve data
POST:   Create new resource
PUT:    Update existing resource
PATCH:  Partial update
DELETE: Remove resource
HEAD:   Same as GET but no response body
```

---

## S: Sockets & Servers

### Sockets

Endpoint for network communication (file descriptor).

```
"A socket is like a telephone jack - the interface to the network"
```

**Types:**
```
SOCK_STREAM:   TCP (reliable, ordered)
SOCK_DGRAM:    UDP (unreliable, fast)
```

**Socket states:**
```
LISTEN:        Waiting for connections (server)
ESTABLISHED:   Connected and communicating
CLOSE_WAIT:    Waiting to close (after remote closed)
TIME_WAIT:     Waiting before fully closing (2MSL timeout)
```

```bash
# See all sockets
netstat -an
ss -an          # Modern alternative

# Filter to specific port
netstat -an | grep :3000

# Count connections
netstat -an | grep ESTABLISHED | wc -l
```

### Servers

Programs listening for incoming connections on a socket.

```
Flask/Django:
1. Bind to IP:Port (0.0.0.0:5000)
2. Listen for connections
3. Accept client connections
4. Process request
5. Send response
6. Close connection (or keep alive)
```

---

## T: TCP/IP & Transport

### TCP (Transmission Control Protocol)

Reliable, ordered delivery. Guarantees:
```
- All data arrives
- In correct order
- No duplicates
```

**TCP Connection:**
```
3-Way Handshake (SYN, SYN-ACK, ACK)
Client: SYN (synchronize, seq=1000)
Server: SYN-ACK (acknowledge, seq=2000, ack=1001)
Client: ACK (acknowledge, seq=1001, ack=2001)
[Connection established]
```

**Closing:**
```
FIN → Acknowledge → FIN → Acknowledge
[Connection closed]
```

### TCP Window (Flow Control)

```
Sender says: "I can send up to 65,536 bytes before you must acknowledge"
This prevents overwhelming the receiver
```

### IP (Internet Protocol)

Addressing and routing.

```
IPv4: 32-bit addresses (4 billion possible)
IPv6: 128-bit addresses (340 undecillion possible)
```

---

## U: UDP & User Data

### UDP (User Datagram Protocol)

Fast, unreliable delivery. No guarantees.

```
UDP Characteristics:
- Connectionless (no handshake)
- No flow control
- No ordering guarantee
- Lower overhead
- Suitable for real-time: video, audio, gaming
```

**UDP Packet:**
```
[UDP Header: 8 bytes]
[Data: up to 65,527 bytes]
```

### When to Use

```
TCP: Email, file transfer, web pages (HTTPS)
     Correctness more important than speed

UDP: Video streaming, online games, VoIP
     Speed more important than perfection
     Missing 1 frame = no big deal
```

---

## V: Virtual & VLAN

### Virtual Networks

Networks that exist in software, not physical hardware.

```
Docker bridge network (docker0):
- Virtual network interface
- Virtual switching
- All containers on same "network" can talk directly
```

### VLANs (Virtual LANs)

Logical grouping of devices on physical network.

```
Physical: One Ethernet switch
Virtual: Multiple logical networks on that switch

VLAN 100: Finance (IP range 10.1.x.x)
VLAN 200: Engineering (IP range 10.2.x.x)
VLAN 300: HR (IP range 10.3.x.x)

Even on same switch, VLANs can't talk without a router
```

**Not typically needed for web backends, but good to know.**

---

## W: Wireshark & Web

### Wireshark

Network packet analyzer/sniffer. Captures and displays packets.

```bash
# Capture on eth0 interface
sudo wireshark -i eth0 &

# Or command-line (tcpdump):
sudo tcpdump -i eth0 -w capture.pcap

# Filter for HTTP
sudo tcpdump -i eth0 'port 80'

# Filter for HTTPS
sudo tcpdump -i eth0 'port 443'

# Filter for specific IP
sudo tcpdump -i eth0 'host 192.168.1.100'
```

**Uses:**
```
- Debugging network issues
- Learning how protocols work
- Troubleshooting slow connections
- Security analysis
```

### Web (HTTP/HTTPS)

The primary protocol for backend engineers.

```
HTTP: Plain text (insecure)
HTTPS: HTTP + TLS encryption (secure)

HTTP/1.0: One request per connection
HTTP/1.1: Keep-alive, pipelining
HTTP/2: Multiplexing, compression, push
HTTP/3: Based on UDP instead of TCP
```

---

## X: X.509 Certificates

### X.509

Standard format for public key certificates (encryption/identity).

**Certificate contains:**
```
- Public key
- Subject (who owns this cert)
- Issuer (who signed it)
- Validity dates
- Digital signature
```

**How HTTPS works:**
```
1. Client connects to server (port 443)
2. Server sends X.509 certificate
3. Client verifies certificate is trusted and valid
4. Client and server establish encrypted connection (TLS)
5. Data is encrypted: only client and server can read
```

```bash
# View certificate details
openssl s_client -connect example.com:443 -showcerts

# Check certificate expiration
openssl s_client -connect example.com:443 | \
  openssl x509 -noout -dates
```

---

## Y: Yet Another Protocol (Standards)

### Protocol Standards

The internet is built on open standards and RFCs (Requests for Comments).

```
TCP/IP: RFC 793 (TCP), RFC 791 (IP)
HTTP/1.1: RFC 7230-7237
HTTPS/TLS: RFC 5246 (TLS 1.2), RFC 8446 (TLS 1.3)
DNS: RFC 1035
```

**Why it matters:**
```
Different vendors' equipment can interoperate because they follow same standards
You can predict how networks behave because behavior is standardized
```

### REST (Representational State Transfer)

Standard way to design web APIs.

```
Resource = "thing" (users, posts, comments)
Representation = "how it looks" (JSON, XML)
State Transfer = "changing the thing"

GET /users → List all users
POST /users → Create new user
GET /users/123 → Get user 123
PUT /users/123 → Update user 123
DELETE /users/123 → Delete user 123
```

---

## Z: Zero-Knowledge (Security Basics)

### Zero-Knowledge

Security concept: Prove something without revealing the information.

```
Blockchain example:
- Prove you own Bitcoin without revealing your private key
- Prove you're over 18 without revealing your exact age
```

### Basic Security Concepts

**Authentication:** "Who are you?"
```
Username/password
Certificate
Token (JWT)
OAuth
```

**Authorization:** "What are you allowed to do?"
```
User can only access their own data
Admin can access everything
Guest can only view public data
```

**Encryption:** "Keep secrets secret"
```
TLS/SSL: Encrypts data in transit
Password hashing: Doesn't store plaintext passwords
```

**Examples for backends:**

```python
# Authentication: verify user
user = authenticate_user(username, password)

# Authorization: check permissions
if not user.can_delete_other_users():
    return 403 Forbidden

# Delete user
delete_user(target_user_id)
```

---

## Practice: Putting It Together

### Scenario: A User Loads a Website

```
User types: https://example.com/products

1. DNS (D): Browser resolves example.com → 93.184.216.34
2. IP/Routing (A, G, R): Browser finds route to 93.184.216.34
3. Interfaces (I): Uses eth0 to connect
4. TCP (T): Establishes TCP connection (3-way handshake)
5. TLS/X.509 (X): Verifies server certificate
6. Ports (P): Connects to port 443 (HTTPS)
7. HTTP Request (W): Sends GET request
8. Headers (H): Headers wrapped by each layer
9. Hops (H): Request travels through routers
10. Latency (L): Depending on distance
11. Sockets (S): Server's socket receives data
12. Server Processing: Generates response
13. Response: Travels back through layers 9-1
14. Browser displays: HTML, CSS, JS loads
15. Browser makes more requests: CSS, JavaScript, images
16. Multiplexing (M): HTTP/2 sends all simultaneously
17. Connection closes: TCP teardown (FIN, ACK)
```

### Lab: Check Your Network

```bash
# 1. See your IP
ip addr show

# 2. See your gateway
route -n

# 3. Test connectivity
ping 8.8.8.8

# 4. See what's listening
netstat -an | grep LISTEN

# 5. See active connections
netstat -an | grep ESTABLISHED

# 6. Resolve DNS
nslookup example.com

# 7. Trace route to destination
traceroute google.com

# 8. Check certificate
openssl s_client -connect example.com:443 -showcerts

# 9. Capture packets
sudo tcpdump -i eth0 -n 'port 80'

# 10. List interfaces
ip link show
```

---

## Self-Assessment

### Can You Explain?

- [ ] What's an IP address and why we have both IPv4 and IPv6
- [ ] Difference between TCP and UDP
- [ ] How DNS works (all 5 steps)
- [ ] What a port is and why we need them
- [ ] How a TCP connection is established
- [ ] What layers exist in the OSI model
- [ ] How HTTPS/TLS works at high level
- [ ] What a socket is and why servers use them
- [ ] How routing tables work
- [ ] Why firewalls matter and how they work

### Practical Skills

- [ ] Can run `ip addr show` and explain output
- [ ] Can run `netstat -an` and identify connection states
- [ ] Can use `ping`, `traceroute`, `dig` for debugging
- [ ] Can read a routing table
- [ ] Can check what's listening on your system
- [ ] Can use `tcpdump` to see packets on wire
- [ ] Can check TLS certificate details
- [ ] Can understand CIDR notation (10.0.0.0/8)

---

## Next Steps

You now have the foundation! Ready to dive deeper?

→ **[Module 1: Networking Fundamentals](01-networking-fundamentals.md)** - Deep dive into TCP/IP, sockets, and client-server model with real backend examples.

---

## Quick Reference

### Key Acronyms

| Acronym | Meaning | Relevance |
|---------|---------|-----------|
| IP | Internet Protocol | Addressing |
| TCP | Transmission Control Protocol | Reliable connections |
| UDP | User Datagram Protocol | Fast, unreliable |
| DNS | Domain Name System | Name resolution |
| TLS | Transport Layer Security | Encryption |
| SSL | Secure Sockets Layer | Older encryption (now TLS) |
| HTTP | HyperText Transfer Protocol | Web |
| HTTPS | HTTP Secure | Web + encryption |
| CIDR | Classless Inter-Domain Routing | IP range notation |
| QoS | Quality of Service | Priority |
| MTU | Maximum Transmission Unit | Frame size |
| TTL | Time To Live | Hop count |
| MAC | Media Access Control | Physical address |
| ARP | Address Resolution Protocol | IP to MAC mapping |
| ICMP | Internet Control Message Protocol | Ping, traceroute |
| OSI | Open Systems Interconnection | 7-layer model |
| VPC | Virtual Private Cloud | AWS network |
| VLAN | Virtual LAN | Logical network groups |
| RFC | Request for Comments | Standard specifications |
| JWT | JSON Web Token | Authentication |
| OAuth | Open Authorization | Delegated authentication |

### Port Reference

```
80     HTTP
443    HTTPS
22     SSH
3306   MySQL
5432   PostgreSQL
6379   Redis
5672   RabbitMQ
27017  MongoDB
3000   Node.js (dev)
5000   Flask/Django (dev)
8000   Django (alt)
8080   Common alternate HTTP
```

---

**Completed:** You've covered networking A-to-Z! You now have the language and concepts to understand the deeper modules. Don't worry if you didn't absorb everything—we'll revisit these concepts with practical examples in Module 1.

**Time estimate:** 2-3 hours to read, understand, and practice these basics.
