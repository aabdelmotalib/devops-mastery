# Module 4: Docker Containers

## Container Lifecycle: States and Transitions

A container has a distinct lifecycle from creation to deletion.

```
Created          Exited           Removed
  ↑               ↓                 ↑
  └── Running ────→ Stopped ───────┘
      ↓ (pause)     ↑
    Paused ────────→
```

### Container States

**Created**: Container exists but hasn't started yet
```bash
docker create --name myapp ubuntu sleep 1000
docker ps -a | grep myapp
# STATUS: Created
# Container layer exists but process hasn't started
```

**Running**: Container's main process is executing
```bash
docker start myapp
docker ps | grep myapp
# STATUS: Up X minutes
# Container PID 1 is actively running
```

**Paused**: Container process is frozen (SIGSTOP)
```bash
docker pause myapp
docker ps | grep myapp
# STATUS: Paused
# Process frozen, memory preserved
# Process can be resumed instantly
```

**Stopped**: Container process has exited
```bash
docker stop myapp
docker ps -a | grep myapp
# STATUS: Exited (137)
# Exit code indicates how it stopped
```

**Deleted**: Container and its layer removed
```bash
docker rm myapp
docker ps -a | grep myapp
# Returns nothing (deleted)
```

### Exit Codes

Container exit code indicates how the process exited:

- **0**: Normal exit, no errors
- **1**: Application error
- **125**: Docker runtime error
- **126**: Container exits but not by application
- **127**: Command not found in container
- **128+N**: Process killed by signal N (128+9=137 means SIGKILL/OOM)
- **137**: Out of memory killed (exit code = 128 + 9)
- **143**: Terminated by SIGTERM (exit code = 128 + 15)

```bash
# Check exit code
docker ps -a
# Shows STATUS: Exited (137)

# Inspect exit code
docker inspect myapp | grep -i exitcode
# "ExitCode": 137
```

## Running Containers: docker run

`docker run` creates and starts a container in one command.

```bash
docker run [OPTIONS] IMAGE [COMMAND] [ARG...]

# Simplest form
docker run ubuntu sleep 1000
# Creates container, runs it, streams output to terminal

# Detached (background)
docker run -d ubuntu sleep 1000
# Returns container ID, container runs in background

# Interactive terminal
docker run -it ubuntu /bin/bash
# Allocates pseudo-terminal, can interact with shell

# With name
docker run --name myapp ubuntu sleep 1000

# Remove after exit
docker run --rm ubuntu echo "temporary"
# Container is deleted when command exits
```

### Run Options: Key Parameters

**Naming and Identification:**
```bash
docker run --name myapp ubuntu sleep 1000
# Container is named "myapp"

docker run --label version=1.0 ubuntu sleep 1000
# Add metadata labels
```

**Standard Input/Output:**
```bash
docker run -i ubuntu cat                # Keep stdin open
docker run -t ubuntu echo hello         # Allocate pseudo-terminal
docker run -it ubuntu /bin/bash         # Interactive (common combo)
docker run -a stdout ubuntu echo hello  # Attach only stdout
```

**Filesystem and Volumes:**
```bash
docker run -v /data:/data ubuntu ls /data
# Bind mount: /data on host → /data in container

docker run -v myvolume:/data ubuntu ls /data
# Named volume: named volume → /data in container

docker run --read-only ubuntu touch /file
# Read-only filesystem (container can't modify anything)
```

**Networking:**
```bash
docker run -p 8080:8000 ubuntu nc -l 8000
# Port mapping: host 8080 → container 8000

docker run --network mynet ubuntu ping other-container
# Connect to custom network

docker run --hostname myapp ubuntu hostname
# Set container hostname

docker run --dns 8.8.8.8 ubuntu cat /etc/resolv.conf
# Set DNS resolver
```

**Resources and Limits:**
```bash
docker run --memory=512m ubuntu stress --vm 1
# Limit memory to 512MB

docker run --cpus=1.0 ubuntu stress --cpu 1
# Limit CPU to 1 core

docker run --cpuset-cpus=0,1 ubuntu stress
# Limit to specific CPU cores

docker run --pids-limit=10 ubuntu sleep 1000
# Max 10 processes allowed

docker run --ulimit nofile=1024 ubuntu ulimit -n
# Set OS-level limits
```

