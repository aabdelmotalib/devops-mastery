# Module 07: Infrastructure as Code

## Architecture: Infrastructure Belongs in CI/CD

Infrastructure changes should be version controlled, tested, and deployed like code.

```
Old way:
  Ops engineer logs into production server
  Runs commands manually
  No version control
  Can't reproduce
  Disaster recovery is manual

Modern way:
  Infrastructure defined as code (Terraform, CloudFormation, etc.)
  Code is version controlled
  Deployed through CI/CD pipeline
  Reproducible
  Testable
```

Infrastructure as Code (IaC) means:
- Infrastructure definition (server config) is in Git
- Changes go through code review
- Deployment is automated
- History is tracked
- Rollback is automated

## Why IaC in CI/CD Pipeline?

Consider this scenario:

```
Code deployment: myapp:v1.5.0
Infrastructure hasn't changed: still one server, 4GB RAM

New code needs 8GB RAM (memory leak fixed in v1.5.1)
Operations team manually adds RAM
Change is documented in wiki (outdated)
Next person to provision server, reads outdated wiki
Provisions 4GB RAM
myapp:v1.5.1 crashes (memory exhausted)
Incident
```

Better:

```
Terraform code:
  resource "aws_instance" "app" {
    memory = "8GB"
  }

Code change myapp:v1.5.1 requires more RAM
Engineer updates Terraform to 8GB
Commit to Git
Code review (ops team checks memory change)
Approved
Merged to main
CI/CD deploys code + infrastructure change
New instances provisioned with 8GB RAM
myapp:v1.5.1 deployed
No memory issue
```

## Terraform Conceptually

Terraform is the standard IaC tool. It works with any cloud (AWS, Azure, GCP) and on-premises.

### Terraform Basics

Terraform files define infrastructure:

```hcl
# main.tf

provider "aws" {
  region = "us-east-1"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"  # Ubuntu
  instance_type = "t3.micro"
  
  tags = {
    Name = "web-server"
  }
}

resource "aws_security_group" "allow_http" {
  name = "allow_http"
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

Apply:
```bash
terraform plan    # Preview changes
terraform apply   # Deploy infrastructure
```

### Key Terraform Concepts

**Idempotency:**
Running Terraform twice = same result.

```bash
terraform apply  # Creates resources
terraform apply  # Nothing changes (already exists)
```

This is critical. If Terraform isn't idempotent, re-running it breaks things.

**State:**
Terraform tracks state (what exists).

```
state.tfstate file:
  {
    "aws_instance.web": {
      "id": "i-1234567890abcdef0",
      "instance_type": "t3.micro"
    }
  }
```

When you run terraform apply, it:
1. Compares desired state (code) to actual state (state file)
2. Deploys only changes

**Drift Detection:**
What if someone manually changes infrastructure?

```
Terraform code says: t3.micro
Actual AWS: t3.large (someone manually changed it)

terraform plan will show:
  - t3.micro → t3.large (drift detected)

Options:
  A) terraform apply to correct it (change back to t3.micro)
  B) Update code to t3.large (accept the change)
```

Always choose A (correct drift). Infrastructure should match code.

## IaC in Your CI/CD Pipeline

```
Developer commits infrastructure change
    ↓
Git webhook
    ↓
CI Pipeline:
  1. Syntax check (terraform validate)
  2. Format check (terraform fmt --check)
  3. Plan and diff (terraform plan → show changes)
  4. Security scan (checkov: find insecure configs)
    ↓
Approval required (infrastructure change is high risk)
    ↓
CD Pipeline:
  1. terraform apply (deploy infrastructure)
  2. Verify (smoke tests)
    ↓
Infrastructure deployed
Code deployed
Service runs on new infrastructure
```

## Security in IaC

IaC has security implications. Insecure infrastructure = insecure app.

### Example: Security Group Too Open

```hcl
# BAD - open to world
resource "aws_security_group" "database" {
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # World can access!
  }
}

