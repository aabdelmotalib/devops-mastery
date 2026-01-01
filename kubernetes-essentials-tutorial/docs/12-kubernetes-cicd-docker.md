# Module 12: Kubernetes in CI/CD & Docker Integration

## Overview

This module covers deploying containerized applications to Kubernetes via CI/CD pipelines, managing multiple environments, and best practices for Kubernetes-native deployments.

## CI/CD Pipeline Architecture

### Traditional CI/CD to Kubernetes

```
Developer
    ↓
Commit to Git
    ↓
CI Pipeline (build, test)
    ↓
Build Docker image
    ↓
Push to registry
    ↓
CD Pipeline (deploy)
    ↓
Update Kubernetes manifests
    ↓
Apply to cluster
```

### Example: GitHub Actions CI/CD Pipeline

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
    paths:
    - 'src/**'
    - 'Dockerfile'
    - '.github/workflows/**'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/myapp

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest \
                      -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} \
                      .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.GITHUB_TOKEN }} | docker login ${{ env.REGISTRY }} -u ${{ github.actor }} --password-stdin
        docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
        docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    
    - name: Update Kubernetes manifest
      run: |
        # Update deployment.yaml with new image tag
        sed -i 's|IMAGE_TAG|${{ github.sha }}|g' k8s/deployment.yaml
    
    - name: Deploy to Kubernetes
      run: |
        mkdir -p ~/.kube
        echo ${{ secrets.KUBECONFIG }} | base64 -d > ~/.kube/config
        kubectl apply -f k8s/
```

## Dockerfile to Kubernetes Workflow

### Dockerfile Best Practices for Kubernetes

```dockerfile
# Multi-stage build for small images
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
# Copy only artifacts from builder (not build tools)
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code
COPY app/ .

# Non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Health check (used by Kubernetes probes)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Expose port
EXPOSE 8080

# Run application (should respond to SIGTERM for graceful shutdown)
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
```

**Key practices**:
1. **Multi-stage build**: Smaller final image
2. **Non-root user**: Security (USER 1000)
3. **HEALTHCHECK**: Defines probe behavior
4. **EXPOSE**: Documents port usage
5. **Signal handling**: Graceful shutdown (Python catches SIGTERM)

### Image Tagging Strategy

```bash
# Semantic versioning for releases
docker build -t myrepo/myapp:1.2.3 .
docker push myrepo/myapp:1.2.3

# Build number from CI
docker build -t myrepo/myapp:build-12345 .
docker push myrepo/myapp:build-12345

# Commit SHA for traceability
docker build -t myrepo/myapp:sha-abc123def .
docker push myrepo/myapp:sha-abc123def

# In deployment.yaml, use explicit tag (never "latest")
image: myrepo/myapp:1.2.3
```

## Multi-environment Deployments

### Environment Configuration Structure

```
k8s/
├── base/                    # Common configuration
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── overlays/
│   ├── dev/                 # Development overrides
│   │   ├── kustomization.yaml
│   │   ├── replicas-patch.yaml
│   │   └── values.yaml
│   ├── staging/             # Staging overrides
│   │   ├── kustomization.yaml
│   │   └── values.yaml
│   └── prod/                # Production overrides
│       ├── kustomization.yaml
│       └── values.yaml
```

### Kustomize Example

```yaml
# base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
- deployment.yaml
- service.yaml

commonLabels:
  app: myapp

---
# overlays/dev/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
- ../../base

replicas:
- name: myapp
  count: 1

configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=DEBUG
  - ENVIRONMENT=dev

---
# overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
- ../../base

replicas:
- name: myapp
  count: 5

configMapGenerator:
- name: app-config
  literals:
  - LOG_LEVEL=INFO
  - ENVIRONMENT=production
```

**Deploy to different environments**:
```bash
# Development
kubectl apply -k k8s/overlays/dev -n dev

# Staging
kubectl apply -k k8s/overlays/staging -n staging

# Production
kubectl apply -k k8s/overlays/prod -n prod
```

## Helm in CI/CD Pipelines

### GitOps with Helm

```yaml
# GitHub Actions example
- name: Deploy with Helm
  run: |
    helm repo add myrepo https://charts.example.com
    helm repo update
    
    helm upgrade --install my-release myrepo/my-app \
      --namespace production \
      --values values-prod.yaml \
      --set image.tag=${{ github.sha }} \
      --atomic \
      --timeout=10m
```

**--atomic**: Rollback if deployment fails.

### Helm Values from CI/CD

```yaml
# values.yaml template
image:
  tag: ${IMAGE_TAG}
  pullPolicy: IfNotPresent

environment: ${ENVIRONMENT}

config:
  LOG_LEVEL: ${LOG_LEVEL}
  DATABASE_HOST: ${DATABASE_HOST}

