# Module 03: CI Pipeline Design

## Architecture: The Build System

A CI pipeline is a build system. It takes source code and produces artifacts (or rejects code).

```
Source Code
    ↓
Stage 1: Prepare (checkout, resolve dependencies)
    ↓
Stage 2: Build (compile, bundle)
    ↓
Stage 3: Unit Tests
    ↓
Stage 4: Integration Tests
    ↓
Stage 5: Quality Analysis (linting, coverage)
    ↓
Stage 6: Security Scanning
    ↓
Success: Code is verified
Failure: Developer is notified (must fix)
```

Each stage answers a specific question:

| Stage | Question | Pass = | Fail = |
|-------|----------|--------|--------|
| Prepare | Can we resolve the code and dependencies? | Continue | Code has missing deps or bad syntax |
| Build | Does the code compile/bundle? | Continue | Syntax errors or build misconfiguration |
| Unit Tests | Does each unit do what it's supposed to? | Continue | Feature didn't work as expected |
| Integration Tests | Does code work with other services/DBs? | Continue | Code breaks APIs or data flows |
| Quality Analysis | Does code meet standards? | Continue | Code is messy/unreadable |
| Security | Are there known vulnerabilities? | Continue | Code has security issues |

Fail at any stage = pipeline stops, developer is notified immediately.

## Key Principle: Fail Fast

A good CI pipeline fails as quickly as possible.

```
Bad Pipeline:
  Compile (2 min) → Tests (15 min) → Linting (1 min) → Scan (30 min)
  Total: 48 minutes to find linting error (24 minutes in)

Good Pipeline:
  Lint (1 min) → Compile (2 min) → Unit Tests (5 min) → Integration Tests (10 min) → Scan (5 min)
  Total: 23 minutes if any fails; most failures caught in 3 minutes
```

Order matters:

1. **Fastest checks first**: Syntax, linting (seconds)
2. **Compilation next**: If code doesn't compile, stop (minutes)
3. **Unit tests**: Fast, focused tests (minutes)
4. **Integration tests**: Slower, but necessary (5-10 minutes)
5. **Security scans**: Slow but important (last)

Rationale: If linting fails, no point running 15-minute tests.

## Stage Details

### Stage 1: Prepare/Checkout

```bash
# CI system actions:
git clone <repository>
git checkout <commit-sha>
npm install          # Resolve dependencies
```

This stage:
- Gets the code from Git
- Installs all dependencies
- Verifies package locks (ensure reproducible builds)

**Failures:**
- Missing package in lock file
- Network error during download
- Package registry is down

### Stage 2: Build

For compiled languages:

```bash
# Java
./mvnw clean package

# Go
go build -o app

# TypeScript
npm run build
```

For interpreted languages (Python, JavaScript):
- No compilation needed
- Still need to check for syntax errors
- Might bundle or transpile

**Example: Python**
```bash
python -m py_compile src/**/*.py  # Check syntax
```

**Example: JavaScript**
```bash
npx tsc --noEmit                  # Type check without emitting
```

Failures:
- Syntax errors
- Missing imports
- Type errors
- Misconfigured build settings

### Stage 3: Unit Tests

Tests for individual functions/units.

```bash
# Python
pytest tests/unit/ -v

# JavaScript
npm test -- --testPathPattern=unit

# Go
go test ./...
```

Unit tests:
- Fast (should complete in <5 minutes)
- Focused (one function per test)
- No external dependencies (database, API, etc.)
- Run in isolation

**Good unit test characteristics:**
- No database calls
- No network calls
- No file I/O
- Completely deterministic (same input = same output)

**Example (Python):**
```python
def test_password_hashing():
    hashed = hash_password("test123")
    assert verify_password("test123", hashed) is True
    assert verify_password("wrong", hashed) is False
```

### Stage 4: Integration Tests

Tests for how components work together.

```bash
# Spin up test database
docker run -d postgres:14 -e POSTGRES_PASSWORD=testpass

# Run integration tests (after DB is ready)
pytest tests/integration/ --db=postgres://localhost:5432/test
```

Integration tests:
- Slower (minutes, not seconds)
- Use real or test databases
- Call real APIs (or mock servers)
- Test data flows between components

**Example: Testing auth flow with database**
```python
def test_user_registration():
    # This test uses a real (test) database
    user = register_user("alice@example.com", "password123")
    assert user.id is not None
    
    # Retrieve user from database
    retrieved = get_user_by_email("alice@example.com")
    assert retrieved.id == user.id
```

### Stage 5: Quality Analysis

#### Linting (Code Style)

```bash
# Python
pylint src/
flake8 src/

# JavaScript
eslint src/

# Go
golangci-lint run
```

Linting checks:
- Consistent formatting
- Unused variables
- Code smell patterns
- Style guide violations

Not about functionality, about readability and consistency.

#### Code Coverage

```bash
# Run tests with coverage
pytest --cov=src tests/

# Output: 84% of code is tested
```

Coverage tells you what percentage of code is tested. It's not a quality metric (100% coverage is not good; meaningful coverage is), but it's useful.

