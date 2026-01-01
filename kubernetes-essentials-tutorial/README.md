# Kubernetes Essentials Tutorial

**A Comprehensive, Production-Oriented Guide to Kubernetes for DevOps Engineers and CKA Certification**

## Quick Start

```bash
# Start with Kubernetes Fundamentals
cd docs/
cat 01-kubernetes-fundamentals.md

# Follow the modules sequentially for best learning
# Then test with hands-on labs in /labs/
# Finish with the final project
```

## What This Tutorial Covers

This is a **complete, professional-grade Kubernetes tutorial** designed to:

✅ **Teach real Kubernetes concepts** used in production systems  
✅ **Prepare for CKA (Certified Kubernetes Administrator) exam**  
✅ **Build practical, deployable infrastructure**  
✅ **Teach debugging and troubleshooting techniques**  
✅ **Cover security, monitoring, and operations**  
✅ **Include real failure scenarios** and recovery patterns  

## Who This Is For

- **DevOps Engineers** building and managing Kubernetes clusters
- **Backend Engineers** deploying containerized applications
- **Platform Engineers** creating internal developer platforms
- **SREs** managing production Kubernetes systems
- **Anyone preparing for CKA certification**

## Prerequisites

- **Linux environment** (Linux, macOS, or WSL2)
- **Docker knowledge** (containers, images, Dockerfile)
- **Basic networking** (TCP/IP, DNS, ports)
- **Command-line comfort** (bash, file operations)

**Not required but helpful**:
- Cloud platform experience (AWS, GCP, Azure)
- Python or application development basics
- CI/CD pipeline familiarity

## Tutorial Structure

### 12 Core Modules (550-700 lines each)

| Module | Topic | Focus |
|--------|-------|-------|
| 1 | **Kubernetes Fundamentals** | Architecture, components, cluster lifecycle |
| 2 | **kubectl & Cluster Interaction** | CLI usage, contexts, debugging |
| 3 | **Pods & Workloads** | Deployments, StatefulSets, DaemonSets, Jobs |
| 4 | **Services & Networking** | Service types, Ingress, NetworkPolicies |
| 5 | **ConfigMaps & Secrets** | Configuration management, encryption |
| 6 | **Storage & Volumes** | PV/PVC, StorageClass, Snapshots |
| 7 | **Resource Management** | Requests/limits, QoS, HPA, Quotas |
| 8 | **Health, Probes & Logging** | Readiness/liveness, structured logging |
| 9 | **RBAC & Security** | Roles, ServiceAccounts, SecurityContext |
| 10 | **Helm & Package Management** | Charts, templating, best practices |
| 11 | **Advanced Cluster Operations** | Upgrades, backups, disaster recovery |
| 12 | **Kubernetes in CI/CD** | Docker integration, GitOps, multi-environment |

### Each Module Contains

📖 **Comprehensive Explanations**
- Architecture diagrams (text-based)
- Concept overviews with examples
- YAML manifest examples
- kubectl command reference

🛠️ **Production Patterns**
- Real-world use cases
- Common mistakes (5 per module)
- Best practices
- Security considerations

✅ **Practice Questions**
- 5 multiple-choice questions per module
- Answer key with explanations
- Realistic scenarios

🧪 **Hands-on Cluster Tasks**
- 2 tasks per module
- Step-by-step instructions
- Real cluster testing
- Validation procedures

⚠️ **Realistic Failure Scenarios**
- Production-like problems
- Root cause analysis
- Resolution steps
- Prevention strategies

## Learning Path Recommendations

### For CKA Exam Preparation (60 hours)

1. **Week 1**: Modules 1-2 (Fundamentals & kubectl)
2. **Week 2**: Modules 3-4 (Workloads & Services)
3. **Week 3**: Modules 5-6 (Configuration & Storage)
4. **Week 4**: Modules 7-8 (Resources & Observability)
5. **Week 5**: Modules 9-10 (Security & Helm)
6. **Week 6**: Module 11 (Advanced Operations)
7. **Week 7**: Module 12 + Exam Practice (60 questions)
8. **Week 8**: Final Project + Mock Exam

### For Production Deployments (40 hours)

1. **Days 1-2**: Modules 1-3 (Architecture & Deployments)
2. **Days 3-4**: Modules 4-6 (Networking & Storage)
3. **Days 5-6**: Modules 7-8 (Resources & Health)
4. **Days 7-8**: Modules 9-12 (Security, Helm, CI/CD)
5. **Days 9-10**: Final Project (Deploy real application)

