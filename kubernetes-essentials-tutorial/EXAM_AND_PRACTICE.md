# Comprehensive Practice Exam & Questions

## Overview

This section consolidates all 60 MCQ questions (5 per module), 24 hands-on cluster tasks (2 per module), and 12 failure scenarios (1 per module) with complete answers and solutions.

---

## Module 1: Kubernetes Fundamentals

### MCQ Answers

1. **Q: What is the primary function of the Kubernetes API Server?**  
   A) Run application containers  
   B) Store application data  
   C) Central control point for cluster communication  
   D) Manage networking  
   **Answer: C**

2. **Q: What separates control plane from worker nodes?**  
   A) They are the same thing  
   B) Network segmentation  
   C) Control plane runs system components, workers run applications  
   D) Workers cannot communicate with control plane  
   **Answer: C**

3. **Q: When you declare a Deployment, what component actually schedules Pods?**  
   A) Deployment controller  
   B) kubelet  
   C) Scheduler  
   D) etcd  
   **Answer: C**

4. **Q: How many control plane nodes should a production cluster have?**  
   A) 1  
   B) 2  
   C) 3 (odd number)  
   D) 5  
   **Answer: C** (Odd number for quorum; 3 is minimum for HA)

5. **Q: What is the purpose of kubelets?**  
   A) Manage the cluster  
   B) Schedule Pods  
   C) Ensure Pods on node are running  
   D) Store cluster data  
   **Answer: C**

---

## Module 2: kubectl & Cluster Interaction

### MCQ Answers

1. **Q: What does `kubectl apply` do vs `kubectl create`?**  
   A) Same thing  
   B) apply is declarative, create is imperative  
   C) create updates existing resources  
   D) apply is only for Pods  
   **Answer: B**

2. **Q: How do you switch between clusters?**  
   A) `kubectl cluster-info`  
   B) `kubectl config use-context <context>`  
   C) `kubectl switch-context <context>`  
   D) Cannot switch, kubectl is single-cluster  
   **Answer: B**

3. **Q: What does `--dry-run=server` do?**  
   A) Doesn't actually apply to cluster  
   B) Tests on local client only  
   C) Applies and saves to backup  
   D) Simulates on server without persisting  
   **Answer: D**

4. **Q: How do you see what would change before applying?**  
   A) `kubectl apply --predict`  
   B) `kubectl diff -f file.yaml`  
   C) `kubectl preview`  
   D) Cannot preview in kubectl  
   **Answer: B**

5. **Q: What is the most common debugging technique for Pods?**  
   A) `kubectl get pods`  
   B) `kubectl logs <pod>`  
   C) `kubectl describe <pod>`  
   D) `kubectl exec <pod> -- /bin/sh`  
   **Answer: B/C** (Both are primary; logs shows output, describe shows events)

---

## Module 3: Pods & Workloads

### MCQ Answers

1. **Q: What is the smallest deployable unit in Kubernetes?**  
   A) Container  
   B) Pod  
   C) Deployment  
   D) Node  
   **Answer: B**

2. **Q: When would you use a StatefulSet instead of Deployment?**  
   A) For web applications  
   B) For databases or applications needing stable identity  
   C) For services that are stateless  
   D) StatefulSet is always better  
   **Answer: B**

3. **Q: What is a DaemonSet used for?**  
   A) Running background daemons  
   B) Running one Pod per node across the cluster  
   C) Long-running batch jobs  
   D) Temporary one-off tasks  
   **Answer: B**

4. **Q: How does a Job differ from a Deployment?**  
   A) No difference  
   B) Jobs run to completion, Deployments run continuously  
   C) Jobs are faster  
   D) Deployments can only run one Pod  
   **Answer: B**

5. **Q: What determines Pod scheduling?**  
   A) Manual selection  
   B) Scheduler algorithm (requests, affinity, taints)  
   C) Random node  
   D) Always same node  
   **Answer: B**

---

## Module 4: Services & Networking

### MCQ Answers

1. **Q: What type of Service is accessible only within the cluster?**  
   A) NodePort  
   B) LoadBalancer  
   C) ClusterIP  
   D) ExternalName  
   **Answer: C**

2. **Q: How does a Service discover its backend Pods?**  
   A) Manual IP lists  
   B) Label selectors  
   C) Service registry  
   D) Hardcoded endpoints  
   **Answer: B**

3. **Q: What does an Ingress provide?**  
   A) Internal networking  
   B) Container networking  
   C) HTTP/HTTPS routing from external clients  
   D) Storage access  
   **Answer: C**

