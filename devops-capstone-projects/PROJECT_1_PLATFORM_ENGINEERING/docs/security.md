# Security & Compliance

## Authentication & Authorization

### Multi-Layer Authentication

**Layer 1: Network (Transport Security)**
```
┌─────────────────────────────────────────┐
│ Client connects to API                  │
│                                         │
│ TLS 1.3 encryption (256-bit keys)       │
│ Certificate from AWS ACM                │
│ Cipher suite: ECDHE-RSA-AES256-GCM      │
└─────────────────────────────────────────┘
```

**Layer 2: Application (Token Authentication)**
```python
# User login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secret123"
}

# Server response
{
  "access_token": "eyJhbGc...",  # JWT token
  "token_type": "Bearer",
  "expires_in": 86400  # 24 hours
}

# Subsequent requests
Authorization: Bearer eyJhbGc...

# Token validation
1. Verify signature (RS256 using public key)
2. Check expiration (iat + exp)
3. Check revocation (Redis blacklist)
4. Extract claims (user_id, tenant_id, scopes)
```

**Layer 3: Data (Row-Level Security)**
```sql
-- PostgreSQL Row-Level Security
CREATE POLICY user_isolation 
  ON orders 
  FOR SELECT 
  USING (tenant_id = current_user_id);

-- Even if attacker writes raw SQL:
-- SELECT * FROM orders;
-- Result: Only orders where tenant_id = attacker_id

-- This enforces multi-tenancy at database level
```

### Password Security
```python
import bcrypt

# Storage (never store plain password)
password_hash = bcrypt.hashpw(
    b"password123",
    bcrypt.gensalt(rounds=12)  # Intentionally slow
)
# Result: $2b$12$weaker...

# Verification
is_correct = bcrypt.checkpw(
    b"password123",
    stored_hash
)
# Takes 100ms (prevents brute force)
```

### OAuth2 / OIDC Integration (Optional)

```python
# Allow users to sign in via Google / GitHub
from authlib.integrations.flask_client import OAuth

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id='...',
    client_secret='...',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@app.route('/api/auth/google')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/api/auth/google/callback')
def google_callback():
    token = google.authorize_access_token()
    user_info = token['userinfo']
    
    # Find or create user
    user = db.query(User).filter_by(email=user_info['email']).first()
    if not user:
        user = User(email=user_info['email'], name=user_info['name'])
        db.add(user)
        db.commit()
    
    # Generate internal JWT
    jwt_token = create_access_token(user.id)
    return redirect(f"/?token={jwt_token}")
```

### Scopes & Permissions

```python
# Define scopes
SCOPES = {
    'read:orders': 'Can read orders',
    'write:orders': 'Can create/update orders',
    'delete:orders': 'Can delete orders',
    'admin': 'Can access admin APIs',
}

# User role mapping
USER_ROLES = {
    'customer': ['read:orders'],
    'vendor': ['read:orders', 'write:orders'],
    'admin': ['admin'],
}

# JWT claims
{
    'sub': 'user-123',
    'tenant_id': 'tenant-456',
    'roles': ['vendor'],
    'scopes': ['read:orders', 'write:orders'],
    'exp': 1704067200
}

# API endpoint protection
from functools import wraps

def require_scope(scope):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token_data = get_token_from_request()
            if scope not in token_data.get('scopes', []):
                return {'error': 'Insufficient scope'}, 403
            return f(*args, **kwargs)
        return decorated
    return decorator

@app.route('/api/orders/<id>', methods=['DELETE'])
@require_scope('delete:orders')
def delete_order(id):
    # Only reaches here if user has delete:orders scope
    pass
```

---

## API Security

### SQL Injection Prevention
```python
# BAD: Vulnerable to SQL injection
user_id = request.args.get('id')
result = db.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD: Parameterized queries
result = db.execute(
    "SELECT * FROM users WHERE id = ?",
    (user_id,)
)
# SQLAlchemy ORM (even better)
result = db.query(User).filter_by(id=user_id).first()
```

### XSS (Cross-Site Scripting) Prevention
```python
# Response headers prevent attacks
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
    )
    return response

# Input validation
from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    age = fields.Int(validate=validate.Range(min=0, max=150))

# Use schema to validate input
schema = UserSchema()
try:
    data = schema.load(request.json)
    # data is validated and clean
except ValidationError as err:
    return err.messages, 400
```

