# Module 5: ConfigMaps & Secrets

## Overview

ConfigMaps and Secrets decouple configuration from application code. This module covers how to manage configuration, when to use each, security considerations, and production patterns.

## ConfigMaps: Non-Sensitive Configuration

ConfigMaps store application configuration as key-value pairs.

### ConfigMap Creation

**Via YAML**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: default
data:
  LOG_LEVEL: "INFO"
  DATABASE_HOST: "postgres.default.svc.cluster.local"
  DATABASE_PORT: "5432"
  FEATURES_ENABLED: "feature1,feature2"
```

**Via kubectl**:
```bash
# From literals
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=INFO \
  --from-literal=DATABASE_HOST=postgres

# From file
echo "LOG_LEVEL=INFO" > app.env
kubectl create configmap app-config --from-file=app.env

# From directory
kubectl create configmap app-config --from-file=./config/
```

### Mounting ConfigMaps

**As environment variables**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
      - name: app
        image: myapp:v1
        env:
        # Single variable
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: LOG_LEVEL
        # All keys in ConfigMap
        envFrom:
        - configMapRef:
            name: app-config
```

**As volume (file)**:
```yaml
spec:
  containers:
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: config
      mountPath: /etc/config
  volumes:
  - name: config
    configMap:
      name: app-config
      items:
      - key: app.conf
        path: app.conf        # File name in mounted directory
```

### ConfigMap Limits

- Maximum 1MB per ConfigMap
- Data is plain text (not encrypted)
- Changes don't automatically update running Pods

### When ConfigMaps Change

ConfigMap changes don't automatically restart Pods:

```bash
# ConfigMap v1
LOG_LEVEL=INFO

# Pod mounting it picks up config
# Update ConfigMap:
LOG_LEVEL=DEBUG

# Existing Pod still has old config!
```

**Solution 1**: Annotation-based restart
```yaml
spec:
  template:
    metadata:
      annotations:
        config-checksum: "abc123"  # Change this to force pod restart
```

**Solution 2**: Use GitOps tool (ArgoCD, Flux) that detects ConfigMap changes and restarts Pods

**Solution 3**: Restart Pods manually
```bash
kubectl rollout restart deployment/my-app
```

## Secrets: Sensitive Configuration

Secrets store sensitive data (passwords, tokens, keys).

### Secret Types

**Opaque** (default, generic secret):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: dXNlcm5hbWU=          # base64: username
  password: cGFzc3dvcmQxMjM=      # base64: password123
```

**Docker Registry** (authenticate with private image registry):
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: docker-registry-secret
type: kubernetes.io/dockercfg
data:
  .dockercfg: eyJyZWdpc3RyeS5leGFtcGxlLmNvbSI6eyJhdXRoIjoiZEhkNGFXOXhMbVJ2YlElPSJ9fQ==
```

**Service Account Token** (for workload identity):
```yaml
type: kubernetes.io/service-account-token
```

**Basic Auth**:
```yaml
type: kubernetes.io/basic-auth
```

### Secret Creation

**Via YAML**:
```bash
# Create base64 encoded strings
echo -n "mypassword123" | base64
# Output: bXlwYXNzd29yZDEyMw==

cat > secret.yaml << 'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  username: dXNlcm5hbWU=
  password: bXlwYXNzd29yZDEyMw==
EOF

kubectl apply -f secret.yaml
```

**Via kubectl** (automatic base64 encoding):
```bash
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password=mypassword123

# From file
kubectl create secret generic db-credentials \
  --from-file=cert.pem \
  --from-file=key.pem
```

### Mounting Secrets

**As environment variables**:
```yaml
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-credentials
      key: password
```

**As volume**:
```yaml
volumeMounts:
- name: db-creds
  mountPath: /var/db-credentials
  readOnly: true
volumes:
- name: db-creds
  secret:
    secretName: db-credentials
    defaultMode: 0400  # Read-only
```

### Secret Encoding vs Encryption

**Important distinction**:
- Base64 encoding: Obfuscation only, not encryption
- At-rest encryption: Optional (must enable in cluster)

```bash
# Base64 is trivial to decode
echo "bXlwYXNzd29yZDEyMw==" | base64 -d
# Output: mypassword123

# Anyone with kubectl access can read secrets
kubectl get secret db-credentials -o yaml
# data.password visible in base64
```

### Enabling Secret Encryption

Production clusters should encrypt secrets at rest:

```yaml
# In API server encryption configuration (kube-apiserver flag)
--encryption-provider-config=/etc/kubernetes/encryption.yaml
```

```yaml
# encryption.yaml
kind: EncryptionConfiguration
apiVersion: apiserver.config.k8s.io/v1
resources:
- resources:
  - secrets
  providers:
  - aescbc:
      keys:
      - name: key1
        secret: <32-byte base64 encoded key>
  - identity: {}  # Fallback to unencrypted
```

### External Secret Management

For production, use external secret stores instead of Kubernetes Secrets:

