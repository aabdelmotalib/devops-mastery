# Module 13: Gateway API - Modern Kubernetes Networking

## Overview

The **Kubernetes Gateway API** is the next-generation networking model that replaces Ingress with a more flexible, expressive, and role-based approach. It provides better separation of concerns, improved routing capabilities, and native support for advanced traffic management features like load balancing, traffic splitting, and weighted routing.

**Key Improvement**: Gateway API is the standard successor to Ingress, endorsed by the Kubernetes networking SIG and multiple vendors (AWS ALB Controller, Kong, Envoy, NGINX, etc.).

## Why Gateway API? (Ingress Limitations)

### Problems with Ingress

```
Ingress Limitations:
├── Single resource for all routing logic
├── Limited to HTTP/HTTPS
├── No native request/response modification
├── Minimal traffic management features
├── Poor separation of concerns
├── Vendor-specific annotations (non-standard)
└── No built-in load balancing strategies
```

### Gateway API Advantages

```
Gateway API Benefits:
├── Multi-layer architecture (GatewayClass → Gateway → Routes)
├── Support for HTTP, HTTPS, TCP, UDP
├── Native request/response filters
├── Advanced traffic management (weighted routing, mirroring)
├── Clear RBAC roles (platform → platform-engineer → app-developer)
├── Standard field names across all vendors
└── Built-in resilience patterns
```

## Gateway API Architecture

### Component Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│ GatewayClass                                             │
│ (Vendor/Implementation: AWS ALB, Kong, NGINX, Envoy)    │
│ - Defines capabilities                                   │
│ - Created by platform team                              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Gateway                                                  │
│ (Infrastructure setup for a team/environment)           │
│ - Listeners for different protocols/ports               │
│ - TLS configuration                                     │
│ - Created by platform-engineer                         │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Routes (HTTPRoute, TCPRoute, UDPRoute)                  │
│ (App-specific routing rules)                             │
│ - Request matching rules                                │
│ - Backend services                                      │
│ - Filters and policies                                  │
│ - Created by app-developers                            │
└─────────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. GatewayClass

GatewayClass defines the capabilities of a gateway implementation.

```yaml
# Created by: Platform team (once per cluster)
# Purpose: Vendor/implementation definition
apiVersion: gateway.networking.k8s.io/v1beta1
kind: GatewayClass
metadata:
  name: aws-alb              # Implementation identifier
spec:
  controllerName: aws-load-balancer-controller
  # Optional: Additional parameters for the implementation
  parametersRef:
    group: gateway.networking.k8s.io
    kind: AwsLoadBalancerControllerConfig
    name: alb-config
```

**Characteristics**:
- Represents a specific gateway implementation
- One GatewayClass per implementation type
- Contains controller information and parameters
- Multiple GatewayClasses can coexist

### 2. Gateway

Gateway creates actual infrastructure resources (load balancers) and binds to a GatewayClass.

```yaml
# Created by: Platform-engineer
# Purpose: Infrastructure setup for a team
apiVersion: gateway.networking.k8s.io/v1beta1
kind: Gateway
metadata:
  name: production-gateway
  namespace: infrastructure
spec:
  gatewayClassName: aws-alb        # Reference to GatewayClass
  
  # Listeners define entry points (protocols/ports)
  listeners:
  
  # HTTP listener
  - name: http
    protocol: HTTP
    port: 80
    hostname: "*.example.com"       # Optional: restrict domains
    allowedRoutes:
      namespaces:
        from: Selector              # Routes from specific namespaces
        selector:
          matchLabels:
            gateway: enabled        # Only namespaces with this label

  # HTTPS listener
  - name: https
    protocol: HTTPS
    port: 443
    hostname: "*.example.com"
    tls:
      mode: Terminate               # TLS termination at gateway
      certificateRefs:
      - name: example-cert
        kind: Secret
        group: ""
    allowedRoutes:
      namespaces:
        from: All                   # Accept from all namespaces

  # TCP listener (for non-HTTP protocols)
  - name: database
    protocol: TCP
    port: 5432
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            database-access: allowed
```