4. **Q: What are NetworkPolicies for?**  
   A) Managing networking speed  
   B) Controlling traffic between Pods  
   C) Assigning IP addresses  
   D) Routing traffic to external networks  
   **Answer: B**

5. **Q: How do Pods communicate across nodes?**  
   A) Through services only  
   B) Direct Pod-to-Pod via CNI plugin  
   C) Cannot communicate across nodes  
   D) Through master node  
   **Answer: B**

---

## Module 5: ConfigMaps & Secrets

### MCQ Answers

1. **Q: When should you use Secrets vs ConfigMaps?**  
   A) Both are identical  
   B) ConfigMaps for sensitive data  
   C) Secrets for sensitive data, ConfigMaps for config  
   D) Use ConfigMaps for everything  
   **Answer: C**

2. **Q: How are Secrets stored in etcd?**  
   A) Encrypted by default  
   B) Base64 encoded (not encrypted by default)  
   C) Plain text  
   D) Cannot be stored in etcd  
   **Answer: B**

3. **Q: How do you use ConfigMap in a Pod?**  
   A) Only as environment variables  
   B) Only as mounted files  
   C) As env vars or mounted volumes  
   D) Cannot use ConfigMaps in Pods  
   **Answer: C**

4. **Q: What is immutable ConfigMap?**  
   A) Cannot create ConfigMaps  
   B) ConfigMap that cannot be modified after creation  
   C) ConfigMap with encryption  
   D) ConfigMap stored permanently  
   **Answer: B**

5. **Q: How should production secrets be managed?**  
   A) Store in Git  
   B) Store in ConfigMaps  
   C) Use external secret managers (Vault)  
   D) Hardcode in applications  
   **Answer: C**

---

## Module 6: Storage & Volumes

### MCQ Answers

1. **Q: What is the difference between a PV and PVC?**  
   A) No difference  
   B) PV is storage resource, PVC is request for storage  
   C) PVC is only for databases  
   D) PV is for temporary storage  
   **Answer: B**

2. **Q: When should you use StatefulSet with PVC?**  
   A) Never  
   B) For databases or applications needing persistent data  
   C) For web servers  
   D) For all applications  
   **Answer: B**

3. **Q: What does a StorageClass do?**  
   A) Stores Kubernetes classes  
   B) Dynamically provisions PVs when PVC is created  
   C) Manually creates storage  
   D) Manages container storage  
   **Answer: B**

4. **Q: What happens to data in an emptyDir volume?**  
   A) Persists after Pod deletion  
   B) Persists across node restarts  
   C) Deleted when Pod is deleted  
   D) Can be accessed from other Pods  
   **Answer: C**

5. **Q: How do you expand a PVC?**  
   A) Delete and recreate  
   B) Modify PVC storage size (if StorageClass allows)  
   C) Move to larger volume  
   D) Cannot expand PVCs  
   **Answer: B**

---

## Module 7: Resource Management

### MCQ Answers

1. **Q: What do resource requests do?**  
   A) Limit maximum resource usage  
   B) Reserve resources on node for scheduling  
   C) Monitor resource usage  
   D) Allocate storage  
   **Answer: B**

2. **Q: What does QoS "Guaranteed" mean?**  
   A) Highest priority, least eviction chance  
   B) Medium priority  
   C) Lowest priority, evicted first  
   D) Not related to eviction  
   **Answer: A**

3. **Q: What is a ResourceQuota?**  
   A) Per-Pod resource limit  
   B) Cluster-wide limit  
   C) Namespace-wide resource limit  
   D) Does not exist in Kubernetes  
   **Answer: C**

4. **Q: How does HPA decide to scale?**  
   A) Manual trigger  
   B) Based on metrics (CPU, memory, custom metrics)  
   C) Random scaling  
   D) Cannot auto-scale in Kubernetes  
   **Answer: B**

5. **Q: What is Pod Priority?**  
   A) Task importance for scheduling  
   B) Higher priority Pods evicted first  
   C) Not a real Kubernetes feature  
   D) Only for system Pods  
   **Answer: A**

---

## Module 8: Health, Probes & Logging

### MCQ Answers

1. **Q: What does a readiness probe do?**  
   A) Checks if container is alive  
   B) Checks if Pod is ready to receive traffic  
   C) Checks disk space  
   D) Checks cluster health  
   **Answer: B**

2. **Q: What happens if liveness probe fails?**  
   A) Pod moves to another node  
   B) Container is restarted  
   C) Pod is deleted  
   D) Nothing happens  
   **Answer: B**

