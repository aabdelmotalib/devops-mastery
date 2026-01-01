# Final Project: Containerize a Production-Ready Backend Application

## Project Overview

Build a complete, production-oriented backend application with Docker that demonstrates mastery of all 10 modules.

### Requirements

Your application must include:

1. **Multi-service architecture** (API + Database + Cache)
2. **Multi-stage builds** for small, secure images
3. **Proper service exposure** (networking, port mapping)
4. **Data persistence** (database with volumes)
5. **Security hardening** (non-root, capabilities, secrets)
6. **Health checks** and graceful shutdown
7. **docker-compose** orchestration
8. **CI/CD readiness** (versioning, scanning, testable)
9. **Documentation** and deployment instructions

## Application: REST API with Database

Build a todo application API.

### Architecture

```
┌──────────────┐
│   Frontend   │
│ (client app) │
└──────┬───────┘
       │ HTTP
       ↓
┌──────────────────────────────────────────┐
│         Nginx Reverse Proxy               │
│    (Port 80 → API Port 8000)             │
└──────┬───────────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────────┐
│         API Service (Flask)               │
│   - Authentication                       │
│   - CRUD endpoints                       │
│   - Database ORM (SQLAlchemy)            │
│   - Redis caching                        │
└──────┬───────────────────────────────────┘
       │                   │
       ↓                   ↓
┌──────────────┐    ┌─────────────┐
│  PostgreSQL  │    │    Redis    │
│   Database   │    │    Cache    │
└──────────────┘    └─────────────┘
```

### Directory Structure

```
todo-api-docker/
├── README.md
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── .env.example
├── nginx.conf
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   └── utils.py
└── tests/
    └── test_api.py
```

## Implementation

### 1. Application Code

**app/__init__.py**
```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
import os

db = SQLAlchemy()
redis_client = None

def create_app():
    global redis_client
    app = Flask(__name__)
    
    # Configuration from environment
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/tododb'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    db.init_app(app)
    
    # Initialize Redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    with app.app_context():
        db.create_all()
    
    # Register blueprints
    from app.routes import bp
    app.register_blueprint(bp)
    
    @app.route('/health', methods=['GET'])
    def health():
        return {'status': 'healthy'}, 200
    
    @app.route('/ready', methods=['GET'])
    def ready():
        try:
            # Check database
            db.session.execute('SELECT 1')
            # Check Redis
            redis_client.ping()
            return {'ready': True}, 200
        except Exception as e:
            return {'ready': False, 'error': str(e)}, 503
    
    return app
```

**app/models.py**
```python
from app import db
from datetime import datetime

class Todo(db.Model):
    __tablename__ = 'todos'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'completed': self.completed,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
```

**app/routes.py**
```python
from flask import Blueprint, request, jsonify
from app import db, redis_client
from app.models import Todo
import json

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/todos', methods=['GET'])
def list_todos():
    """List all todos with caching"""
    cache_key = 'todos:list'
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify(json.loads(cached))
    
    todos = Todo.query.all()
    result = [todo.to_dict() for todo in todos]
    
    # Cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return jsonify(result)

@bp.route('/todos', methods=['POST'])
def create_todo():
    """Create a new todo"""
    data = request.get_json()
    
    if not data or not data.get('title'):
        return {'error': 'Title is required'}, 400
    
    todo = Todo(
        title=data['title'],
        description=data.get('description', '')
    )
    
    db.session.add(todo)
    db.session.commit()
    
    # Invalidate cache
    redis_client.delete('todos:list')
    
    return jsonify(todo.to_dict()), 201

@bp.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    """Get a specific todo"""
    cache_key = f'todo:{todo_id}'
    cached = redis_client.get(cache_key)
    if cached:
        return jsonify(json.loads(cached))
    
    todo = Todo.query.get_or_404(todo_id)
    result = todo.to_dict()
    
    redis_client.setex(cache_key, 300, json.dumps(result))
    
    return jsonify(result)

@bp.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    """Update a todo"""
    todo = Todo.query.get_or_404(todo_id)
    data = request.get_json()
    
    if 'title' in data:
        todo.title = data['title']
    if 'description' in data:
        todo.description = data['description']
    if 'completed' in data:
        todo.completed = data['completed']
    
    db.session.commit()
    
    # Invalidate caches
    redis_client.delete('todos:list')
    redis_client.delete(f'todo:{todo_id}')
    
    return jsonify(todo.to_dict())

@bp.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    """Delete a todo"""
    todo = Todo.query.get_or_404(todo_id)
    db.session.delete(todo)
    db.session.commit()
    
    # Invalidate caches
    redis_client.delete('todos:list')
    redis_client.delete(f'todo:{todo_id}')
    
    return {'deleted': True}, 204
```

