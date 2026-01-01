# Module 05: Security in CI/CD

## Architecture: The Left Shift

"Security shift left" means catching security issues earlier (in development, not production).

```
Old (Right):
  Code → Deploy → Production → Hacked → Incident Response

Modern (Left):
  Code → Scan → Build → Test → Deploy → Production (secure by design)
        └─ Early detection saves cost and time
```

The industry saying: A vulnerability caught in development costs $1 to fix. Same vulnerability in production costs $1,000.

## Security Gates in CI/CD

### Gate 1: Secret Detection

Before code is even compiled, detect hardcoded secrets.

```bash
# Scan code for secrets
git-secrets scan
truffleHog scan /repo

# Find patterns like:
#   AWS_SECRET_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
#   postgres://user:password@host.db
#   private_key = "-----BEGIN RSA PRIVATE KEY-----"
```

**Why it matters:** Secrets in code = security breach.

A single leaked secret can:
- Compromise production database
- Allow attackers to impersonate your service
- Cost company millions in remediation

### Gate 2: Dependency Scanning

Check all dependencies for known vulnerabilities.

```bash
# Python
pip-audit

# JavaScript
npm audit

# Go
nancy sleuth

# Java
mvn dependency-check:check
```

Output example:
```
Vulnerability found!
Package: requests-2.25.0
Issue: URL parsing (CVE-2021-33503)
Severity: HIGH
Fix: Upgrade to requests-2.26.0+
```

**Why it matters:** Dependencies have vulnerabilities. You inherit those vulnerabilities when you use them.

### Gate 3: SAST (Static Application Security Testing)

Analyze your code without running it to find security flaws.

```bash
# Semgrep (general purpose)
semgrep --config=p/owasp-top-ten src/

# Bandit (Python specific)
bandit -r src/

# SonarQube (comprehensive)
sonar-scanner -Dsonar.projectKey=myapp
```

SAST finds:
- SQL injection (unsanitized queries)
- XSS (unescaped output)
- Hardcoded credentials
- Weak cryptography
- Authentication bypasses
- Insecure deserialization

**Example:**
```python
# SAST flags this:
username = request.GET.get('username')
query = f"SELECT * FROM users WHERE username = '{username}'"
# SQL injection: username could be: ' OR '1'='1

# Fixed:
query = "SELECT * FROM users WHERE username = %s"
cursor.execute(query, (username,))
# Parameterized query: safe
```

### Gate 4: Image Scanning

For Docker artifacts, scan images for vulnerabilities.

```bash
# Trivy (scans image for vulnerabilities)
trivy image myapp:v1.2.3

# Grype (another scanner)
grype myapp:v1.2.3

# Output:
# Package: openssl-1.1.1g-1
# Vulnerability: CVE-2021-3711 (buffer overflow)
# Severity: HIGH
# Fix: Upgrade to openssl-1.1.1k+
```

**Why it matters:** Your artifact is a Docker image with OS libraries. Vulnerabilities in those libraries = your service is vulnerable.

## Secrets Management

### The Problem with Hardcoded Secrets

Never put secrets in code:

```python
# WRONG - don't do this
DB_PASSWORD = "super_secret_123"
AWS_SECRET = "AKIAIOSFODNN7EXAMPLE"
API_KEY = "sk_live_abc123def456"
```

