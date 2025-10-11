# Known Issues & Solutions

This file contains patterns of previously encountered issues and their solutions. The agent uses this to quickly identify and resolve common problems.

---

## Issue Patterns

### Pattern: ImagePullBackOff

**Symptoms**: Pod stuck in ImagePullBackOff state

**Common Causes**:
1. Invalid image tag or image doesn't exist
2. Registry authentication failure
3. Registry unreachable (network issues)
4. Private registry without imagePullSecrets configured

**Investigation Steps**:
1. Check if image exists: `docker manifest inspect <image>` (requires internet access)
2. Verify imagePullSecrets are configured in pod spec
3. Test registry connectivity from cluster
4. Check image tag in deployment/helm values

**Solutions**:
- Fix image tag in deployment spec or Helm values
- Create and attach imagePullSecrets if using private registry
- Use alternative registry if primary is down
- Check for typos in image name

**Prevention**:
- Validate image exists before deployment
- Use image validation in CI/CD pipeline
- Configure registry mirroring for redundancy

---

### Pattern: CrashLoopBackOff

**Symptoms**: Container repeatedly crashes and restarts

**Common Causes**:
1. Application error (check logs for stack traces)
2. Failed liveness/readiness probes
3. OOMKilled (exit code 137)
4. Missing environment variables or configuration
5. Dependency not available (database, API, etc.)

**Investigation Steps**:
1. Check container exit code
2. Review logs (current and previous container)
3. Check resource limits vs actual usage
4. Verify environment variables and ConfigMaps
5. Check dependent services are healthy
6. Review recent configuration or code changes

**Solutions**:
- Fix application code if bug identified
- Adjust probe timing or thresholds
- Increase memory limits if OOMKilled
- Add missing configuration
- Wait for or fix dependent services
- Rollback to previous working version

**Prevention**:
- Implement comprehensive health checks
- Set appropriate resource limits
- Validate configuration before deployment
- Add dependency health checks to startup

---

### Pattern: OOMKilled (Exit Code 137)

**Symptoms**: Container killed due to out-of-memory

**Common Causes**:
1. Memory limit set too low for workload
2. Memory leak in application
3. Unexpected traffic spike
4. Large data processing without streaming

**Investigation Steps**:
1. Check container exit code (should be 137)
2. Review memory limits in pod spec
3. Query Prometheus for memory usage trends
4. Check application logs for memory-related errors
5. Compare memory usage across replicas

**Solutions**:
- Increase memory limits if workload legitimately needs more
- Investigate and fix memory leaks
- Implement memory-efficient algorithms
- Add horizontal pod autoscaling for traffic spikes
- Configure memory request/limit appropriately

**Prevention**:
- Load test applications before production
- Monitor memory usage trends
- Implement memory profiling
- Set up alerts for high memory usage

---

### Pattern: Pending Pod (Insufficient Resources)

**Symptoms**: Pod remains in Pending state

**Common Causes**:
1. Insufficient CPU/memory on nodes
2. No nodes match pod's nodeSelector/affinity
3. No nodes match pod's tolerations
4. PersistentVolumeClaim not bound
5. Resource quotas exceeded

**Investigation Steps**:
1. Check pod events: `kubectl describe pod <name>`
2. Review node resources: `kubectl top nodes`
3. Check for node selectors/affinity in pod spec
4. Verify PVC status if volumes are used
5. Check namespace resource quotas

**Solutions**:
- Scale cluster to add more nodes
- Adjust pod resource requests
- Remove or fix node selectors/affinity
- Provision storage for PVC
- Increase namespace quotas

---

### Pattern: Readiness Probe Failing

**Symptoms**: Pod running but not receiving traffic

**Common Causes**:
1. Application slow to start
2. Probe endpoint incorrect
3. Dependency not yet available
4. Probe timeout too short

**Investigation Steps**:
1. Check readiness probe configuration
2. Test probe endpoint manually
3. Review application startup logs
4. Check timing: initialDelaySeconds, periodSeconds, timeoutSeconds

**Solutions**:
- Increase initialDelaySeconds if app needs more startup time
- Fix probe endpoint path
- Adjust probe timing parameters
- Implement proper health check in application

---

### Pattern: DNS Resolution Failures

**Symptoms**: Services can't resolve other service names

**Common Causes**:
1. CoreDNS not running or unhealthy
2. Incorrect service name format
3. Service in different namespace (missing namespace suffix)
4. Network policy blocking DNS

**Investigation Steps**:
1. Check CoreDNS pods: `kubectl get pods -n kube-system -l k8s-app=kube-dns`
2. Test DNS from pod: `nslookup kubernetes.default`
3. Verify service name format (service.namespace.svc.cluster.local)
4. Check network policies

**Solutions**:
- Restart CoreDNS if unhealthy
- Use fully qualified service names
- Fix or adjust network policies
- Check cluster DNS configuration

---

### Pattern: Certificate/TLS Errors

**Symptoms**: HTTPS connections failing with certificate errors

**Common Causes**:
1. Certificate expired
2. Certificate doesn't match hostname
3. Certificate not trusted (self-signed or wrong CA)
4. Certificate not properly mounted in pod

**Investigation Steps**:
1. Check certificate expiration: `openssl x509 -in cert.pem -noout -dates`
2. Verify certificate subject/SANs
3. Check certificate chain
4. Verify certificate is mounted in pod

**Solutions**:
- Renew expired certificates
- Update certificate with correct SANs
- Add CA to trusted store
- Fix certificate mounting in deployment

---

## Solved Incidents

[This section will be populated by the agent as it resolves incidents]

Format:
```
### Incident: [Date] - [Brief Description]
**Alert**: [Alert name]
**Root Cause**: [Identified cause]
**Solution Applied**: [What fixed it]
**Verification**: [How it was verified]
**Pattern**: [If matches known pattern above]
```

---

## Notes

- The agent will append new patterns here as it encounters novel issues
- Manual additions are welcome - the agent will learn from them
- Keep solutions actionable with specific commands when possible
