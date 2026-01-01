# Module 6: Docker Volumes & Storage

## The Problem: Ephemeral Container Filesystems

Container writable layers are ephemeral - deleted when the container is deleted.

```bash
# Create data inside container
docker run ubuntu bash -c 'echo "important data" > /data.txt'

# Stop and delete container
docker rm <container_id>

# Data is gone forever
```

This is by design. Containers should be ephemeral. But applications need to persist data.

## Storage Solutions: Three Approaches

Docker provides three mechanisms for persistent storage:

1. **Volumes**: Managed by Docker, best for most use cases
2. **Bind mounts**: Mount host directory, good for development
3. **tmpfs mounts**: In-memory storage, temporary only

## Volumes: Docker-Managed Storage

A volume is a directory managed by Docker, outside the container filesystem.

```
Container (isolated filesystem)
    │
    └─ /data (mount point) ──→ Volume (on host disk)
                               /var/lib/docker/volumes/myvol/data/
                               (managed by Docker)
```

### Creating and Using Volumes

```bash
# Create named volume
docker volume create mydata

# List volumes
docker volume ls

# Run container with volume
docker run -v mydata:/data ubuntu ls /data
# /data inside container is the volume

# Create file in volume
docker run -v mydata:/data ubuntu bash -c 'echo "test" > /data/file.txt'

# Volume persists after container deletion
docker run -v mydata:/data ubuntu cat /data/file.txt
# Still shows "test"

# Delete volume
docker volume rm mydata
```

### Volume Properties

**Volumes are independent of containers:**
```bash
# Create volume
docker volume create database

# Start container with volume
docker run -d -v database:/var/lib/postgresql ubuntu sleep 1000

# Container ID: abc123
docker ps
# Container abc123 uses database volume

# Stop and delete container
docker stop abc123
docker rm abc123

# Volume still exists!
docker volume ls | grep database
# Still there

# Another container can use same volume
docker run -v database:/var/lib/postgresql ubuntu ls /var/lib/postgresql
# Sees same data
```

**Volumes are writable from containers:**
```bash
# Container can read and write
docker run -v mydata:/data ubuntu bash -c 'echo "new data" >> /data/file.txt'
docker run -v mydata:/data ubuntu cat /data/file.txt
# Shows "new data" appended
```

**Volumes can be read-only:**
```bash
# Prevent container from modifying volume
docker run -v mydata:/data:ro ubuntu bash -c 'echo "test" > /data/file.txt'
# Error: Read-only file system

# Container can read but not write
docker run -v mydata:/data:ro ubuntu cat /data/file.txt
# Works
```

## Bind Mounts: Mount Host Directories

Mount a directory from the host into the container.

```
Host filesystem                Container filesystem
/home/user/project       →         /app
(on host disk)           (mount)   (path in container)
```

### Using Bind Mounts

```bash
# Mount host directory into container
docker run -v /home/user/project:/app ubuntu ls /app
# /app in container shows /home/user/project from host

# Works bidirectionally
docker run -v /home/user/project:/app ubuntu bash -c 'echo "from container" > /app/file.txt'

# Check on host
cat /home/user/project/file.txt
# Shows "from container"

# Modify on host
echo "from host" >> /home/user/project/file.txt

# Container sees change
docker run -v /home/user/project:/app ubuntu cat /app/file.txt
# Shows "from container\nfrom host"
```

### Bind Mount Syntax

```bash
# Full syntax
docker run -v /host/path:/container/path:mode ubuntu

# Where mode is:
# (default): read-write
# ro: read-only
# z: shared label
# Z: private label

# Examples:
docker run -v /home/user/src:/app ubuntu          # r-w
docker run -v /home/user/src:/app:ro ubuntu       # r-o
docker run -v /home/user/data:/data:z ubuntu      # r-w, shared
```

## Volumes vs Bind Mounts

| Aspect | Volume | Bind Mount |
|--------|--------|-----------|
| Management | Docker-managed | Host-managed |
| Location | /var/lib/docker/volumes/ | Anywhere on host |
| Performance | Good | Good |
| Use case | Production data | Development, config |
| Permissions | Docker controls | Host controls |
| Backup | Built-in tooling | Manual |
| Removal | `docker volume rm` | Manual delete |

**When to use volumes:**
- Database storage (MySQL, PostgreSQL)
- Persistent data (logs, user uploads)
- Production environments
- Multi-container sharing

**When to use bind mounts:**
- Development (live code changes)
- Configuration files
- Testing
- Sharing host files with container

## Volume Drivers: Advanced Storage

