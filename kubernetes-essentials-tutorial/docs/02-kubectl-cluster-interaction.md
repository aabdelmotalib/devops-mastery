# Module 2: kubectl & Cluster Interaction

## Overview

kubectl is the primary tool for interacting with Kubernetes clusters. Mastering kubectl is essential for both operational tasks and understanding how Kubernetes works.

This module covers kubectl in depth: configuration, commands, debugging strategies, and anti-patterns.

## Installation and Configuration

### Installation

```bash
# macOS (via Homebrew)
brew install kubectl

# Linux
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Verify installation
kubectl version --client
```

### kubeconfig: The Connection File

kubectl reads `~/.kube/config` (or `$KUBECONFIG`) to determine:
- Which cluster to connect to
- Authentication credentials
- Default namespace

**kubeconfig structure**:
```yaml
apiVersion: v1
kind: Config
clusters:                      # Define cluster endpoints
- name: production-cluster
  cluster:
    server: https://api.prod.example.com:6443
    certificate-authority: /path/to/ca.crt
- name: staging-cluster
  cluster:
    server: https://api.staging.example.com:6443
    certificate-authority-data: LS0tLS1CRUdJTi... (base64)

users:                         # Define authentication credentials
- name: admin-prod
  user:
    client-certificate: /path/to/client.crt
    client-key: /path/to/client.key
- name: service-account-app
  user:
    token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

contexts:                      # Combine cluster + user + namespace
- name: prod
  context:
    cluster: production-cluster
    user: admin-prod
    namespace: default
- name: staging
  context:
    cluster: staging-cluster
    user: admin-prod
    namespace: staging

current-context: prod          # Default context
```

### Context Management

**View current context**:
```bash
kubectl config current-context
# Output: prod
```

**List all contexts**:
```bash
kubectl config get-contexts
# NAME      CLUSTER                AUTHINFO     NAMESPACE
# prod      production-cluster     admin-prod   default
# staging   staging-cluster        admin-prod   staging
# *local    docker-desktop         docker-desktop
```

**Switch context** (critical for avoiding production mistakes):
```bash
kubectl config use-context staging
kubectl config use-context prod
```

**View kubeconfig** (useful for debugging):
```bash
kubectl config view
```

**Merge multiple kubeconfigs** (when working with many clusters):
```bash
export KUBECONFIG=~/.kube/config:~/.kube/production.conf:~/.kube/staging.conf
kubectl config view  # Shows merged config
```

### Authorization: Authentication vs Authorization

**Authentication** (who are you?)
- Client certificate
- Token (ServiceAccount, OIDC, webhook)
- Basic auth (deprecated)

**Authorization** (what can you do?)
- RBAC (Role-Based Access Control)
- ABAC (Attribute-Based Access Control)
- Webhook
- AlwaysDeny / AlwaysAllow

kubectl verifies your identity (authentication) with the cluster, then the cluster checks if you're allowed to perform the action (authorization).

## kubectl Command Patterns

### Imperative vs Declarative Approaches

#### Imperative: Direct Commands (Use for quick experiments, NOT production)

```bash
# Create a deployment
kubectl create deployment my-app --image=nginx:1.21 --replicas=3

# Scale immediately
kubectl scale deployment my-app --replicas=5

# Update image immediately
kubectl set image deployment/my-app nginx=nginx:1.22
```

**Advantages**: Fast, simple, immediate feedback  
**Disadvantages**: Not idempotent, hard to version control, unclear what current state should be

#### Declarative: YAML Manifests (Production standard)

```bash
# Apply manifests (create if doesn't exist, update if exists)
kubectl apply -f deployment.yaml

# Apply all manifests in directory
kubectl apply -f k8s/

# Apply from Git/HTTP
kubectl apply -f https://raw.githubusercontent.com/...
```

YAML manifests are:
- Version controlled
- Idempotent (applying same manifest multiple times = same result)
- Auditable
- Collaborative

**Best practice**: Use declarative approach for everything that goes to production.

### Key kubectl Commands

#### Cluster Information

```bash
# Cluster info
kubectl cluster-info

# API server version
kubectl version

# Cluster configuration
kubectl config view

# Node list
kubectl get nodes
kubectl get nodes -o wide          # Show IP, OS, kernel, etc.
kubectl describe node worker-1     # Detailed node info
```

#### Resource Management

