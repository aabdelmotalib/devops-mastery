# Module 0: Bash & YAML Fundamentals

This module covers the essential shell scripting and configuration knowledge you'll use throughout Docker and DevOps work. If you're already comfortable with Bash and YAML, skip to Module 1.

---

## Part 1: Bash Fundamentals

Bash (Bourne Again Shell) is the standard Linux shell. Understanding it is critical for:
- Running Docker commands
- Writing container entry scripts
- Debugging containerized applications
- DevOps automation

### 1.1 Basic Command Syntax

Every Bash command follows this pattern:

```bash
command [options] [arguments]

# Examples:
ls                      # List files
ls -la                  # List with options
ls -la /home            # List with option and argument
cd /path/to/dir         # Change directory
```

### 1.2 Navigating the Filesystem

```bash
# Print working directory
pwd
# Output: /home/user

# List files
ls                      # Current directory
ls -la                  # Long format, show hidden files
ls -R                   # Recursive (all subdirectories)

# Change directory
cd /etc                 # Absolute path
cd ..                   # Parent directory
cd ~                    # Home directory
cd -                    # Previous directory

# Make directory
mkdir my-folder         # Create folder
mkdir -p path/to/folder # Create all parent directories

# Remove directory
rmdir empty-folder      # Only removes empty folders
rm -rf folder-name      # Remove folder and contents (dangerous!)

# Show directory tree
tree /home/user         # If tree is installed
```

### 1.3 Working with Files

```bash
# Create empty file
touch filename.txt

# View file contents
cat file.txt            # Print entire file
head file.txt           # First 10 lines
tail file.txt           # Last 10 lines
tail -f file.txt        # Follow file (updates in real-time)

# Count lines, words, characters
wc -l file.txt          # Count lines
wc -c file.txt          # Count bytes
wc -w file.txt          # Count words

# Search within files
grep "search-term" file.txt         # Find lines containing term
grep -r "search-term" /directory    # Search recursively
grep -i "term" file.txt             # Case-insensitive search
grep -c "term" file.txt             # Count matching lines

# Find files
find /directory -name "*.txt"        # Find .txt files
find /directory -type f -size +10M  # Find files larger than 10MB
find /directory -name "file*"       # Find by pattern

# Copy, move, remove
cp file.txt copy.txt                # Copy file
cp -r folder/ backup/               # Copy directory recursively
mv file.txt new-location/           # Move/rename file
rm file.txt                         # Delete file
rm -rf folder/                      # Delete folder (careful!)
```

### 1.4 File Permissions

Understanding permissions is crucial for Docker and Linux security.

```bash
# View permissions
ls -l file.txt
# Output: -rw-r--r-- 1 user group 1024 Jan 2 10:00 file.txt
#         ^^^^^^^^^^
#         permissions

# Permission breakdown: -rw-r--r--
# First char: file type (- = file, d = directory, l = symlink)
# Next 3 chars: owner permissions (rw- = read, write, no execute)
# Next 3 chars: group permissions (r-- = read only)
# Last 3 chars: other permissions (r-- = read only)

# Change permissions (chmod)
chmod 755 script.sh              # rwxr-xr-x (common for scripts)
chmod 644 file.txt               # rw-r--r-- (common for files)
chmod +x script.sh               # Add execute permission
chmod -r filename                # Remove read permission

# Numeric permission breakdown:
# r = 4 (read)
# w = 2 (write)
# x = 1 (execute)
# So: 755 = 7(rwx) 5(r-x) 5(r-x)

# Change owner
chown user:group file.txt        # Change user and group
chown -R user:group /directory   # Recursive

# Change group
chgrp group file.txt
```

### 1.5 Environment Variables

Variables store values that can be used by commands and scripts.

