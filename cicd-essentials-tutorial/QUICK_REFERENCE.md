# CI/CD Essentials: Quick Reference Guide

## Core Concepts at a Glance

### CI/CD Definition
- **CI (Continuous Integration)**: Automatically test code after every commit
- **CD (Continuous Delivery)**: Prepare code for production (manual approval)
- **CD (Continuous Deployment)**: Automatically deploy to production (no approval)

### The Pipeline Flow
```
Code → Git → CI (test, scan) → Artifact → CD (deploy) → Production
```

## The 10 Modules

| Module | Focus | Key Takeaway |
|--------|-------|--------------|
| 01 | Fundamentals | CI/CD prevents disasters, is systems not tools |
| 02 | Source Control | Git webhooks trigger pipelines, branch protection gates code |
| 03 | CI Pipeline | Stages: lint → build → test → scan, fail fast |
| 04 | Artifacts | Same artifact through all environments, versioned |
| 05 | Security | Scan code, dependencies, and images. Manage secrets. |
| 06 | CD | Blue-green/canary for safe deployments, rollback ready |
| 07 | IaC | Infrastructure in Git, tested in pipeline, versioned |
| 08 | Observability | Logs, metrics, traces. Know what's happening always. |
| 09 | Tools | Tool matters less than system. Don't get locked in. |
| 10 | Failure | Detect fast, rollback automated, post-mortem always |

## Pipeline Checklist

### CI Pipeline Must Have
- [ ] Checkout code
- [ ] Install dependencies
- [ ] Lint (format, style, bugs)
- [ ] Build (compile, bundle)
- [ ] Unit tests (fast, isolated)
- [ ] Integration tests (with services)
- [ ] Security scans (SAST, dependencies)
- [ ] Build artifact

### CD Pipeline Must Have
- [ ] Deploy to staging
- [ ] Smoke tests (basic functionality)
- [ ] Approval gate (for production)
- [ ] Deploy to production
- [ ] Health checks
- [ ] Rollback readiness

## Security Checklist

- [ ] No hardcoded secrets
- [ ] Secret scanning in CI
- [ ] Dependency scanning
- [ ] Container image scanning
- [ ] SAST scanning (code analysis)
- [ ] No secrets in logs
- [ ] Signed artifacts
- [ ] Access control to CI/CD
- [ ] Audit trail maintained

## Deployment Strategies Quick Ref

| Strategy | Duration | Blast Radius | Rollback | Best For |
|----------|----------|--------------|----------|----------|
| Big Bang | 5 min | 100% | Manual (slow) | Small, low-risk apps |
| Blue-Green | 15 min | 0% (instant switch) | Instant (<1 min) | Critical systems |
| Canary | 30 min | 10% initially | Automatic | Large scale |
| Rolling | 10 min | Gradual | N/A (old gone) | Microservices |

## Common Pipeline Problems & Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| Pipeline too slow | Slow tests, sequential stages | Parallelize, optimize tests |
| Flaky tests | Non-deterministic code/infra | Make tests deterministic |
| Failed deployments | Staging != production | Enforce staging parity |
| Forgotten secrets | No scanning | Add secret scanning |
| Slow rollback | Manual processes | Automate rollback |
| Ignorant alerts | No observability | Add logging, metrics |

## Recommended Tools (Examples)

### CI/CD Platform
- GitHub Actions (small teams, GitHub users)
- Jenkins (enterprises, complex needs)
- GitLab CI (integrated with GitLab)

### Artifact Registry
- Docker Hub (public)
- ECR / GCR / ACR (cloud providers)
- Artifactory / Nexus (self-hosted)

### Infrastructure as Code
- Terraform (multi-cloud)
- CloudFormation (AWS-only)
- ARM Templates (Azure-only)

### Monitoring
- Prometheus + Grafana (open source)
- Datadog (commercial)
- New Relic (commercial)
- CloudWatch (AWS-only)

### Secrets Management
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Kubernetes Secrets

## Important Metrics to Track

```
Pipeline Metrics:
  - Duration (target: <5 min)
  - Success rate (target: >99%)
  - Test coverage (target: >80%)

Deployment Metrics:
  - Deployment frequency (higher = good)
  - Lead time (code to production)
  - MTTR (mean time to recovery)
  - Change failure rate (target: <15%)

Production Metrics:
  - Error rate (target: <0.1%)
  - Latency (p95, p99)
  - Availability (target: >99.9%)
  - Uptime (track incidents)
```

## Incident Response Quick Steps

1. **Detect** (automated alerts)
2. **Alert** (notify team)
3. **Decide** (rollback or hotfix?)
4. **Execute** (< 15 min target)
5. **Verify** (confirm recovered)
6. **Document** (post-mortem)

## Cost of CI/CD Investment

### First 6 Months
- Setup time: 2-4 weeks
- Infrastructure: $500-2000/month
- Total: ~$3-5K

### Per Incident Saved
- Manual deployment error: $50K-500K downtime cost
- Prevented by CI/CD: saves millions/year

### ROI
- Prevents ~1 major incident/year
- ROI: 10-100x

## What NOT to Do

- ❌ No testing (code goes untested to production)
- ❌ Manual deployments (human error, slow)
- ❌ No rollback (stuck with bad code)
- ❌ Secrets in code (security breach)
- ❌ No monitoring (can't tell if problem)
- ❌ Manual approval (slow, not scalable)
- ❌ One environment (staging != production issues)
- ❌ No versioning (can't track what's deployed)

## How to Learn CI/CD

1. **Understand principles** (modules 1-3)
2. **Build simple pipeline** (modules 1-4)
3. **Add security** (module 5)
4. **Deploy safely** (module 6)
5. **Version infrastructure** (module 7)
6. **Observe system** (module 8)
7. **Choose tools wisely** (module 9)
8. **Handle failures** (module 10)
9. **Build complete system** (final project)
10. **Iterate and improve**

## Key Terms

- **Artifact**: Output of CI (built code/image)
- **Drift**: Infrastructure differs from code
- **Idempotent**: Running twice = same result
- **MTT**: Mean Time To (MTTD=detect, MTTR=recover)
- **Rollback**: Revert to previous version
- **Smoke test**: Quick test that basic stuff works
- **YAML**: Configuration language (readable)
- **Webhook**: Automated event notification (Git → CI)

## Interview Questions (For Self-Test)

1. What's the difference between CI and CD?
2. Why is fail-fast important in pipelines?
3. How would you prevent secrets from being committed?
4. What's the advantage of artifacts over rebuilding?
5. How would you safely deploy without downtime?
6. How would you detect a deployment failure?
7. What's the difference between staging and production?
8. Why is infrastructure code better than manual?
9. How do you know when to rollback?
10. What would you do if deployment breaks production?

## Final Wisdom

> "CI/CD isn't about the tools. It's about automating safety, catching errors early, and recovering fast. If your system is complex but unreliable, you haven't won. If your system is simple, fast, and safe, you've succeeded."

The best CI/CD system is one you don't think about until it's broken.
