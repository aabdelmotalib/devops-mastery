# Advanced Terraform: Infrastructure as Code Mastery

## Overview

**Terraform** is the industry-standard Infrastructure as Code (IaC) tool that lets you define cloud infrastructure in code, version control it, and automate deployments. This module covers Terraform best practices, state management, modules, and production patterns.

## Mental Model

```
Infrastructure Evolution:

Phase 1: Manual (Click-click-click)
┌──────────────────────────────────┐
│  AWS Console                     │
│  1. Create EC2 instance          │
│  2. Create security group        │
│  3. Create ALB                   │
│  4. Create RDS database          │
│  (30 minutes, error-prone)       │
│                                  │
│  Disaster: Server dies           │
│  → Manual recovery (hours)       │
└──────────────────────────────────┘

Phase 2: Scripts (Bash)
┌──────────────────────────────────┐
│  AWS CLI scripts                 │
│  #!/bin/bash                     │
│  aws ec2 run-instances ...       │
│  aws ec2 create-security-group   │
│  (Hard to test, limited)         │
└──────────────────────────────────┘

Phase 3: Terraform (IaC) ← YOU ARE HERE
┌──────────────────────────────────┐
│  main.tf (Declarative)           │
│  resource "aws_instance" "app"   │
│  resource "aws_security_group"   │
│  resource "aws_db_instance"      │
│                                  │
│  Benefits:                       │
│  • Version control               │
│  • Repeatable deployments        │
│  • Test before apply             │
│  • Easy disaster recovery        │
│  • Team collaboration            │
│  (Minutes, consistent)           │
└──────────────────────────────────┘

Phase 4: GitOps (Terraform + Git)
┌──────────────────────────────────┐
│  Git is source of truth          │
│  Push to main → Auto-deploy      │
│  Audit trail of all changes      │
│  (Full automation)               │
└──────────────────────────────────┘

Terraform Advantage:
  ❌ Manual: 30 min, 10 clicks, inconsistent
  ❌ Scripts: Fragile, hard to maintain
  ✅ Terraform: 2 min, versioned, reproducible
  ✅ GitOps: Automatic, audited, safe
```

## Core Concepts

### 1. Terraform Blocks & Structure

```hcl
# Configuration for AWS provider
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  # Store state in S3 (not local machine)
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region
}

# Input variables
variable "app_name" {
  type        = string
  description = "Application name"
  default     = "myapp"
}

# Resource definition
resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id  # Get latest Ubuntu
  instance_type = var.instance_type       # From variable
  
  tags = {
    Name        = "${var.app_name}-server"
    Environment = var.environment
  }
}

# Output (expose values after apply)
output "server_ip" {
  value       = aws_instance.app_server.public_ip
  description = "Public IP of app server"
}

# Data source (read existing resources)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical
  
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}
```

### 2. State Management

Terraform maintains state (tfstate) to track resources:

```hcl
# Create state file with encryption & locking

terraform {
  backend "s3" {
    bucket         = "my-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true                    # Enable encryption
    dynamodb_table = "terraform-locks"       # Prevent concurrent edits
  }
}

# ❌ WRONG: Local state (single laptop)
# If laptop crashes: state lost, can't manage resources
# If two people edit: conflicts and corruption

# ✅ RIGHT: Remote state (S3 + DynamoDB)
# S3: Durable storage, versioning, encryption
# DynamoDB: Locking prevents concurrent edits
```

### 3. Modules (Reusable Infrastructure)

```hcl
# Main: Use a module
module "vpc" {
  source = "./modules/vpc"
  
  cidr_block = "10.0.0.0/16"
  region     = "us-east-1"
  
  tags = {
    Environment = "prod"
  }
}

module "database" {
  source = "terraform-aws-modules/rds/aws"
  version = "~> 5.0"
  
  identifier = "myapp-db"
  engine     = "postgres"
  
  db_subnet_group_name = module.vpc.db_subnet_group_id
}

# modules/vpc/main.tf
resource "aws_vpc" "main" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  
  tags = merge(var.tags, { Name = "main-vpc" })
}

resource "aws_subnet" "private" {
  count             = 3
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.cidr_block, 4, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]
}

# modules/vpc/outputs.tf
output "vpc_id" {
  value = aws_vpc.main.id
}

output "db_subnet_group_id" {
  value = aws_db_subnet_group.db.id
}
```

