# Infrastructure Security

## Overview

**Infrastructure Security** focuses on protecting the systems where applications run. This includes network segmentation, access control (RBAC), encryption, and runtime threat detection.

## Mental Model

```
Defense in Depth - Layered Security:

┌──────────────────────────────────────────────────────┐
│  Internet (Attacker)                                 │
└────────────────┬─────────────────────────────────────┘
                 │
        ┌────────▼────────┐
        │  Layer 1: Network Access Control            │
        │  - Firewall blocks suspicious traffic       │
        │  - DDoS protection                          │
        │  - GeoIP filtering                          │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Layer 2: Ingress/API Gateway               │
        │  - Authentication check                    │
        │  - Rate limiting                           │
        │  - Request validation                      │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Layer 3: Network Policies (Kubernetes)   │
        │  - Control which pods can communicate     │
        │  - Prevent lateral movement               │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Layer 4: RBAC (Role-Based Access Control) │
        │  - User can only access resources allowed │
        │  - Least privilege principle               │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Layer 5: Data Encryption                  │
        │  - TLS in transit                         │
        │  - Encryption at rest                     │
        │  - Key management                         │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Layer 6: Runtime Security                 │
        │  - Detect unusual behavior                │
        │  - Kill malicious processes               │
        │  - Log everything                         │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │  Sensitive Data  │
        │  (Databases,     │
        │   User Info)     │
        └──────────────────┘

Attacker must breach multiple layers to succeed
Each layer independently provides security
```

## Key Concepts

### 1. Network Segmentation

Divide network into zones; restrict traffic between zones:

```
┌───────────────────────────────────────────────┐
│  DMZ (Public Zone)                            │
│  - API Gateway                                │
│  - Web servers (load balancer)                │
│  - Can talk to: Internet, App tier           │
│  - Cannot talk to: Databases directly        │
└─────────────────┬─────────────────────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Application Tier          │
    │  - Microservices           │
    │  - Can talk to: App servers,│
    │    Databases               │
    │  - Cannot talk to: Internet│
    └─────────────┬──────────────┘
                  │
    ┌─────────────▼──────────────┐
    │  Data Tier (Private)       │
    │  - Databases               │
    │  - Caches                  │
    │  - Can talk to: Nothing    │
    │    (except app tier)       │
    └────────────────────────────┘
```

### 2. Kubernetes Network Policies

Control traffic between pods:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}  # Applies to all pods
  policyTypes:
  - Ingress
  # No rules = deny all ingress traffic

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-api
spec:
  podSelector:
    matchLabels:
      tier: api  # Apply policy to API pods
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          tier: frontend  # Only allow from frontend
    ports:
    - protocol: TCP
      port: 8080
```

### 3. RBAC (Role-Based Access Control)

Implement least privilege principle:

```yaml
# Define a role with specific permissions
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]  # Can read pods
  # Cannot: create, delete, update

---
# Bind role to a user
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
subjects:
- kind: User
  name: developer@example.com
roleRef:
  kind: Role
  name: pod-reader

---
# Example: Deployment can only read secrets, not create
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]  # Can read, not modify
  resourceNames: ["my-secret"]  # Only specific secret
```

### 4. Encryption

#### TLS/mTLS (In Transit)
```bash
# Self-signed certificate for testing
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -subj "/CN=myapp"

# Enable in Kubernetes
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-certificate>
  tls.key: <base64-encoded-key>
```

#### Encryption at Rest
```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  provider:
    aescbc:
      keys:
      - name: key1
        secret: <base64-32-byte-key>  # Secure random key
```

### 5. Runtime Security with Falco

Detect and respond to suspicious behavior:

```yaml
# Install Falco in Kubernetes
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco --set ebpf.enabled=true

# Custom rule: Alert if suspicious shell access
- rule: Suspicious Shell Access
  desc: Detect shell access from container
  condition: >
    spawned_process and
    container and
    shell_procs and
    not trusted_processes
  output: >
    Suspicious shell spawned
    (user=%user.name command=%proc.cmdline container=%container.name)
  priority: WARNING
  tags: [shell, container, malware]

