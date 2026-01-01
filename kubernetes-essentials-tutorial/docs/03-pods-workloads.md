# Module 3: Pods & Workloads

## Overview

Pods are the smallest deployable unit in Kubernetes, but they should rarely be created directly. This module covers Pod anatomy, lifecycle, and the high-level workload abstractions (Deployments, StatefulSets, DaemonSets, Jobs) that manage Pods in production.

## Pod Anatomy

### What is a Pod?

A Pod is a wrapper around one or more containers that share:
- **Network namespace**: Single IP address, same port space
- **Storage volumes**: Mounted in each container
- **Configuration**: Environment variables, resource limits

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-app
  namespace: default
  labels:
    app: myapp
spec:
  # Containers run in same network namespace
  containers:
  # Main application container
  - name: app
    image: myapp:v1.2.3
    ports:
    - containerPort: 8080
      name: http
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 500m
        memory: 512Mi
    env:
    - name: LOG_LEVEL
      value: "INFO"
    volumeMounts:
    - name: config
      mountPath: /etc/config
    - name: data
      mountPath: /var/data

  # Sidecar container (logging agent)
  - name: log-forwarder
    image: filebeat:7.10
    volumeMounts:
    - name: logs
      mountPath: /var/log/app

  # Init container (runs to completion before app containers start)
  initContainers:
  - name: init-db
    image: myapp-migrations:v1.2.3
    command: ["python", "migrate.py"]
    env:
    - name: DATABASE_URL
      valueFrom:
        secretKeyRef:
          name: db-credentials
          key: url

  # Shared volumes
  volumes:
  - name: config
    configMap:
      name: app-config
  - name: data
    emptyDir: {}
  - name: logs
    emptyDir: {}
```

### Single-Container vs Multi-Container Pods

**Single-container Pod** (most common):
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: simple-pod
spec:
  containers:
  - name: app
    image: nginx:1.21
```

**Multi-container Pod** (specific use cases):
1. **Sidecar pattern**: Add functionality without modifying main container
   - Logging agent (Fluentd, Filebeat)
   - Monitoring agent (Prometheus exporter)
   - Service mesh proxy (Envoy)

2. **Ambassador pattern**: Proxy for external services
   - Encapsulate connection logic
   - Example: DB proxy that handles connection pooling

3. **Adapter pattern**: Standardize interface
   - Transform container output to standard format
   - Example: Metrics adapter

**Important**: Containers in a Pod share network, so:
- Containers must use different ports
- Can communicate via `localhost:<port>`
- Share the same IP address (visible externally as one entity)

## Pod Lifecycle

### Pod Phases

```
Pending → Running → Succeeded/Failed
                 ↓
              Unknown
```

**Pending**: Pod created, waiting for scheduling or image pull
**Running**: Pod scheduled, all containers created, at least one running
**Succeeded**: All containers exited with status 0 (normal completion)
**Failed**: At least one container exited with non-zero status
**Unknown**: Pod status can't be determined

### Pod Conditions

Fine-grained status details:

```yaml
status:
  conditions:
  - type: Initialized
    status: "True"
    lastTransitionTime: 2023-01-15T10:00:00Z
  - type: Ready
    status: "False"
    reason: "ContainersNotReady"
    message: "containers with unready status: [app]"
  - type: ContainersReady
    status: "False"
  - type: PodScheduled
    status: "True"
```

**Key conditions**:
- **Initialized**: InitContainers have completed
- **Ready**: Pod is ready to accept traffic (readiness probes pass)
- **ContainersReady**: All containers ready
- **PodScheduled**: Pod assigned to a Node

### Container Restart Policy

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: restart-demo
spec:
  restartPolicy: Always  # Default: restart container if it exits
  containers:
  - name: app
    image: myapp:v1
```

**Restart policies**:
- **Always**: Restart container immediately if it exits (default)
- **OnFailure**: Restart only if exit code != 0
- **Never**: Don't restart, Pod remains with failed container

**Backoff logic**: First restart after 100ms, then 200ms, 400ms, ... up to 5min max.

### Pod Lifecycle Hooks

Execute scripts at specific Pod events:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: lifecycle-demo
spec:
  containers:
  - name: app
    image: myapp:v1
    lifecycle:
      postStart:
        exec:
          command: ["/bin/sh", "-c", "echo 'Started' > /tmp/started.txt"]
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 15"]  # Graceful shutdown
```

