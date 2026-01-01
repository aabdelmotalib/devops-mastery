# Module 2: Docker Architecture

## The Docker Architecture: Components and Concepts

Docker is not a single monolithic tool. It's a collection of components that work together to provide container management.

```
┌─────────────────────────────────────────┐
│         Docker Client (CLI)              │
│  docker run, docker build, docker push  │
└──────────────┬──────────────────────────┘
               │ (Unix socket: /var/run/docker.sock)
               ↓
┌─────────────────────────────────────────┐
│       Docker Daemon (dockerd)            │
│  - Image management                      │
│  - Container lifecycle                   │
│  - Network configuration                 │
│  - Volume management                     │
│  - Logging                               │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴────────┬──────────────┐
      ↓                 ↓              ↓
  ┌────────────┐  ┌──────────┐  ┌──────────┐
  │  Image DB  │  │ Container│  │  Network │
  │ (overlay2) │  │  Runtime │  │   Stack  │
  │            │  │ (runc)   │  │          │
  └────────────┘  └──────────┘  └──────────┘
      ↓                 ↓              ↓
  Filesystem       OS Namespaces   Linux Network
  Layers          & cgroups       Configuration
```

## Docker Client vs Docker Daemon

### Docker Client

The CLI tool you interact with daily.

```bash
docker run -it ubuntu bash
docker build -t myapp .
docker push myapp:latest
```

**Client behavior:**
- Sends commands to daemon via REST API over Unix socket
- Runs locally, can connect to remote daemon
- Stateless - doesn't maintain container state
- Just a command formatter and API client

```bash
# Client can talk to remote daemon
docker -H tcp://remote-server:2375 ps
# Same commands, different daemon
```

### Docker Daemon (dockerd)

The long-running service that actually manages containers.

```bash
# Start daemon (usually systemd manages this)
sudo systemctl start docker

# Daemon listens on Unix socket (default)
ls -la /var/run/docker.sock
# srw-rw---- 1 root docker

# All containers are children of the daemon
ps aux | grep dockerd
pstree dockerd
# Shows all running containers as children
```

**Daemon responsibilities:**
- Accept requests from clients
- Manage container lifecycle
- Manage image storage
- Configure networking
- Handle logging
- Enforce resource limits

**Why the client-server split?**
- Daemon can manage containers when client disconnects
- Multiple clients can talk to same daemon
- Daemon can run on headless servers
- Easy to containerize the daemon itself

## Container Runtime: OCI and runc

Docker doesn't directly run containers. It uses a **container runtime** that conforms to the OCI (Open Container Initiative) standard.

### OCI (Open Container Initiative) Specification

OCI defines:
- **Image spec**: How container images are structured (layers, manifest, config)
- **Runtime spec**: How to execute containers (namespaces, cgroups, capabilities)

Any tool can create images/containers as long as it follows OCI spec.

### runc: The Standard Container Runtime

`runc` is a lightweight, reference implementation of OCI runtime.

```bash
# runc is installed with Docker
which runc
/usr/bin/runc

# You can use runc directly (advanced)
runc list
# Shows running containers managed by runc

# runc is what actually executes containers
ps aux | grep runc
# Shows runc processes, one per container
```

**runc's job:**
1. Receive container config (namespaces, cgroups, mount points)
2. Apply OS-level isolation (create namespaces, set cgroups)
3. Execute the process
4. Manage process lifecycle

```bash
# Docker calls runc like this (simplified):
runc run <container-id>
# runc configures kernel features and executes the application
```

### Other Container Runtimes

Different runtimes, same OCI spec:

- **containerd**: More minimal daemon, used by Kubernetes
- **cri-o**: Kubernetes-focused runtime
- **gVisor**: Sandbox runtime (more isolation, less performance)
- **Kata Containers**: VM-like security with container speed

Docker can use different runtimes:

```bash
# Use gVisor instead of runc (if installed)
docker run --runtime=runsc ubuntu echo hello

# Check available runtimes
docker info | grep -i runtime
```

## Docker Engine: The Abstraction Layer