**Gateway Features**:
- Multiple listeners on same gateway
- Different protocols per listener
- RBAC via allowedRoutes (restrict which namespaces can attach)
- TLS termination configuration
- Hostname-based routing

### 3. HTTPRoute

HTTPRoute defines HTTP-level routing rules.

```yaml
# Created by: App developers
# Purpose: Route traffic for a specific application
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: api-route
  namespace: production
spec:
  # Which gateway(s) this route binds to
  parentRefs:
  - name: production-gateway
    namespace: infrastructure
    sectionName: https             # Specific listener (optional)
  
  # Match conditions (multiple rules = OR logic)
  hostnames:
  - api.example.com
  - api-v2.example.com
  
  rules:
  # Rule 1: API v2 routing
  - matches:
    - path:
        type: PathPrefix
        value: /v2/
      method: GET
    
    # Filters for request modification
    filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
          X-API-Version: "2"
    
    # Backend services
    backendRefs:
    - name: api-v2-service
      port: 8080
      weight: 100              # Load balancing weight
  
  # Rule 2: Canary deployment (traffic splitting)
  - matches:
    - path:
        type: PathPrefix
        value: /api/
    
    backendRefs:
    - name: api-service-stable
      port: 8080
      weight: 90               # 90% to stable
    - name: api-service-canary
      port: 8080
      weight: 10               # 10% to canary (for testing)
  
  # Rule 3: Redirect HTTP to HTTPS
  - matches:
    - path:
        type: PathPrefix
        value: /
    filters:
    - type: RequestRedirect
      requestRedirect:
        scheme: https
        statusCode: 301
```

### 4. TCPRoute (Non-HTTP Protocols)

```yaml
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: TCPRoute
metadata:
  name: database-route
  namespace: production
spec:
  parentRefs:
  - name: production-gateway
    namespace: infrastructure
    sectionName: database      # TCP listener
  
  rules:
  - backendRefs:
    - name: postgres-service
      port: 5432
```

## Gateway API Features Deep Dive

### 1. Weighted Traffic Splitting (Canary Deployments)

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: traffic-split-example
spec:
  parentRefs:
  - name: production-gateway
  hostnames:
  - app.example.com
  
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    
    backendRefs:
    # Current stable version: 95% traffic
    - name: app-v1-service
      port: 8080
      weight: 95
    
    # New version being tested: 5% traffic
    - name: app-v2-service
      port: 8080
      weight: 5
```

**Use Case**: Gradually increase new version traffic (5% → 25% → 50% → 100%) based on metrics.

### 2. Request Filters

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: filter-example
spec:
  parentRefs:
  - name: production-gateway
  hostnames:
  - api.example.com
  
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    
    filters:
    # Add response headers
    - type: ResponseHeaderModifier
      responseHeaderModifier:
        add:
          X-API-Timestamp: "2024-01-01"
          Cache-Control: "public, max-age=3600"
        remove:
        - Server
        - X-Powered-By
    
    # Add request headers
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
          X-Request-ID: "generated-uuid"
          X-Forwarded-For: "client-ip"
        set:
          X-API-Key: "service-key"
    
    # Request body size limit
    - type: RequestSize
      requestSize:
        maxBodyBytes: 5242880    # 5MB
    
    # URL rewriting
    - type: URLRewrite
      urlRewrite:
        path:
          type: ReplaceFullPath
          replaceFullPath: /v2/api/endpoint
    
    # Redirect requests
    - type: RequestRedirect
      requestRedirect:
        scheme: https
        hostname: new-domain.com
        port: 8443
        statusCode: 302
    
    backendRefs:
    - name: api-service
      port: 8080
```

