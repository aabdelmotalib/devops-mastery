# CI/CD Essentials Tutorial - Complete Index

## Welcome

This is a **production-oriented, systems-level CI/CD curriculum** for backend engineers, DevOps engineers, and platform architects preparing for production deployments.

This is NOT a tool walkthrough. This is a comprehensive engineering course that teaches CI/CD as a system, not a collection of YAML files.

## Quick Start

**New to CI/CD?** Start here: [README.md](README.md)

**Want to jump in?** Go to: [Module 01: CI/CD Fundamentals](docs/01-cicd-fundamentals.md)

**Short on time?** Read: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Ready to build?** Jump to: [Final Project](docs/final-project.md)

## The Curriculum (10 Modules + Capstone)

### Part 1: Foundations
1. [CI/CD Fundamentals](docs/01-cicd-fundamentals.md)
   - What CI/CD solves
   - Pipeline failure costs
   - Core concepts

2. [Source Control & Triggers](docs/02-source-control-triggers.md)
   - Git workflows
   - Webhooks and triggers
   - Branch protection

3. [CI Pipeline Design](docs/03-ci-pipeline-design.md)
   - Build stages
   - Test layers
   - Parallelization

### Part 2: Artifacts & Security
4. [Artifact Management](docs/04-artifact-management.md)
   - What is an artifact
   - Versioning strategies
   - Docker images
   - Registries

5. [Security in CI/CD](docs/05-security-in-cicd.md)
   - Secrets management
   - Scanning (SAST, DAST)
   - Supply chain security

### Part 3: Deployment & Operations
6. [Continuous Deployment](docs/06-continuous-deployment.md)
   - Deployment strategies
   - Blue-green, canary, rolling
   - Rollbacks

7. [Infrastructure as Code](docs/07-infrastructure-as-code.md)
   - Terraform concepts
   - Idempotency
   - Drift detection

### Part 4: Operations & Tools
8. [Pipeline Observability](docs/08-pipeline-observability.md)
   - Logs, metrics, traces
   - Audit trails
   - Alerting

9. [CI/CD Tools Comparison](docs/09-cicd-tools-comparison.md)
   - GitHub Actions vs Jenkins vs GitLab CI
   - Tool selection
   - Migration strategies

10. [Failure & Recovery](docs/10-failure-recovery.md)
    - Failure types
    - Detection and response
    - Disaster recovery

### Capstone
[Final Project: Production CI/CD System](docs/final-project.md)
- Build complete, production-grade system
- Containerize application
- Create CI/CD pipelines
- Infrastructure as code
- Deploy safely

## By Topic

### For Beginners
Start with modules in order: 1 → 2 → 3 → 4 → 5...

### For Operations Teams
Focus on: 2, 6, 7, 8, 10 (source control, deployment, infra, observability, recovery)

### For Security Teams
Focus on: 5, 8 (security, observability)

### For Platform Engineers
Focus on: 6, 7, 8, 9 (deployment, IaC, observability, tools)

### For DevOps Engineers
Focus on: All, especially 7, 8, 9, 10 (IaC, observability, tools, failure recovery)

## Key Concepts Reference

### Pipelines
- **CI Pipeline**: Compile → Test → Lint → Scan
- **CD Pipeline**: Deploy staging → Approval → Deploy production
- **Fail-fast**: Check cheapest tests first

### Deployment Strategies
- **Blue-Green**: Two environments, instant switch
- **Canary**: Gradual rollout (10% → 50% → 100%)
- **Rolling**: Replace instances one at a time

### Tools (Examples)
- **CI/CD**: GitHub Actions, Jenkins, GitLab CI, CircleCI
- **Infrastructure**: Terraform, CloudFormation, Ansible
- **Monitoring**: Prometheus, Datadog, CloudWatch
- **Secrets**: AWS Secrets Manager, Vault, Azure Key Vault

### Key Metrics
- Pipeline duration (target: <5 min)
- Test coverage (target: >80%)
- Deployment frequency (higher is better)
- MTTR (mean time to recovery, target: <15 min)

