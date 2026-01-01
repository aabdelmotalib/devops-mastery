# Module 3: Docker Images

## What is a Docker Image?

A Docker image is an immutable, layered filesystem and metadata that serves as a blueprint for creating containers.

**Key properties:**
- Immutable: once created, an image never changes
- Layered: built from stacked read-only filesystem layers
- Self-contained: includes all code, runtime, libraries needed
- Versioned: identified by repository name, tag, and digest
- Portable: runs on any system with Docker

Think of it as a frozen snapshot of an application's entire filesystem and configuration.

```bash
# Images have multiple identifiers
docker images
# Shows: REPOSITORY, TAG, IMAGE ID, SIZE, CREATED

# Three ways to reference same image:
docker run myapp:1.0              # Tag: myapp:1.0
docker run myapp:latest           # Tag: myapp:latest (might be 1.0)
docker run sha256:abc123...       # Digest: exact SHA256 hash
```

## Image Layers: The Foundation

An image is built from layers, stacked on top of each other.

```
┌─────────────────────────────────────────┐
│  Layer 3 (diff): app.py (new file)     │
├─────────────────────────────────────────┤
│  Layer 2 (diff): python3 binary added   │
├─────────────────────────────────────────┤
│  Layer 1 (diff): ubuntu base filesystem │
├─────────────────────────────────────────┤
│       (immutable, read-only)            │
└─────────────────────────────────────────┘
```

### How Layers Work

Each layer is a **diff** - only the changes made in that layer, not the entire filesystem.

```dockerfile
# Dockerfile shows layer creation
FROM ubuntu:22.04                          # Layer 1: 77 MB (ubuntu filesystem)
RUN apt-get update && apt-get install python3  # Layer 2: 150 MB (python3 added)
COPY app.py /app/app.py                   # Layer 3: 5 KB (app.py added)
```

When this image runs, Docker uses `overlay2` to union these layers:

1. Start with Layer 1: `/bin`, `/usr`, `/etc`, `/var`, etc. from ubuntu
2. Overlay Layer 2: Python binaries go into `/usr/bin` (union replaces files)
3. Overlay Layer 3: `app.py` placed in `/app/`
4. Result: single filesystem view containing ubuntu + python + app.py

```bash
# See this in practice
docker build -t demo:1.0 .

docker history demo:1.0
# Shows layers and sizes
# Layer 1: 77MB (FROM ubuntu)
# Layer 2: 150MB (RUN apt-get install python3)
# Layer 3: 5KB (COPY app.py)
# Total: ~227MB

# But actual disk usage is less if layers are reused
docker images demo
# SIZE column shows uncompressed size
```

### Layer Immutability

Once created, a layer never changes. This is fundamental.

```bash
# If you rebuild with same Dockerfile
docker build -t demo:2.0 .

# Docker checks if layers can be reused
# If FROM ubuntu:22.04 is in cache, reuses it
# If RUN command is identical, reuses it
# If files in COPY changed, creates new layer

# The old layers are never modified, only reused
```

## Union Filesystem: How Layers Combine

The union filesystem (overlay2) presents multiple layers as a single filesystem.

```
Container filesystem view (from inside container):
/
├── bin → from layer 1
├── usr
│   ├── bin → contains python3 from layer 2
│   ├── lib → python3 libs from layer 2
├── app → from layer 3
│   └── app.py
└── var → from layer 1

Physical storage: layers don't overlap, only differences stored
/var/lib/docker/overlay2/
├── layer1hash/diff/  (ubuntu files)
├── layer2hash/diff/  (only python3 binary and libs)
├── layer3hash/diff/  (only app.py)
```

### Key Property: Copy-on-Write (CoW)

When a container modifies a file from a read-only layer, the union filesystem copies it to the container's writable layer before modification.

```bash
# Container reads from read-only layer
cat /etc/hostname
# Reads from image layer

# Container modifies a file
echo "new-content" > /etc/hostname
# CoW: Copies /etc/hostname to container layer first
# Then modifies the copy
# Original in image layer unchanged

# When container stops, modification is lost
# Next container from same image gets original
```

