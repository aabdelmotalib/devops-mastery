# Module 6: CI/CD & DevOps Integration

Deploying applications manually is error-prone, slow, and doesn't scale. CI/CD pipelines automate testing, building, and deploying. This module covers AWS's CI/CD services and how to integrate them with your infrastructure.

## 6.1 AWS CodePipeline

CodePipeline orchestrates your deployment workflow. It connects source code, builds, tests, and deployments.

```
Source (GitHub)
    ↓ (on commit)
Build (CodeBuild - compile, test)
    ↓ (on success)
Deploy (CodeDeploy, CloudFormation, Elastic Beanstalk)
    ↓ (on success)
Production
```

### Creating a Pipeline

```bash
# Create service role
aws iam create-role --role-name codepipeline-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "codepipeline.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policies for CodeBuild, CodeDeploy, S3, etc.
aws iam attach-role-policy --role-name codepipeline-role \
  --policy-arn arn:aws:iam::aws:policy/AWSCodePipelineFullAccess

# Create pipeline
aws codepipeline create-pipeline --cli-input-json '{
  "pipeline": {
    "name": "my-app-pipeline",
    "roleArn": "arn:aws:iam::123456789012:role/codepipeline-role",
    "artifactStore": {
      "type": "S3",
      "location": "my-pipeline-artifacts"
    },
    "stages": [
      {
        "name": "Source",
        "actions": [{
          "name": "SourceAction",
          "actionTypeId": {
            "category": "Source",
            "owner": "ThirdParty",
            "provider": "GitHub",
            "version": "1"
          },
          "configuration": {
            "Owner": "mycompany",
            "Repo": "my-app",
            "Branch": "main"
          },
          "outputArtifacts": [{"name": "SourceOutput"}]
        }]
      },
      {
        "name": "Build",
        "actions": [{
          "name": "BuildAction",
          "actionTypeId": {
            "category": "Build",
            "owner": "AWS",
            "provider": "CodeBuild",
            "version": "1"
          },
          "configuration": {
            "ProjectName": "my-app-build"
          },
          "inputArtifacts": [{"name": "SourceOutput"}],
          "outputArtifacts": [{"name": "BuildOutput"}]
        }]
      },
      {
        "name": "Deploy",
        "actions": [{
          "name": "DeployAction",
          "actionTypeId": {
            "category": "Deploy",
            "owner": "AWS",
            "provider": "CodeDeploy",
            "version": "1"
          },
          "configuration": {
            "ApplicationName": "my-app",
            "DeploymentGroupName": "production"
          },
          "inputArtifacts": [{"name": "BuildOutput"}]
        }]
      }
    ]
  }
}'
```

## 6.2 AWS CodeBuild

CodeBuild compiles code, runs tests, and produces artifacts. Fully managed (no servers to provision).

### Buildspec

Define build instructions in buildspec.yml:

```yaml
version: 0.2

phases:
  pre_build:
    commands:
      - echo "Running tests..."
      - pip install -r requirements.txt
      
  build:
    commands:
      - echo "Building application..."
      - pytest tests/
      - python -m py_compile app.py
      
  post_build:
    commands:
      - echo "Build completed"
      - docker build -t my-app:$CODEBUILD_BUILD_NUMBER .
      - docker tag my-app:$CODEBUILD_BUILD_NUMBER 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:$CODEBUILD_BUILD_NUMBER
      - docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:$CODEBUILD_BUILD_NUMBER

artifacts:
  files:
    - appspec.yaml
    - app.py
  name: BuildArtifact
```

### CodeBuild Project

```bash
# Create build project
aws codebuild create-project --name my-app-build \
  --source type=GITHUB,location=https://github.com/mycompany/my-app.git \
  --artifacts type=S3,location=my-pipeline-artifacts \
  --environment type=LINUX_CONTAINER,image=aws/codebuild/standard:4.0,computeType=BUILD_GENERAL1_MEDIUM \
  --service-role arn:aws:iam::123456789012:role/codebuild-role
```

Build automatically runs when CodePipeline triggers it.

## 6.3 AWS CodeDeploy

CodeDeploy deploys artifacts to EC2 instances. Supports rolling deployments, canary deployments, all-at-once.

### Appspec Configuration

appspec.yaml defines deployment:

```yaml
version: 0.0
os: linux

files:
  source: /
  destination: /var/www/myapp

permissions:
  - object: /var/www/myapp
    owner: www-data
    group: www-data
    mode: 755
    type:
      - directory

hooks:
  BeforeInstall:
    - location: scripts/stop_server.sh
      timeout: 300
  ApplicationStart:
    - location: scripts/start_server.sh
      timeout: 300
  ApplicationStop:
    - location: scripts/stop_server.sh
      timeout: 300
  ValidateService:
    - location: scripts/validate.sh
      timeout: 300
```

### Deployment Group

```bash
# Create deployment group (with rolling deployment)
aws deploy create-deployment-group \
  --application-name my-app \
  --deployment-group-name production \
  --deployment-config-name CodeDeployDefault.OneAtATime \
  --ec2-tag-filters Key=Environment,Value=production \
  --service-role-arn arn:aws:iam::123456789012:role/codedeploy-role
```

## 6.4 Infrastructure as Code: CloudFormation

CloudFormation defines infrastructure in JSON/YAML. Makes infrastructure reproducible and version-controlled.

