# Service Mesh Fundamentals

## Overview

A **Service Mesh** is a dedicated infrastructure layer that handles communication between microservices. Instead of building reliability, security, and observability features into each application, a service mesh provides these as infrastructure primitives that work across all services.

## Mental Model

```
Without Service Mesh:
App A --HTTP--> App B
       (timeout? retry? 
        TLS? logs?)

Problem: Every app implements these patterns
         Some do it wrong
         Hard to enforce consistency
         Difficult to change behavior globally

With Service Mesh:
App A --HTTP--> Sidecar Proxy --HTTP--> Sidecar Proxy --HTTP--> App B
                (handles retries,        (understands  traffic,
                 timeouts, TLS,          metrics,      security,
                 metrics, traces,        routing)      observability)
                 security)

Benefit: All apps get reliability + security + observability
         No app code changes needed
         Consistent behavior across all services
         Can be changed globally without redeploying apps
```

## Architecture

### Sidecar Proxy Pattern

```
┌──────────────────────────────────────┐
│  Kubernetes Pod                      │
│  ┌────────────────────────────────┐  │
│  │  Application Container         │  │
│  │  (your code, unaware of mesh)  │  │
│  │  Listens on localhost:8080     │  │
│  └────────────┬───────────────────┘  │
│               │ calls                 │
│  ┌────────────▼───────────────────┐  │
│  │  Sidecar Proxy (Envoy)         │  │
│  │                                │  │
│  │  - Intercepts all traffic     │  │
│  │  - Handles retries, timeouts  │  │
│  │  - Enforces security policies │  │
│  │  - Collects metrics & traces  │  │
│  │  - Routes traffic             │  │
│  └────────────┬───────────────────┘  │
│               │                       │
└───────────────┼───────────────────────┘
                │
        Network │ traffic
                │
        ┌───────▼──────────────────┐
        │  Network Policies        │
        │  (handled by mesh)       │
        └─────────────────────────┘
```

### Control Plane & Data Plane

```
┌─────────────────────────────────┐
│  Control Plane                  │
│  (Istio/Linkerd)                │
│                                 │
│  - Reads service definitions    │
│  - Generates sidecar config     │
│  - Manages policies             │
│  - Provides telemetry           │
└────────────┬────────────────────┘
             │
             │ Distribute config
             ↓
┌────────────────────────────────┐
│  Data Plane (Sidecars)         │
│                                │
│  Pod A ← Proxy A               │
│  Pod B ← Proxy B               │
│  Pod C ← Proxy C               │
│  Pod D ← Proxy D               │
│                                │
│  All traffic flows through     │
│  proxies (Envoy)              │
└────────────────────────────────┘
```

## Key Capabilities

### 1. Traffic Management

**Canary Deployment** - Gradually shift traffic to new version:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: web-app
spec:
  hosts:
  - web-app
  http:
  - match:
    - uri:
        prefix: /api
    route:
    - destination:
        host: web-app
        subset: v1
      weight: 90  # 90% to v1
    - destination:
        host: web-app
        subset: v2
      weight: 10  # 10% to v2 (new version)
  timeout: 30s
  retries:
    attempts: 3
    perTryTimeout: 10s

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: web-app
spec:
  host: web-app
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        maxRequestsPerConnection: 2
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
```

**A/B Testing** - Route based on request attributes:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: web-app
spec:
  hosts:
  - web-app
  http:
  - match:
    - headers:
        user-type:
          exact: beta-tester  # Beta testers → v2
    route:
    - destination:
        host: web-app
        subset: v2
  - route:
    - destination:
        host: web-app
        subset: v1  # Everyone else → v1
```

### 2. Security (Mutual TLS)

Service mesh automatically encrypts traffic between services:

```
Without Service Mesh:
App A → App B (clear text, insecure)

With Service Mesh:
App A → Sidecar A (clear text, localhost only)
        ↓
        Sidecar A ← → Sidecar B (encrypted with mTLS)
        ↓
        Sidecar B → App B (clear text, localhost only)

Result: All inter-service communication encrypted automatically
        No app code changes needed
        Certificates rotated automatically
```

