# AWS Essentials: Index & Quick Navigation

## Quick Start
- New to AWS? Start here: [START_HERE.md](START_HERE.md)
- Want an overview? Read: [README.md](README.md)

## Complete Module List

### Module 1: AWS Fundamentals
[docs/01-aws-fundamentals.md](docs/01-aws-fundamentals.md)

Topics covered:
- Cloud computing models: IaaS, PaaS, SaaS
- AWS Regions and Availability Zones
- Shared responsibility model
- AWS service categories
- Networking fundamentals in AWS
- Cost model and billing

Duration: 2-3 hours reading + 2 hours labs

### Module 2: Identity & Access Management (IAM)
[docs/02-identity-access-management.md](docs/02-identity-access-management.md)

Topics covered:
- IAM users, groups, and roles
- Policies and permission boundaries
- Least privilege principle
- Cross-account access patterns
- MFA and credential management
- Best practices for secure access

Duration: 2-3 hours reading + 3 hours labs

### Module 3: Compute Services
[docs/03-compute-services.md](docs/03-compute-services.md)

Topics covered:
- EC2 instances and lifecycle management
- Launch templates and autoscaling
- Container services: ECS vs EKS
- Lambda serverless computing
- Spot instances and cost optimization
- Production scaling strategies

Duration: 3-4 hours reading + 4 hours labs

### Module 4: Storage & Databases
[docs/04-storage-databases.md](docs/04-storage-databases.md)

Topics covered:
- S3 buckets, versioning, and lifecycle policies
- EFS and FSx for file storage
- RDS and Aurora relational databases
- DynamoDB NoSQL database
- ElastiCache for caching
- Backup and disaster recovery

Duration: 3-4 hours reading + 4 hours labs

### Module 5: Networking & Content Delivery
[docs/05-networking-content-delivery.md](docs/05-networking-content-delivery.md)

Topics covered:
- VPC design and subnets
- Routing and route tables
- Security groups and NACLs
- ELB types: ALB, NLB, Classic Load Balancer
- Route 53 DNS and traffic management
- CloudFront CDN and caching

Duration: 3-4 hours reading + 3 hours labs

### Module 6: CI/CD & DevOps Integration
[docs/06-cicd-devops-integration.md](docs/06-cicd-devops-integration.md)

Topics covered:
- AWS CodePipeline overview
- CodeBuild for compilation and testing
- CodeDeploy for application deployment
- Docker container integration
- Kubernetes with EKS
- Infrastructure as Code: CloudFormation and Terraform
- Multi-environment deployment patterns

Duration: 3-4 hours reading + 4 hours labs

### Module 7: Monitoring & Observability
[docs/07-monitoring-observability.md](docs/07-monitoring-observability.md)

Topics covered:
- CloudWatch metrics and dashboards
- CloudWatch logs and log groups
- CloudTrail audit trails
- Alarms and notifications
- Distributed tracing concepts
- Centralized logging patterns
- Alerting best practices

Duration: 2-3 hours reading + 3 hours labs

### Module 8: Security & Compliance
[docs/08-security-compliance.md](docs/08-security-compliance.md)

Topics covered:
- KMS key management
- Secrets Manager and Parameter Store
- VPC endpoints and PrivateLink
- GuardDuty threat detection
- Security Hub compliance
- Network security best practices
- Data protection strategies

Duration: 2-3 hours reading + 3 hours labs

### Module 9: Cost Management & Optimization
[docs/09-cost-management.md](docs/09-cost-management.md)

Topics covered:
- AWS billing and cost analysis
- Cost Explorer and budgeting
- Right-sizing recommendations
- Spot Instances and Reserved Instances
- Savings Plans
- Identifying unused resources
- Cost optimization strategies

Duration: 2 hours reading + 2 hours labs

### Module 10: Advanced Services Overview
[docs/10-advanced-services.md](docs/10-advanced-services.md)

Topics covered:
- Event-driven architecture: SNS, SQS, EventBridge
- Lambda serverless functions in depth
- API Gateway for REST and WebSocket APIs
- AWS Fargate for container workloads
- EKS integration with CI/CD
- Step Functions for workflow orchestration

Duration: 2-3 hours reading + 2 hours labs

## Final Project

[final-project.md](final-project.md)

A comprehensive, production-ready backend system deployment including:
- Multi-region DNS and routing
- Auto-scaling load-balanced compute
- RDS and DynamoDB backends
- S3 storage and CDN
- CI/CD integration
- Comprehensive logging, monitoring, security
- Disaster recovery and failover

Estimated duration: 8-12 hours

## Supporting Materials

### Examples & Reference Implementations
[examples/REFERENCE_IMPLEMENTATIONS.md](examples/REFERENCE_IMPLEMENTATIONS.md)
- Terraform templates for each module
- CloudFormation examples
- AWS CLI command reference
- Python and Node.js integration examples

### Lab Files & Scripts
(Lab files are located in the `labs/` directory of the source repository)
- Lab setup scripts
- Lab cleanup procedures
- Test scripts for validation
- Sample code for hands-on work

## Recommended Learning Path

### For Backend Engineers
1. Start: AWS Fundamentals (understand regions, costs, model)
2. Core: IAM → Compute → Networking
3. Data: Storage & Databases
4. Practice: Module 6 (CI/CD) with your framework
5. Operations: Monitoring & Observability
6. Final: Security & Cost Management
7. Capstone: Final Project

### For DevOps Engineers
1. Start: AWS Fundamentals
2. Core: IAM → Networking → Compute
3. Operations: Monitoring → Security
4. Deep Dive: CI/CD & DevOps (Module 6)
5. Advanced: Advanced Services
6. Practice: Final Project with multi-environment setup

### For Platform Engineers
1. Start: AWS Fundamentals
2. Core: IAM → Networking → Compute → Storage
3. Focus: CI/CD, Infrastructure as Code
4. Advanced: Services (Lambda, EventBridge)
5. Deep Dive: All monitoring, security, cost modules
6. Capstone: Final Project with full automation

## Time Estimates

- Complete tutorial: 25-35 hours
- Reading only: 20-25 hours
- Labs only: 25-30 hours
- Final project: 8-12 hours

## Knowledge Check

You're ready to move to the next module when you can:
- Explain the concepts in your own words
- Complete both hands-on labs successfully
- Answer the MCQ questions
- Articulate how to handle the incident scenario

## Assessment Criteria

Each module provides:
- 5 multiple-choice questions (answers provided with explanations)
- 2 hands-on cloud tasks with success criteria
- 1 production incident scenario with recommended response

You should score 80%+ on MCQs before moving to the next module. Labs must be fully functional.

## Additional Resources

Throughout this curriculum, you'll find:
- Links to official AWS documentation
- References to relevant Linux/networking concepts
- Best practice guides from AWS
- Real-world incident case studies

---

**Start your journey:** [START_HERE.md](START_HERE.md)

**Jump to a module:** See list above

**Questions?** Each module includes common mistakes and production notes addressing typical confusion.
