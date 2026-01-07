# Application Security Fundamentals

## Overview

**Application Security** is about preventing vulnerabilities in code before they reach production. This includes protecting against injection attacks, broken authentication, insecure dependencies, and insecure configurations.

## Mental Model

```
Security Layers in Application Development:

┌─────────────────────────────────────────────────────┐
│  Deployment (Already Breached)                      │
│  ❌ Too Late: Attacker has access to data          │
│  Minutes to contain, hours to assess damage         │
└─────────────────────────────────────────────────────┘
         ↑
┌─────────────────────────────────────────────────────┐
│  Production Runtime (Last Minute)                   │
│  ⚠️ WAF, authentication, rate limiting              │
│  Still possible to be breached                      │
└─────────────────────────────────────────────────────┘
         ↑
┌─────────────────────────────────────────────────────┐
│  Pre-Deployment Scanning (Sweet Spot)               │
│  ✅ SAST: Find code vulnerabilities                │
│  ✅ SCA: Scan dependencies for known CVEs          │
│  ✅ Secrets: Detect hardcoded passwords            │
│  ✅ Fix before production = Zero cost              │
└─────────────────────────────────────────────────────┘
         ↑
┌─────────────────────────────────────────────────────┐
│  Development (Prevention Phase)                     │
│  ✅ Secure coding practices                        │
│  ✅ Code review                                    │
│  ✅ Developer education on OWASP Top 10           │
└─────────────────────────────────────────────────────┘

Best Practice: Shift left (catch issues early)
Cost of fix in development: ~$100
Cost of fix in testing: ~$1,000
Cost of fix in production: ~$100,000+
```

## OWASP Top 10 (2021)

The **Open Web Application Security Project** identifies the 10 most critical security risks:

### 1. Broken Access Control
```python
# ❌ VULNERABLE: No authorization check
@app.route('/admin/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)  # Any authenticated user can delete anyone
    db.session.commit()
    return {"status": "deleted"}

# ✅ SECURE: Verify user has permission
@app.route('/admin/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    if not current_user.is_admin:  # Check permission
        return {"error": "Unauthorized"}, 403
    
    if current_user.id == user_id:  # Can't delete yourself
        return {"error": "Cannot delete self"}, 400
    
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return {"status": "deleted"}
```

### 2. Cryptographic Failures
```python
# ❌ VULNERABLE: Storing plaintext passwords
user.password = request.json['password']  # NEVER do this
db.session.add(user)

# ✅ SECURE: Hash passwords with salt
from werkzeug.security import generate_password_hash
user.password = generate_password_hash(request.json['password'])
db.session.add(user)

# ✅ ALSO SECURE: Use bcrypt
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### 3. Injection (SQL, Command, etc.)
```python
# ❌ VULNERABLE: String concatenation (SQL injection)
query = f"SELECT * FROM users WHERE email = '{email}'"
result = db.execute(query)  # If email = "'; DROP TABLE users; --"
                             # Entire table deleted!

# ✅ SECURE: Use parameterized queries
result = db.execute("SELECT * FROM users WHERE email = ?", (email,))
# Database driver escapes email automatically
```

### 4. Insecure Design
```yaml
# ❌ VULNERABLE: Sending password in email for password reset
Email body:
  "Click here to reset password: reset.com/reset?token=mysecuretoken
   Your new password is: MyPassword123"

# ✅ SECURE: Send temporary reset link, user sets own password
Email body:
  "Click here to reset password: reset.com/reset?token=<random_32_bytes>
  Token expires in 1 hour"
  
User enters new password through HTTPS form
```

### 5. Broken Authentication
```python
# ❌ VULNERABLE: Weak session handling
@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    
    # Session ID = user ID (predictable)
    session['id'] = user.id  # Can guess next user's session
    return {"status": "logged in"}

# ✅ SECURE: Random, long session tokens
import secrets
@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    
    # Session token is cryptographically random
    token = secrets.token_urlsafe(32)  # 256-bit random
    session['token'] = token
    return {"token": token}
```

### 6-10: Other Top Vulnerabilities
- **6. Vulnerable & Outdated Components** - Use outdated libraries with known CVEs
- **7. Authentication & Session Mgmt** - Session fixation, weak password reset
- **8. Software & Data Integrity Failures** - Unsigned updates, untrusted CI/CD
- **9. Logging & Monitoring Failures** - Insufficient logging of security events
- **10. Server-Side Request Forgery (SSRF)** - App fetches attacker-controlled URL

## Dependency Scanning (SCA)

### What is SCA?
**Software Composition Analysis** scans your dependencies for known vulnerabilities.

```bash
# Example: Your app uses lodash 4.15.0
# CVE-2021-23337: Remote code execution in lodash

