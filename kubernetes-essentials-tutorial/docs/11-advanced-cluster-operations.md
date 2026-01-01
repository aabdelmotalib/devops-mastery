# Module 11: Advanced Cluster Operations

## Overview

This module covers operational tasks: autoscaling, rolling updates, node maintenance, cluster upgrades, and disaster recovery procedures.

## Horizontal Pod Autoscaler (HPA) Deep Dive

### HPA Metrics

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
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  
  # Custom metrics (from Prometheus)
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
  
  # External metrics (cloud provider)
  - type: External
    external:
      metric:
        name: queue_length
      target:
        type: AverageValue
        averageValue: "10"
```

**How scaling works**:
```
current_replicas = 2
avg_cpu_usage = 90%
target_cpu = 70%

desired_replicas = ceil(current_replicas * (90% / 70%))
                 = ceil(2 * 1.286)
                 = 3

Scale up from 2 to 3 replicas
```

### Cooldown Periods

```yaml
behavior:
  scaleUp:
    stabilizationWindowSeconds: 0      # Scale up immediately
    policies:
    - type: Percent
      value: 50                        # Scale up by 50% per cycle
      periodSeconds: 30
    - type: Pods
      value: 2                         # Add 2 pods per cycle
      periodSeconds: 30
    selectPolicy: Max                  # Use whichever is larger
  
  scaleDown:
    stabilizationWindowSeconds: 300    # Wait 5 min before scaling down
    policies:
    - type: Percent
      value: 10                        # Scale down by 10% per cycle
      periodSeconds: 60
```

## Rolling Deployments

### Deployment Strategy Parameters

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: "25%"                  # Can exceed desired replicas by 25%
      maxUnavailable: "25%"            # Can be short 25% of desired replicas
```

**Example**: 4 replicas, maxSurge=25%, maxUnavailable=25%
```
Desired: 4 replicas
Max surge: 4 + (4 * 0.25) = 5 allowed
Max unavailable: 4 - (4 * 0.25) = 3 minimum
```

**Update phases**:
```
Initial: [v1, v1, v1, v1]              (4 running)
Step 1:  [v1, v1, v1, v1, v2]          (5 running, 1 surge)
Step 2:  [v1, v1, v1, v2]              (4 running)
Step 3:  [v1, v1, v2, v2]              (4 running)
Step 4:  [v1, v2, v2, v2]              (4 running)
Step 5:  [v2, v2, v2, v2]              (4 running) ✓ Complete
```

### Monitoring Rolling Updates

```bash
# Watch update progress
kubectl rollout status deployment/my-app

# View history
kubectl rollout history deployment/my-app
# Revision 1: <details>
# Revision 2: <details>

# Rollback to previous
kubectl rollout undo deployment/my-app

# Rollback to specific revision
kubectl rollout undo deployment/my-app --to-revision=1

# Pause rollout (in case of issues)
kubectl rollout pause deployment/my-app

# Resume rollout
kubectl rollout resume deployment/my-app
```

## Taints and Tolerations

### Taints: Mark Nodes as Unavailable

```yaml
# Mark node for specific workload only
spec:
  taints:
  - key: gpu
    value: "true"
    effect: NoSchedule  # Don't schedule pods without toleration
```

**Apply taint** (node-level):
```bash
kubectl taint nodes worker-1 gpu=true:NoSchedule
```

**Effects**:
- `NoSchedule` - Don't schedule new pods
- `NoExecute` - Evict existing pods
- `PreferNoSchedule` - Prefer not to schedule (soft)

### Tolerations: Allow Pods on Tainted Nodes

```yaml
spec:
  tolerations:
  - key: gpu
    operator: Equal
    value: "true"
    effect: NoSchedule
```

**Use case**: GPU workloads only run on GPU nodes
```bash
# Taint GPU node
kubectl taint nodes gpu-node-1 gpu=true:NoSchedule

# Pod with toleration runs on GPU node
# Pod without toleration can't run there
```

## Node Maintenance

### Draining Nodes

```bash
# Gracefully drain node before maintenance
kubectl drain worker-1 \
  --ignore-daemonsets \
  --delete-emptydir-data \
  --grace-period=30

# Nodes become SchedulingDisabled (cordoned)
# Existing pods evicted to other nodes
# New pods won't schedule here
```

**Steps**:
1. Node marked as `SchedulingDisabled`
2. Pods evicted gracefully (preStop hooks called)
3. Pods recreated on other nodes

**Exceptions**:
```bash
kubectl drain worker-1 \
  --ignore-daemonsets           # Don't evict DaemonSet pods
  --delete-emptydir-data        # Delete EmptyDir volumes
  --force                       # Delete pods without owner
  --grace-period=30             # Wait 30s for graceful shutdown
```

### Uncording Node