```bash
# List resources
kubectl get pods
kubectl get pods -A                # All namespaces
kubectl get pods -n staging        # Specific namespace
kubectl get pods --all-namespaces
kubectl get pods -o wide           # Additional columns (IP, Node, etc.)
kubectl get pods -o yaml           # Full YAML of resource
kubectl get pods -o json           # JSON format

# Create resources
kubectl create -f manifest.yaml

# Apply (create or update)
kubectl apply -f manifest.yaml
kubectl apply -k ./overlays/prod   # Kustomize

# Update resources
kubectl set image deployment/app app=nginx:1.22
kubectl set env deployment/app KEY=value
kubectl patch deployment/app -p '{"spec":{"replicas":5}}'

# Delete resources
kubectl delete pod my-pod
kubectl delete deployment my-app
kubectl delete -f manifest.yaml

# Edit resource directly
kubectl edit deployment my-app     # Opens in $EDITOR, applies on save
```

#### Debugging and Inspection

```bash
# View resource details
kubectl describe pod my-pod
kubectl describe node worker-1

# Pod logs
kubectl logs my-pod                # Current logs
kubectl logs my-pod --previous     # Logs from crashed container
kubectl logs my-pod -c app         # Specific container (multi-container pod)
kubectl logs my-pod -f             # Stream logs (tail -f)
kubectl logs my-pod --tail=100     # Last 100 lines

# Execute commands in Pod
kubectl exec my-pod -- env         # Run env command
kubectl exec my-pod -- ps aux
kubectl exec -it my-pod -- /bin/sh # Interactive shell

# Get status and events
kubectl get events
kubectl get events -n staging

# Port forwarding (access Pod from local machine)
kubectl port-forward pod/my-pod 8080:8080
# Now: curl localhost:8080 reaches the pod

# Proxy to API server (advanced debugging)
kubectl proxy --port=8001
# Enables direct HTTP access to API at http://localhost:8001

# Copy files (between local and Pod)
kubectl cp pod/my-pod:/app/data.txt ./local-data.txt
kubectl cp ./local-data.txt pod/my-pod:/app/
```

#### Advanced Filtering and Selection

```bash
# Select by label
kubectl get pods -l app=nginx              # label=value
kubectl get pods -l "app in (nginx, api)"
kubectl get pods -l app=nginx,tier=backend

# Select by field
kubectl get pods --field-selector status.phase=Running

# Sort output
kubectl get pods --sort-by=.metadata.creationTimestamp
kubectl get pods --sort-by=.spec.activeDeadlineSeconds

# Limit output
kubectl get pods --limit=5

# Custom columns
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,IP:.status.podIP
```

### Output Formatting

Understanding output formats helps in scripting and debugging:

```bash
# Human-readable (default)
kubectl get pods
# NAME                       READY   STATUS    RESTARTS   AGE
# nginx-deployment-abcd1234   1/1     Running   0          5m

# YAML (full resource definition)
kubectl get pod nginx-deployment-abcd1234 -o yaml
# Returns complete YAML including metadata, status, etc.

# JSON (programmatic access)
kubectl get pods -o json | jq '.items[0].metadata.name'

# Custom columns (specific fields)
kubectl get pods -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image

# Wide (additional columns)
kubectl get pods -o wide
# Shows IP, Node, Restart count, etc.

# JSONPath (extract specific fields)
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
```

## Dry-Run and Apply Strategies

### Dry-Run: Preview Changes Without Applying

**Why use dry-run?**
- Validate YAML syntax
- See what changes will be applied
- Prevent accidental changes
- Test before applying to production

```bash
# Dry-run (shows if deployment would succeed)
kubectl apply -f deployment.yaml --dry-run=client
# Output: deployment.apps/my-app created (dry run)

# Dry-run server-side (validates against current state)
kubectl apply -f deployment.yaml --dry-run=server

# Generate YAML without applying
kubectl apply -f deployment.yaml --dry-run=client -o yaml
```

### Apply Strategies

**Direct apply** (simple, but can conflict):
```bash
kubectl apply -f deployment.yaml
```

**Strategic merge** (default behavior):
- If field exists in new manifest, update it
- If field exists in cluster but not in new manifest, keep it
- If field doesn't exist in cluster, add it

**Replace** (destructive, loses local changes):
```bash
kubectl replace -f deployment.yaml  # Only if object already exists
kubectl replace --force -f deployment.yaml  # Delete and recreate
```