# Tools find this automatically:
npm audit
pip install pip-audit && pip-audit
cargo audit
```

### Snyk: Comprehensive Dependency Scanner

```bash
# Install Snyk
npm install -g snyk

# Test dependencies for known vulnerabilities
snyk test

# Example output:
# ✗ High severity vulnerability found in lodash
#   Affected versions: < 4.17.21
#   Currently installed: 4.15.0
#   Fix available: 4.17.21
#   Action: npm install lodash@4.17.21

# Fix automatically (where possible)
snyk fix
```

### Trivy: Container Image Scanning

```bash
# Scan Docker image for vulnerabilities
trivy image myapp:1.0

# Output:
# myapp:1.0 (debian 11.1)
# 
# Total: 45 vulnerabilities
# CRITICAL: 5
# HIGH: 12
# MEDIUM: 28
# 
# libc (2.31-13+deb11u1)
# ID             DESCRIPTION          SEVERITY
# CVE-2021-3999  Buffer overflow       CRITICAL
# ...
```

## SAST: Static Application Security Testing

Find vulnerabilities without running code:

```bash
# SonarQube: Scan code for security issues
sonar-scanner \
  -Dsonar.projectKey=myapp \
  -Dsonar.sources=src \
  -Dsonar.host.url=http://sonarqube:9000

# Output categories:
# - Security Hotspots: Code that needs review
# - Vulnerabilities: Known insecure patterns
# - Code Smells: Poor practices (not security)
```

## Secrets Detection

Never commit passwords, API keys, or tokens to Git:

```bash
# TruffleHog: Scan for secrets in repo
pip install truffleHog
truffleHog filesystem . --json

# gitguardian: Pre-commit hook for secrets
pip install detect-secrets
detect-secrets scan

# Found secrets:
# .env:DB_PASSWORD=supersecret123
# config.yaml:aws_access_key_id=AKIA...
```

## Hands-On: Secure Development Pipeline

### Step 1: Setup SAST Scanning

```bash
# Create sample vulnerable app
cat > app.py << 'EOF'
from flask import Flask, request
app = Flask(__name__)

@app.route('/search')
def search():
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{request.args.get('q')}'"
    return query

@app.route('/login', methods=['POST'])
def login():
    # Hardcoded API key
    api_key = "sk-1234567890abcdef"
    # Weak password
    password = request.json['password']
    if len(password) < 4:  # Should be 12+
        return "Password too short"
    return "OK"
EOF

# Scan with Bandit (SAST for Python)
pip install bandit
bandit app.py

# Output:
# B608: hardcoded_sql_string
#   Line 7: Potential SQL injection
#
# B105: hardcoded_password_string
#   Line 11: Hardcoded password API key
```

### Step 2: Dependency Scanning

```bash
# Create requirements with vulnerable library
cat > requirements.txt << 'EOF'
Flask==2.0.0
requests==2.20.0  # CVE-2018-18074
EOF

# Scan dependencies
pip install pip-audit
pip-audit

# Output:
# Found 1 known vulnerability in 1 package:
# requests [2.20.0]
# Vulnerability ID: GHSA-r9hx-8q95-8chw
# Description: Unintended leak of Proxy-Authorization header
```

### Step 3: Container Image Scanning

```bash
# Build vulnerable image
cat > Dockerfile << 'EOF'
FROM ubuntu:18.04
RUN apt-get update && apt-get install -y openssl=1.1.0g-2ubuntu4.1
COPY app.py /app/
CMD ["python", "app.py"]
EOF

docker build -t myapp:1.0 .

# Scan image
trivy image myapp:1.0

# Output shows vulnerable openssl version
```

## Common Mistakes

**Mistake 1: Scanning only in pre-production**
```yaml
# ❌ WRONG: Scan once before deploy
- Deploy to staging
- Run security scan
- If issues found, fix and redeploy (delays release)

# ✅ RIGHT: Scan early and often
- Developer commits code
- CI/CD runs SAST scan (unit test equivalent)
- Auto-scan dependencies in build
- Merge only if scan passes
- Scan production images weekly
```

**Mistake 2: Ignoring low-severity findings**
```
# ❌ WRONG: "It's just low severity, ignore it"
# Low severity vulnerability in dependency
# → Attacker uses it with other low-severity vulns
# → Combined impact becomes critical

# ✅ RIGHT: Fix low-severity issues
# Maintain zero-known-vulnerability posture
# Update dependencies regularly
```

**Mistake 3: Storing secrets in .env files**
```bash
# ❌ WRONG:
cat > .env << 'EOF'
DATABASE_PASSWORD=supersecret123
AWS_ACCESS_KEY=AKIA...
SLACK_WEBHOOK=https://hooks.slack.com/...
EOF