This is why **data written to containers is ephemeral** - modifications are in the writable layer, which is deleted when the container is deleted.

## Dockerfile Anatomy

A Dockerfile is a sequence of commands that build an image layer by layer.

```dockerfile
# 1. Base image (required, first)
FROM ubuntu:22.04
# Creates the first layer from ubuntu image

# 2. Metadata (optional, doesn't create layer)
LABEL version="1.0" maintainer="team@example.com"
WORKDIR /app
ENV NODE_ENV=production

# 3. Run commands (each creates layer)
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git

# 4. Copy files (creates layer with new files)
COPY requirements.txt .
COPY app.py .

# 5. Expose ports (metadata, doesn't create layer)
EXPOSE 8000

# 6. Set entrypoint (metadata)
ENTRYPOINT ["python3"]
CMD ["app.py"]
```

### Which Instructions Create Layers?

Only instructions that modify the filesystem create layers:

**Creates layers:**
- `FROM` (base layer)
- `RUN` (execute command, results are layer)
- `COPY` (add files from build context)
- `ADD` (like COPY, but can extract archives)

**Metadata only (no layers):**
- `LABEL`
- `ENV`
- `EXPOSE`
- `WORKDIR`
- `USER`
- `CMD`
- `ENTRYPOINT`
- `HEALTHCHECK`

```dockerfile
# This creates 4 layers
FROM ubuntu:22.04           # Layer 1
RUN apt-get install curl    # Layer 2
COPY app.py /app/           # Layer 3
ENV NODE_ENV=production     # (metadata only)
CMD ["python3", "/app/app.py"]  # (metadata only)
```

### Image Configuration (Metadata)

Besides layers, images store metadata:

```bash
# View image metadata
docker inspect ubuntu:22.04 | python3 -m json.tool

# Key metadata:
{
  "Architecture": "amd64",
  "Os": "linux",
  "Config": {
    "Env": ["PATH=/usr/local/sbin:/usr/local/bin:..."],
    "Cmd": ["/bin/bash"],
    "WorkingDir": "",
    "Labels": {...},
    "User": "root"
  },
  "RootFS": {
    "Type": "layers",
    "Layers": ["sha256:layer1hash", "sha256:layer2hash", ...]
  }
}
```

When a container starts, Docker uses this metadata:
- Sets `ENV` variables in container process
- Sets `WORKDIR` for relative paths
- Uses `CMD`/`ENTRYPOINT` as default process
- Runs as `USER` (default: root - usually wrong)

## Building Images: How Docker Processes Dockerfiles

### The Build Process

```
1. Read Dockerfile
2. Parse instructions
3. For each instruction:
   a. Check build cache
   b. If in cache, reuse layer (fast)
   c. If not in cache, execute instruction (slow)
   d. Create layer with results
4. Tag image with repository:tag
5. Return image ID
```

### Build Cache: Why Rebuilds Are Fast

Docker caches layers to speed up builds.

```dockerfile
FROM ubuntu:22.04                    # Layer 1 - cached
RUN apt-get update && apt-get install python3  # Layer 2 - cached
COPY requirements.txt .              # Layer 3 - only if changed
RUN pip install -r requirements.txt  # Layer 4 - rerun if Layer 3 changed
COPY app.py /app/                   # Layer 5 - only if changed
```

Cache invalidation:

```bash
# Cache is valid when:
# - Same base image
# - Same instruction text
# - Same source files (for COPY/ADD)

# Cache is invalid when:
# - Base image changed
# - Instruction text changed
# - Files in COPY changed
# - Any previous layer was invalidated
```

**Cache invalidation is sequential and strict:**

```dockerfile
FROM ubuntu:22.04
RUN apt-get install python3         # Cached if previous layers unchanged
RUN pip install flask               # Only runs if previous line ran
COPY app.py /app/                   # If app.py changed, this invalidates
RUN pytest tests/                   # Reruns even if code didn't change
```

### Build Context

The build context is the directory sent to Docker daemon for building.