**Merge strategies** (advanced, useful for patches):
```bash
# Three-way merge (compare last-applied, current, new)
kubectl apply -f deployment.yaml
# Kubernetes tracks the last-applied-configuration annotation

# Patch specific fields
kubectl patch deployment/my-app -p '{"spec":{"replicas":5}}'
```

**Best practice for production**:
1. Store manifests in Git
2. Review changes before applying
3. Use `--dry-run=server` to validate
4. Apply with `kubectl apply -f`
5. Track state with Git commits

## Debugging Strategies

### Issue: Pod Not Running

```bash
# 1. Check pod status
kubectl get pod my-pod
# If STATUS is not Running, investigate

# 2. Describe pod (shows events and conditions)
kubectl describe pod my-pod
# Look for "Events:" section at bottom
# Common events: ImagePullBackOff, CrashLoopBackOff, Pending

# 3. Check pod logs
kubectl logs my-pod
# If container crashed, check previous logs:
kubectl logs my-pod --previous

# 4. Check node status
kubectl get nodes
kubectl describe node <node-name>
# Check "Conditions" section

# 5. Check node capacity
kubectl describe node <node-name> | grep -A 5 Allocated
# Verify node has resources for Pod

# 6. Check events cluster-wide
kubectl get events --sort-by='.lastTimestamp'
```

### Issue: ImagePullBackOff

```bash
# Cause: Image not found or credentials wrong

# Verify image path
kubectl describe pod my-pod | grep Image

# Check if image exists in registry
docker pull <image-name>  # Locally try to pull

# For private registries, verify secret exists
kubectl get secrets
# Pod must reference image pull secret in spec.imagePullSecrets

# View the secret
kubectl get secret my-secret -o yaml
```

### Issue: CrashLoopBackOff

```bash
# Container exits immediately (application crash or misconfiguration)

# View previous logs (container has exited)
kubectl logs my-pod --previous

# View container exit code
kubectl describe pod my-pod | grep "Exit Code"

# Common exit codes:
# 0: Clean exit (pod completed)
# 1: Generic error
# 137: Killed (OOMKilled)
# Others: Application-specific
```

### Issue: Pending Pod

```bash
# Pod can't be scheduled (waiting for resources or other issue)

# Check pod condition
kubectl describe pod my-pod | grep -A 5 Conditions

# Check node resources
kubectl top nodes
kubectl describe node <node-name> | grep -A 10 "Allocated"

# Check if there are taints
kubectl describe node <node-name> | grep Taints

# If taint exists, pod needs matching tolerations
# Add toleration to pod spec and reapply
```

### Issue: Service Not Reaching Pod

```bash
# Pod is running but service doesn't forward traffic

# 1. Check service exists and has endpoints
kubectl get svc my-service
kubectl get endpoints my-service
# If endpoints empty, service can't find pods

# 2. Check labels match
kubectl get pods --show-labels
# Service selector must match pod labels exactly

# 3. Test connectivity within cluster
kubectl run debug --image=busybox -it --rm -- sh
# Inside pod:
wget -O- http://my-service:8080
nslookup my-service

# 4. Check service port mapping
kubectl get svc my-service -o yaml | grep -A 5 ports
# Service.port != Pod.containerPort is OK (service port is virtual)
# But targetPort must match containerPort
```

### Issue: Debugging Production without Restarting Pod

```bash
# Don't delete the pod; instead:

# 1. Get pod logs
kubectl logs my-pod

# 2. Execute shell in pod
kubectl exec -it my-pod -- /bin/bash

# 3. Describe detailed state
kubectl describe pod my-pod

# 4. Get resource usage
kubectl top pod my-pod

# 5. Port-forward to local machine
kubectl port-forward pod/my-pod 8080:8080
# Local: curl localhost:8080

# 6. Copy files from pod
kubectl cp my-pod:/var/log/app.log ./local-app.log

# 7. Don't kubectl delete unless absolutely necessary
# Instead, let controller recreate Pod for you
```

## Common kubectl Mistakes and How to Avoid Them

### Mistake 1: Running Against Wrong Context

```bash
# WRONG: Forgot to check context
kubectl delete pod my-pod
# Deletes from production instead of staging!

# RIGHT: Always verify context first
kubectl config current-context
# Verify output
kubectl delete pod my-pod

# BEST: Use context in command
kubectl --context=staging delete pod my-pod
```