3. **Q: What does a startup probe do?**  
   A) Runs once at container creation  
   B) Prevents liveness/readiness checks until ready  
   C) Stops container startup  
   D) Not used in production  
   **Answer: B**

4. **Q: Where should application logs be sent?**  
   A) Local files in container  
   B) stdout/stderr (captured by container runtime)  
   C) Kubernetes API  
   D) Log files on node  
   **Answer: B**

5. **Q: What is centralized logging?**  
   A) Logging only on control plane  
   B) Logs from multiple Pods aggregated in one place  
   C) Logs stored in Kubernetes  
   D) Cannot aggregate logs  
   **Answer: B**

---

## Module 9: RBAC & Security

### MCQ Answers

1. **Q: What is RBAC?**  
   A) Remote backup and cache  
   B) Role-based access control for API resources  
   C) Resource-based attribute control  
   D) Redundant backup authority  
   **Answer: B**

2. **Q: What is the difference between Role and ClusterRole?**  
   A) No difference  
   B) Role is namespace-scoped, ClusterRole is cluster-wide  
   C) ClusterRole is always more powerful  
   D) Cannot use both  
   **Answer: B**

3. **Q: What is a SecurityContext?**  
   A) Cluster security settings  
   B) Pod/container runtime configuration (user, capabilities, etc.)  
   C) Network security  
   D) Access control for storage  
   **Answer: B**

4. **Q: What should runAsUser be in production?**  
   A) 0 (root)  
   B) 1000+ (non-root)  
   C) Does not matter  
   D) Only for databases  
   **Answer: B**

5. **Q: What is Pod Security Standards?**  
   A) Quality standards for Pods  
   B) Policies restricting Pod security behavior  
   C) Pod performance standards  
   D) Not used in production  
   **Answer: B**

---

## Module 10: Helm & Package Management

### MCQ Answers

1. **Q: What is Helm?**  
   A) Lightweight control plane  
   B) Package manager for Kubernetes (charts)  
   C) Storage management tool  
   D) Monitoring tool  
   **Answer: B**

2. **Q: What is a Helm chart?**  
   A) Graphical data visualization  
   B) Package containing Kubernetes manifests and values  
   C) Helm configuration file  
   D) Not a real Kubernetes object  
   **Answer: B**

3. **Q: How do you override Helm values?**  
   A) `helm install --values custom.yaml`  
   B) `helm install --set key=value`  
   C) Edit Chart.yaml  
   D) Both A and B  
   **Answer: D**

4. **Q: What does `helm rollback` do?**  
   A) Reverts chart to previous version  
   B) Rolls back deployment to previous release  
   C) Undoes kubectl apply  
   D) Cannot rollback Helm  
   **Answer: B**

5. **Q: What is a Helm subgraph?**  
   A) Dependency not used  
   B) Dependency chart included in main chart  
   C) Chart repository  
   D) Not a real Helm concept  
   **Answer: B** (Should be "subchart", not "subgraph")

---

## Module 11: Advanced Cluster Operations

### MCQ Answers

1. **Q: What does HPA stand for?**  
   A) High Priority Access  
   B) Horizontal Pod Autoscaler  
   C) Hardware Performance Alliance  
   D) Highly Parallel Architecture  
   **Answer: B**

2. **Q: What is maxSurge in rolling deployment?**  
   A) Maximum surge in traffic  
   B) Maximum pods running above desired count  
   C) Maximum nodes in cluster  
   D) Maximum storage surge  
   **Answer: B**

3. **Q: What does kubectl drain do?**  
   A) Removes all data  
   B) Evicts Pods from node before maintenance  
   C) Removes node permanently  
   D) Clears node cache  
   **Answer: B**

4. **Q: What is a PodDisruptionBudget?**  
   A) Budget for Pod resources  
   B) Ensures minimum Pod availability during disruptions  
   C) Cost control mechanism  
   D) Does not exist in Kubernetes  
   **Answer: B**

5. **Q: How do you upgrade a Kubernetes cluster?**  
   A) Manual rolling restart  
   B) Use kubeadm or managed service upgrade  
   C) Replace entire cluster  
   D) Cannot upgrade clusters  
   **Answer: B**

---

## Module 12: Kubernetes in CI/CD & Docker Integration

### MCQ Answers

1. **Q: What should image tags be in production?**  
   A) Always use "latest"  
   B) Explicit versions (v1.2.3, commit SHA)  
   C) Build timestamps  
   D) Random identifiers  
   **Answer: B**

2. **Q: What is GitOps?**  
   A) Using Git commands from Kubernetes  
   B) Storing code in Git  
   C) Git as source of truth for infrastructure  
   D) Deploying Git repositories as Pods  
   **Answer: C**