# When violated:
# Suspicious shell spawned
# (user=root command=/bin/bash container=api-pod)
# [WARNING] 2024-01-06 14:23:45
```

## Hands-On: Secure Kubernetes Cluster

### Step 1: Enable Network Policies

```bash
# Create two namespaces
kubectl create namespace frontend
kubectl create namespace backend

# Deploy frontend and backend
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: frontend
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx
        ports:
        - containerPort: 80

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: backend
spec:
  replicas: 1
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
        image: kennethreitz/httpbin
        ports:
        - containerPort: 80
EOF

# Test: Frontend can reach backend (default allow all)
kubectl exec -it -n frontend $(kubectl get pod -n frontend -l app=web -o name) -- curl http://api.backend

# Now deny all
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: backend
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  # No rules = deny all
EOF

# Test: Frontend cannot reach backend
kubectl exec -it -n frontend $(kubectl get pod -n frontend -l app=web -o name) -- curl http://api.backend
# Connection timeout (blocked)

# Allow only from frontend
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-frontend
  namespace: backend
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: frontend
    ports:
    - protocol: TCP
      port: 80
EOF

# Label frontend namespace
kubectl label namespace frontend name=frontend

# Test: Now works
kubectl exec -it -n frontend $(kubectl get pod -n frontend -l app=web -o name) -- curl http://api.backend
# Success
```

### Step 2: Implement RBAC

```bash
# Create developer role (read-only)
kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: developer-read-only
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list"]
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["logs"]
  verbs: ["get"]
EOF

# Bind to user
kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: developer-binding
subjects:
- kind: User
  name: alice@example.com
roleRef:
  kind: ClusterRole
  name: developer-read-only
EOF

# Verify: User can read pods but not delete
# kubectl --user=alice@example.com get pods  # Works
# kubectl --user=alice@example.com delete pod my-pod  # Forbidden
```

### Step 3: Enable Encryption at Rest

```bash
# Generate encryption key
openssl rand -base64 32
# Output: QhVx/7M9Yq2j8R+cK3FpL9xW4ZvB6TnM=

# Create encryption config
cat > /etc/kubernetes/encryption-config.yaml << 'EOF'
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  provider:
    aescbc:
      keys:
      - name: key1
        secret: QhVx/7M9Yq2j8R+cK3FpL9xW4ZvB6TnM=
EOF

# Update kube-apiserver to use encryption
# (In kubeadm, add flag: --encryption-provider-config=/etc/kubernetes/encryption-config.yaml)
```

## Common Mistakes

**Mistake 1: Network policies without default deny**
```yaml
# ❌ WRONG: Create policies but default allow all
# Attacker can bypass policy with direct connection

# ✅ RIGHT: Start with default deny
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  # No rules = deny all

# Then explicitly allow what's needed
```

**Mistake 2: Overly permissive RBAC**
```yaml
# ❌ WRONG: Admin access to everyone
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: all-admins
subjects:
- kind: Group
  name: developers
roleRef:
  kind: ClusterRole
  name: cluster-admin  # Full access!

# ✅ RIGHT: Least privilege
# Developers can: get/list/watch pods, deployments, logs
# Developers cannot: create, delete, modify, patch
```

**Mistake 3: No encryption for secrets at rest**
```yaml
# ❌ WRONG: Secrets stored unencrypted in etcd
kubectl create secret generic db-password --from-literal=password=secret123
# In etcd: plaintext "secret123"

# ✅ RIGHT: Encrypted secrets
# 1. Enable encryption at rest in kube-apiserver
# 2. Rotate existing secrets to encrypt them
# 3. Use sealed-secrets or external secrets manager
```

**Mistake 4: Network policies without egress rules**
```yaml
# ❌ WRONG: Pod can exfiltrate data to attacker
# Egress not controlled = attacker can steal data
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-ingress-only
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress  # Only controls incoming
  ingress:
  - from: ...
  # Egress NOT controlled = pod can connect anywhere

