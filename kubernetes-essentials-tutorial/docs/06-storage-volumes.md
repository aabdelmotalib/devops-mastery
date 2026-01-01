# Module 6: Storage & Volumes

## Overview

Kubernetes provides abstractions for container storage: Volumes (ephemeral), PersistentVolumes (cluster-level storage), and PersistentVolumeClaims (storage requests). This module covers persistent storage, dynamic provisioning, and stateful application patterns.

## Volume Types

### EmptyDir: Temporary, Pod-Scoped Storage

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container-app
spec:
  containers:
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: scratch
      mountPath: /tmp/scratch
  - name: log-processor
    image: log-processor:v1
    volumeMounts:
    - name: scratch
      mountPath: /tmp/scratch
  volumes:
  - name: scratch
    emptyDir: {}           # Created when Pod starts, deleted when Pod ends
```

**Characteristics**:
- Exists for Pod's lifetime
- Deleted when Pod is removed
- Shared between containers in same Pod
- Starts empty

**Use cases**:
- Temporary files between containers
- Scratch space for computation
- Cache that can be recreated

### HostPath: Node Storage

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: log-collector
spec:
  containers:
  - name: collector
    image: log-collector:v1
    volumeMounts:
    - name: host-logs
      mountPath: /var/log
      readOnly: true
  volumes:
  - name: host-logs
    hostPath:
      path: /var/log          # Node filesystem
      type: Directory
```

**Characteristics**:
- Access node's filesystem
- Pod tied to specific node
- Data persists after Pod deletion

**Use cases**:
- DaemonSets accessing node-local data
- Accessing Docker socket for Docker-in-Docker

**Production risk**: Not portable; breaks when Pod moves to different node.

### ConfigMap & Secret Volumes

Already covered in Module 5. These mount configuration/secrets as files.

### NFS: Network File System

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nfs-client
spec:
  containers:
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: nfs-storage
      mountPath: /data
  volumes:
  - name: nfs-storage
    nfs:
      server: nfs.example.com
      path: /shared
      readOnly: false
```

**Characteristics**:
- Network-based storage
- Multiple Pods can mount same NFS
- Data survives Pod/Node deletion

**Use cases**:
- Shared data between multiple Pods
- Legacy NFS infrastructure integration

**Limitations**: Requires NFS server, not as managed as cloud storage solutions.

## PersistentVolumes (PV) & PersistentVolumeClaims (PVC)

### The PV/PVC Model

```
Administrator provisions PersistentVolumes (cluster resources)
            ↓
Application requests storage via PersistentVolumeClaim
            ↓
Kubernetes binds PVC to matching PV
            ↓
Pod mounts the PVC
            ↓
Application reads/writes data
```

### PersistentVolume (Cluster Admin Manages)

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-database
spec:
  capacity:
    storage: 10Gi          # Size
  accessModes:
    - ReadWriteOnce        # Only one node can mount for writing
  storageClassName: fast
  awsElasticBlockStore:    # Cloud provider specific
    volumeID: vol-12345
    fsType: ext4
```

**Access modes**:
- ReadWriteOnce (RWO): Single node, read-write
- ReadOnlyMany (ROX): Multiple nodes, read-only
- ReadWriteMany (RWX): Multiple nodes, read-write (rare, requires network storage)

**Reclaim policies**:
```yaml
persistentVolumeReclaimPolicy: Retain  # Keep PV after PVC deletion
# Or: Delete (delete PV), Recycle (clear contents)
```

### PersistentVolumeClaim (User Requests Storage)

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-storage
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast
  resources:
    requests:
      storage: 5Gi           # Requests 5GB (will bind to ≥5GB PV)
```

### Binding PVC to PV

```bash
# View available PVs
kubectl get pv
# NAME         CAPACITY   ACCESSMODES   RECLAIMPOLICY   STATUS
# pv-database  10Gi       RWO           Retain          Available

# Create PVC
kubectl apply -f pvc.yaml

