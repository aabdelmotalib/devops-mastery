# Kubernetes Quick Reference & Cheat Sheet

## Kubectl Essential Commands

### Cluster & Context
```bash
kubectl cluster-info                    # Show cluster info
kubectl config current-context          # Show current context
kubectl config use-context <ctx>        # Switch context
kubectl config get-contexts             # List all contexts
kubectl api-resources                   # Available API resources
kubectl explain <resource>              # Resource documentation
```

### Getting Information
```bash
kubectl get <resource>                  # List resources
kubectl get <resource> -n <ns>          # In specific namespace
kubectl get <resource> -A               # All namespaces
kubectl get <resource> -o wide          # Wide output (more columns)
kubectl get <resource> -o yaml          # YAML format
kubectl get <resource> -o json          # JSON format
kubectl describe <resource> <name>      # Detailed info
```

### Common Resources
```bash
kubectl get pods                        # List all pods
kubectl get svc                         # List services
kubectl get deploy                      # List deployments
kubectl get statefulsets                # List StatefulSets
kubectl get pvc                         # List PersistentVolumeClaims
kubectl get pv                          # List PersistentVolumes
kubectl get nodes                       # List nodes
kubectl get ns                          # List namespaces
kubectl get events                      # Show events
```

### Creating & Updating
```bash
kubectl apply -f <file.yaml>            # Apply manifest (create or update)
kubectl apply -k <dir>                  # Apply Kustomize
kubectl create -f <file.yaml>           # Create resource
kubectl delete -f <file.yaml>           # Delete resource
kubectl delete <resource> <name>        # Delete specific resource
kubectl patch <resource> <name> -p '{}' # Patch resource
kubectl set image deploy/<name> app=img:v2  # Update image
```

### Debugging
```bash
kubectl logs <pod>                      # Get pod logs
kubectl logs <pod> -c <container>       # Logs from specific container
kubectl logs <pod> --previous           # Previous pod logs
kubectl logs <pod> -f                   # Stream logs
kubectl logs -l <key>=<val>             # Logs from labeled pods
kubectl describe pod <pod>              # Detailed pod info
kubectl get events -n <ns> --sort-by='.lastTimestamp'  # Recent events
kubectl exec -it <pod> -- /bin/sh       # Execute command in pod
kubectl exec -it <pod> -c <cont> -- /bin/bash # In specific container
kubectl port-forward <pod> 8080:8080    # Local port forwarding
kubectl top pods                        # Pod resource usage
kubectl top nodes                       # Node resource usage
```

### Troubleshooting
```bash
kubectl describe node <name>            # Node details & events
kubectl get pods --all-namespaces       # Find pod in all namespaces
kubectl debug <pod> -it                 # Debug pod (Kubernetes 1.25+)
kubectl debug <pod> -it --image=busybox # Debug with specific image
kubectl drain <node> --ignore-daemonsets # Safely evict pods from node
kubectl cordon <node>                   # Mark node unschedulable
kubectl uncordon <node>                 # Mark node schedulable
```

### Deployments & Rollouts
```bash
kubectl rollout status deploy/<name>    # Watch deployment status
kubectl rollout history deploy/<name>   # Deployment revisions
kubectl rollout undo deploy/<name>      # Rollback to previous
kubectl rollout undo deploy/<name> --to-revision=2  # Rollback to specific
kubectl scale deploy/<name> --replicas=5  # Change replica count
kubectl autoscale deploy/<name> --min=2 --max=10  # Create HPA
```

### Dry Run & Preview
```bash
kubectl apply -f <file> --dry-run=client  # Client-side validation
kubectl apply -f <file> --dry-run=server  # Server-side validation
kubectl diff -f <file>                  # Show what would change
```

### Labels & Selectors
```bash
kubectl label pods <name> <key>=<val>   # Add label
kubectl label pods <name> <key>-        # Remove label
kubectl get pods -l <key>=<val>         # Select by label
kubectl get pods -l <key> in (v1,v2)    # Multiple values
kubectl get pods -l <key>               # Has label
kubectl get pods -l !<key>              # Missing label
```

---

## Essential Kubernetes Concepts

### Pod Lifecycle States
```
Pending → Running → Succeeded (or Failed/Unknown)
```

**Pending**: Waiting for scheduling or image pull  
**Running**: Container running  
**Succeeded**: Container completed successfully  
**Failed**: Container exited with error  
**Unknown**: Communication lost  

### ReplicaSet & Deployment
- **ReplicaSet**: Ensures N pods running (low-level)
- **Deployment**: Manages ReplicaSets, rolling updates

### Workload Controllers
| Controller | Use Case |
|------------|----------|
| Deployment | Stateless apps, rolling updates |
| StatefulSet | Stateful apps, stable identity |
| DaemonSet | One pod per node |
| Job | Run to completion |
| CronJob | Scheduled batch jobs |

### Service Types
| Type | Use Case | Access |
|------|----------|--------|
| ClusterIP | Internal | Cluster only |
| NodePort | External | NodeIP:port |
| LoadBalancer | Cloud external | LB DNS/IP |
| ExternalName | Alias | External CNAME |

### Storage
```
PersistentVolume (PV) ← Provision (manual/dynamic)
        ↑
PersistentVolumeClaim (PVC) ← Request from Pod
        ↑
      Pod
```

**StorageClass**: Dynamic PV provisioning  
**Snapshot**: Point-in-time backup  

