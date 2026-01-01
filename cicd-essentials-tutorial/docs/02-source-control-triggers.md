# Module 02: Source Control & Triggers

## Architecture: Git as the Source of Truth

In a CI/CD system, Git is not just version control. Git is the trigger mechanism that initiates everything.

Every commit to Git triggers an event. That event automatically starts your pipeline. Your entire CI/CD system is built on Git webhooks.

```
Developer pushes code to Git
         ↓
Git sends webhook (HTTP POST)
         ↓
CI system receives webhook
         ↓
Pipeline starts automatically
```

Git is the central nervous system. Without it, there's no automation.

## Git Workflows for CI/CD

### Workflow 1: Trunk-Based Development (Single Branch)

All developers work on `main` (or `master`). Every commit to `main` goes directly to production.

```
main: --[A]--[B]--[C]--[D]--[E]
       (all merges immediate)
```

**When CI runs:**
- On every commit to main
- Tests must pass before commit is accepted
- Deployment happens automatically (Continuous Deployment)

**Pros:**
- Simplest workflow
- Fastest deployment
- No long-lived branches (easier merges)
- Everyone works on same code

**Cons:**
- Requires very strong testing (no safety net)
- No way to separate development from production
- Hard for teams with varying code quality

**Production use:** Google, Facebook (internal), Netflix (video processing)

### Workflow 2: Feature Branches + Pull Requests

Developers work on feature branches. Code is merged to `main` through pull requests (code review gate).

```
feature/auth    --[A]--[B]--
                    ↓
                 (PR created)
                    ↓
                 (CI runs on PR)
                    ↓
                 (Code review)
                    ↓
main: -----------[C]--[Merged]--[D]--
      (each merge triggers CI/CD)
```

**When CI runs:**
1. When PR is created (tests on proposed code)
2. When code is pushed to PR (re-run tests)
3. When merged to main (final verification before deploy)

**Pros:**
- Code review gates prevent bad code
- Parallel development (multiple features)
- CI provides automated checks before review
- Safer than trunk-based

**Cons:**
- More complex workflow
- Longer time to production (PR review adds time)
- Branch merge conflicts possible
- Potential for old branches

**Production use:** GitHub, GitLab, most mid-large companies

### Workflow 3: Git Flow (Complex But Structured)

Multiple long-lived branches with specific purposes.

```
main (production)     ←── release branches
  ↑
  ├── develop (staging) ←── feature branches
  │
  └── hotfix (emergency)
```

**Branches:**
- `main`: Production code only
- `develop`: Integration branch (next release)
- `feature/*`: Feature development
- `release/*`: Release preparation
- `hotfix/*`: Emergency production fixes

**When CI runs:**
- On feature branches (before merge to develop)
- On develop (continuous pre-release testing)
- On release branches (release verification)
- On main (production deployment)

**Pros:**
- Clear separation of concerns
- Structured release process
- Good for scheduled releases

**Cons:**
- Complex (steeper learning curve)
- Many branches to manage
- Longer feedback loops
- Can feel heavyweight for small teams

**Production use:** Enterprise software, scheduled release cycles

## Branch Protection Rules

Branch protection is your safety gate. Without it, anyone can merge bad code.

### Essential Rules

```
Protected Branch: main

Rules:
  ✓ Require status checks (CI must pass)
  ✓ Require code reviews (minimum 1)
  ✓ Dismiss stale PR approvals (re-test on new push)
  ✓ Require branches up to date (no merge conflicts)
  ✓ Require signed commits (verify commit author)
  ✓ Enforce admin enforcement (rules apply to everyone)
```

### Example: GitHub Branch Protection

```
Branch name pattern: main
  ✓ Require a pull request before merging
    - Require approvals: 1
    - Dismiss stale pull request approvals when new commits: YES
    - Require review from code owners: YES
  ✓ Require status checks to pass before merging
    - Require branches to be up to date: YES
    - CI Pipeline: required
    - Security Scan: required
    - Unit Tests: required
  ✓ Require code owner review
  ✓ Require commit signatures
  ✓ Include administrators: YES
```

## Webhooks: The Trigger Mechanism

When code is pushed to Git, Git sends a webhook (HTTP POST) to your CI system.

### How Webhooks Work

1. Git receives a push
2. Git looks up configured webhooks
3. Git sends HTTP POST to webhook URL with event data
4. CI system receives POST
5. CI system parses event (what branch? what commit?)
6. CI system triggers appropriate pipeline

### Webhook Event Data