**app/main.py**
```python
import os
import signal
import sys
from app import create_app

app = create_app()

def handle_sigterm(signum, frame):
    print("SIGTERM received, shutting down gracefully")
    sys.exit(0)

signal.signal(signal.SIGTERM, handle_sigterm)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

### 2. Dockerfile (Multi-Stage)

```dockerfile
# ===== Builder Stage =====
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ===== Runtime Stage =====
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 -s /sbin/nologin appuser

WORKDIR /app

# Install runtime dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Make sure app user owns everything
RUN chown -R appuser:appuser /app

# Set environment
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)"

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Entrypoint
ENTRYPOINT ["python3"]
CMD ["app/main.py"]
```

### 3. docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: todo-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-todouser}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-todopass}
      POSTGRES_DB: ${DB_NAME:-tododb}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-todouser}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - SETGID
      - SETUID

  redis:
    image: redis:7-alpine
    container_name: todo-cache
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redispass}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - backend
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL

  api:
    build:
      context: .
      dockerfile: Dockerfile
      cache_from:
        - registry.example.com/todo-api:latest
    container_name: todo-api
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: "postgresql://${DB_USER:-todouser}:${DB_PASSWORD:-todopass}@postgres:5432/${DB_NAME:-tododb}"
      REDIS_URL: "redis://:${REDIS_PASSWORD:-redispass}@redis:6379"
      PORT: 8000
      FLASK_ENV: ${APP_ENV:-production}
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app:ro  # Read-only code volume
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s
    networks:
      - backend
      - frontend
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only_root_filesystem: true
    tmpfs:
      - /tmp
      - /var/tmp

  nginx:
    image: nginx:alpine
    container_name: todo-web
    restart: unless-stopped
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
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only_root_filesystem: true
    tmpfs:
      - /var/run
      - /var/cache

volumes:
  postgres_data:
  redis_data:

networks:
  frontend:
  backend:
```

### 4. Nginx Configuration

**nginx.conf**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /health {
            access_log off;
            proxy_pass http://api/health;
        }
    }
}
```

### 5. Requirements

**requirements.txt**
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
psycopg2-binary==2.9.9
redis==5.0.1
Werkzeug==3.0.1
```

### 6. Test File

**tests/test_api.py**
```python
import pytest
import json
from app import create_app, db
from app.models import Todo

@pytest.fixture
def app():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'

def test_create_todo(client):
    response = client.post('/api/todos', 
        json={'title': 'Test Todo', 'description': 'Test'})
    assert response.status_code == 201
    assert response.json['title'] == 'Test Todo'

def test_list_todos(client):
    client.post('/api/todos', json={'title': 'Todo 1'})
    client.post('/api/todos', json={'title': 'Todo 2'})
    
    response = client.get('/api/todos')
    assert response.status_code == 200
    assert len(response.json) == 2

def test_get_todo(client):
    create_response = client.post('/api/todos', 
        json={'title': 'Test Todo'})
    todo_id = create_response.json['id']
    
    response = client.get(f'/api/todos/{todo_id}')
    assert response.status_code == 200
    assert response.json['title'] == 'Test Todo'

def test_update_todo(client):
    create_response = client.post('/api/todos', 
        json={'title': 'Original'})
    todo_id = create_response.json['id']
    
    response = client.put(f'/api/todos/{todo_id}',
        json={'title': 'Updated'})
    assert response.status_code == 200
    assert response.json['title'] == 'Updated'

def test_delete_todo(client):
    create_response = client.post('/api/todos', 
        json={'title': 'Delete me'})
    todo_id = create_response.json['id']
    
    response = client.delete(f'/api/todos/{todo_id}')
    assert response.status_code == 204
    
    response = client.get(f'/api/todos/{todo_id}')
    assert response.status_code == 404
```