```bash
# Run from directory with Dockerfile
docker build -t myapp:1.0 .
# Context: everything in current directory

# Build context is sent to daemon
# This is why builds are slow with large directories

# Use .dockerignore to exclude files
echo "node_modules/" > .dockerignore
echo ".git/" >> .dockerignore

docker build -t myapp:1.0 .
# Faster because node_modules and .git aren't sent
```

**Important:** Docker sends the entire build context to the daemon.

```bash
# Bad: large build context
docker build -t myapp:1.0 /  # Sends entire filesystem!

# Good: small, focused context
docker build -t myapp:1.0 .  # From project directory
```

## Image Best Practices: Keep Images Small

### Principle: Minimal Images

Smaller images:
- Download faster (less bandwidth)
- Start faster (less disk I/O)
- Have less attack surface (fewer binaries/libraries)
- Reduce storage costs

### Practice 1: Multi-Stage Builds

Split building from running.

```dockerfile
# BAD: Single stage, large image
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y build-essential git gcc
COPY src/ /src/
RUN cd /src && make build
CMD ["/src/bin/app"]

# Result: image includes build tools (gcc, git, build-essential)
# Size: ~600MB (most for build tools that aren't needed at runtime)
```

```dockerfile
# GOOD: Multi-stage, small image
FROM ubuntu:22.04 AS builder
RUN apt-get update && apt-get install -y build-essential gcc
COPY src/ /src/
RUN cd /src && make build

# Now start fresh, copy only the binary
FROM ubuntu:22.04
COPY --from=builder /src/bin/app /usr/local/bin/
CMD ["app"]

# Result: Final image has only the binary and runtime libraries
# Size: ~150MB (build tools not included)
```

```bash
# See the difference
docker build -t badimage:1.0 -f Dockerfile.bad .
docker images badimage
# SIZE: 600MB

docker build -t goodimage:1.0 -f Dockerfile.good .
docker images goodimage
# SIZE: 150MB

# Same application, 4x smaller with multi-stage build
```

### Practice 2: Minimize Layers

Combine `RUN` commands to reduce layer count.

```dockerfile
# BAD: Multiple RUN commands, each creates layer
FROM ubuntu:22.04
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y python3
RUN apt-get install -y git
# 4 layers, each with full apt cache

# GOOD: Single RUN command
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    git
# 1 layer with final result

# Even better: clean up afterward
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    curl \
    python3 \
    git && \
    rm -rf /var/lib/apt/lists/*
# Removes package cache, reduces layer size
```

### Practice 3: Use Minimal Base Images

Choose smallest image that fits your needs.

```dockerfile
# Not minimal
FROM ubuntu:22.04           # 77 MB
RUN apt-get install python3
# Final: 230 MB

# Better
FROM python:3.11-slim       # 125 MB (python already included)
COPY requirements.txt .
RUN pip install -r requirements.txt
# Final: 180 MB (slightly larger but has everything)

# Best (when applicable)
FROM python:3.11-alpine     # 50 MB (minimal Linux)
RUN apk add --no-cache gcc  # Alpine's package manager
COPY requirements.txt .
RUN pip install -r requirements.txt
# Final: 150 MB (smallest, might have compatibility issues)
```

**Trade-off:** Alpine is smaller but can have compatibility issues with Python packages that need C extensions.

### Practice 4: Don't Run as Root

Security: run as non-root user.

```dockerfile
# BAD: Runs as root
FROM ubuntu:22.04
COPY app.py /app/
CMD ["python3", "/app/app.py"]
# Container runs as root (uid=0)

# GOOD: Create non-root user
FROM ubuntu:22.04
RUN useradd -m appuser
COPY app.py /app/
RUN chown appuser:appuser /app/
USER appuser
CMD ["python3", "/app/app.py"]
# Container runs as appuser (uid=1000)

# BETTER: Use official image's user
FROM python:3.11-slim
RUN useradd -m appuser
COPY app.py /app/
RUN chown appuser:appuser /app/
USER appuser
CMD ["python3", "/app/app.py"]
```

### Practice 5: Leverage Build Cache

Arrange Dockerfile to maximize cache reuse.