replicas: ${REPLICAS}
```

```bash
# CI/CD substitutes variables
envsubst < values.yaml > values-substituted.yaml
helm upgrade --install my-app ./chart -f values-substituted.yaml
```

## GitOps: Git as Single Source of Truth

### GitOps Principles

1. **Declarative**: All infrastructure declared in Git
2. **Versioned**: Git tracks all changes
3. **Automated**: Operators reconcile desired state
4. **Observable**: See status in Git

### ArgoCD Example

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
spec:
  project: default
  
  source:
    repoURL: https://github.com/company/app-config.git
    targetRevision: main
    path: k8s/overlays/prod
  
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  
  syncPolicy:
    automated:
      prune: true              # Delete resources removed from Git
      selfHeal: true           # Reconcile if manual changes happen
    syncOptions:
    - CreateNamespace=true
```

**Workflow**:
```
Update Git
    ↓
ArgoCD detects change
    ↓
Compares desired (Git) vs actual (cluster)
    ↓
Automatically syncs
    ↓
Cluster matches Git state
```

## Common Mistakes

### Mistake 1: Using "latest" Image Tag

```dockerfile
# WRONG: Tag changes, unpredictable deployments
docker build -t myrepo/myapp:latest .
```

**Problem**: 
- Image pulled is unpredictable
- Can't reproduce deployments
- Rollback to "latest" doesn't work

**Solution**: Use semantic versioning or commit SHA
```dockerfile
docker build -t myrepo/myapp:v1.2.3 .
docker build -t myrepo/myapp:$(git rev-parse --short HEAD) .
```

### Mistake 2: Storing Secrets in Git

```bash
git add deployment.yaml  # Contains API_KEY=secret123
git push
# Secret now in Git history FOREVER
```

**Solution**:
- Use external secret management
- Store only secret reference in Git
- Use Sealed Secrets or Helm Secrets plugin

### Mistake 3: No Image Verification

```bash
# Deploy any image without validation
kubectl set image deployment/app app=malicious:latest

# Malicious container runs in production
```

**Solution**:
- Sign images
- Use image scanning
- Require approval for deployments
- Only deploy from CI/CD (no manual kubectl commands in prod)

### Mistake 4: Not Testing Deployments in Staging

```bash
# Deploy directly to production
# Configuration error → downtime
```

**Solution**: Deploy to dev → staging → production pipeline

### Mistake 5: Inefficient Image Size

```dockerfile
# WRONG: Installs build tools in final image
FROM python:3.11

RUN apt-get update && apt-get install -y build-essential
COPY . .
RUN pip install -r requirements.txt

# Final image 1.5GB (includes build tools)
```

**Solution**: Multi-stage build
```dockerfile
FROM python:3.11 as builder
RUN apt-get update && apt-get install -y build-essential
COPY . .
RUN pip install -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages .
# Final image 400MB (no build tools)
```

## Production Patterns

### Blue-Green Deployment via CI/CD

```bash
# CI/CD creates new "green" deployment
helm install my-app-green ./chart --values values-prod.yaml --set version=green

# Run integration tests against green
./test-green.sh

# If success, switch traffic to green
kubectl patch service my-app -p '{"spec":{"selector":{"version":"green"}}}'

# Keep blue for quick rollback
```

### Canary Deployment Automation

```bash
# Deploy new version to 10% of traffic
helm install my-app-canary ./chart \
  --set replicas=1 \
  --set weight=10

# Monitor metrics
# If good: increase weight gradually
# If bad: rollback immediately
```

### Automated Rollback on Failure

```yaml
# Kubernetes deployment automatic rollback
spec:
  progressDeadlineSeconds: 600
  
# If not ready within 10 minutes, automatically rollback
# Combined with readiness probes for safety
```

## Key Takeaways

1. **Docker images** are deployable units
2. **Image tagging** should be explicit (semantic versioning)
3. **Multi-environment** setup uses Kustomize or Helm overlays
4. **CI/CD pipelines** automate build → test → deploy
5. **GitOps** treats Git as source of truth
6. **Secrets** should never be in Git or image
7. **Test in staging** before production deployment

---

## Practice Questions

### MCQ Questions

1. What should image tags be in production?
   A) Always use "latest"  
   B) Explicit versions (v1.2.3, commit SHA)  
   C) Build timestamps  
   D) Random identifiers  

2. What is GitOps?
   A) Using Git commands from Kubernetes  
   B) Storing code in Git  
   C) Git as source of truth for infrastructure  
   D) Deploying Git repositories as Pods  

3. Which is more secure for secrets?
   A) Store in Docker image  
   B) Store in Git  
   C) Use external secret manager  
   D) Hardcode in application  

4. How should you deploy to multiple environments?
   A) Manual kubectl apply in each cluster  
   B) Copy manifests for each environment  
   C) Use overlays (Kustomize) or values (Helm)  
   D) Deploy once to prod, others pull from prod  

5. What should multi-stage Docker build accomplish?
   A) Build multiple versions simultaneously  
   B) Smaller final image by removing build tools  
   C) Build for different architectures  
   D) Parallel builds for speed  

### Hands-on Cluster Tasks

**Task 1: CI/CD Pipeline Simulation**