### 3. Path-Based Routing

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: multi-service-routing
spec:
  parentRefs:
  - name: production-gateway
  hostnames:
  - example.com
  
  rules:
  # Route 1: /api/* → API service
  - matches:
    - path:
        type: PathPrefix
        value: /api/
      method: GET
    
    backendRefs:
    - name: api-service
      port: 8080
  
  # Route 2: /static/* → Static content
  - matches:
    - path:
        type: PathPrefix
        value: /static/
    
    backendRefs:
    - name: static-service
      port: 80
  
  # Route 3: /admin/* (with auth)
  - matches:
    - path:
        type: PathPrefix
        value: /admin/
    
    filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
          X-Require-Auth: "true"
    
    backendRefs:
    - name: admin-service
      port: 8080
  
  # Default route
  - backendRefs:
    - name: web-service
      port: 3000
```

### 4. Hostname-Based (Virtual Hosting)

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: virtual-hosting
spec:
  parentRefs:
  - name: production-gateway
  
  rules:
  # api.example.com
  - hostnames:
    - api.example.com
    
    backendRefs:
    - name: api-service
      port: 8080
  
  # admin.example.com
  - hostnames:
    - admin.example.com
    
    backendRefs:
    - name: admin-service
      port: 9000
  
  # Wildcard: *.cdn.example.com
  - hostnames:
    - "*.cdn.example.com"
    
    backendRefs:
    - name: cdn-service
      port: 80
  
  # www.example.com (default)
  - hostnames:
    - www.example.com
    - example.com
    
    backendRefs:
    - name: web-service
      port: 3000
```

### 5. Timeout and Retry Configuration (Policy)

```yaml
# Timeout and retry policies (using PolicyRef if supported by implementation)
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: TimeoutPolicy
metadata:
  name: api-timeout
  namespace: production
spec:
  timeoutSeconds: 30           # 30-second timeout

---
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: resilient-api
spec:
  parentRefs:
  - name: production-gateway
  hostnames:
  - api.example.com
  
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    
    backendRefs:
    - name: api-service
      port: 8080
    
    # Implementation-specific (varies by controller)
    # Some support direct timeout in HTTPRoute
    timeoutSeconds: 30
    
    # Retry configuration
    retries:
      attempts: 3
      backoff:
        type: Exponential
        baseDuration:
          seconds: 1
```

## Production Best Practices

### 1. Namespace Organization

```yaml
# Infrastructure namespace (platform team)
apiVersion: v1
kind: Namespace
metadata:
  name: infrastructure
  labels:
    environment: production

---
# GatewayClass definition (created once)
apiVersion: gateway.networking.k8s.io/v1beta1
kind: GatewayClass
metadata:
  name: aws-alb
  namespace: infrastructure
spec:
  controllerName: aws-load-balancer-controller

---
# Gateway per team/environment
apiVersion: gateway.networking.k8s.io/v1beta1
kind: Gateway
metadata:
  name: team-a-gateway
  namespace: infrastructure
spec:
  gatewayClassName: aws-alb
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    hostname: "*.team-a.example.com"
    tls:
      mode: Terminate
      certificateRefs:
      - name: team-a-cert
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            team: team-a
```

### 2. RBAC and Multi-Tenancy

```yaml
# Namespace label for RBAC
apiVersion: v1
kind: Namespace
metadata:
  name: team-a
  labels:
    team: team-a
    gateway: enabled

---
# App developers can only manage HTTPRoutes, not Gateways
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: route-manager
  namespace: team-a
rules:
- apiGroups:
  - gateway.networking.k8s.io
  resources:
  - httproutes
  verbs:
  - create
  - get
  - list
  - watch
  - update
  - patch
  - delete
- apiGroups:
  - gateway.networking.k8s.io
  resources:
  - gateways
  verbs:
  - get
  - list
  - watch

---
# Platform engineers manage Gateways
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: gateway-manager
rules:
- apiGroups:
  - gateway.networking.k8s.io
  resources:
  - gateways
  - gatewayclasses
  verbs:
  - "*"
```

### 3. TLS/HTTPS Configuration