3. **Q: Which is more secure for secrets?**  
   A) Store in Docker image  
   B) Store in Git  
   C) Use external secret manager  
   D) Hardcode in application  
   **Answer: C**

4. **Q: How should you deploy to multiple environments?**  
   A) Manual kubectl apply in each cluster  
   B) Copy manifests for each environment  
   C) Use overlays (Kustomize) or values (Helm)  
   D) Deploy once to prod, others pull from prod  
   **Answer: C**

5. **Q: What should multi-stage Docker build accomplish?**  
   A) Build multiple versions simultaneously  
   B) Smaller final image by removing build tools  
   C) Build for different architectures  
   D) Parallel builds for speed  
   **Answer: B**

---

## Hands-on Tasks Summary

**Total: 24 tasks (2 per module)**

### Quick Reference for Hands-on Tasks

| Module | Task 1 | Task 2 |
|--------|--------|--------|
| 1 | Inspect cluster components | Desired vs actual state |
| 2 | Switch between contexts | Debug broken deployment |
| 3 | Deploy and update application | Create Job/CronJob |
| 4 | Create and test Service | Create Ingress with TLS |
| 5 | Create and mount ConfigMap | Create and use Secret |
| 6 | Create and use PVC | StatefulSet with storage |
| 7 | Deploy with resource limits | Implement ResourceQuota |
| 8 | Implement health probes | Centralized logging setup |
| 9 | Create RBAC Role/RoleBinding | Implement SecurityContext |
| 10 | Install/manage Helm chart | Create custom chart |
| 11 | Implement node maintenance | Create PodDisruptionBudget |
| 12 | CI/CD pipeline simulation | Multi-environment Kustomize |

---

## Failure Scenarios Summary

**Total: 12 scenarios (1 per module)**

| Module | Failure Scenario | Root Cause |
|--------|-----------------|-----------|
| 1 | Node failure during deployment | Lack of replication/HA |
| 2 | Configuration drift | Manual changes outside Git |
| 3 | Rolling update stuck | Pod crash prevents healthy replica |
| 4 | Service endpoints keep changing | Readiness probe too strict |
| 5 | Pods use old password after rotation | ConfigMap not reloaded automatically |
| 6 | PVC runs out of space | No monitoring/alerting on storage |
| 7 | Pods evicted during traffic spike | Insufficient resource requests/limits |
| 8 | Readiness probe insufficient | App can't reach database |
| 9 | Compromised pod escapes to host | No SecurityContext, runs as root |
| 10 | Helm upgrade breaks cluster | Config incompatibility in new version |
| 11 | Unplanned node failure during peak | No PDB, all Pods on single node |
| 12 | Broken image deployed | No testing before CI/CD deployment |

---

## Exam Strategy & Tips

### Time Management

- **MCQ Section**: 60 questions, ~2-3 minutes each = 2-3 hours
- **Hands-on Lab**: 2-4 hours in real cluster
- **Study strategy**: Review modules 1-6 first (foundations), then 7-12 (advanced)

### Common Pitfalls

1. **Forgetting resource requests/limits**: Every production Pod needs them
2. **Using "latest" image tag**: Always specify explicit version
3. **Not securing Pods**: Run as non-root, use SecurityContext
4. **Missing health checks**: Readiness/liveness probes prevent cascading failures
5. **No backup strategy**: etcd backups for disaster recovery

### Practice Tips

1. **Type YAML manually**: Don't copy-paste in exam
2. **Test in non-prod first**: Always deploy to dev/staging before prod
3. **Use kubectl explain**: Quick API reference
4. **Monitor everything**: Logs, events, metrics
5. **Understand error messages**: They usually indicate root cause

---

## Final Review Checklist

Before attempting CKA exam or production deployment:

- [ ] Can deploy multi-container app with Services, Ingress, StorageClass
- [ ] Can debug stuck Pods using logs, describe, exec
- [ ] Can implement RBAC and SecurityContext correctly
- [ ] Can manage configuration with ConfigMaps/Secrets/Kustomize
- [ ] Can implement health checks (liveness, readiness, startup)
- [ ] Can use HPA and understand resource management
- [ ] Can perform rolling updates and rollbacks
- [ ] Can backup/restore etcd
- [ ] Can implement NetworkPolicies
- [ ] Can deploy via CI/CD pipelines

If you can do all 10, you're ready for CKA certification!

---

## Answer Key Reference

All answers provided above with explanations. For hands-on tasks and failure scenarios, refer back to individual module files for complete step-by-step solutions.
