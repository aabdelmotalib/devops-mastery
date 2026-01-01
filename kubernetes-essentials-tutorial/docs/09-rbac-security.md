# Module 9: RBAC & Security

## Overview

RBAC (Role-Based Access Control) controls who can do what in Kubernetes. This module covers authentication, authorization, service accounts, and Pod security practices.

## Authentication vs Authorization

### Authentication: "Who are you?"

Kubernetes supports multiple authentication methods:

**Client Certificate** (most common for kubectl):
```bash
~/.kube/config contains:
  - client-certificate: /path/to/cert.pem
  - client-key: /path/to/key.pem
```

**Token** (for Pods via Service Account):
```bash
/var/run/secrets/kubernetes.io/serviceaccount/token
```

**OIDC** (external identity provider like Okta, Dex):
```yaml
kube-apiserver:
  - --oidc-issuer-url=https://accounts.google.com
  - --oidc-client-id=...
  - --oidc-username-claim=email
```

**Webhook** (custom authentication):
```yaml
kube-apiserver:
  - --authentication-token-webhook-config-file=/etc/auth/webhook.conf
```

### Authorization: "Can you do that?"

Kubernetes supports multiple authorization methods:

**RBAC** (standard, recommended):
- Roles define permissions
- RoleBindings grant roles to users/groups

**ABAC** (Attribute-Based Access Control):
- More granular but harder to manage

**Webhook**:
- External system makes authorization decisions

**AlwaysAllow / AlwaysDeny**:
- Allow/deny all requests (testing only)

## RBAC Concepts

### Roles: Define Permissions

A Role contains rules (permissions):

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]
- apiGroups: [""]
  resources: ["pods/logs"]
  verbs: ["get"]
```

**API groups**:
- `""` (empty) = core API (Pods, Services, etc.)
- `apps` = Deployments, StatefulSets, DaemonSets
- `batch` = Jobs, CronJobs
- `rbac.authorization.k8s.io` = Roles, RoleBindings
- `networking.k8s.io` = NetworkPolicies
- Full list: `kubectl api-resources`

**Verbs**:
- `get` - Get single resource
- `list` - List resources
- `watch` - Watch for changes
- `create` - Create resource
- `update` - Modify resource
- `patch` - Partial update
- `delete` - Delete resource
- `*` - All verbs

**Resources**:
- `pods`, `services`, `deployments`
- `pods/logs`, `pods/exec` - Subresources
- `*` - All resources

### ClusterRoles: Cluster-wide Permissions

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-admin  # Default cluster-admin role
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
```

ClusterRole is cluster-scoped (not namespace-scoped). Use for:
- Permissions spanning multiple namespaces
- Cluster-level resources (Nodes, PersistentVolumes, ClusterRoles)
- Default cluster roles

### RoleBindings: Grant Roles to Users/Groups

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: default
subjects:
- kind: User
  name: alice@example.com
  apiGroup: rbac.authorization.k8s.io
- kind: Group
  name: developers
  apiGroup: rbac.authorization.k8s.io
- kind: ServiceAccount
  name: app-reader
  namespace: default
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

**Subject kinds**:
- `User` - Individual user
- `Group` - Group of users
- `ServiceAccount` - Pod identity

**Binding types**:
- `RoleBinding` - Namespace-scoped (grants Role to subject in specific namespace)
- `ClusterRoleBinding` - Cluster-wide (grants ClusterRole globally)

### Service Accounts: Pod Identity

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-reader
  namespace: default

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
subjects:
- kind: ServiceAccount
  name: app-reader
roleRef:
  kind: Role
  name: pod-reader
```

Every Pod gets a ServiceAccount:
```bash
# If not specified, uses "default" ServiceAccount
kubectl get pods
# Shows serviceAccountName column
```

Pod can query Kubernetes API using its token:
```bash
# Inside Pod:
TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
NAMESPACE=$(cat /var/run/secrets/kubernetes.io/serviceaccount/namespace)
CA_CERT=/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

curl -H "Authorization: Bearer $TOKEN" \
     --cacert $CA_CERT \
     https://kubernetes.default.svc.cluster.local/api/v1/namespaces/$NAMESPACE/pods
```

## RBAC Best Practices

### Principle of Least Privilege

```yaml
# WRONG: Over-permissive
rules:
- apiGroups: ["*"]
  resources: ["*"]
  verbs: ["*"]
```

**Solution**:
```yaml
# RIGHT: Minimal permissions
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config"]  # Only specific resource
  verbs: ["get"]
```

### Role per Application

```yaml
# app-reader role for app that only reads pods
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]

---
# app-writer role for app that manages its own configmaps
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-config-writer
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config"]
  verbs: ["get", "update", "patch"]
```

### Namespace Isolation via RBAC

```yaml
# team-a can only access team-a namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-a-developer
  namespace: team-a
subjects:
- kind: Group
  name: team-a@company.com
roleRef:
  kind: ClusterRole
  name: developer
