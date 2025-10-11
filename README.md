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

- **Alert-Driven**: Automatically triggered by Prometheus AlertManager
- **Intelligent Analysis**: Uses AI to correlate logs, events, metrics, and configuration changes
- **Multiple Tools**: Kubernetes API, Prometheus, Helm, GitHub API, log analysis
- **Persistent Memory**: Maintains knowledge base of discovered tools and known issues
- **Comprehensive Reports**: Detailed incident reports with root cause and step-by-step solutions
- **Email Notifications**: Styled HTML emails with severity-based routing

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

- Kubernetes 1.28+ (K3s for local development)
- Prometheus + AlertManager configured
- Kagent operator installed
- Helm 3.x
- Docker / Podman
- Gmail account with app password (for notifications)

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

Detailed documentation available in `/docs`:

- [Prerequisites](docs/PREREQUISITES.md) - Required tools and setup
- [Kagent Installation](docs/KAGENT_INSTALLATION.md) - Install Kagent operator
- [GitHub API Setup](docs/GITHUB_API_SETUP.md) - Configure GitHub integration
- [Gmail Setup](docs/GMAIL_SETUP.md) - Configure email notifications
- [Testing Strategy](docs/TESTING_STRATEGY.md) - Testing approach
- [Future Enhancements](docs/FUTURE_MCP.md) - MCP integration plans

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

## Acknowledgments

- Built with [Kagent](https://kagent.dev/)
- Prometheus & AlertManager for monitoring
- FastAPI for microservices
- The Kubernetes community

---

**Status**: MVP Development Phase

**Current Version**: 0.1.0

**Last Updated**: 2025-10-11
