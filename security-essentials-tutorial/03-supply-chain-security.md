# Supply Chain Security

## Overview

**Supply Chain Security** protects the software delivery pipeline from code commit to production. It includes container image scanning, artifact signing, provenance tracking, and policy enforcement.

## Mental Model

```
Supply Chain Attack Vectors:

┌─────────────────────────────────────────────────────────┐
│  Attacker's Goal: Inject malicious code into production │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Developer writes code                                  │
│  Attacker Vector: Compromise developer account         │
│  Defense: MFA, SSH keys, code signing                  │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Code pushed to Git                                     │
│  Attacker Vector: Forge commit (if git history exposed)│
│  Defense: Commit signing with GPG                      │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  CI/CD builds container                                 │
│  Attacker Vector: Compromise build system              │
│  Defense: Secure build environment, audit logs         │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Scan image for vulnerabilities                        │
│  Attacker Vector: Skip scanning if tools compromised   │
│  Defense: Policy enforcement (block unsigned images)   │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Sign container image                                   │
│  Attacker Vector: Use unsigned base image              │
│  Defense: Only allow signed images                     │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Push to container registry                            │
│  Attacker Vector: Replace image with malicious version │
│  Defense: Image verification, immutable tags           │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Deploy to Kubernetes                                   │
│  Attacker Vector: Deploy unsigned image if not checked │
│  Defense: Admission controller enforces signatures     │
└─────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────┐
│  Running in Production                                  │
│  Attack already succeeded                              │
└─────────────────────────────────────────────────────────┘

Defense: Secure each step, verify outputs of previous steps
```

## Container Image Scanning

### Vulnerability Scanning with Trivy

```bash
# Scan local image
trivy image myapp:1.0

# Output:
# myapp:1.0 (debian 11.1)
# Total: 23 vulnerabilities
# CRITICAL: 2
# HIGH: 8
# MEDIUM: 13

# Scan with detailed output
trivy image --severity HIGH,CRITICAL myapp:1.0

# Fail build if critical vulnerabilities found
trivy image --severity CRITICAL --exit-code 1 myapp:1.0
# Exit code 1 = scan found critical issues
```

### Scanning in CI/CD Pipeline

```yaml
# GitHub Actions example
name: Build and Scan
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build image
      run: docker build -t myapp:${{ github.sha }} .
    
    - name: Scan with Trivy
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: 'myapp:${{ github.sha }}'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
    
    - name: Fail if critical
      run: |
        CRITICAL=$(trivy image --severity CRITICAL --format json myapp:${{ github.sha }} | jq '.Results | length')
        if [ "$CRITICAL" -gt 0 ]; then
          echo "Critical vulnerabilities found!"
          exit 1
        fi
```

## Image Signing & Verification

### Sigstore Cosign: Sign Container Images

```bash
# Generate signing key
cosign generate-key-pair
# Creates: cosign.key (private), cosign.pub (public)

# Sign image
cosign sign --key cosign.key myregistry/myapp:1.0
# Creates signature and pushes to registry

# Verify signature
cosign verify --key cosign.pub myregistry/myapp:1.0
# Output:
# Verification successful!
# Signature verified with key: cosign.pub

# Attempt to use unsigned image
cosign verify --key cosign.pub myregistry/unsigned-image:1.0
# Error: no signatures found
```

### Image Signing in CI/CD

```yaml
name: Sign and Push
on: [push]
jobs:
  sign:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build and push image
      uses: docker/build-push-action@v2
      with:
        push: true
        tags: myregistry/myapp:${{ github.sha }}
    
    - name: Install Cosign
      uses: sigstore/cosign-installer@v2
    
    - name: Sign image
      env:
        COSIGN_EXPERIMENTAL: 1  # Use OpenID Connect token
      run: |
        cosign sign --key ${{ secrets.COSIGN_KEY }} \
          myregistry/myapp:${{ github.sha }}
    
    - name: Verify signature
      run: |
        cosign verify --key ${{ secrets.COSIGN_PUBLIC_KEY }} \
          myregistry/myapp:${{ github.sha }}
```

## Software Bill of Materials (SBOM)

Generate list of all components in container:

```bash
# Generate SBOM with Syft
syft myapp:1.0 -o spdx-json > sbom.spdx.json

# Output:
# {
#   "spdxVersion": "SPDX-2.2",
#   "creationInfo": {...},
#   "packages": [
#     {
#       "name": "openssl",
#       "version": "1.1.1g",
#       "downloadLocation": "https://www.openssl.org"
#     },
#     {
#       "name": "curl",
#       "version": "7.64.1",
#       "downloadLocation": "https://curl.se"
#     }
#   ]
# }

# Attach SBOM to image as attestation
cosign attach sbom --sbom sbom.spdx.json myregistry/myapp:1.0
```

