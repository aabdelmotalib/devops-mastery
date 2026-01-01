# Module 7: Docker Compose

## Why Docker Compose Exists

Running multi-container applications with individual `docker run` commands is error-prone:

```bash
# Without Compose (error-prone, order-dependent)
docker network create mynet
docker run -d --network mynet --name db postgres
docker run -d --network mynet --name redis redis
docker run -d --network mynet --name api \
  -e DATABASE_URL=postgresql://db:5432/mydb \
  -e REDIS_URL=redis://redis:6379 \
  -p 8000:8000 \
  myapi:1.0
docker run -d --network mynet --name frontend \
  -e API_URL=http://api:8000 \
  -p 80:80 \
  myfrontend:1.0
```

This requires:
- Manual network creation
- Correct startup order
- Environment variable management
- Port mapping coordination

**Docker Compose solves this with a declarative YAML file.**

## docker-compose.yml: The Configuration File

Compose uses YAML to define entire applications.

```yaml
version: '3.8'

services:
  database:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  api:
    image: myapi:1.0
    depends_on:
      database:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://database:5432/mydb
      REDIS_URL: redis://redis:6379
    ports:
      - "8000:8000"

  frontend:
    image: myfrontend:1.0
    depends_on:
      - api
    environment:
      API_URL: http://api:8000
    ports:
      - "80:80"

volumes:
  postgres_data:
  redis_data:
```

One command runs everything:

```bash
docker-compose up
# Starts all services in correct order
# Creates network automatically
# Manages volumes
# Shows consolidated logs
```

## Compose File Structure

### Services

Each service is a container.

```yaml
services:
  web:
    image: nginx:latest              # Image to use
    build:
      context: ./app                 # Or build from Dockerfile
      dockerfile: Dockerfile
    container_name: my-web           # Custom container name
    ports:
      - "80:80"                      # Port mapping
      - "443:443"
    volumes:
      - ./src:/app                   # Bind mount
      - web-data:/var/www            # Named volume
    environment:
      - APP_ENV=production           # Environment variables
      - LOG_LEVEL=info
    depends_on:                       # Startup order
      - database
      - cache
    networks:
      - frontend                     # Custom networks
      - backend
    restart_policy:
      condition: unless-stopped      # Restart policy
      max_retries: 5
    command: nginx -g "daemon off;"  # Override CMD
    entrypoint: /app/start.sh        # Override ENTRYPOINT
    user: 1000                       # Run as user
    working_dir: /app                # WORKDIR
    cap_drop:                        # Security
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost"]
      interval: 30s
      timeout: 3s
      retries: 3
```

### Networks

Define custom networks.

```yaml
networks:
  frontend:                          # Default bridge
  backend:
    driver: bridge                   # Explicit driver
  overlay:
    driver: overlay
```

### Volumes

Define named volumes.

```yaml
volumes:
  db_data:                           # Simple
  backup_data:
    driver: local                    # With options
    driver_opts:
      type: tmpfs
      device: tmpfs
```

## Running Compose Applications

### Basic Commands

```bash
# Start services
docker-compose up
# Starts all services, shows logs

# In background
docker-compose up -d
# Detached mode

# Stop services
docker-compose down
# Stops and removes containers, keeps volumes

# Restart
docker-compose restart
docker-compose restart web
# Restart specific service

# View logs
docker-compose logs
docker-compose logs -f web
# Follow logs from web service

# Execute command
docker-compose exec web bash
# Interactive shell in web container

# Scale service
docker-compose up -d --scale web=3
# Run 3 instances of web service
```

### Compose Project Name

Compose automatically names resources with project name.

```bash
# In directory with docker-compose.yml
docker-compose up
# Project name = directory name (e.g., "myproject")

# Created resources:
# - Container: myproject-web-1, myproject-api-1
# - Network: myproject-frontend, myproject-backend
# - Volumes: myproject-db_data

# Or specify project name
docker-compose -p production up
# Resources named: production-web-1, etc.

# Check running projects
docker-compose ps

# View all projects (complex query)
docker ps --format "table {{.Names}}"
# Shows all containers from all projects
```

## Service Dependencies

### depends_on: Startup Order