```

## Pod Security

### SecurityContext: Container-Level Security

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: security-demo
spec:
  securityContext:
    runAsUser: 1000           # Non-root user
    runAsGroup: 3000
    fsGroup: 2000
  containers:
  - name: app
    image: myapp:v1
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE
      readOnlyRootFilesystem: true
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

**Key fields**:
- `runAsUser` - User ID to run as
- `runAsGroup` - Group ID
- `fsGroup` - Group for volume permissions
- `readOnlyRootFilesystem` - Prevent writes to /
- `allowPrivilegeEscalation` - Prevent gaining more permissions
- `capabilities` - Linux capabilities to add/drop

### PodSecurityPolicy (Deprecated)

Was used to enforce security constraints. **Now use Pod Security Standards** instead.

### Pod Security Standards

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted  # Enforce strict policy
    pod-security.kubernetes.io/audit: restricted    # Log violations
    pod-security.kubernetes.io/warn: restricted     # Warn on violations
```

**Levels**:
- `unrestricted` - No restrictions (dev)
- `baseline` - Prevent known privilege escalation (production minimum)
- `restricted` - Strict security (recommended)

## Network Policies for Security

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
spec:
  podSelector: {}           # Applies to all pods
  policyTypes:
  - Ingress
  - Egress

---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-from-frontend
spec:
  podSelector:
    matchLabels:
      app: api
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - port: 8080
```

Default: Allow all. Add policies to deny unauthorized traffic.

## Secret Management Security

### Encryption at Rest

```yaml
# Enable encryption in API server
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <32-byte base64 key>
  - identity: {}
```

### RBAC for Secrets

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["db-credentials"]  # Only specific secret
```

### External Secret Managers

For production, use external managers instead of K8s Secrets:

- HashiCorp Vault
- AWS Secrets Manager
- Google Secret Manager
- Azure Key Vault

These provide:
- Centralized secret management
- Audit logging
- Automatic rotation
- Better encryption

## Common Mistakes

### Mistake 1: Default ServiceAccount with Full Permissions

```yaml
# WRONG: App uses default ServiceAccount
spec:
  serviceAccountName: default  # Has no special permissions
```

**Problem**: Pod can't do anything useful, but also can't be exploited via RBAC.

But if you granted default extra permissions (not recommended), now all Pods have those permissions.

**Solution**:
```yaml
# Create specific ServiceAccount for app
serviceAccountName: app-reader
```

### Mistake 2: ClusterRoleBinding for Namespace-Scoped Task

```yaml
# WRONG: Cluster-wide admin access
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: app-admin
subjects:
- kind: ServiceAccount
  name: app
  namespace: default
roleRef:
  kind: ClusterRole
  name: cluster-admin
```

**Problem**: App has cluster-admin access; can do anything.

**Solution**:
```yaml
# Use RoleBinding for namespace-specific access
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-reader
  namespace: default
```

### Mistake 3: Running Containers as Root

```yaml
# WRONG: No securityContext
spec:
  containers:
  - name: app
    image: myapp:v1
```

**Problem**: Container runs as root (UID 0); compromise = full system control.

**Solution**:
```yaml
securityContext:
  runAsUser: 1000
  runAsNonRoot: true
```

### Mistake 4: Wide Open SecurityContext

```yaml
# WRONG: Privileged container
securityContext:
  privileged: true
```

**Problem**: Container can access host; escape = host compromise.

**Solution**:
```yaml
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
```

## Production Patterns

### Multi-team Namespace Setup

```bash
# Each team gets namespace with RBAC
kubectl create namespace team-a
kubectl create namespace team-b

# Team A developers
kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: team-a-developers
  namespace: team-a
subjects:
- kind: Group
  name: team-a-developers@company.com
roleRef:
  kind: ClusterRole
  name: developer
EOF

# Team A can't see team-b namespace
# Team A operator can access team-a only
```

### Service Account per Application

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: backend-app
  namespace: production

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: backend-role
  namespace: production
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["app-config"]
  verbs: ["get"]
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["db-credentials"]
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: backend-binding
  namespace: production
subjects:
- kind: ServiceAccount
  name: backend-app
roleRef:
  kind: Role
  name: backend-role
```

Then in Deployment:
```yaml
spec:
  serviceAccountName: backend-app
