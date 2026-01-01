# AWS Essentials: Start Here

Welcome. This guide orients you to the curriculum and helps you get started.

## What This Curriculum Is

This is an engineering-grade AWS tutorial for building and operating production cloud systems. It's not a certification guide, marketing overview, or shallow introduction. Every concept has been selected because it matters in real deployments.

## What This Curriculum Is NOT

- A certification prep course (though it covers those topics)
- A step-by-step console walkthrough
- Marketing material for AWS services
- A quick reference guide (though INDEX.md works as one)

## If You're New to AWS

You're in the right place. This curriculum assumes no prior AWS experience, but it does assume:
- Basic Linux/Unix command line comfort
- Understanding of networking concepts (IP, DNS, ports, HTTP/HTTPS)
- Experience building backend applications
- Willingness to get hands-on in a real AWS account

If you're missing any of these prerequisites, spend 2-3 hours learning them first. They matter more than AWS-specific knowledge.

## If You Have AWS Experience

You might still benefit from this curriculum because it focuses on:
- Architecture patterns (not console clicks)
- Why services are used together (not what they do individually)
- Production operational concerns (not marketing features)
- Integration with CI/CD, containers, and infrastructure-as-code

Skip Module 1 if you're comfortable with regions, availability zones, and shared responsibility. Start with Module 2.

## Your First Steps

### Step 1: Set Up AWS Account (30 minutes)
1. Create an AWS account: https://aws.amazon.com/
2. Enable billing alerts: AWS Billing Console → Billing Preferences
3. Create an IAM user for yourself (don't use root account)
4. Install AWS CLI v2: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
5. Configure CLI: `aws configure` (use your IAM user credentials)

Test your setup:
```bash
aws sts get-caller-identity
```

You should see your user information. If not, fix your credentials before proceeding.

### Step 2: Understand Your Learning Path (10 minutes)

The curriculum is sequential, building concepts progressively. Read [INDEX.md](INDEX.md) and choose your path:
- **Backend engineers**: Focus on compute, databases, CI/CD
- **DevOps engineers**: Focus on networking, CI/CD, monitoring, security
- **Platform engineers**: Focus on everything, especially advanced services

### Step 3: Commit to the Cloud Mental Model (5 minutes)

Every lesson fits this model. Internalize it:

```
User/Client
    ↓
DNS / Route 53
    ↓
Load Balancer (ELB/ALB/NLB)
    ↓
Compute (EC2 / ECS / EKS / Lambda)
    ↓
Databases (RDS / DynamoDB / ElastiCache)
    ↓
Storage (S3 / EFS)
    ↓
Monitoring / Security (CloudWatch, IAM, CloudTrail)
```

When learning a new service, ask: "Where does this fit in the mental model?" If you can't answer, reread the module.

### Step 4: Read Module 1 (2-3 hours)

[docs/01-aws-fundamentals.md](docs/01-aws-fundamentals.md)

This module covers:
- What cloud computing actually is
- AWS regions and availability zones
- The shared responsibility model (critical for security)
- Basic networking in AWS
- Cost model

You don't need to memorize region names, but you need to understand why regions and AZs matter for production deployments.

### Step 5: Complete Module 1 Labs (2 hours)

After reading Module 1, complete the two hands-on labs in the lab section. These use your real AWS account (within free tier). Labs are mandatory—reading alone doesn't build operational skill.

### Step 6: Answer Assessment Questions (20 minutes)

After labs, answer the 5 MCQ questions at the end of Module 1. You should score 80%+ before moving on.

Read the answers and explanations carefully. If you don't understand why an answer is correct, reread that section.

## Time Commitment

- **Complete curriculum**: 25-35 hours over 2-4 weeks
- **Per module**: 3-5 hours (reading + labs + assessment)
- **Final project**: 8-12 hours

Schedule accordingly. Rushing through labs teaches nothing. Better to spend 4 hours on one hands-on exercise than to quickly skim 10 modules.

## Lab Environment Notes

### Cost Management
- All labs stay within AWS free tier (< $1/month total)
- Delete resources immediately after labs to avoid charges
- Each lab includes cleanup instructions
- Enable billing alerts in AWS console

### Linux Environment
- All labs assume Linux/macOS terminal
- If you're on Windows, use WSL2 or use AWS CloudShell
- Labs use bash scripts and standard Unix tools

### AWS CLI Usage
- All labs include AWS CLI commands (not console clicks)
- Learn the CLI—it's how real operations happen
- Terraform examples are optional but recommended

## Common Mistakes to Avoid

1. **Skipping prerequisites**: Don't proceed if you don't understand the cloud model
2. **Skipping labs**: Theory doesn't translate to production skill
3. **Ignoring costs**: Always delete test resources immediately
4. **Using root credentials**: Create an IAM user and never use root
5. **Not reading error messages**: AWS errors are detailed; read them fully

## FAQ

**Q: I've used AWS before. Do I really need to read this?**
A: Probably. This curriculum focuses on architecture and production patterns, not console walkthroughs. You might skip Module 1, but Module 2 onwards offers depth most engineers miss.

**Q: Can I skip modules?**
A: Not recommended. Each module builds on previous ones. Module 6 (CI/CD) requires understanding from Modules 1-5.

**Q: How long should I spend on each module?**
A: Don't rush. 3-5 hours per module including labs. A one-hour skim teaches nothing.

**Q: What if I fail a lab?**
A: That's fine. Troubleshoot it. Read error messages. Check AWS documentation. This is how you learn operational troubleshooting.

**Q: Can I use Terraform instead of AWS CLI?**
A: Yes. Examples are provided for both. Terraform is recommended for reproducible infrastructure.

**Q: What about certification exams?**
A: This curriculum covers SAA-C02 and SAA-C03 material, but not as a focus. If you need certification prep, use this tutorial plus official AWS training.

## Getting Help

1. **Stuck on a concept?** Reread the section. Read AWS documentation for the service.
2. **Lab not working?** Check error messages. Search AWS documentation. Try simplifying your setup.
3. **Confused about design?** Look at production incident scenarios—they illustrate why designs matter.
4. **Cost worried?** Use AWS Cost Explorer to see exactly what's costing money. Delete resources immediately.

## Next Steps

Ready to begin?

1. Complete AWS account setup (Step 1 above)
2. Test your AWS CLI: `aws sts get-caller-identity`
3. Open [docs/01-aws-fundamentals.md](docs/01-aws-fundamentals.md)
4. Read carefully. Take notes. This is your foundation.

---

**You're ready. Let's begin.**

Next: [Module 1: AWS Fundamentals](docs/01-aws-fundamentals.md)
