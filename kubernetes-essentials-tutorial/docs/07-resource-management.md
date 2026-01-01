# Module 7: Resource Management

## Overview

Resource requests and limits control how Pods consume cluster resources (CPU, memory). This module covers capacity planning, QoS classes, resource quotas, and scheduling strategies.

## Requests vs Limits

### Resource Requests

A request is the minimum amount of resources a Pod needs to run. Scheduler uses requests to decide where to place Pods.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: resource-demo
spec:
  containers:
  - name: app
    image: myapp:v1
    resources:
      requests:
        cpu: 100m              # 0.1 CPU cores (millicores)
        memory: 256Mi          # 256 megabytes
```

**How scheduler uses requests**:
```
Cluster has 3 nodes, each with 2 CPU cores
Total capacity: 6 cores

Node 1: 1.5 cores available
Node 2: 1.2 cores available
Node 3: 0.8 cores available

Pod requests 1.5 cores

Scheduler: "Which node has ≥1.5 cores available?"
Result: Can schedule on Node 1 or Node 2
Decision: Place on Node 1 (most available)
```

**If no node has enough capacity**, Pod stays Pending:
```bash
kubectl get pod
# NAME            READY   STATUS    RESTARTS   AGE
# resource-demo   0/1     Pending   0          5m
# (insufficient CPU)
```

### Resource Limits

A limit is the maximum amount of resources a Pod can use. If a container exceeds limits, it's throttled or killed.

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

**CPU limit**: Container process is throttled (slowed down, not killed)
**Memory limit**: Container killed if it exceeds limit

**Example**: Container requests 256Mi, limited to 512Mi
- Uses 256Mi normally (OK)
- Spike to 400Mi (OK, below limit)
- Tries to use 600Mi (KILLED - OOMKilled)

## CPU and Memory Units

### CPU

```
1 CPU = 1000 millicores (m)
0.5 CPU = 500m
0.1 CPU = 100m
```

CPU is compressible: throttled, not terminated.

**How much CPU for your app?**
- Lightweight: 50m - 100m
- Standard: 100m - 500m
- Compute-heavy: 500m - 2000m

### Memory

```
1 Gi = 1 gibibyte = 1024^3 bytes ≈ 1.07 billion bytes
1 G  = 1 gigabyte  = 1000^3 bytes ≈ 1 billion bytes
1 Mi = 1 mebibyte  = 1024^2 bytes ≈ 1 million bytes
1 M  = 1 megabyte  = 1000^2 bytes ≈ 1 million bytes
```

Use Gi/Mi (binary) not G/M (decimal) for accuracy.

Memory is incompressible: Pod killed if limit exceeded.

**How much memory for your app?**
- Lightweight: 64Mi - 256Mi
- Standard: 256Mi - 1Gi
- Memory-heavy: 1Gi - 10Gi+

## Quality of Service (QoS) Classes

Kubernetes automatically assigns QoS class to Pod based on requests/limits:

### Guaranteed (Highest Priority)

```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

**Conditions**:
- Requests == Limits for all containers
- All containers have requests and limits

**Behavior**:
- Pod evicted only if node out of memory (last resort)
- Highest priority for resources
- Best for critical workloads

### Burstable (Medium Priority)

```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

**Conditions**:
- Requests < Limits
- Or only some containers have requests/limits

**Behavior**:
- Can burst above requests (if resources available)
- Evicted before Guaranteed if node under pressure
- Good for most applications

### BestEffort (Lowest Priority)

```yaml
# No requests or limits
resources: {}
```

**Conditions**:
- No requests or limits set

**Behavior**:
- No resource guarantees
- Uses any available resources
- Evicted first if node under pressure
- Use for non-critical workloads only

## Resource Quotas

Resource quotas limit resource consumption per namespace:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "100"           # Max 100 cores requested across all pods
    requests.memory: "100Gi"      # Max 100 GB requested
    limits.cpu: "200"             # Max 200 cores limit
    limits.memory: "200Gi"        # Max 200 GB limit
    pods: "100"                   # Max 100 pods
    services.loadbalancers: "2"   # Max 2 load balancer services
```