**User and Permissions:**
```bash
docker run --user=1000 ubuntu id
# Run as user ID 1000

docker run --group-add=1001 ubuntu id
# Add supplementary group

docker run --cap-drop=ALL ubuntu
# Drop all Linux capabilities (restrictive, safe)

docker run --cap-add=NET_RAW ubuntu
# Add specific capability (dangerous)
```

**Restart Policy:**
```bash
docker run --restart=always ubuntu sleep 1000
# Always restart if it exits

docker run --restart=unless-stopped ubuntu sleep 1000
# Restart unless explicitly stopped

docker run --restart=on-failure:5 ubuntu sleep 1000
# Restart up to 5 times if it fails

docker run --restart=no ubuntu sleep 1000
# Never restart (default)
```

**Environment Variables:**
```bash
docker run -e APP_ENV=production ubuntu printenv
# Set environment variable

docker run --env-file config.env ubuntu printenv
# Load environment variables from file

# env-file format
APP_ENV=production
LOG_LEVEL=info
DATABASE_URL=postgres://...
```

**Entrypoint and Command:**
```bash
docker run ubuntu echo hello
# Uses image's default CMD (usually /bin/bash)
# Override with: echo hello

docker run --entrypoint=/bin/sh ubuntu -c "echo hello"
# Override ENTRYPOINT (rare)

# Difference:
# ENTRYPOINT: the command to run (not easily overridden)
# CMD: default arguments (easily overridden)
```

## Executing Commands in Containers: docker exec

Run a command inside an already-running container.

```bash
# Start a long-running container
docker run -d --name myapp ubuntu sleep 3600

# Execute command inside it
docker exec myapp ps aux
# Shows processes inside container

# Interactive shell
docker exec -it myapp /bin/bash
# Enter shell, can interact

# Get environment
docker exec myapp printenv
# Shows container's environment variables

# Working directory
docker exec -w /tmp myapp pwd
# Run command in /tmp (not / which is WORKDIR)
```

### exec vs run

| Aspect | docker run | docker exec |
|--------|-----------|-----------|
| Prerequisites | Image exists | Container running |
| Creates | New container | Uses existing |
| Process isolation | Separate namespace | Same namespace |
| Common use | Start service | Debug, maintenance |
| Exit code | Container exits | Just command |

```bash
# run: creates new container, separate namespace
docker run ubuntu ps aux
# Shows only one process (PID 1)

# exec: shares container namespace
docker exec myapp ps aux
# Shows container's processes

# The difference matters for debugging
```

## Attaching to Containers: docker attach

Connect to a running container's stdin/stdout/stderr.

```bash
# Start interactive container
docker run -it --name myapp ubuntu /bin/bash

# In another terminal, attach to it
docker attach myapp
# Now typing affects the original container

# detach without stopping: Ctrl+P then Ctrl+Q
# Stops both: Ctrl+C or exit
```

### attach vs exec

```bash
# attach: connects to container's original process
docker attach myapp
# stdin/stdout go to /bin/bash (PID 1)
# Ctrl+C kills the container

# exec: creates new process in container
docker exec -it myapp /bin/bash
# New /bin/bash process spawned
# Exiting doesn't kill container
```

**Common use:**
- `attach`: Rare, use for interactive debugging if container started interactive
- `exec`: Standard for running commands or shell in running container

## Container Logs: Capturing Output

Docker captures container's stdout and stderr.

```bash
# View logs
docker logs myapp
# Shows all captured output

# Follow logs (like tail -f)
docker logs -f myapp
# Streams new output to terminal
# Ctrl+C to detach

# Last N lines
docker logs --tail 50 myapp

# Since timestamp
docker logs --since 2024-01-15T10:00:00 myapp

# Timestamps
docker logs -t myapp
# Shows when each line was logged

# Whole JSON
docker logs --details myapp
```

### Logging Drivers

Docker can send logs to different destinations.

```bash
# Default: json-file (stored on disk)
docker run --log-driver=json-file ubuntu echo "hello"
cat /var/lib/docker/containers/<id>/<id>-json.log

# Send to syslog
docker run --log-driver=syslog ubuntu echo "hello"
tail /var/log/syslog | grep hello

# Send to host's logging
docker run --log-driver=awslogs \
  --log-opt awslogs-group=/ecs/myapp \
  ubuntu echo "hello"

# Send to Splunk
docker run --log-driver=splunk \
  --log-opt splunk-token=xxxxx \
  --log-opt splunk-url=https://... \
  ubuntu echo "hello"
```