Docker Engine combines:
- **Image management** (building, storing, versioning)
- **Container management** (lifecycle, execution)
- **Networking** (bridge networks, port mapping, DNS)
- **Storage** (volumes, bind mounts, union filesystem)
- **Logging** (capture stdout/stderr)

All on top of the container runtime (runc).

```
User (docker run)
    ↓
Docker CLI (client)
    ↓
Docker Daemon (accepts request, validates config)
    ↓
Image Layer (provides filesystem, config)
    ↓
Container Runtime (runc - applies namespaces/cgroups)
    ↓
Linux Kernel (enforces isolation)
```

### Example: When You Run `docker run`

```bash
docker run --memory=512m --name myapp -p 8080:8080 myimage:1.0
```

Docker daemon:

1. **Image validation**
   - Checks if image exists locally
   - Downloads from registry if needed
   - Verifies image integrity

2. **Container configuration**
   - Generates container ID (random hash)
   - Prepares filesystem (unions layers with writable layer)
   - Configures memory limit (512m) via cgroups
   - Sets port mapping (8080 -> 8080)

3. **Runtime execution**
   - Calls runc with config
   - runc creates namespaces (PID, network, mount, etc.)
   - runc applies cgroups limits
   - runc executes the entrypoint process

4. **Monitoring**
   - Daemon tracks container state
   - Captures stdout/stderr for logging
   - Monitors process exit

## Image Registry: Where Images Live

An image registry is a server that stores and distributes container images.

```
┌──────────────────────────────────┐
│     Image Registry Server        │
│  (Docker Hub, ECR, GCR, etc.)    │
│                                  │
│  [image:v1]  [image:v2]          │
│  [db:latest] [cache:stable]      │
└──────────────────────────────────┘
      ↑               ↑
      │               │
   docker push    docker pull
      │               │
      └───────────────┘
         Docker Daemon
```

### Registry Responsibilities

- Store image layers (blobs)
- Store image manifests (metadata)
- Provide image verification (signatures)
- Handle authentication and authorization
- Distribute images to clients

### Common Registries

**Docker Hub** (free, public default)
```bash
docker push myuser/myimage:1.0
# Stores at hub.docker.com/myuser/myimage
```

**AWS ECR** (private, for AWS users)
```bash
docker tag myimage:1.0 123456789.dkr.ecr.us-east-1.amazonaws.com/myimage:1.0
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/myimage:1.0
```

**Docker Distribution** (self-hosted)
```bash
# Run your own registry
docker run -d -p 5000:5000 registry:2
docker tag myimage:1.0 localhost:5000/myimage:1.0
docker push localhost:5000/myimage:1.0
```

### Image Naming Convention

```
[registry]/[repository]/[image]:[tag]

Examples:
- ubuntu:22.04 (Docker Hub default)
- hub.docker.com/library/ubuntu:22.04 (explicit)
- gcr.io/myproject/myapp:v1.0 (GCR)
- 123456.dkr.ecr.us-east-1.amazonaws.com/myapp:v1.0 (ECR)
```

## Docker vs containerd: The Architecture Evolution

### Original: Docker Architecture

```
Docker CLI
    ↓
dockerd (daemon)
    ↓
runc (container runtime)
    ↓
Linux Kernel
```

The daemon directly talks to runc.

### Modern: containerd Architecture

```
Docker CLI
    ↓
dockerd (thinner layer)
    ↓
containerd (container runtime daemon)
    ↓
runc (runtime)
    ↓
Linux Kernel
```

**Why the shift?**

1. **Modularity**: containerd can manage containers without dockerd
2. **Kubernetes**: containerd is lighter for Kubernetes nodes
3. **Portability**: containerd works across different platforms
4. **Separation of concerns**: daemon doesn't need image/storage logic

```bash
# Modern Docker uses containerd
systemctl status containerd
# Running: containerd manages actual containers

# You can use containerd directly
ctr images ls
# Lists images using containerd's database

# Or use nerdctl (CLI for containerd)
nerdctl run ubuntu echo hello
# Similar to docker, but uses containerd directly
```

### For This Tutorial

We focus on Docker CLI because:
- It's the standard interface for most users
- containerd is an implementation detail
- Concepts apply regardless of underlying runtime
- Kubernetes will teach you about containerd

