# Compliance & Audit

## Overview

**Compliance** means meeting regulatory requirements (HIPAA, PCI-DSS, GDPR, SOC2). **Audit** means proving you're compliant through documentation, logs, and evidence.

## Mental Model

```
Compliance Mindset Shift:

❌ OLD (Checkbox Compliance):
   - Implement security
   - Once per year, auditor checks
   - If pass: Compliant! 🎉
   - Problem: Gaps between audits undetected

✅ NEW (Continuous Compliance):
   - Implement security with compliance built-in
   - Automated checks verify compliance continuously
   - Audit logs track all access and changes
   - Evidence collected automatically
   - If problem detected: Fix immediately
   
   Result: Always audit-ready, not scrambling before audit
```

## Common Regulations

### HIPAA (Healthcare)
Protects patient health information (PHI)

```
Requirements:
- Access control: Only authorized personnel see patient data
- Encryption: All data encrypted in transit and at rest
- Audit logs: Track all access to PHI
- Breach notification: Notify within 60 days if data breached
- Business Associates: Vendors handling PHI must be vetted

Example Control:
  Dr. Alice accesses patient record
  → Logged: who, what, when, from where
  → Audit trail shows: Dr. Alice viewed John's MRI
  → Regular review: Ensure accesses are appropriate
```

### PCI-DSS (Payment Card Industry)
Protects credit card data

```
Requirements:
- Network segmentation: Card data isolated from internet
- Strong authentication: MFA for system access
- Encryption: All card data encrypted
- Vulnerability management: Regular scanning/patching
- Access control: Least privilege
- Monitoring: Real-time alerting

Example Control:
  Credit card processing in isolated network
  → No direct internet access
  → All card data encrypted
  → Access requires MFA
  → Monthly scanning for vulnerabilities
  → Quarterly penetration testing
```

### GDPR (Europe)
Protects personal data of EU residents

```
Requirements:
- Consent: User must opt-in for data collection
- Right to deletion: User can delete their data
- Data portability: User can download their data
- Privacy by design: Security built-in from start
- Data Protection Impact Assessment (DPIA)
- Breach notification: Notify within 72 hours
- Data Processing Agreement with vendors

Example Control:
  Collecting user email for marketing
  → Explicit consent checkbox (not pre-checked)
  → User can unsubscribe/delete at any time
  → Personal data deleted after consent withdrawn
  → All vendors must have DPA signed
  → Breach notified within 72 hours
```

### SOC2 (Service Organizations)
General security, availability, processing integrity, confidentiality, privacy

```
Requirements:
- Security controls: Firewalls, access control, encryption
- Change management: Control who can change systems
- Incident response: Process for handling breaches
- Business continuity: Plan for disasters
- Risk assessment: Identify and mitigate risks

SOC2 Type I:
  Point-in-time audit: Are controls designed properly?
  (One audit, snapshot in time)

SOC2 Type II:
  Operational audit: Are controls working over time?
  (12-month observation period)
```

## Audit Logging

Comprehensive logging for compliance evidence:

### Kubernetes Audit Logging

```yaml
# Enable audit logging in kube-apiserver
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
# Log all authenticated requests
- level: RequestResponse
  omitStages:
  - RequestReceived

# Sample output:
# {
#   "kind": "Event",
#   "apiVersion": "audit.k8s.io/v1",
#   "level": "RequestResponse",
#   "timestamp": "2024-01-06T15:30:45.123456Z",
#   "auditID": "abc-123",
#   "stage": "RequestReceived",
#   "requestObject": {
#     "apiVersion": "v1",
#     "kind": "Pod",
#     "metadata": {"name": "myapp", "namespace": "default"}
#   },
#   "user": {
#     "username": "alice@example.com",
#     "groups": ["developers"]
#   },
#   "sourceIPAddress": "192.168.1.100",
#   "userAgent": "kubectl/1.24.0",
#   "verb": "create",
#   "requestURI": "/api/v1/namespaces/default/pods"
# }
```

