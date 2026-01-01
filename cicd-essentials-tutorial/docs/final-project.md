# Final Project: Production-Grade CI/CD System

## Overview

Build a complete, production-oriented CI/CD system for a backend application. This project integrates concepts from all 10 modules.

**Time commitment:** 1-2 weeks

**Difficulty:** Advanced (assumes completion of modules 1-10)

## Project Requirements

### System Architecture

You will build a system that:

```
Developer ─→ Git Repository
               ↓ (webhook)
          ┌─────────────────┐
          │  CI PIPELINE    │
          │  • Compile      │
          │  • Test         │
          │  • Scan         │
          │  • Build image  │
          └────────┬────────┘
                   ↓
          ┌──────────────────┐
          │ Artifact Registry│
          │ (Docker images)  │
          └────────┬─────────┘
                   ↓
          ┌──────────────────┐
          │  CD PIPELINE     │
          │  • Deploy stage  │
          │  • Verify        │
          │  • Deploy prod   │
          │  • Rollback      │
          └──────────────────┘
                   ↓
          ┌──────────────────┐
          │   Production     │
          │  (healthy app)   │
          └──────────────────┘
```

### Application to Deploy

Use the `flask-backend-tutorial/backend` application (provided in workspace).

**Application details:**
- Python Flask backend
- Requires Python 3.11+
- Dependencies in `requirements.txt`
- Routes in `app/routes/`
- Models in `app/models/`
- Tests in `tests/`

You will need to:
1. Add missing test files
2. Create CI/CD pipeline configuration
3. Create Dockerfile
4. Create deployment infrastructure (IaC)
5. Set up monitoring and rollback

## Part 1: Containerize the Application

### Task 1.1: Create Dockerfile

Location: `flask-backend-tutorial/backend/Dockerfile`

Requirements:
- Multi-stage build (build stage + runtime stage)
- Based on Python 3.11-slim
- Install dependencies from requirements.txt
- Run on port 8000
- Non-root user for security
- Health check endpoint

**Deliverable:** Dockerfile that builds successfully

```bash
# Test:
cd flask-backend-tutorial/backend
docker build -t flask-app:test .
docker run -p 8000:8000 flask-app:test
# Should start without errors
```

### Task 1.2: Create .dockerignore

Location: `flask-backend-tutorial/backend/.dockerignore`

Exclude:
- `__pycache__`
- `.pytest_cache`
- `*.pyc`
- `.git`
- `.gitignore`
- `venv/`
- `.env`

## Part 2: Create CI Pipeline

### Task 2.1: GitHub Actions Workflow

Location: `flask-backend-tutorial/.github/workflows/ci.yml`

Pipeline must:

**Stage 1: Checkout & Setup**
- Check out code
- Set up Python 3.11

**Stage 2: Lint**
- Run `pylint` on `app/` and `tests/`
- Run `flake8` for style
- Fail if linting fails

**Stage 3: Security Scan**
- Scan for hardcoded secrets (truffleHog or similar)
- Scan dependencies (pip-audit)
- Fail if critical vulnerabilities found

**Stage 4: Tests**
- Install dependencies
- Run unit tests (`pytest tests/unit/`)
- Run integration tests (`pytest tests/integration/`)
- Generate coverage report
- Fail if coverage < 80%

**Stage 5: Build Artifact**
- Build Docker image tagged with Git SHA
- Push to Docker Hub (or local registry)
- Tag as `latest` for main branch

**Deliverable:** CI workflow that:
- Runs on every push and pull request
- Fails fast (lint before tests)
- Generates coverage report
- Produces Docker artifact

### Task 2.2: Branch Protection

In Git platform settings:
- Require CI to pass before merge
- Require code review (1 approval)
- Require branches up to date

**Deliverable:** Screenshot of branch protection rules

## Part 3: Create CD Pipeline

### Task 3.1: CD Workflow

Location: `flask-backend-tutorial/.github/workflows/cd.yml`