**postStart**: Runs immediately after container creation (not guaranteed before ENTRYPOINT)
**preStop**: Runs before container termination (use for graceful shutdown)

**Important**: preStop runs before SIGTERM, giving application time to clean up connections.

## Deployments: The Standard Workload

### Deployment Purpose

A Deployment manages a set of identical Pods. It handles:
- Creating/removing Pods to match desired replica count
- Rolling updates (new version replaces old gradually)
- Rollback to previous versions
- Scaling up/down

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
  labels:
    app: api
spec:
  replicas: 3  # Desired number of Pods
  
  selector:    # Which Pods does this Deployment manage?
    matchLabels:
      app: api
  
  template:    # Pod template (used to create Pods)
    metadata:
      labels:
        app: api
    spec:
      containers:
      - name: api
        image: myrepo/api:v1.2.3
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

  strategy:    # How to update Pods
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1           # Max Pods above desired replicas during update
      maxUnavailable: 0     # Max Pods below desired replicas during update
```

### ReplicaSet: Deployment's Engine

A Deployment creates a ReplicaSet, which manages Pods:

```
Deployment → ReplicaSet → Pods
  (rolling updates)  (replica count)
```

You typically don't interact with ReplicaSets directly; Deployments handle them.

```bash
# Deployments create ReplicaSets automatically
kubectl create deployment my-app --image=nginx:1.21 --replicas=3

# View the ReplicaSet created
kubectl get replicasets

# Deployment coordinates rolling update via new ReplicaSet
kubectl set image deployment/my-app nginx=nginx:1.22

# Old ReplicaSet: 3 replicas → 0 replicas
# New ReplicaSet: 0 replicas → 3 replicas
```

### Rolling Update Strategy

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1              # Allow 1 extra Pod during update
    maxUnavailable: 0        # Allow 0 missing Pods during update
```

**Example**: Deploying version 2 of app (3 replicas, maxSurge: 1, maxUnavailable: 0)

```
Initial state: [v1, v1, v1]  (3 running)

Step 1: Create new pod
        [v1, v1, v1, v2]     (4 running, 1 surge)

Step 2: Kill old pod
        [v1, v1, v2]         (3 running)

Step 3: Create new pod
        [v1, v1, v2, v2]     (4 running)

Step 4: Kill old pod
        [v1, v2, v2]         (3 running)

Step 5: Create new pod
        [v1, v2, v2, v2]     (4 running)

Step 6: Kill old pod
        [v2, v2, v2]         (3 running) ✓ Done
```

**Trade-off**:
- `maxSurge: 1, maxUnavailable: 0`: Slower update, no downtime
- `maxSurge: 0, maxUnavailable: 1`: Faster, temporary downtime
- For critical services: Use first strategy

### Deployment Update Operations

```bash
# Rolling update to new image
kubectl set image deployment/my-app app=myrepo/app:v2.0

# Watch the update progress
kubectl rollout status deployment/my-app

# View rollout history
kubectl rollout history deployment/my-app
# Revision 1: <revision details>
# Revision 2: <revision details>

# Rollback to previous version
kubectl rollout undo deployment/my-app

# Rollback to specific revision
kubectl rollout undo deployment/my-app --to-revision=1

# Update strategy (declarative)
kubectl patch deployment/my-app -p '{"spec":{"strategy":{"type":"RollingUpdate","rollingUpdate":{"maxSurge":2,"maxUnavailable":0}}}}'
```

## StatefulSets: Stateful Applications

### When to Use StatefulSets

Use StatefulSets for applications requiring:
- **Stable Pod identity**: Pod name is predictable (pod-0, pod-1, pod-2)
- **Ordered startup/shutdown**: Pods created/destroyed in order
- **Persistent identity**: Same Pod name across restarts
- **Persistent storage**: Each Pod has dedicated PVC

