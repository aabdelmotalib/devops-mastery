# Module 10: Docker → Kubernetes Readiness

## What Docker Doesn't Do

Docker is excellent for running single containers and simple multi-container applications. But production systems are more complex.

### Single-Host Limitations

```
Docker on one host:
┌─────────────────────────┐
│      Docker Host        │
│  ┌─────┐  ┌──────┐     │
│  │ app │  │ db   │     │
│  └─────┘  └──────┘     │
└─────────────────────────┘
  Single point of failure
  No auto-scaling
  Manual failover
  Manual load balancing
```

**Problems:**
- Host failure → all containers down
- No automatic rescheduling
- Manual resource management
- No self-healing
- Limited observability at scale

## When Docker Stops Being Enough

### Scale Beyond One Machine

Once you need 5+ hosts, manual management fails.

```bash
# With Docker, you manually:
# 1. Decide which containers run on which hosts
# 2. Monitor containers, restart if they die
# 3. Balance load across hosts
# 4. Handle host failures (move containers elsewhere)
# 5. Update containers (rolling updates)
# 6. Manage secrets across machines
# 7. Provision storage across machines
# 8. Debug issues across machines

# This is error-prone and doesn't scale
```

### High Availability

Applications need to survive failures.

```
Docker: Manual approach
┌─────────┐       ┌─────────┐       ┌─────────┐
│ Host 1  │       │ Host 2  │       │ Host 3  │
│ app(1)  │       │ app(1)  │       │         │
└─────────┘       └─────────┘       └─────────┘
  Host 1 dies
         ↓
┌─────────X       ┌─────────┐       ┌─────────┐
│ Host 1  │       │ Host 2  │       │ Host 3  │
│ app(1)  │       │ app(1)  │       │         │
└─────────┘       └─────────┘       └─────────┘
           ↓ (manual intervention needed)
┌─────────┐       ┌─────────┐       ┌─────────┐
│ Host 1  │       │ Host 2  │       │ Host 3  │
│(restart)│       │ app(1)  │       │app(new) │
└─────────┘       └─────────┘       └─────────┘
```

### Orchestration

Container orchestration automatically:
- Schedules containers across hosts
- Monitors container health
- Restarts failed containers
- Scales applications up/down
- Updates rolling deployments
- Manages networking across hosts
- Manages persistent storage

## Kubernetes: The Industry Standard

Kubernetes is a container orchestration platform. It solves Docker's limitations.

### Kubernetes Architecture

```
┌──────────────────────────────────────────┐
│       Kubernetes Cluster                 │
│                                          │
│  ┌──────────────────────────────────┐   │
│  │     Control Plane (Master)       │   │
│  │  - API Server                    │   │
│  │  - Scheduler (where to place)    │   │
│  │  - Controller Manager            │   │
│  └──────────────────────────────────┘   │
│                   │                      │
│       ┌───────────┼───────────┐          │
│       │           │           │          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Worker 1 │ │Worker 2 │ │Worker 3 │   │
│  │kubelet  │ │kubelet  │ │kubelet  │   │
│  │┌──────┐ │ │┌──────┐ │ │┌──────┐ │   │
│  ││pod   │ │ ││pod   │ │ ││pod   │ │   │
│  │└──────┘ │ │└──────┘ │ │└──────┘ │   │
│  └─────────┘ └─────────┘ └─────────┘   │
└──────────────────────────────────────────┘
```

### Key Kubernetes Concepts

**Pod**: Smallest deployable unit (usually one container)
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  containers:
  - name: app
    image: myapp:v1.0.5
```

**Deployment**: Manages replicated pods with rolling updates
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1.0.5
```

**Service**: Networking abstraction, stable endpoint
```yaml
apiVersion: v1
kind: Service
metadata:
  name: myapp
spec:
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: myapp
```

## Mapping Docker Concepts to Kubernetes

| Docker Concept | Kubernetes Equivalent | Notes |
|---|---|---|
| Image | Image (same) | Same OCI image format |
| Container | Pod | May contain 1+ containers |
| docker run | Pod/Deployment spec | Declarative instead of imperative |
| Network | Service | More sophisticated, DNS built-in |
| Volume | PersistentVolume | More complex, supports many backends |
| docker logs | kubectl logs | Same concept, different interface |
| Restart policy | Deployment controller | Automatic, more intelligent |
| Resource limits | ResourceRequest/Limit | More granular |

## Docker Knowledge Required for Kubernetes

Kubernetes uses Docker (or compatible runtime) underneath. You need to understand:

1. **Container images**
   - How to build with Dockerfile
   - Image layers and caching
   - Image naming and registry