```json
{
  "ref": "refs/heads/feature/auth",
  "before": "abc123def456",
  "after": "xyz789uvw012",
  "repository": {
    "name": "backend",
    "full_name": "company/backend"
  },
  "pusher": {
    "name": "alice",
    "email": "alice@company.com"
  },
  "commits": [
    {
      "id": "xyz789uvw012",
      "message": "Add JWT authentication",
      "author": {
        "name": "alice",
        "email": "alice@company.com"
      }
    }
  ]
}
```

CI system uses this data to:
- Determine which branch was pushed
- Get the commit SHA
- Identify the author
- Trigger appropriate pipeline

### Webhook Configuration (Conceptual)

```
Git Platform Setup:
  Repository: backend
  Webhook URL: https://ci.company.com/webhook
  Events: push, pull_request
  Secret: (for verification)
  
Triggers:
  - Push to main → Run full CI/CD pipeline
  - Push to feature/* → Run CI only
  - Pull request opened → Run CI
  - Pull request updated → Re-run CI
```

## Tag-Based Releases

Tags mark specific commits as releases. They're the explicit release mechanism.

### Semantic Versioning

Versions: `MAJOR.MINOR.PATCH`

- `MAJOR`: Incompatible API changes
- `MINOR`: Backward-compatible feature additions
- `PATCH`: Bug fixes

Examples:
- `v1.0.0` - First release
- `v1.1.0` - New feature (backward compatible)
- `v1.1.1` - Bug fix
- `v2.0.0` - Breaking changes

### Release Workflow

```
Developer commits code to main
         ↓
Code passes CI
         ↓
Ready for release: git tag v1.2.3
         ↓
Git webhook triggered with tag event
         ↓
CI detects tag (not branch)
         ↓
CI builds release artifacts
         ↓
CD deploys to production
         ↓
All tagged versions are in production
```

### Why Tags Matter for CI/CD

1. **Explicit versioning**: Release is intentional, not automatic
2. **Audit trail**: Every production version is tagged in Git
3. **Rollback clarity**: "Rollback to v1.2.1" is clear
4. **Artifact traceability**: Docker image v1.2.3 matches Git tag v1.2.3

### Example: Tag-Based Pipeline Logic

```
if webhook event is "tag":
    if tag matches "v*":
        build_release_artifacts()
        deploy_to_production()
    else:
        skip()

if webhook event is "push to main":
    run_ci_tests()
    if tests pass:
        build_staging_artifacts()
        deploy_to_staging()
```

## Practical Example: Real Feature Development

**Scenario:** Adding two-factor authentication to a banking app

### Step 1: Create Feature Branch

```bash
git checkout -b feature/2fa
# Webhook: Feature branch created (might not trigger pipeline)
```

### Step 2: Develop Feature

```bash
# Alice writes code
git commit -m "Add TOTP support"
git push origin feature/2fa
# Webhook: Push to feature/2fa
# CI System: Runs tests on feature/2fa
# Result: Tests pass (or fail, Alice fixes)
```

### Step 3: Create Pull Request

```bash
# Create PR on GitHub/GitLab
# Webhook: Pull request opened
# CI System: Runs tests again on PR
# GitHub: Shows "CI passed" or "CI failed"
# Code review begins
```

### Step 4: Approve and Merge

```bash
# Reviewer approves PR after code review
git merge --squash
# Webhook: Push to main
# CI System: Runs full pipeline on main
# Result: Tests + scan + lint all pass
# CD System: Builds artifact
# CD System: Deploys to staging
# Smoke tests on staging pass
```

### Step 5: Release

```bash
git tag v2.5.0
git push origin v2.5.0
# Webhook: Tag created
# CI System: Detects tag is a release
# CD System: Builds production artifact
# CD System: Deploys to production
# Monitoring: All systems green
```

**Total flow:** 3 days (feature development + review)

## Common Mistakes

### Mistake 1: Large Feature Branches

Wrong: "We'll work on this feature for 3 months, then merge"

Problem:
- 3-month divergence from main means massive merge conflicts
- CI can't catch integration issues until merge time
- Code review is 500+ files; impossible to review
- Merge takes days to resolve conflicts

Right: Feature branches stay open 1-2 weeks maximum

### Mistake 2: No Branch Protection

Wrong: "Anyone can merge anything to main"

Problem:
- Bad code reaches main
- Tests don't run before merge
- Untested code goes to production
- No accountability

Right: Branch protection enforces code quality rules

### Mistake 3: Ignoring CI Results

Wrong: "CI failed but we'll merge anyway"

Problem:
- You're saying "I know the tests fail, let's ignore it"
- Untested code reaches production
- This is how disasters happen

Right: CI failure = automatic merge block, or explicit emergency override (rare)

### Mistake 4: Slow Code Review

Wrong: "PR is open for a week waiting for review"