Problems:
1. Secret is in Git history forever (cloned to everyone's laptop)
2. Secret shows in logs if code is debugged
3. Secret visible in code review
4. Secret accidentally pushed to public GitHub
5. If engineer's laptop stolen, secret is compromised
6. No way to rotate secret without code change

### How Secrets Should Work

1. Never in code
2. Injected at runtime from secure store
3. Different secret per environment
4. Rotated regularly
5. Audited (know who accessed)

### Secrets in CI/CD

**During CI:**
- CI pipeline needs secrets to run tests
- Example: Database password for integration tests

```yaml
# DON'T do this:
env:
  DB_PASSWORD: "super_secret_123"

# DO this:
env:
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
```

CI platform stores actual secret securely. Pipeline gets secret at runtime only.

**During CD:**
- Deployment needs secrets to run in production
- Example: Database credentials

```yaml
# GitHub Actions
- run: deploy.sh
  env:
    DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}
    AWS_SECRET: ${{ secrets.PROD_AWS_SECRET }}
```

**In Production:**
- Application reads secrets from secure store
- NOT environment variables, those can leak

```python
# WRONG (environment variable):
db_password = os.getenv("DB_PASSWORD")
# Gets logged if someone prints os.environ

# RIGHT (secrets manager):
import boto3
secrets = boto3.client('secretsmanager')
response = secrets.get_secret_value(SecretId='prod/db/password')
db_password = response['SecretString']
# Secret never prints, only used once
```

Secrets managers:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Kubernetes Secrets (for container orchestration)

## SAST vs DAST

### SAST: Static Application Security Testing

Analyzes code WITHOUT running it.

**How it works:**
1. Scanner reads source code
2. Looks for vulnerable patterns
3. Reports issues (often with high false-positive rate)

Pros:
- Fast (runs in seconds)
- Finds issues early (in development)
- No infrastructure needed

Cons:
- Many false positives
- Doesn't catch runtime vulnerabilities
- Can't understand business logic context

**Example SAST tool: Bandit**
```bash
bandit -r src/
# Finds: hardcoded secrets, SQL injection patterns, weak crypto, etc.
```

### DAST: Dynamic Application Security Testing

Analyzes running application by attacking it.

**How it works:**
1. Start the application
2. Send attack payloads (SQL injection, XSS, etc.)
3. See if application breaks

Pros:
- Finds real vulnerabilities (not false positives)
- Finds runtime issues
- Understands actual application behavior

Cons:
- Slow (takes minutes to hours)
- Needs running application
- Can't run against all code paths

**Example DAST tool: OWASP ZAP**
```bash
zap.sh -cmd -quickurl http://localhost:8000 -quickout report.html
# Attacks the running app, produces vulnerability report
```

### SAST + DAST Together

SAST finds code issues early. DAST validates actual app behavior.

```
Development:
  SAST (fast, catch obvious issues)
      ↓
Staging:
  DAST (slow, validate real app)
      ↓
Production:
  Automated monitoring (runtime detection)
```

## Supply Chain Security

"Supply chain attack" = attacker compromises dependencies or build process.

### Risk 1: Compromised Dependencies

You use npm package `lodash`. Attacker hacks lodash, injects malicious code, publishes `lodash-4.17.21-evil`.

Your app installs it → malicious code runs in your service.

**Defense:**
1. Use lock files (package-lock.json, yarn.lock)
   - Lock ensures same versions installed
   - If version is compromised, you don't auto-upgrade

2. Dependency scanning
   - Detect known vulnerable packages

3. Software Bill of Materials (SBOM)
   - List all dependencies
   - Track them over time
   - Detect if new dependency is suspicious

### Risk 2: Compromised Build System

Attacker gains access to your CI system, modifies artifacts.

All subsequent deployments include malicious code.

**Defense:**
1. Access control
   - Only authorized users can trigger builds
   - Only CI system can push artifacts

2. Artifact signing
   - Sign artifacts after building
   - Verify signature before deploying
   - Attacker can't modify signed artifact

3. Build reproducibility
   - Same code = same artifact
   - If artifact differs, something is wrong

### Risk 3: Typosquatting

Attacker creates package named `requets` (misspelling of `requests`).

Developer accidentally types `pip install requets` → malicious package installed.

**Defense:**
1. Careful dependency declaration
2. Code review of dependency additions
3. Package repository reputation checks
4. Binary analysis of new packages

## Compliance and Audit

For regulated industries (healthcare, finance), security must be auditable.

### Audit Trail Requirements

1. Who made changes? (Git commit author)
2. What changed? (Git diff)
3. Was it reviewed? (Pull request approval)
4. Did tests pass? (CI pipeline results)
5. Who deployed? (CD pipeline logs)
6. When was it deployed? (CD timestamp)
7. What version is running? (Production artifact version)

Example audit trail:
```
2024-01-15 10:00 - alice commits code (abc123d)
2024-01-15 10:05 - CI runs, tests pass
2024-01-15 10:15 - bob reviews PR, approves
2024-01-15 10:20 - PR merged to main
2024-01-15 10:25 - CD builds artifact myapp:abc123d
2024-01-15 10:30 - carol approves production deployment
2024-01-15 10:35 - myapp:abc123d deployed to production
2024-01-15 10:37 - monitoring confirms healthy
```

For audit, you need:
- Git history (immutable)
- CI/CD logs (immutable)
- Signed commits (verify author)
- Approval records

## Common Mistakes

### Mistake 1: Scanning Too Late

Wrong: Only DAST in production

Problem:
- Vulnerabilities found after users are already at risk
- Late fixes are expensive

Right: SAST in CI, DAST in staging

### Mistake 2: Ignoring Scan Results

Wrong: Security scan finds 47 vulnerabilities, ignore them

Problem:
- Vulnerabilities accumulate
- Production is increasingly insecure
- Incident when attacker finds known vuln

Right: Fail pipeline if vulnerabilities found (or have SLA to fix)

### Mistake 3: Weak Dependency Management

Wrong: No lock file, dependencies auto-upgrade

Problem:
- Malicious package version installed
- New dependency version has breaking changes
- Can't reproduce builds

Right: Lock file, explicit upgrade decisions

### Mistake 4: Storing Secrets in Environment Variables

Wrong: Kubernetes secret → environment variable → application logs secret

Problem:
- Secret appears in logs
- Secret visible in ps output
- Secret survives process death

Right: Inject secret from secure store, use once, don't store

### Mistake 5: No Code Signing

Wrong: Anyone can commit code in your name (or CI system is compromised)

Problem:
- Malicious code attributed to wrong person
- No proof of who authorized it
- Compliance failure

Right: Require signed commits, verify signatures

## Example: Complete Security Pipeline

```yaml
name: Secure Build

on:
  push:
    branches: [main]

jobs:
  security-checks:
    runs-on: ubuntu-latest
    steps:
      # Secret scanning
      - uses: actions/checkout@v3
      - uses: truffleHog@v3
        with:
          path: ./
      
      # Dependency scanning
      - run: pip install pip-audit
      - run: pip-audit --desc
      
      # SAST
      - uses: semgrep/semgrep-action@v1
        with:
          config: >-
            p/owasp-top-ten
            p/security-audit
  
  build:
    runs-on: ubuntu-latest
    needs: security-checks
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm run build
      - run: docker build -t myapp:${{ github.sha }} .
      
      # Image scanning
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
      
      # Sign artifact
      - run: |
          docker login -u ${{ secrets.REGISTRY_USER }} -p ${{ secrets.REGISTRY_PASSWORD }}
          docker push myapp:${{ github.sha }}
          
          # Cosign for image signing (immutable verification)
          cosign sign --key ${{ secrets.COSIGN_KEY }} myapp:${{ github.sha }}
```

## Production Notes

### False Positives vs Security Risk

SAST tools have false positives. Not every finding is a real vulnerability.

Balance:
- Too strict: Developers ignore scan (boy who cried wolf)
- Too lenient: Real vulnerabilities missed

Solution:
1. Tune scanning tool to reduce false positives
2. Have security team review findings
3. Categorize issues (critical, high, medium, low)
4. Only fail pipeline on critical/high
5. Track and plan fixes for medium/low

### Secrets Rotation

Secrets shouldn't live forever. Rotate them regularly.

```
Rotation schedule:
- Database passwords: every 90 days
- API keys: every 30-90 days
- TLS certificates: before expiry
- SSH keys: annually or if compromised
```

Process:
1. Generate new secret
2. Update secret manager (old + new active)
3. Update applications to use new secret
4. Disable old secret after grace period
5. Delete old secret

### Audit Log Retention

Keep audit logs for compliance (usually 7 years for regulated industries).

Policy:
- CI/CD logs: 2 years (for debugging and audit)
- Git history: forever (immutable)
- Production deployment logs: 7 years (compliance)

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. You find an SSH private key in source code (committed to Git). What's the correct action?
   - a) Assume it's not a real key, leave it
   - b) Revoke the key immediately, rotate, audit access
   - c) Delete from Git history
   - d) Both b and c