### Application Audit Logging

```python
import logging
import json
from datetime import datetime

# Configure audit logger
audit_logger = logging.getLogger('audit')
handler = logging.FileHandler('/var/log/app-audit.log')
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
audit_logger.addHandler(handler)

@app.route('/api/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    # Log the action
    audit_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": "user_deleted",
        "actor": current_user.email,
        "resource": f"users/{user_id}",
        "status": "success",
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get('User-Agent')
    }
    audit_logger.info(json.dumps(audit_log))
    
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()
    return {"status": "deleted"}
```

## Data Protection Implementation

### Encryption at Rest

```yaml
# Example: Encrypt database backups
apiVersion: v1
kind: Secret
metadata:
  name: db-backup-key
type: Opaque
data:
  encryption-key: <base64-32-byte-key>

---
# Backup job with encryption
apiVersion: batch/v1
kind: CronJob
metadata:
  name: encrypted-db-backup
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:latest
            env:
            - name: ENCRYPTION_KEY
              valueFrom:
                secretKeyRef:
                  name: db-backup-key
                  key: encryption-key
            command:
            - /bin/sh
            - -c
            - |
              pg_dump $DATABASE_URL | openssl enc -aes-256-cbc \
                -S $ENCRYPTION_KEY -out /backup/db-$(date +%Y%m%d).enc
```

### Data Deletion (Right to be Forgotten)

```python
@app.route('/api/user/<user_id>', methods=['DELETE'])
def delete_user_gdpr(user_id):
    """Delete user data (GDPR right to be forgotten)"""
    
    # Verify user identity
    if current_user.id != user_id and not current_user.is_admin:
        return {"error": "Forbidden"}, 403
    
    # Delete from all systems
    user = User.query.get(user_id)
    
    # Primary database
    db.session.delete(user)
    db.session.commit()
    
    # Cache
    cache.delete(f"user:{user_id}")
    
    # Search index
    search.delete_user(user_id)
    
    # Backups: Mark for deletion (can't instantly delete from backups)
    backup_request = BackupDeletionRequest(
        user_id=user_id,
        requested_at=datetime.utcnow(),
        deletion_deadline=datetime.utcnow() + timedelta(days=90)
    )
    db.session.add(backup_request)
    db.session.commit()
    
    # Audit log
    audit_logger.info(json.dumps({
        "action": "user_deleted_gdpr",
        "user_id": user_id,
        "timestamp": datetime.utcnow().isoformat()
    }))
    
    return {"status": "deletion_requested"}
```

## Access Control for Compliance

### Implement Segregation of Duties

Prevent single person from making critical changes:

```yaml
# Example: Database password change requires 2 approvals

apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-modifier
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["patch"]
  # BUT: Cannot approve own changes
  
---
# Change requires approval
apiVersion: batch/v1
kind: Job
metadata:
  name: change-db-password-approval
spec:
  template:
    spec:
      containers:
      - name: change-password
        image: postgres:latest
        env:
        - name: APPROVAL_COUNT
          value: "2"  # Requires 2 approvals
        command:
        - /bin/sh
        - -c
        - |
          # Wait for 2 approvals from different people
          while [ $(kubectl get approvals | wc -l) -lt 2 ]; do
            sleep 60
          done
          # Now safe to make change
          kubectl patch secret db-password -p '{"data":{"password":"<new-value>"}}'
```

## Hands-On: HIPAA-Compliant System

### Step 1: Enable Audit Logging

```bash
# Create audit policy
kubectl apply -f - << 'EOF'
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
- RequestReceived
rules:
# Log all requests with request/response
- level: RequestResponse
  verbs: ["create", "update", "patch", "delete"]
  resources: ["secrets", "configmaps"]

# Log all pod access to secrets
- level: Metadata
  verbs: ["get", "list", "watch"]
  resources: ["secrets"]

# Log all user actions
- level: RequestResponse
  omitStages:
  - RequestReceived
EOF

# View audit logs
tail -f /var/log/kube-apiserver-audit.log
```

