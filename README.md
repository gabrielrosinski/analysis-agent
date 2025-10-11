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

### Core Capabilities
- 🚨 **Alert-Driven Investigation**: Automatically triggered by Prometheus AlertManager webhooks
- 🧠 **AI-Powered Analysis**: Uses Kagent AI framework to correlate logs, events, metrics, and configuration changes
- 🔍 **Multi-Source Investigation**:
  - Kubernetes API (pods, events, deployments, services)
  - Container logs with intelligent pattern matching
  - Helm release history and configuration analysis
  - GitHub commit and workflow correlation (optional)
  - Prometheus metrics queries

### Intelligence & Learning
- 📚 **Persistent Memory**: Maintains markdown-based knowledge base of:
  - Discovered tools and services in cluster
  - Previously solved incidents and patterns
  - Helm releases and deployment history
  - GitHub repositories and workflows
- 🎯 **Pattern Recognition**: Identifies common errors (connection failures, OOM, authentication issues, etc.)
- 📈 **Learning System**: Each investigation updates knowledge base for future incidents

### Reporting & Notifications
- 📊 **Comprehensive Reports**:
  - Executive summary
  - Chronological timeline
  - Root cause analysis with evidence
  - Immediate fix (stop the bleeding)
  - Root fix (permanent solution)
  - Prevention recommendations
- 📧 **Styled HTML Emails**:
  - Professional design with syntax-highlighted code blocks
  - Severity-based routing (critical/warning/info)
  - Color-coded sections for readability

### Operational Excellence
- ⚡ **Alert-Agnostic**: Handles ANY AlertManager alert (not just predefined types)
- 🔒 **Read-Only**: Agent has no write permissions (safe by design)
- 📝 **Audit Trail**: All investigations saved to persistent storage
- 🔄 **High Availability**: Services designed for multiple replicas

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

#### Required
- **Kubernetes** 1.28+ (tested with K3s 1.28, AWS EKS 1.28+)
- **kubectl** 1.28+ matching your cluster version
- **Helm** 3.x (tested with 3.12+)
- **Docker** or Podman for building images
- **Kagent Operator** (installation guide below)
- **Prometheus + AlertManager** configured and running
  - AlertManager v0.25+ with webhook support
  - Prometheus with pod monitoring enabled
- **Gmail Account** with app password for email notifications

#### Optional
- **GitHub Personal Access Token** - For commit/workflow correlation (read-only scope)
- **Private Container Registry** - If not using Docker Hub

#### System Resources (Minimum)
- **Agent**: 512Mi RAM, 250m CPU (requested) / 1Gi RAM, 500m CPU (limit)
- **Webhook Service**: 128Mi RAM, 100m CPU per replica (2 replicas recommended)
- **Notifier Service**: 128Mi RAM, 100m CPU per replica (2 replicas recommended)
- **Storage**: 5GB PersistentVolume for agent memory

#### Development Tools (Optional)
- **Python** 3.11+ for local testing of custom tools
- **Git** for version control

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

Edit `manifests/secrets.yaml` to configure email recipients:

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

## Quick Reference

### Common Commands

```bash
# Verify system health
./tests/verify-agent.sh

# Send test alert
./tests/send-test-alert.sh

# Deploy test failure scenario
./tests/create-test-failure.sh

# Monitor webhook service
kubectl logs -f -n analysis-agent -l app=webhook-service

# Monitor notifier service
kubectl logs -f -n analysis-agent -l app=notifier-service

# Monitor agent activity
kubectl logs -f -n kagent-system -l app=kagent-operator

# View saved reports
kubectl exec -n analysis-agent <agent-pod> -- ls -la /agent-memory/reports/

# Read latest report
kubectl exec -n analysis-agent <agent-pod> -- cat /agent-memory/reports/<report-file>

# Check Gmail credentials
kubectl get secret gmail-credentials -n analysis-agent

# Check email recipients configuration
kubectl get secret email-recipients -n analysis-agent

# Port-forward webhook for testing
kubectl port-forward svc/webhook-service 8080:8080 -n analysis-agent

# Port-forward notifier for testing
kubectl port-forward svc/notifier-service 8081:8080 -n analysis-agent

# Test email notification
curl -X POST http://localhost:8081/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '{"recipients": ["your-email@example.com"]}'
```

### Troubleshooting Quick Links

- **Alert not firing?** → Check Prometheus targets and AlertManager configuration
- **Webhook not receiving alerts?** → Verify AlertManager webhook config and network connectivity
- **Agent not investigating?** → Check Kagent operator logs and agent resource status
- **No email sent?** → Test SMTP with notifier service test endpoint
- **Full troubleshooting guide:** [tests/README.md](tests/README.md#troubleshooting-tests)

### Service Endpoints

| Service | Internal URL | Purpose |
|---------|-------------|---------|
| Webhook | `http://webhook-service.analysis-agent.svc.cluster.local:8080` | AlertManager webhook receiver |
| Notifier | `http://notifier-service.analysis-agent.svc.cluster.local:8080` | Email notification service |
| Webhook Health | `http://webhook-service.analysis-agent.svc.cluster.local:8080/health` | Health check |
| Notifier Health | `http://notifier-service.analysis-agent.svc.cluster.local:8080/health` | Health check |

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

Detailed guides available:

- **[Testing Guide](tests/README.md)** - Comprehensive testing strategy, test scripts, and troubleshooting
- **[Webhook Service](services/webhook/README.md)** - AlertManager integration and configuration
- **[Notifier Service](services/notifier/README.md)** - Email notification setup and Gmail configuration
- **[Custom Tools](tools/README.md)** - Tool development guide and API reference
- **[Development Plan](development_plan.md)** - Implementation phases and roadmap
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for working with this codebase

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

## Acknowledgments

- Built with [Kagent](https://kagent.dev/)
- Prometheus & AlertManager for monitoring
- FastAPI for microservices
- The Kubernetes community

---

**Status**: MVP Development Phase

**Current Version**: 0.1.0

**Last Updated**: 2025-10-11