```bash
# After maintenance, make node schedulable again
kubectl uncordon worker-1

# Node becomes Ready again
```

## Pod Disruption Budgets (PDB)

Ensure minimum availability during voluntary disruptions (node maintenance, updates):

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app-pdb
spec:
  minAvailable: 2              # Always keep ≥2 pods running
  selector:
    matchLabels:
      app: myapp
```

Or use maxUnavailable:
```yaml
spec:
  maxUnavailable: 1            # At most 1 pod can be evicted
```

**Effect**:
```bash
kubectl drain node
# Can only evict pods if PDB allows
# If PDB says minAvailable=2, and only 2 running, drain waits
```

## etcd: Backup and Restore

etcd stores all cluster state. Regular backups are critical.

### Backup etcd

```bash
# On control-plane node:
ETCDCTL_API=3 etcdctl --endpoints=127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /tmp/etcd-backup.db

# Verify backup
ETCDCTL_API=3 etcdctl --write-out=table snapshot status /tmp/etcd-backup.db
```

### Restore from Backup

```bash
# Stop API server
kubectl static pod stop kube-apiserver

# Restore etcd
ETCDCTL_API=3 etcdctl snapshot restore /tmp/etcd-backup.db \
  --data-dir=/var/lib/etcd-backup

# Switch to restored data
mv /var/lib/etcd /var/lib/etcd-old
mv /var/lib/etcd-backup /var/lib/etcd

# Start API server
# It automatically restarts with new etcd data
```

**Important**: Disaster recovery procedure should be tested regularly.

## Cluster Upgrades

### Planning Upgrade

```
Kubernetes versions:
- 1.23 (old)
- 1.24 (current)
- 1.25 (new)

