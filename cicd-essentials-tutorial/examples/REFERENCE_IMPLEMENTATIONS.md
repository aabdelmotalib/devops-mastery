# Example Dockerfile for Flask Backend

```dockerfile
# Stage 1: Build
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime (final image)
FROM python:3.11-slim

# Create non-root user for security
RUN useradd -m appuser

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /root/.local /home/appuser/.local
COPY app/ ./app/

# Set environment
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

EXPOSE 8000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"]
```

# Example CI Pipeline (GitHub Actions)

```yaml
name: CI

on:
  push:
    branches: [main, develop, feature/**]
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install linting tools
        working-directory: flask-backend-tutorial/backend
        run: |
          pip install pylint flake8
      
      - name: Pylint
        working-directory: flask-backend-tutorial/backend
        run: pylint app/ tests/ --exit-zero
      
      - name: Flake8
        working-directory: flask-backend-tutorial/backend
        run: flake8 app/ tests/ --max-line-length=100

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install security tools
        working-directory: flask-backend-tutorial/backend
        run: |
          pip install pip-audit bandit
      
      - name: Pip audit
        working-directory: flask-backend-tutorial/backend
        run: pip-audit
      
      - name: Bandit
        working-directory: flask-backend-tutorial/backend
        run: bandit -r app/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      
      - name: Install dependencies
        working-directory: flask-backend-tutorial/backend
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Unit tests
        working-directory: flask-backend-tutorial/backend
        run: pytest tests/unit/ -v --cov=app --cov-report=xml
      
      - name: Check coverage
        working-directory: flask-backend-tutorial/backend
        run: |
          coverage report --fail-under=80

  build:
    needs: [lint, security, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - uses: docker/setup-buildx-action@v2
      
      - name: Build Docker image
        run: |
          cd flask-backend-tutorial/backend
          docker build -t flask-app:${{ github.sha }} .
          docker tag flask-app:${{ github.sha }} flask-app:latest
      
      - name: Scan image
        run: |
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest image --exit-code 1 --severity HIGH,CRITICAL \
            flask-app:${{ github.sha }} || true
```

# Example CD Pipeline

```yaml
name: CD

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to staging
        run: |
          # Pull artifact
          docker pull flask-app:${{ github.sha }}
          
          # Tag for staging
          docker tag flask-app:${{ github.sha }} flask-app:staging
          
          # Deploy (example using docker-compose)
          docker-compose -f docker-compose.staging.yml up -d
      
      - name: Smoke tests
        run: |
          sleep 5  # Wait for app to start
          curl -f http://localhost:8000/health || exit 1
          curl -f http://localhost:8000/api/users || exit 1

  approve-production:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Approval
        run: echo "Waiting for manual approval..."

  deploy-production:
    needs: approve-production
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy blue-green
        run: |
          # This is a simplified example
          # In reality, you'd implement proper blue-green:
          # 1. Deploy new version to "green"
          # 2. Run tests on green
          # 3. Switch traffic from blue to green
          # 4. Keep blue running for rollback
          
          docker pull flask-app:${{ github.sha }}
          docker-compose -f docker-compose.prod.yml up -d
      
      - name: Verify production
        run: |
          sleep 10
          curl -f http://api.production.example.com/health || exit 1
```

# Example Terraform Module (Compute)

```hcl
# modules/compute/main.tf

variable "name" {
  type = string
}

variable "environment" {
  type = string
}

variable "instance_count" {
  type    = number
  default = 1
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "vpc_id" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

resource "aws_instance" "app" {
  count           = var.instance_count
  ami             = data.aws_ami.ubuntu.id
  instance_type   = var.instance_type
  subnet_id       = var.subnet_ids[count.index % length(var.subnet_ids)]
  security_groups = [aws_security_group.app.id]

  user_data = base64encode(file("${path.module}/init.sh"))

  tags = {
    Name        = "${var.name}-${var.environment}-${count.index + 1}"
    Environment = var.environment
  }
}

resource "aws_security_group" "app" {
  name        = "${var.name}-${var.environment}-sg"
  description = "Security group for ${var.name} app"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name}-${var.environment}-sg"
  }
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

output "instance_ids" {
  value = aws_instance.app[*].id
}

output "private_ips" {
  value = aws_instance.app[*].private_ip
}

output "security_group_id" {
  value = aws_security_group.app.id
}
```