**Example coverage output:**
```
Name          Stmts   Miss Cover
---------------------------------
src/auth.py      45      7    84%
src/api.py      120     15    87%
src/models.py   200     30    85%
---------------------------------
TOTAL           365     52    85%
```

### Stage 6: Security Scanning

#### Dependency Scanning

```bash
# Python
pip-audit

# JavaScript
npm audit

# Go
go list -json -m all | nancy sleuth
```

Checks all dependencies for known vulnerabilities.

Example output:
```
Found 3 vulnerabilities:
  - requests 2.25.0 (CVE-2021-33503): URL parsing vulnerability
  - lodash 4.17.20 (CVE-2021-23337): Prototype pollution
  - Django 3.0.0 (CVE-2020-7471): SQL injection
```

#### SAST (Static Application Security Testing)

Analyzes your code for security issues WITHOUT running it.

```bash
# Semgrep (general purpose SAST)
semgrep --config=p/owasp-top-ten src/

# Find SQL injection risks
semgrep --pattern='SELECT ... FROM ... WHERE ...' src/
```

SAST can find:
- SQL injection risks
- Hardcoded secrets
- Insecure cryptography
- Authentication bypasses
- Unvalidated input

Example:
```python
# SAST would flag this:
username = request.GET.get('username')
query = f"SELECT * FROM users WHERE username = '{username}'"  # SQL injection!
```

## Parallelization

Stages run sequentially (one after another). But some stages can run in parallel.

```
Bad (Sequential):
Lint (1min) → Unit Tests (5min) → Integration Tests (10min) → Scan (5min)
Total: 21 minutes

Good (Parallel where possible):
Lint (1min)
Unit Tests (5min)  ─────────────────────────────────┐
Integration Tests (10min)                           │ 
Scan (5min)                                         ├→ Total: 10 min
                                                    │
All parallel: Most time = longest job (10 min)    ─┘
```

**Rules for parallelization:**

Stages that CAN run in parallel:
- Unit tests and linting (independent)
- Security scanning and tests (independent)
- Multiple test suites (different data)

Stages that MUST run sequentially:
- Build must come after dependency resolution
- Integration tests after unit tests (unit tests should pass first)
- Artifact building after all tests pass

## Example CI Pipeline: Python Flask Backend

```
Developer pushes to feature branch
        ↓
Webhook triggers CI
        ↓
┌─────────────────────────────────────────┐
│ Stage 1: Prepare                        │
│  - git checkout                         │
│  - pip install -r requirements.txt      │
│  - pip install -r requirements-dev.txt  │
│  [1 minute]                             │
└──────────┬────────────────────────────┬─┘
           ↓                            ↓
    ┌──────────────────┐      ┌─────────────────┐
    │ Stage 2: Build   │      │ Stage 3A: Lint  │
    │ - Check syntax   │      │ - pylint        │
    │ - Type check     │      │ - flake8        │
    │ [30 seconds]     │      │ [30 seconds]    │
    └─────────┬────────┘      └────────┬────────┘
              ↓                         ↓
    ┌──────────────────────────────────────────┐
    │ Stage 3: Unit Tests                      │
    │ pytest tests/unit/ -v --cov              │
    │ [3 minutes]                              │
    └──────────┬─────────────────────────────┬─┘
               ↓                             ↓
      ┌─────────────────┐       ┌───────────────────┐
      │ Stage 4A: Scan  │       │ Stage 4B: Integ   │
      │ - bandit        │       │ Tests             │
      │ - safety check  │       │ - pytest integ/   │
      │ [1 minute]      │       │ - test DB         │
      └────────┬────────┘       │ [5 minutes]       │
               ↓                └────────┬──────────┘
    ┌────────────────────────────────────┘
    │
    ↓
┌─────────────────────────────────────────┐
│ ALL STAGES PASSED                       │
│ Code is verified                        │
│ Ready to be merged (or deployed)        │
└─────────────────────────────────────────┘

Total time: 5 minutes (with parallelization)
```

## Example: Simple GitHub Actions Pipeline

```yaml
name: CI

on:
  push:
    branches: [main, feature/**]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements-dev.txt
      - run: pylint src/
      - run: flake8 src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/unit/ -v

  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/integration/ -v --db=postgres://postgres:testpass@postgres:5432/test

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install pip-audit bandit
      - run: pip-audit --desc
      - run: bandit -r src/
```

This pipeline:
- Runs linting and tests in parallel (lint and test jobs)
- Integration tests run separately (needs database)
- Security scans run in parallel
- All must pass before code can be merged

## Common Mistakes

### Mistake 1: Slow Tests in Unit Test Stage

Wrong: Unit tests take 20 minutes because they test against real database

Problem:
- "Unit tests" that require infrastructure aren't unit tests
- Slows down feedback loop
- Developers skip running tests locally

Right: Unit tests use mocks, no external dependencies. <5 minutes total.

### Mistake 2: Not Failing Fast

Wrong: Linting runs at the end of the pipeline (after 30-minute test suite)

Problem:
- Linting error discovered after 30 minutes
- Developer waits, context switches
- Slow feedback loop