**Use cases**: Databases, Kafka, Zookeeper, Redis cluster, RabbitMQ

### StatefulSet Anatomy

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres  # Required: headless service
  replicas: 3
  
  selector:
    matchLabels:
      app: postgres
  
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:13
        ports:
        - containerPort: 5432
          name: db
        env:
        - name: POSTGRES_DB
          value: mydb
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql
  
  # Persistent volumes for each Pod
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

---
# Headless Service (required for StatefulSet)
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None  # Headless service (no virtual IP)
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### Pod Identity in StatefulSets

```bash
# Pods are named predictably
kubectl get pods -l app=postgres
# NAME         READY   STATUS    RESTARTS   AGE
# postgres-0   1/1     Running   0          5m
# postgres-1   1/1     Running   0          4m
# postgres-2   1/1     Running   0          3m

# DNS names are stable
# postgres-0.postgres
# postgres-1.postgres
# postgres-2.postgres

# Each Pod gets dedicated PVC
kubectl get pvc
# NAME                   STATUS   CAPACITY   ACCESSMODES
# data-postgres-0        Bound    10Gi       RWO
# data-postgres-1        Bound    10Gi       RWO
# data-postgres-2        Bound    10Gi       RWO
```

### Headless Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres
spec:
  clusterIP: None       # No virtual IP (headless)
  selector:
    app: postgres
  ports:
  - port: 5432
```

**Why headless?** StatefulSet Pods need stable DNS names (pod-0.service, pod-1.service). A regular Service (with ClusterIP) would round-robin, making Pod-to-Pod communication unpredictable.

## DaemonSets: Per-Node Workloads

### DaemonSet Purpose

Runs one Pod per Node (or selected Nodes). Used for system-level tasks.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: node-exporter
  
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      # Allow running on all Nodes (even control-plane in some cases)
      tolerations:
      - key: node-role.kubernetes.io/master
        effect: NoSchedule
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
      
      containers:
      - name: exporter
        image: prom/node-exporter:latest
        ports:
        - containerPort: 9100
        volumeMounts:
        - name: rootfs
          mountPath: /rootfs
          readOnly: true
        - name: procfs
          mountPath: /proc
          readOnly: true
      
      volumes:
      - name: rootfs
        hostPath:
          path: /
      - name: procfs
        hostPath:
          path: /proc
```

**Common uses**:
- Monitoring agents (Prometheus node-exporter, Datadog agent)
- Logging agents (Fluentd, Filebeat)
- CNI plugins (Flannel, Calico)
- Security scanning

### DaemonSet Scheduling

DaemonSets respect:
- **Node selectors**: Only run on labeled nodes
- **Taints/tolerations**: Can run on tainted nodes (like control-plane)
- **Node affinity**: Complex scheduling rules

```bash
# View which nodes have the DaemonSet pod
kubectl get pods -o wide -l app=node-exporter
# Every node should have one pod

# Check for scheduling issues
kubectl describe daemonset node-exporter
```

## Jobs: One-Time Tasks

### Job Purpose

Runs a containerized task to completion. Ensures task completes successfully (retry on failure).

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: database-backup
spec:
  # How many times to retry on failure
  backoffLimit: 3
  
  # Max execution time (seconds)
  activeDeadlineSeconds: 3600
  
  # How many successful completions required
  completions: 1
  
  # How many tasks run in parallel
  parallelism: 1
  
  template:
    spec:
      containers:
      - name: backup
        image: postgres:13
        command:
        - /bin/bash
        - -c
        - |
          pg_dump -U postgres mydb > /backups/db_$(date +%s).sql
      restartPolicy: OnFailure
      volumes:
      - name: backups
        persistentVolumeClaim:
          claimName: backup-storage
```

### Job Status and Cleanup

```bash
# View job status
kubectl get job database-backup

# View job logs
kubectl logs job/database-backup

# Delete job (and associated pods)
kubectl delete job database-backup

# Delete job but keep pods (for inspection)
kubectl delete job database-backup --cascade=orphan
```

**Successful job cleanup**:
```yaml
spec:
  ttlSecondsAfterFinished: 86400  # Delete 24 hours after completion
