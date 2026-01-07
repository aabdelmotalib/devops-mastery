# Advanced Ansible: Configuration Management & Orchestration

## Overview

**Ansible** is agentless configuration management that uses SSH to configure servers. While Terraform builds infrastructure, Ansible configures what runs on that infrastructure. This module covers playbooks, roles, inventory management, and production patterns.

## Mental Model

```
Infrastructure Lifecycle:

Stage 1: BUILD (Terraform)
┌─────────────────────────┐
│ infrastructure-as-code  │
│ main.tf + variables.tf  │
│                         │
│ Output:                 │
│ • EC2 instances (raw)   │
│ • Security groups       │
│ • Load balancers        │
│ • Databases             │
│                         │
│ State: Clean slate      │
│ OS: Running but empty   │
└─────────────────────────┘
              ↓
Stage 2: CONFIGURE (Ansible)
┌─────────────────────────┐
│ configuration-as-code   │
│ playbooks + roles       │
│                         │
│ Actions:                │
│ • Install packages      │
│ • Configure services    │
│ • Deploy applications   │
│ • Set up logging        │
│ • Configure monitoring  │
│                         │
│ State: Ready to serve   │
│ OS: Running with apps   │
└─────────────────────────┘
              ↓
Stage 3: VALIDATE (Testing)
┌─────────────────────────┐
│ Verify configuration    │
│ ansible-test            │
│ Health checks           │
│ Smoke tests             │
└─────────────────────────┘

Typical Workflow:

1. Terraform apply
   ↓ (servers created)
2. Ansible playbook run
   ↓ (servers configured)
3. Application deployed
   ↓ (services running)
4. Monitoring alerts
   ↓ (if issues detected)
5. Ansible adjusts config
   ↓ (remediation)
6. Back to normal

Why Ansible wins:
✅ Agentless (SSH only)
✅ YAML-based (human readable)
✅ Idempotent (safe to run multiple times)
✅ Fast (parallel execution)
✅ Huge community (40,000+ modules)
```

## Core Concepts

### 1. Playbook Structure

```yaml
---
# Simple playbook to install and start Apache
- name: Configure web servers
  hosts: web_servers  # Target group from inventory
  become: yes         # Run as sudo
  
  vars:
    apache_port: 80
    app_version: "1.0.0"
  
  tasks:
    - name: Install Apache
      package:
        name: apache2
        state: present
      when: ansible_os_family == "Debian"
    
    - name: Start Apache service
      service:
        name: apache2
        state: started
        enabled: yes
    
    - name: Deploy application
      copy:
        src: /local/app.tar.gz
        dest: /opt/app.tar.gz
      notify: restart apache
  
  handlers:
    - name: restart apache
      service:
        name: apache2
        state: restarted
```

### 2. Inventory Management

```ini
# inventory.ini - Define target servers

[web_servers]
web1.example.com ansible_user=ec2-user
web2.example.com ansible_user=ec2-user
web3.example.com ansible_user=ec2-user

[db_servers]
db1.example.com ansible_user=ubuntu
db2.example.com ansible_user=ubuntu

[all:vars]
# Variables for all servers
ansible_ssh_private_key_file=~/.ssh/id_rsa
ansible_python_interpreter=/usr/bin/python3

[web_servers:vars]
# Variables for web servers only
apache_port=80
app_env=production

[db_servers:vars]
# Variables for db servers only
postgres_version=14
postgres_data_dir=/var/lib/postgresql/14
```

### 3. Roles (Reusable Playbooks)

```yaml
# Directory structure
roles/
├── webserver/
│   ├── tasks/
│   │   ├── main.yml        # Main tasks
│   │   ├── install.yml     # Install Apache
│   │   ├── configure.yml   # Configure Apache
│   │   └── start.yml       # Start service
│   ├── handlers/
│   │   └── main.yml        # Restart Apache handler
│   ├── vars/
│   │   └── main.yml        # Default variables
│   ├── defaults/
│   │   └── main.yml        # Override-able defaults
│   └── templates/
│       └── apache2.conf.j2 # Config template
├── database/
│   ├── tasks/main.yml
│   ├── handlers/main.yml
│   └── templates/
├── monitoring/
│   └── tasks/main.yml
└── logging/
    └── tasks/main.yml

# roles/webserver/tasks/main.yml
---
- import_tasks: install.yml
- import_tasks: configure.yml
- import_tasks: start.yml

# roles/webserver/tasks/install.yml
---
- name: Install Apache
  apt:
    name: "{{ item }}"
    state: present
  loop:
    - apache2
    - apache2-utils
    - libapache2-mod-wsgi-py3

# Usage in playbook
---
- name: Setup web servers
  hosts: web_servers
  roles:
    - webserver
    - monitoring
    - logging
```

