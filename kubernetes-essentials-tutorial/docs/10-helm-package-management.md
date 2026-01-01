# Module 10: Helm & Package Management

## Overview

Helm is the package manager for Kubernetes, similar to apt/yum for Linux. It enables templating, versioning, and distribution of Kubernetes applications. This module covers Helm concepts, chart creation, and best practices.

## Why Helm?

### Problem: Managing Multiple YAML Files

Without Helm:
```bash
# Deploy application requires:
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
# 5 separate files to manage
```

With Helm:
```bash
helm install my-app ./my-app-chart
# Single command installs everything
```

### Helm Features

1. **Templating**: Parameterize manifests for different environments
2. **Versioning**: Release versions of applications
3. **Rollback**: Easy rollback to previous version
4. **Dependency Management**: Declare application dependencies
5. **Package Distribution**: Share and reuse applications

## Helm Basics

### Installation

```bash
# Linux
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# macOS
brew install helm

# Verify
helm version
```

### Helm Repositories

Helm Charts are stored in repositories (like Docker registries):

```bash
# Add repository
helm repo add stable https://charts.helm.sh/stable
helm repo add bitnami https://charts.bitnami.com/bitnami

# List repositories
helm repo list

# Update to get latest charts
helm repo update

# Search charts
helm search repo nginx
```

### Installing Charts

```bash
# Install chart from repository
helm install my-release stable/nginx-ingress

# Install with custom values
helm install my-release stable/nginx-ingress \
  --set controller.replicas=3 \
  --set controller.service.type=LoadBalancer

# Install with values file
helm install my-release stable/nginx-ingress -f values.yaml

# Install into specific namespace
helm install my-release stable/nginx-ingress -n ingress-nginx --create-namespace
```

### Helm Release Operations

```bash
# List releases
helm list
helm list -n ingress-nginx

# View status
helm status my-release

# View values used
helm get values my-release

# View manifest (generated YAML)
helm get manifest my-release

# Upgrade to new version
helm upgrade my-release stable/nginx-ingress --set controller.replicas=5

# Rollback
helm rollback my-release 1  # Rollback to revision 1

# Uninstall
helm uninstall my-release
```

## Helm Charts: The Application Package

### Chart Structure

```
my-app-chart/
├── Chart.yaml              # Chart metadata
├── values.yaml              # Default configuration
├── templates/              # Kubernetes manifests (with templating)
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   └── _helpers.tpl        # Template helper functions
├── charts/                 # Subchart dependencies
├── README.md
└── .helmignore
```

### Chart.yaml: Metadata

```yaml
apiVersion: v2
name: my-app
description: A Helm chart for my-app application
type: application
version: 1.0.0               # Chart version
appVersion: 1.2.3            # Application version
keywords:
- app
- microservice
maintainers:
- name: John Doe
  email: john@example.com
```

### values.yaml: Default Configuration

```yaml
# Application settings
replicaCount: 3

image:
  repository: myrepo/my-app
  tag: "1.2.3"
  pullPolicy: IfNotPresent

imagePullSecrets: []

service:
  type: ClusterIP
  port: 80
  targetPort: 8080

ingress:
  enabled: true
  className: nginx
  hosts:
  - host: app.example.com
    paths:
    - path: /
      pathType: Prefix

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

config:
  LOG_LEVEL: INFO
  DATABASE_HOST: postgres

environment: production
```

