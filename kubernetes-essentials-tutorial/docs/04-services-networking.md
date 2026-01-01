# Module 4: Services & Networking

## Overview

Services expose Pods to the network and provide stable endpoints for communication. Understanding Services is critical for deploying applications that communicate within and outside the cluster.

## Pod-to-Pod Communication

### Direct Pod Communication

Pods have IP addresses and can communicate directly:

```
Pod A (10.0.0.1)  ←→  Pod B (10.0.0.2)
 ```

Pod IP is assigned from cluster's pod network CIDR. Pods see each other through this network, managed by a CNI (Container Network Interface) plugin like Flannel or Calico.

**Issue**: Pod IP is temporary. When Pod recreates, it gets a new IP. Code shouldn't hardcode Pod IPs.

**Solution**: Use Services for stable endpoints.

## Service Types

### ClusterIP (Internal Service)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  type: ClusterIP              # Default
  selector:
    app: api                   # Route to Pods with this label
  ports:
  - port: 80                   # Service port (virtual)
    targetPort: 8080           # Container port in Pod
    protocol: TCP
```

**Characteristics**:
- Internal-only (no external access)
- Virtual IP (ClusterIP) created by kube-proxy
- Stable DNS name: `api-service` (within namespace)
- Load balances across matching Pods
- Default type

**DNS resolution**:
```bash
# Same namespace
curl http://api-service:80

# Different namespace
curl http://api-service.staging:80

# Full FQDN
curl http://api-service.staging.svc.cluster.local:80
```

### NodePort (External Access via Node IP)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-service
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - port: 80          # Service port
    targetPort: 8080  # Pod port
    nodePort: 30000   # Host port (30000-32767 range)
```

**Characteristics**:
- Exposes service on every Node's IP
- Access via `<node-ip>:30000`
- ClusterIP also created (internal service)
- Useful for small clusters, testing

**Access pattern**:
```bash
kubectl get nodes -o wide
# Find node IPs

curl http://<node-ip>:30000
# Reaches the service, load-balanced to Pods
```

**Limitations**:
- Each service needs a different port
- Nodes' IPs can change
- Not suitable for production with many services

### LoadBalancer (Cloud External Load Balancer)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-lb
spec:
  type: LoadBalancer
  selector:
    app: api
  ports:
  - port: 80
    targetPort: 8080
```

**Characteristics**:
- Cloud provider provisions external load balancer (AWS ELB, GCP LB, Azure LB)
- External IP assigned by cloud provider
- ClusterIP and NodePort also created
- Each service gets its own load balancer (cost considerations)

**Access**:
```bash
kubectl get svc api-lb
# EXTERNAL-IP: 35.192.1.1 (assigned by cloud provider)

curl http://35.192.1.1:80
```

**Use cases**:
- Simple deployment with few services
- Direct external access needed
- Each service worth the cost of an external LB

### ExternalName (Alias to External Service)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: db.example.com
  ports:
  - port: 5432
```

**Characteristics**:
- No ClusterIP
- DNS CNAME points to external service
- Pods access external service via Service name

**Use case**: Legacy database outside cluster, migrating to Kubernetes gradually.

```bash
# Inside Pod
curl external-db:5432  # Resolved to db.example.com:5432
```

## Service Endpoints and Load Balancing

### How Services Find Pods

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api      # Find Pods with label app=api
  ports:
  - port: 80
    targetPort: 8080
```

Service controller constantly watches:
1. Service selector (app=api)
2. Pods with matching labels
3. Creates Endpoints object linking service to pod IPs

```bash
# View endpoints for service
kubectl get endpoints api
# NAME   ENDPOINTS              AGE
# api    10.0.0.1:8080,10.0.0.2:8080,10.0.0.3:8080

# If no endpoints, service selector doesn't match any pods
```

### Load Balancing Algorithms

**Round-robin** (default):
1. Request 1 → Pod A
2. Request 2 → Pod B
3. Request 3 → Pod C
4. Request 4 → Pod A

**Sticky sessions** (session affinity):
```yaml
spec:
  sessionAffinity: ClientIP  # Route client to same pod
  sessionAffinityConfig:
    clientIPConfig:
      timeoutSeconds: 10800  # 3 hours