## Policy Enforcement

### Image Policy with Admission Controllers

Prevent unsigned/vulnerable images from deploying:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: image-signature-check
webhooks:
- name: verify-image-signature.io
  clientConfig:
    service:
      name: webhook-service
      namespace: default
      path: "/verify-signature"
    caBundle: ...
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  # When pod created/updated, webhook intercepts and verifies image signature

---
# Webhook implementation checks:
# 1. Is image signed by trusted key?
# 2. Does image have security scan passing?
# 3. Is image from approved registry?
# If any check fails: REJECT pod creation
```

### Using Kyverno for Policy

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-image-signature
spec:
  validationFailureAction: enforce  # Block if fails
  rules:
  - name: verify-signature
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - imageReferences:
      - "myregistry/*"
      attestors:
      - name: "check-cosign-sig"
        entries:
        - keys:
            publicKeys: |
              -----BEGIN PUBLIC KEY-----
              MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
              -----END PUBLIC KEY-----

---
# Additional policy: Require vulnerability scan pass
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: block-high-severity-vulns
spec:
  validationFailureAction: enforce
  rules:
  - name: check-vulnerabilities
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - imageReferences:
      - "myregistry/*"
        attestations:
        - name: "scan-passed"
          predicateType: "cosign.sigstore.dev/attachment"
```

## Build Artifact Provenance

Track who built what, when, and with what source:

```bash
# GitHub Actions generates provenance automatically
# Provenance format (SLSA - Supply chain Levels for Software Artifacts):
{
  "version": 1,
  "materials": [
    {
      "uri": "git+https://github.com/myorg/myapp@abc123",
      "digest": {
        "sha256": "abc123..."
      }
    }
  ],
  "byproducts": {
    "github-actions-used": [
      "docker/build-push-action@v2",
      "actions/checkout@v2"
    ]
  },
  "invocation": {
    "configSource": "github.com/myorg/myapp/.github/workflows/build.yaml",
    "parameters": {
      "version": "1.0.0",
      "build-date": "2024-01-06T15:00:00Z"
    },
    "environment": {
      "github-actions": true
    }
  },
  "builder": {
    "id": "https://github.com/actions/runner"
  }
}

# Verify provenance
cosign verify-blob --bundle provenance.json \
  --certificate-identity-regexp="myorg/myapp" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"
```

## Hands-On: Secure Container Pipeline

### Step 1: Scan Image in Build

```bash
# Dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3 \
    pip \
    curl
COPY app.py /app/
CMD ["python3", "/app/app.py"]

# Build and scan
docker build -t myapp:1.0 .
trivy image --severity HIGH,CRITICAL myapp:1.0

# If vulnerabilities found:
# 1. Update base image (FROM ubuntu:22.04 → ubuntu:latest)
# 2. Remove unnecessary packages
# 3. Apply security patches
# 4. Rebuild and rescan
```

### Step 2: Sign Image

```bash
# Generate key pair
cosign generate-key-pair

# Sign with private key
cosign sign --key cosign.key myregistry/myapp:1.0

# Verify with public key
cosign verify --key cosign.pub myregistry/myapp:1.0
```

### Step 3: Deploy with Signature Verification

```bash
# Kubernetes deployment that only allows signed images
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 1
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: myapp
        # Must be signed with cosign
        image: myregistry/myapp:1.0
        # Image must have passed scan
        imagePullPolicy: IfNotPresent
```

## Common Mistakes

**Mistake 1: Scanning only at build time**
```yaml
# ❌ WRONG:
# Scan image once during build
# If deployed 6 months later, new vulnerabilities not detected
# - Container image built 6 months ago (0 vulns at time)
# - New CVE published last week affecting base image
# - Old container deployed today with new vulnerability

# ✅ RIGHT: Continuous scanning
# - Scan at build time
# - Scan daily with new CVE data
# - Alert if running image becomes vulnerable
# - Auto-update or remove vulnerable images
```

**Mistake 2: Signing without verification**
```bash
# ❌ WRONG:
# Sign every image but don't enforce verification
# Attacker pushes unsigned malicious image
# No enforcement = malicious image deployed

# ✅ RIGHT: Enforce signature verification
# - Only signed images pass admission controller
# - Unsigned image rejected at deployment
# - Attacker can sign, but wrong key fails verification
```

**Mistake 3: Using wrong image registry**
```dockerfile
# ❌ WRONG:
FROM ubuntu:latest  # Who controls this image?
# Could be attacker's malicious image

# ✅ RIGHT: Use internal registry with scanning
FROM internal-registry.mycompany.com/ubuntu:22.04
# - Image scanned before stored
# - Image signed with our key
# - Only known-good images available
```