**Options**:
- Vault (HashiCorp)
- AWS Secrets Manager
- Google Secret Manager
- Azure Key Vault

**Pattern**: Sync external secrets to Kubernetes Secrets via controller

## ConfigMap vs Secret: Decision Matrix

| Aspect | ConfigMap | Secret |
|--------|-----------|--------|
| Data type | Configuration, non-sensitive | Passwords, tokens, keys |
| Encoding | Plain text | Base64 (or encrypted at-rest) |
| Size limit | 1MB | 1MB |
| Encryption | No | Yes (if enabled) |
| Access control | RBAC | RBAC + encryption |
| Use case | App config, feature flags | DB passwords, API tokens |

## Immutable ConfigMaps & Secrets

Make ConfigMap/Secret immutable to prevent accidental changes:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "INFO"
immutable: true    # Can't update or delete
```

**Benefit**: Prevents accidental misconfiguration that affects production Pods.

## Common Mistakes

### Mistake 1: Storing Secrets in ConfigMaps

```yaml
# WRONG: Secret in ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_PASSWORD: "mypassword123"  # Plaintext!
```

**Problem**: Anyone with kubectl access can read it.

**Solution**: Use Secrets instead.

### Mistake 2: Committing Secrets to Git

```bash
# WRONG: Secrets in repository
$ git add secret.yaml
$ git push

# Secrets now visible in Git history (FOREVER)
```

**Solution**:
1. Use sealed-secrets or encryption tools
2. Store secrets in external manager (Vault)
3. Generate secrets dynamically
4. Add to .gitignore

### Mistake 3: Assuming Base64 is Encrypted

```yaml
data:
  password: bXlwYXNzd29yZDEyMw==  # ENCODED, not encrypted!
```

**Problem**: Anyone can base64 decode this trivially.

**Solution**: Enable at-rest encryption in cluster.

### Mistake 4: Not Setting RBAC for Secrets

```bash
# WRONG: Everyone can read secrets
kubectl get secret db-credentials -o yaml
```

**Solution**: Restrict Secret read access via RBAC:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]
  resourceNames: ["db-credentials"]  # Only specific secret
```

### Mistake 5: Not Rotating Secrets

```yaml
# Old password used for years
password: bXlwYXNzd29yZDEyMw==
```

**Problem**: Compromised password stays active indefinitely.

**Solution**: Implement rotation policy:
1. Generate new secret
2. Update applications to support both old and new
3. Switch to new secret
4. Retire old secret

## Production Patterns

### Feature Flags via ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: feature-flags
data:
  FEATURE_NEW_UI: "true"
  FEATURE_BETA_API: "false"
```

Application reads ConfigMap and enables features dynamically. Change flag without code change.

### Injecting Environment-Specific Configuration

```bash
# Development
kubectl apply -f config-dev.yaml -n dev

# Staging
kubectl apply -f config-staging.yaml -n staging

