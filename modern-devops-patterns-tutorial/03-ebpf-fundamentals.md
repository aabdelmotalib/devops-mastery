# eBPF (Extended Berkeley Packet Filter) Fundamentals

## Overview

**eBPF (Extended Berkeley Packet Filter)** is a technology that lets you run programs directly in the Linux kernel without modifying kernel source code or loading kernel modules. This enables:

- Real-time observability of every packet, system call, and function call
- Network and security policies enforced at kernel level
- Performance monitoring with zero sampling (100% fidelity)
- Dynamic tracing of any running application

Unlike traditional monitoring that samples data (1% of traffic, periodic checks), eBPF can observe everything in real-time.

## Mental Model

```
Traditional Observability (Sampling):
┌─────────────────────────────────┐
│  All Traffic (1,000,000 pps)    │
└──────────┬──────────────────────┘
           │ Sample 0.1%
           ▼
┌─────────────────────────────────┐
│  Sampled Data (1,000 pps)       │
└──────────┬──────────────────────┘
           │ Aggregate
           ▼
┌─────────────────────────────────┐
│  Metrics (Request rates, etc)   │
│  ~99% blind spots!              │
└─────────────────────────────────┘

Problem: Missing 99.9% of events
         Can't detect rare errors
         False confidence


eBPF Observability (All events):
┌─────────────────────────────────┐
│  All Traffic (1,000,000 pps)    │
└──────────┬──────────────────────┘
           │ eBPF program in kernel
           │ (intercept ALL packets)
           ▼
┌─────────────────────────────────┐
│  Kernel-Level Tracing           │
│  - See every packet             │
│  - See system calls             │
│  - See function calls           │
│  - Zero sampling overhead       │
└──────────┬──────────────────────┘
           │ Filter/aggregate
           │ (kernel space)
           ▼
┌─────────────────────────────────┐
│  Complete Metrics               │
│  - 100% accuracy                │
│  - All events captured          │
│  - No blind spots               │
└─────────────────────────────────┘

Benefit: Perfect visibility + low overhead (CPU budget < 1%)
```

## Architecture

### eBPF Program Lifecycle

```
┌──────────────────────────────────┐
│  eBPF Source Code                │
│  (C program)                     │
└──────────────┬───────────────────┘
               │ clang (C compiler)
               ▼
┌──────────────────────────────────┐
│  eBPF Bytecode                   │
│  (machine independent)           │
└──────────────┬───────────────────┘
               │ Linux kernel
               │ (JIT compiler)
               ▼
┌──────────────────────────────────┐
│  Native Machine Code             │
│  (x86, ARM, etc)                 │
│  Runs directly in kernel        │
│  No context switch               │
└──────────────────────────────────┘
```

### Event Attachment Points

```
┌──────────────────────────────────────────────────────┐
│  Linux Kernel                                        │
│                                                      │
│  Syscall Layer                                       │
│  ↓ ↑  ← Attach kprobes/tracepoints                  │
│  ┌───────────────────────┐                          │
│  │  Networking Stack     │                          │
│  │  ┌─────────────────┐  │                          │
│  │  │ IP Layer        │  │ ← Attach XDP programs   │
│  │  │ (pre-kernel    │  │                          │
│  │  │  processing)   │  │                          │
│  │  └─────────────────┘  │                          │
│  │  ┌─────────────────┐  │                          │
│  │  │ TCP/UDP Layer   │  │ ← Attach eBPF          │
│  │  └─────────────────┘  │    filters             │
│  └───────────────────────┘                          │
│  ↓ ↑  ← Attach programs here                       │
│                                                      │
│  Application Syscalls (read, write, open, etc)     │
│  ↓ ↑  ← Attach uprobe for app-level tracing       │
│                                                      │
│  Memory Management, Scheduling, etc                 │
│  ↓ ↑  ← Attach for resource monitoring            │
└──────────────────────────────────────────────────────┘
```

## Core Concepts

### 1. XDP (eXpress Data Path) - Early Packet Processing

Process packets before kernel network stack:

