# Module 1: Kubernetes Fundamentals

## Overview

Kubernetes is a production-grade container orchestration platform that automates deployment, scaling, and operations of containerized applications across clusters of machines. Understanding its architecture is essential before using any feature.

This module establishes the mental model you need for all subsequent Kubernetes operations.

## Architecture: The Kubernetes Cluster

A Kubernetes cluster consists of:

```
Cluster
├── Control Plane (Management Layer)
│   ├── API Server - RESTful interface, stores state in etcd
│   ├── Scheduler - Assigns Pods to Nodes based on resources
│   ├── Controller Manager - Runs controllers (deployment, statefulset, etc.)
│   └── etcd - Distributed key-value store (single source of truth)
│
└── Worker Nodes (Execution Layer) - Multiple machines
    ├── kubelet - Agent that runs containers
    ├── kube-proxy - Network proxy and load balancer
    ├── Container Runtime (Docker, containerd, cri-o)
    └── Pods (smallest deployable units containing 1+ containers)
```

### Control Plane Components Explained

**API Server**
- Every Kubernetes operation goes through the API Server
- All cluster state is stored in etcd
- kubectl commands communicate with this endpoint
- Must be highly available in production

**Scheduler**
- Watches for Pods that have no Node assigned
- Evaluates resource requests, node affinity, taints/tolerations
- Never moves a Pod after scheduling (use Deployments for updates)
- Default scheduler is configurable

**Controller Manager**
- Runs multiple controllers as infinite loops
- Examples: Deployment Controller, StatefulSet Controller, DaemonSet Controller
- Each controller watches for resource changes and takes action
- Example: If a Deployment has 3 replicas and 1 Pod dies, the Deployment Controller creates a new Pod

**etcd**
- Stores all cluster state: Pods, Services, ConfigMaps, Secrets, etc.
- Single source of truth
- Requires backup/restore procedures
- Not for application data storage

### Worker Node Components Explained

**kubelet**
- Agent running on every Node
- Ensures Pods are running as specified
- Can't manage Pods from other cluster architectures
- Reports Node status to API Server
- Never stop kubelet; instead, use `kubectl drain` for maintenance

**kube-proxy**
- Implements Service abstraction using iptables rules (or IPVS)
- Maintains network rules for Pod-to-Pod and Pod-to-Service communication
- Enables load balancing across Pods

**Container Runtime**
- Executes containers inside Pods
- Common choices: containerd, cri-o, Docker (deprecated as of 1.24)
- Kubernetes only cares about the interface, not the specific runtime

## Kubernetes Objects: The API Model

Everything in Kubernetes is an **object** - a persistent entity that represents the desired state and current state of something in your cluster.

### Common Object Types

**Pod** - Smallest deployable unit
- One or more containers (usually one)
- Ephemeral: replaced, not restarted when failed
- Rarely created directly; use Deployments instead

**Deployment** - Manages ReplicaSets
- Desired state: replicas, container image, update strategy
- Enables rolling updates, rollbacks, scaling
- Standard workload for stateless applications

**Service** - Exposes Pods to network
- Provides stable IP and DNS name
- Load balances traffic across Pod replicas
- Acts as internal or external entry point

**Namespace** - Virtual cluster inside physical cluster
- Resource quotas and RBAC boundaries
- Isolates teams/environments (dev, staging, prod)
- Pods in different namespaces can communicate but have stricter RBAC

**ConfigMap** - Store non-sensitive configuration
- Key-value pairs injected as environment variables or files
- Supports up to 1MB per object

**Secret** - Store sensitive data
- Base64 encoded (not encrypted by default!)
- Used for passwords, tokens, SSH keys
- Consider external secret management in production

**PersistentVolume (PV)** - Storage resource
- Provisioned by cluster administrator
- Independent of Pod lifecycle
- Has access modes, capacity, storage class

**PersistentVolumeClaim (PVC)** - Storage request
- Claim made by a Pod to use storage
- Automatically binds to matching PV or creates one dynamically

**StatefulSet** - Manages stateful applications
- Unlike Deployments, StatefulSets provide stable Pod names
- Useful for databases, message queues, stateful services
- Requires persistent storage

