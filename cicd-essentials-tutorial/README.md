# CI/CD Essentials Tutorial

A production-oriented, systems-level curriculum for backend engineers, DevOps engineers, and platform architects preparing for production deployments.

## What This Is

This is NOT a tool walkthrough. This is a comprehensive engineering curriculum that treats CI/CD as a system, not a collection of YAML files.

Every module explains architecture first, tools second. Every concept includes real production use cases and secure, correct examples.

## Target Audience

- Backend engineers
- DevOps engineers
- Platform engineers
- Engineers preparing for production deployments

## Core Philosophy

1. CI/CD is a SYSTEM, not a YAML file
2. Pipelines are architecture first, tools second
3. Linux-based examples only
4. CI and CD are separate but connected concerns
5. Every concept includes explanation, use case, and examples
6. Git-based workflows throughout
7. No vendor lock-in thinking
8. Security and reliability are mandatory topics

## Pipeline Mental Model

All examples follow this realistic flow:

```
Developer
    ↓
Git Repository
    ↓
CI (build, test, scan)
    ↓
Artifact Registry
    ↓
CD (deploy)
    ↓
Production
```

## Curriculum

1. [CI/CD Fundamentals](docs/01-cicd-fundamentals.md) - What CI/CD solves, failure costs, core concepts
2. [Source Control & Triggers](docs/02-source-control-triggers.md) - Git workflows, webhooks, branch protection
3. [CI Pipeline Design](docs/03-ci-pipeline-design.md) - Build stages, test layers, parallelization
4. [Artifact Management](docs/04-artifact-management.md) - Artifacts, versioning, Docker images, registries
5. [Security in CI/CD](docs/05-security-in-cicd.md) - Secrets, scanning, SAST/DAST, supply chain risks
6. [Continuous Deployment](docs/06-continuous-deployment.md) - Blue/green, canary, rollbacks, promotions
7. [Infrastructure as Code](docs/07-infrastructure-as-code.md) - Terraform, idempotency, drift detection
8. [Pipeline Observability](docs/08-pipeline-observability.md) - Logs, metrics, alerting, audit trails
9. [CI/CD Tools Comparison](docs/09-cicd-tools-comparison.md) - GitHub Actions, GitLab CI, Jenkins, trade-offs
10. [Failure & Recovery](docs/10-failure-recovery.md) - Broken pipelines, rollbacks, disaster recovery

## Final Project

[Complete Production CI/CD System](docs/final-project.md) - Build a production-grade system covering:
- Backend application builds
- Test and security scanning
- Docker image building
- Artifact management
- Safe deployments
- Rollback capability

## How to Use This Tutorial

1. **Sequential learning**: Follow modules 1-10 in order. Each builds on previous concepts.
2. **Practice questions**: Each module includes 5 MCQ questions (without answers—test yourself first).
3. **Pipeline design tasks**: Each module has 2 practical design challenges.
4. **Failure scenarios**: Each module includes 1 real-world failure case to analyze.
5. **Capstone project**: Complete the final project to integrate all concepts.

## Key Assumptions

- You have Linux/Unix environment access
- You understand basic Git workflows
- You have Docker familiarity
- You can read YAML and shell scripts
- No prior CI/CD platform experience required (will be taught platform-agnostically)

## Time Commitment

- Modules 1-10: ~4-6 weeks (self-paced)
- Final project: 1-2 weeks
- Total: 5-8 weeks for comprehensive mastery

## What You'll Master

By completing this curriculum, you will understand:

- How CI/CD prevents production disasters
- How to design pipelines for speed AND safety
- How to manage artifacts and versions securely
- How to deploy without downtime
- How to observe and debug pipeline failures
- How to choose the right CI/CD tool
- How to recover from deployment disasters

## No Prerequisites

This curriculum assumes:
- NO prior CI/CD experience
- NO specific tool knowledge
- Basic Git understanding is helpful but not required
- Linux terminal comfort

## Notes on Examples

- All examples use Linux/Unix syntax
- Tool-specific examples are platform-agnostic (GitHub Actions, GitLab CI, Jenkins shown equally)
- Docker is used for artifact examples, not required knowledge
- YAML snippets are minimal and illustrative, not production copy-paste

---

Start with [Module 01: CI/CD Fundamentals](docs/01-cicd-fundamentals.md)