Right: Linting is first stage. Fails in seconds if there's an issue.

### Mistake 3: Ignoring Flaky Tests

Wrong: "This integration test sometimes fails, but not consistently"

Problem:
- You can't trust the pipeline
- Developers ignore failures ("it's just the flaky test")
- Bad code passes because "flaky tests" mask it
- Pipeline is unreliable

Right: Fix flaky tests. If you can't, remove them or mock them.

### Mistake 4: No Code Coverage Baseline

Wrong: "We don't track code coverage"

Problem:
- Code gets less tested over time
- New code might not be tested at all
- Production issues from untested code

Right: Set a minimum coverage threshold (e.g., >80%). Fail if below.

### Mistake 5: Running Tests Serially When They Could Parallel

Wrong: Running 10 test suites one after another (100 minutes total)

Problem:
- Slow feedback
- Resources are idle (1 CPU running tests, 7 idle)
- Developers wait longer

Right: Run tests in parallel on multiple executors (each test suite on different CPU).

## Production Notes

### Test Database Strategy

For integration tests, you need a test database.

**Option 1: Spin up per pipeline**
```bash
docker run -d postgres:14 -e POSTGRES_PASSWORD=testpass
pytest tests/integration/
docker stop postgres
```
Pros: Isolated, clean state. Cons: Slower (setup/teardown overhead)

**Option 2: Reuse test database**
```bash
# Database is long-running
# Each pipeline truncates tables, runs tests
pytest tests/integration/
```
Pros: Faster. Cons: State can leak between tests

**Recommendation:** Spin up per pipeline (isolated = reliable)

### Caching Dependencies

Downloading dependencies for every pipeline run is slow.

```yaml
# GitHub Actions example
- uses: actions/setup-python@v4
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
```

This caches pip packages. If requirements.txt doesn't change, use cached packages.

Typical speedup: 2-3 minutes saved per pipeline run.

### Pipeline Timeouts

Set a maximum pipeline runtime. If it exceeds, fail the pipeline.

Default: Usually 60 minutes. You might set to 15 minutes.

Why? Prevents runaway pipelines that consume resources indefinitely.

### Artifact Retention

After pipeline completes, you have artifacts:
- Test reports
- Coverage reports
- Build logs

Store them short-term (7 days) for debugging, then delete.

```
Total pipeline runs per day: 50
Artifacts per run: 100 MB
Storage after 7 days: 50 * 7 * 100 MB = 35 GB
```

Cleanup policy: Delete artifacts older than 7 days.

---

## Practice

### Multiple Choice Questions (NO ANSWERS - Test Yourself)

1. In which order should CI pipeline stages run?
   - a) Build → Unit Tests → Integration Tests → Lint → Scan
   - b) Lint → Build → Unit Tests → Integration Tests → Scan
   - c) Lint → Build → Scan → Unit Tests → Integration Tests
   - d) Unit Tests → Integration Tests → Build → Scan

2. Why should unit tests NOT call a real database?
   - a) It's slower
   - b) Tests become dependent on database state (unreliable)
   - c) Tests can't run in parallel
   - d) All of the above

3. Your pipeline runs in 45 minutes. What's the most likely reason?
   - a) Tests are too strict
   - b) Tests are running sequentially that could run in parallel
   - c) Linting is too aggressive
   - d) SAST scanning is too comprehensive

4. A security scan finds a SQL injection vulnerability. When should this be caught?
   - a) In code review
   - b) In SAST scanning (before tests)
   - c) In integration tests (when you test against real DB)
   - d) In production (when user reports it)

5. Code coverage is 45%. What does this mean?
   - a) Code is 45% reliable
   - b) 45% of code is tested by automated tests
   - c) Code has 45% of possible bugs
   - d) Code quality is below acceptable

### Pipeline Design Tasks

**Task 1: Design a Go Backend Pipeline**
You're building a CI pipeline for a Go backend. The code:
- Uses PostgreSQL
- Has both unit and integration tests
- Needs linting (golangci-lint)
- Has 500+ tests
- Currently takes 25 minutes

Design the pipeline:
1. What stages would you include?
2. What runs in parallel?
3. How would you reduce the 25 minutes?
4. Which tests need a database?

**Task 2: Optimize a Slow Pipeline**
Your current pipeline takes 60 minutes:
- Dependency download: 5 min
- Build: 10 min
- Unit tests: 20 min
- Integration tests: 15 min
- Security scan: 10 min

What changes would you make to get it under 20 minutes?

### Failure Scenario

**Scenario: The Test That Sometimes Works**

Your CI pipeline has an integration test that passes 8 out of 10 times. The other 2 times it times out waiting for database connection.

You have two options:
A) Increase timeout from 5 seconds to 30 seconds
B) Remove the test (it's flaky anyway)
C) Fix the test

The team is frustrated with random failures. You push for option A (quick fix).

Questions:
1. Why is option A a bad idea?
2. What happens if you choose option B?
3. What should you actually do (option C)?
4. How would you detect flaky tests automatically?
5. What's the long-term cost of ignoring flaky tests?

---

Next: [Module 04: Artifact Management](04-artifact-management.md)