```yaml
services:
  database:
    image: postgres:15
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 5s

  api:
    image: myapi:1.0
    depends_on:
      database:
        condition: service_healthy
      # service_healthy: wait for health check
      # service_started: wait for container to start (default)
      # service_completed_successfully: wait for successful exit

  frontend:
    image: myfrontend:1.0
    depends_on:
      - api
      # Simple list: start after, don't wait for health
```

**Important:** Compose waits for dependency startup, but **doesn't wait for service readiness**. The application must handle unavailable dependencies.

```yaml
# This is NOT recommended:
api:
  depends_on:
    - database

# Better: use health checks and retry logic
api:
  depends_on:
    database:
      condition: service_healthy
  environment:
    - DATABASE_RETRY_ATTEMPTS=10
```

## Environment Management

### Environment Variables

```yaml
services:
  app:
    environment:
      - APP_ENV=production
      - LOG_LEVEL=info
      - DATABASE_HOST=database
      - DATABASE_PORT=5432

    # Or from file
    env_file:
      - .env
      - .env.production
```

Environment file (.env):

```
APP_ENV=production
DATABASE_PASSWORD=secret
API_SECRET=xxxxx
LOG_LEVEL=debug
```

### Variable Substitution

Compose substitutes ${VAR} with environment values.

```yaml
services:
  database:
    image: postgres:${POSTGRES_VERSION}
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - ${DATA_PATH}:/var/lib/postgresql/data
```

Usage:

```bash
# Set variables before compose
export POSTGRES_VERSION=15
export DB_PASSWORD=secret
export DATA_PATH=/data/postgres

docker-compose up

# Or in .env file in same directory
echo "POSTGRES_VERSION=15" > .env
echo "DB_PASSWORD=secret" >> .env

docker-compose up
# Automatically reads .env
```

## Multi-Environment Composition

Use multiple Compose files for different environments.

```bash
# Base configuration
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  database:
    image: postgres:15
    volumes:
      - db_data:/var/lib/postgresql/data
volumes:
  db_data:
EOF

# Development overrides
cat > docker-compose.dev.yml << 'EOF'
services:
  database:
    environment:
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
EOF

# Production overrides
cat > docker-compose.prod.yml << 'EOF'
services:
  database:
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart_policy:
      condition: unless-stopped
EOF

# Compose them together
docker-compose up                                    # base + dev
docker-compose -f docker-compose.yml \
  -f docker-compose.prod.yml up                    # base + prod
```

## Real-World Example: Full Stack Application

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: myapp-database
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "appuser"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    container_name: myapp-cache
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
    networks:
      - backend

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: myapp-api
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://appuser:${DB_PASSWORD}@postgres:5432/myapp
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      APP_ENV: ${APP_ENV}
      LOG_LEVEL: ${LOG_LEVEL}
      SECRET_KEY: ${SECRET_KEY}
    ports:
      - "${API_PORT}:8000"
    volumes:
      - api_logs:/var/log/myapp
    restart_policy:
      condition: unless-stopped
      max_retries: 3
    networks:
      - backend
      - frontend

  nginx:
    image: nginx:alpine
    container_name: myapp-web
    depends_on:
      - api
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    networks:
      - frontend

volumes:
  postgres_data:
  redis_data:
  api_logs:

networks:
  frontend:
  backend:
```

## Compose Anti-Patterns

### Anti-Pattern 1: No Health Checks

```yaml
# BAD
services:
  api:
    depends_on:
      - database
    # API might start before database is ready
    # Will crash trying to connect
```

```yaml
# GOOD
services:
  database:
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 5s
  api:
    depends_on:
      database:
        condition: service_healthy
    # Waits for actual readiness
```

### Anti-Pattern 2: Running as Root

```yaml
# BAD
services:
  app:
    image: myapp:1.0
    # Runs as root (default)
```

```yaml
# GOOD
services:
  app:
    image: myapp:1.0
    user: 1000
    # Or in Dockerfile: USER appuser
```

### Anti-Pattern 3: No Resource Limits

```yaml
# BAD
services:
  app:
    image: myapp:1.0
    # Can consume unlimited resources
```

```yaml
# GOOD
services:
  app:
    image: myapp:1.0
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Anti-Pattern 4: Loose Dependencies

```yaml
# BAD
services:
  api:
    depends_on:
      - database
    # Starts immediately, might fail

  background_worker:
    depends_on:
      - api
    # If api fails, worker starts anyway
```

