# Module 9: Docker in CI/CD

## Why Docker in Pipelines

Docker solves CI/CD problems:

1. **Reproducibility**: Same image runs identically on dev, staging, production
2. **Isolation**: Tests don't interfere with each other
3. **Speed**: Cached layers mean fast rebuilds
4. **Artifact**: Image is the immutable artifact deployed to production
5. **Consistency**: Build artifacts don't depend on CI runner's OS/tools

Traditional CI/CD without Docker:
```
Code → Build (install deps on CI) → Test (on CI) → Deploy (hope it works)
       ↑                            ↑              ↑
   Different tools          Different environment   Fragile handoff
```

With Docker:
```
Code → Build image → Test image → Deploy image
       ↑                           ↑
   Same everywhere          Same everywhere
```

## Building Images in CI/CD

### Basic Pipeline

```yaml
# GitHub Actions example
name: Build and Test

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      # Build image
      - name: Build Docker image
        run: docker build -t myapp:${{ github.sha }} .

      # Test image
      - name: Run tests in container
        run: docker run myapp:${{ github.sha }} pytest

      # Push to registry
      - name: Push to registry
        run: |
          docker login -u ${{ secrets.REGISTRY_USER }} \
            -p ${{ secrets.REGISTRY_PASS }} myregistry.com
          docker tag myapp:${{ github.sha }} \
            myregistry.com/myapp:${{ github.sha }}
          docker push myregistry.com/myapp:${{ github.sha }}
```

### Build Context in CI/CD

CI/CD should send minimal build context.

```bash
# Bad: sends entire repository
docker build -t myapp .
# Build context: .git/, node_modules/, test/fixtures/, ...
# Slow and unnecessary

# Good: use .dockerignore
# .dockerignore
.git
.gitignore
node_modules
test/fixtures
.env
*.log
```

```bash
# Now build is faster
docker build -t myapp .
# Smaller context, quicker to daemon
```

## Image Tagging Strategy for CI/CD

### Version Tags

Use meaningful, immutable tags.

```yaml
# On every commit
docker build -t myapp:${{ github.sha }} .
# Tag: commit hash (unique, immutable)

# On release/tag
docker build -t myapp:v1.0.0 .
docker tag myapp:v1.0.0 myapp:latest
# Tag: semantic version + latest pointer

# On branch
docker build -t myapp:main .
# Tag: branch name (for tracking current main)
```

**Recommended tagging scheme:**

```bash
# In CI/CD pipeline:

# Always: commit SHA (never changes)
docker tag myapp:$commit_sha myregistry.com/myapp:$commit_sha

# On merge to main: also tag as latest
if [ "$BRANCH" = "main" ]; then
  docker tag myapp:$commit_sha myregistry.com/myapp:latest
fi

# On version release: tag as version
if [ "$TAG" = "v*" ]; then
  docker tag myapp:$commit_sha myregistry.com/myapp:$TAG
fi

# Optional: branch name for debugging
docker tag myapp:$commit_sha myregistry.com/myapp:$BRANCH-latest
```

### Never Use Mutable Tags in Production

```bash
# BAD for production deployment
docker run myregistry.com/myapp:latest
# latest can change, different runs get different images

# GOOD for production deployment
docker run myregistry.com/myapp:v1.0.5
# Immutable, always the same image
```

## Caching in CI/CD

Docker's layer cache speeds rebuilds.

### Default Behavior

```bash
# First build: slow (all layers built)
docker build -t myapp:1.0 .
# Result: image with 5 layers

# Second build with no changes: fast (layers cached)
docker build -t myapp:1.0 .
# Reuses all 5 layers

# Second build with code change: medium (partial cache)
docker build -t myapp:1.0 .
# Reuses base, deps, but rebuilds app layer
```

### Cache Invalidation in CI/CD

The CI/CD environment is typically ephemeral (new runner each time).

```bash
# Problem: No cache in CI/CD by default
docker build -t myapp:1.0 .  # No cache from previous run
# Slow rebuild every time

# Solution 1: Use external cache registry
docker build \
  --cache-from myregistry.com/myapp:latest \
  -t myapp:1.0 .
# Pulls previous image layers as cache

# Solution 2: Docker BuildKit with inline cache
docker buildx build \
  --cache-from=type=registry,ref=myregistry.com/myapp:latest \
  --cache-to=type=registry,ref=myregistry.com/myapp:cache,mode=max \
  -t myapp:1.0 .
```

### Buildkit: Modern Build Engine

BuildKit is Docker's improved builder.

```bash
# Enable buildkit
export DOCKER_BUILDKIT=1

# Use in build
docker build -t myapp:1.0 .
# Faster, better caching, better parallelization

# With compose
DOCKER_BUILDKIT=1 docker-compose build
```

