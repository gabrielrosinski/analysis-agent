# Helm Chart Deployment Guide

This guide explains how to deploy the Analysis Agent to any Kubernetes cluster using the custom Helm chart.

## Overview

The Helm chart packages the complete DevOps RCA system for easy deployment, including:

- **Webhook Service** - Receives AlertManager webhooks
- **Notifier Service** - Sends email notifications
- **Kagent AI Agent** - Intelligent RCA investigator
- **RBAC Resources** - ServiceAccounts, ClusterRole, ClusterRoleBinding
- **Persistent Storage** - PVC for agent memory

## Prerequisites

Before using this guide, complete the basic installation:

**→ [Complete Installation Guide](./INSTALLATION.md)** ⭐

This includes:
1. **Prerequisites**: Verify tools, get API keys → [Prerequisites](./INSTALLATION.md#prerequisites)
2. **Install Kagent**: Deploy operator with Claude → [Step 1](./INSTALLATION.md#step-1-install-kagent-operator)
3. **Configure Secrets**: Gmail, recipients → [Step 2](./INSTALLATION.md#step-2-configure-secrets)
4. **Basic Helm Deployment**: Single helm install command (uses pre-built images) → [Step 3](./INSTALLATION.md#step-3-deploy-application)
5. **Verify Installation**: Test all components → [Step 4](./INSTALLATION.md#step-4-verify-installation)
6. **Configure AlertManager**: Enable real alerts → [Step 5](./INSTALLATION.md#step-5-configure-alertmanager) ⚠️ **Required**

Once you have a working basic installation, use this guide for:
- ✅ Production configurations with custom values
- ✅ Multi-environment deployments (dev/staging/prod)
- ✅ CI/CD integration (GitLab CI, GitHub Actions)
- ✅ Advanced Helm patterns (rollback, upgrades, backup)
- ✅ External secrets management
- ✅ Monitoring and ingress configuration

---

## Deployment Options

### Option 1: Using Values File (Recommended)

Create a custom values file:

```yaml
# my-values.yaml
global:
  namespace: analysis-agent

webhook:
  replicaCount: 2
  image:
    repository: your-registry/analysis-agent-webhook
    tag: v0.1.0

notifier:
  replicaCount: 2
  image:
    repository: your-registry/analysis-agent-notifier
    tag: v0.1.0
  email:
    recipients:
      critical: "oncall@company.com,sre@company.com"
      warning: "devops@company.com"
      info: "alerts@company.com"

storage:
  pvc:
    size: 10Gi
    storageClassName: fast-ssd
```

Install:

```bash
helm install analysis-agent ./chart/analysis-agent \
  -n analysis-agent \
  --create-namespace \
  -f my-values.yaml
```

### Option 2: Using --set Flags

```bash
helm install analysis-agent ./chart/analysis-agent \
  --namespace analysis-agent \
  --create-namespace \
  --set webhook.image.repository=your-registry/webhook \
  --set webhook.image.tag=v0.1.0 \
  --set notifier.image.repository=your-registry/notifier \
  --set notifier.image.tag=v0.1.0 \
  --set storage.pvc.size=10Gi
```

### Option 3: Package and Deploy from Chart Repository

```bash
# Package the chart
helm package chart/analysis-agent

# Upload to chart repository (e.g., Harbor, ChartMuseum)
helm repo add myrepo https://charts.example.com
helm cm-push analysis-agent-0.1.0.tgz myrepo

# Install from repository
helm repo update
helm install analysis-agent myrepo/analysis-agent \
  -n analysis-agent \
  -f values.yaml
```

## Production Deployment

### 1. Use External Secrets Management

#### Using External Secrets Operator

```yaml
# external-secrets.yaml
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
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: email-recipients
  namespace: analysis-agent
spec:
  secretStoreRef:
    name: aws-secretsmanager
  target:
    name: email-recipients
  data:
    - secretKey: recipients-critical
      remoteRef:
        key: prod/rca-agent/recipients-critical
    - secretKey: recipients-warning
      remoteRef:
        key: prod/rca-agent/recipients-warning
    - secretKey: recipients-info
      remoteRef:
        key: prod/rca-agent/recipients-info
```

Deploy external secrets first:

```bash
kubectl apply -f external-secrets.yaml
helm install analysis-agent ./chart/analysis-agent -f prod-values.yaml
```

#### Using Sealed Secrets

```bash
# Create sealed secrets
kubectl create secret generic gmail-credentials \
  --from-literal=username="your-email@gmail.com" \
  --from-literal=password="your-app-password" \
  --from-literal=from-address="RCA Agent <email@gmail.com>" \
  --dry-run=client -o yaml | \
  kubeseal -o yaml > gmail-credentials-sealed.yaml

kubectl apply -f gmail-credentials-sealed.yaml
helm install analysis-agent ./chart/analysis-agent -f prod-values.yaml
```

### 2. Production Values Configuration

```yaml
# production-values.yaml
global:
  namespace: analysis-agent

kagent:
  namespace: kagent
  modelConfig: claude-sonnet-prod

webhook:
  replicaCount: 3
  image:
    repository: your-registry.io/analysis-agent-webhook
    tag: v1.0.0
    pullPolicy: Always
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
    repository: your-registry.io/analysis-agent-notifier
    tag: v1.0.0
    pullPolicy: Always
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 200m
      memory: 256Mi

storage:
  pvc:
    size: 20Gi
    storageClassName: gp3-encrypted

nodeSelector:
  workload: monitoring

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
            - key: app
              operator: In
              values:
                - webhook-service
                - notifier-service
        topologyKey: kubernetes.io/hostname

imagePullSecrets:
  - name: registry-credentials
```

### 3. Enable Monitoring

```yaml
# Enable ServiceMonitor for Prometheus Operator
serviceMonitor:
  enabled: true
  namespace: monitoring
  interval: 30s
  scrapeTimeout: 10s
```

### 4. Configure Ingress

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: rca-webhook.example.com
      paths:
        - path: /
          pathType: Prefix
          service: webhook-service
  tls:
    - secretName: rca-webhook-tls
      hosts:
        - rca-webhook.example.com
```

## Multi-Environment Deployment

### Development Environment

```yaml
# values-dev.yaml
global:
  namespace: analysis-agent-dev

webhook:
  replicaCount: 1
  resources:
    limits:
      cpu: 500m
      memory: 512Mi

notifier:
  replicaCount: 1
  resources:
    limits:
      cpu: 500m
      memory: 512Mi

storage:
  pvc:
    size: 5Gi
```

```bash
helm install analysis-agent-dev ./chart/analysis-agent \
  -n analysis-agent-dev \
  --create-namespace \
  -f values-dev.yaml
```

### Staging Environment

```yaml
# values-staging.yaml
global:
  namespace: analysis-agent-staging

webhook:
  replicaCount: 2
  image:
    tag: v1.0.0-rc.1

notifier:
  replicaCount: 2
  image:
    tag: v1.0.0-rc.1

storage:
  pvc:
    size: 10Gi
```

```bash
helm install analysis-agent-staging ./chart/analysis-agent \
  -n analysis-agent-staging \
  --create-namespace \
  -f values-staging.yaml
```

### Production Environment

```bash
helm install analysis-agent-prod ./chart/analysis-agent \
  -n analysis-agent-prod \
  --create-namespace \
  -f production-values.yaml
```

## Upgrading

### Zero-Downtime Upgrade

```bash
# Upgrade webhook service first
helm upgrade analysis-agent ./chart/analysis-agent \
  -n analysis-agent \
  --set webhook.image.tag=v0.2.0 \
  --wait

# Then upgrade notifier
helm upgrade analysis-agent ./chart/analysis-agent \
  -n analysis-agent \
  --set notifier.image.tag=v0.2.0 \
  --wait

# Verify
kubectl get pods -n analysis-agent
```

### Rollback

```bash
# View release history
helm history analysis-agent -n analysis-agent

# Rollback to previous version
helm rollback analysis-agent -n analysis-agent

# Rollback to specific revision
helm rollback analysis-agent 3 -n analysis-agent
```

## CI/CD Integration

### GitLab CI Example

```yaml
# .gitlab-ci.yml
stages:
  - build
  - deploy

build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY/webhook:$CI_COMMIT_TAG services/webhook
    - docker build -t $CI_REGISTRY/notifier:$CI_COMMIT_TAG services/notifier
    - docker push $CI_REGISTRY/webhook:$CI_COMMIT_TAG
    - docker push $CI_REGISTRY/notifier:$CI_COMMIT_TAG

deploy:prod:
  stage: deploy
  script:
    - helm upgrade --install analysis-agent ./chart/analysis-agent \
        -n analysis-agent \
        -f values-prod.yaml \
        --set webhook.image.tag=$CI_COMMIT_TAG \
        --set notifier.image.tag=$CI_COMMIT_TAG \
        --wait
  only:
    - tags
  environment:
    name: production
```

### GitHub Actions Example

```yaml
# .github/workflows/deploy.yml
name: Deploy to Kubernetes

on:
  push:
    tags:
      - 'v*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build and push images
        run: |
          docker build -t ${{ secrets.REGISTRY }}/webhook:${{ github.ref_name }} services/webhook
          docker build -t ${{ secrets.REGISTRY }}/notifier:${{ github.ref_name }} services/notifier
          docker push ${{ secrets.REGISTRY }}/webhook:${{ github.ref_name }}
          docker push ${{ secrets.REGISTRY }}/notifier:${{ github.ref_name }}

      - name: Deploy with Helm
        run: |
          helm upgrade --install analysis-agent ./chart/analysis-agent \
            -n analysis-agent \
            -f values-prod.yaml \
            --set webhook.image.tag=${{ github.ref_name }} \
            --set notifier.image.tag=${{ github.ref_name }} \
            --wait
```

## Backup and Restore

### Backup Agent Memory

```bash
# Create backup
AGENT_POD=$(kubectl get pod -n analysis-agent -l component=agent -o jsonpath='{.items[0].metadata.name}')
kubectl cp analysis-agent/$AGENT_POD:/agent-memory ./backup-$(date +%Y%m%d)

# Or use velero for full cluster backup
velero backup create analysis-agent-backup --include-namespaces analysis-agent
```

### Restore Agent Memory

```bash
# Restore from backup
kubectl cp ./backup-20251012 analysis-agent/$AGENT_POD:/agent-memory

# Or restore with velero
velero restore create --from-backup analysis-agent-backup
```

## Troubleshooting

### Chart Installation Fails

```bash
# Debug template rendering
helm template test ./chart/analysis-agent \
  --debug \
  --set webhook.image.repository=test/webhook \
  --set notifier.image.repository=test/notifier

# Validate chart
helm lint ./chart/analysis-agent
```

### Pods Not Starting

```bash
# Check events
kubectl get events -n analysis-agent --sort-by='.lastTimestamp'

# Check pod status
kubectl describe pod -n analysis-agent <pod-name>

# Check image pull
kubectl get pods -n analysis-agent -o jsonpath='{.items[*].spec.containers[*].image}'
```

### Agent Not Connecting to Kagent

```bash
# Verify ModelConfig exists
kubectl get modelconfig -n kagent

# Check Kagent controller logs
kubectl logs -n kagent -l app.kubernetes.io/name=kagent-controller --tail=50

# Verify agent spec
kubectl get agent devops-rca-agent -n analysis-agent -o yaml
```

## Best Practices

1. **Use External Secrets**: Never commit secrets to Git
2. **Pin Image Versions**: Don't use `latest` tag in production
3. **Resource Limits**: Always set resource limits
4. **Health Checks**: Verify liveness and readiness probes
5. **Monitoring**: Enable ServiceMonitor for Prometheus
6. **Backup Regularly**: Schedule automatic backups of agent memory
7. **Test Upgrades**: Always test in staging first
8. **Version Control**: Keep values files in Git (without secrets)

## Support

- **Chart Documentation**: [README.md](../chart/analysis-agent/README.md)
- **Installation Guide**: [INSTALLATION.md](./INSTALLATION.md)
- **Main Documentation**: [README.md](../README.md)
- **Issues**: Create an issue in the repository

---

**Last Updated**: 2025-10-12
**Chart Version**: 0.1.0