Upgrade path: 1.23 → 1.24 → 1.25
(Can't skip minor versions)
```

### Upgrade Process (kubeadm)

1. **Drain master node**:
   ```bash
   kubectl drain controlplane-1 --ignore-daemonsets
   ```

2. **Upgrade kubeadm**:
   ```bash
   apt-get upgrade kubeadm=1.24.0
   ```

3. **Plan upgrade**:
   ```bash
   kubeadm upgrade plan
   ```

4. **Apply upgrade**:
   ```bash
   kubeadm upgrade apply v1.24.0
   ```

5. **Upgrade kubelet**:
   ```bash
   apt-get upgrade kubelet kubectl
   systemctl restart kubelet
   ```

6. **Uncordon node**:
   ```bash
   kubectl uncordon controlplane-1
   ```

7. **Repeat for worker nodes**

### Upgrade with Managed Kubernetes

```bash
# AWS EKS
aws eks update-cluster-version --name my-cluster --kubernetes-version 1.24

# GKE
gcloud container clusters upgrade my-cluster --cluster-version 1.24

# Azure AKS
az aks upgrade --resource-group mygroup --name mycluster --kubernetes-version 1.24
```

## Disaster Recovery Patterns

### RTO / RPO

- **RTO** (Recovery Time Objective): How long can you be down?
- **RPO** (Recovery Point Objective): How much data can you lose?

Example:
- RTO: 1 hour (must recover within 1 hour)
- RPO: 15 minutes (can lose up to 15 min of data)

### Multi-region Setup

```
Region A (Primary)          Region B (Secondary)
├── Control Plane    ←→     ├── Control Plane
├── Worker Nodes     ←→     ├── Worker Nodes
└── etcd             ←→     └── etcd (replica)
```

**Failure scenario**: Region A fails
- Automatically failover to Region B
- Continues serving requests
- RTO: minutes

### Backup Strategy

```
Daily:  Snapshot etcd + PVCs
Weekly: Full cluster backup
Monthly: Archive off-site

Test recovery monthly
```

### Cluster Autoscaling

```yaml
# Scale cluster size based on pod demand
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
data:
  priorities: |
    10:
    - .*-spot
    20:
    - .*-ondemand
```

When pods can't be scheduled:
- Cluster autoscaler adds nodes
- Scales down when capacity excess

## Common Mistakes

### Mistake 1: No PodDisruptionBudget

```bash
# Drain node with 3 replicas
kubectl drain worker-1

# All 3 pods evicted immediately
# Service has 0 replicas, downtime
```

**Solution**: Add PDB:
```yaml
minAvailable: 2  # Always keep 2 running
```

### Mistake 2: Not Testing Disaster Recovery

```bash
# Have backup, never tested restore
# When disaster hits, restore fails
```

**Solution**: Monthly drill to restore from backup.

### Mistake 3: Upgrading Without Testing

```bash
# Upgrade production cluster directly
# Incompatible add-on breaks cluster
```

**Solution**: Test upgrade in staging first.

### Mistake 4: No Backup Strategy

```bash
# No etcd backups
# Cluster corrupted, all data lost
```

**Solution**: Automated, tested backup procedures.

## Key Takeaways

1. **HPA** scales pods based on metrics
2. **Rolling updates** achieve zero-downtime deployments
3. **Taints/tolerations** control pod placement
4. **Node drain** for safe maintenance
5. **PDB** ensures availability during disruptions
6. **etcd backup/restore** for disaster recovery
7. **Test all DR procedures** regularly

---

## Practice Questions

### MCQ Questions

1. What does kubectl drain do?
   A) Deletes all pods on node  
   B) Gracefully evicts pods so node can be maintained  
   C) Removes node from cluster permanently  
   D) Shuts down kubelet  

2. What effect does a taint have?
   A) Prevents node from joining cluster  
   B) Prevents pods without tolerations from scheduling on node  
   C) Encrypts node traffic  
   D) Changes node IP address  

3. What does PodDisruptionBudget do?
   A) Limits pod resource usage  
   B) Ensures minimum availability during voluntary disruptions  
   C) Automatically scales pods  
   D) Prevents pod crashes  

4. How often should etcd be backed up in production?
   A) Never (etcd is replicated)  
   B) Daily minimum  
   C) Hourly  
   D) Continuously to another region  

5. What happens when all control-plane nodes fail?
   A) Cluster automatically recovers  
   B) Cluster stays up, but can't create/modify resources  
   C) All pods immediately crash  
   D) Automatic failover to backup cluster  

### Hands-on Cluster Tasks

**Task 1: Node Maintenance with Drain**

1. Label a node:
   ```bash
   kubectl label nodes worker-1 maintenance=true
   ```

2. Run pods on labeled node:
   ```bash
   kubectl run test-pod-1 --image=busybox -- sleep 3600 \
     --node-selector maintenance=true
   ```

3. Drain node:
   ```bash
   kubectl drain worker-1 --ignore-daemonsets --dry-run=client
   # Verify what would be evicted
   
   kubectl drain worker-1 --ignore-daemonsets
   ```

4. Verify node cordoned:
   ```bash
   kubectl get nodes worker-1
   # STATUS shows SchedulingDisabled
   ```

5. Verify pod moved:
   ```bash
   kubectl get pod test-pod-1 -o wide
   # Pod now on different node
   ```

6. Uncordon:
   ```bash
   kubectl uncordon worker-1
   ```

7. Cleanup:
   ```bash
   kubectl delete pod test-pod-1
   ```

**Task 2: PodDisruptionBudget**

1. Create deployment:
   ```bash
   kubectl create deployment pdb-test --image=nginx --replicas=3
   ```

2. Create PDB:
   ```bash
   cat > pdb.yaml << 'EOF'
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: pdb-test
   spec:
     minAvailable: 2
     selector:
       matchLabels:
         app: pdb-test
   EOF
   
   kubectl apply -f pdb.yaml
   ```

3. Verify PDB:
   ```bash
   kubectl get pdb pdb-test
   ```

4. Try to drain node (will be constrained by PDB):
   ```bash
   kubectl drain <node-with-pdb-pod> --ignore-daemonsets --dry-run=client
   # Shows disruption would violate budget
   ```

5. Cleanup:
   ```bash
   kubectl delete deployment pdb-test
   kubectl delete pdb pdb-test
   ```

### Realistic Production Failure Scenario

**Scenario: Unplanned Node Failure During Peak Traffic**

A worker node crashes suddenly (hardware failure, not gracefully drained). Pods running on it are lost.

```bash
# Worker-1 crashes

# Status:
# Worker-1: NotReady

# Pods on worker-1:
# - app-replica-1: Lost
# - app-replica-2: Lost
# - app-replica-3: Still running on worker-2

# Deployment has only 1/3 replicas
# Service load capacity reduced 67% → overload
# Response times spike, errors increase
```

**Without PDB**:
- All 3 replicas might be on same node
- Single node failure = complete service outage

**With PDB**:
- minAvailable: 2 ensures at least 2 replicas on different nodes
- Max 1 replica lost to single node failure
- Service continues with degraded capacity

**With HPA**:
- Load increases on remaining pods
- HPA detects CPU spike
- Scales up to 5 replicas automatically
- New pods distribute across healthy nodes
- Capacity recovers

**Prevention**:
1. Use PDB to ensure resilience
2. Spread replicas across multiple nodes (pod anti-affinity)
3. Monitor node health continuously
4. Keep spare cluster capacity (don't run at 90% utilization)

---

## Further Reading

- HPA: https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- Node Maintenance: https://kubernetes.io/docs/tasks/administer-cluster/safely-drain-node/
- Taints: https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/
- PDB: https://kubernetes.io/docs/tasks/run-application/configure-pdb/
- Cluster Upgrade: https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-upgrade/
- etcd Backup: https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/
