# Module 1: Container Fundamentals

## What Containers Actually Are

A container is an isolated Linux process (or group of processes) that runs on a shared kernel with restricted access to system resources.

Key insight: **Containers are not lightweight virtual machines.** They are processes with enforced boundaries.

### The Three-Layer Understanding

**Layer 1: Operating System**
- Linux kernel provides: namespaces (isolation) and cgroups (resource control)
- All processes share the same kernel
- The kernel enforces boundaries between processes

**Layer 2: Container Runtime**
- Takes OS primitives (namespaces, cgroups) and applies them to a process
- `runc` is the standard Linux container runtime
- Sets up the isolated environment before starting the application

**Layer 3: Docker**
- Manages container images, networking, storage
- Provides user-friendly CLI
- Abstracts the complexity of runtime configuration

### How Containers Work at the OS Level

When you run a container, the kernel executes these operations:

1. **Create a new namespace** - Process sees its own:
   - PID namespace: isolated process IDs (container's PID 1 is init)
   - Network namespace: isolated network stack (own IP, ports)
   - Mount namespace: isolated filesystem view
   - UTS namespace: isolated hostname
   - IPC namespace: isolated interprocess communication
   - User namespace: optional UID/GID mapping

2. **Apply resource limits (cgroups)** - Kernel enforces:
   - Memory limit: container cannot use more RAM
   - CPU limits: fraction of CPU time
   - I/O limits: disk read/write rates
   - Process limits: max number of child processes

3. **Load the filesystem** - Docker union filesystem:
   - Base image layers stacked read-only
   - Writable container layer on top
   - Changes isolated to this container

4. **Start the process** - Execute the application with:
   - Restricted system call access (seccomp, AppArmor)
   - Limited capabilities (no root privileges by default - best practice)
   - Redirected stdout/stderr to Docker logging

### Example: Running a Container at the OS Level

```bash
# When you run:
docker run --memory=256m --cpus=1.0 -e APP_ENV=prod ubuntu sleep 1000

# Docker actually does (simplified):
# 1. Create cgroup: /sys/fs/cgroup/memory/docker/<container-id>
#    Set memory.limit_in_bytes = 256m
# 2. Create cgroup: /sys/fs/cgroup/cpu/docker/<container-id>
#    Set cpu quotas to limit to 1 CPU
# 3. Use unshare(CLONE_NEWPID|CLONE_NEWNET|CLONE_NEWNS|...)
#    This clones the namespaces
# 4. Mount filesystem from image layers
# 5. execve("/bin/sleep", ["1000"], ["APP_ENV=prod"])
```

You can verify this from the host:

```bash
# Start a container
docker run -d --name myapp ubuntu sleep 3600

# Find its PID
docker inspect -f '{{.State.Pid}}' myapp
# Output: 12345

# Check from host (as root):
ps aux | grep 12345
# PID 12345 appears on host, but
# inside container it's PID 1

# Check its cgroup memory limit
cat /sys/fs/cgroup/memory/docker/$(docker inspect -f '{{.Id}}' myapp)/memory.limit_in_bytes
# Shows 268435456 (256m in bytes)

# Check its namespace
ls -l /proc/12345/ns/
# ipc, mnt, net, pid, uts, user all different from host
```

## Containers vs Virtual Machines

| Aspect | Container | VM |
|--------|-----------|-----|
| Kernel | Shared with host | Own kernel |
| Boot time | Milliseconds | Seconds |
| Size | Megabytes | Gigabytes |
| Isolation | Process-level (namespaces) | Hardware-level (hypervisor) |
| Performance | Native | ~10-20% overhead |
| Density | 100s-1000s per host | 10s per host |
| Use case | Application isolation | Complete OS isolation |

**When to use containers:**
- Microservices architecture
- DevOps/CI-CD workflows
- Multi-tenant applications
- Scalable workloads

**When to use VMs:**
- Running Windows applications
- Needing OS-level isolation for security
- Legacy applications with OS dependencies
- Compliance requiring full OS separation

## Image vs Container

**Image** - Blueprint, static artifact
- Immutable layered filesystem
- Contains application code, runtime, dependencies
- Stored as layers (like a git history)
- Created once, never changes
- Identified by hash (SHA256 digest)

**Container** - Running instance, ephemeral
- Writable layer on top of image layers
- Running process (or set of processes)
- Created, modified, deleted
- Has lifecycle: created → running → stopped → deleted
- Identified by container ID

**Analogy:**
- Image = class definition in OOP
- Container = instance of that class

```bash
# Create an image (build phase)
docker build -t myapp:1.0 .
# Image is immutable, stored on disk

# Create and run a container (runtime phase)
docker run myapp:1.0
# Container is a running process with writable layer
# When stopped, the container layer is lost (ephemeral)

# Same image can run many containers
docker run myapp:1.0
docker run myapp:1.0
docker run myapp:1.0
# Three different containers, same image
```

## Common Misconceptions

### Misconception 1: "Containers are lightweight VMs"

**Reality:** Containers are processes with enforced OS-level boundaries. The entire operating system (kernel, modules, network stack) is shared with the host. A container is just a process whose namespace and resource limits are configured differently from other processes.

```bash
# Verify: containers share the kernel
docker run ubuntu uname -r
# 5.15.0-91-generic

# Same kernel on host
uname -r
# 5.15.0-91-generic
```

### Misconception 2: "Containers include an OS"

**Reality:** The container image contains filesystem artifacts (binaries, libraries) that expect a Linux OS, but the actual OS kernel is shared. When you see "Ubuntu" in a container, you're seeing a minimal filesystem that provides Ubuntu userspace tools - not Ubuntu's kernel.

### Misconception 3: "You need Docker to run containers"

**Reality:** Docker is one tool for managing containers. The actual container execution is done by `runc` (the OCI runtime). You could use podman, containerd, or other runtimes instead. Docker is a convenience layer.

```bash
# These all run containers:
docker run ubuntu echo hello      # Uses runc underneath
podman run ubuntu echo hello       # Alternative runtime
nerdctl run ubuntu echo hello      # Another wrapper
```

### Misconception 4: "Containers are automatically secure"

**Reality:** Containers provide isolation between applications, but they share the kernel. If the kernel has vulnerabilities, all containers are affected. Running containers as root negates most isolation benefits.

```bash
# Insecure (running as root):
docker run ubuntu id
# uid=0(root)

# Better (explicit non-root user):
docker run --user 1000 ubuntu id
# uid=1000
```

### Misconception 5: "A container can do anything a VM can do"

**Reality:** Containers cannot run different OSes (Windows, macOS kernels). They cannot load kernel modules. They cannot use raw disk access. They are restricted to application-level workloads on shared Linux.

## Namespaces: The Foundation of Container Isolation

Linux namespaces allow processes to have isolated views of system resources.

### PID Namespace

Each container has its own process ID numbering. Container's first process is always PID 1.

```bash
# On host
ps aux | head -5

# In container
docker run ubuntu ps aux
# Shows only processes inside container
# PID 1 is the sleep/init process

# Inside container, PID 1 is different from host PID
docker run -it ubuntu
# Inside: ps aux shows PID 1
# On host: docker ps shows container with host PID > 1000
```

**Why this matters:**
- Container init process (PID 1) must handle signals
- When PID 1 exits, container stops
- No access to host processes from inside container

### Network Namespace

Each container has its own network stack: IP, ports, routing table.

```bash
# Container has own IP
docker run --rm ubuntu hostname -I
# Shows container's IP (172.17.x.x usually)

# Host doesn't see container's internal IP
ifconfig
# Only sees host IPs

# Port isolation - two containers can use port 8080
docker run -d --name app1 ubuntu nc -l 8080
docker run -d --name app2 ubuntu nc -l 8080
# Both work because they're in different network namespaces
```

### Mount Namespace

Each container sees a different filesystem tree.

```bash
# Host sees /home, /var, /usr, /etc normally
ls /

# Container sees only what image provides + container layer
docker run ubuntu ls /
# Minimal filesystem, no /home, custom /etc
```

### UTS Namespace

Each container has its own hostname.

```bash
# Host hostname
hostname

# Container hostname (default is truncated container ID)
docker run ubuntu hostname

# Set custom hostname
docker run --hostname myapp ubuntu hostname
# Returns: myapp
```

### IPC Namespace

Isolated System V IPC objects (message queues, semaphores, shared memory).

```bash
# Two containers cannot access each other's shared memory
docker run --name app1 ubuntu sleep 1000
docker run --name app2 ubuntu sleep 1000
# app1 and app2 have different IPC namespaces
```

## cgroups: The Foundation of Resource Control

Control Groups enforce resource limits on processes.

### Memory Limit

Prevent container from exceeding memory allocation.

```bash
# Limit to 256MB
docker run --memory=256m ubuntu stress --vm 1 --vm-bytes 300m
# Process will be OOM killed when exceeding limit
```

### CPU Limit

Control CPU time available to container.

```bash
# Limit to 50% of one CPU core
docker run --cpus=0.5 ubuntu stress --cpu 4
# Process will be throttled, not killed

# Limit to specific CPU cores
docker run --cpuset-cpus=0,1 ubuntu stress --cpu 2
# Uses only CPUs 0 and 1
```

### I/O Limit

Control disk I/O rates.

```bash
# Limit disk read to 1MB/s
docker run --device-read-bps=/dev/sda:1mb ubuntu dd if=/dev/sda of=/dev/null bs=1m
```

## Kernel Capabilities: Fine-Grained Privilege Control

Containers should run with minimal capabilities (not as full root).

```bash
# See default capabilities
docker run ubuntu getcap /usr/bin/ping

# Container drops dangerous capabilities by default:
docker run ubuntu capsh --print
# CAP_SYS_ADMIN, CAP_SYS_BOOT, CAP_SYS_MODULE, etc. are dropped

# Verify you cannot load kernel modules
docker run ubuntu insmod mymodule.ko
# Error: operation not permitted
```

## The Container Startup Sequence

When you `docker run ubuntu sleep 1000`:

1. **Image loaded**: Docker Engine reads image layers from filesystem/registry
2. **Container created**: kernel creates namespaces, cgroup limits applied
3. **Filesystem mounted**: Union filesystem built, writable layer prepared
4. **Network configured**: Docker assigns IP, sets up port mappings
5. **Process exec'd**: `execve` system call runs the command in container
6. **Logging attached**: stdout/stderr redirected to Docker daemon
7. **Container waits**: Process runs until exit or docker stop

```bash
# Watch this sequence:
docker run -it ubuntu /bin/bash

# Inside the container:
ps aux
# Shows only processes inside (your shell and whatever you run)

exit
# Container stops because PID 1 (bash) exited
```

## Real-World Example: Understanding Container Behavior

```dockerfile
# Dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y python3
COPY app.py /app/
EXPOSE 8000
CMD ["python3", "/app/app.py"]
```

When you `docker run myapp`:

- Ubuntu's filesystem is immutable (read-only layers)
- Your app.py is in a read-only layer
- Container gets a writable layer
- Python process runs with:
  - Own PID namespace (is PID 1 inside)
  - Own network namespace (has own IP:8000)
  - Own mount namespace (sees /app/, /usr/bin/, etc. from image)
  - Memory limit if specified
  - CPU limits if specified
  - No CAP_SYS_ADMIN capability (cannot load kernel modules)
- When Python exits, container stops

This is fundamentally different from running `python3 /app/app.py` on a host - the isolation is enforced by the kernel.

## Production Insights

1. **Containers are ephemeral by design** - Don't store data in writable layer
2. **Shared kernel means shared vulnerability** - Kernel CVEs affect all containers
3. **Init process matters** - Ensure PID 1 can handle signals (SIGTERM)
4. **Resource limits prevent noisy neighbor** - Always set memory and CPU limits
5. **Namespace isolation has limits** - Don't rely on containers for strong security isolation
6. **Debug from outside container** - `docker exec` or `nsenter` to inspect running processes

---

## Practice: Exam Questions

1. **What is the fundamental difference between a VM and a container?**
   - A) Containers use less disk space
   - B) Containers share the kernel with the host; VMs have their own kernel
   - C) Containers are faster to boot
   - D) Containers cannot run operating systems