By default, volumes use `local` driver (stores on host). Custom drivers enable different backends.

```bash
# Create volume with different driver
docker volume create --driver nfs \
  --opt o=addr=10.0.0.2,vers=4,soft,timeo=180,bg,tcp \
  --opt device=:/nfsshare \
  nfs_volume

# Run with NFS volume (stored on remote server)
docker run -v nfs_volume:/data ubuntu ls /data
# /data actually stored on NFS server
```

**Common drivers:**
- `local`: Host filesystem (default)
- `nfs`: Network File System
- `glusterfs`: Distributed filesystem
- `flocker`: Container volume orchestration

## Volume Permissions and Ownership

A common issue: volume files have wrong ownership/permissions.

```bash
# Create volume
docker volume create appdata

# Container writes as root (uid=0)
docker run -v appdata:/data -u root ubuntu bash -c 'echo "data" > /data/file.txt'

# Check ownership on host
docker run -v appdata:/data ubuntu ls -la /data
# Shows: root:root

# Host user can't modify it
echo "more data" >> /var/lib/docker/volumes/appdata/_data/file.txt
# Permission denied

# Solution: Container should run as non-root
docker run -v appdata:/data -u 1000 ubuntu bash -c 'echo "data" > /data/file.txt'

# Or: Docker manages permissions with :Z flag
docker run -v appdata:/data:Z ubuntu bash -c 'echo "data" > /data/file.txt'
```

## tmpfs Mounts: Temporary Storage

Temporary storage in memory, lost when container stops.

```bash
# Create tmpfs mount
docker run --tmpfs /tmp ubuntu df /tmp
# Shows /tmp is mounted in RAM

docker run --tmpfs /tmp:size=1g,noexec ubuntu mount | grep /tmp
# /tmp: 1GB, noexec (can't run executables)

# Data is lost when container stops
docker run --tmpfs /tmp ubuntu bash -c 'echo "temp" > /tmp/file.txt'
# File only exists in this container's RAM

# Another container doesn't see it
docker run --tmpfs /tmp ubuntu cat /tmp/file.txt
# File not found
```

**Use cases:**
- Temporary build artifacts
- Cache files
- Session storage (Redis instead)
- Secrets (in memory, not on disk)

## Backup and Restoration

### Backup Volume Data

```bash
# Create backup of volume
docker run --rm \
  -v mydata:/data \
  -v $(pwd)/backup:/backup \
  ubuntu tar czf /backup/mydata.tar.gz -C /data .

# Creates: backup/mydata.tar.gz on host
```

### Restore Volume Data

```bash
# Create new volume
docker volume create restored_data

# Restore from backup
docker run --rm \
  -v restored_data:/data \
  -v $(pwd)/backup:/backup \
  ubuntu tar xzf /backup/mydata.tar.gz -C /data

# Volume now contains restored data
```

### Database Backups

```bash
# Backup PostgreSQL
docker run --rm \
  -v postgres_data:/var/lib/postgresql/data \
  postgres pg_dump -U postgres > backup.sql

# Restore PostgreSQL
docker run --rm \
  -v postgres_data:/var/lib/postgresql/data \
  postgres psql -U postgres < backup.sql
```

## Real-World Example: Multi-Container Application with Storage

```docker-compose
version: '3.8'

services:
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_PASSWORD: secretpassword
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  app:
    image: myapp:1.0
    volumes:
      - app_logs:/var/log/myapp
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres:secretpassword@postgres:5432/mydb
      REDIS_URL: redis://redis:6379

volumes:
  postgres_data:
  redis_data:
  app_logs:
```

Key patterns:
- Each service has its own volume for persistent data
- Volumes are created and managed by Docker
- Services communicate via network, not volumes
- Logs stored in separate volume

## Storage Best Practices

1. **Use named volumes in production** - `docker volume create mydata`
2. **Never run as root** - Use `USER` in Dockerfile, specify `-u` in docker run
3. **Make filesystem read-only when possible** - Use `:ro` flag
4. **Separate logs from data** - Use multiple volumes
5. **Plan for backup and restore** - Don't rely on only one copy
6. **Monitor volume usage** - Full volumes cause failures
7. **Clean up unused volumes** - `docker volume prune`

---

## Practice: Exam Questions

1. **What happens to data in a container's writable layer when the container is deleted?**
   - A) It's automatically backed up
   - B) It's moved to a volume
   - C) It's deleted
   - D) It persists in the image

2. **Which storage mechanism is best for database persistence?**
   - A) Container writable layer
   - B) Volumes
   - C) Bind mounts
   - D) tmpfs