git add .env  # Accidentally committed!
git push      # Secret exposed to all developers

# ✅ RIGHT: Use secrets manager
# .env.example shows structure only
DATABASE_PASSWORD=***CHANGE_ME***

# Actual secrets in:
# - AWS Secrets Manager
# - HashiCorp Vault
# - Kubernetes Secrets
# - GitHub Secrets
```

**Mistake 4: No process for vulnerability remediation**
```
# ❌ WRONG:
# Scan finds CVE
# Alert sent to team
# No clear owner, no timeline, no follow-up
# CVE never fixed

# ✅ RIGHT: Clear process
# SLA for remediation by severity:
# - CRITICAL: 24 hours
# - HIGH: 7 days
# - MEDIUM: 30 days
# - LOW: 90 days
# 
# Tracked in issue tracker
# Escalate if SLA approaching
```

**Mistake 5: Cargo cult scanning (tools without context)**
```
# ❌ WRONG:
# Run 5 different SAST tools
# False positive rate: 80%
# Team ignores all alerts (alert fatigue)
# Real vulnerability missed

# ✅ RIGHT: Curated tool selection
# Choose 1-2 tools per language
# Configure to reduce false positives
# Team reviews alerts actively
# Actually fix issues
```

## Production Incident Scenario

### Scenario: "We deployed code with hardcoded API key; attacker accessed our cloud account"

**Symptoms:**
- Unauthorized API calls from random IPs
- Cloud provider disabled suspicious access key
- Credentials found in public GitHub repo

**Investigation:**

```bash
# 1. Find when secret was committed
git log --all --full-history -- config.py | head -5
# Found commit from 3 weeks ago

# 2. Check all branches
git log --all --oneline | grep -i secret
# 5 commits with "secret" or "credentials" in message

# 3. Check git history for secrets
gitleaks detect --report-path vulns.json
# Found AWS_SECRET_ACCESS_KEY in commit abc123d

# 4. Determine blast radius
# When was secret first exposed?
# Who has access to repo?
# What did attacker do with credentials?
```

**Root Cause:**
- No pre-commit hook to detect secrets
- Code review didn't catch hardcoded key
- No automated secret scanning in CI/CD
- Secret remained in history even after deletion

**Solution:**

```bash
# 1. Rotate the exposed key immediately
aws iam delete-access-key --access-key-id AKIA...

# 2. Install pre-commit secret detection
pip install detect-secrets
detect-secrets install-hook .git/hooks/pre-commit

# 3. Add CI/CD scanning
# In pipeline:
- truffleHog filesystem . --fail  # Fail if secrets found
- bandit -r src/  # Code security scan
- snyk test  # Dependency scanning

# 4. Remove from git history (if not public repo)
# ⚠️ WARNING: This is complex, use carefully
git filter-branch --tree-filter 'rm -f .env' --prune-empty

# 5. Education: Train developers on secret management
```

**Prevention:**
- Pre-commit hooks detect secrets before commit
- CI/CD pipeline scans every merge request
- Automated secret rotation
- Regular audits of repository history

## Practice Questions

1. **Scenario:** Your team uses lodash 4.15.0 with CVE-2021-23337 (RCE). Attacker can execute code. What should you do?
   - Answer: Update lodash immediately (4.17.21+). Run snyk fix. Verify no other vulnerable versions elsewhere.

2. **Question:** Should secrets (passwords, keys) be stored in environment variables?
   - Answer: Better than hardcoded, but best practice is secrets manager (Vault, AWS Secrets, K8s Secrets). Env vars visible in docker history, process listings.

3. **Decision:** Your SAST scanner found 500 security hotspots. What should you do?
   - Answer: Configure tool to reduce false positives. Prioritize HIGH/CRITICAL. Create backlog for MEDIUM/LOW. Don't ignore all alerts (alert fatigue).

4. **Comparison:** SAST vs SCA vs DAST?
   - SAST (Static): Code analysis, finds logical flaws - runs on source code
   - SCA (Software Composition): Dependency scanning - finds known CVEs
   - DAST (Dynamic): Runtime testing, finds auth/injection issues - requires running app

## Further Reading

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Secure Coding Practices](https://cheatsheetseries.owasp.org/)
- [Snyk Documentation](https://docs.snyk.io/)
- [Bandit for Python Security](https://bandit.readthedocs.io/)
- [NIST Secure Software Development Framework](https://csrc.nist.gov/publications/detail/sp/800-218/final)

---

**Next:** Learn to secure the infrastructure where your applications run—[Infrastructure Security](02-infrastructure-security.md)