**Enforcement**:
```bash
# Quota v1
requests.cpu = 10 + 20 + 15 = 45  # Used
hard = 100                         # Limit

# When new Pod requests 60 cores:
# 45 + 60 = 105 > 100 (exceeds quota)
# Pod creation rejected
```

**View quota usage**:
```bash
kubectl describe resourcequota production-quota -n production
# Shows requests.cpu, requests.memory usage vs limits
```

## LimitRanges

LimitRange enforces min/max resource bounds per Pod or container:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limits
  namespace: production
spec:
  limits:
  # Per container
  - type: Container
    min:
      cpu: 50m
      memory: 64Mi
    max:
      cpu: 2000m
      memory: 2Gi
    default:
      cpu: 500m
      memory: 512Mi
    defaultRequest:
      cpu: 250m
      memory: 256Mi
  
  # Per Pod (across all containers)
  - type: Pod
    min:
      cpu: 100m
      memory: 128Mi
    max:
      cpu: 4000m
      memory: 4Gi
```

**Effect**:
- Container without requests → Gets default values
- Pod exceeding max → Creation rejected

## Vertical Pod Autoscaler (VPA)

VPA recommends resource request values based on actual usage:

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: app-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  updateMode: "Auto"              # auto-update pods when recommendations change
  resourcePolicy:
    containerPolicies:
    - containerName: "*"
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: 2000m
        memory: 2Gi
```

**How it works**:
1. Observes actual CPU/memory usage
2. Computes recommendations
3. Auto-updates Pod requests
4. Triggers pod recreation

**Use case**: Right-sizing Pods for optimal resource utilization.

## Horizontal Pod Autoscaler (HPA)

HPA scales number of Pods based on metrics (CPU, custom metrics).

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80      # Scale up if avg CPU > 80%
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 85      # Scale up if avg memory > 85%
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
    scaleUp:
      stabilizationWindowSeconds: 0    # Scale up immediately
```

**Prerequisites**: Metrics-server running (collects pod metrics).

**Scaling logic**:
```
If average CPU usage > 80% target:
  Desired replicas = ceil(current CPU / target CPU * current replicas)
  Example: 5 pods using 400m, target 80%
           400m / (80% * 5) = 100m per pod
           Desired: ceil(5 * (current usage / target)) = scaled count
```

### HPA with Custom Metrics

```yaml
metrics:
- type: Pods
  pods:
    metric:
      name: http_request_rate
    target:
      type: AverageValue
      averageValue: "100"      # Scale if avg > 100 req/s
```

Requires custom metrics provider (Prometheus, Stackdriver).

## Pod Priority and Preemption

Pod priority determines eviction order when resources scarce:

```yaml
apiVersion: v1
kind: PriorityClass
metadata:
  name: critical
value: 1000
globalDefault: false
description: "Critical production workloads"

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: critical-api
spec:
  template:
    spec:
      priorityClassName: critical
      containers:
      - name: api
        image: api:v1
```

**Preemption**:
```
High-priority Pod pending (no resources)
  ↓
Evict low-priority Pods
  ↓
Schedule high-priority Pod
```

**Use cases**:
- Production workloads should preempt dev workloads
- Critical services should preempt batch jobs

## Common Mistakes

### Mistake 1: No Resource Requests/Limits

```yaml
# WRONG: No constraints
spec:
  containers:
  - name: app
    image: myapp:v1
```

**Problem**:
- Scheduler can't make informed decisions
- Pod uses all available resources, starving others
- Under memory pressure, no QoS → easily evicted

**Solution**:
```yaml
resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### Mistake 2: Requests Equal Limits (Wasteful)

```yaml
# INEFFICIENT: No burst capacity
resources:
  requests:
    cpu: 500m
  limits:
    cpu: 500m
```

**Problem**: Can't burst when needed, resources wasted if utilization is variable.

**Solution**: Limit > Request (burstable class)
```yaml
resources:
  requests:
    cpu: 100m
  limits:
    cpu: 500m
```

### Mistake 3: Setting Limits Too Low

```yaml
resources:
  requests:
    cpu: 100m
  limits:
    cpu: 100m  # ← Exact same as request
```

**Problem**: App spike → Throttled or killed.

**Solution**: Set limit 3-5x request value (for typical apps).