### For Infrastructure Platform (50 hours)

1. **Week 1**: Modules 1-4 (Core concepts)
2. **Week 2**: Modules 5-7 (Configuration, Storage, Resources)
3. **Week 3**: Modules 8-11 (Observability, Security, Operations)
4. **Week 4**: Module 12 + Final Project
5. **Week 5**: Advanced topics (Multi-cluster, networking)

## Directory Structure

```
kubernetes-essentials-tutorial/
├── README.md                              # This file
├── EXAM_AND_PRACTICE.md                   # 60 MCQ + answers + tasks
├── FINAL_PROJECT.md                       # Production e-commerce backend
├── docs/
│   ├── 01-kubernetes-fundamentals.md      # (550+ lines)
│   ├── 02-kubectl-cluster-interaction.md  # (600+ lines)
│   ├── 03-pods-workloads.md               # (700+ lines)
│   ├── 04-services-networking.md          # (600+ lines)
│   ├── 05-configmaps-secrets.md           # (550+ lines)
│   ├── 06-storage-volumes.md              # (650+ lines)
│   ├── 07-resource-management.md          # (600+ lines)
│   ├── 08-health-probes-logging.md        # (550+ lines)
│   ├── 09-rbac-security.md                # (700+ lines)
│   ├── 10-helm-package-management.md      # (650+ lines)
│   ├── 11-advanced-cluster-operations.md  # (700+ lines)
│   └── 12-kubernetes-cicd-docker.md       # (650+ lines)
├── examples/                              # YAML manifests (to be created)
│   ├── 01-basic-pod.yaml
│   ├── 02-deployment.yaml
│   ├── 03-statefulset.yaml
│   ├── 04-service.yaml
│   ├── 05-configmap-secret.yaml
│   └── ... (examples for each module)
└── labs/                                  # Step-by-step lab guides (to be created)
    ├── lab-01-cluster-setup.md
    ├── lab-02-pod-deployment.md
    └── ... (lab instructions for each module)
```

## Getting Started with a Kubernetes Cluster

### Option 1: Local Cluster with kind (Recommended for Learning)

```bash
# Install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster --name learning

# Verify
kubectl cluster-info
kubectl get nodes
```

### Option 2: Minikube

```bash
# Install minikube
curl -LO https://github.com/kubernetes/minikube/releases/download/v1.31.0/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start cluster
minikube start --cpus=4 --memory=4096

# Verify
kubectl cluster-info
kubectl get nodes
```

### Option 3: Cloud Provider Managed Kubernetes

```bash
# AWS EKS
aws eks create-cluster --name learning-cluster ...

# Google Cloud GKE
gcloud container clusters create learning-cluster ...

# Azure AKS
az aks create --resource-group myGroup --name learning-cluster ...
```

## Setting Up Your Learning Environment

```bash
# Clone this tutorial
git clone https://github.com/your-org/kubernetes-essentials-tutorial
cd kubernetes-essentials-tutorial

# Create a practice namespace
kubectl create namespace learning

# Install useful tools
# kubectl-debug plugin
curl -Lo ./kubectl-debug.tar.gz https://github.com/JamesTGrant/kubectl-debug/releases/download/v0.1.1/kubectl-debug_0.1.1_linux_amd64.tar.gz
tar -xzf kubectl-debug.tar.gz
sudo mv ./kubectl-debug /usr/local/bin/

# kubectx (context switching)
git clone https://github.com/ahmetb/kubectx.git
sudo mv kubectx/kubectx /usr/local/bin/

# k9s (TUI cluster manager)
curl -Lo k9s.tar.gz https://github.com/derailed/k9s/releases/download/v0.28.0/k9s_Linux_amd64.tar.gz
tar -xzf k9s.tar.gz
sudo mv k9s /usr/local/bin/
```

## Module Topics At a Glance

### Module 1: Kubernetes Fundamentals
- Control plane components (API Server, Scheduler, Controller Manager, etcd)
- Worker node components (kubelet, kube-proxy, container runtime)
- Pod networking model (CNI)
- Cluster roles and resource types
- Common misconceptions

### Module 2: kubectl & Cluster Interaction
- kubeconfig setup and management
- Context switching and cluster configuration
- Declarative vs imperative approaches
- Debugging broken deployments
- Advanced output formatting and queries

### Module 3: Pods & Workloads
- Pod anatomy (containers, volumes, init containers)
- Deployment rolling updates
- StatefulSet for stateful applications
- DaemonSet for node-wide services
- Job and CronJob for batch processing
- Pod scheduling and affinity rules

