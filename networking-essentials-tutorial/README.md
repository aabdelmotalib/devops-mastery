# Networking Essentials for Backend Engineers

A production-oriented networking curriculum built for developers who deploy real systems.

## What This Is NOT

- A CCNA theory dump
- Academic networking fundamentals
- Vendor-specific cloud networking
- Conceptual-only material

## What This IS

- How networking actually works in production backends
- Practical Linux commands and configurations
- Real architecture patterns (Flask, FastAPI, Docker, Kubernetes)
- Incident-driven learning

## Target Audience

- Backend engineers (Python, Go, Node.js)
- DevOps engineers
- Cloud engineers (AWS, Azure, GCP)
- Docker/Kubernetes practitioners
- Anyone deploying real systems

## Mental Model

Every example fits into this realistic backend architecture:

```
Client
  ↓ [DNS Resolution]
  ↓ [HTTPS Connection]
  ↓
Reverse Proxy (Nginx)
  ↓ [Routing/Rate Limiting]
  ↓
Load Balancer
  ↓ [L4/L7 Algorithms]
  ↓
Backend Services (Flask/FastAPI)
  ↓ [Connection Pooling]
  ↓
Databases (PostgreSQL/Redis)
```

This model is referenced consistently throughout all modules.

## Curriculum Overview

| Module | Focus | Duration |
|--------|-------|----------|
| **PREMODULE** | **Networking Basics A-Z** | **2-3 hours** |
| 1. Networking Fundamentals | IP, ports, sockets, TCP/UDP | 2 hours |
| 2. HTTP/HTTPS Protocol | Request/response, encryption | 2 hours |
| 3. REST API Design | Resource design, versioning | 2.5 hours |
| 4. WebSockets | Real-time communication | 2 hours |
| 5. Load Balancing | Distribution algorithms | 2.5 hours |
| 6. Reverse Proxy (Nginx) | Request flow, routing | 3 hours |
| 7. DNS & Domain Management | Resolution, records, TTL | 2 hours |
| 8. SSL/TLS Certificates | Encryption, keys, Let's Encrypt | 2.5 hours |
| 9. Final Project | Production-ready setup | 4 hours |

**Total: ~24.5-25.5 hours of material**

### Where to Start

**New to networking?** → Start with the [**Premodule: Networking Basics A-Z**](docs/00-networking-basics-a-to-z.md)

**Have some networking background?** → Jump to [**Module 1: Networking Fundamentals**](docs/01-networking-fundamentals.md)

## How to Use This Tutorial

1. Read modules in order (they build on each other)
2. Run commands in the labs/ directory
3. Study example configurations in examples/
4. Complete practice questions at module end
5. Solve incident scenarios
6. Build the final project

## Prerequisites

- Linux shell familiarity (bash)
- Basic Python or JavaScript
- Docker basics (optional but helpful)
- A Linux VM or WSL2 environment
- Never designed for Windows cmd/PowerShell

## Module Structure

Each module includes:

- **Concept Explanation**: What and why
- **Backend Use Cases**: Real Flask/FastAPI scenarios
- **Linux Commands**: Practical terminal examples
- **Nginx Configuration**: Where relevant
- **Common Mistakes**: What NOT to do
- **Production Notes**: Deployment considerations

## Assessment

### Per-Module

- 5 MCQ questions (no answers provided - challenge yourself)
- 2 practical networking tasks
- 1 production incident scenario

### Final Project

Design and implement:
- Domain + DNS records
- HTTPS with valid TLS certificates
- Nginx reverse proxy
- Load-balanced backend services
- Secure API exposure

## Key Learning Outcomes

After completing this tutorial, you will:

1. **Understand** how networks actually work in production systems
2. **Debug** networking issues in real deployments
3. **Design** scalable backend architectures
4. **Configure** Nginx for real production workloads
5. **Implement** secure communication layers
6. **Troubleshoot** connectivity issues systematically
7. **Optimize** network performance for backend services

## Important Notes

- All examples use Linux tools (netstat, ss, curl, dig, tcpdump)
- Focus is application → infrastructure perspective
- Every concept connects to deployed systems
- No filler material, no repetition
- Practical over theoretical

## Quick Start

```bash
# Clone or download this tutorial
cd networking-essentials-tutorial

# Start with Module 1
cat docs/01-networking-fundamentals.md

# Try practical labs
cd labs/
bash 01-fundamentals-lab.sh

# Examine example configs
cd ../examples/
cat nginx-reverse-proxy.conf
```

## File Structure

```
networking-essentials-tutorial/
├── README.md (this file)
├── docs/
│   ├── 01-networking-fundamentals.md
│   ├── 02-http-https-protocol.md
│   ├── 03-rest-api-design.md
│   ├── 04-websockets.md
│   ├── 05-load-balancing.md
│   ├── 06-reverse-proxy-nginx.md
│   ├── 07-dns-domain-management.md
│   ├── 08-ssl-tls-certificates.md
│   └── 09-final-project.md
├── examples/
│   ├── nginx-reverse-proxy.conf
│   ├── nginx-load-balancer.conf
│   ├── flask-app-example.py
│   ├── docker-compose-lab.yml
│   └── production-setup.sh
└── labs/
    ├── 01-fundamentals-lab.sh
    ├── 02-http-request-lab.sh
    ├── 03-rest-api-lab.sh
    ├── 04-websocket-lab.py
    ├── 05-load-balance-lab.sh
    ├── 06-nginx-lab.sh
    ├── 07-dns-lab.sh
    └── 08-tls-lab.sh
```

## How Modules Connect

```
Fundamentals (IP, TCP, sockets)
    ↓
HTTP/HTTPS (how apps communicate)
    ↓
REST API (patterns for backends)
    ↓
WebSockets (real-time needs)
    ↓
Load Balancing (distributing traffic)
    ↓
Nginx (implementing distribution)
    ↓
DNS (domain to IP mapping)
    ↓
SSL/TLS (securing the whole stack)
    ↓
Final Project (integrate everything)
```

## A Word on Philosophy

This tutorial makes opinionated choices:

- **Linux-only**: Production happens on Linux
- **Practical**: Theory only when it affects deployment
- **Backend-focused**: Not general networking
- **No vendor lock-in**: Concepts work anywhere
- **Real architecture**: Not simplified models

If you need pure CCNA content, this isn't it. If you need to understand networking for real systems, read on.

## Questions & Issues

- Module too fast? Re-read and run the labs multiple times
- Labs not working? Check your Linux environment and network setup
- Need clarification? Review the "Common Mistakes" section
- Stuck on incident scenarios? Think about debugging methodology first

---

**Start with Module 1**: [Networking Fundamentals](docs/01-networking-fundamentals.md)