1. Create simple application:
   ```bash
   mkdir -p myapp/app
   cat > myapp/Dockerfile << 'EOF'
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install flask
   CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
   EOF
   
   cat > myapp/app.py << 'EOF'
   from flask import Flask
   app = Flask(__name__)
   @app.route('/health')
   def health():
       return 'OK', 200
   @app.route('/')
   def hello():
       return 'Hello World', 200
   EOF
   ```

2. Build and tag image:
   ```bash
   cd myapp
   docker build -t myapp:v1.0.0 .
   ```

3. Create deployment manifest:
   ```bash
   cat > deployment.yaml << 'EOF'
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: myapp
   spec:
     replicas: 2
     selector:
       matchLabels:
         app: myapp
     template:
       metadata:
         labels:
           app: myapp
       spec:
         containers:
         - name: myapp
           image: myapp:v1.0.0
           ports:
           - containerPort: 5000
           readinessProbe:
             httpGet:
               path: /health
               port: 5000
             initialDelaySeconds: 5
             periodSeconds: 5
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: myapp
   spec:
     type: LoadBalancer
     selector:
       app: myapp
     ports:
     - port: 80
       targetPort: 5000
   EOF
   ```

4. Deploy:
   ```bash
   kubectl apply -f deployment.yaml
   ```

5. Verify:
   ```bash
   kubectl get pods -l app=myapp
   kubectl logs -l app=myapp
   ```

6. Simulate CI/CD update:
   ```bash
   # Update code
   echo "# v2 update" >> app.py
   
   # Rebuild
   docker build -t myapp:v1.0.1 .
   
   # Update manifest
   sed -i 's/v1.0.0/v1.0.1/g' deployment.yaml
   
   # Redeploy (rolling update)
   kubectl apply -f deployment.yaml
   
   # Watch update
   kubectl rollout status deployment/myapp
   ```

7. Cleanup:
   ```bash
   kubectl delete -f deployment.yaml
   ```

**Task 2: Multi-environment with Kustomize**

1. Create base:
   ```bash
   mkdir -p k8s/base k8s/overlays/dev k8s/overlays/prod
   
   cat > k8s/base/deployment.yaml << 'EOF'
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: myapp
   spec:
     replicas: 1
     selector:
       matchLabels:
         app: myapp
     template:
       metadata:
         labels:
           app: myapp
       spec:
         containers:
         - name: myapp
           image: myapp:latest
   EOF
   
   cat > k8s/base/kustomization.yaml << 'EOF'
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   resources:
   - deployment.yaml
   EOF
   ```

2. Create overlays:
   ```bash
   cat > k8s/overlays/dev/kustomization.yaml << 'EOF'
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   bases:
   - ../../base
   replicas:
   - name: myapp
     count: 1
   EOF
   
   cat > k8s/overlays/prod/kustomization.yaml << 'EOF'
   apiVersion: kustomize.config.k8s.io/v1beta1
   kind: Kustomization
   bases:
   - ../../base
   replicas:
   - name: myapp
     count: 3
   EOF
   ```

3. Deploy to different environments:
   ```bash
   # Dev
   kubectl apply -k k8s/overlays/dev -n dev

   # Prod
   kubectl apply -k k8s/overlays/prod -n prod
   ```

4. Verify different replica counts:
   ```bash
   kubectl get pods -n dev
   kubectl get pods -n prod
   ```

5. Cleanup:
   ```bash
   kubectl delete -k k8s/overlays/dev -n dev
   kubectl delete -k k8s/overlays/prod -n prod
   ```

### Realistic Production Failure Scenario

**Scenario: Broken Image Deployed to Production**

CI/CD pipeline builds and pushes image, but doesn't test it. When deployed, container fails to start (missing dependency, wrong port, etc.).

```bash
# CI/CD pushes myapp:v2.0.0 without testing

# Deployment applies new version:
# kubectl set image deployment/app app=myapp:v2.0.0

# Rolling update begins:
# Old pods (v1.0.0): 3 running
# New pods (v2.0.0): CrashLoopBackOff

# Service has no healthy endpoints
# Requests fail: "no available backends"
```

**Prevention**:
1. **Test image after build**:
   ```bash
   docker run --rm myapp:v2.0.0 --version
   # Verify it starts and responds
   ```

2. **Dry-run before apply**:
   ```bash
   kubectl apply -f deployment.yaml --dry-run=server
   ```

3. **Progressive rollout**:
   ```bash
   # Deploy to canary (1 pod) first
   # Test with real traffic
   # Then full deployment
   ```

4. **Automated smoke tests**:
   ```bash
   # After deployment, run tests
   kubectl run smoke-test --image=my-test:v1 \
     -it --rm -- ./tests/smoke-tests.sh
   ```

5. **Readiness probe catches issues**:
   ```yaml
   readinessProbe:
     httpGet:
       path: /health
       port: 8080
     failureThreshold: 3  # Fail after 3 retries
   ```
   Deployment waits for ready before full rollout.

---

## Further Reading

- Docker Best Practices: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
- Kustomize: https://kustomize.io/
- ArgoCD: https://argoproj.github.io/cd/
- GitOps: https://www.gitops.tech/
- Image Scanning: https://github.com/aquasecurity/trivy