### Mistake 2: Using `latest` Image Tag in Production

```yaml
# WRONG: Latest tag changes unpredictably
containers:
- name: app
  image: myrepo/app:latest

# RIGHT: Explicit version tags
containers:
- name: app
  image: myrepo/app:v1.2.3
```

### Mistake 3: No Resource Requests/Limits

```yaml
# WRONG: Unbounded resource usage
containers:
- name: app
  image: myapp:v1

# RIGHT: Explicit resource boundaries
containers:
- name: app
  image: myapp:v1
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 512Mi
```

### Mistake 4: Editing Deployed Resources Directly (kubectl edit)

```bash
# WRONG: Edit live pod (changes lost on restart)
kubectl edit pod my-pod
# Changes are temporary and not in version control

# RIGHT: Edit source YAML and reapply
# 1. Edit deployment.yaml
# 2. kubectl apply -f deployment.yaml
# Changes are versioned and reproducible
```

### Mistake 5: Not Using Namespaces

```bash
# WRONG: Everything in default namespace
kubectl apply -f app.yaml

# RIGHT: Use namespaces for isolation
kubectl apply -f app.yaml -n production
kubectl apply -f app.yaml -n staging

# Or in YAML:
metadata:
  namespace: production
```

### Mistake 6: Assuming Pod IPs are Stable

```bash
# WRONG: Hardcoding pod IP
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: app
    env:
    - name: BACKEND_IP
      value: "10.0.0.1"  # POD IP - CHANGES AFTER RESTART!

# RIGHT: Use service DNS
    env:
    - name: BACKEND_URL
      value: "http://backend-service:8080"  # Stable DNS
```

### Mistake 7: Overlapping Pod Selectors

```yaml
# WRONG: Pod labeled with multiple conflicting selectors
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: nginx       # Service A targets this
    app: apache      # Service B targets this (overwrites)
spec:
  containers:
  - name: app
    image: nginx

# RIGHT: Use distinct label keys
metadata:
  labels:
    app: nginx-service
    environment: production
    team: platform
```

## Advanced kubectl Features

### Kustomize: Overlay-based Configuration

Kustomize manages multiple versions of same app (dev, staging, prod):

```
kustomize/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patch-replicas.yaml
    ├── staging/
    │   └── kustomization.yaml
    └── prod/
        └── kustomization.yaml
```

```bash
# Apply with overlays
kubectl apply -k kustomize/overlays/prod
```

### Plugins and Extensions

```bash
# List installed plugins
kubectl plugin list

# Example: kubectl-tree (show resource hierarchy)
kubectl tree deployment my-app

# Example: kubectl-debug (advanced debugging)
kubectl debug pod/my-pod
```

## Key Takeaways

1. **Context management is critical**: Always verify current context before destructive operations
2. **Dry-run before applying**: Use `--dry-run=client` or `--dry-run=server`
3. **Declarative over imperative**: Use YAML manifests, version control them
4. **Debugging requires methodical approach**: Check pod → describe → logs → events
5. **kubectl is just an HTTP client**: It translates commands to API calls
6. **YAML formatting matters**: Indentation is significant

---

## Practice Questions

### MCQ Questions

1. What file does kubectl use to determine cluster connection?
   A) /etc/kubernetes/kubelet.conf  
   B) ~/.kube/config  
   C) /var/lib/kubelet/config.yaml  
   D) ~/.kubernetes/credentials  

2. What does `kubectl apply --dry-run=client` do?
   A) Validates YAML syntax without connecting to cluster  
   B) Applies changes to cluster but doesn't save them  
   C) Connects to cluster and validates but doesn't apply  
   D) Dry-run mode is not available for apply command  

3. Which command shows detailed troubleshooting information for a Pod?
   A) kubectl get pod my-pod  
   B) kubectl describe pod my-pod  
   C) kubectl logs pod my-pod  
   D) kubectl inspect pod my-pod  

4. A Pod is in "ImagePullBackOff" status. What is the most likely cause?
   A) Container crashed during startup  
   B) Pod can't find the image in the registry  
   C) Node doesn't have enough CPU  
   D) Service selector doesn't match pod labels  

5. To access logs from a crashed container, which flag is needed?
   A) kubectl logs my-pod --all  
   B) kubectl logs my-pod --previous  
   C) kubectl logs my-pod --crashed  
   D) kubectl logs my-pod --history  