### Step 2: Implement Encryption at Rest

```bash
# Generate encryption key
openssl rand -base64 32
# Output: QhVx/7M9Yq2j8R+cK3FpL9xW4ZvB6TnM=

# Create secret with key
kubectl create secret generic encryption-key \
  --from-literal=key=QhVx/7M9Yq2j8R+cK3FpL9xW4ZvB6TnM=

# Enable encryption in kube-apiserver
# (Add flag: --encryption-provider-config=/etc/kubernetes/encryption-config.yaml)
```

### Step 3: RBAC for Healthcare Data

```bash
# Create HIPAA-specific roles
kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: patient-data-viewer
rules:
# Can only read patient data
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["patient-records"]
  verbs: ["get"]
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["patient-configs"]
  verbs: ["get", "list"]
# Cannot create, delete, modify, patch

---
# Bind to doctors
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: doctors-can-view-patient-data
subjects:
- kind: Group
  name: doctors
roleRef:
  kind: ClusterRole
  name: patient-data-viewer

---
# Bind to nurses (can also edit certain fields)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: patient-data-editor
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["patient-vitals"]  # Only vitals, not full records
  verbs: ["get", "patch"]
- apiGroups: [""]
  resources: ["configmaps"]
  resourceNames: ["patient-configs"]
  verbs: ["get", "list"]
EOF
```

### Step 4: Data Retention Policy

```python
# Automatically delete old patient data
from celery import shared_task
from datetime import datetime, timedelta

@shared_task
def purge_old_records():
    """Delete patient records older than 7 years (HIPAA retention)"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=365*7)
    
    # Find old records
    old_records = PatientRecord.query.filter(
        PatientRecord.created_at < cutoff_date
    ).all()
    
    for record in old_records:
        audit_logger.info(json.dumps({
            "action": "record_purged_retention_policy",
            "patient_id": record.patient_id,
            "record_id": record.id,
            "age_days": (datetime.utcnow() - record.created_at).days,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        db.session.delete(record)
    
    db.session.commit()
    
    return len(old_records)

# Schedule: Run daily at 3 AM
# (In production: Celery Beat)
```

## Common Mistakes

**Mistake 1: Logging sensitive data**
```python
# ❌ WRONG:
audit_logger.info(f"User {username} login with password {password}")
# Password exposed in logs (if logs breached)

# ✅ RIGHT:
audit_logger.info(f"User {username} login attempt")
# Log action, not secrets
```

**Mistake 2: Audit logs without protection**
```bash
# ❌ WRONG:
# Audit logs stored unencrypted
# Attacker can edit logs to cover tracks

# ✅ RIGHT:
# 1. Immutable log storage (append-only)
# 2. Encrypt logs in transit and at rest
# 3. Ship logs to central system (can't be modified locally)
# 4. Separate system with restricted access
```

**Mistake 3: No audit log retention policy**
```bash
# ❌ WRONG:
# Logs deleted after 30 days
# Need to prove incident from 90 days ago: no evidence!

# ✅ RIGHT:
# HIPAA: 6 years minimum
# PCI-DSS: 1 year minimum
# GDPR: Duration of data + 1 year after deletion
```

**Mistake 4: Compliance tool without consequences**
```yaml
# ❌ WRONG:
# Tool flags non-compliant configuration
# No enforcement, just warning
# Non-compliant config deployed anyway

# ✅ RIGHT:
# Tool enforces compliance (blocks deployment)
# All production configs verified at deploy time
```

**Mistake 5: "Security by obscurity" for compliance**
```bash
# ❌ WRONG:
# Don't document security controls
# Don't log access
# "Secret" system is secure (it's not)

# ✅ RIGHT:
# Document all controls
# Audit log everything
# Regular security review
# External audit/penetration testing
```

## Production Incident Scenario