2. **Container runtime behavior**
   - Entrypoint vs CMD
   - Environment variables
   - Volume mounts
   - Resource limits

3. **Networking basics**
   - Port mapping
   - Environment-based service discovery
   - Network isolation

4. **Container security**
   - Running as non-root
   - Linux capabilities
   - Image scanning

## Common Migration Mistakes

### Mistake 1: Assuming 1:1 Mapping

```bash
# Docker: one container per service
docker run mydb
docker run myapi

# Kubernetes: multiple replicas automatically
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3  # Kubernetes will run 3 instances
```

Container that expects single instance will break if replicated.

**Fix:** Design applications to be stateless and horizontally scalable.

### Mistake 2: Storing State in Containers

```dockerfile
# BAD: App writes to local disk
FROM python:3.11
COPY app.py /app/
CMD ["python3", "/app/app.py"]
# Any state written to /app is lost on restart
```

Kubernetes replaces containers frequently.

**Fix:** Use PersistentVolumes or external storage.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: app-storage
```

### Mistake 3: Environment-Based Configuration

```dockerfile
# BAD: Hard-coded in Dockerfile
FROM ubuntu:22.04
ENV DATABASE_URL=postgresql://localhost/db
ENV LOG_LEVEL=debug
```

Kubernetes needs flexibility across environments.

**Fix:** Use ConfigMap and Secrets.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    envFrom:
    - configMapRef:
        name: app-config
    - secretRef:
        name: app-secrets
```

### Mistake 4: Ignoring Resource Requests

```bash
# Docker: container might use all host resources
docker run ubuntu
```

Kubernetes needs to know resource requirements to schedule.

**Fix:** Set requests and limits.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

### Mistake 5: No Health Checks

```bash
# Docker: container might appear running but broken
docker run ubuntu sleep 3600
```

Kubernetes needs to know if container is healthy.

**Fix:** Implement health checks.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Kubernetes-Ready Docker Image Checklist

### Image Properties

- [ ] Non-root user (USER directive)
- [ ] Health check endpoint (/health, /ready)
- [ ] Graceful shutdown (handle SIGTERM)
- [ ] Logs to stdout/stderr (not files)
- [ ] No hardcoded configuration
- [ ] Scanned for vulnerabilities
- [ ] Optimized size (multi-stage build)
- [ ] Clear entrypoint/cmd

### Runtime Properties (via deployment)

- [ ] Resource requests and limits set
- [ ] Liveness probe configured
- [ ] Readiness probe configured
- [ ] Graceful termination timeout (terminationGracePeriodSeconds)
- [ ] Restart policy managed by Kubernetes
- [ ] Security context applied (non-root, drop capabilities)

## Docker Compose to Kubernetes Translation

Simple translation patterns for migration:

### Docker Compose Version

```yaml
# docker-compose.yml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - db_data:/var/lib/postgresql/data

  api:
    image: myapi:v1.0
    depends_on:
      - database
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://database:5432/mydb

volumes:
  db_data:
```

### Kubernetes Version

```yaml
---
# ConfigMap: environment variables
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
data:
  DATABASE_URL: "postgresql://postgres-svc:5432/mydb"

---
# Secret: sensitive data
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
type: Opaque
stringData:
  password: secret

---
# Database Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        volumeMounts:
        - name: db-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: db-storage
        persistentVolumeClaim:
          claimName: db-pvc

---
# Database Service
apiVersion: v1
kind: Service
metadata:
  name: postgres-svc
spec:
  clusterIP: None
  ports:
  - port: 5432
  selector:
    app: postgres

---
# API Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: myapi:v1.0
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: api-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# API Service
apiVersion: v1
kind: Service
metadata:
  name: api-svc
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 8000
  selector:
    app: api
```

## When to Stop Using Docker Directly

Use Docker for:
- Local development
- Simple single-host deployments
- Quick prototyping
- Learning containers

Move to Kubernetes when:
- 5+ servers
- High availability required
- Automatic scaling needed
- Complex networking
- Large development teams

## Learning Path: Docker to Kubernetes

1. **Master Docker fundamentals** (this tutorial)
   - Container concepts
   - Image building
   - Multi-container with Compose
   - Basic security

2. **Kubernetes basics** (separate tutorial)
   - Pods, Deployments, Services
   - ConfigMaps, Secrets
   - Persistent storage
   - Networking

3. **Advanced Kubernetes**
   - StatefulSets, DaemonSets
   - Ingress controllers
   - Custom resources
   - Operators

