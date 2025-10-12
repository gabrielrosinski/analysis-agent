# Analysis Agent Helm Chart

AI-powered Root Cause Analysis agent for Kubernetes using the Kagent framework and Anthropic Claude.

## Overview

This Helm chart deploys the complete DevOps RCA system to any Kubernetes cluster, including:

- **Webhook Service**: Receives AlertManager webhooks
- **Notifier Service**: Sends email notifications
- **Kagent AI Agent**: Intelligent RCA investigator
- **RBAC Resources**: ServiceAccounts, ClusterRole, ClusterRoleBinding
- **Persistent Storage**: For agent memory and learnings

## Prerequisites

1. **Kubernetes Cluster**: v1.28+
2. **Helm**: v3.12+
3. **Kagent Operator**: Must be installed separately (see [Installation Guide](../../docs/INSTALLATION.md#step-1-install-kagent-operator))
4. **Anthropic API Key**: Configured in Kagent (see prerequisites)
5. **Gmail Account**: With app password for email notifications
6. **Prometheus + AlertManager**: For alert integration (optional for testing)

## Installation

### 1. Install Kagent Operator First

```bash
# Install Kagent CRDs
helm install kagent-crds oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
    --namespace kagent \
    --create-namespace

# Install Kagent with Anthropic provider
export ANTHROPIC_API_KEY="sk-ant-api-YOUR-KEY-HERE"
kubectl create secret generic kagent-anthropic \
    -n kagent \
    --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY

helm install kagent oci://ghcr.io/kagent-dev/kagent/helm/kagent \
    --namespace kagent \
    --set providers.default=anthropic \
    --set providers.anthropic.apiKeySecret=kagent-anthropic \
    --set providers.anthropic.apiKeySecretKey=ANTHROPIC_API_KEY

# Create ModelConfig for Claude
cat <<EOF | kubectl apply -f -
apiVersion: kagent.dev/v1alpha2
kind: ModelConfig
metadata:
  name: claude-sonnet-config
  namespace: kagent
spec:
  provider: Anthropic
  model: claude-3-5-sonnet-20241022
  apiKeySecret: kagent-anthropic
  apiKeySecretKey: ANTHROPIC_API_KEY
  anthropic: {}
EOF
```

### 2. Prepare Secrets

Create secrets for Gmail and email recipients:

```bash
# Gmail credentials
kubectl create secret generic gmail-credentials \
  -n analysis-agent \
  --from-literal=username="your-email@gmail.com" \
  --from-literal=password="your-app-password" \
  --from-literal=from-address="DevOps RCA Agent <your-email@gmail.com>"

# Email recipients by severity
kubectl create secret generic email-recipients \
  -n analysis-agent \
  --from-literal=recipients-critical="oncall@example.com,sre@example.com" \
  --from-literal=recipients-warning="devops@example.com" \
  --from-literal=recipients-info="devops-alerts@example.com"
```

### 3. Install the Chart

**Option A: Default Installation (Recommended)**

Uses pre-built images from GitHub Container Registry. No customization needed!

```bash
# Simple installation - uses default pre-built images
helm install analysis-agent ./chart/analysis-agent \
  --namespace analysis-agent \
  --create-namespace
```

**That's it!** The chart automatically uses:
- `ghcr.io/your-org/analysis-agent-webhook:0.1.0`
- `ghcr.io/your-org/analysis-agent-notifier:0.1.0`

**Option B: Custom Images** (only if you built your own images)

```bash
# Override image repositories
helm install analysis-agent ./chart/analysis-agent \
  --namespace analysis-agent \
  --create-namespace \
  --set webhook.image.repository=your-registry/webhook \
  --set webhook.image.tag=custom \
  --set notifier.image.repository=your-registry/notifier \
  --set notifier.image.tag=custom
```

**Option C: With Values File** (for production settings)

```bash
# Create custom values
cat <<EOF > my-values.yaml
# Only specify what you want to change
# Images default to ghcr.io/your-org/... if not specified

webhook:
  replicaCount: 3
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi

notifier:
  replicaCount: 3
  email:
    recipients:
      critical: "oncall@mycompany.com"
      warning: "devops@mycompany.com"
      info: "alerts@mycompany.com"
EOF

# Install with custom values
helm install analysis-agent ./chart/analysis-agent \
  --namespace analysis-agent \
  --create-namespace \
  -f my-values.yaml
```

### 4. Verify Installation

```bash
# Check all resources
kubectl get all -n analysis-agent

# Check agent status
kubectl get agent devops-rca-agent -n analysis-agent

# View logs
kubectl logs -f -n analysis-agent -l app=webhook-service
```

## Configuration

### Key Values

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespace` | Namespace to install | `analysis-agent` |
| `kagent.namespace` | Kagent operator namespace | `kagent` |
| `kagent.modelConfig` | ModelConfig name | `claude-sonnet-config` |
| `webhook.enabled` | Enable webhook service | `true` |
| `webhook.replicaCount` | Number of webhook replicas | `2` |
| `webhook.image.repository` | Webhook image repository | `ghcr.io/your-org/analysis-agent-webhook` |
| `webhook.image.tag` | Webhook image tag | `0.1.0` |
| `notifier.enabled` | Enable notifier service | `true` |
| `notifier.replicaCount` | Number of notifier replicas | `2` |
| `notifier.image.repository` | Notifier image repository | `ghcr.io/your-org/analysis-agent-notifier` |
| `notifier.image.tag` | Notifier image tag | `0.1.0` |
| `agent.enabled` | Enable agent | `true` |
| `agent.name` | Agent name | `devops-rca-agent` |
| `storage.enabled` | Enable persistent storage | `true` |
| `storage.pvc.size` | PVC size for agent memory | `5Gi` |
| `storage.pvc.storageClassName` | Storage class name | `""` (default) |
| `rbac.create` | Create RBAC resources | `true` |
| `secrets.create` | Create secrets from values | `false` |

### Example: Production Configuration

```yaml
# production-values.yaml
global:
  namespace: analysis-agent-prod

kagent:
  namespace: kagent-prod
  modelConfig: claude-sonnet-prod

webhook:
  replicaCount: 3
  image:
    repository: myregistry.io/analysis-agent-webhook
    tag: v1.0.0
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 200m
      memory: 256Mi

notifier:
  replicaCount: 3
  image:
    repository: myregistry.io/analysis-agent-notifier
    tag: v1.0.0
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 200m
      memory: 256Mi
  email:
    recipients:
      critical: "pagerduty@company.com,sre-oncall@company.com"
      warning: "devops-team@company.com"
      info: "monitoring-alerts@company.com"

storage:
  pvc:
    storageClassName: fast-ssd
    size: 20Gi

nodeSelector:
  workload: monitoring

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values:
                  - webhook-service
                  - notifier-service
          topologyKey: kubernetes.io/hostname
```

Install with production values:

```bash
helm install analysis-agent ./chart/analysis-agent \
  -n analysis-agent-prod \
  --create-namespace \
  -f production-values.yaml
```

## Upgrades

```bash
# Upgrade with new values
helm upgrade analysis-agent ./chart/analysis-agent \
  -n analysis-agent \
  -f my-values.yaml

# Upgrade with new image versions
helm upgrade analysis-agent ./chart/analysis-agent \
  -n analysis-agent \
  --set webhook.image.tag=v0.2.0 \
  --set notifier.image.tag=v0.2.0
```

## Uninstallation

```bash
# Uninstall the release
helm uninstall analysis-agent -n analysis-agent

# Delete namespace (optional)
kubectl delete namespace analysis-agent
```

**Warning**: Uninstalling will delete the PVC and all agent memory/learnings unless you backup first.

## Backup Agent Memory

```bash
# Backup agent memory before uninstall
AGENT_POD=$(kubectl get pod -n analysis-agent -l component=agent -o jsonpath='{.items[0].metadata.name}')
kubectl cp analysis-agent/$AGENT_POD:/agent-memory ./agent-memory-backup
```

## Testing

### Send Test Alert

```bash
# Port forward webhook service
kubectl port-forward -n analysis-agent svc/webhook-service 8080:8080

# Send test alert
curl -X POST http://localhost:8080/api/v1/webhook/test \
  -H "Content-Type: application/json" \
  -d '{
    "version": "4",
    "status": "firing",
    "alerts": [{
      "status": "firing",
      "labels": {
        "alertname": "TestAlert",
        "severity": "warning",
        "namespace": "default",
        "pod": "test-pod"
      },
      "annotations": {
        "description": "Test alert for RCA agent",
        "summary": "Testing RCA system"
      }
    }]
  }'
```

### Test Email Notifications

```bash
# Port forward notifier service
kubectl port-forward -n analysis-agent svc/notifier-service 8081:8080

# Send test email
curl -X POST http://localhost:8081/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '["your-test-email@example.com"]'
```

## Integration with AlertManager

Configure AlertManager to send webhooks to the agent:

```yaml
# alertmanager-config.yaml
receivers:
  - name: 'devops-rca-agent'
    webhook_configs:
      - url: 'http://webhook-service.analysis-agent.svc.cluster.local:8080/api/v1/webhook'
        send_resolved: false

route:
  group_wait: 10s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'devops-rca-agent'
  routes:
    - match:
        severity: critical
      receiver: devops-rca-agent
      continue: true
    - match:
        severity: warning
      receiver: devops-rca-agent
      continue: true
```

Apply configuration:

```bash
kubectl apply -f alertmanager-config.yaml -n monitoring
kubectl rollout restart statefulset/alertmanager-prometheus-kube-prometheus-alertmanager -n monitoring
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n analysis-agent

# View pod logs
kubectl logs -n analysis-agent <pod-name>

# Describe pod for events
kubectl describe pod -n analysis-agent <pod-name>
```

### Agent Not Investigating Alerts

```bash
# Check agent resource
kubectl get agent devops-rca-agent -n analysis-agent
kubectl describe agent devops-rca-agent -n analysis-agent

# Check Kagent controller logs
kubectl logs -n kagent -l app.kubernetes.io/name=kagent-controller --tail=100

# Verify RBAC permissions
kubectl auth can-i list pods \
  --as=system:serviceaccount:analysis-agent:agent-sa \
  --all-namespaces
```

### Email Not Sending

```bash
# Check notifier logs
kubectl logs -n analysis-agent -l app=notifier-service

# Verify secrets
kubectl get secret gmail-credentials -n analysis-agent -o yaml
kubectl get secret email-recipients -n analysis-agent -o yaml

# Test notifier directly
kubectl port-forward -n analysis-agent svc/notifier-service 8081:8080
curl -X POST http://localhost:8081/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '["your-email@example.com"]'
```

## Advanced Configuration

### Using External Secrets Operator

```yaml
# external-secret.yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: gmail-credentials
  namespace: analysis-agent
spec:
  secretStoreRef:
    name: aws-secretsmanager
  target:
    name: gmail-credentials
  data:
    - secretKey: username
      remoteRef:
        key: prod/rca-agent/gmail-username
    - secretKey: password
      remoteRef:
        key: prod/rca-agent/gmail-password
    - secretKey: from-address
      remoteRef:
        key: prod/rca-agent/from-address
```

### Custom Agent Instructions

Override default instructions:

```yaml
agent:
  instructions: |
    You are a specialized RCA agent for our e-commerce platform.
    Focus on: payment processing, inventory management, and user authentication.

    Investigation priorities:
    1. Payment gateway issues (highest priority)
    2. Database connection problems
    3. Cache invalidation issues
    4. Third-party API failures

    When investigating, always check:
    - Redis cache status
    - PostgreSQL connection pool
    - Stripe API connectivity
    - AWS service health
```

### Multi-Cluster Deployment

Deploy to multiple clusters with different configurations:

```bash
# Cluster 1 (Production US)
helm install analysis-agent ./chart/analysis-agent \
  -n analysis-agent \
  -f values-prod-us.yaml \
  --kube-context prod-us-cluster

# Cluster 2 (Production EU)
helm install analysis-agent ./chart/analysis-agent \
  -n analysis-agent \
  -f values-prod-eu.yaml \
  --kube-context prod-eu-cluster
```

## Security Considerations

1. **Secrets Management**: Use external secret management (External Secrets Operator, Sealed Secrets, Vault)
2. **RBAC**: Agent has read-only cluster access (no write permissions)
3. **Network Policies**: Implement network policies to restrict traffic
4. **Image Security**: Use private registries and image scanning
5. **API Key Rotation**: Regularly rotate Anthropic API keys and Gmail passwords

## Performance Tuning

### Resource Limits

Adjust based on cluster size and alert volume:

```yaml
webhook:
  resources:
    limits:
      cpu: 2000m
      memory: 2Gi
    requests:
      cpu: 500m
      memory: 512Mi

notifier:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 250m
      memory: 256Mi
```

### Autoscaling (HPA)

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: webhook-hpa
  namespace: analysis-agent
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: webhook-service
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

## Support

- **Documentation**: [Main README](../../README.md)
- **Installation Guide**: [INSTALLATION.md](../../docs/INSTALLATION.md)
- **Issues**: [GitHub Issues](https://github.com/your-org/analysis-agent/issues)
- **Slack**: #devops-rca-agent

## License

[Your License]

---

**Chart Version**: 0.1.0
**App Version**: 0.1.0
**Last Updated**: 2025-10-12