```

Traffic from same client IP always routes to same Pod. Useful for stateful apps (not recommended; prefer stateless design).

## Headless Services

### Use Case: Direct Pod Communication

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None          # Headless (no virtual IP)
  selector:
    app: postgres
  ports:
  - port: 5432
```

**Characteristics**:
- No ClusterIP assigned
- DNS returns Pod IPs directly
- Each Pod gets DNS record: `pod-name.service-name.svc.cluster.local`

**Use case**: StatefulSets, Pods need to communicate with specific instance.

```bash
# DNS A records for individual Pods
postgres-0.postgres
postgres-1.postgres
postgres-2.postgres
```

## Ingress: HTTP(S) Routing

### Service vs Ingress

```
External Traffic
    ↓
Ingress (routing rules, SSL/TLS)
    ↓
Service (load balance to pods)
    ↓
Pods
```

**Service**: Layer 4 (TCP/UDP) load balancing  
**Ingress**: Layer 7 (HTTP/HTTPS) routing (path-based, host-based)

### Ingress Specification

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
spec:
  ingressClassName: nginx    # Which controller processes this?
  
  rules:
  # Host-based routing
  - host: api.example.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: api-v1
            port:
              number: 80
      - path: /v2
        pathType: Prefix
        backend:
          service:
            name: api-v2
            port:
              number: 80
  
  - host: web.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
  
  # TLS/SSL
  tls:
  - hosts:
    - api.example.com
    - web.example.com
    secretName: tls-cert
```

### Ingress Controllers

Ingress is a Kubernetes API object. An Ingress Controller (running as Deployment) watches Ingress objects and configures the actual reverse proxy:

**Popular controllers**:
- NGINX Ingress Controller (most common)
- Traefik
- AWS ALB Ingress Controller
- Kong

Installation (NGINX example):
```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.0.0/deploy/static/provider/cloud/deploy.yaml
```

### Ingress vs LoadBalancer Service

**LoadBalancer**:
- One service = one external IP/LB
- Cost: Multiple LBs = expensive
- Simple setup
- Use for specific services needing external access

**Ingress**:
- Multiple services behind one LB
- Cost-effective (one LB, many services)
- Layer 7 routing (better UX)
- Requires Ingress Controller
- Use for HTTP(S) services with complex routing

## Network Policies

### Default Network Behavior

By default, Pods can communicate with all other Pods in the cluster:
```
Pod A → Pod B (any namespace)
Pod A → Pod C (any namespace)
```

### Network Policy: Firewall Rules

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-only
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: database  # This policy applies to database pods
  
  policyTypes:
  - Ingress           # Control incoming traffic
  - Egress            # Control outgoing traffic
  
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          environment: production
      podSelector:
        matchLabels:
          app: api    # Only api pods can reach database
    ports:
    - protocol: TCP
      port: 5432
  
  egress:
  - to:
    - namespaceSelector: {}  # Allow egress to any namespace
    ports:
    - protocol: TCP
      port: 443      # Only allow HTTPS (DNS, etc.)
```

**Deny-all pattern** (default deny, then allow specific):
```yaml
---
# Deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
spec:
  podSelector: {}  # Applies to all pods
  policyTypes:
  - Ingress

---
# Allow from specific pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
spec:
  podSelector:
    matchLabels:
      app: api
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: web
```

### Network Policy Limitations

- Requires CNI plugin supporting network policies (Calico, Cilium, Kube-router)
- Doesn't support blocking at container level within Pod
- No DNS-based filtering (IP/port only)

## DNS in Kubernetes

### CoreDNS: Internal DNS

CoreDNS pod (usually in kube-system) runs as:
```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns
```

### DNS Names

**Service DNS**:
```
<service-name>.<namespace>.svc.cluster.local
```

**Pod DNS** (rarely used directly):
```
<pod-ip-with-dashes>.<namespace>.pod.cluster.local
```

Example:
```
Pod IP: 10.0.0.1 → DNS: 10-0-0-1.default.pod.cluster.local
Service: my-service.default.svc.cluster.local
```

### DNS Queries Inside Cluster