Problem:
- Developer context is gone
- Branch diverges from main
- Code deploys slower
- Feature takes longer to reach users

Right: Code review SLA should be <24 hours

### Mistake 5: Manual Webhooks

Wrong: "We manually triggered the CI pipeline"

Problem:
- Inconsistent pipeline runs
- Missed triggers
- No automation
- Manual is the opposite of CI/CD

Right: Webhooks automatically trigger pipelines (no manual intervention)

## Production Notes

### Webhook Security

Never trust webhook data blindly.

**Good practices:**
1. Verify webhook signature (Git provides a secret to sign webhooks)
2. Only accept webhooks from your Git platform's IPs
3. Log all webhook events for audit
4. Reject webhooks with invalid signatures

### Branch Naming Conventions

Consistent naming makes automation and policy easier:

```
feature/*     - New features (e.g., feature/2fa, feature/auth-v2)
bugfix/*      - Bug fixes (e.g., bugfix/login-redirect)
hotfix/*      - Emergency production fixes (e.g., hotfix/data-loss)
release/*     - Release branches (e.g., release/v2.5.0)
docs/*        - Documentation changes (e.g., docs/api-readme)
chore/*       - Non-code changes (e.g., chore/dependency-update)
```

Policy: Certain branches might have different CI rules. Example:
- `hotfix/*` skips some tests, deploys faster
- `feature/*` requires full test suite
- `docs/*` skips certain security scans

### Commit Messages Matter

Good commit messages help debugging:

```
Good:   "Fix database connection pool exhaustion on high load"
Bad:    "fix stuff"

Good:   "Add TOTP 2FA support (fixes issue #1234)"
Bad:    "2fa"

Good:   "Refactor auth service for readability"
Bad:    "cleanup"
```

Why? When a deployment fails, you read commit messages to understand what changed.

### Git vs CI/CD Coupling

Git and CI/CD are tightly coupled. You need:

1. Webhooks enabled (bidirectional communication)
2. CI system has Git read access
3. CI system can post status back to Git (PR status checks)
4. Secrets stored securely (CI system uses Git credentials)

This is why CI/CD setup is both Git configuration AND CI system configuration.

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. You have two developers working on features simultaneously. What Git workflow allows this?
   - a) Trunk-based development
   - b) Feature branches
   - c) Git flow
   - d) Both b and c

2. A developer pushes code to their feature branch. CI tests fail. What should happen next?
   - a) Code automatically merges to main
   - b) Code cannot merge until tests pass
   - c) Manual override merges anyway
   - d) Developer creates new feature branch

3. Why is a tag-based release better than "deploy main every hour"?
   - a) Tags are faster
   - b) Tags provide explicit version numbers for audit trail
   - c) Tags don't require testing
   - d) Tags work in all Git platforms

4. Your CI pipeline is triggered by a webhook push to `develop` branch. What should happen?
   - a) Only main should trigger production deployment
   - b) Develop should deploy to staging automatically
   - c) Both a and b
   - d) Webhooks are unreliable; use manual triggers

5. A merged PR to main has a critical security vulnerability discovered 30 minutes later. Why would tag-based releases help?
   - a) Tag prevents the merge
   - b) Tag wasn't created yet, so no production release happened
   - c) Tags allow instant rollback
   - d) Tags don't help in this scenario

### Pipeline Design Tasks

**Task 1: Design a Git Workflow**
You're setting up a team of 8 engineers. They work on features concurrently. What Git workflow would you use?
- Draw the branch structure
- Explain when CI runs
- Explain when CD runs
- What's your merge strategy?

**Task 2: Webhook Trigger Logic**
Design the logic for when a CI pipeline should run. For each webhook event, determine if pipeline runs:

- Push to main: ? (full CI/CD or staging only?)
- Push to feature/auth: ? (run tests or skip?)
- Pull request opened: ? (run CI on PR code)
- Tag v2.5.0: ? (release pipeline)
- Tag deployment-test: ? (temporary tag)

### Failure Scenario

**Scenario: Webhook Cascade Failure**

Your CI system receives a webhook. A bug in the webhook handler causes the CI system to:
1. Crash on every webhook event
2. Stop processing new pipeline triggers
3. Mark all pending pipelines as "in progress" indefinitely

Meanwhile, developers are pushing code, merging PRs, and creating tags. None of them trigger pipelines (the system is broken).

Questions:
1. How long before anyone notices?
2. What's the failure impact (code not tested, deployments not happening)?
3. How would you detect this failure?
4. How would you prevent developers from merging untested code during the outage?
5. How would you recover (do you reprocess old webhooks)?

---

Next: [Module 03: CI Pipeline Design](03-ci-pipeline-design.md)