```yaml
# Create certificate secret (or use cert-manager)
apiVersion: v1
kind: Secret
metadata:
  name: tls-cert
  namespace: infrastructure
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTi... (base64)
  tls.key: LS0tLS1CRUdJTi... (base64)

---
# Gateway with TLS
apiVersion: gateway.networking.k8s.io/v1beta1
kind: Gateway
metadata:
  name: secure-gateway
  namespace: infrastructure
spec:
  gatewayClassName: aws-alb
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      options:
        gateway.networking.k8s.io/alpn: "h2,http/1.1"
        gateway.networking.k8s.io/min-version: "1.2"
      certificateRefs:
      - name: tls-cert
        kind: Secret
        group: ""
  
  # Redirect HTTP to HTTPS
  - name: http
    protocol: HTTP
    port: 80
```

### 4. Monitoring and Observability

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: observable-api
  namespace: production
  labels:
    monitoring: enabled
spec:
  parentRefs:
  - name: production-gateway
  hostnames:
  - api.example.com
  
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    
    # Add tracing headers
    filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
          X-Trace-ID: "generated-uuid"
          X-Span-ID: "generated-uuid"
    
    # Add metrics labels
    - type: ResponseHeaderModifier
      responseHeaderModifier:
        add:
          X-Route-Name: "observable-api"
          X-Service-Version: "v1"
    
    backendRefs:
    - name: api-service
      port: 8080
      weight: 100
```

## Comparison: Ingress vs Gateway API

| Feature | Ingress | Gateway API |
|---------|---------|------------|
| **Protocols** | HTTP/HTTPS only | HTTP, HTTPS, TCP, UDP |
| **Routing** | Path/host based | Path/host/method/header |
| **RBAC** | All-or-nothing | Fine-grained roles |
| **Traffic Management** | Limited | Weighted, mirroring, retries |
| **Request Filtering** | Vendor annotations | Standard filters |
| **Multi-tenancy** | Poor | Excellent (allowedRoutes) |
| **Status/Conditions** | Limited | Detailed status |
| **Learning Curve** | Easy | Moderate |

## Migration Path: Ingress → Gateway API

### Phase 1: Parallel Operation (Months 1-2)

```yaml
# Keep existing Ingress resources
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
spec:
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8080

---
# Add Gateway API resources alongside
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: api-route
spec:
  parentRefs:
  - name: production-gateway
  hostnames:
  - api.example.com
  rules:
  - backendRefs:
    - name: api-service
      port: 8080
```

### Phase 2: Gradual Traffic Migration (Months 2-4)

Monitor both Ingress and Gateway API traffic. Increase Gateway API percentage:
- Week 1: Ingress 100%, Gateway 0%
- Week 2: Ingress 80%, Gateway 20%
- Week 3: Ingress 50%, Gateway 50%
- Week 4: Ingress 20%, Gateway 80%
- Week 5: Ingress 0%, Gateway 100%

### Phase 3: Complete Migration (Month 5+)

Remove Ingress resources and fully adopt Gateway API.

## Hands-On Practice

### Task 1: Deploy Gateway API Controller

```bash
# Install AWS ALB Controller (supports Gateway API)
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=my-cluster

# Or NGINX Gateway Controller
helm repo add nginx-stable https://helm.nginx.com/stable
helm install nginx-gateway nginx-stable/nginx-gateway
```

### Task 2: Create GatewayClass and Gateway

```bash
# Create infrastructure namespace
kubectl create namespace infrastructure

# Apply GatewayClass
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1beta1
kind: GatewayClass
metadata:
  name: aws-alb
spec:
  controllerName: aws-load-balancer-controller
EOF

# Apply Gateway
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1beta1
kind: Gateway
metadata:
  name: my-gateway
  namespace: infrastructure
spec:
  gatewayClassName: aws-alb
  listeners:
  - name: http
    protocol: HTTP
    port: 80
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - name: tls-cert
EOF

# Verify gateway status
kubectl get gateway -n infrastructure -o wide
```

### Task 3: Create HTTPRoute

```bash
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: demo-route
  namespace: default
spec:
  parentRefs:
  - name: my-gateway
    namespace: infrastructure
  hostnames:
  - demo.example.com
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: demo-service
      port: 80
EOF