3. **What is the key difference between volumes and bind mounts?**
   - A) Volumes are faster
   - B) Volumes are Docker-managed; bind mounts are host directories
   - C) Bind mounts can't be shared
   - D) Volumes only work with networks

4. **How do you prevent a container from modifying a volume?**
   - A) Delete the volume before starting container
   - B) Use `:ro` flag in volume mount
   - C) Use tmpfs instead
   - D) Set volume ownership to root

5. **What is tmpfs storage used for?**
   - A) Long-term persistence
   - B) Sharing between containers
   - C) Temporary in-memory storage
   - D) Backing up container data

---

## Hands-On Labs

### Lab 1: Volumes vs Bind Mounts

**Objective:** Experience the difference between storage mechanisms.

```bash
# Create data directory on host
mkdir -p /tmp/host-data
echo "host file" > /tmp/host-data/file.txt

# Create volume
docker volume create lab-vol

# Bind mount approach
docker run -v /tmp/host-data:/app/data ubuntu ls /app/data
# Shows: file.txt (from host)

# Modify in container
docker run -v /tmp/host-data:/app/data ubuntu bash -c 'echo "modified" >> /app/data/file.txt'

# Check on host
cat /tmp/host-data/file.txt
# Shows: "host file\nmodified"

# Volume approach
docker run -v lab-vol:/data ubuntu bash -c 'echo "vol-file" > /data/file.txt'

# Data only exists in volume
docker run -v lab-vol:/data ubuntu cat /data/file.txt
# Shows: "vol-file"

# On host, can't directly access
cat /var/lib/docker/volumes/lab-vol/_data/file.txt
# Requires sudo (owned by Docker)

# Clean up
docker volume rm lab-vol
rm -rf /tmp/host-data
```

**What you're observing:**
- Bind mounts provide bidirectional access to host
- Volumes are isolated from host filesystem
- Different use cases for each

### Lab 2: Volume Persistence and Sharing

**Objective:** Verify volumes persist across containers.

```bash
# Create volume
docker volume create database

# Container 1: Write data
docker run -d --name writer -v database:/db ubuntu bash -c 'for i in {1..100}; do echo "line $i" >> /db/data.txt; done; sleep 1000'

# Monitor progress
sleep 5
docker exec writer wc -l /db/data.txt
# Shows ~100 lines (or in progress)

# Container 2: Read same volume simultaneously
docker run -d --name reader -v database:/db ubuntu bash -c 'watch -n 1 wc -l /db/data.txt'

# Check from reader
docker logs reader
# Shows increasing line count

# Delete writer container
docker stop writer
docker rm writer

# Reader can still access volume
docker exec reader cat /db/data.txt | head -5
# Still shows data

# Delete reader, recreate it
docker stop reader
docker rm reader

docker run -v database:/db --name reader2 ubuntu wc -l /db/data.txt
# Same data (volume persisted)

# Clean up
docker rm reader2
docker volume rm database
```

**What you're observing:**
- Volume persists after container deletion
- Multiple containers can share same volume
- Data is not tied to any container

---

## Failure Scenario: Permission Denied on Volume Files

**Scenario:**
Your application works fine in development but fails in production with "Permission denied" errors when accessing volume files.

**Symptoms:**
```
Error: Cannot write to /data/app.log
Error: Permission denied (os.error 13)
```

**Root cause:**
Container running as root (uid=0) creates files. Host user (uid=1000) can't access them.

```bash
# Container as root creates file
docker run -u root -v mydata:/data ubuntu bash -c 'echo "log" > /data/app.log'

# Check ownership
docker run -v mydata:/data ubuntu ls -la /data
# Shows: root:root

# Host user tries to access
cat /var/lib/docker/volumes/mydata/_data/app.log
# Permission denied
```

**Solutions:**

Option 1: Run container as non-root:
```bash
docker run -u 1000 -v mydata:/data ubuntu bash -c 'echo "log" > /data/app.log'

# File now owned by uid 1000
docker run -v mydata:/data ubuntu ls -la /data
# Shows: 1000:1000
```

Option 2: Use Z flag (SELinux relabeling):
```bash
docker run -v mydata:/data:Z ubuntu bash -c 'echo "log" > /data/app.log'
# Docker relabels volume for shared access
```

Option 3: Fix permissions after container creation:
```bash
docker run -v mydata:/data ubuntu chown 1000:1000 /data
```

**Prevention:**
Always run containers as non-root. Specify USER in Dockerfile.

---

Next: [Module 7: Docker Compose](07-docker-compose.md)