# ✅ RIGHT: Control both ingress and egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
spec:
  policyTypes:
  - Ingress
  - Egress
  ingress: ...
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
  # Only allow specific outbound connections
```

**Mistake 5: Not monitoring what RBAC allows**
```bash
# ❌ WRONG: Grant permission, never verify if user needs it
# User given admin role in month 1
# User transfers teams in month 3
# Still has admin access in month 6 (orphaned privilege)

# ✅ RIGHT: Regular RBAC audits
kubectl auth can-i list pods --as=alice@example.com  # What can user do?
kubectl get rolebindings -A  # Who has what roles?

# Review quarterly:
# - Did users transfer teams? Revoke old roles.
# - Do users still need their role? Remove if not.
# - New users? Grant minimal role.
```

## Production Incident Scenario

### Scenario: "Attacker gained access to database through lateral movement in Kubernetes cluster"

**Symptoms:**
- Unauthorized database queries from pod IP
- Data exfiltration to external IP
- Database password found in pod environment variable

**Investigation:**

```bash
# 1. Which pod accessed database?
kubectl logs -l app=compromised-app --all-containers=true | grep "database connection"

# 2. How did attacker get in?
# Check pod logs for suspicious commands
kubectl logs <pod-name> | grep -i "curl\|wget\|bash"

# 3. Can pods communicate with database?
kubectl get networkpolicies -A
# Found: No network policy! All pods can reach database

# 4. What roles does pod have?
kubectl describe pod <pod-name>
# serviceAccountName: default
# Default service account has no restrictions
```

**Root Cause:**
- No network policies (pod could talk to database)
- No RBAC for pod (service account unrestricted)
- Database password in plaintext env var
- No egress control (could exfiltrate data)

**Solution:**

```bash
# 1. Immediate: Rotate database credentials
# Delete exposed password secret
kubectl delete secret db-password

# 2. Implement network policies
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress

---
# Allow only necessary connections
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-to-db
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Egress
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
EOF

# 3. Implement RBAC
kubectl apply -f - << 'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-account

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-secrets-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["db-password"]  # Only this secret
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api-read-db-secret
subjects:
- kind: ServiceAccount
  name: api-account
roleRef:
  kind: Role
  name: api-secrets-reader
EOF

# 4. Use sealed-secrets instead of plaintext secrets
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.18.0/controller.yaml

# 5. Enable runtime security monitoring
helm install falco falcosecurity/falco
```

**Prevention:**
- Default deny network policies (whitelist approach)
- Minimal RBAC for service accounts
- Secrets encryption at rest
- Egress controls to prevent data exfiltration
- Runtime threat detection

## Practice Questions

1. **Scenario:** Pod A needs to talk to Pod B. What's the first step?
   - Answer: Implement `default deny-all` network policy. Then create specific allow policy from A to B.

2. **Decision:** Should pods have `cluster-admin` role?
   - Answer: Never. Pods should have minimal required role (usually none or read-only).

3. **Question:** How do you prevent password leaks in environment variables?
   - Answer: Use Kubernetes Secrets. Better: use sealed-secrets or external secret manager to encrypt them.

4. **Comparison:** Network policies vs RBAC?
   - Network policies: Control L4 traffic (which pods can reach which)
   - RBAC: Control L7 access (which users can run which commands)
   Both needed for defense in depth.

## Further Reading

- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Kubernetes RBAC](https://kubernetes.io/docs/reference/access-authn-authz/rbac/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [Falco Documentation](https://falco.org/)
- [Cilium Network Policies](https://docs.cilium.io/en/stable/concepts/overview/)

---

**Next:** Secure the build pipeline and verify artifacts—[Supply Chain Security](03-supply-chain-security.md)