# Verify route attachment
kubectl describe httproute demo-route
```

### Task 4: Test Weighted Routing

```bash
# Create two versions
kubectl create deployment app-v1 --image=nginx:1.19 -l app=app,version=v1
kubectl create deployment app-v2 --image=nginx:1.21 -l app=app,version=v2

# Create services
kubectl expose deployment app-v1 --name=app-v1 --port=80
kubectl expose deployment app-v2 --name=app-v2 --port=80

# Apply route with traffic splitting
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: app-canary
spec:
  parentRefs:
  - name: my-gateway
    namespace: infrastructure
  hostnames:
  - app.example.com
  rules:
  - backendRefs:
    - name: app-v1
      port: 80
      weight: 90
    - name: app-v2
      port: 80
      weight: 10
EOF

# Send requests and verify distribution
for i in {1..100}; do
  curl http://app.example.com/
done | grep -c "nginx"
```

## Common Mistakes

### Mistake 1: Not Labeling Namespaces for RBAC

```yaml
# ❌ Wrong: Gateway allowedRoutes uses label selector
allowedRoutes:
  namespaces:
    from: Selector
    selector:
      matchLabels:
        gateway: enabled

# But namespace doesn't have the label
kubectl create namespace app
# Error: HTTPRoute won't attach to Gateway

# ✅ Correct
kubectl label namespace app gateway=enabled
```

### Mistake 2: Mixing Route Types

```yaml
# ❌ Wrong: HTTPRoute can't handle TCP traffic
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
spec:
  rules:
  - backendRefs:
    - name: database  # TCP database service

# ✅ Correct: Use TCPRoute for non-HTTP
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: TCPRoute
spec:
  rules:
  - backendRefs:
    - name: database
      port: 5432
```

### Mistake 3: Forgetting parentRefs

```yaml
# ❌ Wrong: Route won't attach to gateway
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: orphaned-route
spec:
  rules:
  - backendRefs:
    - name: service

# ✅ Correct: Always specify parentRefs
parentRefs:
- name: my-gateway
  namespace: infrastructure
```

### Mistake 4: Incorrect Filter Ordering

```yaml
# ❌ Might fail: Order matters
filters:
- type: URLRewrite         # URL changed
- type: RequestHeaderModifier # Headers reference old URL

# ✅ Correct: Match headers to rewritten URL
filters:
- type: RequestHeaderModifier
  requestHeaderModifier:
    add:
      X-Original-Path: "/api"
- type: URLRewrite
  urlRewrite:
    path:
      type: ReplaceFullPath
      replaceFullPath: /v2/api
```

### Mistake 5: Forgetting TLS Secret in Same Namespace

```yaml
# ❌ Wrong: TLS secret not found
spec:
  listeners:
  - protocol: HTTPS
    tls:
      certificateRefs:
      - name: tls-cert        # Secret in different namespace

# ✅ Correct: Secret must be in Gateway namespace OR referred with namespace
spec:
  listeners:
  - protocol: HTTPS
    tls:
      certificateRefs:
      - name: tls-cert
        group: ""
        kind: Secret
        namespace: certs       # Specify if different namespace