```bash
# Set variable (no spaces around =)
ENVIRONMENT=production
APP_PORT=8080
DATABASE_URL="postgresql://localhost/db"

# Use variable (with $)
echo $ENVIRONMENT
# Output: production

echo $APP_PORT
# Output: 8080

# Common built-in variables
$HOME                   # User's home directory
$USER                   # Current user
$PWD                    # Current working directory
$PATH                   # Directories where commands are searched
$0                      # Script name
$1, $2, etc             # Script arguments
$@                      # All script arguments
$#                      # Number of arguments
$?                      # Exit status of last command

# Export variable (make it available to child processes)
export DATABASE_URL="postgresql://localhost/db"

# View all environment variables
env
printenv

# Set default value
${VARIABLE:-default_value}
# If VARIABLE is not set, use default_value

# Example in Docker context
docker run -e DATABASE_URL="postgres://localhost/db" my-app
# This sets an environment variable inside the container
```

### 1.6 Pipes and Redirection

Pipes and redirection connect commands together.

```bash
# Redirection operators
command > file.txt      # Write stdout to file (overwrite)
command >> file.txt     # Append stdout to file
command < input.txt     # Use file as stdin
command 2> errors.txt   # Redirect stderr to file
command &> output.txt   # Redirect both stdout and stderr

# Pipes (pass output of one command to another)
cat file.txt | grep "error"         # Pipe grep the file contents
ps aux | grep "python"              # Find Python processes
ls -la | wc -l                      # Count files
docker ps | grep "myapp"            # Find specific container

# Useful combinations
# Count lines in a file
cat large-file.txt | wc -l

# Search multiple files
grep -r "error" /logs | wc -l       # Count error occurrences

# Find and process
find /var/log -name "*.log" | xargs cat | grep "ERROR"
```

### 1.7 Control Flow: Conditionals and Loops

```bash
# IF statement
if [ $? -eq 0 ]; then
    echo "Last command succeeded"
else
    echo "Last command failed"
fi

# String comparison
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Production mode"
fi

# File checks
if [ -f /etc/passwd ]; then
    echo "File exists"
fi

if [ -d /home ]; then
    echo "Directory exists"
fi

if [ -z "$VARIABLE" ]; then
    echo "Variable is empty"
fi

# FOR loop
for i in 1 2 3 4 5; do
    echo "Iteration $i"
done

# FOR loop with command output
for file in $(ls *.txt); do
    echo "Processing $file"
done

# WHILE loop
count=0
while [ $count -lt 5 ]; do
    echo "Count: $count"
    count=$((count + 1))
done

# CASE statement (switch-like)
case $ENVIRONMENT in
    development)
        echo "Dev environment"
        ;;
    production)
        echo "Prod environment"
        ;;
    *)
        echo "Unknown environment"
        ;;
esac
```

### 1.8 Functions

Reusable blocks of code in Bash.

```bash
# Define a function
function greet() {
    echo "Hello, $1!"
}

# Or alternative syntax
greet() {
    local name=$1                   # local variable
    local greeting=${2:-"Hello"}    # default value
    echo "$greeting, $name!"
}

# Call function
greet "Alice"                       # Hello, Alice!
greet "Bob" "Hi"                    # Hi, Bob!

# Function with return value
is_running() {
    local container=$1
    if docker ps | grep -q $container; then
        return 0        # Success
    else
        return 1        # Failure
    fi
}

# Use function's return value
if is_running "myapp"; then
    echo "Container is running"
else
    echo "Container is stopped"
fi

# Function with output
get_port() {
    local container=$1
    docker inspect -f '{{.NetworkSettings.Ports}}' $container
}

PORT=$(get_port "myapp")
echo "App running on port: $PORT"
```

### 1.9 Useful Utilities for DevOps

```bash
# Process management
ps aux                              # List all processes
ps aux | grep "python"              # Find processes
top                                 # Real-time process monitor
kill 1234                           # Kill process by PID
pkill -f "python"                   # Kill by pattern

# System information
uname -a                            # System info
df -h                               # Disk usage
du -h /directory                    # Directory size
free -h                             # Memory usage
uptime                              # System uptime

# Network utilities
ifconfig                            # Network interfaces
ip addr                             # IP addresses
netstat -tuln                       # Open ports
ss -tuln                            # Open ports (newer)
curl http://localhost:8080          # Make HTTP request
curl -i http://localhost:8080       # With headers
curl -X POST -d "data" http://localhost:8080  # POST request
wget file-url                       # Download file

# Package management (Ubuntu/Debian)
apt update                          # Update package list
apt install package-name            # Install package
apt remove package-name             # Remove package
apt search package-name             # Search packages

# User and group management
whoami                              # Current user
sudo command                        # Run as root
sudo -l                             # List sudo permissions
adduser username                    # Add user
usermod -aG docker username         # Add user to group
```

