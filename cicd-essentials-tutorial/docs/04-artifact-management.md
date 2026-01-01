# Module 04: Artifact Management

## Architecture: What is an Artifact?

An artifact is the output of your CI pipeline. It's a deployable unit of code.

Artifacts are not source code. They are:
- Compiled binaries
- Docker images
- JAR files
- WAR files
- Python wheels
- Node packages
- Bundles

Artifacts answer the question: "What exactly gets deployed to production?"

```
Source Code (human readable)
        ↓
CI Pipeline: Compile, Test, Verify
        ↓
Artifact (machine executable)
        ↓
Artifact Registry (storage)
        ↓
CD Pipeline: Deploy to staging/production
```

## Why Artifacts Matter

Without artifacts, CD becomes fragile:

```
Bad (no artifacts):
  CD System gets source code from Git
  CD System compiles code on production server
  Compilation fails (missing tool, wrong version)
  Production is broken
  Rollback: recompile previous version

Good (with artifacts):
  CD System gets pre-built artifact from registry
  Artifact is already tested (CI guaranteed it works)
  Deployment is just "run this artifact"
  Rollback: "get previous artifact"
```

Artifacts guarantee:
1. **Reproducibility**: Same artifact, same behavior
2. **Traceability**: Know exactly what's in production
3. **Speed**: No compilation on production (just deploy)
4. **Reliability**: Artifact was tested before being pushed

## Versioning Strategies

### Strategy 1: Semantic Versioning

Version format: `MAJOR.MINOR.PATCH`

```
v1.0.0   - First release
v1.1.0   - New feature (backward compatible)
v1.1.1   - Bug fix
v2.0.0   - Breaking changes
```

**Pros:**
- Clear to humans
- Matches Git tags
- Standard across industry

**Cons:**
- Manual versioning (human must decide MAJOR/MINOR/PATCH)
- Hard to automate (how does system know if feature is MINOR or MAJOR?)

### Strategy 2: Git Commit SHA

Version is the first 7 characters of Git commit hash.

```
Commit SHA: abc123def456789
Artifact version: abc123d

Deploy: docker run app:abc123d
Rollback: docker run app:previous_sha
```

**Pros:**
- Fully automatic
- Exact Git traceability
- Every commit = unique version

**Cons:**
- Not human readable
- Hard to remember/reference
- Requires Git history to understand

### Strategy 3: Timestamp

Version is build timestamp.

```
20240101-153042  (Jan 1, 2024 at 3:30:42 PM)
20240102-091510

docker run app:20240102-091510
```

**Pros:**
- Automatic
- Somewhat readable (you know when it was built)

**Cons:**
- No traceability to code changes
- Multiple artifacts could have same timestamp
- Doesn't tell you what changed

### Strategy 4: Monotonic Counter

Each build gets the next sequential number.

```
build-1
build-2
build-3
build-4827

docker run app:build-4827
```

**Pros:**
- Simple
- Automatic

**Cons:**
- Not meaningful (you don't know what's different between build-4827 and build-4826)
- Doesn't scale to multiple services

## Recommendation: Git SHA + Semantic Tags

Use Git commit SHA as primary version (automatic, 100% traceable).
Use Git tags (semantic versions) for important releases.

```
Every commit: artifact tagged as abc123d
  - Automatically versioned
  - Tied to exact Git commit
  - Can deploy any commit

Every release: tag as v1.2.3
  - Human friendly
  - Marks important milestones
  - Easy to reference in documentation

Production artifacts: both v1.2.3 AND abc123d (same artifact)
```

## Docker Images as Artifacts

Docker is the standard for containerized artifacts.

```
Source Code
    ↓
Docker Build (CI)
    ↓
Docker Image (artifact)
    ↓
Docker Registry (storage)
    ↓
Docker Run (deployment)
```

### Why Docker?

1. **Consistency**: Code runs same whether on laptop, staging, or production
2. **Dependencies included**: No "works on my machine" problems
3. **Reproducibility**: Same image always produces same behavior
4. **Fast deployment**: Just download image, run container

### Building a Docker Image

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0"]
```

Build process:
```bash
# Tag with Git SHA
docker build -t myapp:abc123d .

# Also tag with semantic version
docker tag myapp:abc123d myapp:v1.2.3

# Push to registry
docker push myapp:abc123d
docker push myapp:v1.2.3
```

In CI pipeline:
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: docker/setup-buildx-action@v2
      - run: |
          # Get Git SHA
          SHA=$(git rev-parse --short HEAD)
          docker build -t myapp:$SHA .
          docker push myapp:$SHA
```

## Artifact Registries (Conceptual)

A registry is centralized storage for artifacts.

### Registry Types

**Docker Registry (Container images)**
- Docker Hub (public)
- Private Docker registries
- AWS ECR
- Google Artifact Registry
- Azure Container Registry

