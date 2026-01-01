# Module 09: CI/CD Tools Comparison

## Philosophy: Tools Are Interchangeable

The most important thing to understand: **The tool doesn't matter as much as the system.**

A bad CI/CD system with GitHub Actions works no better than with Jenkins. A good system works with any tool.

Your job is to understand CI/CD systems, then choose tools that fit. Not the reverse.

## The Tool Landscape

```
Self-Hosted:
  - Jenkins (most flexible, steepest learning curve)
  - GitLab (integrated, good for enterprises)
  - Gitea (lightweight)

Cloud-Hosted:
  - GitHub Actions (free with GitHub, tight integration)
  - GitLab CI (built-in)
  - CircleCI (cloud-native, scalable)

Enterprise:
  - JFrog (artifact management focus)
  - Harness (deployment-focused)
  - CloudBees (Jenkins enterprise)
```

## GitHub Actions

### Advantages

**Tight Git Integration:**
- Workflows defined in repo (`.github/workflows/`)
- Trigger on any Git event
- PR status checks native
- Built into GitHub UI

**Free for public repos:**
- Unlimited free minutes for public projects
- Good for open source

**Simple syntax:**
- YAML-based
- Easy to learn
- Lots of pre-built actions (community library)

**Matrix builds:**
```yaml
strategy:
  matrix:
    python-version: [3.9, 3.10, 3.11]
    os: [ubuntu, windows, macos]
```

Runs tests on 6 combinations (3 Python × 2 OS) automatically.

### Disadvantages

**Limited self-hosting:**
- GitHub-hosted runners only (or expensive self-hosted)
- Less control over execution environment

**Locked to GitHub:**
- Can't use if you switch platforms
- No code portability

**Less customization:**
- Actions ecosystem is good but not as deep as Jenkins

**Pricing:**
- Free for public repos
- $0.008/minute for private (can be expensive at scale)

### When to Choose GitHub Actions

- Small-medium teams
- GitHub already in use
- Don't need advanced customization
- Budget-conscious

## Jenkins

### Advantages