### Module 4: Services & Networking
- ClusterIP, NodePort, LoadBalancer services
- Service discovery via DNS
- Ingress for HTTP/HTTPS routing
- Network Policies for traffic control
- Multi-cluster networking patterns

### Module 5: ConfigMaps & Secrets
- Configuration management approaches
- Secret encryption and rotation
- ConfigMap update strategies
- External secret managers
- Secure credential handling

### Module 6: Storage & Volumes
- Volume types (EmptyDir, HostPath, NFS, etc.)
- Persistent Volumes and Claims
- StorageClass for dynamic provisioning
- StatefulSet persistent storage patterns
- Snapshot and restoration

### Module 7: Resource Management
- CPU and memory requests/limits
- QoS classes and eviction behavior
- Resource Quotas and Limit Ranges
- Horizontal Pod Autoscaler (HPA)
- Vertical Pod Autoscaler (VPA)
- Pod Priority and Preemption

### Module 8: Health, Probes & Logging
- Liveness probes (restart on failure)
- Readiness probes (remove from traffic)
- Startup probes (delay health checks)
- Centralized logging architecture
- Prometheus metrics collection
- ELK stack integration

### Module 9: RBAC & Security
- Role-Based Access Control (RBAC)
- Roles, ClusterRoles, RoleBindings
- ServiceAccounts for Pod identity
- SecurityContext (user, capabilities, filesystem)
- Pod Security Standards
- Network Policies

### Module 10: Helm & Package Management
- Helm chart structure and anatomy
- Values and templating
- Chart repositories
- Subcharts and dependencies
- Helm lifecycle and updates
- Production patterns

### Module 11: Advanced Cluster Operations
- Horizontal Pod Autoscaler (HPA) deep dive
- Rolling deployments and blue-green
- Taints and tolerations for node management
- Node draining and eviction
- Pod Disruption Budgets
- etcd backup and disaster recovery
- Cluster upgrades and maintenance

### Module 12: Kubernetes in CI/CD & Docker Integration
- Docker best practices for Kubernetes
- Multi-stage Docker builds
- Image tagging strategies
- Multi-environment deployments (Kustomize, Helm)
- GitOps with ArgoCD
- CI/CD pipeline integration
- Container registry management

## Study Tips

1. **Type YAML manually** - Don't copy-paste. Understanding comes from typing.

2. **Create your own manifests** - After reading examples, write from scratch.

3. **Test immediately** - Read module → deploy to cluster → verify behavior.

4. **Use kubectl explain** - Quick inline API documentation
   ```bash
   kubectl explain pod.spec.containers
   ```

5. **Read error messages carefully** - They usually indicate the root cause.

6. **Debug with kubectl describe** - Best tool for understanding Pod issues
   ```bash
   kubectl describe pod <name>
   ```

7. **Check logs frequently** - Most problems visible in logs
   ```bash
   kubectl logs <pod> -f
   ```

8. **Use dry-run for safety** - Test before applying
   ```bash
   kubectl apply -f manifest.yaml --dry-run=server
   ```

9. **Review the failure scenarios** - Understand how to prevent/recover from failures.

10. **Do the hands-on tasks** - Reading alone won't prepare you for real usage.

## Practice Questions

- **Total**: 60 MCQ questions (5 per module)
- **Location**: `EXAM_AND_PRACTICE.md`
- **Format**: Multiple choice with answer key
- **Time estimate**: 2-3 hours for all questions
- **CKA alignment**: Questions focus on practical, exam-relevant scenarios

## Final Project

**Project**: Production-Ready E-commerce Backend
- **Duration**: 8-10 hours
- **Location**: `FINAL_PROJECT.md`
- **Components**: Multi-tier Flask API, PostgreSQL database, Redis cache
- **Requirements**: HA, RBAC, secrets, storage, monitoring, CI/CD
- **Success Criteria**: 12-point checklist for production readiness

## Troubleshooting Common Issues

### Cluster Setup

**Problem**: `kubectl: connection refused`
```bash
# Solution: Check kubeconfig
echo $KUBECONFIG
kubectl config current-context
kubectl cluster-info
```

**Problem**: Pods stuck in Pending
```bash
# Solution: Check node resources
kubectl describe nodes
kubectl top nodes
# Likely: insufficient CPU/memory resources
```

### Pod Issues