2. SAST scanning finds 200 potential SQL injection issues. 195 are false positives. What should you do?
   - a) Ignore all results (tool is useless)
   - b) Fix all 200 (better safe than sorry)
   - c) Tune tool to reduce false positives, investigate real issues
   - d) Pay for commercial SAST tool

3. Your Docker image uses base image `ubuntu:latest`. Why is this risky?
   - a) Latest might have new vulnerabilities
   - b) Latest changes (not reproducible)
   - c) Image size might differ
   - d) All of the above

4. When should DAST (Dynamic testing) happen?
   - a) Staging environment (before production)
   - b) Production (real attack validation)
   - c) Development (early detection)
   - d) Only when required by compliance

5. A developer adds `requests-4.3.12` to dependencies (newest version). Why scan this?
   - a) Known vulnerability might have been published
   - b) Package might have been compromised
   - c) Version might not work with your code
   - d) All of the above

### Pipeline Design Tasks

**Task 1: Design Security Pipeline**
You're designing CI security for a financial services backend. Compliance requires:
- No hardcoded secrets
- All dependencies tracked
- Code security scanned
- Artifacts signed

Design the security gates:
1. What scans run in CI?
2. When do scans fail pipeline?
3. What's the SLA for fixing security issues?
4. How do you prove compliance?

**Task 2: Secrets Architecture**
You have a Python backend that needs:
- Database password
- AWS API credentials
- Third-party API key

Design how these are managed:
1. In development (local)
2. In CI (running tests)
3. In staging (test deployment)
4. In production (live)
5. Rotation strategy

### Failure Scenario

**Scenario: The Supply Chain Attack**

Your CI system builds and pushes Docker images to your private registry every 30 minutes.

An attacker gains temporary access to CI system credentials.

For 2 hours (4 deployments), the attacker:
1. Modifies built artifacts
2. Injects malicious code
3. Pushes to registry with legitimate version tags

Meanwhile, developers and automation are continuously deploying. 4 bad versions are deployed to production.

Questions:
1. How would you detect this happened?
2. What's the blast radius (how many users affected)?
3. How do you prevent unsigned artifacts from deploying?
4. What's the recovery procedure?
5. How would artifact signing help?
6. Would dependency scanning catch this? (No - code is yours, not a dependency)

---

Next: [Module 06: Continuous Deployment](06-continuous-deployment.md)