Enable mTLS:
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: STRICT  # All traffic must use mTLS
```

### 3. Observability

Service mesh automatically collects metrics without code changes:

```yaml
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: custom-metrics
spec:
  metrics:
  - providers:
    - name: prometheus
    dimensions:
    - request_path
    - response_code
    - custom_dimension
```

**Metrics collected automatically:**
- Request rate (requests/second)
- Error rate (% of failed requests)
- Latency (p50, p95, p99)
- Traffic volume (bytes sent/received)

Visualize with Grafana/Prometheus:
```
Graph shows: 
- Service A → Service B: 1000 req/sec
- Service A → Service C: 500 req/sec
- Error rate A→B: 0.5%
- P99 latency A→B: 150ms
```

## Hands-On: Deploy Istio

### Step 1: Install Istio
```bash
# Download Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

# Install
istioctl install --set profile=demo -y

# Verify
kubectl get pod -n istio-system
# Should see: istiod, ingress gateway, egress gateway
```

### Step 2: Enable Sidecar Injection

```bash
# Label namespace for automatic sidecar injection
kubectl label namespace default istio-injection=enabled

# Deploy an app
kubectl apply -f - <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
        version: v1
    spec:
      containers:
      - name: api
        image: kennethreitz/httpbin
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 80
EOF

# Verify sidecar injected
kubectl describe pod -l app=api
# Should see: 2 containers (api + istio-proxy)
```

### Step 3: Create VirtualService

```bash
kubectl apply -f - <<'EOF'
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: api
spec:
  hosts:
  - api
  http:
  - timeout: 5s
    retries:
      attempts: 3
      perTryTimeout: 2s
    route:
    - destination:
        host: api
        port:
          number: 80

---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: api
spec:
  host: api
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
EOF
```

### Step 4: Test Traffic Management

```bash
# Deploy a client
kubectl run -it --rm client --image=curlimages/curl --restart=Never -- sh

# Inside pod, make requests
for i in {1..10}; do curl http://api; done

# Check metrics
kubectl logs -l app=api,version=v1 -c istio-proxy --tail=20

# Metrics show: retries, timeouts, routing decisions
```

## Common Mistakes

**Mistake 1: Service mesh without clear use case**
```
❌ WRONG: Install Istio because it's cool
         Add 1000s of sidecars
         Don't use any features
         Just adds overhead

✅ RIGHT: Install only if you need:
         - Traffic management (canary, A/B testing)
         - Observability across services
         - Security (mTLS)
         - Failure injection (testing)
```

**Mistake 2: Running service mesh without observability setup**
```yaml
# ❌ WRONG: Install Istio, don't set up monitoring
# Metrics generated but not collected

# ✅ RIGHT: Deploy Istio + Prometheus + Grafana
# Then you can visualize:
# - Service dependency graph
# - Error rates and latencies
# - Traffic flows
```

**Mistake 3: Strict mTLS before verifying connectivity**
```yaml
# ❌ WRONG: 
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: STRICT  # Break all non-mTLS traffic immediately

# ✅ RIGHT: Start with PERMISSIVE
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: PERMISSIVE  # Allow both mTLS and plain
    
# Test that everything works
# Then change to STRICT
```

**Mistake 4: Over-complicated traffic policies**
```yaml
# ❌ WRONG: Too many match conditions
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: complex-routing
spec:
  hosts:
  - api
  http:
  - match:
    - headers:
        user-id:
          prefix: "beta"
      sourceLabels:
        env: test
      uri:
          regex: "^/api/v[23]/.*"
    - timeout: 30s
      retries:
        attempts: 5
        perTryTimeout: 10s
      route:
      - destination: api-v2

# Result: Hard to debug, unclear behavior