### CloudFormation Template

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: 'Web application stack'

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true

  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      AvailabilityZone: us-east-1a

  InternetGateway:
    Type: AWS::EC2::InternetGateway

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  EC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: ami-0c55b159cbfafe1f0
      InstanceType: t3.micro
      SubnetId: !Ref PublicSubnet
      Tags:
        - Key: Name
          Value: web-server

  RDSDatabase:
    Type: AWS::RDS::DBInstance
    Properties:
      AllocatedStorage: 20
      DBInstanceClass: db.t3.micro
      Engine: postgres
      MasterUsername: admin
      MasterUserPassword: !Sub '{{resolve:secretsmanager:db-password:SecretString:password}}'

Outputs:
  InstanceId:
    Description: EC2 Instance ID
    Value: !Ref EC2Instance
  
  DatabaseEndpoint:
    Description: RDS Database Endpoint
    Value: !GetAtt RDSDatabase.Endpoint.Address
```

Create stack:
```bash
aws cloudformation create-stack --stack-name my-app \
  --template-body file://template.yaml
```

CloudFormation advantages:
- Infrastructure version-controlled in Git
- Reproducible deployments
- Rollback to previous version
- Templated for multiple environments

## 6.5 Terraform (Alternative to CloudFormation)

Terraform is a multi-cloud IaC tool (works with AWS, Azure, GCP, etc.).

### Terraform Configuration

```hcl
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
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "public-subnet"
  }
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "web-server"
  }
}

resource "aws_db_instance" "postgres" {
  allocated_storage    = 20
  engine               = "postgres"
  engine_version       = "14.7"
  instance_class       = "db.t3.micro"
  username             = "admin"
  password             = var.db_password
  skip_final_snapshot  = true

  tags = {
    Name = "main-db"
  }
}

output "instance_id" {
  value = aws_instance.web.id
}

output "db_endpoint" {
  value = aws_db_instance.postgres.endpoint
}
```

Deploy:
```bash
terraform init
terraform plan      # See what will be created
terraform apply     # Create resources
terraform destroy   # Delete all resources
```

### CloudFormation vs. Terraform

| Aspect | CloudFormation | Terraform |
|--------|---|---|
| Multi-cloud | AWS only | AWS, Azure, GCP, others |
| Learning | AWS-specific | Cloud-agnostic |
| Integration | Deep AWS integration | Community-driven |
| State | CloudFormation manages | Terraform state file |
| Adoption | AWS default | Growing industry standard |

Choose CloudFormation if AWS-only. Choose Terraform for multi-cloud.

## 6.6 Complete Pipeline Example

Production-grade pipeline:

```
GitHub (commit to main)
    ↓
CodePipeline triggers
    ↓
CodeBuild (run tests)
    ├─ Unit tests
    ├─ Integration tests
    ├─ Build Docker image
    ├─ Push to ECR (Elastic Container Registry)
    └─ Produce buildspec artifacts
    ↓
CodeDeploy (deploy to staging)
    ├─ Rolling deployment
    └─ Validate (health checks)
    ↓
Manual approval stage (review staging)
    ↓
CodeDeploy (deploy to production)
    ├─ Rolling deployment (5% at a time)
    └─ Automatic rollback if health checks fail
    ↓
CloudWatch (monitor deployment)
    ├─ Errors spike → Automatic rollback
    └─ Success → Pipeline complete
```

## 6.7 Common Mistakes

**Mistake 1: Deploying without tests**
If tests don't run in CodeBuild, bugs reach production. Always run tests before building.

**Mistake 2: Not automating rollbacks**
Deployments fail. Have automatic rollback, not manual "let me fix it" scramble.

**Mistake 3: Deploying all instances simultaneously**
All-at-once deployment = total downtime if something goes wrong. Use rolling deployments.

**Mistake 4: Infrastructure not in version control**
Manually clicking CloudFormation/Terraform is error-prone. Define infrastructure in code, store in Git.

**Mistake 5: Not testing infrastructure changes**
Test infrastructure in a dev environment before deploying to production.

## Assessment

### Practice Questions

**Q1: CodeBuild fails during build stage. What happens?**
A) Pipeline continues to deploy
B) Pipeline stops, doesn't deploy
C) Manual approval required
D) Automatic rollback

**Q2: You want to deploy to 10% of instances first, monitor, then 100%. Deployment type?**
A) All-at-once
B) Rolling
C) Canary
D) Blue-green

**Q3: CloudFormation stack creation fails. What happens to resources?**
A) Partial resources remain (partial stack)
B) All resources deleted (rollback)
C) Manual cleanup required
D) Resources remain, manual deletion

**Q4: Terraform state file is lost. What happens?**
A) Terraform has no record of resources
B) Resources deleted automatically
C) Manual state recovery required
D) No impact; Terraform queries AWS

**Q5: CodePipeline needs S3 permissions. Configured where?**
A) CodePipeline service role
B) S3 bucket policy
C) IAM user policy
D) EC2 instance role

### Hands-On Labs

**Lab 1: Create CodePipeline**

Set up pipeline with GitHub source, CodeBuild build, CodeDeploy deploy.

**Lab 2: Deploy with CloudFormation**

Create CloudFormation template, deploy stack, update and re-deploy.

### Production Incident Scenario

**Scenario: Bad Deployment Causes Outage**

New feature deployed via CodePipeline. 1 second later, errors spike 500%. Users affected.

Problem: Tests didn't catch the issue (insufficient test coverage). No automatic rollback configured.

Recovery:
1. Manual trigger rollback in CodeDeploy
2. Revert to previous deployment
3. Deploy with fixed code

Time to recovery: 15 minutes (manual process)

Prevention:
- Improve test coverage (unit + integration)
- Configure automatic CloudWatch-based rollback
- Use canary deployment (5% of instances first)
- Monitor error rates for 5 minutes before full deployment

---

Next Module: [Module 7: Monitoring & Observability](07-monitoring-observability.md)