### 4. Templates (Dynamic Configuration)

```yaml
# tasks
- name: Generate Apache config from template
  template:
    src: apache2.conf.j2
    dest: /etc/apache2/apache2.conf
  notify: restart apache

# templates/apache2.conf.j2 (Jinja2 template)
ServerRoot "{{ apache_root }}"
Listen {{ apache_port }}

<Directory /var/www>
    {% if allow_directory_listing %}
    Options Indexes FollowSymLinks
    {% else %}
    Options FollowSymLinks
    {% endif %}
    AllowOverride All
    Require all granted
</Directory>

# vars/main.yml
apache_root: /etc/apache2
apache_port: 80
allow_directory_listing: no

# Result after template:
# ServerRoot "/etc/apache2"
# Listen 80
# Options FollowSymLinks (no Indexes)
```

### 5. Variable Precedence & Conditionals

```yaml
---
- name: Configure servers based on variables
  hosts: all
  
  vars:
    # Playbook-level vars (lowest priority)
    service_state: started
    service_port: 8080
  
  tasks:
    # Task-level vars (override playbook)
    - name: Install service
      package:
        name: myapp
      vars:
        cache_valid_time: 3600
    
    # Conditionals
    - name: Configure production settings
      copy:
        src: prod.conf
        dest: /etc/myapp/
      when:
        - ansible_hostname.startswith("prod")
        - ansible_memtotal_mb > 4096  # Only if 4GB+ RAM
    
    - name: Configure dev settings
      copy:
        src: dev.conf
        dest: /etc/myapp/
      when: inventory_hostname in groups['dev_servers']
    
    # Loops
    - name: Create users
      user:
        name: "{{ item.name }}"
        state: present
        groups: "{{ item.groups }}"
      loop:
        - name: app_user
          groups: docker,sudo
        - name: monitoring_user
          groups: docker
    
    # Register output
    - name: Check service status
      command: systemctl is-active myapp
      register: service_status
      ignore_errors: yes
    
    - name: Restart if not running
      service:
        name: myapp
        state: restarted
      when: service_status.rc != 0
```

## Hands-On: Deploy Multi-Server Application

### Step 1: Create Inventory

```bash
# Create directory structure
mkdir -p ansible-deploy/{inventory,roles,playbooks}
cd ansible-deploy

# Create inventory
cat > inventory/hosts.ini << 'EOF'
[web_servers]
web1 ansible_host=10.0.1.10 ansible_user=ubuntu
web2 ansible_host=10.0.1.11 ansible_user=ubuntu

[api_servers]
api1 ansible_host=10.0.2.10 ansible_user=ubuntu

[db_servers]
db1 ansible_host=10.0.3.10 ansible_user=ubuntu

[all:vars]
ansible_ssh_private_key_file=~/.ssh/id_rsa
ansible_python_interpreter=/usr/bin/python3

[web_servers:vars]
app_port=80

[api_servers:vars]
app_port=8000

[db_servers:vars]
postgres_version=14
EOF
```

### Step 2: Create Roles

```bash
# Generate role structure
ansible-galaxy init roles/webserver
ansible-galaxy init roles/api_server
ansible-galaxy init roles/database

# Create web server role
cat > roles/webserver/tasks/main.yml << 'EOF'
---
- name: Update package cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install packages
  apt:
    name: "{{ item }}"
    state: present
  loop:
    - nginx
    - python3-pip

- name: Deploy application
  git:
    repo: https://github.com/company/web-app.git
    dest: /opt/app
    version: main
  notify: restart nginx

- name: Start nginx
  service:
    name: nginx
    state: started
    enabled: yes
EOF

# Create handler
cat > roles/webserver/handlers/main.yml << 'EOF'
---
- name: restart nginx
  service:
    name: nginx
    state: restarted
EOF
```

### Step 3: Create Main Playbook