### Hands-on Cluster Tasks

**Task 1: Configure and Switch Contexts**

Prerequisites: Access to at least 2 Kubernetes clusters (or kind, minikube)

1. View current kubeconfig:
   ```bash
   kubectl config view
   ```

2. Get current context:
   ```bash
   kubectl config current-context
   ```

3. List all available contexts:
   ```bash
   kubectl config get-contexts
   ```

4. Switch to a different context (if available):
   ```bash
   kubectl config use-context <context-name>
   ```

5. Verify you're in the new context:
   ```bash
   kubectl cluster-info
   kubectl get nodes
   ```

6. Switch back to original context:
   ```bash
   kubectl config use-context <original-context>
   ```

7. Create a new context for practice (optional):
   ```bash
   kubectl config set-context practice --cluster=<cluster> --user=<user> --namespace=default
   kubectl config use-context practice
   ```

**Expected understanding**: You can navigate between clusters safely, verify context before operations.

**Task 2: Debug a Broken Deployment**

1. Create a broken deployment with image that doesn't exist:
   ```bash
   kubectl create deployment broken-app --image=nonexistent:latest
   ```

2. Observe pod status:
   ```bash
   kubectl get pods
   # Status: ImagePullBackOff or ErrImagePull
   ```

3. Debug systematically:
   ```bash
   # Step 1: Pod status
   kubectl get pod <pod-name>
   
   # Step 2: Detailed description
   kubectl describe pod <pod-name>
   # Look at "Events" section
   
   # Step 3: Pod logs (might not exist if image never pulled)
   kubectl logs <pod-name>
   
   # Step 4: Node status
   kubectl get nodes
   kubectl describe node <node-name>
   ```

4. Fix the deployment:
   ```bash
   kubectl set image deployment/broken-app broken-app=nginx:1.21
   ```

5. Verify pod recovered:
   ```bash
   kubectl get pods -l app=broken-app
   # Should show Running status
   ```

6. Check new pod logs:
   ```bash
   kubectl logs -l app=broken-app
   ```

7. Cleanup:
   ```bash
   kubectl delete deployment broken-app
   ```

**Learning outcomes**: 
- Identify root cause of pod failures
- Use describe and logs for debugging
- Fix issues and verify resolution

### Realistic Production Failure Scenario

**Scenario: Configuration Mismatch After Manual Edit**

You have a running application. A team member manually edited the deployment using `kubectl edit` (anti-pattern).

```bash
# Initial state: Deployment with 3 replicas
kubectl get deployment my-api
# my-api   3/3     3            3           5d

# Team member manually scales it
kubectl edit deployment my-api
# Manually changes replicas: 3 → 5
# Saves

# Now deployment shows 5 replicas
kubectl get pods -l app=my-api | wc -l
# 5 pods
```

**The problem**:
1. Source YAML in Git still says 3 replicas
2. Cluster has 5 replicas (diverged from source)
3. Next CI/CD run applies source YAML
4. Suddenly: 5 replicas → 3 replicas (unexpected downscaling!)

**How to detect this**:
```bash
# Check last-applied-configuration annotation
kubectl get deployment my-api -o yaml | grep -A 10 "last-applied-configuration"

# The annotation will differ from current spec

# Compare with dry-run
kubectl apply -f deployment.yaml --dry-run=server
# Shows what would change if applied now
```

**How to fix it**:
```bash
# Option 1: Reapply source YAML (enforces source of truth)
kubectl apply -f deployment.yaml
# This overwrites manual changes

# Option 2: Update source YAML to match actual state
# Edit deployment.yaml: set replicas: 5
# kubectl apply -f deployment.yaml
# Commit to Git

# Option 3: Use GitOps tool (ArgoCD, Flux)
# Automatically syncs cluster to Git source
# Prevents manual drift
```

**Prevention**:
- Never use `kubectl edit` in production
- Always update source YAML and use `kubectl apply`
- Use GitOps tools that enforce Git as source of truth
- Review all kubectl commands in code reviews
- Use RBAC to prevent edit operations for most users

---

## Further Reading

- kubectl Reference: https://kubernetes.io/docs/reference/kubectl/
- kubeconfig Documentation: https://kubernetes.io/docs/concepts/configuration/organize-cluster-access-kubeconfig/
- Kubernetes API Conventions: https://kubernetes.io/docs/concepts/overview/kubernetes-api/