Triggered when code is merged to `main`:

**Stage 1: Deploy to Staging**
- Pull Docker artifact
- Deploy to staging environment
- Run smoke tests (health check, basic endpoints)

**Stage 2: Manual Approval**
- Wait for human approval before production

**Stage 3: Deploy to Production**
- Deploy same artifact to production
- Use blue-green or canary strategy (describe in comments)
- Monitor metrics
- Auto-rollback if error rate spikes

**Stage 4: Verification**
- Verify production is healthy
- Generate deployment report

**Deliverable:** CD workflow that:
- Deploys only tested artifacts
- Requires approval before production
- Has rollback capability
- Includes monitoring

### Task 3.2: Rollback Procedure

Document (in `DEPLOYMENT.md`):
- How to manually rollback
- What metrics trigger automatic rollback
- How to verify rollback succeeded
- Time to rollback (SLA: <5 minutes)

**Deliverable:** DEPLOYMENT.md with rollback procedures

## Part 4: Infrastructure as Code

### Task 4.1: Terraform Configuration

Location: `flask-backend-tutorial/infrastructure/`

Define infrastructure for:

**Staging Environment**
- 1 application server (compute)
- Database (PostgreSQL, dev-sized)
- Load balancer (if multi-instance)
- Security groups

**Production Environment**
- 2+ application servers
- Database (PostgreSQL, production-sized)
- Load balancer
- Security groups (restrictive)
- Auto-scaling rules

Structure:
```
infrastructure/
├── main.tf (orchestration)
├── variables.tf (inputs)
├── outputs.tf (outputs)
├── modules/
│   ├── compute/ (servers)
│   ├── database/ (RDS/similar)
│   └── networking/ (security, LB)
└── environments/
    ├── staging.tfvars
    └── production.tfvars
```

**Deliverable:** Terraform code that:
- Is modular
- Defines staging and production
- Uses variables for environment-specific values
- Outputs connection info

### Task 4.2: Infrastructure in CI/CD

Add to CI/CD pipeline:
- `terraform validate` (check syntax)
- `terraform fmt --check` (check formatting)
- `terraform plan` (show changes)
- Security scan (checkov or tfsec)
- Manual approval before `terraform apply`

**Deliverable:** Infrastructure validation in pipeline

## Part 5: Monitoring & Observability

### Task 5.1: Application Metrics

Add to Flask application (in `app/metrics.py` or similar):

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics:
request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'Request duration')
active_users = Gauge('active_users', 'Active users')

# Instrument routes:
@app.route('/api/users')
def get_users():
    request_count.inc()
    # ... logic ...
```

**Deliverable:** Flask app with Prometheus metrics endpoint at `/metrics`

### Task 5.2: Deployment Logs

Configure pipeline to:
- Upload CI/CD logs to storage (S3 or artifact storage)
- Log all deployments (who, what, when)
- Include audit trail

Location: `docs/OBSERVABILITY.md`

Document:
- What's logged?
- Where are logs stored?
- How long retained?
- How to query logs?

**Deliverable:** OBSERVABILITY.md with logging strategy

### Task 5.3: Alerts

Define alerts (in monitoring system or cloud provider):

- CI pipeline failure rate > 10%
- CD deployment failure
- Production error rate > 1%
- Production latency > 500ms
- Production database connection exhausted
- Disk space < 10%

**Deliverable:** Alert configuration (as code if possible)

## Part 6: Security

### Task 6.1: Secret Management

Document (in `docs/SECURITY.md`):
- How secrets are managed in CI/CD
- How application accesses secrets in production
- Secret rotation policy
- Who has access to what

Example:
```
CI/CD: Secrets stored as GitHub Secrets
  - Database password
  - Docker registry credentials
  - AWS credentials (if using cloud)

Production: Secrets stored in cloud provider
  - AWS Secrets Manager
  - OR environment variables
  - OR Kubernetes secrets