**Package Registries**
- npm (JavaScript)
- PyPI (Python)
- Maven Central (Java)
- RubyGems (Ruby)

**Generic Registries**
- Artifactory (supports any artifact type)
- Nexus (any artifact type)

### Registry Concepts

**Authentication:** You authenticate to push and pull artifacts
```bash
docker login registry.example.com
docker push registry.example.com/myapp:v1.2.3
```

**Namespacing:** Artifacts are organized
```
registry.example.com/team/service:version
registry.example.com/mycompany/backend:v1.2.3
registry.example.com/mycompany/frontend:v1.2.3
```

**Retention Policies:** Old artifacts are deleted
```
Keep latest 10 artifacts
Delete artifacts older than 30 days
Keep all tagged versions (releases) permanently
```

## Artifact Promotion

Artifact promotion is moving artifacts through environments.

```
Build Artifact
    ↓
Push to Registry (tagged: abc123d)
    ↓
Deploy to Staging (staging environment)
    ↓
Run tests on staging
    ↓
✓ Tests pass → Promote to Production
✗ Tests fail → Don't promote (rollback or fix)
```

**Key point:** The SAME artifact goes through all environments. You don't rebuild in each environment.

### Why Same Artifact?

Bad approach (rebuild per environment):
```
Environment: staging
  Build code
  Run
  
Environment: production
  Build code again (different compiler version?)
  Run
  
Result: Code might behave differently
```

Good approach (same artifact):
```
Artifact: abc123d (built in CI)

Environment: staging
  Deploy artifact:abc123d
  Run
  
Environment: production
  Deploy artifact:abc123d (same binary)
  Run
  
Result: Code behaves identically
```

## Example: Artifact Lifecycle

**Scenario:** Deploying a payment service

```
Day 1, 10:00 AM
  Engineer pushes code to feature/payment
  Webhook triggers CI
  CI builds Docker image: paymentapp:abc123d
  Tests pass
  Image pushed to registry

Day 1, 11:00 AM
  Engineer creates pull request
  Code review happens
  Pull request approved

Day 1, 12:00 PM
  Pull request merged to main
  Webhook triggers CI again
  CI builds image: paymentapp:def456g
  All tests pass (compile, unit, integration, security)
  Image pushed to registry
  CD system detects merge
  CD deploys paymentapp:def456g to staging
  Staging smoke tests run

Day 1, 2:00 PM
  Staging tests all pass
  Engineer approves production deployment (manual gate)
  CD system deploys paymentapp:def456g to production
  Production monitoring shows all healthy
  Rollout complete

Day 2, 8:00 AM
  Critical bug discovered in production
  Rollback decision made
  CD system deploys paymentapp:abc123d (previous version)
  Previous version is running
  Incident resolved
```

Notice: No new build during rollback. Previous artifact is re-deployed.

## Multi-Service Artifacts

For microservices, each service has its own artifact.

```
Repo: company/backend-auth
  CI builds: auth-service:v1.2.3

Repo: company/backend-payments
  CI builds: payments-service:v2.1.0

Repo: company/backend-orders
  CI builds: orders-service:v1.0.5

Production deployment:
  - auth-service:v1.2.3
  - payments-service:v2.1.0
  - orders-service:v1.0.5
  
  (Each service version is independent)
```

Artifact tracing in production:
```bash
# Show what's running
docker ps
# Shows:
#  auth-service:v1.2.3 (running)
#  payments-service:v2.1.0 (running)
#  orders-service:v1.0.5 (running)

# If payment fails, you know:
# - It's in payments-service:v2.1.0
# - You can quickly check what changed in that version
# - Rollback is: deploy payments-service:v2.0.9
```

## Common Mistakes

### Mistake 1: Not Tagging Artifacts Clearly

Wrong: Every artifact is named `latest`

Problem:
- You don't know which version is running
- Rollback is unclear (what are you rolling back to?)
- Production artifacts are indistinguishable

Right: Every artifact has semantic version + Git SHA

### Mistake 2: Rebuilding in Each Environment

Wrong: CD system checks out code, rebuilds in staging and production

Problem:
- Code might compile differently
- Dependencies might resolve differently
- Staging works, production breaks
- Not reproducible

Right: Build once in CI, same artifact in all environments

### Mistake 3: No Retention Policy

Wrong: Registry stores every artifact ever built (500+ versions)

Problem:
- Registry storage grows indefinitely
- Old artifacts never cleaned up
- Hard to find right version
- Cost increases

Right: Delete old artifacts (keep 10 latest versions, or 30-day retention)

### Mistake 4: Deploying Source Code Instead of Artifacts

Wrong: CD system checks out Git repository, compiles on production server

Problem:
- Compilation can fail on production (missing tools, wrong environment)
- Production is broken, takes time to fix
- Slow deployment

Right: CD system gets pre-built artifact, deploys it immediately