**DaemonSet** - Runs Pod on every (or selected) Node
- Example: log collectors, monitoring agents, CNI plugins
- Automatically creates Pods on new Nodes

**Job** - Runs to completion (not continuously)
- Example: batch processing, one-time tasks
- Can be parallelized

**CronJob** - Scheduled Job
- Example: daily backups, cleanup tasks
- Specified with cron syntax

## The Desired State vs Actual State Model

Kubernetes operates on a simple principle:

```
Your declarative YAML (Desired State)
            ↓
    API Server stores it
            ↓
    Controllers constantly watch
            ↓
    Compare: Desired vs Actual
            ↓
    Take action to converge
            ↓
    System eventually reaches Desired State
```

This is the **reconciliation loop**. Controllers run infinitely, checking if actual state matches desired state. If not, they take corrective action.

**Critical insight**: You never tell Kubernetes "do this action." Instead, you declare "this is what should exist" and Kubernetes makes it happen.

## Namespaces: Logical Isolation

Namespaces partition a single cluster into multiple virtual clusters.

### Default Namespaces
- `default` - where resources are created if not specified
- `kube-system` - Kubernetes system components (CoreDNS, kube-proxy, etc.)
- `kube-public` - Publicly readable data
- `kube-node-lease` - Node lease objects (kubelet heartbeats)

### Namespace Scope

**Namespace-scoped resources** (most resources)
```bash
kubectl get pods --namespace production
kubectl get services --namespace staging
```

**Cluster-scoped resources** (no namespace)
- Nodes
- PersistentVolumes
- ClusterRoles
- Namespaces themselves

### Production Use of Namespaces

```yaml
# Each team/environment gets its own namespace
namespaces:
  - development    # shared dev environment
  - staging        # staging environment
  - production     # production environment
  - monitoring     # centralized monitoring stack
```

Namespaces enable:
- Resource quotas per team
- RBAC boundaries
- Network policies isolation
- Resource cleanup (delete namespace = delete all resources in it)

## Cluster Lifecycle

### 1. Cluster Creation

In production, you typically use a managed service:
- AWS EKS (Elastic Kubernetes Service)
- Google GKE (Google Kubernetes Engine)
- Azure AKS (Azure Kubernetes Service)
- On-premises: kubeadm, kops, Talos

```bash
# Example: Create with kubeadm (manual approach for learning)
# On control-plane node:
kubeadm init --pod-network-cidr=10.244.0.0/16

# Output provides join command for worker nodes
```

### 2. Nodes Join Cluster

```bash
# On worker nodes:
kubeadm join <control-plane-ip>:6443 --token <token> --discovery-token-ca-cert-hash sha256:<hash>
```

After join, node appears in cluster:
```bash
kubectl get nodes
```

### 3. Pod Network Plugin Installation

```bash
# Example: Install Flannel CNI plugin
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
```

This enables Pod-to-Pod communication across nodes.

### 4. Workload Deployment

After cluster is ready, deploy applications:
```bash
kubectl apply -f deployment.yaml
```

### 5. Upgrades and Maintenance

- Drain node: `kubectl drain node-name`
- Upgrade kubelet/container runtime
- Uncordon node: `kubectl uncordon node-name`

## Common Misconceptions

### 1. "Pods are containers"
**Reality**: A Pod is a wrapper around one or more containers. It's an abstraction that enables:
- Shared network namespace (same IP, port space)
- Shared storage volumes
- Init containers and sidecar patterns

You rarely create a single-container Pod directly. Use Deployments.

### 2. "Kubernetes automatically runs my code"
**Reality**: Kubernetes assumes your container image is already built and pushed to a registry. Kubernetes orchestrates existing images; it doesn't build them.

```yaml
# This deployment references a pre-built image
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-server
spec:
  containers:
  - name: api
    image: myrepo/api:v1.2.3  # Must exist in registry!
```

### 3. "If a Pod fails, Kubernetes restarts it"
**Reality**: A Pod is ephemeral. If it crashes:
- A Deployment creates a **new** Pod (different instance)
- The old Pod is removed
- This is not a "restart" in the VM sense