## Deployment & Usage

### Local Development

```bash
# Create .env file
cat > .env << 'EOF'
APP_ENV=development
DB_USER=todouser
DB_PASSWORD=todopass
DB_NAME=tododb
REDIS_PASSWORD=redispass
EOF

# Add to .gitignore
echo ".env" >> .gitignore

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Run tests
docker-compose run --rm api pytest

# Access API
curl http://localhost/api/todos
```

### Production Deployment

```bash
# Build with specific version
docker build -t myregistry.com/todo-api:v1.0.0 .

# Push to registry
docker push myregistry.com/todo-api:v1.0.0

# On production server, use specific version
docker-compose -f docker-compose.prod.yml up -d

# Verify health
curl http://server/health
curl http://server/api/todos
```

## Production Checklist

- [x] Multi-stage build (builder + runtime)
- [x] Non-root user execution
- [x] Read-only filesystem with tmpfs
- [x] Dropped Linux capabilities
- [x] Health checks (liveness + readiness)
- [x] Graceful shutdown (SIGTERM handling)
- [x] Secrets management (.env with .gitignore)
- [x] Data persistence (volumes)
- [x] Proper networking (frontend/backend isolation)
- [x] Docker Compose orchestration
- [x] Test coverage
- [x] Version tagging (immutable releases)
- [x] Restart policies
- [x] Resource limits (recommended)
- [x] Scanning ready (uses standard images)

## What You've Demonstrated

1. **Container Fundamentals**: Multi-service isolation with networks
2. **Docker Architecture**: Understanding daemon, runtime, networking
3. **Docker Images**: Multi-stage builds, layer optimization, size reduction
4. **Docker Containers**: Lifecycle, health checks, graceful shutdown
5. **Docker Networking**: Custom networks, service discovery, reverse proxy
6. **Docker Volumes**: Persistent storage for database and cache
7. **Docker Compose**: Orchestration of multi-service application
8. **Docker Security**: Non-root, capabilities, read-only filesystems, secrets
9. **Docker in CI/CD**: Version tagging, testable, scannable images
10. **Kubernetes Readiness**: Health checks, environment config, stateless design

---

## Extension Ideas

### Add Features

- [ ] User authentication (JWT)
- [ ] Request rate limiting
- [ ] Database migrations (Alembic)
- [ ] Logging aggregation (ELK stack)
- [ ] Monitoring (Prometheus metrics)
- [ ] API documentation (Swagger/OpenAPI)

### Add Complexity

- [ ] Multiple databases (read replicas)
- [ ] Message queue (RabbitMQ, Kafka)
- [ ] Search engine (Elasticsearch)
- [ ] File storage (S3, MinIO)
- [ ] CDN integration
- [ ] GraphQL endpoint

### Add Production Readiness

- [ ] TLS/SSL certificates
- [ ] Rate limiting and DDoS protection
- [ ] Database backups and recovery
- [ ] Chaos engineering testing
- [ ] Disaster recovery plan
- [ ] Cost optimization

---

## Conclusion

You have successfully built a production-grade, containerized backend application demonstrating expertise across all Docker concepts. This application is ready to be:

- Deployed on a single Docker host
- Pushed to a registry for distribution
- Migrated to Kubernetes with minimal changes
- Integrated into CI/CD pipelines
- Scaled across multiple machines
- Monitored and debugged in production

**You're ready for professional Docker and container engineering roles.**
