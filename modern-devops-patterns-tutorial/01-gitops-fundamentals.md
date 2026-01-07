# GitOps Fundamentals

## Overview

**GitOps** is an operational framework that uses Git as the single source of truth for infrastructure and application deployments. Instead of manually running `kubectl apply` or deployment tools, you commit your desired state to Git, and automated systems converge your actual infrastructure to match.

## Mental Model

```
Traditional Deployment:
Developer writes code
    ↓
Pipeline builds artifacts
    ↓
Admin manually deploys (kubectl apply)
    ↓
Infrastructure updates
    ↓
Problem: Who made the change? What's the current state?

GitOps Deployment:
Developer commits code + config to Git
    ↓
Git becomes source of truth
    ↓
GitOps controller (ArgoCD/Flux) watches Git
    ↓
Controller detects drift from desired state
    ↓
Controller automatically reconciles (deploys)
    ↓
Audit trail: Every change is a Git commit
    ↓
Self-healing: If someone manually changes cluster, controller fixes it

┌─────────────────────┐
│  Git Repository     │
│  (desired state)    │
└────────┬────────────┘
         │
         │ Watch
         ↓
┌─────────────────────┐
│  GitOps Controller  │
│  (ArgoCD/Flux)      │
└────────┬────────────┘
         │
         │ Reconcile
         ↓
┌─────────────────────┐
│  Kubernetes Cluster │
│  (actual state)     │
└─────────────────────┘
```

## Core Principles

### 1. **Declarative**
You declare **what** you want, not **how** to get there.

```yaml
# ✅ RIGHT (Declarative - GitOps)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: app
        image: web-app:v1.5.0

# ❌ WRONG (Imperative - not GitOps)
kubectl set image deployment/web-app app=web-app:v1.5.0 --record
# Only person running this knows what changed
```

### 2. **Git-Based Workflow**
All infrastructure changes go through Git commits, pull requests, and reviews.

```
Feature branch
    ↓
Create PR (review infrastructure change)
    ↓
Approved? Merge to main
    ↓
GitOps controller pulls from Git
    ↓
Automatically deploys
    ↓
Audit trail: Git history shows who changed what when
```

### 3. **Continuous Reconciliation**
The controller constantly compares desired state (Git) vs actual state (cluster) and fixes mismatches.

```
Loop (every 30 seconds):
    1. Read desired state from Git
    2. Check actual cluster state
    3. Are they the same?
       - YES: Do nothing
       - NO: Apply changes to cluster
    4. Repeat
```

## GitOps Architecture

### Components

```
┌──────────────────────────────────────────────────────────┐
│  Source Code Repository (GitHub/GitLab)                 │
│                                                          │
│  app/                                                    │
│    ├─ src/ (application code)                           │
│    ├─ Dockerfile                                        │
│    └─ k8s/ (Kubernetes manifests)                       │
│         ├─ deployment.yaml                              │
│         ├─ service.yaml                                 │
│         └─ ingress.yaml                                 │
│                                                          │
│  infrastructure/                                        │
│    ├─ k8s/ (shared infra)                               │
│    ├─ helm/ (Helm charts)                               │
│    └─ kustomize/ (Kustomize patches)                    │
└──────────────────────────────────────────────────────────┘
                        │
                        │ Pull
                        ↓
┌──────────────────────────────────────────────────────────┐
│  GitOps Controller (ArgoCD/Flux)                         │
│                                                          │
│  1. Watch Git repository for changes                    │
│  2. Fetch desired state (manifests)                     │
│  3. Compare with actual cluster state                   │
│  4. Sync (reconcile) if different                       │
│  5. Report health & status                              │
└──────────────────────────────────────────────────────────┘
                        │
                        │ Deploy
                        ↓
┌──────────────────────────────────────────────────────────┐
│  Kubernetes Cluster                                      │
│  (actual running state)                                 │
└──────────────────────────────────────────────────────────┘
```

## GitOps Workflow Example

### Step 1: Push Code & Config Change
```bash
# Developer commits new version
git add app/deployment.yaml
# Change image: web-app:v1.0 → web-app:v1.5

git commit -m "feat: update web-app to v1.5"
git push origin main
```

### Step 2: GitOps Controller Detects Change
```bash
# ArgoCD/Flux polls Git every 30 seconds
# Detects: deployment.yaml changed

# Fetches desired state from Git
# Compares to actual cluster state

# Finds: cluster running v1.0, Git says v1.5
# Actions: kubectl apply new config
```