```

## Key Takeaways

1. **Authentication** identifies who; **Authorization** controls what they can do
2. **Roles** define permissions; **RoleBindings** grant them
3. **ServiceAccounts** provide Pod identity
4. **Least privilege**: Only grant what's needed
5. **SecurityContext** restricts container capabilities
6. **Encryption** and **external secret managers** for sensitive data

---

## Practice Questions

### MCQ Questions

1. What is a ServiceAccount used for?
   A) Storing user credentials  
   B) Providing Pod identity for API access  
   C) Managing cluster access  
   D) Encrypting secrets  

2. What is the difference between Role and ClusterRole?
   A) Role is for users, ClusterRole for Pods  
   B) Role is namespace-scoped, ClusterRole is cluster-wide  
   C) Role is for authentication, ClusterRole for authorization  
   D) Role is deprecated in favor of ClusterRole  

3. Which best practice principle should guide RBAC?
   A) Grant all permissions for convenience  
   B) Use default ServiceAccount for everything  
   C) Least privilege: grant only needed permissions  
   D) Use ClusterRoleBinding for all access  

4. What does runAsUser do?
   A) Specifies which user can access the pod  
   B) Specifies which user ID the container runs as  
   C) Requires user authentication to start pod  
   D) Limits resource usage per user  

5. How can Pods access Kubernetes API securely?
   A) Use hardcoded token in code  
   B) Use ServiceAccount token mounted in pod  
   C) Use same credentials as cluster admin  
   D) Pods can't access API safely  

### Hands-on Cluster Tasks

**Task 1: Create RBAC for Application**

1. Create namespace:
   ```bash
   kubectl create namespace app-ns
   ```

2. Create ServiceAccount:
   ```bash
   kubectl create serviceaccount app-sa -n app-ns
   ```

3. Create Role (read-only pods):
   ```bash
   cat > role.yaml << 'EOF'
   apiVersion: rbac.authorization.k8s.io/v1
   kind: Role
   metadata:
     name: pod-reader
     namespace: app-ns
   rules:
   - apiGroups: [""]
     resources: ["pods"]
     verbs: ["get", "list", "watch"]
   EOF
   
   kubectl apply -f role.yaml
   ```

4. Create RoleBinding:
   ```bash
   cat > rolebinding.yaml << 'EOF'
   apiVersion: rbac.authorization.k8s.io/v1
   kind: RoleBinding
   metadata:
     name: read-pods
     namespace: app-ns
   subjects:
   - kind: ServiceAccount
     name: app-sa
     namespace: app-ns
   roleRef:
     kind: Role
     name: pod-reader
   EOF
   
   kubectl apply -f rolebinding.yaml
   ```

5. Test with Pod:
   ```bash
   kubectl run test-pod --image=curlimages/curl -n app-ns \
     --serviceaccount=app-sa \
     -it --rm -- \
     sh -c 'curl -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
       --cacert /var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
       https://kubernetes.default/api/v1/namespaces/app-ns/pods'
   ```

6. Cleanup:
   ```bash
   kubectl delete namespace app-ns
   ```

**Task 2: SecurityContext**

1. Create secure Pod:
   ```bash
   cat > secure-pod.yaml << 'EOF'
   apiVersion: v1
   kind: Pod
   metadata:
     name: secure-app
   spec:
     securityContext:
       runAsUser: 1000
       runAsNonRoot: true
       fsGroup: 2000
     containers:
     - name: app
       image: busybox
       command: ['sh', '-c', 'id && ls -l /tmp && sleep 3600']
       securityContext:
         allowPrivilegeEscalation: false
         readOnlyRootFilesystem: true
         capabilities:
           drop:
           - ALL
       volumeMounts:
       - name: tmp
         mountPath: /tmp
     volumes:
     - name: tmp
       emptyDir: {}
   EOF
   
   kubectl apply -f secure-pod.yaml
   ```

2. Check running user:
   ```bash
   kubectl logs secure-app
   # uid=1000 (should not be 0/root)
   ```

3. Verify read-only filesystem:
   ```bash
   kubectl exec secure-app -- touch /file.txt
   # Error: read-only file system
   ```

4. Cleanup:
   ```bash
   kubectl delete pod secure-app
   ```

### Realistic Production Failure Scenario

**Scenario: Compromised Pod Escapes to Host**

A Pod's container is compromised via vulnerability. Because it runs as root with privileged access, attacker gains host access.

```bash
# Inside compromised container:
$ id
uid=0(root) gid=0(root)

$ ls /host
# Full access to host filesystem

$ docker ps
# Can access Docker daemon
```

**Root cause**: Running as root, privileged container, excessive capabilities.

**Prevention**:
1. Run as non-root user:
   ```yaml
   securityContext:
     runAsUser: 1000
     runAsNonRoot: true
   ```

2. Remove unnecessary capabilities:
   ```yaml
   securityContext:
     capabilities:
       drop:
       - ALL
   ```

3. Read-only filesystem:
   ```yaml
   securityContext:
     readOnlyRootFilesystem: true
   ```

4. Pod Security Standards:
   ```yaml
   pod-security.kubernetes.io/enforce: restricted
   ```

5. Network Policies to contain breach:
   ```yaml
   # Compromised pod can only reach necessary services
   ```

---

## Further Reading

- RBAC: https://kubernetes.io/docs/reference/access-authn-authz/rbac/
- ServiceAccounts: https://kubernetes.io/docs/concepts/security/service-accounts/
- SecurityContext: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- Pod Security Standards: https://kubernetes.io/docs/concepts/security/pod-security-standards/
- Network Policies: https://kubernetes.io/docs/concepts/services-networking/network-policies/
