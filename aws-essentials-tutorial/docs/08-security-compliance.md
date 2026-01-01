# Module 8: Security & Compliance

Security must be built in from the start, not bolted on. This module covers encryption, secrets management, threat detection, and compliance.

## 8.1 KMS: Key Management Service

KMS manages encryption keys. Keys encrypt data at-rest and in-transit.

### Customer Master Keys (CMKs)

AWS manages key material (never exposed), you manage permissions.

```bash
# Create CMK
aws kms create-key --description "MyApp encryption key"

# Get key ID
KEY_ID=$(aws kms create-key --query 'KeyMetadata.KeyId' --output text)

# Encrypt data
aws kms encrypt --key-id $KEY_ID \
  --plaintext "sensitive data" \
  --query CiphertextBlob --output text > encrypted.txt

# Decrypt data
aws kms decrypt --ciphertext-blob fileb://encrypted.txt \
  --query Plaintext --output text | base64 -d
```

### Encryption Use Cases

**S3 encryption** (server-side):
```bash
aws s3api put-object --bucket my-bucket --key sensitive.txt \
  --body sensitive.txt \
  --sse aws:kms --sse-kms-key-id $KEY_ID
```

**RDS encryption**:
```bash
aws rds create-db-instance --db-instance-identifier mydb \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --storage-encrypted \
  --kms-key-id $KEY_ID
```

**DynamoDB encryption**:
```bash
aws dynamodb create-table --table-name Users \
  --sse-specification Enabled=true,SSEType=KMS,KMSMasterKeyId=$KEY_ID \
  ...
```

### Key Rotation

Automatically rotate keys every 90 days:

```bash
aws kms enable-key-rotation --key-id $KEY_ID
```

## 8.2 Secrets Manager

Secrets Manager stores database passwords, API keys, and credentials. Rotate automatically without downtime.

```bash
# Create secret
aws secretsmanager create-secret --name prod/db-password \
  --description "Production RDS password" \
  --secret-string "MySecurePassword123"

# Retrieve secret
aws secretsmanager get-secret-value --secret-id prod/db-password \
  --query SecretString

# Update secret
aws secretsmanager update-secret --secret-id prod/db-password \
  --secret-string "NewSecurePassword456"
```

### Automatic Rotation

Rotate credentials without downtime:

```bash
# Create Lambda function to rotate password
cat > rotate.py << 'EOF'
def lambda_handler(event, context):
    secret_id = event['SecretId']
    client_secret = event['ClientSecret']
    
    # Generate new password
    new_password = generate_secure_password()
    
    # Update application secret
    update_secret(secret_id, new_password)
    
    # Update database password
    update_database_password(new_password)
    
    return {'statusCode': 200}
EOF

# Configure rotation
aws secretsmanager rotate-secret --secret-id prod/db-password \
  --rotation-rules AutomaticallyAfterDays=30 \
  --rotation-lambda-arn arn:aws:lambda:...
```

## 8.3 VPC Endpoints & PrivateLink

Access AWS services from private subnets without internet gateway (more secure, faster, cheaper).

```bash
# Create S3 VPC endpoint
aws ec2 create-vpc-endpoint --vpc-id vpc-12345 \
  --service-name com.amazonaws.us-east-1.s3 \
  --route-table-ids rtb-12345

# EC2 in private subnet can now access S3 without NAT
# Traffic stays within AWS network
```

## 8.4 GuardDuty: Threat Detection

GuardDuty analyzes CloudTrail, VPC Flow Logs, and DNS logs for threats.

```bash
# Enable GuardDuty
aws guardduty create-detector --enable
```

Detects:
- Compromised EC2 instances (unusual API calls)
- Brute force attacks (many failed SSH attempts)
- Cryptocurrency mining
- Data exfiltration
- Malware

## 8.5 Security Hub: Compliance

Security Hub aggregates security findings. Checks against CIS benchmarks and compliance standards.

```bash
# Enable Security Hub
aws securityhub enable-security-hub

# Get compliance status
aws securityhub describe-standards-controls
```