```c
#include <uapi/linux/bpf.h>
#include <linux/in.h>
#include <linux/ip.h>

SEC("xdp")
int xdp_drop_dns_packets(struct xdp_md *ctx) {
    // Parse packet
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;  // Not enough data
    
    // Check if UDP port 53 (DNS)
    if (eth->h_proto == htons(ETH_P_IP)) {
        struct iphdr *ip = (void *)(eth + 1);
        if ((void *)(ip + 1) > data_end)
            return XDP_PASS;
        
        // If DNS (port 53), drop the packet
        if (ip->protocol == IPPROTO_UDP) {
            struct udphdr *udp = (void *)(ip + 1);
            if ((void *)(udp + 1) > data_end)
                return XDP_PASS;
            
            if (ntohs(udp->dest) == 53)
                return XDP_DROP;  // Drop DNS queries
        }
    }
    
    return XDP_PASS;  // Let packet through
}

char _license[] SEC("license") = "GPL";
```

**Why it matters:**
- Drop unwanted packets at line rate (zero-copy)
- DDoS mitigation without consuming kernel resources
- Faster than firewall rules

### 2. Kprobes - Dynamic Function Tracing

Trace any kernel function without source code modification:

```c
#include <uapi/linux/ptrace.h>
#include <linux/sched.h>

struct data_t {
    u32 pid;
    u64 ts;
    char comm[16];
} __attribute__((packed));

BPF_PERF_OUTPUT(events);

SEC("kprobe/sys_clone")
int trace_clone(struct pt_regs *ctx) {
    struct data_t data = {};
    data.pid = bpf_get_current_pid_uid() >> 32;
    data.ts = bpf_ktime_get_ns();
    bpf_get_current_comm(&data.comm, sizeof(data.comm));
    
    events.perf_submit(ctx, &data, sizeof(data));
    return 0;
}

char _license[] SEC("license") = "GPL";
```

**Use cases:**
- Trace when processes are created (sys_clone)
- Trace file operations (sys_open, sys_read)
- Trace network connections (tcp_connect)
- No app code changes, no recompilation

### 3. Uprobes - Application-Level Tracing

Trace function calls in running applications:

```bash
# Trace every call to malloc in a process
sudo trace -u 'malloc' -n 100

# Trace HTTP requests in Python
sudo trace -u 'http.client:HTTPConnection.request' -n 50

# Output:
# PID    FUNCTION              ARGS
# 1234   http.client:request   method='GET', url='/api/users'
# 1235   http.client:request   method='POST', url='/api/logs'
```

**Advantage:**
- See app behavior without code changes
- No performance impact (event-driven)
- Live in production environments

### 4. Cilium - eBPF-Based Networking

Using eBPF to replace iptables/netfilter:

```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend-to-api
spec:
  description: "Allow frontend pods to call API"
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP

---
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: deny-all-egress
spec:
  description: "Deny all outbound by default"
  endpointSelector: {}
  egress:
  - toEntities:
    - kube-apiserver  # Allow only kube-apiserver
```

**Benefits:**
- Faster than iptables (no rule traversal)
- eBPF programs compiled to native code
- Real-time visibility (know which policy dropped packet)
- Better security enforcement

## Hands-On: eBPF Tracing

### Step 1: Install BCC (eBPF toolkit)

```bash
# Ubuntu/Debian
sudo apt-get install bpfcc-tools linux-headers-$(uname -r)

# Verify installation
bcc-list
```

### Step 2: Trace System Calls

Monitor which files a process opens:

```bash
# Terminal 1: Start tracing all file opens
sudo trace 'syscall::sys_openat { printf("%d: %s\n", uid, str(arg2)); }'

# Terminal 2: Run an application
python3 -c "import json; json.dumps({})"

# Terminal 1 output:
# UID: FILE
# 1000: /etc/ld.so.cache
# 1000: /lib/x86_64-linux-gnu/libc.so.6
# 1000: /usr/lib/python3.9/lib-dynload/_json.cpython-39-so
```

### Step 3: Monitor Network Traffic

```bash
# Live TCP flow tracing
sudo tcpconnect -v

# Output:
# PID    COMM           SADDR            DADDR           DPORT
# 12345  curl           192.168.1.100    93.184.216.34   80
# 12346  python         192.168.1.100    142.251.41.1    443

# See where network traffic originates
```