```dockerfile
# BAD: Invalidates cache too early
FROM ubuntu:22.04
COPY app.py /app/
RUN pip install -r requirements.txt

# If you modify app.py, the RUN layer is invalidated
# RUN command re-executes (slow) even if requirements unchanged

# GOOD: Dependencies before code
FROM ubuntu:22.04
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py /app/

# If you modify app.py, dependencies are cached
# Only the COPY layer is recreated (fast)
```

**Golden rule:** Put things that change frequently AFTER things that change rarely.

## Image Tagging and Versioning

### Tagging Strategy

```bash
# Tag syntax: [registry]/[repository]:[tag]
docker tag myimage:1.0 hub.docker.com/myuser/myimage:1.0

# Typical tags:
docker tag myapp:latest myapp:1.0            # Semantic versioning
docker tag myapp:latest myapp:v1.0           # v prefix (also good)
docker tag myapp:latest myapp:stable         # Semantic tag
docker tag myapp:latest myapp:2024-01-15     # Date tag
```

**Naming conventions:**

```bash
# Good: immutable, specific
docker build -t myapp:v1.0.5-build.123 .    # Includes build number
docker tag myapp:v1.0.5-build.123 myregistry.com/team/myapp:v1.0.5

# Less good: mutable, ambiguous
docker build -t myapp:latest .                # Latest changes frequently
docker tag myapp:latest myapp:stable          # "Stable" is subjective
```

### Version Tags

Use semantic versioning for releases:

```
v[MAJOR].[MINOR].[PATCH][-prerelease][+build]

Examples:
v1.0.0          # Release
v1.0.1          # Patch fix
v1.1.0          # Minor feature
v2.0.0          # Major breaking change
v1.1.0-rc1      # Release candidate
v1.1.0-beta.1   # Beta
```

### Latest vs Floating Tags

```bash
# latest: points to most recent build (mutable)
docker build -t myapp:latest .      # Latest now points here
docker build -t myapp:latest .      # Latest now points here (old one orphaned)

# v1.0: points to v1.0.X releases (floats, mutable)
docker tag myapp:v1.0.1 myapp:v1.0
docker tag myapp:v1.0.2 myapp:v1.0  # v1.0 now points to v1.0.2

# v1.0.1: immutable, never changes
docker build -t myapp:v1.0.1 .
# This version always means this exact build
```

**Best practice for production:**
- Deploy using specific version tags (v1.0.1)
- Never use `latest` in production
- Use floating tags (v1.0) for convenience only

## Image Digest: Immutable Identity

Every image has a unique SHA256 hash digest.

```bash
# View digest
docker images --digests
# Shows: REPOSITORY, TAG, DIGEST, IMAGE ID, SIZE

# Example output:
# ubuntu    22.04  sha256:abc123def456...  abc123  77MB

# Same image, multiple tags
docker pull ubuntu:22.04
docker pull ubuntu:latest
# If latest points to 22.04, they have same digest

# Reference by digest (immutable)
docker run ubuntu@sha256:abc123def456...
# Always this exact version, regardless of tags
```

**Why digests matter:**
- Tags can change (latest updated)
- Digests never change (immutable identity)
- For critical deployments, use digests

```dockerfile
# Less safe: latest can change
FROM ubuntu:latest
RUN apt-get install ...

# More safe: version-specific
FROM ubuntu:22.04
RUN apt-get install ...

# Most safe: digest-specific
FROM ubuntu@sha256:abc123def456...
RUN apt-get install ...
```

## Image Compression and Distribution

### How Images Are Compressed

Images are compressed with gzip when pushed to registries.

```bash
# Build image (uncompressed on disk)
docker build -t myapp:1.0 .
ls -la /var/lib/docker/overlay2/
# Uncompressed layers on disk

# Push to registry (compressed)
docker push myregistry.com/myapp:1.0
# Docker compresses layers with gzip before upload

# Pull from registry (compressed)
docker pull myregistry.com/myapp:1.0
# Docker downloads compressed, then decompresses
```

**Compression rates:**
- Text files: 10-50% of original
- Binaries: 30-60% of original
- Overall image: ~30-50% of uncompressed