Checks for:
- Unencrypted S3 buckets
- Public RDS databases
- Root account usage (with MFA)
- Unused credentials
- Overly permissive security groups

## 8.6 Network Security Best Practices

### Principle of Least Privilege

Allow only what's necessary:

Good:
```
Security Group: App Servers
Inbound:
  - Port 443 from 0.0.0.0/0 (HTTPS from anyone)
  - Port 80 from 0.0.0.0/0 (HTTP from anyone)
```

Bad:
```
Security Group: App Servers
Inbound:
  - All traffic from 0.0.0.0/0 (anybody can do anything)
```

### Bastion Hosts

SSH into private servers through bastion in public subnet:

```
User SSH (port 22) → Bastion Host (public subnet)
    ↓ (port 22)
Private EC2 Instance
```

Only bastion is internet-accessible. Private servers are truly private.

### VPC Flow Logs

Log all network traffic for analysis:

```bash
# Enable VPC Flow Logs
aws ec2 create-flow-logs --resource-type VPC \
  --resource-ids vpc-12345 \
  --traffic-type ALL \
  --log-destination-type CLOUD_WATCH_LOGS \
  --log-group-name /aws/vpc/flowlogs
```

Logs show:
- Source/destination IPs
- Ports and protocols
- Bytes sent/received
- Accept/Reject (blocked traffic)

## 8.7 Common Mistakes

**Mistake 1: Using root account**
Root has unlimited permissions. If compromised, attacker owns the account. Always use IAM users/roles.

**Mistake 2: Storing credentials in code**
Never:
```python
aws_key = "AKIA123456789"
aws_secret = "secret123"
```

Always use:
- IAM roles (EC2, Lambda)
- Environment variables (passed by CI/CD)
- Secrets Manager

**Mistake 3: Not encrypting data at-rest**
Encryption adds 5% overhead and eliminates data loss from stolen disks. Always encrypt.

**Mistake 4: Public databases**
RDS accessible from internet (0.0.0.0/0) is a security disaster. Use private subnets only.

**Mistake 5: Not rotating credentials**
Leaked credentials stay leaked. Rotate every 90 days.

## Assessment

### Practice Questions

**Q1: Where should you store RDS password?**
A) In application code
B) Environment variable
C) Secrets Manager (with rotation)
D) S3 bucket

**Q2: EC2 instance needs S3 access. How to authenticate?**
A) Embed access key in application
B) Store key in ~/.aws/credentials
C) Use IAM instance role
D) Use root account credentials

**Q3: Which finding from Security Hub is most critical?**
A) Unencrypted S3 bucket (no sensitive data)
B) Public RDS database
C) Root account MFA disabled
D) Log group retention 30 days

**Q4: GuardDuty detects unusual API calls from EC2. What likely happened?**
A) Programming bug
B) EC2 instance compromised
C) CloudTrail misconfiguration
D) AWS internal testing

**Q5: VPC endpoint to S3 vs. NAT gateway: Which is more secure?**
A) NAT gateway (external routing)
B) VPC endpoint (stays on AWS network)
C) Same security
D) Depends on region

### Hands-On Labs

**Lab 1: KMS and Encryption**

Create CMK, encrypt/decrypt data, rotate keys.

**Lab 2: Secrets Manager**

Create secret, retrieve in application, configure rotation.

### Production Incident Scenario

**Scenario: Compromised Database Credentials**

Database credentials posted in GitHub. Before you notice, attacker accesses database for 2 hours.

Damage:
- Customer data copied
- Database modified with malicious records
- Encryption keys?

Recovery:
1. Rotate database password immediately
2. Review database logs (CloudTrail, database audit logs) to see what was accessed
3. Notify customers of breach (GDPR required)
4. Investigate GitHub access logs
5. Restore from clean backup (if audit shows corruption)

Prevention:
- Secrets Manager (auto-rotates, no hardcoding)
- GitHub secret scanning (detects committed credentials)
- CloudTrail (audit trail of accesses)
- VPC: Database not internet-accessible
- GuardDuty: Detect unusual queries

---

Next Module: [Module 9: Cost Management & Optimization](09-cost-management.md)