## Docker Storage Architecture

Docker stores images and containers in a **storage driver**. The most common is `overlay2`.

```
/var/lib/docker/overlay2/
├── <layer-1-hash>/
│   ├── diff/ (actual filesystem changes)
│   └── link (unique identifier)
├── <layer-2-hash>/
│   ├── diff/
│   └── link
├── <merged-container-id>/
│   ├── upper/ (writable layer)
│   ├── work/  (temporary space)
│   └── merged (union filesystem view)
└── ...
```

### How overlay2 Works

The union filesystem allows stacking read-only layers with a writable top layer.

```bash
# When you build an image with three FROM/RUN commands
FROM ubuntu:22.04           # Layer 1: base filesystem
RUN apt-get install python3 # Layer 2: added python3 binary
COPY app.py /app/          # Layer 3: added app.py

# Docker creates:
# Layer 1: ubuntu's filesystem (/bin, /usr, /etc, etc.)
# Layer 2: Python's binaries added
# Layer 3: app.py file added

# Each layer only stores differences (delta)
ls -la /var/lib/docker/overlay2/*/diff
# Shows only changed files, not entire filesystem

# When container runs, overlay2 unions all layers:
# 1. Mount layer 1 (read-only): /
# 2. Mount layer 2 (read-only): overwrites what's in layer 1
# 3. Mount layer 3 (read-only): overwrites what's in layer 2
# 4. Mount container layer (read-write): on top
# Result: a single filesystem that looks like the full app
```

**Why this matters:**

1. **Efficient storage**: Layers are deduplicated across images
   - Image A and Image B both based on ubuntu:22.04
   - ubuntu layer stored once, shared by both

2. **Build cache**: Docker can reuse layers
   - `FROM ubuntu` caches the layer
   - Next build, docker reuses it
   - Speeds up builds

3. **Distribution**: Only changed layers are transferred
   - Pull myapp:1.0 (downloads all layers)
   - Pull myapp:1.1 (downloads only changed layers)

```bash
# See this yourself
docker images
# Shows SIZE for each image

# Build a new image with same base
docker build -t test1:v1 .
# Downloads base layer: 50MB

docker build -t test2:v1 .
# Same base layer, reused from cache
# Much faster, no network download
```

## Docker Networking Architecture

Docker manages container networking at the daemon level.

```
┌─────────────────┐  ┌─────────────────┐
│   Container A   │  │   Container B   │
│ IP: 172.17.0.2  │  │ IP: 172.17.0.3  │
└────────┬────────┘  └────────┬────────┘
         │ eth0               │ eth0
         └─────────────┬──────┘
                       │
                ┌──────────────┐
                │ Docker Bridge│ (docker0)
                │ IP: 172.17.0.1
                └──────────────┘
                       │
                   Host eth0
                 (192.168.1.10)
```

### Default Bridge Network

When you run a container, Docker creates virtual network interfaces:

```bash
# Container gets virtual eth0
docker run -it ubuntu hostname -I
# 172.17.0.2

# Host has docker0 bridge
ip addr show docker0
# inet 172.17.0.1/16

# Containers are connected to docker0 bridge
docker network inspect bridge
# Shows all containers on default bridge network
```

### Custom Networks

More advanced: user-defined networks with DNS.

```bash
# Create custom network
docker network create mynet

# Run containers on custom network
docker run --network mynet --name app1 ubuntu sleep 1000
docker run --network mynet --name app2 ubuntu sleep 1000

# Inside app2, can resolve app1 by hostname
docker exec app2 ping app1
# Works because Docker provides DNS for custom networks

# Default bridge network has limitations:
# - No DNS resolution by hostname (must use IP)
# - No network aliases
```

## Container Lifecycle and State Management

Docker tracks container state through the daemon.

