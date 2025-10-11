# Testing Guide for DevOps RCA Agent

Comprehensive testing tools and scenarios for validating the DevOps RCA Agent system.

## Quick Start

```bash
# 1. Verify system is deployed correctly
./tests/verify-agent.sh

# 2. Send a test alert directly to webhook
./tests/send-test-alert.sh

# 3. OR deploy real failure scenarios
./tests/create-test-failure.sh
```

## Test Scripts

### 1. `verify-agent.sh` - System Health Check

Validates all components are deployed and healthy.

**What it checks:**
- ✓ Namespace exists
- ✓ RBAC resources (ServiceAccounts, ClusterRole, bindings)
- ✓ Persistent storage (PVC is Bound)
- ✓ Secrets (Gmail credentials, recipients, GitHub token)
- ✓ Webhook service (deployment + pods ready)
- ✓ Notifier service (deployment + pods ready)
- ✓ Kagent operator (running in kagent-system)
- ✓ Agent resource (devops-rca-agent exists)
- ⚠ AlertManager integration (optional)

**Usage:**
```bash
./tests/verify-agent.sh

# Expected output:
# ✓ Passed:   25
# ✗ Failed:   0
# ⚠ Warnings: 2
```

**When to run:**
- After initial deployment
- After configuration changes
- When troubleshooting issues
- Before running E2E tests

---

### 2. `send-test-alert.sh` - Direct Alert Injection

Sends a test alert directly to the webhook service, bypassing AlertManager.

**What it does:**
1. Prompts for alert details (name, severity, namespace, pod)
2. Constructs AlertManager v4 webhook format JSON
3. Sends POST request to webhook service from inside cluster
4. Triggers agent investigation immediately

**Usage:**
```bash
./tests/send-test-alert.sh

# Interactive prompts:
# Alert name [KubePodCrashLooping]:
# Severity [critical]:
# Affected namespace [production]:
# Pod name [test-app-7d4f8-x9k2m]:
# Description [Pod is crash looping]:
```

**Advantages:**
- ✅ No need for Prometheus/AlertManager
- ✅ Immediate feedback (no wait for evaluation period)
- ✅ Full control over alert parameters
- ✅ Good for development and quick testing

**Limitations:**
- ❌ Doesn't test AlertManager integration
- ❌ Doesn't validate Prometheus rules
- ❌ May not match real alert format exactly

**When to use:**
- During development
- Testing agent logic without infrastructure
- Quick validation of fixes
- CI/CD integration tests

---

### 3. `create-test-failure.sh` - Real Failure Scenarios

Deploys actual failing applications to trigger real alerts through Prometheus/AlertManager.

**Available scenarios:**
1. **CrashLoop** - Database connection failure
2. **OOMKilled** - Memory leak exceeding limits
3. **ImagePullBackOff** - Invalid image tag
4. **All scenarios** - Deploy all at once
5. **Cleanup** - Remove all test failures

**Usage:**
```bash
./tests/create-test-failure.sh

# Select scenario (1-5):
# 1 - CrashLoop
# 2 - OOMKilled
# 3 - ImagePullBackOff
# 4 - All scenarios
# 5 - Cleanup
```

