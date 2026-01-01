# Module 2: Identity & Access Management (IAM)

IAM is the security foundation of every AWS account. Poor IAM practices lead to compromised accounts, data breaches, and unauthorized resource deletion. This module covers how to implement security through least privilege access control.

## 2.1 IAM Core Concepts

IAM manages who can do what in your AWS account. It's fundamentally about authentication (proving who you are) and authorization (what you're allowed to do).

### Principals

A principal is anything requesting access to AWS resources:
- **Users**: Human employees or contractors
- **Roles**: Sets of permissions that can be assumed by users, services, or other roles
- **Services**: AWS services like EC2 needing permission to call other services
- **Federated identities**: External users from corporate AD, Google, etc.

### Identities vs. Resources

IAM secures two things:
1. **Identity-based policies**: Grant permissions to users/roles (most common)
2. **Resource-based policies**: Grant permissions on specific resources (S3 buckets, SQS queues)

Example identity policy: "This IAM user can read from S3 bucket example-bucket"
Example resource policy: "This S3 bucket allows anyone from company IP range to read objects"

### Authentication Methods

**Credentials**:
- **Access keys**: Programmatic access (AWS CLI, SDKs)
- **Passwords**: Console login (users only)
- **Temporary credentials**: Created by STS, expire in minutes to hours

**Multi-factor Authentication (MFA)**:
- Adds second authentication factor (authenticator app, hardware token)
- Mandatory in production for human users
- Optional for temporary credentials

## 2.2 Users, Groups, and Roles

### Users

An IAM user represents a person or application. Users have:
- Username and password (for console login)
- Access keys (for programmatic access)
- Assigned policies (direct or via groups)

Permissions are permanent until explicitly removed.

```bash
# Create a user
aws iam create-user --user-name alice

# Attach policy
aws iam attach-user-policy --user-name alice \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Create access keys for CLI/SDK
aws iam create-access-key --user-name alice
```

**Production Note**: Never use root account. Create IAM users for all human access.

### Groups

A group is a collection of users with shared permissions. Grouping simplifies management.

```bash
# Create group
aws iam create-group --group-name developers

# Attach policies to group
aws iam attach-group-policy --group-name developers \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

# Add users to group
aws iam add-user-to-group --group-name developers --user-name alice
aws iam add-user-to-group --group-name developers --user-name bob
```

Both alice and bob now have EC2 full access. When new developers join, add them to the group; when they leave, remove them.

### Roles

A role is a set of permissions that can be assumed by users, services, or other accounts. Unlike users, roles have no permanent credentials. When you assume a role, you receive temporary credentials valid for 15 minutes to 12 hours.

Roles are for two scenarios:
1. **Cross-account access**: User in account A assumes role in account B
2. **Service access**: EC2 instance assumes role to access other AWS services

```bash
# Create a role for EC2 to use
aws iam create-role --role-name ec2-app-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "ec2.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policy to role
aws iam attach-role-policy --role-name ec2-app-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Create instance profile to attach role to EC2
aws iam create-instance-profile --instance-profile-name ec2-app-profile
aws iam add-role-to-instance-profile --instance-profile-name ec2-app-profile \
  --role-name ec2-app-role

# Launch EC2 with this role
aws ec2 run-instances --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.micro \
  --iam-instance-profile Name=ec2-app-profile
```

When this EC2 instance runs, it automatically has S3 read-only access. No access keys to manage.

## 2.3 Policies: The Core of Permission Management

A policy is a JSON document defining actions (what) on resources (where) under conditions (when).