2. **When a container is created, which system call creates the isolated PID namespace?**
   - A) fork()
   - B) clone(CLONE_NEWPID)
   - C) unshare(CLONE_NEWPID)
   - D) exec()

3. **If you run two containers from the same image, are they sharing the same image layers?**
   - A) Yes, image layers are read-only and shared
   - B) No, each container gets its own copy of layers
   - C) Only if they run the same command
   - D) Only if they're on the same Docker network

4. **What happens to a container's writable layer when you stop the container?**
   - A) It's saved to the image
   - B) It persists in a Docker volume
   - C) It's preserved until you delete the container
   - D) It's discarded after the process exits

5. **Why is the concept of "PID 1" important in containers?**
   - A) It determines the container's network IP
   - B) It's the init process that must handle signals; when it exits, the container stops
   - C) It limits the number of processes in the container
   - D) It determines the container's resource limits

---

## Hands-On Labs

### Lab 1: Observe Namespace Isolation

**Objective:** See how containers have isolated views of system resources.

```bash
# Terminal 1: Start a long-running container
docker run -d --name isolated-test ubuntu sleep 3600
PID=$(docker inspect -f '{{.State.Pid}}' isolated-test)
echo "Container's host PID: $PID"

# Terminal 2: Check from host
ps aux | grep $PID
# Shows process on host

# Terminal 1: Inside container, PID is different
docker exec isolated-test ps aux
# Shows PID 1 for sleep

# Terminal 2: Check hostname isolation
docker exec isolated-test hostname
# Different from host

docker exec isolated-test hostname -I
# Container's isolated IP

# Terminal 1: Clean up
docker stop isolated-test
docker rm isolated-test
```