### CSRF (Cross-Site Request Forgery) Prevention
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

@app.route('/api/orders', methods=['POST'])
@csrf.protect
def create_order():
    # CSRF token validated automatically
    order = Order(**request.json)
    db.add(order)
    db.commit()
    return order.to_dict()

# Client must include CSRF token
POST /api/orders
X-CSRFToken: <token>
{
  "product_id": "123",
  "quantity": 1
}
```

### Rate Limiting

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.remote_addr,
    storage_uri="redis://redis:6379"
)

# Prevent brute force attacks
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 login attempts per minute
def login():
    email = request.json['email']
    password = request.json['password']
    
    user = db.query(User).filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash):
        return {'error': 'Invalid credentials'}, 401
    
    return {'token': create_access_token(user.id)}

# Per-user rate limiting
@app.route('/api/orders', methods=['POST'])
@limiter.limit("10 per hour", key_func=get_user_id)
def create_order():
    # Max 10 orders per hour per user
    pass
```

---

## Data Security

### Encryption at Rest
```
PostgreSQL:
  - Data stored in EBS volume (encrypted)
  - RDS encryption using AWS KMS
  - Master key stored in AWS Key Management Service

Redis:
  - Data stored in memory (encrypted at rest)
  - Persistence files (RDB/AOF) encrypted

S3 (Logs/Backups):
  - Server-side encryption (AWS KMS)
  - All objects encrypted with customer key
```

### Encryption in Transit
```
TLS 1.3 everywhere:
  Client ↔ ALB: TLS 1.3
  ALB ↔ API: TLS 1.3 (internal AWS network)
  API ↔ PostgreSQL: TLS 1.2+ (within VPC, could be unencrypted)
  API ↔ Redis: TLS 1.2+ (within VPC)

Certificate:
  - Issued by AWS ACM
  - Auto-renewal 60 days before expiration
  - RSA-2048 or ECDSA P-256
```

### Data Retention & Purging
```python
# Set retention policies
class Log(Base):
    __tablename__ = 'logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    action = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Delete logs older than 1 year
    @staticmethod
    def cleanup():
        cutoff = datetime.utcnow() - timedelta(days=365)
        db.query(Log).filter(Log.created_at < cutoff).delete()
        db.commit()

# Run nightly
@app.cli.command()
def cleanup_old_logs():
    Log.cleanup()
    print("Cleanup complete")

# Schedule with cron or Kubernetes CronJob
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-logs
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: api
            image: api:latest
            command: ["python", "-c", "from app import app; app.cli.invoke('cleanup_old_logs')"]
```

---

## Compliance & Audit

### Audit Logging

```python
# Log all sensitive operations
def audit_log(user_id, tenant_id, action, resource, changes):
    log = AuditLog(
        timestamp=datetime.utcnow(),
        user_id=user_id,
        tenant_id=tenant_id,
        action=action,  # 'CREATE', 'UPDATE', 'DELETE'
        resource=resource,  # 'order', 'user', 'payment'
        resource_id=resource.id,
        before=resource.to_dict(),  # Snapshot before change
        after=changes,  # Snapshot after change
        ip_address=request.remote_addr,
    )
    db.add(log)
    db.commit()
    
    # Also send to CloudWatch for compliance
    logger.info(f"AUDIT: {action} {resource} by {user_id}")

# Usage
@app.route('/api/orders/<id>', methods=['DELETE'])
def delete_order(id):
    order = db.query(Order).get(id)
    audit_log(
        user_id=current_user.id,
        tenant_id=order.tenant_id,
        action='DELETE',
        resource=order,
        changes={'status': 'deleted'}
    )
    db.delete(order)
    db.commit()
    return {'status': 'deleted'}
```

### GDPR Compliance