```

### Parallel Jobs

```yaml
spec:
  completions: 10      # Need 10 successful tasks
  parallelism: 3       # Run 3 tasks at a time
  # Total time: ~4 "waves" of execution
```

## CronJob: Scheduled Jobs

### CronJob Specification

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-backup
spec:
  # Cron schedule (minute hour day month dayOfWeek)
  schedule: "0 2 * * *"  # 2 AM daily
  
  # How many successful completions to keep
  successfulJobsHistoryLimit: 3
  
  # How many failed completions to keep
  failedJobsHistoryLimit: 3
  
  # Pod template for Job
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: myapp:v1
            command:
            - /app/backup.sh
          restartPolicy: OnFailure
```

**Cron syntax examples**:
- `0 0 * * *` - Midnight daily
- `*/15 * * * *` - Every 15 minutes
- `0 */6 * * *` - Every 6 hours
- `0 0 1 * *` - First day of month

```bash
# View cronjobs
kubectl get cronjobs

# View jobs created by cronjob
kubectl get jobs -l cronjob=daily-backup

# View logs from specific job run
kubectl logs job.batch/<job-name>
```

## Pod Scheduling and Affinity

### Node Selectors: Simple Scheduling

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: gpu-task
spec:
  # Only schedule on nodes with label gpu=true
  nodeSelector:
    gpu: "true"
  containers:
  - name: task
    image: cuda-app:v1

---
# First, label a node
# kubectl label nodes worker-1 gpu=true
```

### Node Affinity: Advanced Scheduling

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: advanced-scheduling
spec:
  affinity:
    nodeAffinity:
      # REQUIRED: Pod only schedules on matching nodes
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: kubernetes.io/arch
            operator: In
            values: ["amd64", "arm64"]
          - key: zone
            operator: In
            values: ["us-east-1a", "us-east-1b"]
      
      # PREFERRED: Scheduler prefers matching nodes
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100  # Higher weight = stronger preference
        preference:
          matchExpressions:
          - key: node-type
            operator: In
            values: ["compute-optimized"]
  
  containers:
  - name: app
    image: myapp:v1
```

### Pod Anti-Affinity: Spread Pods Across Nodes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: distributed-app
spec:
  replicas: 3
  template:
    metadata:
      labels:
        app: distributed-app
    spec:
      affinity:
        # Don't schedule two replicas on same node
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values: ["distributed-app"]
            topologyKey: kubernetes.io/hostname
      
      containers:
      - name: app
        image: myapp:v1
```

**Benefit**: If one node fails, only one replica is lost (not multiple).

## Common Mistakes

### Mistake 1: Creating Pods Directly Instead of Using Deployments

```yaml
# WRONG: Raw Pod
apiVersion: v1
kind: Pod
metadata:
  name: my-api
spec:
  containers:
  - name: api
    image: myapi:v1

# When deleted, it's gone permanently.
# No rolling updates, no high availability.
```

**Solution**: Always use Deployments (unless running one-time Job).

### Mistake 2: Not Setting Resource Requests/Limits

```yaml
# WRONG: No resource constraints
spec:
  containers:
  - name: app
    image: myapp:v1

# App can consume all node resources, affecting other Pods.
```

**Solution**:
```yaml
resources:
  requests:    # Scheduler uses for placement
    cpu: 100m
    memory: 256Mi
  limits:      # Hard limit; Pod killed if exceeded
    cpu: 500m
    memory: 512Mi
```

### Mistake 3: Using Deployment for Stateful Applications

```yaml
# WRONG: Deployment with persistent storage
apiVersion: apps/v1
kind: Deployment
metadata:
  name: database
spec:
  template:
    spec:
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: db-storage

# When Pod recreated, storage mounting order is unpredictable.
# Multiple Pods might mount same storage (read/write conflict).
```

**Solution**: Use StatefulSet for stateful apps. It ensures:
- One Pod per PVC
- Ordered startup
- Stable Pod identity

### Mistake 4: Not Understanding Pod Lifecycle Hooks

```yaml
# WRONG: Assuming postStart ensures app is ready
lifecycle:
  postStart:
    exec:
      command: ["/bin/sh", "-c", "echo ready"]