### Policy Structure

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::my-bucket/*"
    },
    {
      "Effect": "Deny",
      "Action": "s3:DeleteObject",
      "Resource": "arn:aws:s3:::my-bucket/protected/*"
    }
  ]
}
```

Components:
- **Effect**: "Allow" or "Deny" (Deny always wins)
- **Action**: What API calls are permitted (e.g., s3:GetObject)
- **Resource**: ARN (Amazon Resource Name) specifying what resources the policy applies to
- **Condition**: Optional restrictions (IP address, time of day, MFA requirement)

### ARN Format

```
arn:partition:service:region:account-id:resource-type/resource-id
arn:aws:s3:::my-bucket/documents/*
  ├─ partition: aws
  ├─ service: s3
  ├─ region: (empty for S3, which is global)
  ├─ account-id: (empty for S3)
  └─ resource: my-bucket/documents/* (wildcard for all files in documents folder)
```

Another example:
```
arn:aws:ec2:us-east-1:123456789012:instance/i-0123456789abcdef0
  ├─ service: ec2
  ├─ region: us-east-1
  ├─ account-id: 123456789012
  └─ instance with ID i-0123456789abcdef0
```

### Common Policy Examples

**Read-only S3 access**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:GetObject", "s3:ListBucket"],
    "Resource": [
      "arn:aws:s3:::my-bucket",
      "arn:aws:s3:::my-bucket/*"
    ]
  }]
}
```

**Write to specific S3 bucket only**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject"],
    "Resource": "arn:aws:s3:::my-app-uploads/*"
  }]
}
```

**Cross-account role assumption**:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "sts:AssumeRole",
    "Resource": "arn:aws:iam::999999999999:role/cross-account-role"
  }]
}
```

## 2.4 Least Privilege Principle

Least privilege means granting the minimum permissions necessary to do a job. It's the foundation of secure AWS architecture.

### Anti-pattern: Overly Permissive

```json
{
  "Effect": "Allow",
  "Action": "*",
  "Resource": "*"
}
```

This grants full AWS access. Ever. If the user's credentials are compromised, an attacker has complete access to your account.

### Better: Principle of Least Privilege

Grant only what's needed:

Developer needs to deploy code to S3:
```json
{
  "Effect": "Allow",
  "Action": ["s3:PutObject", "s3:GetObject"],
  "Resource": "arn:aws:s3:::my-app-releases/*"
}
```

Database administrator needs to create RDS snapshots:
```json
{
  "Effect": "Allow",
  "Action": [
    "rds:CreateDBSnapshot",
    "rds:DescribeDBSnapshots"
  ],
  "Resource": "arn:aws:rds:*:*:db/*"
}
```

### Implementation Strategy

1. **Deny by default**: No permissions unless explicitly granted
2. **Whitelist model**: Only grant specific actions on specific resources
3. **Time-based access**: Temporary elevations for sensitive operations
4. **Audit everything**: CloudTrail logs every API call
5. **Review periodically**: Remove permissions when roles change

## 2.5 Cross-Account Access

Enterprise environments often have multiple AWS accounts:
- One for development
- One for staging
- One for production
- One for billing/security oversight

Users in one account need to access resources in another. This is where role assumption comes in.

### Cross-Account Role Example

Account A (dev): User alice@company.com
Account B (prod): RDS database with customer data

Setup:
1. In Account B, create role `cross-account-rds-read` with RDS read permissions
2. In Account B, set trust relationship to allow Account A principals
3. In Account A, create policy allowing alice to assume the role
4. alice runs: `aws sts assume-role --role-arn arn:aws:iam::999999999999:role/cross-account-rds-read`
5. STS returns temporary credentials
6. alice now has RDS read access in Account B

Benefits:
- alice's permanent credentials stay in Account A
- Account B has temporary credentials (auto-expire)
- Audit trail in Account B shows which Account A user accessed resources
- Easy to revoke: Delete the trust relationship

## 2.6 Best Practices

### 1. Enable MFA for All Human Users

```bash
# Create virtual MFA
aws iam enable-mfa-device --user-name alice \
  --serial-number arn:aws:iam::123456789012:mfa/alice \
  --authentication-code1 123456 \
  --authentication-code2 654321
```

Every login and sensitive operation requires MFA code. Protects against credential theft.

### 2. Use IAM Roles for Services, Not Access Keys

When your EC2 instance needs S3 access, use an instance role (no access keys to leak).

Bad:
```bash
# EC2 instance has long-term access keys embedded
export AWS_ACCESS_KEY_ID="AKIA123456789"
export AWS_SECRET_ACCESS_KEY="secret123..."
```

Good:
```bash
# EC2 assumes role with temporary credentials
aws ec2 run-instances --iam-instance-profile Name=ec2-app-role
# Application uses temporary credentials from metadata service
```

### 3. Rotate Access Keys Regularly

If you must use access keys (CLI, CI/CD), rotate them every 90 days.

```bash
# Create new key
aws iam create-access-key --user-name alice

# Update applications to use new key

# Delete old key
aws iam delete-access-key --user-name alice --access-key-id AKIA123456789
```

### 4. Use Policy Conditions for Additional Security

Require MFA for sensitive operations:
```json
{
  "Effect": "Allow",
  "Action": "rds:DeleteDBInstance",
  "Resource": "*",
  "Condition": {
    "Bool": {"aws:MultiFactorAuthPresent": "true"}
  }
}
```

Restrict to specific IP ranges (for on-premises access):
```json
{
  "Effect": "Allow",
  "Action": "ec2:*",
  "Resource": "*",
  "Condition": {
    "IpAddress": {"aws:SourceIp": "203.0.113.0/24"}
  }
}
```

### 5. Regular Access Reviews

Quarterly:
- List all users and their permissions
- Remove users who left the company
- Remove permissions that are no longer needed
- Review cross-account access

```bash
# List users
aws iam list-users

# List user permissions
aws iam list-user-policies --user-name alice

# List attached policies
aws iam list-attached-user-policies --user-name alice
```

## 2.7 AWS Managed vs. Customer Managed Policies

**AWS Managed Policies**: Pre-built policies for common use cases. Updated by AWS.

Examples:
- AmazonS3ReadOnlyAccess
- AmazonEC2FullAccess
- AmazonRDSReadOnlyAccess

Pros: Simple, well-tested, auto-updated
Cons: Often more permissive than needed

**Customer Managed Policies**: Custom policies you create for specific needs.

Pros: Precisely limited, full control
Cons: Must maintain and update

Production best practice: Use customer managed policies for production. AWS managed policies are acceptable for development.

```bash
# Create customer managed policy
aws iam create-policy --policy-name app-s3-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::app-data/*"
    }]
  }'

# Attach to user
aws iam attach-user-policy --user-name alice \
  --policy-arn arn:aws:iam::123456789012:policy/app-s3-access
```

## 2.8 Common Mistakes

**Mistake 1: Using root account credentials**
Root has unlimited permissions. If compromised, attacker owns your entire AWS account. Root credentials cannot be revoked. Always create IAM users.

**Mistake 2: Sharing access keys**
If Bob's credentials are shared for "just this once," revoking Bob's access revokes Bob's ability to do legitimate work. Use roles for shared scenarios.

**Mistake 3: Wildcard permissions in production**
`Action: "*"` on `Resource: "*"` means compromised credentials = total account takeover. Always specify exact actions and resources.

**Mistake 4: Not rotating access keys**
Old access keys accumulate. If one is leaked, you don't know which, so you rotate all. Rotate proactively every 90 days.

**Mistake 5: Storing credentials in code**
Never:
```python
import boto3
client = boto3.client('s3',
    aws_access_key_id='AKIA123456789',
    aws_secret_access_key='secret...')
```

Always use roles, environment variables, or credential files.

## 2.9 Production Notes

### IAM Security Checklist

- [ ] All human users have MFA enabled
- [ ] No access keys older than 90 days
- [ ] Root account access is disabled/unavailable
- [ ] Cross-account roles have explicit trust relationships
- [ ] Policies follow least privilege (specific actions, specific resources)
- [ ] CloudTrail is enabled to audit all IAM changes
- [ ] Monthly access reviews performed
- [ ] Service roles only grant necessary permissions
- [ ] No credentials in code or environment variables
- [ ] All API calls are logged in CloudTrail

### Audit Trail: CloudTrail

Every IAM action is logged in CloudTrail. Use it to:
- Find who deleted that important resource
- Audit compliance (who accessed sensitive data)
- Detect suspicious activity (failed login attempts, permission changes)

## Assessment

### Practice Questions

**Q1: An EC2 instance needs to write logs to CloudWatch. Should you use access keys or a role?**
A) Access keys (more direct)
B) Role with instance profile (best practice)
C) Both
D) Neither; EC2 doesn't need CloudWatch access

**Q2: You need to grant a developer read-only S3 access to buckets starting with "dev-". What's the correct resource ARN?**
A) arn:aws:s3:::*
B) arn:aws:s3:::dev-*
C) arn:aws:s3:::dev-*/\*
D) Both B and C