```python
# Right to be forgotten: Delete user data
@app.route('/api/users/me', methods=['DELETE'])
@require_authentication
def delete_user_account():
    user_id = current_user.id
    
    # Delete all user data
    db.query(Order).filter_by(user_id=user_id).delete()
    db.query(UserProfile).filter_by(user_id=user_id).delete()
    db.query(User).filter_by(id=user_id).delete()
    
    # Delete from cache
    redis.delete(f"user:{user_id}:*")
    
    # Log deletion for compliance
    audit_log(
        user_id=user_id,
        tenant_id=current_user.tenant_id,
        action='DELETE_ACCOUNT',
        resource=user_id,
        changes={'status': 'deleted_permanently'}
    )
    
    db.commit()
    return {'status': 'account deleted'}, 200

# Data export: Right to access
@app.route('/api/users/me/export', methods=['GET'])
@require_authentication
def export_user_data():
    user_id = current_user.id
    
    # Collect all user data
    user = db.query(User).get(user_id)
    orders = db.query(Order).filter_by(user_id=user_id).all()
    
    data = {
        'user': user.to_dict(),
        'orders': [o.to_dict() for o in orders],
        'exported_at': datetime.utcnow().isoformat(),
    }
    
    # Return as JSON file
    return jsonify(data)
```

---

## Container & Pod Security

### Non-Root User
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy app
COPY . /app
WORKDIR /app

# Change ownership
RUN chown -R appuser:appuser /app

# Switch to non-root
USER appuser

ENTRYPOINT ["python", "app.py"]
```

### Pod Security Policy

```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  
  # Disallow root user
  runAsUser:
    rule: MustRunAsNonRoot
  
  # Restrict volumes
  volumes:
    - configMap
    - emptyDir
    - projected
    - secret
    - downwardAPI
    - persistentVolumeClaim
  
  # Read-only filesystem
  readOnlyRootFilesystem: true
  
  # Capabilities
  requiredDropCapabilities:
    - ALL
  allowedCapabilities: []
  
  # Networking
  hostNetwork: false
  hostIPC: false
  hostPID: false
  
  # SELinux
  seLinux:
    rule: MustRunAs
    seLinuxOptions:
      level: "s0:c123,c456"

# Apply to all pods in namespace
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: restricted-psp
rules:
- apiGroups: ['policy']
  resources: ['podsecuritypolicies']
  verbs: ['use']
  resourceNames:
  - restricted

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: restricted-psp
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: restricted-psp
subjects:
- kind: ServiceAccount
  name: default
  namespace: default
```

### Network Policies (Zero-Trust)

```yaml
# Deny all traffic by default
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress

# Allow ingress only from Ingress controller
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-ingress
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
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 5000

# Allow egress to specific services
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-to-database
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: databases
    ports:
    - protocol: TCP
      port: 5432
```

---

## Dependency & Image Scanning

### Container Image Scanning
```bash
# Scan for vulnerabilities
trivy image 123456789.dkr.ecr.us-east-1.amazonaws.com/api:v1.0

# Output:
# database Pulled from ghsa, osv, nvd
#
# api:v1.0 (python:3.11-slim)
# ===============================================
# Total: 3 (CRITICAL: 0, HIGH: 2, MEDIUM: 1, LOW: 0)
#
# python (python-baseimage) --------
# CVE-2023-40000: High - Remote code execution
# CVE-2023-40001: Medium - Denial of service
#
# flask (pip) --------
# CVE-2023-30000: High - CSRF token bypass
```

### Supply Chain Security

```yaml
# Only allow images from approved registry
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingWebhookConfiguration
metadata:
  name: image-whitelist
webhooks:
- name: image-whitelist.example.com
  rules:
  - operations: ["CREATE", "UPDATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  clientConfig:
    service:
      name: image-whitelist-service
      namespace: default
      path: /validate

# ValidatingAdmissionPolicy ensures:
# 1. All images from trusted registry
# 2. Images are signed (Sigstore)
# 3. No images from untrusted sources
```

---

## Interview Points

**Q: "How do you prevent SQL injection?"**
A: "Use parameterized queries (SQLAlchemy ORM) instead of string formatting. Database enforces row-level security, so even if injection occurs, attacker limited to their tenant's data."

**Q: "How is data encrypted?"**
A: "At rest: RDS encryption (AWS KMS), S3 encryption (customer key). In transit: TLS 1.3 everywhere. Keys managed by AWS KMS, rotated automatically."

**Q: "How do you ensure only users can see their data?"**
A: "Multi-layer approach: JWT validates user identity, row-level security in database enforces tenant_id filter, API endpoint validates tenant_id matches user's tenant."

**Q: "What about compliance (GDPR, HIPAA)?"**
A: "Audit logging on all sensitive operations, data retention policies (delete after 1 year), user data export endpoint, account deletion option. Encrypted backups in S3, compliance monitoring in place."
