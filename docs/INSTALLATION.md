# Installation Guide

Complete step-by-step guide to install and configure the DevOps RCA Agent on any Kubernetes cluster.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Install Kagent Operator](#step-1-install-kagent-operator)
3. [Step 2: Configure Secrets](#step-2-configure-secrets)
4. [Step 3: Deploy Application](#step-3-deploy-application)
5. [Step 4: Verify Installation](#step-4-verify-installation)
6. [Step 5: Configure AlertManager](#step-5-configure-alertmanager)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, ensure you have:

### Required Tools

- **Kubernetes Cluster**: v1.28+ (K3s, Minikube, or cloud-managed)
  ```bash
  kubectl version --short
  kubectl cluster-info
  ```

- **Helm**: v3.12+
  ```bash
  helm version
  ```

- **Docker**: v24.0+ (for building images)
  ```bash
  docker --version
  ```

### Required Accounts & Keys

1. **Anthropic API Key** (for Claude AI)
   - Sign up at: https://console.anthropic.com/
   - Create API key (starts with `sk-ant-api...`)
   - Add $5-10 credits for testing

2. **Gmail Account** (for email notifications)
   - Enable 2FA: https://myaccount.google.com/security
   - Generate app password: https://myaccount.google.com/apppasswords

3. **Docker Registry** (for image storage)
   - Docker Hub, or private registry (Harbor, ECR, GCR, ACR)

### System Resources

- **Minimum**: 4 vCPU, 8GB RAM, 20GB storage
- **Recommended**: 8 vCPU, 16GB RAM, 50GB storage

---

## Step 1: Install Kagent Operator

Kagent is the AI agent framework that powers the RCA analysis. Install it first.

### 1.1 Install Kagent CRDs

```bash
helm install kagent-crds oci://ghcr.io/kagent-dev/kagent/helm/kagent-crds \
    --namespace kagent \
    --create-namespace
```

**Verify:**
```bash
kubectl get crd | grep kagent
# Should show: agents.kagent.dev, modelconfigs.kagent.dev, etc.
```

### 1.2 Configure Anthropic API Key

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-api-YOUR-ACTUAL-KEY"

# Create secret
kubectl create secret generic kagent-anthropic \
    -n kagent \
    --from-literal=ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY
```

### 1.3 Install Kagent Operator

```bash
helm install kagent oci://ghcr.io/kagent-dev/kagent/helm/kagent \
    --namespace kagent \
    --set providers.default=anthropic \
    --set providers.anthropic.apiKeySecret=kagent-anthropic \
    --set providers.anthropic.apiKeySecretKey=ANTHROPIC_API_KEY
```

**Verify:**
```bash
kubectl get pods -n kagent
# Should show kagent-controller and kagent-ui pods running
```

### 1.4 Create Claude Model Configuration

```bash
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

**Verify:**
```bash
kubectl get modelconfig -n kagent
# Should show claude-sonnet-config
```

---

## Step 2: Configure Secrets

**Note**: Pre-built Docker images are provided. You do NOT need to build images yourself unless you're modifying the webhook/notifier services. See [Docker Build Guide](./DOCKER_BUILD.md) only if you need custom builds.

Create secrets for Gmail and email recipients.

### 2.1 Gmail Credentials

```bash
kubectl create secret generic gmail-credentials \
  -n analysis-agent \
  --from-literal=username="your-email@gmail.com" \
  --from-literal=password="your-16-char-app-password" \
  --from-literal=from-address="DevOps RCA Agent <your-email@gmail.com>"
```

### 2.2 Email Recipients

```bash
kubectl create secret generic email-recipients \
  -n analysis-agent \
  --from-literal=recipients-critical="oncall@example.com,sre@example.com" \
  --from-literal=recipients-warning="devops@example.com" \
  --from-literal=recipients-info="devops-alerts@example.com"
```

**Replace with your actual email addresses!**

### 2.3 GitHub Token (Optional)

For GitHub integration (commit correlation):

```bash
kubectl create secret generic github-credentials \
  -n analysis-agent \
  --from-literal=token="ghp_your_github_token"
```

---

## Step 3: Deploy Application

Choose **Option A (Helm)** for production or **Option B (Manual)** for learning.

### Option A: Deploy with Helm (Recommended)

```bash
# Install with Helm (uses pre-built images by default)
helm install analysis-agent ./chart/analysis-agent \
  --namespace analysis-agent \
  --create-namespace
```

**That's it!** The Helm chart uses pre-built images by default. No need to specify image repositories.

**For advanced Helm configurations** (custom images, production settings), see [Helm Deployment Guide](./HELM_DEPLOYMENT.md).

### Option B: Deploy Manually

```bash
# 1. Create namespace and RBAC
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/rbac.yaml

# 2. Create storage
kubectl apply -f manifests/storage.yaml

# 3. Initialize agent memory
./scripts/init-memory.sh

# 4. Deploy webhook service
kubectl apply -f manifests/deployments/webhook-deployment.yaml

# 5. Deploy notifier service
kubectl apply -f manifests/deployments/notifier-deployment.yaml

# 6. Deploy agent
kubectl apply -f agents/devops-rca-agent.yaml
```

---

## Step 4: Verify Installation

Check that all components are running correctly.

### 4.1 Check Pods

```bash
kubectl get pods -n analysis-agent
```

**Expected output:**
```
NAME                               READY   STATUS    RESTARTS   AGE
webhook-service-xxxxx-xxxxx        1/1     Running   0          1m
webhook-service-xxxxx-xxxxx        1/1     Running   0          1m
notifier-service-xxxxx-xxxxx       1/1     Running   0          1m
notifier-service-xxxxx-xxxxx       1/1     Running   0          1m
```

### 4.2 Check Agent

```bash
kubectl get agent devops-rca-agent -n analysis-agent
```

**Expected output:**
```
NAME               AGE
devops-rca-agent   1m
```

### 4.3 Test Webhook Service

```bash
# Port forward
kubectl port-forward -n analysis-agent svc/webhook-service 8080:8080

# In another terminal, send test request
curl -X POST http://localhost:8080/health

# Should return: {"status": "healthy"}
```

### 4.4 Test Notifier Service

```bash
# Port forward
kubectl port-forward -n analysis-agent svc/notifier-service 8081:8080

# Send test email
curl -X POST http://localhost:8081/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '["your-email@example.com"]'

# Check your email inbox for test message
```

### 4.5 Send Test Alert

```bash
# Use the test script
./tests/send-test-alert.sh

# Follow the prompts to send a test alert
# Check logs: kubectl logs -f -n analysis-agent -l app=webhook-service
```

### 4.6 Access Kagent Dashboard (UI)

The Kagent operator includes a web-based dashboard for monitoring and interacting with your agents.

```bash
# Port forward to Kagent UI service
kubectl port-forward -n kagent svc/kagent-ui 8082:8082
```

Open your browser to: **http://localhost:8082**

**Dashboard Features:**

- **Agent Overview**: View all deployed agents (including your `devops-rca-agent`)
- **Chat Interface**: Interact directly with agents for testing
- **Tool Inspection**: See available tools and their configurations
- **Execution History**: Review past agent investigations and responses
- **Configuration Review**: Verify agent settings and model configurations

**Using the Dashboard:**

1. **View Your Agent**: Navigate to the agents list and click on `devops-rca-agent` (from `analysis-agent` namespace)
2. **Test Agent Chat**: Send test queries like "What tools do you have available?" or "Check the cluster health"
3. **Review Tool Output**: Expand "Arguments" and "Results" sections to see tool executions
4. **Monitor Investigations**: View real-time updates when AlertManager triggers investigations

**Tips:**

- The dashboard shows agents from ALL namespaces (both `kagent` and `analysis-agent`)
- Use the "New Chat" button to start fresh conversations with your agent
- The UI automatically refreshes when new agent sessions start
- For production, consider setting up ingress instead of port-forward (see [Helm Deployment Guide](./HELM_DEPLOYMENT.md))

---

## Step 5: Configure AlertManager

Integrate with Prometheus AlertManager to receive real alerts.

### 5.1 Check AlertManager

```bash
kubectl get pods -n monitoring | grep alertmanager
# Should show alertmanager pods running
```

### 5.2 Configure Webhook

```bash
# Apply AlertManager configuration
kubectl apply -f manifests/alertmanager-config.yaml -n monitoring

# Restart AlertManager to pick up changes
kubectl rollout restart statefulset/alertmanager-prometheus-kube-prometheus-alertmanager -n monitoring
```

### 5.3 Verify Webhook Configuration

```bash
# Check AlertManager config
kubectl get configmap -n monitoring alertmanager-config -o yaml | grep webhook-service

# Should show webhook URL pointing to your webhook service
```

---

## Troubleshooting

### Issue: Kagent Operator Not Running

```bash
# Check pods
kubectl get pods -n kagent

# Check logs
kubectl logs -n kagent -l app.kubernetes.io/name=kagent-controller --tail=50

# Common fix: Verify API key secret
kubectl get secret kagent-anthropic -n kagent
```

### Issue: Images Not Pulling

```bash
# Check image pull status
kubectl describe pod -n analysis-agent <pod-name>

# Common fixes:
# 1. Create image pull secret (if using private registry)
kubectl create secret docker-registry regcred \
  --docker-server=your-registry \
  --docker-username=your-username \
  --docker-password=your-password \
  -n analysis-agent

# 2. Update deployment to use secret
kubectl patch deployment webhook-service -n analysis-agent \
  -p '{"spec":{"template":{"spec":{"imagePullSecrets":[{"name":"regcred"}]}}}}'
```

### Issue: Agent Not Investigating

```bash
# 1. Check agent resource
kubectl describe agent devops-rca-agent -n analysis-agent

# 2. Check Kagent controller logs
kubectl logs -n kagent -l app.kubernetes.io/name=kagent-controller --tail=100

# 3. Verify RBAC permissions
kubectl auth can-i list pods \
  --as=system:serviceaccount:analysis-agent:agent-sa \
  --all-namespaces
```

### Issue: Emails Not Sending

```bash
# 1. Check secret
kubectl get secret gmail-credentials -n analysis-agent -o yaml

# 2. Check notifier logs
kubectl logs -n analysis-agent -l app=notifier-service --tail=50

# 3. Verify Gmail app password
# - Must be 16 characters (no spaces)
# - 2FA must be enabled on Gmail account
# - App password generated from: https://myaccount.google.com/apppasswords
```

### Issue: Webhook Not Receiving Alerts

```bash
# Test connectivity from monitoring namespace
kubectl run test -n monitoring --rm -i --restart=Never --image=curlimages/curl -- \
  curl -v http://webhook-service.analysis-agent.svc.cluster.local:8080/health

# Check AlertManager config
kubectl get configmap -n monitoring alertmanager-config -o yaml

# Verify webhook URL is correct
```

---

## Next Steps

After successful installation:

1. **Monitor Operations**
   ```bash
   # Watch all logs
   kubectl logs -f -n analysis-agent --all-containers=true

   # Access Kagent dashboard (see Step 4.6 for full details)
   kubectl port-forward -n kagent svc/kagent-ui 8082:8082
   # Open: http://localhost:8082
   ```

2. **Create Test Failure**
   ```bash
   ./tests/create-test-failure.sh
   # Wait 2-3 minutes for alert to fire and agent to investigate
   ```

3. **View Reports**
   ```bash
   # List agent memory reports
   AGENT_POD=$(kubectl get pod -n analysis-agent -l component=agent -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -it -n analysis-agent $AGENT_POD -- ls -la /agent-memory/reports/
   ```

4. **Production Deployment**
   - See [Helm Deployment Guide](./HELM_DEPLOYMENT.md) for production patterns
   - Configure external secrets management
   - Set up monitoring and alerting
   - Implement backup strategy

---

## Quick Reference

### Key Commands

```bash
# Check all resources
kubectl get all -n analysis-agent
kubectl get agent -n analysis-agent

# View logs
kubectl logs -f -n analysis-agent -l app=webhook-service
kubectl logs -f -n analysis-agent -l app=notifier-service
kubectl logs -f -n kagent -l app.kubernetes.io/name=kagent-controller

# Restart services
kubectl rollout restart deployment/webhook-service -n analysis-agent
kubectl rollout restart deployment/notifier-service -n analysis-agent

# Delete everything
helm uninstall analysis-agent -n analysis-agent
kubectl delete namespace analysis-agent
helm uninstall kagent -n kagent
helm uninstall kagent-crds -n kagent
kubectl delete namespace kagent
```

### Important Files

- **Agent Definition**: `agents/devops-rca-agent.yaml`
- **Helm Chart**: `chart/analysis-agent/`
- **Secrets Template**: `manifests/secrets.yaml.template`
- **Test Scripts**: `tests/`

---

## Support

- **Documentation**: [README.md](../README.md)
- **Helm Guide**: [HELM_DEPLOYMENT.md](./HELM_DEPLOYMENT.md)
- **Issues**: Create an issue in the repository

---

**Last Updated**: 2025-10-12
**Version**: 0.1.0