**What happens:**
1. Creates `test-failures` namespace (if not exists)
2. Deploys failing application(s)
3. Application fails (crashes, OOM, can't pull image)
4. Prometheus detects the failure
5. AlertManager evaluates rules
6. Alert fires (after evaluation period ~2-5 minutes)
7. AlertManager sends webhook to our service
8. Agent investigates and generates report
9. Email notification sent

**Timeline:**
- `T+0s` - Deployment created
- `T+10s` - Pod starts failing
- `T+30s` - Prometheus scrapes and detects issue
- `T+2m` - AlertManager evaluation period completes
- `T+2m` - Alert fires, webhook sent
- `T+2m` - Agent starts investigation
- `T+3m` - Email report received

**When to use:**
- End-to-end testing
- Validating full alert pipeline
- Demo/presentation purposes
- Realistic testing before production

---

## Test Scenarios

### Scenario 1: CrashLoop (Database Connection Failure)

**Location:** `examples/crashloop-scenario/`

**Simulates:** Pod that crashes immediately due to missing database service

**Key Features:**
- Exit code 1 (application error)
- Clear error messages in logs
- "Connection refused" pattern
- Kubernetes restart loop

**Expected Alert:** `KubePodCrashLooping`

**Deploy:**
```bash
kubectl apply -f examples/crashloop-scenario/bad-deployment.yaml -n test-failures
```

**What Agent Should Find:**
- Root cause: Database service doesn't exist
- Evidence: Logs show "Connection refused: database-service:5432"
- Solution: Create database service or fix connection string

[Full documentation](../examples/crashloop-scenario/README.md)

---

### Scenario 2: OOMKilled (Memory Exhaustion)

**Location:** `examples/oom-scenario/`

**Simulates:** Memory leak that exceeds container limits

**Key Features:**
- Exit code 137 (SIGKILL from OOM killer)
- Last termination reason: "OOMKilled"
- Memory limit: 128Mi (intentionally low)
- Continuous memory allocation

**Expected Alert:** `KubePodCrashLooping` or `KubeContainerOOMKilled`

**Deploy:**
```bash
kubectl apply -f examples/oom-scenario/oom-deployment.yaml -n test-failures
```

**What Agent Should Find:**
- Root cause: Container exceeded 128Mi memory limit
- Evidence: Exit code 137, OOMKilled event, memory allocation in logs
- Solution: Increase memory limits or fix memory leak

[Full documentation](../examples/oom-scenario/README.md)

---

### Scenario 3: ImagePullBackOff (Invalid Image Tag)

**Location:** `examples/imagepull-scenario/`

**Simulates:** Deployment with non-existent image tag

**Key Features:**
- Pod stuck in ImagePullBackOff
- Never reaches Running state
- No application logs (container never started)
- Image: `nginx:this-tag-does-not-exist-v999`

**Expected Alert:** `KubePodNotReady` or `KubePodImagePullBackOff`

**Deploy:**
```bash
kubectl apply -f examples/imagepull-scenario/imagepull-deployment.yaml -n test-failures
```

**What Agent Should Find:**
- Root cause: Image tag doesn't exist in registry
- Evidence: "manifest not found" error in events
- Solution: Use correct image tag (e.g., nginx:latest)

[Full documentation](../examples/imagepull-scenario/README.md)

---

## End-to-End Testing Workflow

### Full E2E Test (Using Real Failures)

```bash
# Step 1: Verify system is healthy
./tests/verify-agent.sh

# Step 2: Deploy a failure scenario
./tests/create-test-failure.sh
# Select: 1 (CrashLoop)

# Step 3: Watch the failure happen
kubectl get pods -n test-failures --watch

# Step 4: Wait for alert (2-5 minutes)
# Check AlertManager: kubectl port-forward -n monitoring svc/alertmanager-operated 9093:9093
# Visit: http://localhost:9093/#/alerts

# Step 5: Monitor webhook receiving alert
kubectl logs -f -n analysis-agent -l app=webhook-service

# Step 6: Watch agent investigation
kubectl logs -f -n kagent-system -l app=kagent-operator

# Step 7: Check email for incident report

# Step 8: View saved report in agent memory
AGENT_POD=$(kubectl get pods -n analysis-agent -l component=agent -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n analysis-agent $AGENT_POD -- ls -la /agent-memory/reports/
kubectl exec -it -n analysis-agent $AGENT_POD -- cat /agent-memory/reports/<latest-report>.md

# Step 9: Cleanup
./tests/create-test-failure.sh
# Select: 5 (Cleanup)
```

### Quick Test (Using Direct Alert)

```bash
# Step 1: Verify system
./tests/verify-agent.sh

# Step 2: Send test alert
./tests/send-test-alert.sh
# Alert name: TestAlert
# Severity: warning
# Namespace: test
# Pod: test-pod-12345

# Step 3: Monitor webhook logs
kubectl logs -f -n analysis-agent -l app=webhook-service

# Step 4: Check email immediately (no waiting)
```

---

## Monitoring During Tests

### Webhook Service Logs
```bash
kubectl logs -f -n analysis-agent -l app=webhook-service

# Look for:
# "Received webhook from AlertManager"
# "Triggering agent investigation"
# "Agent invoked successfully"
```

### Notifier Service Logs
```bash
kubectl logs -f -n analysis-agent -l app=notifier-service

# Look for:
# "Received notification request"
# "Sending email to X recipient(s)"
# "Email sent successfully"
```

### Kagent Operator Logs
```bash
kubectl logs -f -n kagent-system -l app=kagent-operator

# Look for:
# "Agent invocation started"
# "Tool execution: memory_tool"
# "Tool execution: log_tool"
# "Agent invocation completed"
```

### Agent Memory (Reports)
```bash
# List reports
kubectl exec -it -n analysis-agent <agent-pod> -- ls -la /agent-memory/reports/

# View latest report
kubectl exec -it -n analysis-agent <agent-pod> -- cat /agent-memory/reports/<timestamp>-<alertname>.md
```

### AlertManager UI
```bash
kubectl port-forward -n monitoring svc/alertmanager-operated 9093:9093

# Visit: http://localhost:9093/#/alerts
# Check for: Firing alerts, Silenced alerts
```

### Prometheus UI
```bash
kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090

# Visit: http://localhost:9090/alerts
# Check: Alert rules, current alert states
```

---

## Troubleshooting Tests

### Alert Not Firing

**Symptoms:**
- Deployed failure scenario but no alert after 5+ minutes

**Checks:**
1. Is Prometheus scraping the pods?
   ```bash
   kubectl port-forward -n monitoring svc/prometheus-operated 9090:9090
   # Visit: http://localhost:9090/targets
   ```

2. Are alert rules configured?
   ```bash
   kubectl get prometheusrules -n monitoring
   # Visit: http://localhost:9090/alerts
   ```

3. Is AlertManager running?
   ```bash
   kubectl get pods -n monitoring -l app.kubernetes.io/name=alertmanager
   ```

4. Check pod labels match alert selectors
   ```bash
   kubectl get pods -n test-failures --show-labels
   ```

### Webhook Not Receiving Alerts

**Symptoms:**
- Alert fires in AlertManager but webhook service logs are empty

**Checks:**
1. Is webhook service running?
   ```bash
   kubectl get pods -n analysis-agent -l app=webhook-service
   ```

2. Is AlertManager configured with webhook URL?
   ```bash
   kubectl get secret -n monitoring alertmanager-<release>-alertmanager -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d
   # Should contain: http://webhook-service.analysis-agent.svc.cluster.local:8080/api/v1/webhook/alertmanager
   ```

3. Test connectivity from monitoring namespace
   ```bash
   kubectl run test -n monitoring --rm -i --restart=Never --image=curlimages/curl -- \
     curl -v http://webhook-service.analysis-agent.svc.cluster.local:8080/health
   ```

### Agent Not Investigating

**Symptoms:**
- Webhook receives alert but agent doesn't investigate

**Checks:**
1. Is Kagent operator running?
   ```bash
   kubectl get pods -n kagent-system
   ```

2. Does agent resource exist?
   ```bash
   kubectl get agent devops-rca-agent -n analysis-agent
   ```

3. Check agent logs for errors
   ```bash
   kubectl logs -n kagent-system -l app=kagent-operator | grep devops-rca-agent
   ```

4. Check webhook is calling correct agent API
   ```bash
   kubectl logs -n analysis-agent -l app=webhook-service | grep "Invoking agent"
   ```

### Email Not Sent

**Symptoms:**
- Investigation completes but no email received

**Checks:**
1. Are Gmail credentials configured?
   ```bash
   kubectl get secret gmail-credentials -n analysis-agent
   kubectl describe secret gmail-credentials -n analysis-agent
   ```

2. Are recipients configured?
   ```bash
   kubectl get secret email-recipients -n analysis-agent
   ```

3. Test notifier service directly
   ```bash
   kubectl port-forward svc/notifier-service 8080:8080 -n analysis-agent
   curl -X POST http://localhost:8080/api/v1/test-email \
     -H "Content-Type: application/json" \
     -d '{"recipients": ["your-email@example.com"]}'
   ```

4. Check notifier logs
   ```bash
   kubectl logs -n analysis-agent -l app=notifier-service
   ```

---

## Test Checklist

Use this checklist for comprehensive system validation:

- [ ] **System Verification**
  - [ ] All components deployed (`verify-agent.sh`)
  - [ ] All pods are Ready
  - [ ] Secrets configured
  - [ ] PVC is Bound

- [ ] **Quick Tests**
  - [ ] Send test alert (`send-test-alert.sh`)
  - [ ] Webhook receives alert
  - [ ] Agent investigates
  - [ ] Email notification sent

- [ ] **E2E Tests**
  - [ ] Deploy CrashLoop scenario
  - [ ] Wait for alert to fire
  - [ ] Verify investigation report
  - [ ] Cleanup scenario

- [ ] **Additional Tests**
  - [ ] Deploy OOMKilled scenario
  - [ ] Deploy ImagePullBackOff scenario
  - [ ] Test with different severities
  - [ ] Test email routing by severity

- [ ] **Validation**
  - [ ] Reports saved to agent memory
  - [ ] Known issues updated
  - [ ] Email formatting is correct
  - [ ] Solutions are actionable

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test RCA Agent

on: [push, pull_request]

jobs:
  test-agent:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Create K3s cluster
        run: |
          curl -sfL https://get.k3s.io | sh -
          kubectl wait --for=condition=Ready nodes --all --timeout=60s

      - name: Deploy agent
        run: |
          kubectl apply -f manifests/

      - name: Verify deployment
        run: |
          ./tests/verify-agent.sh

      - name: Send test alert
        run: |
          echo "KubePodCrashLooping\ncritical\ntest\ntest-pod" | ./tests/send-test-alert.sh

      - name: Check webhook logs
        run: |
          kubectl logs -n analysis-agent -l app=webhook-service
```

---

**Last Updated:** 2025-10-11