### 4. Workspaces (Separate Environments)

```bash
# Create environments with workspaces
terraform workspace new dev
terraform workspace new prod

# Select workspace
terraform workspace select prod

# Apply creates separate resources
terraform apply  # Creates prod resources

terraform workspace select dev
terraform apply  # Creates dev resources

# Same code, different environments
# Different state files: prod.tfstate, dev.tfstate
```

### 5. Variables & Locals

```hcl
# Input variables (passed in)
variable "instance_count" {
  type        = number
  description = "Number of instances"
  default     = 1
  
  validation {
    condition     = var.instance_count > 0 && var.instance_count <= 10
    error_message = "Instance count must be 1-10."
  }
}

# Local values (computed)
locals {
  common_tags = {
    Project     = "myapp"
    Environment = terraform.workspace
    ManagedBy   = "Terraform"
  }
  
  app_name = "${var.app_name}-${terraform.workspace}"
}

# Using
resource "aws_instance" "app" {
  count         = var.instance_count
  instance_type = "t3.micro"
  
  tags = merge(
    local.common_tags,
    { Name = "${local.app_name}-${count.index + 1}" }
  )
}
```

## Hands-On: Deploy VPC with Terraform

### Step 1: Initialize Terraform

```bash
# Create project directory
mkdir terraform-vpc && cd terraform-vpc

# Create main.tf
cat > main.tf << 'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  
  tags = {
    Name = "main-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
  
  tags = {
    Name = "public-subnet"
  }
}

output "vpc_id" {
  value = aws_vpc.main.id
}

output "subnet_id" {
  value = aws_subnet.public.id
}
EOF

# Initialize
terraform init
# Output: Terraform has been successfully configured
```

### Step 2: Plan & Review Changes

```bash
# Preview changes before applying
terraform plan

# Output:
# Terraform will perform the following actions:
#
#   + resource "aws_vpc" "main"
#       + cidr_block           = "10.0.0.0/16"
#       + enable_dns_hostnames = true
#
#   + resource "aws_subnet" "public"
#       + vpc_id       = (known after apply)
#       + cidr_block   = "10.0.1.0/24"
#
# Plan: 2 to add, 0 to change, 0 to destroy
```

### Step 3: Apply Configuration

```bash
# Apply changes
terraform apply

# Review plan, type "yes" to confirm
# 
# Apply complete! Resources: 2 added, 0 changed, 0 destroyed
# 
# Outputs:
# vpc_id = "vpc-0123456789abcdef"
# subnet_id = "subnet-0123456789abcdef"
```

### Step 4: Modify & Update

```hcl
# Add another subnet to main.tf
resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  
  tags = {
    Name = "private-subnet"
  }
}

# Plan shows only new subnet
terraform plan
# Plan: 1 to add, 0 to change, 0 to destroy

terraform apply
# Apply complete! Resources: 1 added
```

### Step 5: Destroy

```bash
# Remove all resources
terraform destroy

# Confirmation: type "yes"
# Destroy complete! Resources: 3 destroyed.
```

## Common Mistakes

**Mistake 1: Storing state locally**
```hcl
# ❌ WRONG:
# terraform.tfstate on laptop
# If laptop crashes: resources become unmanageable
# If two people edit: state corruption

# ✅ RIGHT:
terraform {
  backend "s3" {
    bucket = "company-terraform-state"
    key    = "prod/terraform.tfstate"
    # S3 versioning + DynamoDB locking
  }
}
```

**Mistake 2: Hardcoding values**
```hcl
# ❌ WRONG:
resource "aws_instance" "app" {
  instance_type = "t3.micro"  # Hardcoded
  region        = "us-east-1"  # Hardcoded
}
# Can't reuse for different environments

# ✅ RIGHT:
variable "instance_type" {
  default = "t3.micro"
}

variable "aws_region" {
  default = "us-east-1"
}

resource "aws_instance" "app" {
  instance_type = var.instance_type
}

provider "aws" {
  region = var.aws_region
}
```

**Mistake 3: Manual edits to infrastructure**
```bash
# ❌ WRONG:
# terraform apply creates resources
# Then manually edit in AWS Console
# terraform apply tries to recreate → conflicts

# ✅ RIGHT:
# Only modify via Terraform code
# Everything tracked in version control
# Manual changes: terraform import to bring back to code
```