### Step 4: Profile CPU Time

```bash
# Flame graph of CPU usage
sudo profile -F 99 -f > perf.stacks

# Convert to flame graph
flamegraph.pl perf.stacks > perf.svg

# Open in browser to see:
# - Which functions consume CPU
# - Which call chains are hottest
# - Unexpected CPU consumers
```

### Step 5: Deploy Cilium (eBPF networking)

```bash
# Install Cilium CNI
helm repo add cilium https://helm.cilium.io
helm install cilium cilium/cilium --namespace kube-system

# Verify
kubectl get pods -n kube-system -l k8s-app=cilium

# Create network policy
kubectl apply -f - <<'EOF'
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-isolation
  namespace: default
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: web
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
EOF

# Test: Only web pods can reach api pods
kubectl exec -it pod/web-xxx -- curl http://api:8080  # Works
kubectl exec -it pod/other-xxx -- curl http://api:8080  # Fails
```

## Common Mistakes

**Mistake 1: Running eBPF programs without kernel version verification**
```bash
# ❌ WRONG: Assume eBPF works on all kernel versions
sudo trace 'syscall::sys_openat ...'
# ERROR: sys_openat not available (kernel 4.14)

# ✅ RIGHT: Check kernel version and eBPF features
uname -r  # Should be 4.15+

# Check eBPF support
grep BPF /boot/config-$(uname -r)
# CONFIG_BPF=y
# CONFIG_BPF_SYSCALL=y
# CONFIG_NET_CLS_BPF=y
```

**Mistake 2: Writing unsafe eBPF code that crashes the kernel**
```c
// ❌ WRONG: Unsafe memory access
SEC("kprobe/my_function")
int trace_function(struct pt_regs *ctx) {
    char *ptr = (char *)ctx->rdi;
    char value = *ptr;  // Could be kernel/invalid memory
    // Kernel panic!
}

// ✅ RIGHT: Use eBPF verifier-safe code
SEC("kprobe/my_function")
int trace_function(struct pt_regs *ctx) {
    #pragma clang loop unroll_count(100)
    for (int i = 0; i < 100; i++) {
        // Only read kernel-safe memory
        // Or use bpf_probe_read_kernel()
    }
    return 0;
}
```

**Mistake 3: Overwhelming the kernel with too much tracing**
```bash
# ❌ WRONG: Trace every packet on high-traffic interface
sudo tcpdump 'port 80' --ringbuffer-size=10

# On 100Gbps network:
# Kernel buffer overflows, packets lost
# System becomes unresponsive

# ✅ RIGHT: Use eBPF filters to drop unwanted packets in kernel
# Trace only important packets:
sudo trace 'net::filter_packet { if (sport == 443) print(); }'

# Or use sampling:
sudo tcpdump 'port 80 and random() > 0.99'  # Sample 1%
```

**Mistake 4: Ignoring eBPF helper function limitations**
```c
// ❌ WRONG: Calling non-whitelisted helpers
SEC("xdp")
int process_packet(struct xdp_md *ctx) {
    // XDP context can only use ~30 helpers
    bpf_get_prandom_u32();  // Available in XDP
    bpf_probe_read_kernel();  // Available in kprobes, NOT XDP
    // ERROR: Verifier rejects
}

// ✅ RIGHT: Use only available helpers for context
SEC("xdp")
int process_packet(struct xdp_md *ctx) {
    u32 random = bpf_get_prandom_u32();  // Available
    return XDP_PASS;
}

SEC("kprobe/syscall")
int trace_call(struct pt_regs *ctx) {
    char buffer[100];
    bpf_probe_read_kernel(buffer, 100, (void *)ctx->rdi);  // Available
    return 0;
}
```

**Mistake 5: Missing security context in eBPF policies**
```yaml
# ❌ WRONG: Allow all traffic by default, deny suspicious
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: weak-policy
spec:
  endpointSelector:
    matchLabels:
      app: api
  # No ingress rules = allow all

# ✅ RIGHT: Deny by default, allow only what's needed
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: secure-policy
spec:
  endpointSelector:
    matchLabels:
      app: api
  policyTypes:
  - Ingress  # Default deny all ingress
  - Egress   # Default deny all egress
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: web
    toPorts:
    - ports:
      - port: "8080"
  egress:
  - toEndpoints:
    - matchLabels:
        app: cache
    toPorts:
    - ports:
      - port: "6379"
```