```bash
# Inside Pod, query DNS
kubectl run -it debug --image=busybox -- sh

# From Pod:
nslookup my-service              # Short name (same namespace)
nslookup my-service.staging      # Different namespace
nslookup my-service.staging.svc.cluster.local  # Full FQDN
```

### External DNS

If you want Kubernetes Services/Ingresses to be accessible externally, use External DNS project:

```bash
# Automatically creates DNS records in external DNS (Route53, CloudDNS)
# When you create Ingress, DNS record automatically created
```

## Common Mistakes

### Mistake 1: Service Selector Doesn't Match Pod Labels

```yaml
# Service
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api-server  # ← Selector

---
# Pod
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: api         # ← Doesn't match!
```

**Problem**: Service has no endpoints; requests fail.

**Solution**: Ensure selector matches pod labels exactly.

### Mistake 2: targetPort Mismatch

```yaml
spec:
  containers:
  - name: app
    image: myapp:v1
    ports:
    - containerPort: 3000  # App listens on 3000

---
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  ports:
  - port: 80
    targetPort: 8080       # ← Wrong! Should be 3000
```

**Problem**: Service forwards traffic to wrong port; connection refused.

**Solution**: Match targetPort to containerPort.

### Mistake 3: Hardcoding Service IPs

```yaml
# WRONG
env:
- name: API_URL
  value: "http://10.0.1.5:8080"  # Pod IP - changes after restart!
```

**Problem**: Pod recreates with new IP; env var is stale.

**Solution**: Use Service DNS name:
```yaml
env:
- name: API_URL
  value: "http://api-service:80"
```

### Mistake 4: LoadBalancer Service for Every Service

```yaml
# Expensive - each service gets separate load balancer
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  type: LoadBalancer  # $10-50/month in cloud

---
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  type: LoadBalancer  # Another $10-50/month
```

**Solution**: Use one LoadBalancer + Ingress for routing.

### Mistake 5: Not Using Network Policies

```bash
# Default: Pod A can access everything
# No firewall rules
```

**Issue**: Lateral movement risk. Compromised Pod can access database Pod.

**Solution**: Implement network policies following zero-trust principle.

## Production Patterns

### Multi-region Service Discovery

For applications spread across multiple regions:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: global-api
  annotations:
    external-dns.alpha.kubernetes.io/hostname: api.example.com
spec:
  type: ExternalName
  externalName: my-global-ingress.example.com
```

### Canary Deployments with Services

```bash
# Service initially points to v1 only
kubectl patch service api -p '{"spec":{"selector":{"version":"v1"}}}'

# Deploy v2
kubectl apply -f api-v2-deployment.yaml

# Route 10% traffic to v2
kubectl patch service api -p '{"spec":{"selector":{"version":"v1","v2-canary":"true"}}}'
# Requires dual-label approach or weighted traffic control

