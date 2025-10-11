# CrashLoop Test Scenario

Simulates a pod that continuously crashes due to database connection failure.

## Failure Scenario

**Root Cause**: Application fails to connect to database service that doesn't exist

**Symptoms**:
- Pod enters CrashLoopBackOff state
- Container exit code: 1
- Logs show: "Connection refused: database-service:5432"
- Pod restarts repeatedly with increasing backoff

## Expected Alert

```
Alert: KubePodCrashLooping
Severity: warning (or critical depending on configuration)
Namespace: test-failures
Pod: crashloop-test-app-xxxxx-yyyyy
```

## What the Agent Should Find

1. **Pod Status**: CrashLoopBackOff with multiple restarts
2. **Exit Code**: 1 (application error)
3. **Logs**: Clear error messages about database connection failure
4. **Events**: "Back-off restarting failed container"
5. **Root Cause**: Non-existent database service
6. **Solution**: Either create the database service or fix the connection string

## Deploy Scenario

```bash
# Deploy the failing application
kubectl apply -f examples/crashloop-scenario/bad-deployment.yaml -n test-failures

# Watch pod status
kubectl get pods -n test-failures --watch

# You should see:
# crashloop-test-app-xxxxx-yyyyy   0/1     CrashLoopBackOff   3 (30s ago)   2m
```

## Manual Investigation (What Agent Will Do)

```bash
# 1. Check pod status
kubectl get pods -n test-failures

# 2. Describe pod for events
kubectl describe pod <pod-name> -n test-failures

# 3. Check logs
kubectl logs <pod-name> -n test-failures

# 4. Check recent events
kubectl get events -n test-failures --sort-by='.lastTimestamp' | grep crashloop
```

## Expected Agent Report

The agent should generate a report with:

- **Executive Summary**: "Application pod crash-looping due to inability to connect to database service at database-service:5432"
- **Timeline**: Deployment created → Pod started → Connection failed → Crash → Restart cycle began
- **Root Cause**: Database service 'database-service' does not exist in namespace
- **Evidence**: Log lines showing "Connection refused", Kubernetes events showing restarts
- **Immediate Fix**: `kubectl delete deployment crashloop-test-app -n test-failures` (stop the failing deployment)
- **Root Fix**:
  1. Create database service
  2. Update DB_HOST to correct service name
  3. Add missing DB_PASSWORD
  4. Redeploy

## Cleanup

```bash
kubectl delete -f examples/crashloop-scenario/bad-deployment.yaml -n test-failures
```

## Variations

You can modify this scenario to test different issues:

1. **Wrong port**: Change DB_PORT to 3306 (MySQL port) while still trying PostgreSQL
2. **Missing credentials**: Add a database but don't provide credentials
3. **Wrong namespace**: Point to database-service.production.svc.cluster.local
