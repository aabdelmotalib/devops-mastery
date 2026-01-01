# Module 8: Health, Probes & Logging

## Overview

Health probes determine if Pods are ready to serve traffic and detect when they become unhealthy. Logging aggregates container logs for debugging. This module covers probes, observability, and debugging strategies.

## Health Probes

### Probe Types

Kubernetes defines three probe types:

**Liveness Probe**: "Is the application running?"
- Restarts Pod if probe fails
- Use for detecting deadlocks, unresponsive processes

**Readiness Probe**: "Can the Pod serve traffic?"
- Removes Pod from Service endpoints if probe fails
- No restart; Pod stays in cluster but no traffic
- Use for startup initialization, temporary unavailability

**Startup Probe**: "Has the application started?"
- Prevents liveness/readiness checks until startup complete
- Useful for slow-starting applications
- Overrides liveness during startup phase

### Probe Mechanisms

**HTTP Probe** (most common):
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
    scheme: HTTP
    httpHeaders:
    - name: Authorization
      value: "Bearer token123"
  initialDelaySeconds: 10      # Wait 10s before first check
  periodSeconds: 10             # Check every 10s
  timeoutSeconds: 2             # Request timeout
  successThreshold: 1           # Minimum successes to be healthy
  failureThreshold: 3           # 3 failures = unhealthy
```

**TCP Probe**:
```yaml
livenessProbe:
  tcpSocket:
    port: 3306
  initialDelaySeconds: 5
  periodSeconds: 10
```

**Exec Probe**:
```yaml
readinessProbe:
  exec:
    command: ["/bin/sh", "-c", "curl localhost:8080/ready"]
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Probe Configuration Best Practices

```yaml
spec:
  containers:
  - name: app
    image: myapp:v1
    ports:
    - containerPort: 8080
    
    # Startup: app might need 30s to initialize
    startupProbe:
      httpGet:
        path: /startup
        port: 8080
      failureThreshold: 30      # Allow 30 failures (30 * 10s = 5min)
      periodSeconds: 10
    
    # Liveness: detect if app becomes unresponsive
    livenessProbe:
      httpGet:
        path: /live
        port: 8080
      initialDelaySeconds: 10
      periodSeconds: 10
      failureThreshold: 3       # 3 failures (30s) = restart
      timeoutSeconds: 2
    
    # Readiness: detect if app can't handle traffic
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 2       # 2 failures = not ready
      timeoutSeconds: 1
```

### Probe Failure Scenarios

**Liveness failure**:
```
livenessProbe fails → Probe failures accumulate
After failureThreshold failures → Container restarted
Pod IP changes → Service updates endpoints
```

**Readiness failure**:
```
readinessProbe fails → Pod.Ready = False
Service removes Pod from endpoints
No traffic sent to Pod
Pod stays running (not restarted)
```

**Startup failure**:
```
startupProbe fails → Container restarted
Only affects initialization; doesn't restart after startup complete
```

## Application-Level Health Endpoints

### Design Health Endpoint

```go
// Example: Go application
http.HandleFunc("/live", func(w http.ResponseWriter, r *http.Request) {
    // Minimal checks: is process running?
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("OK"))
})

http.HandleFunc("/ready", func(w http.ResponseWriter, r *http.Request) {
    // Database connected?
    db.Ping(context.Background())
    
    // Can handle traffic?
    if !isReady {
        w.WriteHeader(http.StatusServiceUnavailable)
        return
    }
    
    w.WriteHeader(http.StatusOK)
})
```

### Health Check Best Practices

1. **Liveness** should be minimal (fast to fail)
   - Check: Is process running?
   - Don't check: External dependencies

2. **Readiness** checks dependencies
   - Database connectivity
   - Cache availability
   - External service reachability

3. **Avoid cascading failures**
   - Readiness probe shouldn't connect to other services
   - Use circuit breakers for external dependencies

## Logging Architecture

### Container Logging

Containers write to stdout/stderr:
```bash
# Access pod logs
kubectl logs my-pod
kubectl logs my-pod -c app  # Specific container
kubectl logs my-pod --previous  # Previous run (if crashed)
kubectl logs my-pod -f  # Stream logs (tail -f)
```