### Mistake 4: Ignoring QoS Classes

```yaml
# BestEffort (no requests/limits)
# Gets evicted first under pressure!
```

**Problem**: Critical workload gets evicted first.

**Solution**: Set requests/limits for all production Pods (at least Burstable).

### Mistake 5: Not Using Resource Quotas in Multi-tenant Cluster

```bash
# Multiple teams, no quotas
# One team's Pod consumes all cluster resources
# Other teams' Pods can't schedule
```

**Solution**: Implement ResourceQuota per namespace.

## Production Patterns

### Calculating Resource Requests

1. **Load test** your application
2. **Monitor actual usage** (CPU, memory)
3. **Set request** to 70th percentile of usage
4. **Set limit** to 95th percentile or spike max

Example:
```
Monitoring shows:
- Average CPU: 150m
- Peak CPU: 500m
- 95th percentile: 400m

request: 150m
limit: 500m (or 400m + buffer)
```

### Resource Quotas for Multi-tenant

```yaml
# development namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-quota
spec:
  hard:
    requests.cpu: "20"
    requests.memory: "20Gi"
    limits.cpu: "40"
    limits.memory: "40Gi"

---
# production namespace
apiVersion: v1
kind: ResourceQuota
metadata:
  name: prod-quota
spec:
  hard:
    requests.cpu: "200"
    requests.memory: "200Gi"
    limits.cpu: "400"
    limits.memory: "400Gi"
```

### HPA + Resource Requests

Always set requests when using HPA. HPA uses metrics from actual usage, which requires requests to make proper decisions.

```bash
# Check HPA status
kubectl get hpa app-hpa
# REFERENCE             TARGETS   MINPODS   MAXPODS   REPLICAS
# Deployment/my-app     45%/80%   2         10        5
```

## Key Takeaways

1. **Requests** guide scheduling; **Limits** enforce maximums
2. **Set both** requests and limits for all Pods
3. **QoS classes** determine eviction order
4. **ResourceQuotas** limit namespace consumption
5. **HPA** scales replicas; **VPA** right-sizes resources
6. **Pod Priority** determines preemption order

---

## Practice Questions

### MCQ Questions

1. What is the purpose of a resource request?
   A) Maximum amount of CPU/memory a pod can use  
   B) Minimum amount needed for scheduler to place pod  
   C) Amount charged for the pod  
   D) Amount reserved for emergency use  

2. What happens if a Pod exceeds its memory limit?
   A) Process is throttled  
   B) Pod is killed (OOMKilled)  
   C) Kubernetes migrates pod to different node  
   D) Memory limit is ignored  

3. Which QoS class gets evicted first under memory pressure?
   A) Guaranteed  
   B) Burstable  
   C) BestEffort  
   D) All equally  

4. What does a ResourceQuota enforce?
   A) Limit on single Pod's resource usage  
   B) Limit on total resource usage in namespace  
   C) Priority ordering of pods  
   D) Physical CPU/memory of nodes  

5. What does Horizontal Pod Autoscaler do?
   A) Scales CPU/memory of existing pods  
   B) Scales number of pods based on metrics  
   C) Automatically optimizes code  
   D) Provisions new nodes  

### Hands-on Cluster Tasks

**Task 1: Create Pods with Resource Requests/Limits**

1. Create Pod without resources:
   ```bash
   kubectl run no-resources --image=busybox -- sleep 3600
   ```

2. Create Pod with guaranteed QoS:
   ```bash
   cat > guaranteed.yaml << 'EOF'
   apiVersion: v1
   kind: Pod
   metadata:
     name: guaranteed-pod
   spec:
     containers:
     - name: app
       image: busybox
       command: ['sleep', '3600']
       resources:
         requests:
           cpu: 100m
           memory: 128Mi
         limits:
           cpu: 100m
           memory: 128Mi
   EOF
   
   kubectl apply -f guaranteed.yaml
   ```

3. Create Pod with burstable QoS:
   ```bash
   cat > burstable.yaml << 'EOF'
   apiVersion: v1
   kind: Pod
   metadata:
     name: burstable-pod
   spec:
     containers:
     - name: app
       image: busybox
       command: ['sleep', '3600']
       resources:
         requests:
           cpu: 100m
           memory: 128Mi
         limits:
           cpu: 500m
           memory: 512Mi
   EOF
   
   kubectl apply -f burstable.yaml
   ```