This is actually desirable: failed containers aren't reused; clean instances replace them.

### 4. "Namespaces provide security isolation"
**Reality**: Namespaces are for organization, not security. By default:
- Pods in different namespaces can communicate
- No network isolation without Network Policies

For true isolation, use:
- Network Policies
- RBAC
- Pod Security Policies/Standards
- Separate clusters

### 5. "StatefulSets are required for data consistency"
**Reality**: StatefulSets provide stable Pod names and ordered creation. They don't guarantee data consistency. That's your application's responsibility.

A StatefulSet running 3 replicas of a database still requires:
- Proper replication logic (PostgreSQL primary-replica, MongoDB replica set)
- Careful backup strategy
- Understanding of split-brain scenarios

### 6. "More nodes = better performance"
**Reality**: More nodes help with:
- Availability (Pod distribution)
- Resource capacity
- Fault tolerance

But performance depends on:
- Pod resource requests/limits
- Application efficiency
- Network latency
- Storage performance

Adding nodes without understanding bottlenecks doesn't help.

### 7. "kubectl delete pod will recreate it"
**Reality**: Only if the Pod is managed by a controller (Deployment, StatefulSet, DaemonSet).
- If you `kubectl run nginx --image=nginx`, get the Pod name, and delete it: **it's gone**
- If you deploy via Deployment and delete a Pod: **Deployment creates a new one**

### 8. "Environment variables in Kubernetes are permanent"
**Reality**: Pod environment variables are set at Pod creation time. Changing a ConfigMap doesn't update running Pods.

You must:
1. Update ConfigMap
2. Restart Pods (via rolling update, restart policy, etc.)
3. New Pods use updated ConfigMap

This is why immutable deployments (new image version = new Pods) are simpler than mutating configuration.

## Production Considerations

### High Availability
- Multiple control-plane nodes (3, 5, or 7 for HA)
- Distribute worker nodes across availability zones
- Pod anti-affinity for critical workloads
- Test failure scenarios regularly

### Backup & Disaster Recovery
- Regular etcd backups (different from application data)
- Document recovery procedures
- Test recovery procedures (not hypothetical)

### Cluster Access & Authorization
- RBAC for role-based access
- Service accounts for workload identity
- Audit logging for compliance
- Separate kubeconfig contexts per environment

### Resource Management
- Set requests/limits on all Pods
- Resource quotas per namespace
- Monitor cluster capacity
- Plan for growth

### Observability
- Logging aggregation (ELK, Loki, Splunk)
- Metrics collection (Prometheus)
- Distributed tracing (Jaeger)
- Alerting on cluster and application health

## Key Takeaways

1. Kubernetes is a **declarative system**: you define desired state; controllers make it happen
2. **Architecture is fixed**: Control Plane + Worker Nodes with specific components
3. **Objects are the API**: Everything (Pods, Services, ConfigMaps) is an object with desired and actual state
4. **Namespaces organize** but don't secure
5. **Controllers reconcile** state infinitely
6. **Pods are ephemeral**; use higher-level abstractions (Deployments)

---

## Practice Questions

### MCQ Questions

1. In a Kubernetes cluster, which component stores all cluster state?
   A) API Server  
   B) Scheduler  
   C) etcd  
   D) kubelet  

2. What is the primary role of the Scheduler?
   A) Run containers on nodes  
   B) Assign Pods to Nodes based on resource availability  
   C) Manage Service discovery  
   D) Store cluster state  

3. If a Pod crashes, what happens by default?
   A) The kubelet restarts the container inside the same Pod  
   B) A Deployment creates a completely new Pod  
   C) The Pod is reused after cleanup  
   D) Nothing; the Pod remains crashed  

4. Which resource is cluster-scoped (not namespace-scoped)?
   A) Deployment  
   B) Service  
   C) PersistentVolume  
   D) ConfigMap  

5. What does a namespace provide in Kubernetes?
   A) Security isolation preventing pod-to-pod communication  
   B) Logical isolation and resource quotas  
   C) Automatic encryption of traffic  
   D) Pod scheduling constraints  

### Hands-on Cluster Tasks

**Task 1: Inspect Cluster Architecture**