# View binding
kubectl get pvc
# NAME        STATUS   VOLUME        CAPACITY   ACCESSMODES
# db-storage  Bound    pv-database   10Gi       RWO
```

Kubernetes automatically binds PVC to matching PV based on:
- Capacity (PV must be ≥ requested storage)
- Access modes (must match)
- Storage class (if specified)

### Mounting PVC in Pod

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
spec:
  template:
    spec:
      containers:
      - name: db
        image: postgres:13
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: db-storage  # Reference the PVC
```

## Storage Classes: Dynamic Provisioning

### Manual Provisioning (Tedious)

1. Admin creates PV manually
2. User creates PVC
3. Kubernetes binds them

Problem: Slow, not scalable.

### Dynamic Provisioning via StorageClass

StorageClass automates PV creation:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com         # Which provisioner creates storage?
allowVolumeExpansion: true            # Can PVC size increase?
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
volumeBindingMode: WaitForFirstConsumer  # Bind only when Pod scheduled
reclaimPolicy: Delete                 # Delete storage when PVC deleted
```

### Using StorageClass for Dynamic Provisioning

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-storage
spec:
  storageClassName: fast-ssd         # Reference StorageClass
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi                 # PV created automatically
```

When PVC is created:
1. Provisioner (e.g., AWS EBS CSI driver) receives request
2. Creates actual storage (EBS volume)
3. Creates PV automatically
4. Binds PVC to PV

**Benefit**: No manual PV creation; scales easily.

### Default StorageClass

Managed Kubernetes services come with default StorageClass:

```bash
# View StorageClasses
kubectl get storageclass

# Mark as default
kubectl patch storageclass fast-ssd -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# PVCs using default class if not specified
```

## StatefulSet Storage Pattern

StatefulSet + PVC template = stable storage per Pod:

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-cluster
spec:
  serviceName: postgres
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
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql
  
  # Volume template: creates PVC for each replica
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 50Gi
```

**Result**:
- postgres-0 has data-postgres-0 PVC
- postgres-1 has data-postgres-1 PVC
- postgres-2 has data-postgres-2 PVC

Each Pod has dedicated storage that survives Pod recreation.

## Snapshots and Backups

### VolumeSnapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: db-snapshot
spec:
  volumeSnapshotClassName: csi-snapshotter
  source:
    persistentVolumeClaimName: db-storage
```

Creates point-in-time snapshot of PVC data. Useful for backups.

### Restoring from Snapshot

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: db-storage-restored
spec:
  dataSource:
    name: db-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
```

Creates new PVC from snapshot.

## Expansion: Growing PVC Size

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
allowVolumeExpansion: true             # Must enable in StorageClass
```

**Expand PVC**:
```bash
# Edit PVC
kubectl patch pvc db-storage -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'

# Underlying storage expands (may require Pod restart depending on storage type)
```

## Common Mistakes

### Mistake 1: Using EmptyDir for Persistent Data

```yaml
# WRONG: Data lost when Pod deleted
volumes:
- name: data
  emptyDir: {}
```

**Problem**: Pod crashes → Container restarts → Data lost.

**Solution**: Use PVC for data you want to persist.

### Mistake 2: Single Node Storage for Multi-Node App

```yaml
# WRONG: Pod moves to different node, can't access storage
volumes:
- name: data
  hostPath:
    path: /data
```

**Problem**: Pod scheduled on node-1, writes to /data. Pod recreated on node-2, that node's /data is empty.

**Solution**: Use network storage (NFS) or PVC.

### Mistake 3: PVC Not Matching StorageClass Parameters

```yaml
# StorageClass requires ReadWriteMany
spec:
  accessModes: ["ReadWriteOnce"]
# WRONG: Mismatched access mode
```

**Problem**: PVC stays Pending; can't bind to StorageClass.

**Solution**: Verify StorageClass requirements.

### Mistake 4: Not Backing Up PVCs

```bash
# Data stored in PVC, no backups
# Hardware failure → Data lost
```