## Testing in CI/CD

### Unit Tests in Container

```bash
# Run tests in built image
docker run myapp:$sha pytest

# Or with custom test runner
docker run myapp:$sha npm test

# With volume for test reports
docker run \
  -v $(pwd)/reports:/app/reports \
  myapp:$sha \
  pytest --junit-xml=/app/reports/junit.xml
```

### Integration Tests with docker-compose

```bash
# Start services
docker-compose -f docker-compose.test.yml up -d

# Run integration tests
docker-compose -f docker-compose.test.yml run tests pytest

# Clean up
docker-compose -f docker-compose.test.yml down
```

docker-compose.test.yml:
```yaml
version: '3.8'
services:
  database:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: test
  
  cache:
    image: redis:7-alpine
  
  app:
    build: .
    depends_on:
      - database
      - cache
  
  tests:
    build:
      context: .
      dockerfile: Dockerfile.test
    depends_on:
      - app
```

## Scanning in CI/CD

### Vulnerability Scanning

Fail build if image has vulnerabilities.

```bash
# Scan and fail if critical vulnerabilities found
docker scout cves $image --format sarif > scan_results.json

if grep -q '"level": "critical"' scan_results.json; then
  echo "Critical vulnerabilities found"
  exit 1
fi
```

### Security Best Practices Scanning

```bash
# Using Trivy
trivy image --severity HIGH,CRITICAL myimage:$sha

# Using Grype
grype myimage:$sha -f sarif -o scan_results.sarif
```

## Pushing to Registries

### Authentication

```bash
# Docker Hub
docker login -u username -p password

# Private registry
docker login -u username -p password myregistry.com

# Using auth file (in CI/CD)
echo $REGISTRY_PASSWORD | docker login -u $REGISTRY_USER \
  --password-stdin myregistry.com

# With credentials helper
echo '{"auths":{"myregistry.com":{"auth":"..."}}}' > ~/.docker/config.json
```

### Pushing Images

```bash
# Tag for registry
docker tag myapp:local myregistry.com/team/myapp:v1.0

# Push
docker push myregistry.com/team/myapp:v1.0

# Push multiple tags
docker push myregistry.com/team/myapp:latest
docker push myregistry.com/team/myapp:v1.0
docker push myregistry.com/team/myapp:main

# Or use buildx for multi-platform builds and push
docker buildx build --push \
  -t myregistry.com/team/myapp:v1.0 .
```

## Practical CI/CD Pipeline

### Full GitHub Actions Example

```yaml
name: Build, Test, Push

on:
  push:
    branches: [main, develop]
    tags: [v*]
  pull_request:
    branches: [main]

env:
  REGISTRY: myregistry.com
  IMAGE_NAME: team/myapp

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
      packages: write
    
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}
    
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Log in to registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-
      
      - name: Build and push
        id: build
        uses: docker/build-push-action@v4
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
          cache-to: type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache,mode=max
      
      - name: Run tests
        run: |
          docker run --rm \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
            pytest -v
      
      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'
```

## Deployment from CI/CD

### Updating Production

```bash
# After image is pushed to registry:

# Update service to new image
docker pull myregistry.com/myapp:v1.0.5
docker stop myapp
docker rm myapp
docker run -d \
  --name myapp \
  --restart=unless-stopped \
  myregistry.com/myapp:v1.0.5

# Or with docker-compose
docker-compose pull
docker-compose up -d

# Or with orchestration (Kubernetes)
kubectl set image deployment/myapp \
  app=myregistry.com/myapp:v1.0.5
```

### Blue-Green Deployment

```bash
# Current: running version 1.0
docker ps | grep myapp
# myapp-v1.0 running

# Deploy version 1.1
docker run -d --name myapp-v1.1 myregistry.com/myapp:v1.1

# Test new version
curl localhost:8001/health  # new version on different port
# Success

# Switch traffic
docker stop myapp-v1.0
docker rename myapp-v1.1 myapp-v1.1-backup
docker rename myapp-v1.0 myapp-v1.0-backup
# New version is now primary

# Keep old running for rollback
docker start myapp-v1.0-backup
# Rollback: traffic back to v1.0
```

---

## Practice: Exam Questions

1. **What is the primary advantage of using Docker in CI/CD?**
   - A) Faster compilation
   - B) Same image runs identically everywhere (dev, test, prod)
   - C) Reduces storage costs
   - D) Enables parallel builds

2. **Why should you tag images by commit SHA in CI/CD?**
   - A) To make images smaller
   - B) To create immutable, traceable artifacts
   - C) To speed up builds
   - D) Commit SHAs are required by Docker

