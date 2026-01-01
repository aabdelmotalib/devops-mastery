# Final Project: Production-Ready Multi-tier E-commerce Backend

## Project Overview

Deploy a complete, production-ready e-commerce backend to Kubernetes. This project integrates all concepts from modules 1-12: containerization, multi-tier architecture, configuration management, storage, monitoring, security, and CI/CD deployment.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Ingress    │ (Module 4)
                    │   (TLS)      │
                    └──────┬──────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
  ┌────▼────┐         ┌────▼────┐         ┌───▼────┐
  │API Pod  │         │API Pod  │         │API Pod │ (Module 3)
  │(Flask)  │         │(Flask)  │         │(Flask) │
  └────┬────┘         └────┬────┘         └───┬────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
              │ Service (Module 4)
       ┌──────▼──────┐
       │ PostgreSQL  │ (StatefulSet, Module 6)
       │ Database    │
       │ (Persistent │
       │  Storage)   │
       └─────────────┘

       ┌────────────────────────────────────┐
       │ Redis Cache (StatefulSet, Module 6)│
       └────────────────────────────────────┘

       ┌────────────────────────────────────┐
       │ Monitoring (Prometheus + Grafana)  │
       │ Logging (ELK/Loki) (Module 8)      │
       └────────────────────────────────────┘
```

## Requirements

### Functional Requirements

1. **REST API** with endpoints:
   - `GET /api/products` - List products
   - `POST /api/products` - Create product (admin)
   - `POST /api/orders` - Create order (user)
   - `GET /api/orders/:id` - Get order status
   - `GET /health` - Health check

2. **Data Persistence**:
   - PostgreSQL database for products, orders, users
   - Redis cache for session/product cache

3. **Multiple Environments**:
   - Development (1 replica, basic resources)
   - Staging (2 replicas, moderate resources)
   - Production (3 replicas, high resources, HA)

### Non-Functional Requirements

1. **High Availability**:
   - Minimum 3 API replicas in production
   - Health checks (readiness/liveness/startup)
   - Pod Disruption Budget for graceful shutdown
   - Multi-zone node distribution

2. **Security**:
   - RBAC roles for different services
   - Secrets for database credentials
   - Non-root container user
   - Network policies restricting traffic
   - Pod SecurityContext (read-only filesystem, no privilege escalation)

3. **Resource Management**:
   - CPU/memory requests and limits
   - Namespace ResourceQuotas
   - HPA for automatic scaling
   - Pod Priority classes

4. **Observability**:
   - Structured logging to stdout
   - Prometheus metrics
   - Liveness/readiness probes
   - Event tracking

5. **CI/CD Integration**:
   - Docker multi-stage build
   - Image registry push
   - Multi-environment deployment (Kustomize)
   - GitOps with ArgoCD

## Project Structure

```
ecommerce-backend/
├── docker-compose.yml          # Local development
├── Dockerfile                  # Multi-stage build
├── .dockerignore
├── requirements.txt            # Python dependencies
├── k8s/                        # Kubernetes manifests
│   ├── base/                   # Base configs (all envs)
│   │   ├── api-deployment.yaml
│   │   ├── api-service.yaml
│   │   ├── postgres-statefulset.yaml
│   │   ├── postgres-service.yaml
│   │   ├── redis-statefulset.yaml
│   │   ├── redis-service.yaml
│   │   ├── namespace.yaml
│   │   ├── rbac.yaml
│   │   ├── network-policy.yaml
│   │   ├── configmap.yaml
│   │   ├── secrets.yaml        # encrypted with sealed-secrets
│   │   ├── hpa.yaml
│   │   ├── pdb.yaml
│   │   ├── pvc.yaml
│   │   ├── storageclass.yaml
│   │   └── kustomization.yaml
│   └── overlays/               # Environment-specific
│       ├── dev/
│       │   └── kustomization.yaml
│       ├── staging/
│       │   └── kustomization.yaml
│       └── prod/
│           ├── kustomization.yaml
│           └── ingress-tls.yaml
├── app/
│   ├── __init__.py
│   ├── main.py                 # Flask application
│   ├── models.py               # Database models
│   ├── routes/
│   │   ├── products.py
│   │   ├── orders.py
│   │   └── health.py
│   ├── utils/
│   │   ├── database.py
│   │   ├── cache.py
│   │   └── logging.py
│   └── config.py               # Configuration
├── migrations/                 # Alembic database migrations
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_health.py
├── .github/workflows/
│   └── deploy.yml              # GitHub Actions CI/CD
└── README.md
```

## Implementation Guide

### Step 1: Create Flask Application

```python
# app/main.py
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import logging
import json
from pythonjsonlogger import jsonlogger