4. **Cloud integration**
   - EKS, GKE, AKS
   - CI/CD with Kubernetes
   - Service mesh (Istio, Linkerd)
   - Observability (Prometheus, Grafana)

---

## Practice: Exam Questions

1. **What does Kubernetes provide that Docker doesn't?**
   - A) Better networking
   - B) Automatic scaling and self-healing
   - C) Smaller image sizes
   - D) Faster container startup

2. **What is a Kubernetes Pod?**
   - A) Multiple containers running together
   - B) A cluster of machines
   - C) Smallest deployable unit (usually one container)
   - D) A type of storage volume

3. **Why should applications be stateless for Kubernetes?**
   - A) Stateless is faster
   - B) Kubernetes replaces containers frequently
   - C) Kubernetes doesn't support persistent storage
   - D) Docker requires stateless applications

4. **What Docker concept maps to Kubernetes Deployment?**
   - A) Container
   - B) Service
   - C) Replicated containers with orchestration
   - D) Image layer

5. **What should be included in a Kubernetes-ready Docker image?**
   - A) Cron jobs for health checking
   - B) Health check endpoint, non-root user, graceful shutdown handling
   - C) Hardcoded database configuration
   - D) Log files written to filesystem

---

## Hands-On Lab: Prepare Application for Kubernetes

**Objective:** Take a Docker application and make it Kubernetes-ready.

```bash
mkdir k8s-ready && cd k8s-ready

# Create simple Flask app
cat > app.py << 'EOF'
from flask import Flask, jsonify
import os
import signal
import sys

app = Flask(__name__)
shutting_down = False

def handle_sigterm(signum, frame):
    global shutting_down
    shutting_down = True
    print("SIGTERM received, shutting down gracefully")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/ready')
def ready():
    if shutting_down:
        return jsonify({'ready': False}), 503
    return jsonify({'ready': True})

@app.route('/api/hello')
def hello():
    return jsonify({'message': 'Hello from Kubernetes!'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
EOF

# Create Kubernetes-ready Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

RUN useradd -m -u 1000 appuser && \
    mkdir -p /app && \
    chown -R appuser:appuser /app

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
RUN chown appuser:appuser app.py

USER appuser
EXPOSE 8000

# Entrypoint handles signals gracefully
ENTRYPOINT ["python3"]
CMD ["app.py"]
EOF

# Requirements
cat > requirements.txt << 'EOF'
Flask==3.0.0
Werkzeug==3.0.0
EOF

# Build
docker build -t k8s-app:v1.0.0 .

# Test locally
docker run -d \
  --name test-app \
  -p 8000:8000 \
  -e PORT=8000 \
  k8s-app:v1.0.0

# Test endpoints
curl localhost:8000/health
curl localhost:8000/ready
curl localhost:8000/api/hello

# Test graceful shutdown
docker stop test-app
# Should exit gracefully due to SIGTERM handling

# Create Kubernetes deployment manifest
cat > deployment.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-app
  labels:
    app: k8s-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: k8s-app
  template:
    metadata:
      labels:
        app: k8s-app
    spec:
      containers:
      - name: app
        image: myregistry.com/k8s-app:v1.0.0
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: PORT
          value: "8000"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: http
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: http
          initialDelaySeconds: 5
          periodSeconds: 5
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
          capabilities:
            drop:
            - ALL
EOF

echo "Dockerfile and Kubernetes manifest created"
echo "Image is ready for:"
echo "- Non-root execution"
echo "- Health checks"
echo "- Graceful shutdown"
echo "- Resource limits"
echo "- Security constraints"
```

---

## Failure Scenario: Migration Gone Wrong

**Scenario:**
You migrated from Docker Compose to Kubernetes. Your application keeps crashing in Kubernetes but works fine locally with Compose.

**Debugging:**
```bash
# Check pod logs
kubectl logs deployment/myapp
# No logs appearing (logging is buffered)

# Check pod status
kubectl describe pod <pod-name>
# Status: CrashLoopBackOff

# Check events
kubectl get events
# Shows repeated restarts

# Common causes:
# 1. Port binding - hardcoded to 127.0.0.1
# 2. Configuration - looking for files in wrong paths
# 3. Health check failing immediately
# 4. OOM (out of memory) - limits too tight
```

**Prevention:**
- Test image with Kubernetes patterns locally (k3s, kind)
- Implement proper health checks
- Use environment variables for configuration
- Don't hardcode IPs or ports
- Set appropriate resource limits
- Handle SIGTERM for graceful shutdown

---

Congratulations! You've completed all 10 modules. Now tackle the [Final Project](final-project.md) to integrate all concepts.