Prerequisites: Access to a running Kubernetes cluster (kind, minikube, or cloud-managed)

1. List all nodes in the cluster:
   ```bash
   kubectl get nodes -o wide
   ```

2. Inspect control-plane components:
   ```bash
   kubectl get pods -n kube-system
   ```

3. Check API Server logs (if on control-plane machine):
   ```bash
   journalctl -u kubelet -f
   ```

4. Query cluster info:
   ```bash
   kubectl cluster-info
   ```

5. Get detailed node information:
   ```bash
   kubectl describe node <node-name>
   ```

**Expected output understanding**:
- You should see kubelet, kube-proxy, and CNI plugin running on nodes
- kube-system namespace contains API Server pod, Scheduler pod, Controller Manager pod
- Nodes have different statuses (Ready, NotReady, SchedulingDisabled)

**Task 2: Understand Desired vs Actual State**

1. Create a simple Deployment:
   ```bash
   kubectl create deployment test-app --image=nginx:1.21 --replicas=3
   ```

2. View the Deployment (desired state):
   ```bash
   kubectl get deployment test-app -o yaml
   ```

3. View Pods created by the Deployment (actual state):
   ```bash
   kubectl get pods -l app=test-app
   ```

4. Simulate failure: delete a Pod
   ```bash
   kubectl delete pod <pod-name>
   ```

5. Observe Deployment controller creating a new Pod:
   ```bash
   kubectl get pods -l app=test-app --watch
   ```

6. Scale the Deployment:
   ```bash
   kubectl scale deployment test-app --replicas=5
   ```

7. Observe new Pods created:
   ```bash
   kubectl get pods -l app=test-app
   ```

8. Cleanup:
   ```bash
   kubectl delete deployment test-app
   ```

**Learning outcomes**:
- Desired state (Deployment with 3 replicas) vs actual state (3 running Pods)
- Reconciliation: deleting a Pod → Deployment creates a new one
- Scaling changes desired state → Deployment adjusts actual state

### Realistic Production Failure Scenario

**Scenario: Node Failure During Deployment**

You have a 3-node cluster with a critical backend service. You're deploying version 2.0 of your API.

```bash
# Current state: Deployment with 3 replicas across 3 nodes
kubectl get pods -o wide
# NAME                    READY   STATUS    RESTARTS   AGE   IP        NODE
# api-server-xyz-1        1/1     Running   0          5m    10.0.0.1  node-1
# api-server-xyz-2        1/1     Running   0          5m    10.0.0.2  node-2
# api-server-xyz-3        1/1     Running   0          5m    10.0.0.3  node-3

# Start rolling update to v2.0
kubectl set image deployment/api-server api=myrepo/api:v2.0
```

**The failure**: Node-2 crashes during the rolling update.

**What happens**:
1. Node-2 becomes unreachable (NotReady)
2. Deployment has 2 running replicas (on node-1 and node-3)
3. kubelet on node-2 can't report Pod status (it's down)
4. After ~5 minutes (pod eviction timeout), Kubernetes considers Pods on node-2 as failed
5. Deployment controller sees only 2 replicas running, needs 3
6. Creates a new Pod on node-3 (or node-1, depending on capacity)
7. Rolling update continues with the new Pod

**Important nuances**:
- The old Pod on node-2 doesn't automatically disappear immediately (node is offline)
- After eviction timeout, the Pod is considered terminated
- Application must handle traffic temporarily going to fewer Pods (2 instead of 3)
- Rolling update pauses until healthy replicas are achieved

**Production mitigations**:
1. Set `minAvailable` in PodDisruptionBudget to prevent simultaneous Pod evictions
2. Use pod anti-affinity to spread replicas across nodes
3. Implement load balancing to handle fewer Pods gracefully
4. Monitor node health and drain failing nodes before they crash
5. Use multiple availability zones (cloud) to survive zone failures

---

## Further Reading

- Kubernetes Documentation: https://kubernetes.io/docs/
- Kubernetes Architecture: https://kubernetes.io/docs/concepts/overview/components/
- etcd: https://etcd.io/
- CKA Exam Topics: https://www.cncf.io/certification/cka/