## Production Incident Scenario

### Scenario: "Network performance degraded, packets being dropped silently"

**Symptoms:**
- API latency increased from 50ms to 500ms
- Error rate 5% (timeouts)
- Network interface shows no errors/drops
- CPU usage normal

**Investigation:**

```bash
# 1. Check network interface stats
ethtool -S eth0 | grep -i drop
# rx_dropped: 5000  ← Packets being dropped!

# 2. Check kernel logs
sudo dmesg | tail -50
# No errors shown - silent drops

# 3. Use eBPF to trace which packets dropped
sudo drop-tracer -i eth0
# Output:
# SIZE  SOURCE          DEST           PROTO DROP_REASON
# 1500  10.0.1.5:5000   10.0.1.10:443  TCP   receive_ring_full

# 4. Check receive ring size
ethtool -g eth0
# RX ring size: 256  ← Too small for traffic
```

**Root Cause:**
- Network interface RX ring buffer too small
- High-frequency traffic overwhelms buffer
- NIC starts dropping packets
- Kernel doesn't report (silent in many cases)

**Solution:**

```bash
# 1. Increase RX ring size
ethtool -G eth0 rx 4096  # Increase from 256 to 4096

# 2. Verify new size
ethtool -g eth0
# RX ring size: 4096  ✓

# 3. Monitor for drops
watch ethtool -S eth0 | grep drop

# 4. Verify latency improves
# Monitor API response time
# Should drop back to 50ms after ring resize

# 5. Make persistent (add to /etc/network/interfaces or systemd)
```

**eBPF-based prevention:**

```bash
# Use eBPF to monitor queue depth
sudo queue-depth -i eth0 --alert=80%

# Output:
# TIMESTAMP    QUEUE_DEPTH  THRESHOLD  STATUS
# 14:23:01     256/256      80%        ⚠️ FULL - increase ring size

# Trigger alert before drops occur
```

**Prevention:**
- Monitor queue depth proactively (eBPF)
- Increase RX ring size if approaching limit
- Use XDP to drop unwanted packets early (before ring fills)
- Monitor network interface statistics continuously

## Practice Questions

1. **Sampling vs eBPF:** Why is eBPF better than tcpdump sampling for detecting rare errors?
   - Answer: eBPF captures 100% of events in kernel space. Sampling might miss rare error conditions. With eBPF, you have complete visibility.

2. **Security:** Can an unprivileged user run eBPF programs?
   - Answer: No. eBPF requires root/CAP_SYS_ADMIN. Non-privileged users limited to tracing user-space functions.

3. **Overhead:** What's the performance cost of running eBPF tracing?
   - Answer: Minimal (< 1% CPU). Programs run in kernel, no context switches. Events stored in circular buffers.

4. **Kernel requirements:** Can you use eBPF on kernel 4.4?
   - Answer: Limited support. Full eBPF support requires 4.15+. Earlier versions have limited BPF_SYSCALL support.

5. **Networking:** How does Cilium's eBPF approach differ from iptables?
   - Answer: eBPF compiled to native code (faster). No rule traversal overhead. Real-time visibility. Can enforce policy at line rate.

## Further Reading

- [BPF/eBPF Documentation](https://www.kernel.org/doc/html/latest/userspace-api/ebpf/)
- [BCC Tools Guide](https://github.com/iovisor/bcc/blob/master/docs/reference_guide.md)
- [Cilium Documentation](https://docs.cilium.io/)
- [eBPF in Production](https://ebpf.io/)
- [XDP Tutorial](https://github.com/xdp-project/xdp-tutorial)
- [Brendan Gregg's Linux Performance Tools](https://www.brendangregg.com/ebpf.html)

---

**Summary:** The Modern DevOps Patterns track is now complete:
- **GitOps:** Declarative, Git-driven infrastructure
- **Service Mesh:** Reliability, security, observability for microservices
- **eBPF:** Kernel-level visibility and enforcement

Together, these patterns enable scalable, observable, and secure DevOps systems.