3. **What is the disadvantage of using `latest` tag in production?**
   - A) It's slower than version tags
   - B) It can change, causing unpredictable deployments
   - C) It requires more storage
   - D) It prevents caching

4. **How do you use Docker layer cache in ephemeral CI/CD environments?**
   - A) Cache is never available in CI/CD
   - B) Enable DOCKER_BUILDKIT
   - C) Pull previous image from registry as cache source
   - D) Copy .docker directory between runs

5. **What should be done to an image after scanning finds vulnerabilities?**
   - A) Always deploy anyway
   - B) Fail the build or require manual approval
   - C) Ignore and redeploy
   - D) Increase logging

---

## Hands-On Labs

### Lab 1: CI/CD Pipeline Simulation

**Objective:** Simulate a CI/CD build process locally.

```bash
mkdir ci-demo && cd ci-demo

# Create simple app
cat > app.py << 'EOF'
print("Hello from CI/CD")
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
COPY app.py /app/
WORKDIR /app
CMD ["python3", "app.py"]
EOF

# Create test script
cat > test.sh << 'EOF'
#!/bin/bash
set -e
echo "Running tests..."
python3 -m py_compile app.py
echo "Tests passed!"
EOF
chmod +x test.sh

# Simulate CI/CD pipeline
simulate_ci_cd() {
  local commit_sha="$1"
  local branch="$2"
  
  echo "=== Simulating CI/CD ==="
  echo "Commit: $commit_sha"
  echo "Branch: $branch"
  
  # Step 1: Build
  echo -e "\n[1] Building image..."
  docker build -t myapp:$commit_sha .
  
  # Step 2: Test
  echo -e "\n[2] Running tests..."
  docker run --rm myapp:$commit_sha /bin/bash -c 'python3 -m py_compile /app/app.py'
  
  # Step 3: Tag
  echo -e "\n[3] Tagging..."
  if [ "$branch" = "main" ]; then
    docker tag myapp:$commit_sha myapp:latest
    echo "Tagged as latest (main branch)"
  fi
  
  # Step 4: Scan
  echo -e "\n[4] Scanning for vulnerabilities..."
  docker scout cves myapp:$commit_sha --format json | \
    jq '.vulnerabilities | length' 2>/dev/null || echo "Scanning completed"
  
  # Step 5: List artifacts
  echo -e "\n[5] Built artifacts:"
  docker images | grep myapp:
}

# Run simulations
simulate_ci_cd "abc123def456" "feature/new-feature"
simulate_ci_cd "xyz789abc123" "main"
```

### Lab 2: Multi-Stage Build for CI/CD

**Objective:** Optimize image for CI/CD scenarios.

```bash
mkdir multi-stage-demo && cd multi-stage-demo

# Create Go application
cat > main.go << 'EOF'
package main
import "fmt"
func main() { fmt.Println("Hello CI/CD") }
EOF

# Dockerfile with multi-stage
cat > Dockerfile << 'EOF'
# Stage 1: Build
FROM golang:1.20 AS builder
WORKDIR /src
COPY main.go .
RUN go build -o app main.go

# Stage 2: Runtime (minimal)
FROM alpine:3.18
RUN adduser -D -u 1000 appuser
COPY --from=builder /src/app /usr/local/bin/
USER appuser
CMD ["app"]
EOF

# Build
docker build -t go-app:v1.0 .

# Check size
docker images | grep go-app
# Multi-stage: ~10MB (only binary)
# Single-stage would be: ~900MB (entire Go toolchain)

# Run
docker run --rm go-app:v1.0
# Hello CI/CD
```

---

## Failure Scenario: Deployment with Wrong Image Tag

**Scenario:**
You deployed what you thought was version 1.0.5 to production. It's actually version 1.0.3 with critical bugs. The deployment pipeline used the wrong tag.

**What happened:**
```bash
# CI/CD built and pushed multiple tags
docker push myregistry.com/myapp:v1.0.5       # Correct
docker push myregistry.com/myapp:latest       # Points to v1.0.5
docker push myregistry.com/myapp:main-latest  # Points to latest build from main

# Deployment script used wrong tag
docker run myregistry.com/myapp:latest
# "Latest" was manually overwritten elsewhere to point to v1.0.3
```

**Prevention:**
```bash
# Always deploy by specific version
docker run myregistry.com/myapp:v1.0.5
# Never: docker run myregistry.com/myapp:latest

# Validate in deployment
expected_version="v1.0.5"
deployed_version=$(docker inspect \
  myregistry.com/myapp:$expected_version | \
  jq -r '.Config.Labels.version')

if [ "$deployed_version" != "$expected_version" ]; then
  echo "Version mismatch! Aborting."
  exit 1
fi
```

---

Next: [Module 10: Docker → Kubernetes Readiness](10-docker-kubernetes-readiness.md)
