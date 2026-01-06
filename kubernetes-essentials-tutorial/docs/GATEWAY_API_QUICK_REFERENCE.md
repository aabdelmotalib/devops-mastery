# Gateway API Quick Reference

## Installation

```bash
# AWS ALB Controller (supports Gateway API)
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system --set clusterName=my-cluster

# NGINX Gateway Controller
helm repo add nginx-stable https://helm.nginx.com/stable
helm install nginx-gateway nginx-stable/nginx-gateway
```

## Core Resources

### 1. GatewayClass (One per implementation)

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: GatewayClass
metadata:
  name: aws-alb
spec:
  controllerName: aws-load-balancer-controller
```

### 2. Gateway (Per team/environment)

```yaml
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
```

### 3. HTTPRoute (Per application)

```yaml
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: api-route
spec:
  parentRefs:
  - name: my-gateway
  hostnames:
  - api.example.com
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api-service
      port: 8080
```

## Common Patterns

### Weighted Traffic Split (Canary)

```yaml
backendRefs:
- name: app-stable
  port: 8080
  weight: 90
- name: app-canary
  port: 8080
  weight: 10
```

### Path-Based Routing

```yaml
rules:
- matches:
  - path:
      type: PathPrefix
      value: /api/
  backendRefs:
  - name: api-service
    port: 8080

- matches:
  - path:
      type: PathPrefix
      value: /static/
  backendRefs:
  - name: static-service
    port: 80
```

### Request Header Modification

```yaml
filters:
- type: RequestHeaderModifier
  requestHeaderModifier:
    add:
      X-Request-ID: "uuid"
      X-API-Version: "v2"
    remove:
    - X-Internal-Header
```

### URL Rewriting

```yaml
filters:
- type: URLRewrite
  urlRewrite:
    path:
      type: ReplaceFullPath
      replaceFullPath: /v2/api/endpoint
```

### HTTP to HTTPS Redirect

```yaml
rules:
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

## Kubectl Commands

```bash
# List GatewayClasses
kubectl get gatewayclasses

# List Gateways
kubectl get gateway -A

# List HTTPRoutes
kubectl get httproute -A

# Describe a gateway
kubectl describe gateway my-gateway -n infrastructure

# Check route status
kubectl describe httproute api-route

# Get gateway's external IP
kubectl get gateway my-gateway -n infrastructure -o wide

# Watch for route attachments
kubectl get httproute api-route -w
```

## Comparison: Ingress vs Gateway API

| Feature | Ingress | Gateway API |
|---------|---------|------------|
| **Protocols** | HTTP/HTTPS | HTTP, HTTPS, TCP, UDP |
| **Routing** | Path/host | Path, host, method, header |
| **Status** | Limited | Detailed conditions |
| **RBAC** | Limited | Fine-grained (allowedRoutes) |
| **Traffic Mgmt** | Annotations | Standard filters |
| **Vendors** | Many | Growing support |
| **Learning Curve** | Easy | Moderate |

## Architecture

```
GatewayClass
    ↓
  (1 per vendor type)
    ↓
  Gateway (Create infrastructure)
    ↓
  (1+ Listeners: protocols, ports, TLS)
    ↓
  HTTPRoute (Route traffic)
    ↓
  (App developers create these)
    ↓
  Backend Services
```

## Best Practices

✅ **Use GatewayClass per implementation type** (AWS ALB, NGINX, etc.)  
✅ **Create Gateway per team/environment** with proper namespace isolation  
✅ **Allow app teams to create HTTPRoutes only** (not Gateways)  
✅ **Label namespaces** for RBAC (`gateway: enabled`)  
✅ **Use filters** for request/response modification  
✅ **Implement canary deployments** with weighted backends  
✅ **Configure TLS in Gateway** (not in routes)  
✅ **Add tracing headers** via request filters  
✅ **Use multiple listeners** for different protocols/ports  
✅ **Monitor route attachment status** for troubleshooting  

## Migration from Ingress

### Phase 1: Parallel (Both active)
- Keep Ingress resources
- Add Gateway API resources
- Monitor both

### Phase 2: Gradual (Increase Gateway %)
- Week 1: 80% Ingress, 20% Gateway
- Week 2: 50% Ingress, 50% Gateway
- Week 3: 20% Ingress, 80% Gateway
- Week 4: 0% Ingress, 100% Gateway

### Phase 3: Complete
- Remove all Ingress resources
- Full Gateway API adoption

## Troubleshooting

### Route won't attach to gateway

```bash
# Check namespace has required label
kubectl label namespace my-app gateway=enabled

# Verify parentRef matches
kubectl describe httproute my-route

# Check gateway's allowedRoutes
kubectl describe gateway my-gateway -n infrastructure
```

### TLS certificate not found

```bash
# Ensure secret is in Gateway's namespace
kubectl get secret tls-cert -n infrastructure

# Or reference from different namespace (if supported)
# certificateRefs:
# - name: tls-cert
#   namespace: certs
```

### External IP not assigned

```bash
# Check controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Check gateway status
kubectl get gateway -o wide
```

## HTTP Route Status

```bash
# Check if route is attached
kubectl describe httproute api-route | grep -A 5 "Parents"

# Expected output: Accepted: True, PartiallyInvalid: False
```

## Resources

- **Gateway API**: https://gateway.api.dev/
- **Kubernetes Docs**: https://kubernetes.io/docs/concepts/services-networking/gateway/
- **AWS ALB Controller**: https://github.com/aws/aws-load-balancer-controller
- **NGINX Gateway**: https://github.com/nginxinc/nginx-kubernetes-gateway