# GOOD - only from app server
resource "aws_security_group" "database" {
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]  # Only from app
  }
}
```

### Security Scanning for IaC

Tools like Checkov scan infrastructure for issues:

```bash
checkov -f main.tf

# Output:
# Check: Ensure all S3 buckets are encrypted
#   FAILED at line 15
# Check: Ensure RDS encrypted
#   PASSED
# Check: Ensure security group doesn't allow all
#   FAILED at line 32 (cidr_blocks = ["0.0.0.0/0"])
```

## Versioning Infrastructure

Infrastructure changes must be versioned like code.

```
v1.0 (initial infrastructure)
v1.1 (added CDN)
v1.2 (increased database size)
v2.0 (migrated to Kubernetes)
```

In your Git tag, version should match code version:

```
Release v1.2.0:
  Code: myapp:v1.2.0
  Infrastructure: terraform @ tag v1.2.0
  
  Both deployed together
```

## Common Mistakes

### Mistake 1: Manual Infrastructure Changes

Wrong: "I'll manually provision the server, then apply Terraform"

Problem:
- Manual changes bypass code review
- Manual changes aren't reproducible
- Code and actual state diverge
- Disaster recovery assumes code is truth (but it's not)

Right: Every infrastructure change goes through code + review + pipeline

### Mistake 2: Not Detecting Drift

Wrong: "Terraform code says t3.micro, but someone manually changed to t3.large. We'll fix it next sprint."

Problem:
- Code and actual differ
- Terraform doesn't update (thinks nothing changed)
- Next deploy, it reverts to t3.micro (unexpected)
- Infrastructure is unreliable

Right: Daily drift detection, immediate correction

```bash
# Scheduled job
terraform plan -out=plan.out

# If plan shows drift:
#   Alert ops
#   Either accept change (update code)
#   Or reject (revert to code)
```

### Mistake 3: Untested Terraform

Wrong: "We'll apply Terraform in production for the first time"

Problem:
- First application might fail
- Syntax errors, missing variables, etc.
- Production breaks

Right: Test Terraform in staging/dev first

```
Dev environment: Deploy Terraform (test)
Staging environment: Deploy Terraform (staging)
Production: Deploy Terraform (real)

If Terraform breaks in staging, fix before production
```

### Mistake 4: No Rollback Path

Wrong: "Terraform apply created bad infrastructure, can't undo"

Problem:
- Have to manually delete resources
- Might miss something
- Expensive to fix

Right: Terraform tracks state, rollback is:
```bash
# Previous state is in version control
git checkout HEAD~1    # Revert to previous state
terraform apply        # Rolls back infrastructure
```

### Mistake 5: State File Insecurity

Wrong: State file stored in Git (contains passwords)

Problem:
- Secrets in version control
- Anyone with Git access has secrets
- Backup leaks secrets

Right: Store state in secure remote backend

```hcl
# main.tf
terraform {
  backend "s3" {
    bucket = "company-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
    encrypt = true  # Encrypted at rest
  }
}
```

State never stored in Git. Instead, stored on:
- AWS S3 (encrypted)
- Azure Storage
- Terraform Cloud (encrypted)
- Any remote backend

## Scaling Terraform

For large systems, Terraform can become unwieldy.

### Modules

Group related infrastructure into modules:

```
├── modules/
│   ├── vpc/
│   │   ├── main.tf (network definition)
│   │   ├── outputs.tf (what this module exports)
│   │   └── variables.tf (inputs)
│   ├── database/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   ├── kubernetes/
│   │   ├── main.tf
│   │   └── ...
│   └── load_balancer/
│       └── ...

├── main.tf (orchestration - uses modules)
```

main.tf:
```hcl
module "vpc" {
  source = "./modules/vpc"
  cidr   = "10.0.0.0/16"
}

module "database" {
  source       = "./modules/database"
  vpc_id       = module.vpc.id
  engine       = "postgres"
  instance_class = "db.t3.micro"
}