**Production note:** Don't rely on `docker logs`. Use centralized logging.

## Environment Variables

Pass configuration to containers via environment variables.

```dockerfile
# In Dockerfile
FROM python:3.11
ENV APP_ENV=production
ENV LOG_LEVEL=info
CMD ["python", "app.py"]
```

```bash
# Override at runtime
docker run -e APP_ENV=development myapp

# Multiple variables
docker run -e APP_ENV=prod -e LOG_LEVEL=debug myapp

# From file
docker run --env-file config.env myapp

# View container's environment
docker inspect myapp | grep -A 20 Env
```

### Environment File Format

```bash
# config.env
APP_ENV=production
DATABASE_HOST=db.example.com
DATABASE_PORT=5432
DATABASE_USER=admin
LOG_LEVEL=info
LOG_FORMAT=json
SECRET_KEY=xxx (NOT RECOMMENDED)
```

**Security note:** Don't put secrets in environment files. Use secrets management (Docker secrets, Vault, etc.).

## Resource Limits

Control how many system resources a container can use.

### Memory Limits

```bash
# Hard limit: container can't exceed
docker run --memory=512m ubuntu stress --vm 1 --vm-bytes 600m
# Killed with exit code 137 (OOM) when exceeding limit

# Memory reservation: soft limit, other containers can borrow
docker run --memory=512m --memory-reservation=256m ubuntu

# Swap memory (beyond RAM)
docker run --memory=512m --memory-swap=1g ubuntu
# Total: 512m RAM + 512m swap

# Disable OOM killer
docker run --memory=512m --oom-kill-disable ubuntu
# Container can exceed limit (not recommended)
```

### CPU Limits

```bash
# Limit CPU shares (relative to other containers)
docker run --cpu-shares=1024 ubuntu stress --cpu 1
# Default is 1024, higher value gets more CPU time

# Limit to specific percentage of one core
docker run --cpus=0.5 ubuntu stress --cpu 1
# Uses 50% of one core

# Limit to specific cores
docker run --cpuset-cpus=0,1 ubuntu stress
# Uses only CPUs 0 and 1

# CPUs with memory binding
docker run --cpuset-mems=0 ubuntu sleep 1000
# Uses memory from NUMA node 0 (advanced)
```

### Process Limits

```bash
# Max number of processes (PIDs)
docker run --pids-limit=10 ubuntu sleep 1000
# Container can spawn at most 10 processes (including PID 1)

# Very useful to prevent fork bombs
```

### Device Access

```bash
# Grant device access
docker run --device=/dev/ttyUSB0 ubuntu ls -la /dev/ttyUSB0

# Grant with permissions
docker run --device=/dev/sda:/dev/sda ubuntu ls -la /dev/sda
```

## Restart Policies

Control container restart behavior.

```bash
docker run --restart=no ubuntu sleep 1000
# Default: don't restart if it exits

docker run --restart=always ubuntu sleep 1000
# Restart if exits, regardless of exit code

docker run --restart=unless-stopped ubuntu sleep 1000
# Restart unless container was explicitly stopped

docker run --restart=on-failure:5 ubuntu sleep 1000
# Restart up to 5 times if exit code is non-zero

docker run --restart=on-failure:5:10 ubuntu sleep 1000
# Restart up to 5 times, wait 10 seconds between restarts
```

**Use in production:**
```bash
docker run --restart=unless-stopped \
  --name myapp \
  myimage:1.0
# Survives daemon restart, can be explicitly stopped
```

### How Restart Works

```bash
# Container exits
docker run --restart=always ubuntu sleep 10
# After 10 seconds, container exits
# Docker daemon notices exit
# After short delay, daemon restarts container
# Process is back, PID 1 is new

# Check restart count
docker inspect myapp | grep -i restartcount
# Shows how many times it's been restarted
```

## Health Checks

Monitor container's health status.

```dockerfile
# In Dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y curl
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

Parameters:
- `--interval`: How often to check (default 30s)
- `--timeout`: How long to wait for check (default 3s)
- `--start-period`: Grace period before first check (default 0s)
- `--retries`: Failures before unhealthy (default 3)

```bash
# Check status
docker ps
# STATUS: Up 5 minutes (healthy)
# If unhealthy: Up 5 minutes (unhealthy)