### Templates: Kubernetes Manifests with Variables

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "my-app.selectorLabels" . | nindent 8 }}
    spec:
      containers:
      - name: {{ .Chart.Name }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        ports:
        - containerPort: {{ .Values.service.targetPort }}
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
        env:
        {{- range $key, $value := .Values.config }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
```

### Template Syntax

**Variables**:
```yaml
{{ .Values.replicaCount }}          # Access values.yaml
{{ .Chart.Name }}                   # Chart name
{{ .Release.Name }}                 # Release name
{{ .Namespace }}                    # Namespace
```

**Conditionals**:
```yaml
{{ if .Values.ingress.enabled }}
# Ingress manifest
{{ end }}
```

**Loops**:
```yaml
{{ range .Values.containers }}
- name: {{ .name }}
  image: {{ .image }}
{{ end }}
```

**Pipes & Functions**:
```yaml
{{ .Values.replicaCount | add 1 }}  # Arithmetic
{{ .Values.image.tag | default "latest" }}  # Default value
{{ .Values.config | toYaml }}       # Format as YAML
```

### Helper Templates (_helpers.tpl)

```yaml
{{- define "my-app.labels" -}}
helm.sh/chart: {{ include "my-app.chart" . }}
{{ include "my-app.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}

{{- define "my-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "my-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
```

Use helpers to avoid repeating labels across templates.

## Helm Best Practices

### 1. Use Semantic Versioning

```yaml
version: 1.0.0               # Chart version
appVersion: 1.2.3            # Application version
```

When you change chart (values, templates), increment Chart version. When app updates, update appVersion.

### 2. Provide Sane Defaults

```yaml
# values.yaml should work for most deployments
# Users override only what's different for their environment
```

### 3. Document Your Chart

```yaml
# README.md
# Installation
# helm install my-app ./my-app-chart

# Configuration
# - replicaCount: number of replicas (default: 3)
# - image.tag: application version (default: latest)
```

### 4. Validate Charts

```bash
# Lint chart for errors
helm lint ./my-app-chart

# Dry-run to preview generated manifests
helm install my-app ./my-app-chart --dry-run --debug

# Template locally without cluster
helm template my-app ./my-app-chart
```

### 5. Use Subcharts for Dependencies

```yaml
# Chart.yaml
dependencies:
- name: postgresql
  version: "11.0.0"
  repository: "https://charts.bitnami.com/bitnami"

- name: redis
  version: "17.0.0"
  repository: "https://charts.bitnami.com/bitnami"

# values.yaml
postgresql:
  enabled: true
  auth:
    password: "mypassword"

redis:
  enabled: true
```

```bash
# Download dependencies
helm dependency update ./my-app-chart
```

## Common Mistakes

### Mistake 1: Overly Complex Charts

```yaml
# WRONG: Too many conditionals and complex logic
{{ if or .Values.feature1 .Values.feature2 }}
  {{ if and .Values.ingress.enabled (eq .Values.environment "production") }}
    ...
{{ end }}
```

**Solution**: Keep charts simple; use separate charts for variants.

### Mistake 2: Not Validating Before Installation

```bash
# WRONG: Install without validation
helm install my-app ./my-app-chart
# Template error discovered after deployment
```

**Solution**:
```bash
helm lint ./my-app-chart
helm template my-app ./my-app-chart
helm install ... --dry-run --debug
```

### Mistake 3: Committing Secrets in Chart

```yaml
# WRONG: Secret in values.yaml
config:
  DATABASE_PASSWORD: "mypassword123"
```

**Solution**: Use external secret management or Helm Secrets plugin.

### Mistake 4: Not Updating Dependencies

```bash
# WRONG: Old dependencies with vulnerabilities
helm install my-app ./my-app-chart

# Uses old postgresql version with CVE
```

**Solution**: Regularly update dependencies.

### Mistake 5: No RBAC in Chart

```yaml
# WRONG: Chart doesn't create ServiceAccount and RBAC
spec:
  serviceAccountName: default
```

**Solution**:
```yaml
# templates/serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: {{ include "my-app.serviceAccountName" . }}

# templates/role.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {{ include "my-app.fullname" . }}
rules:
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
```

## Production Patterns

### Multi-environment Deployments

```bash
# Development
helm install my-app ./my-app-chart -n dev \
  -f values-dev.yaml

# Staging
helm install my-app ./my-app-chart -n staging \
  -f values-staging.yaml

# Production
helm install my-app ./my-app-chart -n prod \
  -f values-prod.yaml
```

Where values-prod.yaml overrides defaults:
```yaml
replicaCount: 5
image:
  tag: "1.2.3"
ingress:
  enabled: true
  hosts:
  - host: app.example.com
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 2000m
    memory: 2Gi
autoscaling:
  enabled: true
  minReplicas: 5
  maxReplicas: 20
```

### GitOps with Helm

Store Helm charts in Git; use GitOps operator to deploy:

```bash
# ArgoCD watches Git repo, applies Helm charts
# Any commit automatically deploys
```

### Helm Secrets Management

Using Sealed Secrets or Helm Secrets plugin:

```bash
# Install plugin
helm plugin install https://github.com/jkroepke/helm-secrets

# Create encrypted secret
helm secrets enc secrets.yaml

# Values file references encrypted secret
# During helm install, secret is decrypted and injected
```

## Key Takeaways

1. **Helm** is K8s package manager
2. **Charts** are application packages (templates + values)
3. **Values** provide configuration customization
4. **Templates** use Go templating syntax
5. **Subcharts** manage dependencies
6. **Validation** before installation prevents errors
7. **Helm Secrets** for sensitive data

---

## Practice Questions

### MCQ Questions

1. What is a Helm Chart?
   A) A visualization of cluster resources  
   B) A package containing templated Kubernetes manifests  
   C) A database schema  
   D) A monitoring dashboard  

2. What does helm install do?
   A) Installs Helm on your computer  
   B) Creates a release from a chart  
   C) Uploads chart to repository  
   D) Updates chart version  

3. Where is default configuration stored in a chart?
   A) Chart.yaml  
   B) values.yaml  
   C) templates/  
   D) README.md  

4. How do you override default values during installation?
   A) Edit Chart.yaml  
   B) Edit values.yaml before install  
   C) Use --set or -f values-override.yaml flag  
   D) Modify manifests after installation  

5. What is the purpose of helpers (_helpers.tpl)?
   A) Provide documentation  
   B) Reusable template functions to avoid duplication  
   C) Store secret values  
   D) Manage dependencies  

### Hands-on Cluster Tasks

**Task 1: Install and Manage Chart from Repository**

1. Add Helm repository:
   ```bash
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update
   ```

2. Search chart:
   ```bash
   helm search repo nginx
   ```

3. Inspect chart:
   ```bash
   helm show values bitnami/nginx | head -30
   ```

4. Install with custom values:
   ```bash
   helm install my-nginx bitnami/nginx \
     --set replicas=2 \
     --set service.type=NodePort \
     --namespace default
   ```

5. Verify installation:
   ```bash
   helm list
   helm status my-nginx
   ```

6. Get manifest:
   ```bash
   helm get manifest my-nginx
   ```

7. Upgrade:
   ```bash
   helm upgrade my-nginx bitnami/nginx \
     --set replicas=3
   ```

8. Rollback:
   ```bash
   helm rollback my-nginx 1
   ```

9. Cleanup:
   ```bash
   helm uninstall my-nginx
   ```

**Task 2: Create Your Own Chart**

1. Create chart:
   ```bash
   helm create my-app-chart
   cd my-app-chart
   ```

2. Review structure:
   ```bash
   ls -la
   cat Chart.yaml
   cat values.yaml
   cat templates/deployment.yaml
   ```

3. Modify values.yaml:
   ```bash
   # Edit values.yaml
   # Change image.repository to your image
   # Change replicaCount to 2
   ```

4. Validate:
   ```bash
   helm lint .
   helm template my-app .
   ```

5. Install locally:
   ```bash
   helm install my-app . --dry-run --debug
   helm install my-app .
   ```

6. Verify:
   ```bash
   kubectl get deployment
   kubectl get pods
   ```

7. Cleanup:
   ```bash
   helm uninstall my-app
   ```

### Realistic Production Failure Scenario

**Scenario: Helm Upgrade Breaks Cluster**

You upgrade your application chart to a new version. The new chart version expects different configmap keys. Old Pods still reference old keys → application fails.

```bash
# Old configmap has key: LOG_LEVEL
# New chart expects key: LOG_VERBOSE

# After helm upgrade:
# Old Pods still reference LOG_LEVEL
# New Pods can't find LOG_VERBOSE

# Application: "Missing required environment variable"
# Requests fail with 500 errors
```

**Root cause**: ConfigMap changed, but Pods weren't restarted automatically.

**Solution**:
1. Force pod restart during upgrade:
   ```bash
   helm upgrade my-app ./my-app-chart \
     --force \
     --cleanup-on-fail
   ```

2. Or add checksum annotation to force restart:
   ```yaml
   # templates/deployment.yaml
   spec:
     template:
       metadata:
         annotations:
           config-checksum: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
   ```

**Prevention**:
1. Test chart upgrades in staging first
2. Document breaking changes in Chart release notes
3. Provide migration guide if config changes
4. Use helm test to validate post-upgrade state
5. Keep old and new configurations for transition period

---

## Further Reading

- Helm Documentation: https://helm.sh/docs/
- Chart Best Practices: https://helm.sh/docs/chart_best_practices/
- Helm Hub: https://artifacthub.io/
