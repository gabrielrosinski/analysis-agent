# OOMKilled Test Scenario

Simulates a pod that exceeds its memory limit and gets killed by the OOM (Out of Memory) killer.

## Failure Scenario

**Root Cause**: Application has a memory leak and exceeds container memory limit

**Symptoms**:
- Pod enters CrashLoopBackOff state
- Container exit code: 137 (SIGKILL from OOM killer)
- Kubernetes events show: "OOMKilled"
- Container status shows: "OOMKilled" in last termination reason
- Pod restarts repeatedly

## Expected Alert

```
Alert: KubePodCrashLooping or KubeContainerOOMKilled
Severity: critical (memory issues are often critical)
Namespace: test-failures
Pod: oom-test-app-xxxxx-yyyyy
Reason: OOMKilled
```

## What the Agent Should Find

1. **Pod Status**: CrashLoopBackOff with multiple restarts
2. **Exit Code**: 137 (SIGKILL - OOM killer)
3. **Last Termination Reason**: OOMKilled
4. **Logs**: Memory allocation messages before termination
5. **Events**: "Container killed: OOMKilled"
6. **Root Cause**: Memory limit (128Mi) insufficient for application or memory leak
7. **Solution**: Increase memory limit or fix memory leak

## Deploy Scenario

```bash
# Deploy the memory-leaking application
kubectl apply -f examples/oom-scenario/oom-deployment.yaml -n test-failures

# Watch pod status
kubectl get pods -n test-failures --watch

# You should see:
# oom-test-app-xxxxx-yyyyy   0/1     OOMKilled         3 (45s ago)   2m
# oom-test-app-xxxxx-yyyyy   0/1     CrashLoopBackOff  3 (50s ago)   2m
```

## Manual Investigation (What Agent Will Do)

```bash
# 1. Check pod status
kubectl get pods -n test-failures

# 2. Describe pod - look for OOMKilled in last state
kubectl describe pod <pod-name> -n test-failures

# Output will show:
#   Last State:     Terminated
#     Reason:       OOMKilled
#     Exit Code:    137

# 3. Check logs (may be truncated if killed mid-write)
kubectl logs <pod-name> -n test-failures

# 4. Check events
kubectl get events -n test-failures --sort-by='.lastTimestamp' | grep oom

# 5. Check resource limits
kubectl get pod <pod-name> -n test-failures -o jsonpath='{.spec.containers[0].resources}'
```

## Expected Agent Report

The agent should generate a report with:

- **Executive Summary**: "Container killed by OOM (Out of Memory) killer due to memory usage exceeding 128Mi limit"
- **Timeline**:
  - Pod started
  - Memory allocation began
  - Memory usage approached limit
  - OOM killer terminated container (exit code 137)
  - Kubernetes restarted container
  - Crash loop began
- **Root Cause**: Container memory limit (128Mi) exceeded, resulting in OOMKill
- **Evidence**:
  - Exit code 137 (SIGKILL)
  - Last termination reason: OOMKilled
  - Kubernetes event: "Container killed: OOMKilled"
  - Logs showing memory allocation before termination
- **Immediate Fix**: `kubectl delete deployment oom-test-app -n test-failures` (stop the failing deployment)
- **Root Fix**:
  1. Investigate memory leak in application code
  2. Fix the leak if present
  3. If legitimate usage, increase memory limits to appropriate value
  4. Add memory monitoring alerts
  5. Consider setting up vertical pod autoscaler
- **Prevention**:
  - Profile application memory usage during load testing
  - Set memory limits based on actual usage + buffer
  - Implement memory monitoring and alerting
  - Use memory profiling tools to detect leaks early

## Understanding Exit Code 137

The agent's log analyzer should interpret:
- **Exit Code 137** = 128 + 9 (SIGKILL)
- SIGKILL from OOM killer means container exceeded memory limits
- This is NOT an application bug per se, but a resource constraint issue

## Cleanup

```bash
kubectl delete -f examples/oom-scenario/oom-deployment.yaml -n test-failures
```

## Variations

1. **Gradual leak**: Slow memory increase with `sleep 10` between allocations
2. **CPU + Memory**: Combined resource exhaustion
3. **Multiple containers**: One container OOMKilled affects sidecar containers