# Inspect health
docker inspect myapp | grep -A 10 Health
# Shows last check result
```

**Health check is informational.** Docker doesn't automatically restart unhealthy containers.

```bash
# Combine with restart policy
docker run --restart=unless-stopped \
  --health-cmd="curl -f http://localhost:8000/health || exit 1" \
  --health-interval=30s \
  myapp
```

## Real-World Example: Running a Web Application

```bash
# Build image
docker build -t myapi:v1.0 .

# Run with production settings
docker run \
  --name myapi \
  --restart=unless-stopped \
  --memory=1g \
  --cpus=2.0 \
  -p 8080:8000 \
  -e APP_ENV=production \
  -e LOG_LEVEL=info \
  -e DATABASE_URL=postgres://db.example.com/mydb \
  -v /data/uploads:/app/uploads \
  --health-cmd="curl -f http://localhost:8000/health || exit 1" \
  --health-interval=30s \
  myapi:v1.0
```

Breaking down:
- `--name`: Identifiable in `docker ps`
- `--restart=unless-stopped`: Survives daemon restart
- `--memory=1g`: Prevent OOM issues
- `--cpus=2.0`: Fair resource allocation
- `-p 8080:8000`: Public port mapping
- `-e APP_ENV=production`: Configuration
- `-v /data/uploads:/app/uploads`: Persistent storage
- `--health-cmd`: Monitor container health
- `myapi:v1.0`: Specific version (not latest)

## Container Inspection

Inspect running container details.

```bash
# Overview
docker ps
# Live containers

docker ps -a
# All containers (including stopped)

# Detailed inspection
docker inspect myapp
# Returns JSON with all details

# Specific fields
docker inspect -f '{{.State.Pid}}' myapp
# Host PID of container's init process

docker inspect -f '{{.NetworkSettings.IPAddress}}' myapp
# Container's IP address

docker inspect -f '{{.Config.Env}}' myapp
# Container's environment variables
```

### Get Container Statistics

```bash
# Live resource usage
docker stats myapp
# Shows CPU, memory, network, block I/O usage

# All containers
docker stats
# Shows all running containers

# Specific format
docker stats --format "table {{.Container}}\t{{.MemUsage}}"
# Memory usage in table format
```

## Container Copying

Copy files between host and container.

```bash
# Copy from host to container
docker cp myfile.txt myapp:/tmp/
# Copies myfile.txt to /tmp/ in container

# Copy from container to host
docker cp myapp:/tmp/result.txt ./
# Copies result.txt from container to current directory

# Copy directories
docker cp ./data myapp:/app/
# Recursive copy
```

## Production Insights

1. **Avoid interactive containers in production** - Use exec for debugging
2. **Always set resource limits** - Prevents noisy neighbor issues
3. **Use restart policies** - Ensures recovery from crashes
4. **Name containers for identification** - Makes management easier
5. **Prefer environment variables** - Standard configuration method
6. **Monitor with health checks** - Early detection of issues
7. **Use specific versions** - Not latest
8. **Log to external system** - Not just docker logs

---

## Practice: Exam Questions

1. **What is the difference between docker run and docker exec?**
   - A) run is faster than exec
   - B) run creates a new container; exec runs in existing container
   - C) run is for background; exec is for interactive
   - D) exec is for image building; run is for execution

2. **What exit code 137 indicates?**
   - A) Normal exit
   - B) Application error
   - C) Out of memory kill
   - D) Command not found

3. **Which restart policy ensures a container survives daemon restart but can be explicitly stopped?**
   - A) --restart=always
   - B) --restart=on-failure
   - C) --restart=unless-stopped
   - D) --restart=no

4. **What is the purpose of a health check in Docker?**
   - A) To prevent container startup
   - B) To monitor container status and report health
   - C) To automatically restart unhealthy containers
   - D) To scan for security vulnerabilities

5. **If you run `docker run -e VAR=value myimage`, where is VAR available?**
   - A) On the host system
   - B) Only in the Dockerfile
   - C) Inside the running container
   - D) In the Docker daemon

6. **What happens to a container with --restart=always if it exits with code 0?**
   - A) It stays stopped
   - B) It restarts
   - C) Docker logs an error
   - D) The host reboots

---

## Hands-On Labs

### Lab 1: Container Lifecycle and State Management

**Objective:** Understand container states and transitions.

```bash
# Create container without running
docker create --name lifecycle-test ubuntu sleep 3600
docker ps -a | grep lifecycle-test
# Shows STATUS: Created