## Practice Exercises

### Per Module
Each module includes:
- 5 multiple-choice questions (no answers—test yourself)
- 2 pipeline design tasks
- 1 real-world failure scenario

### Final Project
Build a complete CI/CD system for a real Flask application:
- Containerize with Docker
- Create CI pipeline (test, lint, scan)
- Create CD pipeline (staging, production)
- Infrastructure as code (Terraform)
- Monitoring and rollback
- Security throughout

## Reference Materials

- [Quick Reference Guide](QUICK_REFERENCE.md) - One-page overview
- [Example Implementations](examples/REFERENCE_IMPLEMENTATIONS.md) - Real code samples
- [README](README.md) - Getting started guide

## How to Use This Tutorial

### Option 1: Self-Paced Learning
1. Read modules sequentially
2. Understand concepts before moving forward
3. Answer practice questions honestly
4. Complete final project

### Option 2: Team Learning
1. Assign module per week
2. Team discusses concepts
3. Review practice questions together
4. Build system as a team project

### Option 3: Just the Project
If you have CI/CD experience:
1. Skim modules 1-3 (basics)
2. Read modules 4-10 (focus areas)
3. Jump to final project

## Learning Outcomes

After completing this curriculum, you will be able to:

**Understand CI/CD as a System**
- Explain what CI/CD solves (not just how tools work)
- Design pipelines for safety and speed
- Choose appropriate tools
- Implement complete systems

**Build Production Pipelines**
- Create CI pipelines that test thoroughly
- Implement CD pipelines that deploy safely
- Version and manage artifacts
- Automate infrastructure

**Operate Safely**
- Deploy without downtime
- Detect and respond to failures
- Rollback automatically
- Monitor effectively

**Make Engineering Decisions**
- Choose deployment strategies
- Select appropriate tools
- Design for observability
- Prioritize security

## Questions You'll Answer

By completing this curriculum, you'll be able to confidently answer:

1. Why does my company need CI/CD? (Cost savings, speed, reliability)
2. How do I build a pipeline that doesn't break? (Testing strategy)
3. How do I deploy without downtime? (Deployment strategies)
4. What do I do if deployment fails? (Rollback, incident response)
5. How do I know my system is working? (Observability)
6. Which tool should we use? (Requirements analysis)
7. How do I secure my pipeline? (Multiple layers)
8. How do I scale this to 100 engineers? (Architecture)

## Success Criteria

You've mastered CI/CD when:

- [ ] You can explain CI/CD to a non-technical person
- [ ] You can design a pipeline from scratch
- [ ] You understand why each stage exists
- [ ] You can troubleshoot pipeline failures
- [ ] You know when to rollback vs. hotfix
- [ ] You think about observability from the start
- [ ] You choose tools based on requirements
- [ ] You prioritize safety over speed
- [ ] You can conduct a post-mortem
- [ ] You can mentor others on CI/CD

## Important Notes

### This Tutorial Assumes

- You understand Git basics
- You can read YAML
- You have Linux/Unix access
- You can read shell scripts
- No prior CI/CD experience required

### This Tutorial Does NOT Cover

- Specific tool deep-dives (focus on concepts)
- Kubernetes (orchestration is separate)
- Cloud provider details (Azure, AWS, GCP equally valid)
- Advanced observability (distributed tracing, APM, etc.)
- Performance optimization (for specific systems)

### Philosophy

> "The best CI/CD system is one that prevents problems from reaching users and helps you fix mistakes quickly. It's not about the fanciest tools. It's about reliable automation."

---

## Start Learning

**New?** → [Module 01: CI/CD Fundamentals](docs/01-cicd-fundamentals.md)

**Have questions?** → [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

**Ready to build?** → [Final Project](docs/final-project.md)

**Want examples?** → [examples/REFERENCE_IMPLEMENTATIONS.md](examples/REFERENCE_IMPLEMENTATIONS.md)

---

Last Updated: December 2024
Course Version: 1.0
Estimated Learning Time: 5-8 weeks (self-paced)