# Production
kubectl apply -f config-prod.yaml -n prod
```

### Secret Rotation with Zero Downtime

1. Create new secret:
   ```bash
   kubectl create secret generic db-credentials-v2 \
     --from-literal=password=newpassword
   ```

2. Update Deployment to mount both:
   ```yaml
   env:
   - name: DB_PASSWORD_OLD
     valueFrom:
       secretKeyRef:
         name: db-credentials-v1
   - name: DB_PASSWORD_NEW
     valueFrom:
       secretKeyRef:
         name: db-credentials-v2
   ```

3. Application tries new password, falls back to old
4. Rollout restart:
   ```bash
   kubectl rollout restart deployment/app
   ```

5. Delete old secret once fully migrated:
   ```bash
   kubectl delete secret db-credentials-v1
   ```

## Key Takeaways

1. **ConfigMaps**: Non-sensitive configuration, plain text
2. **Secrets**: Sensitive data, base64 encoded, can be encrypted
3. **Mounting**: Environment variables or volume files
4. **Base64 is not encryption**: Use at-rest encryption or external secret manager
5. **Pod doesn't auto-restart** when ConfigMap/Secret changes
6. **External secret managers** recommended for production

---

## Practice Questions

### MCQ Questions

1. What is the maximum size of a ConfigMap?
   A) 256KB  
   B) 512KB  
   C) 1MB  
   D) 10MB  

2. Base64 encoding in Kubernetes Secrets provides:
   A) Encryption (security)  
   B) Obfuscation (not secure)  
   C) Compression  
   D) Validation  

3. If you update a ConfigMap, running Pods:
   A) Automatically reflect the new values  
   B) Need manual restart to pick up changes  
   C) Keep old values until kubelet restart  
   D) Are deleted automatically  

4. Which Secret type is for Docker registry authentication?
   A) Opaque  
   B) kubernetes.io/dockercfg  
   C) kubernetes.io/basic-auth  
   D) kubernetes.io/service-account-token  

5. When should you use Secrets instead of ConfigMaps?
   A) When configuration is large  
   B) When storing sensitive data (passwords, tokens)  
   C) When configuration needs to change frequently  
   D) When configuration is used by multiple apps  

### Hands-on Cluster Tasks

**Task 1: Create and Mount ConfigMap**

1. Create ConfigMap:
   ```bash
   kubectl create configmap app-config \
     --from-literal=LOG_LEVEL=DEBUG \
     --from-literal=DATABASE_HOST=localhost
   ```

2. View ConfigMap:
   ```bash
   kubectl get configmap app-config -o yaml
   ```

3. Create Pod mounting ConfigMap:
   ```bash
   cat > pod.yaml << 'EOF'
   apiVersion: v1
   kind: Pod
   metadata:
     name: config-test
   spec:
     containers:
     - name: app
       image: busybox
       command: ['sh', '-c', 'env | grep -E "^(LOG_LEVEL|DATABASE)" && sleep 3600']
       envFrom:
       - configMapRef:
           name: app-config
   EOF
   
   kubectl apply -f pod.yaml
   ```

4. Verify environment variables:
   ```bash
   kubectl logs config-test
   # Should show LOG_LEVEL=DEBUG and DATABASE_HOST=localhost
   ```

5. Update ConfigMap:
   ```bash
   kubectl patch configmap app-config -p '{"data":{"LOG_LEVEL":"INFO"}}'
   ```

6. Create new Pod (should have new value):
   ```bash
   # Old pod still has old values
   kubectl delete pod config-test
   kubectl apply -f pod.yaml
   kubectl logs config-test
   # Now shows LOG_LEVEL=INFO
   ```

7. Cleanup:
   ```bash
   kubectl delete pod config-test
   kubectl delete configmap app-config
   ```

**Task 2: Create and Use Secret**

1. Create Secret:
   ```bash
   kubectl create secret generic db-credentials \
     --from-literal=username=admin \
     --from-literal=password=secret123
   ```

2. View Secret (notice base64 encoding):
   ```bash
   kubectl get secret db-credentials -o yaml
   # data.password: c2VjcmV0MTIz (base64)
   ```

3. Decode Secret (to show it's not encrypted):
   ```bash
   kubectl get secret db-credentials -o jsonpath='{.data.password}' | base64 -d
   # Output: secret123 (DECODED!)
   ```

4. Create Pod using Secret:
   ```bash
   cat > pod.yaml << 'EOF'
   apiVersion: v1
   kind: Pod
   metadata:
     name: secret-test
   spec:
     containers:
     - name: app
       image: busybox
       command: ['sh', '-c', 'echo "User: $DB_USERNAME"; echo "Pass: $DB_PASSWORD"; sleep 3600']
       env:
       - name: DB_USERNAME
         valueFrom:
           secretKeyRef:
             name: db-credentials
             key: username
       - name: DB_PASSWORD
         valueFrom:
           secretKeyRef:
             name: db-credentials
             key: password
   EOF
   
   kubectl apply -f pod.yaml
   ```

5. Verify Secret in Pod:
   ```bash
   kubectl logs secret-test
   # Shows User: admin and Pass: secret123
   ```

6. Cleanup:
   ```bash
   kubectl delete pod secret-test
   kubectl delete secret db-credentials
   ```

### Realistic Production Failure Scenario

**Scenario: Database Password Rotated, Pods Still Using Old Password**

DBA rotates database password for security. New password is stored in Kubernetes Secret. However, running Pods still use old password (from their environment variables set at Pod creation time).

```bash
# Old password stored in Secret
kubectl get secret db-credentials -o jsonpath='{.data.password}' | base64 -d
# Output: oldpassword123

# Update Secret with new password
kubectl patch secret db-credentials -p '{"data":{"password":"bmV3cGFzc3dvcmQxMjM="}}'

# Existing Pods still have env var with old password!
kubectl logs app-pod
# DB_PASSWORD=oldpassword123

# Application can't connect to database
# Error: "authentication failed"
```

**Root cause**: Environment variables are set at Pod creation time and don't change when Secret is updated.

**Solution**:
1. Restart Pods to pick up new Secret:
   ```bash
   kubectl rollout restart deployment/app
   ```

2. Or mount Secret as volume (automatically updated, but needs application polling):
   ```yaml
   volumeMounts:
   - name: db-creds
     mountPath: /var/db-credentials
     readOnly: true
   volumes:
   - name: db-creds
     secret:
       secretName: db-credentials
   ```
   
   Application reads file periodically instead of env var.

3. Best practice: Use external Secret manager with automatic rotation (Vault, AWS Secrets Manager)

**Prevention**:
- Document that environment variables need Pod restart to update
- Use Secret volumes for dynamically updated values
- Implement secret rotation tooling that automatically restarts Pods
- Test rotation process regularly

---

## Further Reading

- ConfigMaps: https://kubernetes.io/docs/concepts/configuration/configmap/
- Secrets: https://kubernetes.io/docs/concepts/configuration/secret/
- Secret Encryption: https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/
- External Secrets: https://external-secrets.io/