**Mistake 4: Not scanning dependencies (transitive vulnerabilities)**
```
# ❌ WRONG: Only scan direct dependencies
# App depends on: lodash 4.17.0 (no vulns)
# But lodash depends on: internal-lib (HAS RCE vuln)
# Transitive vuln not detected

# ✅ RIGHT: Full dependency tree scanning
# Scan all 1 direct + 50 transitive dependencies
# Tools like Snyk/Trivy do this automatically
```

**Mistake 5: Trusting all registries equally**
```yaml
# ❌ WRONG:
# Allow pulling from Docker Hub
# Allow pulling from internal registry
# No difference in trust level
# Attacker publishes image to Docker Hub, trick deploy

# ✅ RIGHT: Trust hierarchy
# Only internal registry allowed
# Or: Only images signed with our key allowed
# Or: Image must be scanned in our pipeline
```

## Production Incident Scenario

### Scenario: "Malicious image deployed, data exfiltrated"

**Symptoms:**
- Unexpected network connections to external IPs
- Pod consuming high CPU (crypto mining)
- Image version doesn't match what was tagged in CI/CD

**Investigation:**

```bash
# 1. Check image used
kubectl get pod myapp-xxx -o jsonpath='{.spec.containers[0].image}'
# Output: myregistry/myapp:1.0

# 2. Get image hash
kubectl get pod myapp-xxx -o jsonpath='{.spec.containers[0].imageID}'
# Output: docker-pullable://myregistry/myapp@sha256:abc123...

# 3. Check if image was signed
cosign verify --key cosign.pub myregistry/myapp@sha256:abc123...
# Output: no valid signatures found

# 4. Check image scan report
trivy image myregistry/myapp:1.0 --severity CRITICAL
# Output: 15 critical vulnerabilities

# 5. Check audit logs (who deployed this?)
kubectl logs -n kube-system -l component=kube-apiserver | grep "myapp-xxx"
# Found: user=deployment-bot, time=2024-01-06 14:00:00
```

**Root Cause:**
- No image signature enforcement (unsigned malicious image deployed)
- No vulnerability scanning (image not scanned for vulns)
- Scanning skipped in CI/CD (or results ignored)

**Solution:**

```bash
# 1. Immediately remove malicious pod
kubectl delete deployment myapp

# 2. Implement signature verification
helm install cosign-policy-webhook \
  --repo https://sigstore.github.io/cosign-webhook \
  cosign-webhook

# 3. Create policy: Only signed images allowed
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-signed-images
spec:
  validationFailureAction: enforce
  rules:
  - name: verify-signature
    match:
      resources:
        kinds:
        - Pod
    verifyImages:
    - imageReferences:
      - "myregistry/*"
      attestors:
      - name: "check-signature"
        entries:
        - keys:
            publicKeys: |
              -----BEGIN PUBLIC KEY-----
              <our-public-key>
              -----END PUBLIC KEY-----

# 4. Implement scan passing requirement
- name: check-scan
  # Image must have scan attestation
  # showing no high/critical vulnerabilities

# 5. Rotate credentials
# If attacker had registry access, rotate pull secrets

# 6. Audit: Review who deployed this
# Disable deployment-bot account temporarily
# Investigate how account was compromised
```

**Prevention:**
- All images must be signed before deploy
- Admission controller enforces signature verification
- Scans must show no critical/high vulnerabilities
- Provenance tracking shows who built/deployed
- Regular scanning of running images for new CVEs

## Practice Questions

1. **Scenario:** Base image gets critical CVE. What happens to old deployed containers?
   - Answer: Without continuous scanning, they remain vulnerable. Implement daily scanning and auto-updates/removal.

2. **Question:** Should all images be signed with the same key?
   - Answer: No. Use role-based keys (CI/CD signs with one key, developers with another). Review logs to see who signed.

3. **Decision:** Is scanning at build time enough?
   - Answer: No. Scan at build (prevents initial deployment). Also scan daily (detects new CVEs in running containers).

4. **Comparison:** Image signing vs scan passing?
   - Signing: Proves image wasn't modified after creation
   - Scanning: Proves image doesn't have known vulnerabilities
   Both needed for secure supply chain.

## Further Reading

- [Sigstore Project](https://www.sigstore.dev/)
- [SLSA Framework](https://slsa.dev/)
- [NIST Software Supply Chain Security](https://csrc.nist.gov/publications/detail/sp/800-218/final)
- [Kyverno Image Verification](https://kyverno.io/docs/writing-policies/verifyimages/)
- [Cosign Documentation](https://docs.sigstore.dev/cosign/overview/)

---

**Next:** Comply with regulations and audit your security—[Compliance & Audit](04-compliance-audit.md)