**Q3: What happens if both an Allow and Deny policy apply to the same action?**
A) Allow wins (most permissive)
B) Deny wins (most restrictive)
C) They're combined (both apply)
D) Explicit Allow overrides Explicit Deny

**Q4: You accidentally shared database credentials in a Slack message. What should you do?**
A) Just monitor for unauthorized access
B) Rotate credentials immediately (they might be cached by Slack)
C) Send follow-up message "Please delete my previous message"
D) Credentials in messages are always encrypted by Slack; no risk

**Q5: A contractor needs temporary production access for 1 week. How should you grant it?**
A) Create an IAM user with password (they can delete it later)
B) Create an IAM role and use STS to issue 1-week credentials
C) Add them to production group (easier)
D) Share root credentials (most direct)

### Hands-On Labs

**Lab 1: Create IAM Users, Groups, and Policies**

Objective: Practice least-privilege IAM design.

Tasks:
1. Create two IAM groups: developers, admins
2. Create four IAM users: alice, bob, charlie, diana
3. Create a custom policy allowing S3 read access to "app-data" bucket only:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [{
       "Effect": "Allow",
       "Action": ["s3:GetObject", "s3:ListBucket"],
       "Resource": ["arn:aws:s3:::app-data", "arn:aws:s3:::app-data/*"]
     }]
   }
   ```
4. Attach this policy to developers group
5. Attach AmazonAdministratorAccess to admins group (for demo; never do in production)
6. Add alice, bob to developers
7. Add charlie, diana to admins
8. Verify: `aws iam get-user-policy --user-name alice --policy-name ...` should show inherited permissions

Success Criteria:
- Groups created and policies attached
- Users successfully listed
- Permissions inherited from group to user

**Lab 2: Cross-Account Role Assumption**

Objective: Practice cross-account access.

Tasks:
1. Create two AWS accounts (or use two IAM test accounts if single account)
2. In Account B, create role `cross-account-read-role`:
   ```bash
   aws iam create-role --role-name cross-account-read-role \
     --assume-role-policy-document '{
       "Version": "2012-10-17",
       "Statement": [{
         "Effect": "Allow",
         "Principal": {"AWS": "arn:aws:iam::ACCOUNT-A-ID:root"},
         "Action": "sts:AssumeRole"
       }]
     }'
   ```
3. Attach S3 read-only policy to this role
4. In Account A, create policy allowing assume-role:
   ```json
   {
     "Effect": "Allow",
     "Action": "sts:AssumeRole",
     "Resource": "arn:aws:iam::ACCOUNT-B-ID:role/cross-account-read-role"
   }
   ```
5. Attach to Account A user
6. Assume the role from Account A:
   ```bash
   aws sts assume-role --role-arn arn:aws:iam::ACCOUNT-B-ID:role/cross-account-read-role \
     --role-session-name cross-account-session
   ```
7. Credentials should be returned with temporary access

Success Criteria:
- Role successfully assumed
- Temporary credentials received
- Can list S3 buckets in Account B using temporary credentials

### Production Incident Scenario

**Scenario: Compromised Credentials**

At 9:00 AM, your security team notifies you: Someone posted AWS access keys (from a developer's laptop) in a public GitHub repository. The keys belong to user `jenkins-ci` and have EC2, RDS, and S3 permissions.

Timeline:
- 9:00 AM: GitHub alerts detected
- 9:05 AM: Security team extracts the keys from GitHub history
- 9:10 AM: CloudTrail shows suspicious activity: Delete commands on production RDS, unautorized EC2 launches in unknown regions

Impact:
- Production RDS databases deleted
- EC2 instances spawned in eu-west-1 and ap-southeast-1 (likely for crypto-mining)
- S3 bucket permissions modified
- Unknown data access

Questions:
1. What should be your first action in the first 5 minutes?
2. How would you determine the extent of the breach?
3. What systems were compromised due to poor permission design?
4. How would you have prevented this?

Recommended Response:
1. **Immediately** disable the `jenkins-ci` user access keys
2. Review CloudTrail to determine blast radius
3. Terminate unauthorized EC2 instances
4. Review RDS deletion events in CloudTrail backup to restore
5. Review S3 bucket policy changes and revert
6. Review all API calls from the compromised keys during the exposure window

Prevention:
- jenkins-ci should only have EC2 and S3 permissions (not RDS delete)
- Use an IAM role on the CI/CD server instead of long-term credentials
- Rotate credentials every 90 days
- Use AWS CloudTrail to detect suspicious activities (resource deletions)
- Implement GuardDuty threat detection (future module)

---

Next Module: [Module 3: Compute Services](03-compute-services.md)