**Maximum flexibility:**
- Can do anything (it's a framework)
- Plugin ecosystem (3000+)
- Can run on any infrastructure

**No vendor lock-in:**
- Runs anywhere
- Control everything
- Export jobs/configs

**Self-hosted:**
- No per-minute pricing
- Can scale horizontally
- Can optimize for your needs

**Advanced features:**
- Sophisticated workflow orchestration
- Multi-branch pipelines
- Distributed builds

### Disadvantages

**Complex setup:**
- Steep learning curve
- Requires ops expertise
- Infrastructure management required

**Maintenance burden:**
- Must manage Jenkins server
- Must maintain plugins
- Must manage security updates

**Not integrated with Git:**
- Must configure webhooks manually
- More setup overhead

**No free tier:**
- Must host yourself (cost in infrastructure)
- More operational overhead

### When to Choose Jenkins

- Enterprise with ops team
- Complex, custom workflows needed
- Switching from old system (already trained)
- Need no vendor lock-in
- Already have infrastructure

## GitLab CI

### Advantages

**Integrated into GitLab:**
- CI/CD built-in, no separate tool
- Easy to set up for GitLab users
- Workflow lives in repo

**Good documentation:**
- Better docs than GitHub Actions
- Mature product

**Self-hosted option:**
- Can self-host GitLab + CI/CD
- Full control

**Free tier:**
- Reasonable free tier
- Open source projects get free minutes

### Disadvantages

**GitLab lock-in:**
- Must use GitLab for Git hosting
- Less portable than Jenkins

**Smaller ecosystem:**
- Fewer community extensions
- Less third-party integrations than Jenkins

**Requires GitLab:**
- If you use GitHub/Gitea, doesn't apply
- Migration cost if switching from GitHub

### When to Choose GitLab CI

- Already using GitLab
- Want integrated CI/CD (no separate tool)
- Self-hosting preferred
- Medium-sized teams

## Tool Comparison Table

| Aspect | GitHub Actions | Jenkins | GitLab CI | CircleCI |
|--------|---|---|---|---|
| **Setup Time** | <1 hour | 1-2 days | 1-2 hours | <1 hour |
| **Learning Curve** | Easy | Hard | Medium | Easy |
| **Customization** | Good | Excellent | Good | Medium |
| **Self-Hosting** | Limited | Yes | Yes | Limited |
| **Vendor Lock-In** | GitHub | None | GitLab | CircleCI |
| **Pricing Model** | Minutes-based | Self-hosted | Minutes-based | Minutes-based |
| **Community** | Large | Very Large | Medium | Large |
| **Enterprise Ready** | Yes | Yes | Yes | Yes |
| **Container Support** | Good | Excellent | Good | Excellent |
| **Secret Management** | Good | Good | Excellent | Good |

## Choosing a Tool: Decision Matrix

```
Question 1: Are you already using GitHub?
  YES → GitHub Actions (easiest)
  NO → Continue

Question 2: Do you need maximum flexibility?
  YES → Jenkins
  NO → Continue

Question 3: Are you using GitLab?
  YES → GitLab CI
  NO → Continue

Question 4: Do you need cloud-hosted only?
  YES → CircleCI
  NO → Consider Jenkins or self-hosted GitLab

Question 5: Do you have a DevOps team?
  YES (experienced) → Jenkins
  YES (small) → GitHub Actions or GitLab CI
  NO → GitHub Actions (simplest)
```

## Tool-Agnostic Practices

Regardless of tool, follow these principles:

### 1. Version Control Your Pipeline

```
WRONG: Configure CI through web UI
RIGHT: Pipeline defined in repo (Jenkinsfile, .github/workflows/, .gitlab-ci.yml)

Why: You can review, version, and rollback pipeline changes
```

### 2. Use Standard Formats

Pipeline definition should be:
- Text-based (YAML or similar)
- In version control
- Reviewable in pull requests

### 3. Portable Design

Write pipelines assuming portability:

```
WRONG:
  Uses GitHub Actions-only syntax
  Uses Jenkins plugins
  Uses GitLab-only features

RIGHT:
  Uses basic YAML
  Uses standard build tools (npm, docker, terraform)
  Minimal platform-specific code
```

If you port to new tool, rewrite should take <1 day.

### 4. Document Your Tool Choice

Document:
- Why you chose this tool
- Key features you're using
- How to set up new environment
- Training for new team members

This helps when it's time to change tools (and you will change tools).

## Real Examples

### GitHub Actions for Open Source

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pytest
```

Simple, clean, free for public projects.

### Jenkins for Enterprise

```groovy
pipeline {
  agent any
  
  stages {
    stage('Checkout') {
      steps {
        git url: 'https://github.com/company/backend.git'
      }
    }
    
    stage('Build') {
      steps {
        sh './build.sh'
      }
    }
    
    stage('Test') {
      parallel {
        stage('Unit') {
          steps {
            sh 'pytest tests/unit/'
          }
        }
        stage('Integration') {
          steps {
            sh 'pytest tests/integration/'
          }
        }
      }
    }
    
    stage('Deploy') {
      when {
        branch 'main'
      }
      steps {
        sh './deploy.sh'
      }
    }
  }
  
  post {
    always {
      junit '**/test-results.xml'
      publishHTML([
        reportDir: 'coverage',
        reportFiles: 'index.html',
        reportName: 'Coverage Report'
      ])
    }
  }
}
```

More complex, but powerful. Requires Jenkins infrastructure.

### GitLab CI for Integrated Teams

```yaml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - pytest
  coverage: '/TOTAL.*\s+(\d+%)$/'

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t myapp:$CI_COMMIT_SHA .
    - docker push myapp:$CI_COMMIT_SHA

deploy:
  stage: deploy
  image: bitnami/kubectl:latest
  only:
    - main
  script:
    - kubectl set image deployment/myapp myapp=myapp:$CI_COMMIT_SHA
```

Built-in to GitLab, good defaults, easy to extend.

## Common Mistakes

### Mistake 1: Choosing Tool Before Understanding Requirements

Wrong: "Let's use Jenkins because it's powerful"

Problem:
- Complex setup for simple needs
- Team overwhelmed
- Maintenance burden

Right: Understand your CI/CD needs first, then choose tool

### Mistake 2: Over-Customizing Tool

Wrong: "We'll extend Jenkins with 20 custom plugins"

Problem:
- Impossible to migrate later
- Maintenance nightmare
- Only expert can touch it

Right: Use standard features, minimal customization

### Mistake 3: Tool Evangelicism

Wrong: "GitHub Actions is the best, anyone not using it is wrong"

Problem:
- Different teams have different needs
- One size doesn't fit all
- Waste time arguing instead of building

Right: Choose tool for team/project, respect other choices

### Mistake 4: Never Reevaluating

Wrong: "We chose Jenkins in 2010, never revisit"

Problem:
- Landscape changes
- New tools might be better fit
- Team might be happier with different tool
- Costs might be higher than alternatives

Right: Reevaluate every 2-3 years

### Mistake 5: Tightly Coupling to Tool

Wrong: Pipeline heavily uses Jenkins-specific features

Problem:
- Can't migrate if Jenkins is deprecated
- New team members must learn Jenkins first
- Expensive to switch

Right: Minimal tool-specific code, portable where possible

## Migration Between Tools

When switching from Jenkins to GitHub Actions:

```
Step 1: Audit existing pipelines
  - What does Jenkins do?
  - List all jobs
  - Document each job's purpose

Step 2: Group similar jobs
  - Which jobs can consolidate?
  - Which are redundant?

Step 3: Translate high-value jobs first
  - Most critical pipelines → GitHub Actions
  - Others can wait

Step 4: Run in parallel
  - Keep Jenkins running
  - New pipelines in GitHub Actions
  - Gradually migrate

Step 5: Retire Jenkins
  - Last jobs migrated
  - Jenkins decommissioned
```

Time to migrate: 2-4 weeks for medium team.

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. Your team already uses GitHub. What's the best choice for CI/CD?
   - a) Jenkins (most flexible)
   - b) GitHub Actions (already in GitHub)
   - c) GitLab CI (best integration)
   - d) CircleCI (most scalable)

2. Jenkins' main advantage is:
   - a) Low cost
   - b) Tight GitHub integration
   - c) Maximum flexibility and customization
   - d) Easiest to learn

3. You want to switch CI/CD tools in 1 year. What's the best approach now?
   - a) Use tool-specific features for power
   - b) Write pipeline as tool-agnostically as possible
   - c) Expect 2-month migration
   - d) Accept vendor lock-in

4. What's the biggest risk of choosing Jenkins?
   - a) High per-minute costs
   - b) Operational overhead (must manage)
   - c) Limited customization
   - d) GitHub lock-in

5. True or False: GitHub Actions is always better than Jenkins.
   - a) True (modern > old)
   - b) False (tool choice depends on context)
   - c) True (GitHub integration)
   - d) False (Jenkins is always better)

### Pipeline Design Tasks

**Task 1: Evaluate Tools for Your Team**
Your team: 15 engineers, no DevOps specialists, using GitHub.

Evaluate each tool:
1. GitHub Actions - pros/cons for your team?
2. Jenkins - pros/cons for your team?
3. GitLab CI - pros/cons?
4. Which would you choose and why?

**Task 2: Design Tool Migration**
You're moving from Jenkins to GitHub Actions.

Plan:
1. What's your timeline?
2. Which jobs migrate first?
3. How do you run both in parallel?
4. How do you know migration is complete?

### Failure Scenario

**Scenario: Vendor Lock-In**

Your company chose Jenkins in 2015. Built heavily customized pipelines:
- 30 custom plugins
- Groovy scripts (Jenkins-specific)
- Complex plugin ecosystem
- Only 1 engineer understands full setup

Now (2024):
- That engineer left
- Jenkins is unmaintained
- New tools are much easier
- But migrating seems impossible (30 plugins!)

Questions:
1. How did this happen?
2. What would have prevented it?
3. How long to migrate to GitHub Actions?
4. What should you do now?
5. What would you do differently for a new tool?

---

Next: [Module 10: Failure & Recovery](10-failure-recovery.md)