```bash
# See compression in action
docker images myapp:1.0
# Shows uncompressed size: 500MB

# Check registry storage size (usually much smaller)
# (Requires registry admin access)
# Actual stored: ~200MB (compressed)
```

## Image Verification: Trust and Integrity

### Image Signing

Sign images to verify they haven't been tampered with.

```bash
# Docker Content Trust (DCT) signs images
export DOCKER_CONTENT_TRUST=1
docker push myregistry.com/myapp:1.0
# Requires signing key

# Pull signed image
export DOCKER_CONTENT_TRUST=1
docker pull myregistry.com/myapp:1.0
# Verifies signature before pulling
```

**Note:** DCT is less common now. Sigstore is the modern approach.

### Scanning for Vulnerabilities

Before pushing, scan images for known vulnerabilities.

```bash
# Docker Scout (built-in)
docker scout cves myapp:1.0
# Shows CVEs in image layers

# Trivy (external tool)
trivy image myapp:1.0
# Scans and reports vulnerabilities

# Grype (Anchore tool)
grype myapp:1.0
# Another vulnerability scanner
```

## Real-World Example: Production Web App Image

```dockerfile
# Multi-stage build for Node.js app

# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /build
COPY package*.json ./
RUN npm ci --only=production  # Install deps only
COPY . .
RUN npm run build             # Compile TypeScript, bundle
RUN npm prune --production    # Remove dev dependencies

# Stage 2: Runtime (minimal)
FROM node:18-alpine
LABEL version="1.0" maintainer="devops@example.com"

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

WORKDIR /app

# Copy only built artifacts and node_modules
COPY --from=builder --chown=nodejs:nodejs /build/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /build/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /build/package.json ./

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "require('http').get('http://localhost:3000/health', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

USER nodejs
EXPOSE 3000
CMD ["node", "dist/index.js"]
```

Build and push:

```bash
# Build with version tag
docker build -t myapp:v1.0.0 -f Dockerfile.prod .

# Verify image size
docker images myapp:v1.0.0
# SIZE: ~250MB (Node app with dependencies)

# Scan for vulnerabilities
docker scout cves myapp:v1.0.0

# Tag for registry
docker tag myapp:v1.0.0 myregistry.com/team/myapp:v1.0.0

# Push to registry
docker push myregistry.com/team/myapp:v1.0.0
```

## Production Insights

1. **Image immutability is a feature** - Same image runs identically everywhere
2. **Layers enable efficient distribution** - Only changed layers transfer
3. **Build cache speeds development** - Strategic Dockerfile arrangement matters
4. **Small images reduce risk** - Fewer binaries = fewer vulnerabilities
5. **Specific versions over latest** - latest is convenient, versions are reliable
6. **Non-root is mandatory** - Always specify USER in production images

---

## Practice: Exam Questions

1. **What is the primary difference between a Docker image layer and the final image?**
   - A) Layers are compressed; images are uncompressed
   - B) A layer is a difference (delta); the image is the union of all layers
   - C) Layers are read-write; images are read-only
   - D) There is no difference; they are the same thing

2. **When you modify a file in a running container that exists in an image layer, what happens?**
   - A) The image layer is modified
   - B) Copy-on-write: file is copied to container's writable layer, then modified
   - C) Modification is prevented (read-only)
   - D) Modification is written back to the image

3. **Which Dockerfile instruction creates a new layer?**
   - A) LABEL
   - B) ENV
   - C) RUN
   - D) EXPOSE

4. **In a multi-stage build, what is the primary advantage?**
   - A) Faster builds
   - B) Smaller final image (build tools not included)
   - C) Easier to read Dockerfile
   - D) Automatic caching

5. **How can you maximize Docker's build cache?**
   - A) Use smaller base images
   - B) Combine all RUN commands into one
   - C) Place frequently-changing files AFTER less-frequently-changing files
   - D) Use latest tags

6. **What is a Docker image digest?**
   - A) A summary of the Dockerfile commands
   - B) A SHA256 hash that uniquely identifies an image version
   - C) The compressed size of an image
   - D) A registry index

---

## Hands-On Labs

### Lab 1: Build Images and Observe Layer Creation