### Log Drivers

Docker captures stdout/stderr and stores in:
```
/var/lib/docker/containers/<container-id>/<container-id>-json.log
```

kubelet exposes via API.

### Centralized Logging Architecture

```
Pods (containers)
    ↓
Container stdout/stderr
    ↓
Kubelet (exposes via API)
    ↓
Log Aggregator (Fluentd, Filebeat, Loki)
    ↓
Centralized Storage (Elasticsearch, Grafana Loki, Splunk)
    ↓
Visualization & Search (Kibana, Grafana)
```

### Sidecar Logging Pattern

For applications that write to files (not stdout):

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: logging-demo
spec:
  containers:
  # Main application
  - name: app
    image: myapp:v1
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  
  # Sidecar: forwards logs to stdout
  - name: log-forwarder
    image: fluent-bit:latest
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
    # Reads /var/log/app/app.log and sends to stdout
    # kubectl logs pod-name -c log-forwarder gets the logs
  
  volumes:
  - name: logs
    emptyDir: {}
```

### Multi-line Logging

Applications that write multi-line stack traces to single log line:

```
2023-01-15 10:00:00 ERROR NullPointerException at com.example.App.main(App.java:42) ...
```

Log aggregators should parse and restructure:

```json
{
  "timestamp": "2023-01-15T10:00:00Z",
  "level": "ERROR",
  "message": "NullPointerException",
  "stacktrace": "at com.example.App.main(App.java:42) ..."
}
```

## Structured Logging

### JSON Logging

Instead of text logs, applications should output structured JSON:

```json
{
  "timestamp": "2023-01-15T10:00:00Z",
  "level": "INFO",
  "logger": "com.example.User",
  "message": "User created",
  "user_id": 12345,
  "email": "user@example.com",
  "duration_ms": 42
}
```

**Advantages**:
- Queryable by field (user_id, duration_ms)
- Aggregatable (count errors by level)
- Sortable

## Monitoring & Metrics

### Prometheus Metrics

Kubernetes uses Prometheus format for metrics. Application exposes /metrics endpoint:

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",status="200"} 1234
http_requests_total{method="POST",status="201"} 45

# HELP request_duration_seconds Request duration in seconds
# TYPE request_duration_seconds histogram
request_duration_seconds_bucket{le="0.1"} 100
request_duration_seconds_bucket{le="0.5"} 500
request_duration_seconds_bucket{le="1.0"} 950
request_duration_seconds_bucket{le="+Inf"} 1000
```

### Metrics Collection

```
Pods (expose /metrics)
    ↓
Prometheus (scrapes /metrics)
    ↓
Prometheus Server (time-series database)
    ↓
Grafana (visualization)
    ↓
Alerting (PagerDuty, Slack)
```

### Key Metrics

**Container metrics** (kubelet):
- CPU usage
- Memory usage
- Disk I/O
- Network I/O

**Application metrics**:
- HTTP request rate
- Error rate
- Response latency
- Business metrics (user signups, transactions)

### ServiceMonitor (for Prometheus)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: app-monitor
spec:
  selector:
    matchLabels:
      app: myapp
  endpoints:
  - port: metrics
    interval: 30s
```

Prometheus scrapes all Pods matching label every 30s.

## Debugging Techniques

### Logs as First Step

```bash
# Get logs
kubectl logs my-pod

# Follow logs
kubectl logs -f my-pod

# Last N lines
kubectl logs my-pod --tail=100

# Since specific time
kubectl logs my-pod --since=1h
```

### Exec into Pod

```bash
# Interactive shell
kubectl exec -it my-pod -- /bin/bash

# Run command
kubectl exec my-pod -- ps aux
kubectl exec my-pod -- curl localhost:8080
```

### Describe for Events

```bash
# Pod events
kubectl describe pod my-pod

# Shows Events section:
# Events:
#   Type    Reason    Age   From        Message
#   ----    ------    ---   ----        -------
#   Normal  Created   5m    kubelet     Created container
#   Normal  Started   5m    kubelet     Started container
#   Warning Unhealthy 2m    kubelet     Readiness probe failed
```

### Port-Forward for Testing

```bash
# Forward local port to pod
kubectl port-forward pod/my-pod 8080:8080