### Mistake 5: Image Size Explosion

Wrong: Docker image is 2GB (includes build tools, test files, etc.)

Problem:
- Slow to push to registry
- Slow to pull on production server
- Takes 5 minutes just to deploy image
- Storage costs high

Right: Multi-stage build, final image is 50MB

### Multi-Stage Docker Build Example

```dockerfile
# Stage 1: Build
FROM python:3.11 as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ .
RUN python -m py_compile src/

# Stage 2: Runtime (final image)
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app /app
CMD ["python", "-m", "uvicorn", "main:app"]
```

Final image only includes runtime, not build tools.

## Production Notes

### Artifact Immutability

Never redeploy the same artifact with different code.

Right:
```
v1.0.0 = specific code commit (frozen)
v1.0.1 = different code commit
```

Wrong:
```
v1.0.0 = deployed code
(Find bug)
(Fix code)
(Rebuild v1.0.0 with new code) ← WRONG
```

If you rebuild, increment version. Once a version is released, it's locked.

### Artifact Scanning Before Registry Push

Scan artifacts for vulnerabilities BEFORE pushing to registry.

```bash
# In CI pipeline
docker build -t myapp:abc123d .

# Scan image
trivy image myapp:abc123d  # Find vulnerabilities

# If scan fails, don't push
if scan_failed:
    exit 1
    
# Only push clean images
docker push myapp:abc123d
```

### Private vs Public Registries

**Public registry** (Docker Hub):
- Anyone can pull
- Good for open-source projects
- Risky for proprietary code

**Private registry**:
- Only authenticated users can pull
- Protects proprietary code
- Requires authentication in deployment

For production, always use private registry.

### Artifact Metadata

Include metadata with artifacts for traceability:

```dockerfile
FROM python:3.11
# ... build steps ...
LABEL org.example.version="1.2.3"
LABEL org.example.build-date="2024-01-15"
LABEL org.example.git-commit="abc123d"
LABEL org.example.git-branch="main"
LABEL org.example.build-url="https://ci.example.com/builds/1234"
```

Retrieve metadata:
```bash
docker inspect myapp:v1.2.3 | grep Labels
```

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. You have a choice of versioning strategies. Which is fully automatic?
   - a) Semantic versioning (v1.2.3)
   - b) Timestamp (20240115-153042)
   - c) Git commit SHA (abc123d)
   - d) Both b and c

2. What is the key difference between an artifact and source code?
   - a) Artifacts are human readable
   - b) Artifacts are machine executable
   - c) Artifacts include comments
   - d) Artifacts are checked into Git

3. Your Docker image is 2.5GB. What's the likely cause?
   - a) You're including build tools in final image
   - b) You're copying test files into image
   - c) You're not using multi-stage build
   - d) All of the above

4. You built artifact:abc123d, tested it in staging, and it passed. Later, you deploy artifact:xyz789d to production and it fails. Why could this happen?
   - a) You rebuilt the code (shouldn't rebuild)
   - b) Environment difference
   - c) You deployed different artifact than tested
   - d) All of the above (implies you didn't use same artifact)

5. How should you version production artifacts?
   - a) Always "latest"
   - b) Git commit SHA + semantic tag
   - c) Timestamp
   - d) Just the branch name

### Pipeline Design Tasks

**Task 1: Design Artifact Versioning**
You're building a microservices system:
- 5 independent services
- Different teams own different services
- Need to deploy services independently
- Need to rollback services independently

Design your versioning and artifact structure:
1. How do you version each artifact?
2. How does production know what's deployed?
3. How do you rollback a single service?

**Task 2: Multi-Stage Docker Build**
You have a Go backend with:
- Compilation takes 5 minutes
- Final binary is 50MB
- Build uses 2GB of build tools and source code
- Current image is 2.1GB

Optimize using multi-stage build:
1. Show the Dockerfile structure (2 stages)
2. What goes in stage 1?
3. What goes in stage 2?
4. What's final image size?

### Failure Scenario

**Scenario: The Wrong Artifact Deployment**

Your artifacts are tagged as:
- payment-service:v2.1.0
- payment-service:latest

Production deployment config says:
```
docker run payment-service:latest
```

A developer commits to main. CI builds and tags:
- payment-service:abc456d (Git SHA)
- payment-service:latest (overwrites previous)

A critical bug is discovered in the new version. Someone manually restarts production (thinking it will start previous version).

Instead:
```bash
docker run payment-service:latest
# Pulls NEWEST image (the buggy one)
# Not the previous version
# Restart doesn't help
```

Questions:
1. What's the root cause of this design problem?
2. Why is `latest` tag dangerous?
3. How would you prevent manual restarts?
4. What deployment practices would prevent this?
5. How do you do a real rollback?

---

Next: [Module 05: Security in CI/CD](05-security-in-cicd.md)
