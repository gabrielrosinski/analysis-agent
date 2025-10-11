# Kagent DevOps RCA System

> AI-powered Root Cause Analysis agent for Kubernetes using Kagent framework

## Overview

This project implements an intelligent AI agent that automatically investigates Kubernetes alerts, identifies root causes, and provides actionable solutions. Built on the [Kagent](https://kagent.dev/) framework, it combines Kubernetes-native operations with AI reasoning.

### Alert-Agnostic Design

**The system can analyze ANY alert that AlertManager sends.** It's not limited to specific alert types because:

1. **Generic Investigation Process**: The agent doesn't have hardcoded alert handlers. Instead, it:
   - Reads alert labels/annotations (present in ANY alert)
   - Uses generic tools (kubectl, logs, Prometheus, Helm)
   - Applies AI reasoning to correlate data
   - Determines root cause based on evidence

2. **Memory-Based Learning**: The `known-issues.md` contains common patterns, but the agent can:
   - Analyze novel/unknown alert types
   - Learn from them
   - Add new patterns to memory over time

3. **Flexible Tool Set**: The custom tools (log analyzer, Helm analyzer, etc.) work on:
   - Pod logs (regardless of alert type)
   - Kubernetes events (any resource)
   - Helm configurations (any chart)
   - Metrics (any query)

Whether it's a pod crash, database issue, certificate expiration, network policy violation, or custom application alert - the agent investigates using the same intelligent, tool-based approach.

## How It Works

```
Prometheus Alert → Webhook Service → Kagent AI Agent → Investigation → Report → Email
```

1. **Alert Reception**: AlertManager sends webhooks when issues are detected
2. **AI Investigation**: Kagent agent investigates using Kubernetes, Prometheus, Helm, and GitHub APIs
3. **Root Cause Analysis**: Agent analyzes logs, metrics, configs, and recent changes
4. **Report Generation**: Comprehensive markdown report with timeline and solutions
5. **Notification**: HTML email sent to DevOps team

## Features

### 🔍 Core Capabilities
- **Alert-Agnostic Analysis**: Investigates ANY AlertManager alert using generic investigation patterns
- **AI-Powered Reasoning**: Claude-powered agent correlates logs, events, metrics, and configuration changes
- **Multi-Tool Investigation**: Kubernetes API, Prometheus queries, Helm analysis, log parsing, GitHub integration
- **Root Cause Determination**: Identifies primary causes and contributing factors with supporting evidence

### 🧠 Intelligence & Learning
- **Persistent Memory System**: Markdown-based knowledge base (`/agent-memory/`) that grows over time
- **Pattern Recognition**: Learns from past incidents and applies solutions to similar problems
- **Contextual Analysis**: Reads alert labels/annotations and correlates with system state
- **Exit Code Intelligence**: Interprets container exit codes (137=OOMKilled, 143=SIGTERM, etc.)

### 📊 Reporting & Notifications
- **Comprehensive Reports**: Detailed markdown reports with executive summary, timeline, root cause, and solutions
- **Styled HTML Emails**: Professional email templates with syntax highlighting and color-coded severity
- **Severity-Based Routing**: Critical → oncall, Warning → devops, Info → alerts list
- **Actionable Solutions**: Exact kubectl/helm commands, not placeholders

### ⚙️ Operational Excellence
- **Zero False Positives**: Only triggers on actual AlertManager alerts (no polling/scanning)
- **Alert Deduplication**: 5-minute cache prevents duplicate investigations
- **High Availability**: Webhook service runs with 2 replicas
- **GitOps Ready**: All configurations managed via Kubernetes manifests

## Architecture

### Components

1. **Webhook Service** (FastAPI)
   - Receives AlertManager webhooks
   - Triggers Kagent agent

2. **Kagent AI Agent**
   - Performs intelligent investigation
   - Uses custom Python tools
   - Maintains persistent memory
   - Generates reports

3. **Notifier Service** (FastAPI)
   - Sends email notifications
   - Converts markdown to styled HTML

4. **Custom Tools**
   - Memory Manager: Read/write knowledge base
   - Helm Analyzer: Chart and release analysis
   - Log Analyzer: Pattern matching and error extraction
   - GitHub API: Commit and workflow history (optional)

## Quick Start

### Prerequisites

**Required:**
- **Kubernetes**: v1.28+ (K3s 1.28+ recommended for local development)
- **Kagent Operator**: Latest version from [kagent.dev](https://kagent.dev/)
- **Prometheus + AlertManager**: v2.45+ (via kube-prometheus-stack Helm chart)
- **Helm**: v3.12+
- **kubectl**: v1.28+
- **Docker or Podman**: v24.0+ (for building images)
- **Gmail Account**: With app password enabled (2FA required)

**Optional:**
- **GitHub Personal Access Token**: For commit/workflow correlation (read-only scope)
- **Grafana**: v10.0+ for visualization (included in kube-prometheus-stack)

**System Resources:**
- Minimum: 4 vCPU, 8GB RAM, 20GB storage
- Recommended: 8 vCPU, 16GB RAM, 50GB storage

### Installation

```bash
# 1. Clone repository
git clone <your-repo>
cd analysis-agent

# 2. Install Kagent operator (see docs/KAGENT_INSTALLATION.md)

# 3. Create namespace and resources
kubectl create namespace analysis-agent
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/rbac.yaml
kubectl apply -f manifests/storage.yaml

# 4. Initialize agent memory
./scripts/init-memory.sh

# 5. Configure Gmail credentials
cp manifests/secrets.yaml.template manifests/secrets.yaml
# Edit manifests/secrets.yaml with your credentials
kubectl apply -f manifests/secrets.yaml

# 6. Build and deploy services
cd services/webhook
docker build -t your-dockerhub/analysis-agent-webhook:v0.1.0 .
docker push your-dockerhub/analysis-agent-webhook:v0.1.0

cd ../notifier
docker build -t your-dockerhub/analysis-agent-notifier:v0.1.0 .
docker push your-dockerhub/analysis-agent-notifier:v0.1.0

# 7. Deploy all components
kubectl apply -f manifests/deployments/

# 8. Configure AlertManager
kubectl apply -f manifests/alertmanager-config.yaml -n monitoring
kubectl rollout restart statefulset/alertmanager-prometheus-kube-prometheus-alertmanager -n monitoring

# 9. Verify installation
./tests/verify-agent.sh
```

## Testing

### Send Test Alert

```bash
# Create a test failure scenario
./tests/create-test-failure.sh

# Or send test alert directly
./tests/send-test-alert.sh
```

### Monitor Logs

```bash
# Webhook service
kubectl logs -f -n analysis-agent -l app=webhook-service

# Notifier service
kubectl logs -f -n analysis-agent -l app=notifier-service

# Agent logs (check Kagent operator logs)
kubectl logs -f -n kagent-system -l app=kagent-operator
```

## Configuration

### Alert Routing

Configure email recipients in `manifests/secrets.yaml`:

```yaml
recipients-critical: "oncall@example.com,sre@example.com"
recipients-warning: "devops@example.com"
recipients-info: "devops-alerts@example.com"
```

### Agent Memory

The agent maintains a knowledge base in `/agent-memory/`:

- `discovered-tools.md` - Known services and tools
- `known-issues.md` - Previously solved issues
- `github-repos.md` - Linked repositories
- `helm-charts.md` - Deployed charts
- `reports/` - Incident reports

## Example Report

When an issue occurs, you'll receive an email like this:

```
Subject: [CRITICAL] Pod CrashLoopBackOff: payment-service

# Incident Report: KubePodCrashLooping

## Executive Summary
Payment service pod crashed due to database connection failure caused by
incorrect connection string after recent deployment.

## Timeline
14:15 - Deployment updated (commit abc123)
14:16 - Pod started
14:17 - Database connection failed
14:18 - Pod entered CrashLoopBackOff
14:20 - Alert fired

## Root Cause
Primary: Database connection string missing DB_PASSWORD environment variable

## Solutions

### Immediate Fix
1. Rollback deployment:
   kubectl rollout undo deployment/payment-service -n production

2. Verify:
   kubectl rollout status deployment/payment-service -n production

### Root Fix
1. Add DB_PASSWORD to ConfigMap
2. Update deployment to reference secret
3. Redeploy with correct configuration

## Prevention
- Add secret validation in CI/CD pipeline
- Implement smoke tests before production
```

## Documentation

**Core Documentation:**
- [Development Plan](development_plan.md) - Detailed 6-phase implementation roadmap
- [CLAUDE.md](CLAUDE.md) - Architecture details and development guide

**Service Documentation:**
- [Webhook Service](services/webhook/README.md) - AlertManager webhook receiver
- [Notifier Service](services/notifier/README.md) - Email notification service

**Testing Documentation:**
- [Testing Guide](tests/README.md) - Comprehensive testing scenarios and scripts
- [Verification Script](tests/verify-agent.sh) - System health check
- [Test Failure Creator](tests/create-test-failure.sh) - Deploy failure scenarios
- [Send Test Alert](tests/send-test-alert.sh) - Manual alert injection

**Example Scenarios:**
- [CrashLoop Scenario](examples/crashloop-scenario/README.md) - Database connection failure
- [OOMKilled Scenario](examples/oom-scenario/README.md) - Memory exhaustion
- [ImagePull Scenario](examples/imagepull-scenario/README.md) - Invalid image tag

## Development Plan

See [development_plan.md](development_plan.md) for detailed implementation phases.

## Project Structure

```
analysis-agent/
├── README.md                      # This file
├── development_plan.md            # Detailed implementation plan
├── agents/                        # Kagent agent definitions
│   └── devops-rca-agent.yaml
├── services/                      # Python microservices
│   ├── webhook/                   # AlertManager webhook receiver
│   └── notifier/                  # Email notification service
├── tools/                         # Custom Python tools for agent
│   ├── memory_manager.py
│   ├── helm_analyzer.py
│   ├── log_analyzer.py
│   └── github_api.py
├── manifests/                     # Kubernetes manifests
│   ├── namespace.yaml
│   ├── rbac.yaml
│   ├── storage.yaml
│   └── deployments/
├── memory-templates/              # Agent memory templates
├── docs/                          # Documentation
├── tests/                         # Test scenarios and scripts
└── examples/                      # Example failure scenarios
```

## Common Alert Examples (MVP)

The system handles **any alert type**, but these examples demonstrate typical scenarios:

- **Pod Issues**: CrashLoopBackOff, ImagePullBackOff, Pending
- **Resource Issues**: OOMKilled, CPU throttling
- **Infrastructure**: Node problems, storage issues
- **Application**: Health check failures, connection errors
- **Security**: Certificate expiration, RBAC violations
- **Storage**: PVC binding failures, volume mount issues
- **Networking**: DNS failures, ingress misconfigurations
- **Custom Alerts**: Any application-specific alerts from your services

The agent's generic investigation approach works for all AlertManager alerts, not just these examples.

## Future Enhancements

- **MCP Integration**: GitHub Actions, ArgoCD, Slack MCP servers
- **Auto-Remediation**: Automated fixes with approval workflow
- **Multi-Cluster**: Support for multiple Kubernetes clusters
- **RAG System**: Vector database for historical incident search
- **Predictive Analysis**: Proactive alerting based on patterns

## Contributing

This is a learning project focused on Kagent development. Contributions welcome!

## Support

For issues and questions:
- Check [documentation](docs/)
- Review [development plan](development_plan.md)
- Create an issue in the repository

## License

[Your chosen license]

## Quick Reference

### Common Commands

```bash
# Deploy everything
kubectl apply -f manifests/

# Check system status
kubectl get all -n analysis-agent

# View recent reports
AGENT_POD=$(kubectl get pods -n analysis-agent -l component=agent -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n analysis-agent $AGENT_POD -- ls -lh /agent-memory/reports/

# Tail all logs
kubectl logs -f -n analysis-agent --all-containers=true

# Port forward services
kubectl port-forward -n analysis-agent svc/webhook-service 8080:8080
kubectl port-forward -n analysis-agent svc/notifier-service 8081:8080

# Test webhook
curl -X POST http://localhost:8080/api/v1/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "alert"}'

# Test notifier
curl -X POST http://localhost:8081/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '["your-email@example.com"]'

# Delete everything
kubectl delete namespace analysis-agent
```

### Troubleshooting

**Webhook not receiving alerts:**
```bash
# Check AlertManager config
kubectl get configmap -n monitoring alertmanager-config -o yaml

# Test connectivity from monitoring namespace
kubectl run test -n monitoring --rm -i --restart=Never --image=curlimages/curl -- \
  curl -v http://webhook-service.analysis-agent.svc.cluster.local:8080/health
```

**Agent not investigating:**
```bash
# Check Kagent operator
kubectl get pods -n kagent-system

# Check agent resource
kubectl get agent devops-rca-agent -n analysis-agent

# Verify RBAC permissions
kubectl auth can-i list pods --as=system:serviceaccount:analysis-agent:agent-sa --all-namespaces
```

**Emails not sending:**
```bash
# Check Gmail credentials
kubectl get secret gmail-credentials -n analysis-agent -o yaml

# Test notifier directly
kubectl port-forward -n analysis-agent svc/notifier-service 8080:8080
curl -X POST http://localhost:8080/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '["your-email@example.com"]'
```

## Acknowledgments

- Built with [Kagent](https://kagent.dev/)
- Prometheus & AlertManager for monitoring
- FastAPI for microservices
- The Kubernetes community

---

**Status**: MVP Development Phase

**Current Version**: 0.1.0

**Last Updated**: 2025-10-11