### 1.10 Writing Bash Scripts

Create executable scripts to automate tasks.

```bash
#!/bin/bash
# Above line (shebang) tells system this is a Bash script

# Set error handling
set -e          # Exit on error
set -u          # Exit if undefined variable used
set -o pipefail # Exit if pipe command fails

# Variables
CONTAINER_NAME="myapp"
IMAGE_NAME="myapp:latest"
LOG_FILE="/var/log/deploy.log"

# Function to log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# Main script
log "Starting deployment..."

# Check if image exists
if docker inspect $IMAGE_NAME > /dev/null 2>&1; then
    log "Image found: $IMAGE_NAME"
else
    log "ERROR: Image not found: $IMAGE_NAME"
    exit 1
fi

# Stop existing container
if docker ps -a | grep -q $CONTAINER_NAME; then
    log "Stopping existing container..."
    docker stop $CONTAINER_NAME || true
    docker rm $CONTAINER_NAME || true
fi

# Start new container
log "Starting container..."
docker run -d \
    --name $CONTAINER_NAME \
    --restart always \
    -p 8080:8080 \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    log "Deployment successful!"
    exit 0
else
    log "Deployment failed!"
    exit 1
fi
```

Save as `deploy.sh`, then:
```bash
chmod +x deploy.sh      # Make executable
./deploy.sh             # Run script
bash deploy.sh          # Alternative
```

---

## Part 2: YAML Fundamentals