**What you're observing:**
- One process appears with different PIDs inside/outside
- Different namespaces provide isolated views
- No access to host processes from inside

### Lab 2: Resource Limit Enforcement

**Objective:** Demonstrate cgroup-enforced resource limits.

```bash
# Terminal 1: Run container with 256MB memory limit
docker run --name memory-test --memory=256m ubuntu \
  bash -c 'python3 -c "import sys; x = []; 
  [x.append([0]*1024*1024) for i in range(300)]"'

# Watch system logs (Terminal 2)
dmesg | tail -20
# You'll see "Memory cgroup out of memory" message

# Container exits with code 137 (OOM kill)
docker inspect -f '{{.State.ExitCode}}' memory-test
# Shows 137

# Clean up
docker rm memory-test

# Terminal 1: Run container with CPU limits
docker run --cpus=0.5 --name cpu-test ubuntu \
  stress --cpu 1 --timeout 10s

# Monitor CPU (Terminal 2)
docker stats cpu-test
# Shows CPU% around 50% (limited to 0.5 cores)

# Clean up
docker rm cpu-test
```

**What you're observing:**
- Memory limits are enforced by kernel (OOM killer)
- CPU limits throttle the process
- Cgroups provide resource isolation
- Processes cannot exceed their limits

---

## Failure Scenario: The Mysterious OOM Kill

**Scenario:**
You have a Python application container that occasionally dies with exit code 137. No error messages appear in your logs. The app seems fine locally.

**Clues:**
- Exit code 137 means SIGKILL (OOM killer)
- Container logs show normal operation until sudden stop
- It happens under load, not consistently
- Your local machine has 16GB RAM; production has 4GB

**Root cause:**
Container has no memory limit set. When load spikes, Python allocates memory unbounded, kernel runs out of RAM, and randomly kills containers.

**Debugging steps:**
```bash
# Check container limits
docker inspect myapp | grep -i memory
# MemoryLimit: 0 (unlimited - this is the problem)

# Check kernel messages
dmesg | grep -i oom
# Shows container processes being killed

# Solution: Set memory limit
docker run --memory=1g myapp
```

**Prevention:**
Always set resource limits in production. Make them explicit in docker-compose.yml and Kubernetes manifests.

---

Next: [Module 2: Docker Architecture](02-docker-architecture.md)