### ConfigMaps vs Secrets
| Feature | ConfigMap | Secret |
|---------|-----------|--------|
| Data type | Config | Sensitive |
| Encoding | Plain text | Base64 |
| Encryption | No | Optional |
| Size limit | 1MB | 1MB |
| Mount | Env/volume | Env/volume |

### Resource Management Hierarchy
```
Pod spec: requests, limits
    ↓
Node: allocatable resources
    ↓
Cluster: total capacity
```

### QoS Classes (Eviction Priority)
1. **Guaranteed** (Highest): requests = limits
2. **Burstable** (Medium): requests < limits
3. **BestEffort** (Lowest): no requests/limits

---

## Common YAML Patterns

### Minimal Pod
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
spec:
  containers:
  - name: app
    image: nginx:latest
    ports:
    - containerPort: 80
```

### Deployment with Rolling Update
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: my-app:v1.0.0
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8080
  selector:
    app: my-app
```

### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_HOST: postgres
  LOG_LEVEL: INFO
  config.yaml: |
    app:
      port: 8080
      timeout: 30
```

### Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-creds
type: Opaque
stringData:
  username: postgres
  password: secret123
```

### PersistentVolumeClaim
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  storageClassName: fast-ssd
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

### StatefulSet
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
  replicas: 1
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
        image: postgres:15
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      storageClassName: standard
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
```

### Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.example.com
    secretName: tls-cert
  rules:
  - host: api.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
```

### NetworkPolicy
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-netpol
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

### HorizontalPodAutoscaler
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
        averageUtilization: 70
```

### PodDisruptionBudget
```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: app-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: my-app
```

### Role & RoleBinding
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["pods/log"]
  verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-reader
subjects:
- kind: ServiceAccount
  name: default
  namespace: default
```

### SecurityContext
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    fsGroup: 1000
  containers:
  - name: app
    image: my-app:latest
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop: ["ALL"]
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir: {}
```

---

## Debugging Workflow

### 1. Check Pod Status
```bash
kubectl get pod <name> -o wide
# Check: Node assignment, restart count, status
```

### 2. Describe Pod (Events)
```bash
kubectl describe pod <name>
# Check: Events section for error messages
```

### 3. Check Logs
```bash
kubectl logs <name> --tail=50 -f
# Check: Application error messages
```

### 4. Check Probes
```bash
kubectl describe pod <name> | grep -A 5 "Liveness"
# Check: Probe configuration and last status
```

### 5. Verify Resources
```bash
kubectl top pod <name>
kubectl describe node <node>
# Check: Memory/CPU usage vs limits
```

### 6. Test Connectivity
```bash
kubectl port-forward <pod> 8080:8080
curl http://localhost:8080/health
# Check: Application responding
```

### 7. Check Node
```bash
kubectl describe node <name>
# Check: Node status, disk, memory, conditions
```

---

## Performance Tuning

### Check Resource Usage
```bash
kubectl top pods -n <ns>
kubectl top nodes
```

### Adjust Resource Limits
```bash
# Current
kubectl get deploy <name> -o yaml | grep -A 5 resources

# Update
kubectl set resources deploy <name> --limits=cpu=500m,memory=512Mi
kubectl set resources deploy <name> --requests=cpu=100m,memory=128Mi
```

### Configure HPA
```bash
# Create
kubectl autoscale deploy <name> --min=2 --max=10 --cpu-percent=70

# Check
kubectl get hpa <name> -o wide
kubectl describe hpa <name>
```

---

## Security Checklist

- [ ] Pods run as non-root user
- [ ] Resource limits set
- [ ] Health checks configured
- [ ] RBAC roles minimal
- [ ] Secrets encrypted at rest
- [ ] Network policies restrict traffic
- [ ] Pod SecurityContext applied
- [ ] Read-only filesystem enabled
- [ ] Capabilities dropped
- [ ] Privilege escalation prevented

---

## Emergency Commands

### Restart All Pods in Deployment
```bash
kubectl rollout restart deploy/<name>
```

### Force Delete Stuck Pod
```bash
kubectl delete pod <name> --grace-period=0 --force
```

### Scale to 0, Then Back Up
```bash
kubectl scale deploy/<name> --replicas=0
kubectl scale deploy/<name> --replicas=3
```

### Get Shell in Pod
```bash
kubectl exec -it <pod> -- /bin/bash
```

### View Last 20 Lines of Logs
```bash
kubectl logs <pod> --tail=20
```

### Watch Pod Status
```bash
kubectl get pod <name> -w
```

---

## Useful Aliases

```bash
alias k='kubectl'
alias kg='kubectl get'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias ke='kubectl exec -it'
alias ka='kubectl apply'
alias kex='kubectl exec -it'
alias kdel='kubectl delete'
alias kn='kubectl config set-context --current --namespace'
```

---

## Tips & Tricks

### List All Pods in Error State
```bash
kubectl get pods --all-namespaces --field-selector=status.phase!=Running
```

### Find Pods Using Most Memory
```bash
kubectl top pods -A | sort -k 4 -rn | head -10
```

### Get Pod IP
```bash
kubectl get pod <name> -o jsonpath='{.status.podIP}'
```

### Wait for Deployment
```bash
kubectl rollout status deploy/<name> -w
```

### Tail Logs from All Pods
```bash
kubectl logs -f -l app=<app> --all-containers
```

### Compare Manifests
```bash
kubectl diff -f <file>
```

### Get YAML of Running Resource
```bash
kubectl get pod <name> -o yaml > backup.yaml
```

---

**Keep this reference handy for quick command lookups!**