# Monitor v2
# Increase traffic gradually
# Full cutover when stable
```

## Key Takeaways

1. **Services provide stable endpoints** (ClusterIP for internal, LoadBalancer/Ingress for external)
2. **Endpoints** automatically track Pod IPs matching service selector
3. **Ingress** provides layer 7 HTTP routing (preferred for web apps)
4. **Network Policies** implement zero-trust networking
5. **DNS** allows Pod-to-Pod communication via service names
6. Use service names, never hardcode Pod IPs

---

## Practice Questions

### MCQ Questions

1. Which service type is suitable for internal-only communication?
   A) NodePort  
   B) LoadBalancer  
   C) ClusterIP  
   D) ExternalName  

2. What does a Service selector do?
   A) Selects which nodes to run pods on  
   B) Selects which pods to forward traffic to  
   C) Selects which images to pull  
   D) Selects which storage to use  

3. If a Service has no endpoints, what is the likely cause?
   A) Service port doesn't match pod port  
   B) Service selector doesn't match any pod labels  
   C) Insufficient node capacity  
   D) Service IP is unreachable  

4. What is an Ingress?
   A) A pod that proxies traffic  
   B) A Kubernetes API object for HTTP(S) routing  
   C) A way to expose pods directly to internet  
   D) A load balancer running inside pod  

5. Network Policies are:
   A) Mandatory for all clusters  
   B) Firewall rules at pod level (requires CNI support)  
   C) Applied at node level  
   D) DNS filtering rules  

### Hands-on Cluster Tasks

**Task 1: Create Service and Test Connectivity**

1. Create a Deployment:
   ```bash
   kubectl create deployment web --image=nginx:1.21 --replicas=3
   kubectl expose deployment web --port=80 --target-port=80 --type=ClusterIP
   ```

2. Verify Service and Endpoints:
   ```bash
   kubectl get svc web
   kubectl get endpoints web
   # Should see 3 pod IPs
   ```

3. Test from another Pod:
   ```bash
   kubectl run -it debug --image=busybox -- sh
   # Inside pod:
   wget -O- http://web:80
   # Should get nginx welcome page
   ```

4. Observe load balancing:
   ```bash
   # Make multiple requests
   for i in {1..6}; do wget -O- -q http://web:80; done
   # If nginx is configured differently per pod, see different responses
   ```

5. Cleanup:
   ```bash
   exit  # Exit debug pod
   kubectl delete deployment web
   kubectl delete svc web
   ```

**Task 2: Create and Test Ingress**

Prerequisites: Ingress Controller installed (NGINX)

1. Create two deployments:
   ```bash
   kubectl create deployment api --image=httpbin:latest --replicas=2
   kubectl create deployment web --image=nginx:1.21 --replicas=2
   ```

2. Expose as services:
   ```bash
   kubectl expose deployment api --port=80 --target-port=8080
   kubectl expose deployment web --port=80 --target-port=80
   ```

3. Create Ingress:
   ```bash
   cat > ingress.yaml << 'EOF'
   apiVersion: networking.k8s.io/v1
   kind: Ingress
   metadata:
     name: my-ingress
   spec:
     ingressClassName: nginx
     rules:
     - host: api.local
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: api
               port:
                 number: 80
     - host: web.local
       http:
         paths:
         - path: /
           pathType: Prefix
           backend:
             service:
               name: web
               port:
                 number: 80
   EOF
   
   kubectl apply -f ingress.yaml
   ```

4. Get Ingress IP:
   ```bash
   kubectl get ingress my-ingress
   # May take a minute for IP to be assigned
   ```

5. Test (requires DNS or /etc/hosts):
   ```bash
   curl -H "Host: api.local" http://<ingress-ip>/
   curl -H "Host: web.local" http://<ingress-ip>/
   ```

6. Cleanup:
   ```bash
   kubectl delete ingress my-ingress
   kubectl delete deployment api web
   kubectl delete svc api web
   ```

### Realistic Production Failure Scenario

**Scenario: Service Endpoints Keep Changing, Breaking Client Connections**

Your client-side code connects to `database-service` and expects persistent connection. However, endpoints keep changing, disconnecting the client.

```bash
# Client connects
curl http://database-service:5432

# Meanwhile, Deployment rolls out new Pod
kubectl set image deployment/database db=db:v2

# Rolling update:
# Old Pod dies → endpoint removed
# New Pod created → endpoint added
# Connection drops → client must retry
```

**Problem**:
- Client connection was routed to a Pod that was evicted
- No graceful connection drain
- Client experiences 100ms+ connection drop

**Root cause**:
Pod lifecycle doesn't account for in-flight connections.

**Mitigation**:
1. **Graceful shutdown** in application:
   ```yaml
   lifecycle:
     preStop:
       exec:
         command: ["/bin/sh", "-c", "sleep 15"]  # Drain connections
   ```

2. **Connection pooling** in client:
   - Multiple connections to service
   - If one drops, others still active
   - Automatic reconnect

3. **Pod Disruption Budgets** (PDB):
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: database-pdb
   spec:
     minAvailable: 2  # Always keep 2 pods running
     selector:
       matchLabels:
         app: database
   ```

4. **Rolling update strategy**:
   ```yaml
   strategy:
     rollingUpdate:
       maxUnavailable: 0  # Never disconnect
       maxSurge: 1
   ```

---

## Further Reading

- Services: https://kubernetes.io/docs/concepts/services-networking/service/
- Ingress: https://kubernetes.io/docs/concepts/services-networking/ingress/
- Network Policies: https://kubernetes.io/docs/concepts/services-networking/network-policies/
- DNS: https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