```bash
cat > playbooks/deploy.yml << 'EOF'
---
- name: Deploy complete application
  hosts: localhost
  gather_facts: no
  
  tasks:
    - name: Configure web servers
      include_role:
        name: webserver
      loop: "{{ groups['web_servers'] }}"
      vars:
        ansible_host: "{{ item }}"
    
    - name: Configure API servers
      include_role:
        name: api_server
      loop: "{{ groups['api_servers'] }}"
      vars:
        ansible_host: "{{ item }}"
    
    - name: Configure databases
      include_role:
        name: database
      loop: "{{ groups['db_servers'] }}"
      vars:
        ansible_host: "{{ item }}"
EOF
```

### Step 4: Run Playbook

```bash
# Syntax check
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --syntax-check

# Dry run (no changes)
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml --check

# Execute
ansible-playbook -i inventory/hosts.ini playbooks/deploy.yml -v
```

### Step 5: Verify Deployment

```bash
# Run ad-hoc commands to verify
ansible web_servers -i inventory/hosts.ini -m command -a "nginx -v"
# Output: nginx version: nginx/1.24.0

ansible api_servers -i inventory/hosts.ini -m command -a "ps aux | grep app"
# Output: app process running

ansible db_servers -i inventory/hosts.ini -m command -a "psql --version"
# Output: psql (PostgreSQL) 14.5
```

## Common Mistakes

**Mistake 1: Not using handlers for notifications**
```yaml
# ❌ WRONG:
- name: Update config
  copy:
    src: app.conf
    dest: /etc/app/app.conf

- name: Restart immediately
  service:
    name: app
    state: restarted
# Restarts even if config unchanged

# ✅ RIGHT:
- name: Update config
  copy:
    src: app.conf
    dest: /etc/app/app.conf
  notify: restart app

handlers:
  - name: restart app
    service:
      name: app
      state: restarted
# Only restarts if config actually changed
```

**Mistake 2: Hardcoded values in playbooks**
```yaml
# ❌ WRONG:
- name: Configure app
  copy:
    dest: /etc/app/config.yml
    content: |
      port: 8000
      debug: false
      database: mydb

# ❌ Can't reuse for different environments
# ❌ Environment variables different each deploy

# ✅ RIGHT:
vars/
├── main.yml          # Default vars
├── prod.yml          # Production override
└── dev.yml           # Dev override

# playbook
- name: Configure app
  copy:
    dest: /etc/app/config.yml
    content: |
      port: {{ app_port }}
      debug: {{ debug_mode }}
      database: {{ db_name }}

# Run with extra vars
ansible-playbook site.yml -e "@vars/prod.yml"
```

**Mistake 3: Not idempotent tasks**
```yaml
# ❌ WRONG:
- name: Update app
  shell: |
    cd /opt/app
    git pull
    pip install -r requirements.txt
    python manage.py migrate
    systemctl restart app
# Shell commands not idempotent
# Running twice could cause problems

# ✅ RIGHT:
- name: Update app
  git:
    repo: https://github.com/company/app.git
    dest: /opt/app
    version: main
  register: git_result

- name: Install dependencies
  pip:
    requirements: /opt/app/requirements.txt
    virtualenv: /opt/app/venv
  when: git_result.changed

- name: Run migrations
  command: /opt/app/venv/bin/python manage.py migrate
  when: git_result.changed
  register: migrate_result

- name: Restart app
  service:
    name: app
    state: restarted
  when: migrate_result.changed
# Only runs what's needed, idempotent
```

**Mistake 4: Not using become properly**
```yaml
# ❌ WRONG:
- name: Install package
  command: apt-get install -y nginx
# Fails if not root, works unexpectedly

# ✅ RIGHT:
- name: Install package
  apt:
    name: nginx
    state: present
  become: yes
  become_method: sudo

# Or at play level:
- name: Configure servers
  hosts: all
  become: yes  # Everything becomes root
  tasks:
    - name: Tasks run as root
```

**Mistake 5: Assuming Python/SSH available**
```yaml
# ❌ WRONG:
- name: Configure servers
  hosts: all
  tasks:
    - name: Install Python first
      # But Ansible needs Python to run!
      command: apt-get install python3

# ✅ RIGHT:
---
- name: Pre-configure servers
  hosts: all
  gather_facts: no
  tasks:
    - name: Install Python
      raw: apt-get update && apt-get install -y python3
    
    - name: Gather facts (now Python is available)
      setup:

- name: Configure servers
  hosts: all
  tasks:
    - name: All tasks work (Python available)
```

## Production Incident Scenario

### Scenario: "Ansible playbook cascaded failure across all servers"

**What Happened:**