### Step 3: Automatic Deployment
```bash
# No manual `kubectl apply` needed
# No pipeline approval gates needed
# Controller automatically syncs

# Rolling update starts
# Old pods terminate, new pods start
# Service stays healthy (readiness probes)
```

### Step 4: Audit Trail
```bash
# Git history shows exactly what changed
git log --oneline
# 3f8a2c1 feat: update web-app to v1.5
# 2d4e1b0 fix: increase memory limits
# 1a9c7e3 chore: add monitoring labels

# Every change is traceable to:
# - Who made it (Git author)
# - When (timestamp)
# - Why (commit message)
# - What exactly (diff)
```

## GitOps Tools

### ArgoCD (Most Popular)
```yaml
# ArgoCD Application definition
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: web-app
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/yourorg/apps
    targetRevision: main
    path: k8s/web-app
  
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  
  syncPolicy:
    automated:
      prune: true      # Delete resources not in Git
      selfHeal: true   # Fix drift from actual to desired
    syncOptions:
    - CreateNamespace=true
```

**Install ArgoCD:**
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Visit https://localhost:8080
```

### Flux (Lightweight Alternative)
```yaml
# Flux GitRepository definition
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: GitRepository
metadata:
  name: web-app
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/yourorg/apps
  ref:
    branch: main

---
# Flux Kustomization definition
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: web-app
  namespace: flux-system
spec:
  interval: 10m
  path: ./k8s/web-app
  prune: true
  sourceRef:
    kind: GitRepository
    name: web-app
```

## GitOps vs CI/CD Pipeline

```
Traditional CI/CD Pipeline:
Git commit
    ↓
CI (build, test)
    ↓
Artifact built
    ↓
Manual approval
    ↓
Admin runs deployment
    ↓
Apply to cluster

GitOps:
Git commit (includes deployment config)
    ↓
CI (build, test, update manifests)
    ↓
Push updated manifests to Git
    ↓
GitOps controller watches Git
    ↓
Automatically deploys
    ↓
No manual approval needed
    ↓
Self-healing if drift occurs
```

## Hands-On: Set Up GitOps with ArgoCD

### Prerequisite: Running Kubernetes cluster
```bash
# Check cluster
kubectl cluster-info
```

### Step 1: Install ArgoCD
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods
kubectl wait -n argocd --for=condition=ready pod -l app.kubernetes.io/name=argocd-server --timeout=300s
```

### Step 2: Access ArgoCD UI
```bash
# Port forward
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get initial password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo

# Visit https://localhost:8080
# Login: admin / <password>
```

### Step 3: Create Git Repository
```bash
# Create repo structure
mkdir -p gitops-demo/k8s
cd gitops-demo

cat > k8s/deployment.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: demo-app
  labels:
    app: demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: demo
  template:
    metadata:
      labels:
        app: demo
    spec:
      containers:
      - name: app
        image: nginx:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
EOF

cat > k8s/service.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  name: demo-app
spec:
  selector:
    app: demo
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 80
EOF

# Commit and push
git init
git add .
git commit -m "initial: add demo app manifests"
git remote add origin https://github.com/YOUR_USERNAME/gitops-demo
git push -u origin main
```

### Step 4: Create ArgoCD Application
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: demo-app
  namespace: argocd
spec:
  project: default
  
  source:
    repoURL: https://github.com/YOUR_USERNAME/gitops-demo
    targetRevision: main
    path: k8s
  
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
```

Apply it:
```bash
kubectl apply -f application.yaml

# Watch ArgoCD sync
argocd app watch demo-app

# Or in UI, see status change to "Synced"
```

### Step 5: Test GitOps Self-Healing
```bash
# Change replicas in Git
# Edit k8s/deployment.yaml: replicas: 3 → replicas: 5

git add k8s/deployment.yaml
git commit -m "scale: increase replicas to 5"
git push

# Wait 30 seconds for ArgoCD to detect change
# Watch pods scale up
kubectl get pods -w

# ArgoCD automatically applied the change!
```

## Common Mistakes

**Mistake 1: Storing secrets in Git**
```yaml
# ❌ WRONG
env:
- name: DB_PASSWORD
  value: "super-secret-password"  # Plain text in Git!

# ✅ RIGHT
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-credentials
      key: password

# Secret created separately
kubectl create secret generic db-credentials \
  --from-literal=password=super-secret-password
```

**Mistake 2: Not committing all infrastructure state to Git**
```yaml
# ❌ WRONG: Some configs in Git, some created manually
# Git has: deployment.yaml
# Manual: kubectl create secret, kubectl create configmap

# Result: Git is not source of truth