**Solution**: Implement backup strategy:
- Regular VolumeSnapshots
- Cross-region replication
- External backup tools

### Mistake 5: Reclaim Policy is Delete

```yaml
persistentVolumeReclaimPolicy: Delete  # Deletes storage when PVC deleted!
```

**Problem**: Delete PVC by mistake → All data gone.

**Solution**:
- Use Retain: Keep PV after PVC deletion (manual cleanup later)
- Implement backups
- Use immutable PVCs

## Production Patterns

### Persistent Database

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgresql
spec:
  replicas: 1  # Single for now
  serviceName: postgresql
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:13
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
          subPath: postgres  # Subdirectory within PVC
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      storageClassName: fast-ssd
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 100Gi
```

### Backup and Restore

```bash
# Snapshot current state
kubectl apply -f - << 'EOF'
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: db-$(date +%s)
spec:
  volumeSnapshotClassName: csi-snapshotter
  source:
    persistentVolumeClaimName: postgresql-data-postgresql-0
EOF

# Keep snapshots for N days (retention policy)
```

## Key Takeaways

1. **Volumes**: Pod-scoped, ephemeral storage (EmptyDir)
2. **PersistentVolumes**: Cluster-level storage resources
3. **PersistentVolumeClaims**: Applications request storage
4. **StorageClass**: Automates PV provisioning (dynamic)
5. **StatefulSet + PVC templates**: Stateful applications with stable storage
6. **Always backup** persistent data

---

## Practice Questions

### MCQ Questions

1. What happens to data in EmptyDir volume when Pod is deleted?
   A) Data is retained for 24 hours  
   B) Data is lost  
   C) Data is moved to PersistentVolume  
   D) Data is backed up automatically  

2. Which access mode allows multiple nodes to mount for reading and writing?
   A) ReadWriteOnce  
   B) ReadOnlyMany  
   C) ReadWriteMany  
   D) None; multi-node write is not supported  

3. What is the purpose of StorageClass?
   A) To manually provision PersistentVolumes  
   B) To classify storage by speed  
   C) To enable dynamic provisioning of PVs  
   D) To backup PersistentVolumes  

4. In a StatefulSet, how does each Pod get dedicated storage?
   A) All Pods share one PVC  
   B) volumeClaimTemplates create PVC per Pod  
   C) Manual PVC creation for each Pod  
   D) EmptyDir with manual backup  

5. What should PersistentVolumeReclaimPolicy be for critical data?
   A) Delete  
   B) Recycle  
   C) Retain  
   D) Archive  

### Hands-on Cluster Tasks

**Task 1: Create and Use PVC**

1. Verify StorageClass:
   ```bash
   kubectl get storageclass
   ```

2. Create PVC:
   ```bash
   cat > pvc.yaml << 'EOF'
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: test-storage
   spec:
     accessModes:
       - ReadWriteOnce
     resources:
       requests:
         storage: 1Gi
   EOF
   
   kubectl apply -f pvc.yaml
   ```

3. Verify PVC is bound:
   ```bash
   kubectl get pvc test-storage
   # STATUS should be Bound
   ```

4. Create Pod using PVC:
   ```bash
   cat > pod.yaml << 'EOF'
   apiVersion: v1
   kind: Pod
   metadata:
     name: storage-test
   spec:
     containers:
     - name: app
       image: busybox
       command: ['sh', '-c', 'echo "Hello from $(hostname)" > /data/test.txt && sleep 3600']
       volumeMounts:
       - name: storage
         mountPath: /data
     volumes:
     - name: storage
       persistentVolumeClaim:
         claimName: test-storage
   EOF
   
   kubectl apply -f pod.yaml
   ```

5. Verify file written to PVC:
   ```bash
   kubectl exec storage-test -- cat /data/test.txt
   # Output: Hello from storage-test
   ```

6. Delete Pod and create new one (data persists):
   ```bash
   kubectl delete pod storage-test
   kubectl apply -f pod.yaml
   kubectl exec storage-test -- cat /data/test.txt
   # Data still exists!
   ```

7. Cleanup:
   ```bash
   kubectl delete pod storage-test
   kubectl delete pvc test-storage
   ```

**Task 2: StatefulSet with Persistent Storage**

1. Create StatefulSet:
   ```bash
   cat > statefulset.yaml << 'EOF'
   apiVersion: apps/v1
   kind: StatefulSet
   metadata:
     name: test-statefulset
   spec:
     serviceName: test-statefulset
     replicas: 2
     selector:
       matchLabels:
         app: test-app
     template:
       metadata:
         labels:
           app: test-app
       spec:
         containers:
         - name: app
           image: busybox
           command: ['sh', '-c', 'echo "Pod $(hostname)" > /data/identity.txt && sleep 3600']
           volumeMounts:
           - name: data
             mountPath: /data
     volumeClaimTemplates:
     - metadata:
         name: data
       spec:
         accessModes: ["ReadWriteOnce"]
         resources:
           requests:
             storage: 500Mi
   ---
   apiVersion: v1
   kind: Service
   metadata:
     name: test-statefulset
   spec:
     clusterIP: None
     selector:
       app: test-app
     ports:
     - port: 80
   EOF
   
   kubectl apply -f statefulset.yaml
   ```

2. Verify Pods and PVCs:
   ```bash
   kubectl get pods
   # test-statefulset-0, test-statefulset-1
   
   kubectl get pvc
   # data-test-statefulset-0, data-test-statefulset-1
   ```

3. Verify each Pod has dedicated storage:
   ```bash
   kubectl exec test-statefulset-0 -- cat /data/identity.txt
   # Pod test-statefulset-0
   
   kubectl exec test-statefulset-1 -- cat /data/identity.txt
   # Pod test-statefulset-1
   ```

4. Delete Pod and verify storage persists:
   ```bash
   kubectl delete pod test-statefulset-0
   # StatefulSet recreates it
   
   kubectl exec test-statefulset-0 -- cat /data/identity.txt
   # Data still there, same PVC used
   ```

5. Cleanup:
   ```bash
   kubectl delete statefulset test-statefulset
   kubectl delete svc test-statefulset
   kubectl delete pvc data-test-statefulset-0 data-test-statefulset-1
   ```

### Realistic Production Failure Scenario

**Scenario: PVC Runs Out of Space**

Your PostgreSQL database PVC is 100GB. Application writes rapidly, and storage fills up.

```bash
# PVC at 95% capacity
kubectl exec postgres-pod -- df -h /var/lib/postgresql
# /dev/sda1  100G   95G   5G  95%  /var/lib/postgresql

# Database can't write anymore
# Error: "No space left on device"

# Queries fail
# Application returns 500 errors
```

**Root cause**: No monitoring/alerting for disk usage.

**Detection**:
```bash
# Monitor PVC usage (requires metrics-server)
kubectl top pvc db-storage
```

**Immediate fix**:
1. Expand PVC:
   ```bash
   kubectl patch pvc db-storage -p '{"spec":{"resources":{"requests":{"storage":"200Gi"}}}}'
   ```

2. Database might need recovery if writes were interrupted:
   ```bash
   # Log into database and check integrity
   # Might need VACUUM (PostgreSQL) or similar
   ```

**Prevention**:
1. Monitor PVC usage and alert when >80%:
   ```yaml
   # Prometheus alert rule
   - alert: PVCAlmostFull
     expr: kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.8
   ```

2. Set up automatic expansion (if StorageClass supports it)

3. Implement retention policies (delete old data)

4. Right-size initial PVC based on growth projections

---

## Further Reading

- Volumes: https://kubernetes.io/docs/concepts/storage/volumes/
- PersistentVolumes: https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- StorageClasses: https://kubernetes.io/docs/concepts/storage/storage-classes/
- StatefulSets Storage: https://kubernetes.io/docs/tutorials/stateful-application/