# postStart runs right after container creation.
# App might not be listening yet.
# Readiness probe should verify app is actually ready.
```

**Solution**: Use readiness probes for actual readiness checks.

### Mistake 5: Setting MaxSurge/MaxUnavailable Inconsistently

```yaml
# WRONG: Allows all Pods to be removed during update
strategy:
  rollingUpdate:
    maxUnavailable: "100%"
    maxSurge: 0

# Update starts with 0 running Pods!
# Service has no endpoints, requests fail.
```

**Solution**:
```yaml
maxUnavailable: 0          # Always have minimum replicas
maxSurge: 1                # Create extra Pod during update
# Guarantees continuous availability
```

## Production Patterns

### Progressive Rollout with Canary Deployments

Deploy new version to small percentage of traffic first:

```bash
# Deploy v2 with 10% traffic
kubectl set image deployment/api api=api:v2 --max-surge=1 --max-unavailable=0
# Manually route 10% traffic to new version
# Monitor for errors
# Gradually increase traffic to v2
# Full switch over
```

### Blue-Green Deployments

Keep two complete deployments (blue=current, green=new):

```bash
# Deploy v2 (green)
kubectl apply -f deployment-v2-green.yaml

# Switch service selector
kubectl patch service api -p '{"spec":{"selector":{"version":"green"}}}'

# If issues, switch back instantly
kubectl patch service api -p '{"spec":{"selector":{"version":"blue"}}}'
```

### Immutable Image Tags in Production

```yaml
# GOOD: Explicit version tags
image: api:v1.2.3
image: api:v1.2.4

# BAD: Floating tags that change
image: api:latest
image: api:stable

# Always use specific version tags for reproducibility
```

## Key Takeaways

1. **Pods are ephemeral**: Don't create raw Pods; use Deployments
2. **Deployments enable rolling updates**: Zero-downtime deployments
3. **StatefulSets** for databases, message queues (stateful apps)
4. **DaemonSets** for cluster-wide agents (monitoring, logging)
5. **Jobs** for one-time tasks; **CronJobs** for scheduled tasks
6. **Always set resource requests/limits**
7. **Affinity controls Pod placement**; use pod anti-affinity for resilience

---

## Practice Questions

### MCQ Questions

1. What is the smallest deployable unit in Kubernetes?
   A) Node  
   B) Container  
   C) Pod  
   D) Deployment  

2. You deployed v1 of an app with Deployment. How do you update to v2 without downtime?
   A) Delete the deployment and redeploy v2  
   B) Use kubectl set image to update the deployment  
   C) Manually delete and recreate each Pod  
   D) Edit each Pod directly with kubectl edit  

3. Which workload type is suitable for running database applications?
   A) Deployment  
   B) DaemonSet  
   C) StatefulSet  
   D) Job  

4. What does maxUnavailable: 0 mean in a rolling update strategy?
   A) Allow all Pods to be unavailable during update  
   B) Never remove Pods (keep minimum replicas running)  
   C) Maximum 0 bytes of data downtime  
   D) Don't update the deployment  

5. A DaemonSet is most appropriate for which task?
   A) Running one-time database backup  
   B) Deploying a web application  
   C) Running a monitoring agent on every node  
   D) Running batch processing jobs  

### Hands-on Cluster Tasks

**Task 1: Deploy and Update an Application**

1. Create a Deployment:
   ```bash
   kubectl create deployment web-app --image=nginx:1.21 --replicas=3
   ```

2. View the Deployment and its Pods:
   ```bash
   kubectl get deployment web-app
   kubectl get pods -l app=web-app -o wide
   ```

3. Watch a rolling update:
   ```bash
   # Terminal 1: Watch Pod changes
   kubectl get pods -l app=web-app --watch
   
   # Terminal 2: Trigger update
   kubectl set image deployment/web-app nginx=nginx:1.22
   ```

4. View rollout progress:
   ```bash
   kubectl rollout status deployment/web-app
   ```

5. Check rollout history:
   ```bash
   kubectl rollout history deployment/web-app
   ```

6. Rollback if needed:
   ```bash
   kubectl rollout undo deployment/web-app
   ```

7. Cleanup:
   ```bash
   kubectl delete deployment web-app
   ```

**Learning outcomes**: Rolling updates, no downtime deployment, easy rollbacks

**Task 2: Create a Job and CronJob**

1. Create a one-time Job:
   ```bash
   cat > job.yaml << 'EOF'
   apiVersion: batch/v1
   kind: Job
   metadata:
     name: test-job
   spec:
     template:
       spec:
         containers:
         - name: test
           image: busybox
           command: ['sh', '-c', 'echo "Job completed"; sleep 5']
         restartPolicy: Never
   EOF
   
   kubectl apply -f job.yaml
   ```

2. Monitor job execution:
   ```bash
   kubectl get job test-job
   kubectl logs job/test-job
   ```

3. Create a CronJob:
   ```bash
   cat > cronjob.yaml << 'EOF'
   apiVersion: batch/v1
   kind: CronJob
   metadata:
     name: test-cronjob
   spec:
     schedule: "*/2 * * * *"  # Every 2 minutes
     jobTemplate:
       spec:
         template:
           spec:
             containers:
             - name: test
               image: busybox
               command: ['sh', '-c', 'echo "CronJob ran at $(date)"']
             restartPolicy: Never
   EOF
   
   kubectl apply -f cronjob.yaml
   ```

4. Wait and observe created jobs:
   ```bash
   kubectl get cronjobs
   kubectl get jobs -l cronjob=test-cronjob --watch
   ```

5. Cleanup:
   ```bash
   kubectl delete job test-job
   kubectl delete cronjob test-cronjob
   ```

**Learning outcomes**: Jobs run to completion, CronJobs run on schedule, observing job lifecycle

### Realistic Production Failure Scenario

**Scenario: Deployment Stuck in Rolling Update**

Your Deployment has 3 replicas, and you triggered a rolling update to a new image. However, the new image has a bug: it crashes on startup.

```bash
# Initial: 3 replicas of v1
# Update triggered: kubectl set image deployment/app app=app:v2-buggy