### Scenario: "HIPAA Audit failed; unauthorized access to patient data detected"

**Symptoms:**
- Audit shows 50 accesses to patient records by non-clinical staff
- Some accesses at 3 AM (suspicious timing)
- No RBAC preventing these accesses

**Investigation:**

```bash
# 1. Review audit logs for unauthorized access
grep "patient-records" /var/log/app-audit.log | \
  jq 'select(.user != "doctor" and .user != "nurse")'

# 2. Check RBAC at time of access
kubectl get rolebindings -A | \
  grep "patient-data" | \
  grep "billing-team"  # ← Found! Billing had access

# 3. Determine why billing team had access
# (Answer: Accidental role binding)

# 4. Check what data was accessed
grep "patient-records" /var/log/app-audit.log | \
  jq '.requestObject.query' | \
  sort | uniq  # Shows search terms used (PHI exposure!)
```

**Root Cause:**
- No RBAC preventing non-clinical access to patient data
- Access logging present but not enforced
- Role binding too permissive

**Solution:**

```bash
# 1. Immediate: Remove unauthorized access
kubectl delete rolebinding patient-data-viewer -n billing

# 2. Fix RBAC: Only clinical staff can access patient data
kubectl apply -f - << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: clinical-staff-only
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["patient-records"]
  verbs: ["get", "list"]
subjects:
- kind: Group
  name: doctors
- kind: Group
  name: nurses
EOF

# 3. Implement Segregation of Duties
# Billing team can access: appointment_summaries (not medical records)
# Clinical team can access: patient_records, vital_signs
# IT team can access: system_logs (not patient data)

# 4. Enable detailed audit logging
kubectl apply -f - << 'EOF'
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
- level: RequestResponse
  verbs: ["get", "list"]
  resources: ["secrets"]
  resourceNames: ["patient-records"]
  # Log all access to patient records
EOF

# 5. Set up alerts
# Alert if non-clinical user accesses patient data
# Alert if access occurs outside business hours
# Alert if bulk access (>100 records in 1 minute)

# 6. Breach notification (if data actually accessed/copied)
# Notify patients within 60 days (HIPAA)
# Notify HHS and media based on threshold
```

**Prevention:**
- RBAC enforces least privilege
- Audit logs track all access (immutable)
- Automated alerts on suspicious patterns
- Regular RBAC review (quarterly)
- Segregation of duties (billing ≠ clinical)

## Practice Questions

1. **Scenario:** GDPR user requests deletion. You delete from database. Is that enough?
   - Answer: No. Also delete from: backups, caches, search indexes, analytics. Keep audit log. Ensure all vendors delete too.

2. **Question:** How long should audit logs be kept?
   - Answer: Depends on regulation (HIPAA: 6 years, PCI-DSS: 1 year, GDPR: while data exists + 1 year). Default: 7 years.

3. **Decision:** Should audit logs be encrypted?
   - Answer: Yes, especially for healthcare/payment data. Also make immutable (append-only storage, separate system).

4. **Comparison:** Compliance vs Security?
   - Compliance: Meeting regulatory requirements (legal obligation)
   - Security: Protecting systems (technical practice)
   Both needed. Compliance without security is theater. Security without documentation won't pass audit.

## Further Reading

- [HIPAA Compliance Guide](https://www.hhs.gov/hipaa/for-professionals/security/index.html)
- [PCI-DSS Requirements](https://www.pcisecuritystandards.org/)
- [GDPR Article 32 (Security)](https://gdpr-info.eu/art-32-gdpr/)
- [SOC2 Report](https://www.aicpa.org/cpa-become-cpa/licensure-requirements/uniform-cpa-examination/aicpa-soc-2-service-organizations-control-system)
- [Kubernetes Audit Logging](https://kubernetes.io/docs/tasks/debug-application-cluster/audit/)

---

**Next:** Detect, contain, and respond to security incidents—[Incident Response](05-incident-response.md)