Rotation: Every 90 days (database password)
Access: Only application process, no humans
```

**Deliverable:** SECURITY.md with secret strategy

### Task 6.2: Image Scanning

Add to CI pipeline:
```yaml
- name: Scan Docker Image
  run: |
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
      aquasec/trivy:latest image flask-app:${{ github.sha }}
```

Fail if critical vulnerabilities found.

**Deliverable:** Docker image scanning in CI

### Task 6.3: Code Security

Add to CI pipeline:
- Static analysis (bandit for Python)
- Dependency scanning (pip-audit)
- SAST scanning (semgrep or similar)

**Deliverable:** Security scanning in CI pipeline

## Part 7: Tests (Enhance)

### Task 7.1: Unit Tests

Location: `flask-backend-tutorial/backend/tests/unit/`

Create tests for:
- Authentication routes
- User model
- Password hashing
- Database utilities

Minimum: 20 unit tests

**Coverage target:** > 80%

### Task 7.2: Integration Tests

Location: `flask-backend-tutorial/backend/tests/integration/`

Create tests for:
- End-to-end API flows
- Database transactions
- Error handling
- Authentication + authorization flows

Minimum: 10 integration tests

### Task 7.3: Deployment Tests (Smoke Tests)

Location: `flask-backend-tutorial/tests/smoke/`

Create tests that verify deployment:
```python
def test_health_endpoint():
    resp = requests.get('http://localhost:8000/health')
    assert resp.status_code == 200

def test_users_endpoint():
    resp = requests.get('http://localhost:8000/api/users')
    assert resp.status_code == 200
    assert 'users' in resp.json()