# ✅ RIGHT: Simple policies
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: simple-routing
spec:
  hosts:
  - api
  http:
  - timeout: 10s
    retries:
      attempts: 3
      perTryTimeout: 3s
    route:
    - destination: api-v1
      weight: 90
    - destination: api-v2
      weight: 10
```

**Mistake 5: Not monitoring proxy resource usage**
```yaml
# ❌ WRONG: Add sidecars without resource requests/limits
# Sidecars consume memory/CPU
# Can cause node pressure and evictions

# ✅ RIGHT: Set resource requests/limits
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: app
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
  - name: istio-proxy  # Sidecar
    resources:
      requests:
        memory: "128Mi"  # Proxy needs memory
        cpu: "100m"      # Proxy needs CPU
      limits:
        memory: "256Mi"
        cpu: "500m"
```

## Production Incident Scenario

### Scenario: "Canary deployment stuck, traffic not shifting to new version"

**Symptoms:**
- Deployed v2 with 10% canary traffic
- Metrics show only v1 in use, 0% v2
- New version pods are running (verified with kubectl)
- No errors in logs

**Investigation:**

```bash
# 1. Check VirtualService
kubectl get vs api -o yaml
# Routes show: v1 90%, v2 10% ✓

# 2. Check DestinationRule
kubectl get dr api -o yaml
# Subsets look correct ✓

# 3. Check if v2 pods have correct labels
kubectl get pods -L version
# NAME                    VERSION
# api-v1-xxxxx            v1
# api-v2-xxxxx            version-not-set  ← PROBLEM!

# 4. Check pod labels
kubectl describe pod api-v2-xxxxx | grep Labels
# Labels: app=api
#         version=v2.0  ← Different label value!
```

**Root Cause:**
- DestinationRule looks for `version: v2`
- Pods are labeled `version: v2.0`
- Labels don't match, traffic can't be routed

**Solution:**

```bash
# 1. Fix the labels
kubectl set labels deployment api-v2 version=v2 --overwrite

# 2. Verify
kubectl get pods -L version
# NAME                    VERSION
# api-v1-xxxxx            v1
# api-v2-xxxxx            v2  ✓

# 3. Watch traffic shift to v2
kubectl logs -l app=api,version=v2 -c istio-proxy --tail=20
# Should see: "route_match" for incoming requests

# 4. Verify metrics
# Prometheus query: rate(requests_total[5m])
# Should show ~10% traffic to v2
```

**Prevention:**
- Test routing with curl before canary
- Monitor "routing_failure" metrics in Prometheus
- Verify pod labels match DestinationRule subsets
- Use automated label validation in CI/CD

## Practice Questions

1. **Scenario:** A service takes 5 seconds to respond sometimes. You want to retry failed requests automatically. Does app code need to change?
   - Answer: No. Define retries in VirtualService. Sidecar handles it transparently.

2. **Decision:** Should you enable mTLS for service-to-service communication?
   - Answer: Yes. Service mesh handles encryption automatically. No code changes needed. Protects against eavesdropping.

3. **Comparison:** Service mesh vs application-level retry logic?
   - Answer: Service mesh (simpler, automatic, consistent). App-level (more control, but duplicated in every service).

4. **Troubleshooting:** Traffic still routes to v1 even though VirtualService says v2 gets 100%. Why?
   - Answer: Pod labels don't match DestinationRule subsets. Verify with `kubectl get pods --show-labels`.

## Further Reading

- [Istio Official Documentation](https://istio.io/latest/docs/)
- [Linkerd Documentation](https://linkerd.io/2/getting-started/)
- [Service Mesh Best Practices](https://www.nginx.com/blog/what-is-a-service-mesh/)
- [Envoy Proxy Documentation](https://www.envoyproxy.io/)
- [Canary Deployments Guide](https://istio.io/latest/docs/tasks/traffic-management/mirroring/)

---

**Next:** Learn about eBPF for kernel-level observability and security that captures every packet without sampling.