# Local machine: curl localhost:8080
# Routes to pod:8080
```

### Copy Files

```bash
# Copy from pod
kubectl cp my-pod:/var/log/app.log ./local-log.txt

# Copy to pod
kubectl cp ./file.txt my-pod:/tmp/file.txt
```

## Common Mistakes

### Mistake 1: Overly Sensitive Probes

```yaml
# WRONG: Fails too easily
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  failureThreshold: 1           # 1 failure = not ready
  periodSeconds: 1              # Check every second
```

**Problem**: Temporary network blip → Pod loses all traffic.

**Solution**:
```yaml
failureThreshold: 3
periodSeconds: 5
```

### Mistake 2: Liveness Probe Too Aggressive

```yaml
# WRONG: Restarts frequently
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 0
  failureThreshold: 1
```

**Problem**: Pod restarts constantly → never recovers.

**Solution**: Increase initialDelaySeconds, failureThreshold.

### Mistake 3: No Readiness Probe

```yaml
# No readiness probe
# Pod receives traffic immediately after starting
# But app might not be ready (DB not migrated, cache not warmed)
```

**Problem**: Requests to unready Pod → failures.

**Solution**: Implement readiness probe.

### Mistake 4: Readiness Probe Checks External Dependencies

```yaml
# WRONG: Checks if external service is reachable
readinessProbe:
  exec:
    command: ["curl", "http://external-service"]
```

**Problem**: External service down → all Pods become not ready → cascading failure.

**Solution**: Readiness checks only internal dependencies.

### Mistake 5: Logging to Files Instead of Stdout

```bash
# App logs to /var/log/app.log
# Kubernetes can't access logs: kubectl logs returns empty
```

**Solution**: Redirect logs to stdout or use sidecar.

## Production Patterns

### Progressive Health Checks

```yaml
startupProbe:
  httpGet:
    path: /startup
    port: 8080
  failureThreshold: 60        # 10 minutes to start
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 2

livenessProbe:
  httpGet:
    path: /live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
  failureThreshold: 3
```

### Logging at Scale

```yaml
# Add DaemonSet for log aggregation
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: monitoring
spec:
  template:
    spec:
      tolerations:
      - effect: NoSchedule
        operator: Exists
      containers:
      - name: fluent-bit
        image: fluent/fluent-bit:latest
        volumeMounts:
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: varlibdockercontainers
          mountPath: /var/lib/docker/containers
          readOnly: true
      volumes:
      - name: varlog
        hostPath:
          path: /var/log
      - name: varlibdockercontainers
        hostPath:
          path: /var/lib/docker/containers