4. Check QoS class:
   ```bash
   # Guaranteed
   kubectl get pod guaranteed-pod -o jsonpath='{.status.qosClass}'
   # Burstable
   kubectl get pod burstable-pod -o jsonpath='{.status.qosClass}'
   # BestEffort
   kubectl get pod no-resources -o jsonpath='{.status.qosClass}'
   ```

5. Cleanup:
   ```bash
   kubectl delete pod no-resources guaranteed-pod burstable-pod
   ```

**Task 2: ResourceQuota**

1. Create namespace:
   ```bash
   kubectl create namespace quota-test
   ```

2. Create ResourceQuota:
   ```bash
   cat > quota.yaml << 'EOF'
   apiVersion: v1
   kind: ResourceQuota
   metadata:
     name: test-quota
     namespace: quota-test
   spec:
     hard:
       requests.cpu: "2"
       requests.memory: "2Gi"
       limits.cpu: "4"
       limits.memory: "4Gi"
       pods: "5"
   EOF
   
   kubectl apply -f quota.yaml
   ```

3. Check quota:
   ```bash
   kubectl describe resourcequota test-quota -n quota-test
   # Shows used vs hard limits
   ```

4. Create Pod within quota:
   ```bash
   cat > pod.yaml << 'EOF'
   apiVersion: v1
   kind: Pod
   metadata:
     name: quota-test-pod
     namespace: quota-test
   spec:
     containers:
     - name: app
       image: busybox
       command: ['sleep', '3600']
       resources:
         requests:
           cpu: 500m
           memory: 512Mi
         limits:
           cpu: 1000m
           memory: 1Gi
   EOF
   
   kubectl apply -f pod.yaml
   ```

5. Check quota updated:
   ```bash
   kubectl describe resourcequota test-quota -n quota-test
   # Shows pod using 500m CPU, 512Mi memory
   ```

6. Try to exceed quota:
   ```bash
   # Duplicate pod (would exceed quota)
   kubectl apply -f pod.yaml  # Change name to pod2
   # Should fail: "exceeded quota"
   ```

7. Cleanup:
   ```bash
   kubectl delete namespace quota-test
   ```

### Realistic Production Failure Scenario

**Scenario: Pods Evicted Due to Node Memory Pressure**

Your cluster has 10 nodes. You deploy many low-priority background jobs (no resource requests). A critical application also runs on same nodes.

```bash
# Memory pressure builds up
# Node memory: 99% utilized

# Kubernetes needs to evict some Pods
# Picks: BestEffort Pods (background jobs)
# Critical app: Guaranteed QoS (protected)

# Background jobs evicted
# Critical app still running
# But now background jobs can't schedule
```

**Root cause**: No resource requests on background jobs; no priority classes.

**Detection**:
```bash
kubectl get events | grep Evicted
# Pod evicted due to node memory pressure

kubectl get pods
# Some pods in Evicted state
```

**Immediate fix**:
1. Scale cluster:
   ```bash
   # Add more nodes (if on cloud)
   kubectl scale nodegroup node-group-1 --count=15
   ```

2. Add memory limits to prevent future eviction:
   ```yaml
   resources:
     requests:
       memory: 256Mi
     limits:
       memory: 512Mi
   ```

**Prevention**:
1. Set resource requests on ALL Pods
2. Use priority classes to protect critical workloads
3. Monitor node capacity:
   ```bash
   kubectl top nodes
   ```

4. HPA to scale workloads based on capacity
5. Proper ResourceQuotas to prevent one app from consuming everything

---

## Further Reading

- Resource Management: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
- QoS Classes: https://kubernetes.io/docs/tasks/configure-pod-container/quality-service-pod/
- ResourceQuotas: https://kubernetes.io/docs/concepts/policy/resource-quotas/
- HPA: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- VPA: https://github.com/kubernetes/autoscaler/tree/master/vertical-pod-autoscaler
- Pod Priority: https://kubernetes.io/docs/concepts/scheduling-eviction/pod-priority-preemption/