YAML (YAML Ain't Markup Language) is used extensively in:
- Docker Compose files (docker-compose.yml)
- Kubernetes manifests (deployment.yaml, service.yaml)
- CI/CD configuration (GitHub Actions, GitLab CI)
- Application configuration files

### 2.1 YAML Basics

YAML is a human-readable data format. Key principles:

1. **Whitespace matters** - Indentation defines structure (use 2 or 4 spaces, not tabs)
2. **Simple syntax** - Easier to read than JSON or XML
3. **Key-value pairs** - Basic building blocks

```yaml
# Key: value
name: Alice
age: 25
email: alice@example.com

# This is equivalent to JSON:
# {
#   "name": "Alice",
#   "age": 25,
#   "email": "alice@example.com"
# }
```

### 2.2 Data Types in YAML

```yaml
# Strings (no quotes needed)
name: Alice
message: Hello World

# Strings with quotes (use if containing special characters)
greeting: "Hello, World!"
path: "/home/user/file.txt"

# Numbers
port: 8080              # Integer
timeout: 3.14           # Float
count: 0x1F             # Hexadecimal

# Booleans
debug: true
enabled: false
running: yes
disabled: no

# Null
value: null
empty:                  # Also represents null

# Lists (sequences)
colors:
  - red
  - green
  - blue

# Or inline style
colors: [red, green, blue]

# Numbers in list
numbers:
  - 1
  - 2
  - 3

# Strings in list
names:
  - Alice
  - Bob
  - Charlie
```

### 2.3 Nested Structures

```yaml
# Nested objects (using indentation)
person:
  name: Alice
  age: 25
  contact:
    email: alice@example.com
    phone: 123-456-7890
  tags:
    - developer
    - team-lead

# This is equivalent to JSON:
# {
#   "person": {
#     "name": "Alice",
#     "age": 25,
#     "contact": {
#       "email": "alice@example.com",
#       "phone": "123-456-7890"
#     },
#     "tags": ["developer", "team-lead"]
#   }
# }
```

### 2.4 Special Characters and Escaping

```yaml
# Pipe (|) - preserves newlines (useful for scripts)
script: |
  #!/bin/bash
  echo "Hello"
  echo "World"

# Folded (>) - treats newlines as spaces
description: >
  This is a long
  description that spans
  multiple lines but will
  be converted to a single line.

# Escaped strings
message: "Line 1\nLine 2"  # Actual newline: \n, \t, etc.

# URLs and special characters in quotes
url: "https://example.com/path?param=value&other=123"
regex: "^[a-zA-Z0-9]+$"
```

### 2.5 Comments

```yaml
# This is a comment
name: Alice  # Inline comment

# Multi-line configuration
# This is a cluster configuration
# for production environment
environment: production
```

### 2.6 YAML for Docker Compose

Docker Compose uses YAML to define multi-container applications.

```yaml
version: '3.9'          # Docker Compose version

services:               # Define services (containers)
  web:                  # Service name
    image: myapp:latest # Docker image
    ports:              # Port mapping
      - "8080:8080"     # host:container
    environment:        # Environment variables
      DEBUG: "true"
      DATABASE_URL: "postgresql://db:5432/mydb"
    volumes:            # Volume mounts
      - ./app:/app                    # Bind mount
      - data:/data                    # Named volume
    depends_on:         # Start order
      - db
    restart: always     # Restart policy

  db:                   # Another service
    image: postgres:14
    environment:
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: mydb
    volumes:
      - db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:                # Define named volumes
  data:
  db_data:

networks:               # Define networks
  default:
    driver: bridge
```

### 2.7 YAML for Kubernetes (Preview)

Kubernetes manifests use YAML to define deployments.

```yaml
apiVersion: v1        # API version
kind: Pod             # Type of resource
metadata:
  name: myapp
  labels:
    app: myapp

spec:                 # Specification
  containers:
    - name: web
      image: myapp:latest
      ports:
        - containerPort: 8080
      environment:
        - name: DATABASE_URL
          value: "postgres://db:5432/mydb"
      resources:
        requests:
          memory: "256Mi"
          cpu: "250m"
        limits:
          memory: "512Mi"
          cpu: "500m"
      livenessProbe:
        httpGet:
          path: /health
          port: 8080
        initialDelaySeconds: 30
```

### 2.8 YAML Best Practices

```yaml
# ❌ DON'T: Inconsistent indentation
services:
  web:
    image: myapp
      ports:
        - "8080:8080"

# ✅ DO: Consistent indentation (2 spaces)
services:
  web:
    image: myapp
    ports:
      - "8080:8080"

# ❌ DON'T: Ambiguous types
database:
  port: 5432          # Integer
  timeout: 30         # Could be seconds (unclear)

# ✅ DO: Clear naming
database:
  port: 5432
  timeout_seconds: 30

# ❌ DON'T: Mixing list styles
tags:
  - python
  - [docker, compose]

# ✅ DO: Consistent list style
tags:
  - python
  - docker
  - compose

# ✅ DO: Use comments for complex configurations
# Database connection settings
# Supports primary and replica configuration
database:
  primary:
    host: prod-db-1.example.com
    port: 5432
  replica:
    host: prod-db-2.example.com
    port: 5432
```

### 2.9 YAML Validation

```bash
# Validate YAML syntax
python -m yamllint docker-compose.yml

# Install yamllint if needed
pip install yamllint

# Or use online validators
# https://www.yamllint.com/

# Or in Python
python3 << 'EOF'
import yaml

try:
    with open('docker-compose.yml', 'r') as f:
        config = yaml.safe_load(f)
    print("YAML is valid!")
    print(config)
except yaml.YAMLError as e:
    print(f"YAML error: {e}")
EOF
```

### 2.10 Common YAML Mistakes

```yaml
# ❌ MISTAKE 1: Using tabs instead of spaces
services:
	web:          # This is a TAB - INVALID
		image: myapp

# ✅ CORRECT:
services:
  web:            # These are SPACES
    image: myapp

# ❌ MISTAKE 2: Wrong indentation level
services:
web:              # Not indented enough
  image: myapp

# ✅ CORRECT:
services:
  web:            # Properly indented
    image: myapp

# ❌ MISTAKE 3: Quotes not closed
password: "my-secret-password
# Missing closing quote!

# ✅ CORRECT:
password: "my-secret-password"

# ❌ MISTAKE 4: Colon without space in values
ports: ["8080:8080"]    # Ambiguous

# ✅ CORRECT:
ports:
  - "8080:8080"

# ❌ MISTAKE 5: Undefined anchors
defaults: &defaults
  timeout: 30

service1:
  <<: *defaults    # This works

service2:
  <<: *wrong_anchor  # ERROR: undefined anchor

# ✅ CORRECT: Use defined anchors
defaults: &defaults
  timeout: 30

service1:
  <<: *defaults    # Correct
  
service2:
  <<: *defaults    # Correct
```

---

## Part 3: Common Bash & YAML Patterns for Docker/DevOps

### 3.1 Health Check Script (Bash)

```bash
#!/bin/bash
# health-check.sh

# Check if a service is healthy
SERVICE_URL="http://localhost:8080/health"
MAX_RETRIES=5
RETRY_INTERVAL=2

attempt=0
while [ $attempt -lt $MAX_RETRIES ]; do
    response=$(curl -s -o /dev/null -w "%{http_code}" $SERVICE_URL)
    
    if [ $response -eq 200 ]; then
        echo "Health check passed"
        exit 0
    fi
    
    attempt=$((attempt + 1))
    echo "Health check failed. Attempt $attempt/$MAX_RETRIES"
    sleep $RETRY_INTERVAL
done

echo "Health check failed after $MAX_RETRIES attempts"
exit 1
```

### 3.2 Docker Compose with Environment (YAML)

```yaml
version: '3.9'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: myapp:${VERSION:-latest}
    env_file:
      - .env.local
      - .env.${ENVIRONMENT:-development}
    environment:
      APP_ENV: ${ENVIRONMENT:-development}
      DEBUG: ${DEBUG:-false}
      LOG_LEVEL: ${LOG_LEVEL:-info}
    ports:
      - "${APP_PORT:-8080}:8080"
    volumes:
      - ./src:/app/src      # Development mount
      - app_data:/data      # Data volume
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:${POSTGRES_VERSION:-14}
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
      POSTGRES_DB: ${DB_NAME:-myapp}
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  app_data:
  db_data:
```

### 3.3 Multi-Stage Dockerfile (Bash as entry point)

```bash
#!/bin/bash
# entrypoint.sh

set -e

echo "Starting application..."

# Wait for database
while ! curl -s http://db:5432 > /dev/null; do
    echo "Waiting for database..."
    sleep 1
done

echo "Database is ready!"

# Run migrations
if [ "$RUN_MIGRATIONS" = "true" ]; then
    echo "Running migrations..."
    alembic upgrade head
fi

# Start application
echo "Starting app server..."
exec python app.py
```

---

## Quick Reference

### Essential Bash Commands

```bash
# Navigation
pwd, cd, ls, mkdir, rmdir

# Files
cat, head, tail, touch, cp, mv, rm, find, grep

# Permissions
chmod, chown, ls -l

# System
ps, top, df, du, uptime, ifconfig

# Networking
curl, wget, netstat, ping, ssh

# Variables & Scripting
export, echo, if, for, function
```

### YAML Cheat Sheet

```yaml
# Key value
name: value

# List
items:
  - item1
  - item2

# Nested object
config:
  setting1: value1
  setting2: value2

# Multiline string
description: |
  Line 1
  Line 2

# Comments
# This is a comment
```

---

## What's Next?

Now that you understand:
- ✅ **Bash basics**: Commands, scripting, automation
- ✅ **YAML structure**: Files, syntax, best practices
- ✅ **Common patterns**: Health checks, environment variables

You're ready for **Module 1: Container Fundamentals**, where we'll apply these skills with Docker.

### Checklist Before Module 1

- [ ] Comfortable with basic Bash commands (ls, cd, mkdir, etc.)
- [ ] Can write a simple Bash script with functions
- [ ] Understand YAML indentation and structure
- [ ] Can read and write basic docker-compose.yml files
- [ ] Know how to use environment variables in scripts

---

## References

- **Bash Guide**: https://mywiki.wooledge.org/BashGuide
- **Bash Manual**: https://www.gnu.org/software/bash/manual/
- **YAML Spec**: https://yaml.org/
- **YAML Validator**: https://www.yamllint.com/
- **Linux Command Reference**: https://linux.die.net/man/

---

**Ready to dive in?** Head to [Module 1: Container Fundamentals](01-container-fundamentals.md)