# Start it
docker start lifecycle-test
docker ps | grep lifecycle-test
# Shows STATUS: Up X seconds

# Pause it
docker pause lifecycle-test
docker ps | grep lifecycle-test
# Shows STATUS: Paused

# Unpause
docker unpause lifecycle-test
docker ps | grep lifecycle-test
# Shows STATUS: Up X seconds

# Stop it
docker stop lifecycle-test
docker ps -a | grep lifecycle-test
# Shows STATUS: Exited (0)

# Start again
docker start lifecycle-test
docker ps | grep lifecycle-test
# Shows STATUS: Up (restarted)

# View restart count
docker inspect lifecycle-test | grep -i restartcount
# Shows: 1

# Delete it
docker rm lifecycle-test
docker ps -a | grep lifecycle-test
# Returns nothing
```

**What you're observing:**
- Containers have distinct states
- Container persists until deletion
- Restart count increments each start
- Exit codes indicate how container exited

### Lab 2: Resource Limits and Health Checks

**Objective:** Apply limits and monitor container health.

```bash
# Create Python app with health endpoint
cat > healthcheck_app.py << 'EOF'
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import psutil

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.send_response(200 if memory_percent < 80 else 503)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'ok' if memory_percent < 80 else 'degraded',
                'memory': memory_percent,
                'cpu': cpu_percent
            }).encode())

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8000), HealthHandler)
    server.serve_forever()
EOF

# Create Dockerfile with health check
cat > Dockerfile.health << 'EOF'
FROM python:3.11-slim
RUN pip install psutil
COPY healthcheck_app.py /app/
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=2s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["python3", "/app/healthcheck_app.py"]
EOF

# Build
docker build -t healthcheck-demo:1.0 -f Dockerfile.health .

# Run with memory limit
docker run -d \
  --name health-test \
  --memory=256m \
  --cpus=0.5 \
  -p 8000:8000 \
  healthcheck-demo:1.0

# Monitor health
docker ps | grep health-test
# Shows (healthy) in STATUS after first check

# Watch health status
for i in {1..10}; do 
  docker ps | grep health-test
  echo "---"
  sleep 2
done

# Check health details
docker inspect health-test | grep -A 10 '"Health"'
# Shows health status and history

# Stress test (try to consume memory)
docker exec health-test python3 -c "x = [1]*100000000"
# Health check might fail if memory exceeds threshold

# Monitor stats
docker stats health-test
# Shows CPU%, memory usage

# Clean up
docker stop health-test
docker rm health-test
```

**What you're observing:**
- Health checks run periodically
- Status reflects health
- Resource limits are enforced
- Stats show actual resource usage

---

## Failure Scenario: The Mysterious Restart Loop

**Scenario:**
Your production container constantly restarts. Every few seconds, it starts and immediately crashes. Your logs show nothing useful - each crash loses the previous logs.

**Symptoms:**
```bash
docker ps
# STATUS: Restarting (1) 2 seconds ago

docker logs myapp
# Shows only last run's logs (previous runs lost)
```

**Root cause:**
Container's entrypoint fails immediately. Since restart policy is `--restart=always`, it restarts forever. Each restart happens so fast you can't see logs.

**Debugging:**
```bash
# Turn off restart temporarily
docker update --restart=no myapp
docker stop myapp

# Try starting manually to see error
docker start -a myapp
# Now you see the actual error

# Example error:
# /bin/bash: line 1: /app/app.py: No such file or directory

# Check what's actually in container
docker exec myapp ls -la /app/
# File doesn't exist!

# Problem: Build included /app/app.py, but docker run
# mounted volume at /app that's empty
docker run -v /data:/app myapp  # Overwrote /app with empty /data
```

**Solution:**
```bash
# Remove the problematic volume mount
docker run --restart=unless-stopped \
  -v /data:/data \  # Mount at different path
  myapp

# Or fix the entrypoint to handle missing files
# In Dockerfile:
# CMD ["python3", "-c", "import sys; print('No file found'); sys.exit(1)"]
```

**Prevention:**
- Always test container startup manually first
- Don't use `--restart=always` in testing
- Monitor restart count: `docker inspect | grep RestartCount`
- Log to external system (don't rely on docker logs)

---

Next: [Module 5: Docker Networking](05-docker-networking.md)