**Mistake 4: Not testing before production**
```bash
# ❌ WRONG:
# Write Terraform code
# Run terraform apply in production
# Oops, syntax error, resources partially created

# ✅ RIGHT:
# Test in dev environment first
terraform plan -var-file="dev.tfvars"  # Preview
terraform apply -var-file="dev.tfvars" # Deploy to dev

# Verify works, then:
terraform apply -var-file="prod.tfvars" # Deploy to prod
```

**Mistake 5: Sharing credentials in Terraform code**
```hcl
# ❌ WRONG:
provider "aws" {
  region     = "us-east-1"
  access_key = "AKIA..."  # EXPOSED!
  secret_key = "wJa..."   # EXPOSED!
}

# ✅ RIGHT:
# Use AWS credentials from environment/IAM role
provider "aws" {
  region = "us-east-1"
}

# Or use .tfvars file (not in git):
# terraform.tfvars (add to .gitignore)
variable "aws_access_key" {}
variable "aws_secret_key" {}
```

## Production Incident Scenario

### Scenario: "Terraform apply deleted production database"

**What Happened:**

```hcl
# Original code
resource "aws_db_instance" "prod_db" {
  identifier     = "myapp-db"
  engine         = "postgres"
  instance_class = "db.t3.medium"
}

# Developer removes resource (thinking it's old code)
# Accidentally removed from main.tf (meant to remove from dev)

# Runs: terraform apply -var-file="prod.tfvars"
# Terraform sees: DB in state but not in code
# Result: Database DELETED (with data!)
```

**Root Cause:**
- No approval process for production changes
- Removed resource without checking what environment
- No production safeguards

**Investigation:**

```bash
# 1. Check git history
git log --oneline main.tf | head -5
# Found: commit abc123 "Remove old database"

# 2. Check who made change
git show abc123
# Author: developer@company.com
# "Removed old database" (but it was prod!)

# 3. Check state history
aws s3api list-object-versions \
  --bucket terraform-state \
  --prefix prod/terraform.tfstate
# State files from last hour preserved

# 4. Restore from backup
terraform state pull > current.tfstate
# Current state shows DB deleted

# Restore from S3 version history
aws s3api get-object \
  --bucket terraform-state \
  --key prod/terraform.tfstate \
  --version-id old-version-id \
  restored.tfstate

# Manually restore RDS from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier myapp-db \
  --db-snapshot-identifier myapp-db-snapshot-2024-01-06
```

**Prevention:**

```hcl
# 1. Require approval for production changes
# In CI/CD: Plan step + manual approval before apply

# 2. Use lifecycle rules to prevent accidental deletion
resource "aws_db_instance" "prod_db" {
  identifier     = "myapp-db"
  engine         = "postgres"
  instance_class = "db.t3.medium"
  
  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = true
  }
}

# Now: terraform destroy will FAIL
# Must manually remove lifecycle block first

# 3. Separate code for environments
# prod/main.tf
# dev/main.tf
# Different state files, different approval process

# 4. Use remote state with backup
terraform {
  backend "s3" {
    bucket = "terraform-state"
    # S3 versioning enabled (automatic backup)
  }
}
```

## Practice Questions

1. **Scenario:** You created an EC2 instance with `terraform apply`. Someone manually changes the instance type in AWS Console. What happens next?
   - Answer: Next `terraform plan` shows difference. `terraform apply` reverts manual change back to code. Manual changes = bad.

2. **Question:** Should you commit terraform.tfstate to Git?
   - Answer: NO. It contains sensitive data and causes conflicts. Use remote state (S3, Terraform Cloud) instead.

3. **Decision:** What's the best way to manage dev vs prod?
   - Answer: Use separate directories (dev/, prod/) OR workspaces, both with separate state files and approval processes.

4. **Comparison:** Terraform destroy vs removing resource from code?
   - Destroy: Removes all resources at once
   - Remove from code: Only removes that resource (others stay)
   Use remove-from-code for gradual cleanup.

## Further Reading

- [Terraform Official Docs](https://www.terraform.io/docs)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform State Management](https://www.terraform.io/docs/state)
- [Terraform Modules Registry](https://registry.terraform.io/)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guide/recommended-practices)

---

**Next:** Automate configuration management with [Ansible Deep Dive](14-ansible-deep-dive.md)