```

Run after deployment to verify it worked.

**Deliverable:** Smoke tests that run post-deployment

## Part 8: Documentation

### Task 8.1: README

Location: `flask-backend-tutorial/README.md`

Include:
- Quick start (how to run locally)
- CI/CD pipeline overview
- Deployment procedure
- How to rollback
- Monitoring and alerts
- Contributing guidelines

### Task 8.2: Runbook

Location: `flask-backend-tutorial/docs/RUNBOOK.md`

Include:
- Troubleshooting guide
- Common issues and fixes
- Performance debugging
- Incident response procedure
- Contact information

### Task 8.3: Architecture Diagram

Create diagram (as code or image) showing:
- CI/CD flow
- Infrastructure
- Monitoring
- How code moves from development to production

## Part 9: Validation Checklist

Complete the following:

- [ ] Code compiles without errors
- [ ] All tests pass (unit + integration)
- [ ] Code coverage > 80%
- [ ] Linting passes (pylint, flake8)
- [ ] Docker image builds successfully
- [ ] Docker image scans for vulnerabilities (no critical)
- [ ] CI pipeline runs on every push
- [ ] Broken commits are prevented from merging
- [ ] Code review required before merge
- [ ] CD deploys to staging automatically
- [ ] CD requires approval before production
- [ ] Smoke tests verify deployment
- [ ] Rollback procedure is documented
- [ ] Rollback can be executed in < 5 minutes
- [ ] Infrastructure is defined as code (Terraform)
- [ ] Infrastructure changes go through CI/CD
- [ ] Secrets are not in code or logs
- [ ] Monitoring and alerts are configured
- [ ] Deployment logs are retained
- [ ] README documents everything

## Part 10: Presentation

### Deliverable

Create a brief summary document (in `flask-backend-tutorial/docs/PROJECT_SUMMARY.md`):

**System Overview**
- Architecture (text diagram)
- Pipeline flow
- Environments (staging, production)

**Key Components**
- CI pipeline (stages, duration, gates)
- CD pipeline (deployment strategy, rollback)
- Infrastructure (key resources)

**Highlights**
- Fail-fast mechanism (what's checked first?)
- Safety gates (what prevents bad code from shipping?)
- Recovery procedure (how to rollback?)
- Observability (what's monitored?)

**Lessons Learned**
- What did you learn building this?
- What would you do differently?
- What would you improve with more time?

**Statistics**
- CI pipeline duration
- Test count and coverage
- Number of deployment stages
- Infrastructure resources

## Grading Criteria

| Category | Points | Criteria |
|----------|--------|----------|
| **CI Pipeline** | 25 | Comprehensive testing, linting, security scans, fast feedback |
| **CD Pipeline** | 25 | Safe deployments, staging verification, approval gates, rollback |
| **Infrastructure** | 20 | Terraform modules, environment separation, scalability |
| **Testing** | 15 | Unit tests, integration tests, coverage, smoke tests |
| **Security** | 10 | Secrets management, scanning, no hardcoded values |
| **Documentation** | 5 | README, runbook, architecture clear |

**Total: 100 points**

Passing: 70+ points
Excellent: 85+ points

## Bonus Challenges

If you complete the base project:

**Bonus 1: Canary Deployment**
- Implement canary deployment (deploy to 10% first, monitor)
- Automatic rollback if error rate spikes
- Gradual traffic shift to 100%

**Bonus 2: Multi-Region Deployment**
- Deploy to two regions simultaneously
- Health check from both regions
- Failover if region fails

**Bonus 3: Cost Optimization**
- Add metrics for infrastructure cost
- Implement auto-scaling based on load
- Calculate cost per deployment

**Bonus 4: Advanced Observability**
- Distributed tracing (follow request through system)
- Custom metrics
- Integration with external monitoring (Datadog, NewRelic)

**Bonus 5: GitOps**
- All deployments driven by Git
- Production state reflects Git state
- Automatic remediation if drift detected

**Bonus 6: Compliance**
- Implement audit trail
- Automated compliance checks
- Evidence generation for compliance audits

## Tips for Success

1. **Start small**: Get basic pipeline working, then enhance
2. **Test locally first**: Before committing, run tests locally
3. **Use existing tools**: Don't build everything from scratch
4. **Document as you go**: Don't leave documentation for the end
5. **Practice rollback**: Actually execute it once to verify it works
6. **Monitor from day one**: Add monitoring early, not as afterthought
7. **Security first**: Scan for vulnerabilities, manage secrets properly
8. **Iterate**: First version won't be perfect; that's ok, improve it

## Troubleshooting

### Docker build fails

- Check Dockerfile syntax
- Ensure base image exists
- Check that all files referenced exist
- Try building locally first

### Tests fail in CI but pass locally

- Different Python version? Check CI uses 3.11
- Different dependencies? Check lock file
- Race condition? Flaky test
- Database state? Use fresh DB in tests

### Deployment fails silently

- Check logs
- Verify health checks
- Check error output
- Monitor application metrics

### Infrastructure drift

- Run `terraform plan` to see drift
- Decide: accept manual change (update code) or enforce code (revert)
- Never ignore drift

## Support

If stuck:
1. Review relevant module (1-10)
2. Check examples in `examples/` directory
3. Review Flask backend code structure
4. Ask: "What would production do?"

---

## Submission

Submit the following:

1. **GitHub Repository** with:
   - Modified flask-backend-tutorial/ with CI/CD
   - All pipelines in .github/workflows/ or similar
   - Infrastructure code in infrastructure/
   - Updated README and docs/

2. **Documentation Package** including:
   - DEPLOYMENT.md (how to deploy and rollback)
   - OBSERVABILITY.md (monitoring and logging)
   - SECURITY.md (secrets and security scanning)
   - PROJECT_SUMMARY.md (overview of system)

3. **Proof of Execution**:
   - Screenshot of successful CI pipeline run
   - Screenshot of successful CD deployment
   - Screenshot of branch protection rules
   - Evidence of tests passing

4. **Reflection Document** (1 page):
   - What you learned
   - What was hardest
   - What you'd improve
   - How this compares to manual deployment

---

Congratulations on completing the CI/CD Essentials Tutorial. You now understand CI/CD as a system, not just a tool.

The next step: Apply these principles to your own projects.