```

### Monitoring Critical Paths

```yaml
# For production services, monitor:
# - Request latency (p50, p99)
# - Error rate (5xx responses)
# - Throughput (requests/sec)
```

## Key Takeaways

1. **Liveness** detects hung processes; **Readiness** detects unavailable services
2. **Startup probe** handles slow initialization
3. **Health endpoints** must be implemented by application
4. **Logs** provide debugging; **metrics** provide observability
5. **Structured logging** (JSON) enables better analysis
6. **Centralized logging** required at scale

---

## Practice Questions

### MCQ Questions

1. What happens when a liveness probe fails?
   A) Pod is marked as not ready  
   B) Container is restarted  
   C) Pod is deleted  
   D) Service removes pod from endpoints  

2. When should a startup probe be used?
   A) For all applications  
   B) For slow-starting applications  
   C) For detecting deadlocks  
   D) For checking external dependencies  

3. If readiness probe fails, what happens?
   A) Container restarts  
   B) Pod is deleted  
   C) Service removes pod from endpoints  
   D) Pod gets new IP address  

4. What is the purpose of a sidecar logging pattern?
   A) Speed up application performance  
   B) Forward file logs to stdout  
   C) Reduce memory usage  
   D) Improve security  

5. Where should application logs go?
   A) /var/log/app.log files  
   B) Container stdout/stderr  
   C) Local database  
   D) Email alerts  

### Hands-on Cluster Tasks

**Task 1: Implement Health Probes**

1. Create application with health endpoints:
   ```bash
   cat > app.py << 'EOF'
   from flask import Flask
   import time
   
   app = Flask(__name__)
   startup_time = time.time()
   ready = False
   
   @app.route('/startup')
   def startup():
       if time.time() - startup_time > 5:
           return 'OK', 200
       return 'Starting', 503
   
   @app.route('/ready')
   def ready_endpoint():
       global ready
       if not ready:
           return 'Not ready', 503
       return 'OK', 200
   
   @app.route('/live')
   def live():
       return 'OK', 200
   
   @app.after_request
   def after_request(response):
       global ready
       ready = True
       return response
   
   if __name__ == '__main__':
       app.run(host='0.0.0.0', port=5000)
   EOF
   ```

2. Create Pod with health probes:
   ```bash
   cat > health-pod.yaml << 'EOF'
   apiVersion: v1
   kind: Pod
   metadata:
     name: health-demo
   spec:
     containers:
     - name: app
       image: python:3.9
       command: ["/bin/sh", "-c", "pip install flask && python /app.py"]
       ports:
       - containerPort: 5000
       volumeMounts:
       - name: app-code
         mountPath: /
       startupProbe:
         httpGet:
           path: /startup
           port: 5000
         failureThreshold: 30
         periodSeconds: 1
       readinessProbe:
         httpGet:
           path: /ready
           port: 5000
         failureThreshold: 3
         periodSeconds: 2
       livenessProbe:
         httpGet:
           path: /live
           port: 5000
         initialDelaySeconds: 10
         periodSeconds: 5
     volumes:
     - name: app-code
       configMap:
         name: app-code
   EOF
   ```

3. Create ConfigMap with code:
   ```bash
   kubectl create configmap app-code --from-file=app.py
   ```

4. Deploy and observe:
   ```bash
   kubectl apply -f health-pod.yaml
   kubectl get pod health-demo --watch
   kubectl describe pod health-demo
   ```

5. Cleanup:
   ```bash
   kubectl delete pod health-demo
   kubectl delete configmap app-code
   ```

**Task 2: Logging and Debugging**

1. Create Pod with logs:
   ```bash
   kubectl run log-demo --image=busybox -- sh -c 'echo "Starting..."; for i in {1..10}; do echo "Log line $i"; sleep 1; done'
   ```

2. View logs:
   ```bash
   kubectl logs log-demo
   kubectl logs log-demo -f
   ```

3. Get logs from crashed container:
   ```bash
   # Create a failing pod
   kubectl run failing --image=busybox -- sh -c 'exit 1'
   
   # Get previous logs
   kubectl logs failing --previous
   ```

4. Exec into Pod:
   ```bash
   kubectl run debug --image=busybox -it --rm -- sh
   # Inside pod: echo "Hello", ls /
   ```

5. Cleanup:
   ```bash
   kubectl delete pod log-demo failing
   ```

### Realistic Production Failure Scenario

**Scenario: Readiness Probe Passes but Application Can't Connect to Database**

Your readiness probe only checks that the app is running (HTTP 200), but doesn't verify database connectivity. Database network becomes unreachable.

```bash
# Readiness probe succeeds (app running)
# Pod marked as Ready
# Service routes traffic to pod

# But database queries fail
# Application throws errors
# Users see 500 errors
```

**Root cause**: Readiness probe insufficient; doesn't check dependencies.

**Better readiness probe**:
```yaml
readinessProbe:
  exec:
    command:
    - /bin/sh
    - -c
    - |
      curl localhost:5000/health && \
      pg_isready -h postgres -U user
```

**Prevention**:
1. Readiness probe must verify dependencies
2. Dependencies include: DB, cache, message queue
3. But avoid checking external services (not owned by you)
4. Use circuit breaker pattern for optional dependencies

---

## Further Reading

- Probes: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- Logging: https://kubernetes.io/docs/concepts/cluster-administration/logging/
- Metrics: https://kubernetes.io/docs/tasks/debug-application-cluster/resource-metrics-pipeline/
- Prometheus: https://prometheus.io/