module "kubernetes" {
  source = "./modules/kubernetes"
  vpc_id = module.vpc.id
  node_count = 3
}
```

### Workspaces

For multiple environments:

```
dev environment:
  terraform workspace select dev
  terraform apply

staging environment:
  terraform workspace select staging
  terraform apply

prod environment:
  terraform workspace select prod
  terraform apply
```

Each workspace has separate state and variables.

## Example: Complete IaC Pipeline

```yaml
name: Infrastructure Deploy

on:
  push:
    paths:
      - 'infrastructure/**'
      - '.github/workflows/infra.yml'

jobs:
  plan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0
      
      - run: terraform -chdir=infrastructure fmt -check
      
      - run: terraform -chdir=infrastructure validate
      
      - name: Terraform Plan (Dev)
        run: |
          terraform -chdir=infrastructure plan \
            -var-file=environments/dev.tfvars \
            -out=tfplan
      
      - name: Security Scan
        run: |
          pip install checkov
          checkov -d infrastructure --framework terraform
      
      - name: Save Plan
        uses: actions/upload-artifact@v3
        with:
          name: tfplan
          path: infrastructure/tfplan

  apply:
    runs-on: ubuntu-latest
    needs: plan
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      
      - uses: hashicorp/setup-terraform@v2
      
      - name: Download Plan
        uses: actions/download-artifact@v3
        with:
          name: tfplan
      
      - name: Approval Gate
        run: |
          echo "Manual approval required"
          # In real pipeline, require manual approval
          exit 0
      
      - name: Apply (Dev)
        run: |
          terraform -chdir=infrastructure apply \
            -var-file=environments/dev.tfvars \
            tfplan
      
      - name: Verify
        run: |
          # Smoke tests
          ./scripts/verify-infra.sh dev
```

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. What does idempotency mean in Terraform?
   - a) Terraform can only be run once
   - b) Running Terraform twice produces the same result
   - c) Terraform automatically fixes drift
   - d) Terraform requires approval each run

2. Terraform code says t3.micro, AWS has t3.large. What's this called?
   - a) State mismatch
   - b) Drift
   - c) Configuration error
   - d) Desync

3. Why should infrastructure state NOT be stored in Git?
   - a) State file contains secrets
   - b) State file is too large
   - c) Version control conflicts
   - d) Both a and c

4. What's the advantage of IaC in CI/CD?
   - a) Infrastructure changes are code reviewed
   - b) Infrastructure changes are versioned
   - c) Infrastructure deployment is automated
   - d) All of the above

5. When should Terraform run in your pipeline?
   - a) Before code deployment
   - b) After code deployment
   - c) In parallel with code deployment
   - d) Only during emergencies

### Pipeline Design Tasks

**Task 1: Design IaC Pipeline**
You're deploying infrastructure for three environments:
- Dev (small: 1 server)
- Staging (medium: 3 servers)
- Prod (large: 10 servers, multi-region)

Design CI/CD for infrastructure:
1. When does Terraform run?
2. How do you test infrastructure changes?
3. What approvals are needed?
4. How do you prevent production disasters?

**Task 2: Terraform Module Design**
You need to create reusable infrastructure:
- Kubernetes cluster (EKS)
- Database (RDS)
- Load balancer

Create module structure:
1. How many modules?
2. What inputs does each module need?
3. What outputs does each module provide?
4. How do modules connect?

### Failure Scenario

**Scenario: The Terraform Drift**

Your infrastructure code specifies:
```
database = "db.t3.micro"
```

Someone manually scales database to "db.r5.large" to handle spike.

Three months later, you run terraform plan. Drift is detected.

New engineer doesn't understand the change. Runs terraform apply.

Database is reverted to t3.micro.

Real users are accessing database → crashes.

Incident.

Questions:
1. Why didn't Terraform prevent this?
2. How should drift be handled?
3. What process ensures code reflects reality?
4. How do you recover from this?
5. What guardrails would prevent the revert?

---

Next: [Module 08: Pipeline Observability](08-pipeline-observability.md)