```
┌─────────┐
│ Created │
└────┬────┘
     │ docker start
     ↓
┌─────────┐
│ Running │ ← docker exec, docker attach
└────┬────┘
     │ docker pause (SIGSTOP)
     ↓
┌──────────┐
│ Paused   │
└────┬─────┘
     │ docker unpause
     │ (or stop/restart)
     ↓
┌─────────┐
│ Stopped │ ← docker stop, container exits, OOM kill
└────┬────┘
     │ docker rm
     ↓
┌─────────┐
│ Deleted │
└─────────┘
```

**Container persistence:**
- Created/Stopped container's writable layer persists until `docker rm`
- Data in volumes persists even after container deletion
- Running container's filesystem changes are ephemeral

```bash
# Create container but don't run it
docker create --name myapp ubuntu sleep 1000

# Container exists but isn't running
docker ps -a | grep myapp
# Shows STATUS: Created

# Start it
docker start myapp
# Now it's running

# Stop it
docker stop myapp
# Back to Created/Exited state

# Container and its layer still exist
docker ps -a | grep myapp
# Still shows the container

# Delete container
docker rm myapp
# Now container and layer are gone
```

## Docker Logging Architecture

Docker captures container's stdout/stderr and stores it.

```
Container Process
       ↓
    stdout/stderr
       ↓
   Docker Daemon
(collects and buffers)
       ↓
  Logging Driver
  (determines where to store)
       ↓
┌──────────────────────────────┐
│ json-file    (local JSON)    │
│ syslog       (syslog server) │
│ awslogs      (CloudWatch)    │
│ splunk       (Splunk)        │
│ ... others                   │
└──────────────────────────────┘
```

Default driver is `json-file` (JSON to `/var/lib/docker/containers/<id>/`).

```bash
# View container logs
docker logs myapp
# Reads from JSON files on disk

# Logs are preserved after container stops
docker logs myapp
# Still shows output

# Can stream logs
docker logs -f myapp
# Like tail -f

# Configure logging driver
docker run --log-driver=syslog myapp
# Sends logs to syslog instead
```

## Production Insight: Multi-Node Architecture

Single daemon on one host works for development. Production requires multiple nodes.

```
┌─────────────────────────────────────────┐
│        Container Orchestration          │
│  (Kubernetes, Docker Swarm)             │
│                                         │
│  Schedules containers across nodes      │
│  Manages networking between nodes       │
│  Handles node failures                  │
└────────────────┬────────────────────────┘
     ┌───────────┼───────────┐
     ↓           ↓           ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│ Node 1   │ │ Node 2   │ │ Node 3   │
│ dockerd  │ │ dockerd  │ │ dockerd  │
│          │ │          │ │          │
│[app]    │ │[db]      │ │[cache]  │
└──────────┘ └──────────┘ └──────────┘
  Host1        Host2        Host3
```

Docker Swarm provides orchestration, but Kubernetes is the standard. This is covered in Module 10.

## Key Architectural Decisions

### Client-Server Separation

**Pro:**
- Daemon survives client disconnection
- Multiple clients can manage same containers
- Daemon can run on headless servers

**Con:**
- Requires socket access (security implications)
- Can have state inconsistency between client and daemon

### OCI Runtime Abstraction

**Pro:**
- Containers are portable (run with any OCI runtime)
- Can plug in different runtimes (gVisor, Kata)
- Follows industry standard

**Con:**
- Adds abstraction layer (minimal performance impact)
- Complexity for advanced users

### Union Filesystem for Layers

**Pro:**
- Efficient storage (deduplicated layers)
- Fast builds (cached layers)
- Fast startup (no disk copy)

**Con:**
- Not available on all filesystems (needs overlay2, aufs, etc.)
- Performance penalty on some operations
- Can hit inode limits at scale

---

## Practice: Exam Questions

1. **What is the primary role of the Docker daemon (dockerd)?**
   - A) To format Docker commands for the kernel
   - B) To manage container lifecycle, networking, and storage
   - C) To compile Dockerfiles into machine code
   - D) To provide a GUI for Docker

2. **How does the Docker client communicate with the Docker daemon?**
   - A) Direct system calls to the kernel
   - B) REST API over Unix socket or TCP
   - C) Through the container runtime
   - D) Shared memory IPC

3. **What is the OCI (Open Container Initiative) specification?**
   - A) A Docker-proprietary format for images
   - B) A standard defining image and runtime specifications
   - C) A Linux kernel extension
   - D) A cloud storage format