**Objective:** See how Dockerfile commands create layers.

```bash
# Create simple app
mkdir docker-lab && cd docker-lab
cat > app.py << 'EOF'
import time
while True:
    print("Hello from container")
    time.sleep(1)
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
RUN apt-get update && apt-get install -y curl
RUN apt-get install -y wget
COPY app.py /app/app.py
EXPOSE 5000
CMD ["python3", "/app/app.py"]
EOF

# Build first version
docker build -t myapp:v1.0 .
docker history myapp:v1.0
# Shows each layer with its size and command

# Modify app
echo "print('Modified')" >> app.py

# Build again
docker build -t myapp:v1.1 .
# Cache is used for first 3 layers
# Only COPY layer is recreated (app.py changed)

# Compare histories
docker history myapp:v1.0
docker history myapp:v1.1
# Same layers except COPY and everything after

# Verify cache reuse (timing)
# First build: slow
# Second build: fast (layers cached)
time docker build -t myapp:v1.0 .
time docker build -t myapp:v1.0 .  # Much faster
```

**What you're observing:**
- Each RUN/COPY/ADD command creates a layer
- Layers are cached and reused
- Cache invalidation is sequential (one change invalidates subsequent layers)

### Lab 2: Multi-Stage Build

**Objective:** Understand size reduction with multi-stage builds.

```bash
# Create Go app (small compiled binary)
cat > main.go << 'EOF'
package main
import (
    "fmt"
    "net/http"
)
func main() {
    http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Hello\n")
    })
    http.ListenAndServe(":8080", nil)
}
EOF

# Single-stage build (not ideal)
cat > Dockerfile.single << 'EOF'
FROM golang:1.20
WORKDIR /src
COPY main.go .
RUN go build -o app main.go
EXPOSE 8080
CMD ["./app"]
EOF

# Multi-stage build (optimized)
cat > Dockerfile.multi << 'EOF'
FROM golang:1.20 AS builder
WORKDIR /src
COPY main.go .
RUN go build -o app main.go

FROM alpine:3.18
COPY --from=builder /src/app /app
EXPOSE 8080
CMD ["/app"]
EOF

# Build both
docker build -t demo:single -f Dockerfile.single .
docker build -t demo:multi -f Dockerfile.multi .

# Compare sizes
docker images demo
# Single: ~900MB (includes golang toolchain)
# Multi: ~15MB (only the binary)

# Both produce same app output
docker run --rm demo:single    # Works
docker run --rm demo:multi     # Works, much smaller
```

**What you're observing:**
- Multi-stage separates build from runtime
- Final image includes only what's needed
- Dramatic size reduction (60x in this case)

---

## Failure Scenario: Layer Cache Invalidation Gone Wrong

**Scenario:**
Your team's build pipeline is getting slower each day. A build that took 2 minutes now takes 15 minutes. Meanwhile, a refactor to the Dockerfile didn't improve speed - it made it worse.

**Original Dockerfile:**
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
CMD ["python3", "app.py"]
```

**"Refactored" Dockerfile:**
```dockerfile
FROM python:3.11-slim
COPY . .                          # Copy everything first!
RUN pip install -r requirements.txt
CMD ["python3", "app.py"]
```

**Problem:**
The refactored version invalidates the pip layer when ANY file changes (including .git, test files, etc.). Now every commit causes a full pip reinstall (slow).

**Debugging:**
```bash
# Check build time with verbose output
docker build --progress=plain -t app . 2>&1 | grep -i "run pip"

# Original: Uses cache, instant
# Refactored: Rebuilds, 5+ minutes
```

**Solution:**
Return to careful COPY ordering. Copy dependencies before code.

```dockerfile
FROM python:3.11-slim
COPY requirements.txt .           # Rarely changes
RUN pip install -r requirements.txt  # Only runs if requirements.txt changed
COPY . .                           # Changes frequently
CMD ["python3", "app.py"]          # Doesn't create layer
```

**Learning point:**
Cache invalidation is about file dependencies. Know what changes frequently and order your Dockerfile accordingly.

---

Next: [Module 4: Docker Containers](04-docker-containers.md)