**Problem**: Pods crash immediately
```bash
# Solution: Check logs and events
kubectl logs <pod>
kubectl describe pod <pod>
# Look for: image pull errors, resource limits, misconfigurations
```

**Problem**: Readiness probe failing
```bash
# Solution: Test endpoint manually
kubectl port-forward <pod> 8080:8080
curl http://localhost:8080/health
# Likely: app not ready, health endpoint wrong, timeout too short
```

### Networking

**Problem**: Pods can't reach service
```bash
# Solution: Check service endpoints
kubectl get endpoints <service>
kubectl logs -f <pod>
# Likely: Pod label mismatch, selector wrong, port mismatch
```

**Problem**: External traffic not reaching cluster
```bash
# Solution: Check Ingress
kubectl get ingress
kubectl describe ingress <name>
# Likely: TLS cert missing, host mismatch, controller not installed
```

## Resources & Further Learning

### Official Documentation
- [Kubernetes Official Docs](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [API Reference](https://kubernetes.io/docs/reference/generated/kubernetes-api/)

### Exam Preparation
- [CKA Exam Curriculum](https://github.com/cncf/curriculum)
- [CKA Exam Tips](https://www.kubernetes.io/docs/tasks/tools/)

### Hands-on Practice
- [Kubernetes The Hard Way](https://github.com/kelseyhightower/kubernetes-the-hard-way)
- [KodeKloud CKA Labs](https://kodekloud.com/courses/kubernetes-certification-course/)
- [Linux Academy Labs](https://linuxacademy.com/)

### Tools & Utilities
- [kind - Kubernetes in Docker](https://kind.sigs.k8s.io/)
- [minikube](https://minikube.sigs.k8s.io/)
- [k9s - Kubernetes TUI](https://k9scli.io/)
- [kubectx/kubens](https://github.com/ahmetb/kubectx)

### Community
- [Kubernetes Slack](https://kubernetes.slack.com/)
- [CNCF Community](https://www.cncf.io/community/)
- [Stack Overflow tag: kubernetes](https://stackoverflow.com/questions/tagged/kubernetes)

## Contributing

Found an issue or have suggestions? 

- Submit issues on GitHub
- Update outdated content
- Add more examples
- Improve explanations

## License

This tutorial is provided for educational purposes. 

---

## Quick Command Reference

### Cluster Management
```bash
kubectl cluster-info                    # Cluster information
kubectl get nodes                       # List nodes
kubectl describe node <name>            # Node details
kubectl top nodes                       # Resource usage
```

### Pod Management
```bash
kubectl get pods -A                     # All pods all namespaces
kubectl get pods -n <ns> -o wide        # Pods with IP info
kubectl describe pod <name>             # Detailed pod info
kubectl logs <pod>                      # Container logs
kubectl logs <pod> --previous           # Previous container logs
kubectl exec -it <pod> -- /bin/sh       # Shell into pod
```

### Debugging
```bash
kubectl logs <pod> --follow             # Stream logs
kubectl describe events -n <ns>         # Recent events
kubectl get events -A --sort-by='.lastTimestamp'  # All events
kubectl debug <pod> -it --image=busybox # Debug container
```

### Deployment Management
```bash
kubectl apply -f <file.yaml>            # Apply manifest
kubectl apply -k <dir>                  # Apply Kustomize
kubectl set image deployment/app app=img:v2  # Update image
kubectl rollout status deployment/app   # Watch rollout
kubectl rollout history deployment/app  # Rollout history
kubectl rollout undo deployment/app     # Rollback deployment
```

### Resource Management
```bash
kubectl get all -n <ns>                 # All resources
kubectl delete pod <name>               # Delete pod
kubectl delete deployment <name>        # Delete deployment
kubectl scale deployment <name> --replicas=3  # Scale replicas
```

---

## Next Steps

1. **Start with Module 1**: Read Kubernetes Fundamentals
2. **Set up cluster**: Create a kind/minikube cluster
3. **Work through modules**: 1-3 hours per module
4. **Do hands-on tasks**: Cluster practice for each concept
5. **Review failure scenarios**: Understand prevention/recovery
6. **Practice with exam questions**: 60 MCQ with answers
7. **Build final project**: Deploy real multi-tier application
8. **Schedule CKA exam**: When ready (typically after 6-8 weeks)

---

**Happy learning! 🚀**

For questions, clarifications, or feedback, reach out to the community or file an issue.

---

Last Updated: 2024
Kubernetes Version: 1.24+
Tutorial Edition: 1.0 (Professional, Production-Oriented)