### Anti-Pattern 5: Secrets in Compose File

```yaml
# BAD
services:
  database:
    environment:
      POSTGRES_PASSWORD: mysecret123
```

```yaml
# GOOD
services:
  database:
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}

# Store in .env (add to .gitignore)
# Or Docker secrets (Swarm mode)
# Or external secret management
```

---

## Practice: Exam Questions

1. **What is the primary purpose of docker-compose.yml?**
   - A) Build Docker images
   - B) Define multi-container applications declaratively
   - C) Replace Dockerfiles
   - D) Manage registries

2. **What does `depends_on` with `condition: service_healthy` do?**
   - A) Requires health check to pass before starting
   - B) Waits for container to start (not for readiness)
   - C) Ensures container never crashes
   - D) Automatically creates health checks

3. **What network do services in docker-compose automatically get?**
   - A) Default bridge network
   - B) Host network
   - C) Custom bridge network per project
   - D) No network (must specify)

4. **How do you specify environment variables in compose?**
   - A) Only in image Dockerfile
   - B) Using `environment:` section or `env_file:`
   - C) Must pass as `docker-compose run` arguments
   - D) Can't use environment variables in compose

5. **What happens to volumes when you run `docker-compose down`?**
   - A) Volumes are deleted
   - B) Volumes persist (containers are deleted)
   - C) Depends on the driver
   - D) Volumes are backed up

---

## Hands-On Labs

### Lab 1: Basic Compose Application

**Objective:** Write and run a multi-service application.

```bash
mkdir compose-lab && cd compose-lab

# Create simple Python app
cat > app.py << 'EOF'
from flask import Flask
import redis
import os
from psycopg2 import connect

app = Flask(__name__)

@app.route('/health')
def health():
    return {'status': 'ok'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

# Create docker-compose.yml
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: myapp
    healthcheck:
      test: ["CMD", "pg_isready"]
      interval: 5s
  
  cache:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
  
  api:
    build: .
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres:password@db:5432/myapp
      REDIS_URL: redis://cache:6379
    ports:
      - "5000:5000"
EOF

# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
RUN pip install flask redis psycopg2-binary
COPY app.py /app/
WORKDIR /app
CMD ["python3", "app.py"]
EOF

# Run compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs api

# Test API
curl localhost:5000/health
# {"status":"ok"}

# Clean up
docker-compose down
```

**What you're observing:**
- Compose creates all services with one command
- Services communicate by name (db, cache)
- Health checks control startup order
- One down command stops everything

### Lab 2: Multi-File Compose for Environments

**Objective:** Use multiple compose files for dev and prod.

```bash
mkdir multi-env && cd multi-env

# Base compose file
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  web:
    image: nginx:alpine
    ports:
      - "80:80"
  database:
    image: postgres:15-alpine
    volumes:
      - db_data:/var/lib/postgresql/data
volumes:
  db_data:
EOF

# Development overrides
cat > docker-compose.dev.yml << 'EOF'
services:
  web:
    volumes:
      - ./src:/usr/share/nginx/html
  database:
    environment:
      POSTGRES_PASSWORD: dev
    ports:
      - "5432:5432"
EOF

# Production overrides
cat > docker-compose.prod.yml << 'EOF'
services:
  web:
    restart_policy:
      condition: unless-stopped
  database:
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    restart_policy:
      condition: unless-stopped
EOF

# Start development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

docker-compose ps
# Shows web and database with dev settings

docker-compose down

# Start production (with env vars)
export DB_PASSWORD=prod-secret
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

docker-compose ps
# Shows web and database with prod settings

docker-compose down
```

---

## Failure Scenario: Service Won't Start Due to Dependency

**Scenario:**
Your API service keeps restarting. Logs show: "Connection refused: cannot connect to database"

**Root cause:**
Compose started API before database was ready.

```yaml
# This just waits for container to start, not for service readiness
services:
  database:
    image: postgres:15
  api:
    depends_on:
      - database
    # API started while database still initializing
```

**Solution:**
```yaml
services:
  database:
    image: postgres:15
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
  
  api:
    depends_on:
      database:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://postgres@database:5432/mydb
    # Also add retry logic in app
```

Also implement retry logic in the application itself - compose only guarantees startup order, not that services are fully ready.

---

Next: [Module 8: Docker Security](08-docker-security.md)