4. **Which component actually executes containers and applies namespaces/cgroups?**
   - A) Docker daemon
   - B) Docker CLI
   - C) Container runtime (runc)
   - D) Image registry

5. **What is an image registry?**
   - A) A directory on your computer that stores images
   - B) A server that stores and distributes container images
   - C) The Docker daemon's internal database
   - D) A tool for building container images

6. **In the context of Docker, what is overlay2?**
   - A) A networking protocol
   - B) A storage driver that uses union filesystem
   - C) A container runtime
   - D) A logging mechanism

---

## Hands-On Labs

### Lab 1: Interact with Docker Daemon via CLI and Socket

**Objective:** Understand the client-server separation.

```bash
# Terminal 1: Check daemon socket
ls -la /var/run/docker.sock
# srw-rw---- 1 root docker

# Verify daemon is running
sudo systemctl status docker
# Should be active (running)

# Terminal 2: Run container
docker run -d --name arch-test ubuntu sleep 3600

# Terminal 1: Check daemon process tree
ps aux | grep dockerd
pstree dockerd | head -20
# Shows container processes as children of daemon

# Terminal 2: Call Docker via socket (advanced)
curl --unix-socket /var/run/docker.sock \
  http://localhost/v1.40/containers/json | python3 -m json.tool
# Shows containers (if you have socket access)

# Verify daemon state persistence
docker ps
# Container still running

# Kill the Docker client process (doesn't stop containers)
# Containers keep running

# Clean up
docker stop arch-test
docker rm arch-test
```

**What you're observing:**
- Daemon is a separate process (can restart without affecting running containers)
- Client talks to daemon via socket
- Containers are managed by daemon, not client

### Lab 2: Inspect Image Layers and Storage

**Objective:** See how Docker stores images.

```bash
# Pull an image
docker pull ubuntu:22.04

# Build a custom image
cat > Dockerfile << 'EOF'
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl
RUN apt-get install -y git
COPY test.txt /app/test.txt
EOF

echo "test content" > test.txt
docker build -t layered-test:1.0 .

# Inspect image history (layers)
docker history layered-test:1.0
# Shows each layer with size and command

# Inspect storage
docker inspect layered-test:1.0 | grep -A 10 RootFS
# Shows layers' SHA256 digests

# View actual layer storage
ls -la /var/lib/docker/overlay2/
# See layer directories

# Inspect layer details
docker image inspect --format='{{json .RootFS}}' layered-test:1.0 | python3 -m json.tool
# Shows layer structure

# Build again with same Dockerfile
docker build -t layered-test:2.0 .
# Reuses layers from cache (fast)

# Compare sizes
docker images | grep layered-test
# Same size because layers are deduplicated
```

**What you're observing:**
- Each command in Dockerfile creates a layer
- Layers are immutable and stored separately
- Layers are reused across images
- Storage driver unions layers into single filesystem view

---

## Failure Scenario: The Mysterious Daemon Restart

**Scenario:**
Your production Docker host reboots. All containers are gone. Your monitoring system is screaming. But the container's persistent data is still there (you used volumes).

**Questions:**
- Where did the containers go?
- Why is the data safe?
- How do you prevent this?

**Root cause:**
Containers don't persist across daemon restarts by default. When dockerd starts, it doesn't know about containers that were running before the restart.

**Debugging:**
```bash
# After reboot, check containers
docker ps
# Nothing running

# But check stopped containers
docker ps -a
# Shows containers with STATUS: Exited

# Check for volumes
docker volume ls
# Volumes still exist (independent of containers)
```

**Prevention:**
Use restart policies:

```bash
# Restart container automatically on daemon restart
docker run --restart=unless-stopped -d myapp

# With docker-compose
version: '3'
services:
  app:
    image: myapp
    restart_policy:
      condition: unless-stopped
```

**Learning point:**
Containers are managed by daemon. Daemon going down takes containers with it. Plan for daemon restarts; use restart policies and manage data in volumes.

---

Next: [Module 3: Docker Images](03-docker-images.md)