app = Flask(__name__)
CORS(app)
db = SQLAlchemy(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure structured logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint for K8s probes"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/products', methods=['GET'])
def get_products():
    """List all products"""
    products = Product.query.all()
    return jsonify([p.to_dict() for p in products]), 200

@app.route('/api/products', methods=['POST'])
def create_product():
    """Create new product (admin only)"""
    data = request.json
    product = Product(name=data['name'], price=data['price'])
    db.session.add(product)
    db.session.commit()
    logger.info(f"Product created: {product.id}")
    return jsonify(product.to_dict()), 201

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create new order"""
    data = request.json
    order = Order(user_id=data['user_id'], product_id=data['product_id'])
    db.session.add(order)
    db.session.commit()
    logger.info(f"Order created: {order.id}")
    return jsonify(order.to_dict()), 201

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order status"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify(order.to_dict()), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

### Step 2: Create Dockerfile (Multi-stage)

```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy application code
COPY app/ ./app
COPY config.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

EXPOSE 8080

# Graceful shutdown with signal handling
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "30", "app.main:app"]
```

### Step 3: Create Kubernetes Manifests

#### 3a. Namespace

```yaml
# k8s/base/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ecommerce
  labels:
    app: ecommerce
```

#### 3b. API Deployment

```yaml
# k8s/base/api-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: ecommerce
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        version: v1
    spec:
      serviceAccountName: api
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      
      initContainers:
      - name: wait-for-db
        image: busybox:1.28
        command: ['sh', '-c', 'until nc -z postgres 5432; do echo waiting for db; sleep 2; done;']
      
      containers:
      - name: api
        image: ghcr.io/company/ecommerce-api:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8080
          name: http
        
        # Health checks
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
          failureThreshold: 3
        
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
          failureThreshold: 3
        
        startupProbe:
          httpGet:
            path: /health
            port: 8080
          failureThreshold: 30
          periodSeconds: 2
        
        # Resource limits
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        
        # Configuration from ConfigMap/Secret
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        - name: REDIS_URL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: redis-url
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: log-level
        
        # Volume mounts
        volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true
      
      # Pod affinity for distribution
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - api
              topologyKey: kubernetes.io/hostname
      
      volumes:
      - name: config
        configMap:
          name: app-config
```

#### 3c. Service

```yaml
# k8s/base/api-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: ecommerce
  labels:
    app: api
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  selector:
    app: api
```

#### 3d. PostgreSQL StatefulSet

```yaml
# k8s/base/postgres-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: ecommerce
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 999
      containers:
      - name: postgres
        image: postgres:15-alpine
        ports:
        - containerPort: 5432
        
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: POSTGRES_DB
          value: ecommerce
        
        resources:
          requests:
            cpu: 250m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
        
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - pg_isready -U postgres
          initialDelaySeconds: 30
          periodSeconds: 10
  
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

#### 3e. RBAC

```yaml
# k8s/base/rbac.yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api
  namespace: ecommerce

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api
  namespace: ecommerce
rules:
- apiGroups: [""]
  resources: ["configmaps", "secrets"]
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api
  namespace: ecommerce
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: api
subjects:
- kind: ServiceAccount
  name: api
  namespace: ecommerce
```

#### 3f. NetworkPolicy

```yaml
# k8s/base/network-policy.yaml
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-netpol
  namespace: ecommerce
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-controller
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          k8s-app: kube-dns
    ports:
    - protocol: UDP
      port: 53
```

#### 3g. ConfigMap & Secrets

```yaml
# k8s/base/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: ecommerce
data:
  redis-url: "redis://redis:6379"
  log-level: "INFO"
  environment: "production"

---
# k8s/base/secrets.yaml (Use Sealed Secrets in production)
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: ecommerce
type: Opaque
stringData:
  username: postgres
  password: changeme123!  # Use external secret manager in production
  url: postgresql://postgres:changeme123!@postgres:5432/ecommerce
```

#### 3h. HPA

```yaml
# k8s/base/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: ecommerce
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
```

#### 3i. Pod Disruption Budget

```yaml
# k8s/base/pdb.yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
  namespace: ecommerce
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: api
```

#### 3j. Kustomization (Base)

```yaml
# k8s/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: ecommerce

commonLabels:
  app: ecommerce

resources:
- namespace.yaml
- api-deployment.yaml
- api-service.yaml
- postgres-statefulset.yaml
- postgres-service.yaml
- rbac.yaml
- network-policy.yaml
- configmap.yaml
- secrets.yaml
- hpa.yaml
- pdb.yaml
```

### Step 4: Environment Overlays

```yaml
# k8s/overlays/prod/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

bases:
- ../../base

replicas:
- name: api
  count: 5
- name: postgres
  count: 1

patchesStrategicMerge:
- deployment-patch.yaml

configMapGenerator:
- name: app-config
  behavior: merge
  literals:
  - log-level: WARN
  - environment: production

# Add Ingress for prod
resources:
- ingress-tls.yaml
```

### Step 5: CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Build and Deploy

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}/ecommerce-api

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build image
      run: |
        docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} .
        docker build -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest .
    
    - name: Push to registry
      run: |
        echo ${{ secrets.GITHUB_TOKEN }} | docker login ${{ env.REGISTRY }} -u ${{ github.actor }} --password-stdin
        docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
        docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
    
    - name: Deploy to Kubernetes
      run: |
        mkdir -p ~/.kube
        echo ${{ secrets.KUBECONFIG_PROD }} | base64 -d > ~/.kube/config
        kubectl apply -k k8s/overlays/prod
        kubectl rollout status deployment/api -n ecommerce
```

## Testing & Validation

```bash
# Build and test locally
docker build -t ecommerce-api:test .
docker run -p 8080:8080 ecommerce-api:test

# Test health check
curl http://localhost:8080/health

# Deploy to cluster
kubectl apply -k k8s/overlays/dev
kubectl -n ecommerce get pods
kubectl -n ecommerce logs -f deployment/api

# Run integration tests
kubectl run integration-tests \
  --image=ecommerce-api:test \
  --rm -it \
  -e API_URL=http://api:80 \
  -- pytest /tests/

# Verify monitoring
kubectl -n ecommerce port-forward svc/prometheus 9090:9090
# Visit http://localhost:9090

# Check security
kubectl -n ecommerce describe networkpolicy api-netpol
kubectl -n ecommerce get rolebindings
```

## Deployment Checklist

- [ ] Docker image builds successfully
- [ ] Image scanned for vulnerabilities
- [ ] All manifests validated with `kubectl apply --dry-run=server`
- [ ] Database migrations run successfully
- [ ] Health checks respond correctly
- [ ] RBAC roles restricted to minimum permissions
- [ ] Secrets encrypted with sealed-secrets
- [ ] Network policies restrict traffic correctly
- [ ] ResourceQuotas set per namespace
- [ ] HPA configured with appropriate metrics
- [ ] PDB ensures minimum availability
- [ ] Monitoring and logging configured
- [ ] Backup strategy for database tested
- [ ] GitOps pipeline (ArgoCD) syncs automatically
- [ ] Disaster recovery plan documented

## Success Criteria

Project is complete when:

1. ✅ Multi-environment deployment works (dev, staging, prod)
2. ✅ Application scales horizontally with HPA
3. ✅ Database persists data across Pod restarts
4. ✅ Health checks prevent traffic to broken Pods
5. ✅ RBAC restricts API access to ServiceAccount
6. ✅ Network policies limit Pod communication
7. ✅ Secrets are encrypted and rotated
8. ✅ CI/CD pipeline automatically deploys on git push
9. ✅ Monitoring shows metrics (CPU, memory, requests)
10. ✅ Logging aggregates to central location
11. ✅ Graceful shutdown (PDB) during node maintenance
12. ✅ Can perform blue-green or canary deployment

---

## Next Steps

1. **Production Hardening**:
   - Use Sealed Secrets for secret encryption
   - Implement Pod Security Policies
   - Add Pod Network Policy for all deployments
   - Configure audit logging

2. **Advanced Operations**:
   - Implement multi-region failover
   - Configure etcd backups to S3
   - Set up disaster recovery testing
   - Document runbooks for common incidents

3. **Performance**:
   - Monitor and optimize resource requests
   - Implement caching strategy
   - Profile application for bottlenecks
   - Load test with realistic traffic

4. **Security**:
   - Regular image scanning
   - Implement SBOM (Software Bill of Materials)
   - Add threat modeling
   - Compliance scanning (CIS Kubernetes Benchmark)
