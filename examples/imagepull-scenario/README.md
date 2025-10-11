# ImagePullBackOff Test Scenario

Simulates a pod that cannot start due to an invalid container image tag.

## Failure Scenario

**Root Cause**: Container image tag doesn't exist in registry

**Symptoms**:
- Pod stuck in ImagePullBackOff or ErrImagePull state
- Pod never becomes ready (0/1 Ready)
- No logs available (container never started)
- Kubernetes events show image pull errors
- Error message: "manifest unknown" or "not found"

## Expected Alert

```
Alert: KubePodNotReady or KubePodImagePullBackOff
Severity: warning
Namespace: test-failures
Pod: imagepull-test-app-xxxxx-yyyyy
Reason: ImagePullBackOff
```

## What the Agent Should Find

1. **Pod Status**: ImagePullBackOff or ErrImagePull
2. **Container Status**: Waiting (reason: ImagePullBackOff)
3. **No Logs**: Container never started, so no application logs
4. **Events**: "Failed to pull image" with detailed error
5. **Root Cause**: Image tag "nginx:this-tag-does-not-exist-v999" not found in registry
6. **Solution**: Use correct image tag

## Deploy Scenario

```bash
# Deploy the deployment with bad image
kubectl apply -f examples/imagepull-scenario/imagepull-deployment.yaml -n test-failures

# Watch pod status
kubectl get pods -n test-failures --watch

# You should see:
# imagepull-test-app-xxxxx-yyyyy   0/1     ErrImagePull      0          30s
# imagepull-test-app-xxxxx-yyyyy   0/1     ImagePullBackOff  0          45s
```

## Manual Investigation (What Agent Will Do)

```bash
# 1. Check pod status
kubectl get pods -n test-failures

# Output:
# NAME                                  READY   STATUS             RESTARTS   AGE
# imagepull-test-app-xxxxx-yyyyy        0/1     ImagePullBackOff   0          2m

# 2. Describe pod - look for image pull error
kubectl describe pod <pod-name> -n test-failures

# Output will show:
#   State:          Waiting
#     Reason:       ImagePullBackOff
#   Events:
#     Failed to pull image "nginx:this-tag-does-not-exist-v999":
#     rpc error: code = Unknown desc = Error response from daemon:
#     manifest for nginx:this-tag-does-not-exist-v999 not found

# 3. Try to get logs (will fail - container never started)
kubectl logs <pod-name> -n test-failures
# Error: container is waiting to start

# 4. Check events
kubectl get events -n test-failures --sort-by='.lastTimestamp' | grep imagepull

# 5. Check image specification
kubectl get pod <pod-name> -n test-failures -o jsonpath='{.spec.containers[0].image}'
# Output: nginx:this-tag-does-not-exist-v999
```

## Expected Agent Report

The agent should generate a report with:

- **Executive Summary**: "Pod cannot start due to image pull failure - image tag 'nginx:this-tag-does-not-exist-v999' not found in registry"
- **Timeline**:
  - Deployment created
  - Kubernetes attempted to pull image
  - Pull failed: manifest not found
  - Retry with exponential backoff
  - Pod remains in ImagePullBackOff
- **Root Cause**: Invalid image tag specified in deployment - 'nginx:this-tag-does-not-exist-v999' does not exist in Docker Hub
- **Evidence**:
  - Pod status: ImagePullBackOff
  - Container state: Waiting (ImagePullBackOff)
  - Kubernetes event: "Failed to pull image ... manifest not found"
  - No application logs (container never started)
- **Immediate Fix**: Delete deployment or update with correct image
  ```bash
  kubectl delete deployment imagepull-test-app -n test-failures
  ```
- **Root Fix**:
  1. Identify correct image tag
     ```bash
     # Check available tags:
     # https://hub.docker.com/_/nginx/tags
     ```
  2. Update deployment with valid tag (e.g., `nginx:latest` or `nginx:1.25`)
     ```bash
     kubectl set image deployment/imagepull-test-app app=nginx:latest -n test-failures
     ```
  3. Verify pod starts successfully
     ```bash
     kubectl get pods -n test-failures --watch
     ```
- **Prevention**:
  - Use image tags from verified sources
  - Implement image scanning in CI/CD
  - Use imagePullPolicy: IfNotPresent for testing
  - Pin to specific versions, not "latest"
  - Test image pull in CI before deployment

## Common Variations

This scenario demonstrates one type of image pull failure. Other common variations:

1. **Private Registry Authentication**:
   - Image exists but requires authentication
   - Error: "unauthorized" or "authentication required"
   - Solution: Create imagePullSecret

2. **Network Issues**:
   - Registry unreachable due to network policy
   - Error: "connection timeout" or "connection refused"
   - Solution: Fix network connectivity or policy

3. **Rate Limiting**:
   - Docker Hub rate limits exceeded (anonymous pulls)
   - Error: "Too Many Requests"
   - Solution: Use authenticated pulls or private registry

4. **Wrong Registry**:
   - Image path points to wrong registry
   - Example: `gcr.io/my-project/image` but project doesn't exist
   - Solution: Fix registry path

## Cleanup

```bash
kubectl delete -f examples/imagepull-scenario/imagepull-deployment.yaml -n test-failures
```

## Why This Is Important

ImagePullBackOff is one of the most common Kubernetes deployment failures, especially for:
- New teams learning Kubernetes
- Deployments after CI/CD pipeline changes
- Registry migrations
- Image tagging mistakes

The agent should quickly identify the exact image name and provide actionable next steps.