# What you see:
kubectl get pods
# NAME           READY   STATUS              RESTARTS   AGE
# app-v1-xyz-1   1/1     Running             0          10m
# app-v1-xyz-2   1/1     Running             0          10m
# app-v2-abc-1   0/1     CrashLoopBackOff    5          2m
```

**The problem**:
1. New Pod (app-v2-abc-1) keeps crashing
2. Deployment tries to recreate it (restartPolicy: Always)
3. Crashes again → exponential backoff
4. Old Pods still running, so deployment hasn't fully updated
5. You have partial availability (2 old, 0 new working)

**How to detect the root cause**:
```bash
# Check pod logs
kubectl logs app-v2-abc-1 --previous

# Or if multiple restarts, latest logs show crash
kubectl logs app-v2-abc-1

# Describe pod (shows events)
kubectl describe pod app-v2-abc-1
# Events section shows crash reason
```

**Immediate fix** (roll back):
```bash
# Abort the rolling update
kubectl rollout undo deployment/app
# This scales down v2 pods, scales up v1 pods
# Requests routed back to v1 pods
```

**After fixing**:
```bash
# Fix the v2 image (fix bug, rebuild)
# Push new image: app:v2-fixed

# Try update again with explicit health checks
kubectl set image deployment/app app=app:v2-fixed

# Monitor
kubectl rollout status deployment/app
```

**Prevention**:
1. Test image locally: `docker run app:v2`
2. Test in staging cluster before production
3. Use canary deployment (10% traffic to new version first)
4. Set readiness probes (Deployment waits for pod to be ready before rolling update)
5. Set maxUnavailable: 0 to maintain minimum availability during update

---

## Further Reading

- Deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
- StatefulSets: https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
- DaemonSets: https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/
- Jobs: https://kubernetes.io/docs/concepts/workloads/controllers/job/
- Pod Lifecycle: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- Pod Affinity: https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/