```yaml
# Playbook - update all servers
---
- name: Update all servers
  hosts: all
  
  tasks:
    - name: Update all packages
      apt:
        upgrade: dist  # dist-upgrade, risky!
        autoremove: yes
        autoclean: yes
    
    - name: Reboot servers
      reboot:
        reboot_timeout: 60
        
# Runs simultaneously on 50 servers:
# - apt dist-upgrade removed a critical package
# - Reboot happens before verification
# - Half servers fail to boot
# - Monitoring detects outage (5 minutes later)
```

**Root Cause:**
- No staggered deployment (rolled out simultaneously)
- No validation after updates
- No rollback strategy
- Updates in production without testing first

**Investigation:**

```bash
# 1. Check Ansible logs
grep -r "ERROR" /var/log/ansible/

# 2. Check which servers failed
ansible all -i inventory/hosts.ini -m ping
# Shows unreachable servers

# 3. SSH to failed server, check logs
ssh ubuntu@failed-server "journalctl -xe | tail -50"
# Shows: Missing kernel module, boot failed

# 4. Check what packages changed
apt log  # /var/log/apt/
# Found: libc-bin removed (critical)

# 5. Check Ansible playbook diff
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml -i inventory/hosts.ini -C  # Check mode
```

**Recovery:**

```bash
# 1. Reboot failed servers manually in recovery mode
# 2. Restore /etc/libc-bin from backup
# 3. Manual testing before using Ansible again

# 4. Fix: Create safer playbook
---
- name: Update servers safely
  hosts: all
  serial: 5  # Only 5 servers at a time, not all 50!
  
  pre_tasks:
    - name: Create snapshot before update
      debug:
        msg: "Snapshot created for {{ inventory_hostname }}"
  
  tasks:
    - name: Update only safe packages (no dist-upgrade)
      apt:
        upgrade: safe  # Conservative, not dist-upgrade
        update_cache: yes
      register: apt_result
    
    - name: Check if reboot needed
      stat:
        path: /boot/grub/grub.cfg
      register: grub_stat
    
    - name: Reboot only if kernel updated
      reboot:
        reboot_timeout: 60
      when: apt_result.changed
  
  post_tasks:
    - name: Verify services running
      service:
        name: "{{ item }}"
        state: started
      loop:
        - nginx
        - postgresql
        - monitoring-agent
    
    - name: Health check
      uri:
        url: http://localhost/health
        method: GET
        status_code: 200
      register: health_check
      until: health_check is successful
      retries: 5
      delay: 10
```

**Prevention:**

```yaml
# 1. Always test in staging first
ansible-playbook site.yml -i inventory/staging.ini  # Test first!

# 2. Use serial for gradual rollout
serial: "25%"  # Rolling update, 25% at a time

# 3. Add pre/post checks
pre_tasks:
  - name: Create backup
  - name: Run health check

post_tasks:
  - name: Verify services
  - name: Check logs for errors

# 4. Use --check and --diff
ansible-playbook site.yml --check --diff

# 5. Implement handlers for restarts
- name: Update config
  copy:
    src: app.conf
    dest: /etc/app/app.conf
  notify: restart app
  # Only restarts if config changed

handlers:
  - name: restart app
    service:
      name: app
      state: restarted
```

## Practice Questions

1. **Scenario:** You need to update 100 servers. Should you deploy simultaneously or in batches?
   - Answer: Use `serial` for batches. Deploy 10-20 at a time, verify before continuing.

2. **Question:** Should your playbook always run `service restart` after config changes?
   - Answer: No, use handlers. Only restart if task actually changed something (idempotent).

3. **Decision:** Hardcode values or use variables?
   - Answer: Always use variables. Different envs need different settings.

4. **Best Practice:** How do you prevent breaking all servers if a playbook fails?
   - Answer: 1) Test in staging, 2) Use serial for rollout, 3) Add health checks, 4) Keep rollback ready.

## Further Reading

- [Ansible Official Docs](https://docs.ansible.com/)
- [Ansible Best Practices](https://docs.ansible.com/ansible/latest/user_guide/playbooks_best_practices.html)
- [Ansible Roles](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html)
- [Ansible Galaxy](https://galaxy.ansible.com/)
- [Ansible Testing Guide](https://docs.ansible.com/ansible/latest/reference_appendices/test_strategies.html)

---

**Integration:** Use Terraform to build infrastructure, then Ansible to configure it for production-ready deployments.