# ✅ RIGHT: Everything in Git
# Git has:
#   - deployment.yaml
#   - secret.yaml (with sealed/encrypted values)
#   - configmap.yaml
#   - rbac.yaml
#   - networkpolicy.yaml
```

**Mistake 3: GitOps with manual kubectl apply**
```bash
# ❌ WRONG: Using both
git push (GitOps auto-deploys)
kubectl apply -f config.yaml  # Manual override

# Result: Cluster state diverges from Git

# ✅ RIGHT: ONLY use Git
# All changes go through Git commits
# Never run kubectl apply manually
# Enforce via RBAC if needed
```

**Mistake 4: Not using semantic versioning for deployments**
```yaml
# ❌ WRONG
image: web-app:latest

# Problem: "latest" tag changes, hard to know what version runs
# Leads to: "It worked yesterday, what changed?"

# ✅ RIGHT
image: web-app:v1.5.0

# Explicit version in Git
# Easy to revert: git revert, push, auto-deploy
# Easy to know exactly what's running
```

**Mistake 5: GitOps without proper RBAC restrictions**
```yaml
# ❌ WRONG: Anyone can deploy anything
kubectl apply -f config.yaml  # Any developer

# ✅ RIGHT: Only GitOps controller can deploy
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: argocd-deploy
rules:
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]

# Only ArgoCD service account has this role
# Developers make Git commits, ArgoCD handles deployment
```

## Production Incident Scenario

### Scenario: "Deployment rolled back without approval"

**Symptoms:**
- Production app is running v1.5
- Old version (v1.0) suddenly deployed
- No one approved a rollback
- Git history shows commit to v1.0

**Investigation:**

```bash
# 1. Check ArgoCD sync history
argocd app history demo-app
# Sync: commit 3f8a2c1 (v1.5)
# Sync: commit 1a9c7e3 (v1.0) ← Unexpected!

# 2. Check Git history
git log --oneline
# 2d4e1b0 fix: revert to v1.0 (committed 2 hours ago)
# 3f8a2c1 feat: update to v1.5

# 3. Check who made the commit
git log --format="%h %an %ad %s" -1 2d4e1b0
# 2d4e1b0 John Doe 2 hours ago fix: revert to v1.0

# 4. Check if Git branch protection is enabled
# Settings → Branches → Require pull request reviews
# Result: NOT enabled!
```

**Root Cause:** 
- No branch protection on Git
- Developer could force-push to main
- ArgoCD faithfully synced the change (it's doing its job!)

**Solution:**

```bash
# 1. Enable branch protection on GitHub
Settings → Branches → Add rule for main
- Require pull request reviews
- Require approval from code owners
- Dismiss stale pull request approvals

# 2. Revert the bad commit
git revert 2d4e1b0
git push  # ArgoCD will re-deploy v1.5

# 3. Add code owners file
cat > .github/CODEOWNERS <<'EOF'
# Platform team must approve production config changes
k8s/ @platform-team
helm/ @platform-team
EOF

git add .github/CODEOWNERS
git commit -m "chore: require approval for production changes"
git push
```

**Prevention:**
- Enable branch protection rules on main branch
- Require pull request reviews before merge
- Use code owners for critical files
- Monitor ArgoCD sync events for unexpected changes
- Set up alerts on Git commits to production branches

## Practice Questions

1. **Scenario:** Your Git repository has a deployment config. Someone manually runs `kubectl set image deployment/app image=app:v2`. What happens?
   - Answer: ArgoCD detects drift (actual state v2, desired state v1). It automatically reverts to v1. This is self-healing!

2. **Decision:** Should you commit Docker image tags as "latest" in GitOps?
   - Answer: No. Use explicit versions (v1.5.0) so you can track exactly what's running and easily revert.

3. **Comparison:** Git branch strategy for GitOps?
   - Answer: Trunk-based (main branch only) is simplest. Feature branches → PR → approval → merge → auto-deploy. No hotfix branches needed since reverting is easy (git revert + push).

4. **Troubleshooting:** ArgoCD shows "OutOfSync" but Git and cluster look the same. Why?
   - Answer: Possible causes: (1) ArgoCD hasn't synced yet (wait 30s), (2) field owner conflict, (3) server-side defaults applied by K8s

## Further Reading

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Flux Documentation](https://fluxcd.io/)
- [GitOps Best Practices](https://www.weave.works/technologies/gitops/)
- [GitOps with Kustomize](https://kustomize.io/)
- [Sealed Secrets for GitOps](https://github.com/bitnami-labs/sealed-secrets)

---

**Next:** Learn about Service Mesh for advanced traffic management and observability without code changes.