```

## Summary

| Topic | Key Points |
|-------|-----------|
| **Architecture** | GatewayClass → Gateway → Routes (hierarchical) |
| **Roles** | Platform → Platform-engineer → App-developer |
| **Protocols** | HTTP, HTTPS, TCP, UDP (beyond Ingress) |
| **Routing** | Path, host, method, headers, and more |
| **Traffic Management** | Weighted routing, mirroring, retries |
| **Filters** | Request/response modification, redirects |
| **RBAC** | Fine-grained namespace-level control |
| **Migration** | Run Ingress and Gateway API in parallel |
| **Best Practice** | Use Gateway API for new deployments |

## Further Learning

- **Official Docs**: https://gateway.api.dev/
- **Kubernetes Docs**: https://kubernetes.io/docs/concepts/services-networking/gateway/
- **Controller Implementations**:
  - AWS ALB Controller: https://github.com/aws/aws-load-balancer-controller
  - NGINX Gateway Controller: https://github.com/nginxinc/nginx-kubernetes-gateway
  - Kong Gateway Controller: https://github.com/Kong/kubernetes-ingress-controller

---

## Practice Questions

### MCQ 1: Gateway API Architecture
Which component defines the vendor implementation and capabilities?

**A)** HTTPRoute  
**B)** GatewayClass  
**C)** Gateway  
**D)** RoutePolicy  

**Answer**: B - GatewayClass defines the implementation (AWS ALB, Kong, NGINX, etc.)

### MCQ 2: Weighted Routing
What does a weight of 5 mean when specifying multiple backendRefs?

**A)** Maximum 5 requests per second  
**B)** 5% of traffic routed to this backend  
**C)** Retry maximum of 5 times  
**D)** 5MB maximum request size  

**Answer**: B - Weights are proportional; weight: 5 with weight: 95 = 5% vs 95%

### MCQ 3: RBAC with Gateways
How do you prevent app developers from modifying Gateways?

**A)** Delete the Gateway RBAC permissions  
**B)** Use allowedRoutes with namespace selector  
**C)** Create separate GatewayClass for each team  
**D)** Apply NetworkPolicy to gateway namespace  

**Answer**: A - Remove 'gateways' verb from developer Role

### MCQ 4: Route Attachment
What happens if a namespace doesn't have the required label for Gateway's allowedRoutes?

**A)** Route is automatically deleted  
**B)** Route stays in Pending status, never attaches  
**C)** Route fails with validation error  
**D)** Gateway rejects the entire namespace  

**Answer**: B - Route remains in Pending with detailed conditions

### MCQ 5: TLS Configuration
What is the difference between TLS mode "Terminate" and "Passthrough"?

**A)** Terminate = encrypted, Passthrough = unencrypted  
**B)** Terminate = gateway decrypts, Passthrough = backend decrypts  
**C)** Terminate = one certificate, Passthrough = multiple certificates  
**D)** Terminate = HTTP only, Passthrough = HTTPS only  

**Answer**: B - Terminate: Gateway decrypts/re-encrypts to backend. Passthrough: TLS tunnel to backend.

---

## Scenario: Production Canary Deployment

**Situation**: You need to deploy a new API version with 10% traffic initially, monitoring for errors.

**Requirements**:
- 90% traffic to stable-api service (port 8080)
- 10% traffic to canary-api service (port 8080)
- Add tracing headers for monitoring
- Both services in production namespace

**Solution**:

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: api-canary-deployment
  namespace: production
spec:
  parentRefs:
  - name: production-gateway
    namespace: infrastructure
  hostnames:
  - api.example.com
  
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    
    filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
          X-Trace-ID: "uuid-generated"
          X-Deployment: "canary-v2.1"
    
    - type: ResponseHeaderModifier
      responseHeaderModifier:
        add:
          X-API-Version: "determined-by-backend"
    
    backendRefs:
    # Stable version: 90%
    - name: api-stable-service
      port: 8080
      weight: 90
    
    # Canary version: 10%
    - name: api-canary-service
      port: 8080
      weight: 10
```

**Monitoring steps**:
```bash
# 1. Check route status
kubectl get httproute api-canary-deployment -n production -o wide

# 2. Monitor canary error rate
kubectl logs -l app=api-canary -n production | grep ERROR

# 3. Once stable, increase canary to 25%
kubectl patch httproute api-canary-deployment -n production \
  --type='json' -p='[
  {"op":"replace","path":"/spec/rules/0/backendRefs/1/weight","value":25},
  {"op":"replace","path":"/spec/rules/0/backendRefs/0/weight","value":75}
]'

# 4. Gradually increase to 100% over hours
# 4. Once fully stable, remove old version
```

---

**Gateway API mastery enables**:
✅ Modern, flexible Kubernetes networking  
✅ Better multi-tenancy and RBAC  
✅ Advanced traffic management patterns  
✅ Vendor-independent standardization  
✅ Production-ready microservices architecture
