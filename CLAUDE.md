# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Kagent DevOps RCA System** - An AI-powered Root Cause Analysis agent for Kubernetes that automatically investigates alerts from Prometheus AlertManager, identifies root causes, and provides actionable solutions via email reports. Built on the [Kagent framework](https://kagent.dev/).

## System Architecture

### Alert-Driven Investigation Flow
```
AlertManager → Webhook Service → Kagent AI Agent → RCA Analysis → Report → Email
```

### Core Components

1. **Webhook Service** (`services/webhook/`): Lightweight FastAPI receiver that accepts AlertManager webhooks and triggers the Kagent agent
2. **Kagent AI Agent** (`agents/devops-rca-agent.yaml`): Intelligent investigator that uses custom Python tools to analyze incidents
3. **Notifier Service** (`services/notifier/`): FastAPI service that sends HTML-formatted email reports via Gmail SMTP
4. **Custom Tools** (`tools/`): Python modules that extend the agent's capabilities (memory, Helm, logs, GitHub)
5. **Agent Memory** (PersistentVolume): Markdown-based knowledge base at `/agent-memory/` for discovered tools, known issues, and incident reports

### Design Principles

- **Alert-Driven**: No scheduled scanning; agent only investigates when alerts fire
- **Stateless Services**: Webhook and notifier services are thin, agent does all intelligence
- **Persistent Memory**: Agent maintains knowledge base across investigations to learn patterns
- **Tool-Based Architecture**: Agent uses modular Python tools (memory_manager, helm_analyzer, log_analyzer, github_api)

## Building and Deploying

### Prerequisites Setup
```bash
# Install K3s locally for development
curl -sfL https://get.k3s.io | sh -

# Install Prometheus + AlertManager
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

# Install Kagent operator (see docs/INSTALLATION.md#step-1-install-kagent-operator)
```

### Building Docker Images

**For Maintainers Only**: See **[docs/DOCKER_BUILD.md](docs/DOCKER_BUILD.md)** for complete build and publish instructions.

**For End Users**: Pre-built images are available at `ghcr.io/your-org/analysis-agent-*:0.1.0`. Use Helm chart defaults - no build required!

**Quick Reference** (Maintainers):
```bash
# Build and publish to GHCR (see DOCKER_BUILD.md for details)
docker build -t ghcr.io/your-org/analysis-agent-webhook:0.1.0 services/webhook
docker push ghcr.io/your-org/analysis-agent-webhook:0.1.0

docker build -t ghcr.io/your-org/analysis-agent-notifier:0.1.0 services/notifier
docker push ghcr.io/your-org/analysis-agent-notifier:0.1.0
```

### Deployment
```bash
# Create namespace and base resources
kubectl create namespace analysis-agent
kubectl apply -f manifests/namespace.yaml
kubectl apply -f manifests/rbac.yaml
kubectl apply -f manifests/storage.yaml

# Initialize agent memory with templates
./scripts/init-memory.sh

# Configure secrets
cp manifests/secrets.yaml.template manifests/secrets.yaml
# Edit manifests/secrets.yaml with your Gmail credentials
kubectl apply -f manifests/secrets.yaml

# Deploy services
kubectl apply -f manifests/deployments/

# Configure AlertManager to send webhooks
kubectl apply -f manifests/alertmanager-config.yaml -n monitoring
kubectl rollout restart statefulset/alertmanager-prometheus-kube-prometheus-alertmanager -n monitoring
```

## Development Commands

### Testing Services Locally
```bash
# Port-forward webhook service
kubectl port-forward svc/webhook-service 8080:8080 -n analysis-agent

# Send test alert
curl -X POST http://localhost:8080/api/v1/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": "alert", "severity": "critical"}'

# Port-forward notifier service
kubectl port-forward svc/notifier-service 8081:8080 -n analysis-agent

# Test email
curl -X POST http://localhost:8081/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '["your-email@example.com"]'
```

### Testing Custom Tools Independently
```bash
cd tools

# Test memory manager
python3 -c "
from memory_manager import MemoryManager
m = MemoryManager('/tmp/test-memory')
print(m.list_files())
"

# Test helm analyzer
python3 -c "
from helm_analyzer import HelmAnalyzer
h = HelmAnalyzer()
releases = h.list_releases()
print(releases)
"

# Test log analyzer
python3 -c "
from log_analyzer import LogAnalyzer
la = LogAnalyzer()
logs = 'ERROR: Connection refused\nINFO: Starting app'
errors = la.extract_errors(logs)
print(errors)
"
```

### Creating Test Failures
```bash
# Verify system is running
./tests/verify-agent.sh

# Create a test failure scenario (interactive)
./tests/create-test-failure.sh

# Or send a test alert directly
./tests/send-test-alert.sh
```

### Monitoring Logs
```bash
# Webhook service logs
kubectl logs -f -n analysis-agent -l app=webhook-service

# Notifier service logs
kubectl logs -f -n analysis-agent -l app=notifier-service

# Kagent operator logs (to see agent activity)
kubectl logs -f -n kagent-system -l app=kagent-operator

# View all pods in namespace
kubectl get pods -n analysis-agent

# Access agent memory
kubectl exec -it <agent-pod> -n analysis-agent -- ls -la /agent-memory/
kubectl exec -it <agent-pod> -n analysis-agent -- cat /agent-memory/known-issues.md
```

## Important Architecture Details

### Kagent Agent Tool Interface

The agent uses custom Python tools defined in `tools/`. Each tool must implement a specific function signature:

```python
def tool_name(action: str, **kwargs) -> str:
    """
    Actions:
    - action1: Description (requires: param1, param2)
    - action2: Description (optional: param3)
    """
```

**Example tool invocation by agent**:
- `memory_tool(action="read", filename="known-issues.md")`
- `helm_tool(action="get_values", release="my-app", namespace="production")`
- `log_tool(action="extract_errors", logs="<log content>")`

### Agent Memory Structure

The agent maintains a knowledge base in `/agent-memory/`:

```
/agent-memory/
├── discovered-tools.md    # Auto-discovered services/tools in cluster
├── known-issues.md        # Previously solved incident patterns
├── github-repos.md        # Linked repositories and workflows
├── helm-charts.md         # Deployed Helm releases
├── namespace-map.md       # Namespace topology
└── reports/               # Saved incident reports
    └── 2025-10-11-incident-001.md
```

**Critical**: The agent reads this memory at the start of each investigation to leverage past learnings.

### AlertManager Webhook Format

The webhook service expects AlertManager v4 webhook format:

```json
{
  "version": "4",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "KubePodCrashLooping",
        "namespace": "production",
        "pod": "my-pod",
        "severity": "critical"
      },
      "annotations": {
        "description": "Pod is crash looping",
        "summary": "Pod crash loop detected"
      },
      "startsAt": "2025-10-11T14:30:00.000Z",
      "fingerprint": "abc123"
    }
  ]
}
```

### Email Notification Routing

Severity-based recipient routing in `services/notifier/main.py`:

- **critical** → `RECIPIENTS_CRITICAL` (oncall team)
- **warning** → `RECIPIENTS_WARNING` (devops team)
- **info** → `RECIPIENTS_INFO` (devops-alerts)

Recipients configured via `manifests/secrets.yaml` (comma-separated).

## Phase-Based Development

The project follows a 6-phase development plan (see `development/development_plan.md`):

- **Phase 0**: Project setup, prerequisites, K3s
- **Phase 1**: Foundation (namespace, RBAC, storage, basic agent)
- **Phase 2**: Webhook service + AlertManager integration ✅ **Complete**
- **Phase 3**: Agent intelligence + custom tools
- **Phase 4**: Notifier service + email
- **Phase 5**: Testing & refinement
- **Phase 6**: Future enhancements (MCP servers)

**Current Status**: MVP Development - Phase 2 Complete (Documentation Simplification)

## Recent Updates (Phase 2 - October 2025)

### Documentation Simplification
- **Removed Docker build requirement** for end users
- **Pre-built images** now available at `ghcr.io/your-org/analysis-agent-*`
- Installation reduced from 7 steps to 6 steps (~15-20 minutes saved)

### New Documentation
- **[docs/DOCKER_BUILD.md](docs/DOCKER_BUILD.md)** - Maintainer guide for building/publishing images
- **[docs/IMAGE_ARCHITECTURE.md](docs/IMAGE_ARCHITECTURE.md)** - Separation of concerns for Docker images
- **[docs/ROADMAP.md](docs/ROADMAP.md)** - Future features roadmap (v0.2.0 to v0.6.0)

### Development Folder Reorganization
All planning documents moved to `development/` directory:
- `development/development_plan.md` - Overall 6-phase implementation roadmap
- `development/development_phase2.md` - Phase 2 detailed summary (31KB reference)
- `development/continue_prompt.md` - Concise prompt for continuing development in new sessions

## Key Implementation Notes

### When Adding New Custom Tools

1. Create Python module in `tools/` with function signature: `def toolname(action: str, **kwargs) -> str`
2. Add tool definition to `agents/devops-rca-agent.yaml`:
   ```yaml
   tools:
     - name: my_tool
       type: python
       module: tools.my_module
       function: my_tool
   ```
3. Test tool independently before deploying agent
4. Update agent instructions to explain when/how to use the tool

### When Modifying Agent Instructions

The agent instructions in `agents/devops-rca-agent.yaml` follow this structure:

1. **Understand the Alert** - Parse alert details
2. **Check Memory First** - Read knowledge base
3. **Gather Evidence** - Use all tools (kubectl, logs, Helm, GitHub, Prometheus)
4. **Build Timeline** - Chronological event ordering
5. **Root Cause Analysis** - Identify primary + contributing factors
6. **Generate Solutions** - Step-by-step remediation with exact commands
7. **Create Report** - Markdown format with specific sections
8. **Update Memory** - Save learnings to knowledge base
9. **Send Notification** - Call notifier service

**Important**: Agent must provide EXACT commands, not placeholders. Example: `kubectl rollout undo deployment/payment-service -n production`

### RBAC Permissions

The agent requires cluster-wide READ permissions (defined in `manifests/rbac.yaml`):

```yaml
rules:
- apiGroups: [""]
  resources: ["pods", "services", "events", "configmaps", "secrets", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list"]
```

**No write permissions** - agent is read-only for safety.

### Exit Code Analysis

The `log_analyzer.py` tool includes exit code interpretation:

- **0**: Success
- **1**: General error
- **137**: OOMKilled (memory limit exceeded)
- **143**: SIGTERM (graceful shutdown)

Agent uses this to determine if crashes are due to OOM, application errors, or external termination.

## Testing Strategy

### Test Scenarios

Located in `tests/test-alerts/` and `examples/`:

1. **CrashLoop**: Pod that exits with error (database connection failure simulation)
2. **OOMKilled**: Memory-intensive pod exceeding limits
3. **ImagePullBackOff**: Invalid image tag

### Running E2E Tests

```bash
# 1. Verify all components running
./tests/verify-agent.sh

# 2. Deploy test failure
kubectl apply -f examples/crashloop-scenario/bad-deployment.yaml

# 3. Wait 2-3 minutes for AlertManager to fire

# 4. Monitor webhook logs
kubectl logs -f -n analysis-agent -l app=webhook-service

# 5. Check email inbox for incident report

# 6. Verify agent memory updated
kubectl exec -it <agent-pod> -n analysis-agent -- ls /agent-memory/reports/
```

## Troubleshooting

### Webhook Not Receiving Alerts
```bash
# Check AlertManager config
kubectl get configmap -n monitoring alertmanager-config -o yaml

# Test webhook connectivity from monitoring namespace
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -n monitoring -- \
  curl -X POST http://webhook-service.analysis-agent.svc.cluster.local:8080/api/v1/webhook/test \
  -H "Content-Type: application/json" -d '{"test": "connectivity"}'
```

### Agent Not Investigating
```bash
# Check Kagent operator
kubectl get pods -n kagent-system

# Check agent resource
kubectl get agents -n analysis-agent
kubectl describe agent devops-rca-agent -n analysis-agent

# Check RBAC permissions
kubectl auth can-i list pods --as=system:serviceaccount:analysis-agent:agent-sa --all-namespaces
```

### Emails Not Sending
```bash
# Check SMTP credentials
kubectl get secret gmail-credentials -n analysis-agent -o yaml

# Test notifier independently
kubectl port-forward svc/notifier-service 8081:8080 -n analysis-agent
curl -X POST http://localhost:8081/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '["your-email@example.com"]'

# Check notifier logs for SMTP errors
kubectl logs -n analysis-agent -l app=notifier-service
```

### Memory Not Persisting
```bash
# Check PVC status
kubectl get pvc agent-memory-pvc -n analysis-agent
kubectl describe pvc agent-memory-pvc -n analysis-agent

# Check storage class
kubectl get storageclass

# Verify agent pod has volume mounted
kubectl describe pod <agent-pod> -n analysis-agent | grep -A5 "Volumes:"
```

## Future Enhancements (Phase 6)

### MCP Server Integration (Planned)

Future versions will integrate MCP (Model Context Protocol) servers for:

- **GitHub Actions MCP**: Real-time workflow monitoring, trigger reruns
- **ArgoCD MCP**: GitOps sync/diff operations, rollbacks
- **Slack MCP**: Interactive incident notifications

MCP tools will replace direct API calls (GitHub API, ArgoCD API) for richer functionality.

### RAG System (Planned)

Store incident reports in vector database for:
- Semantic search across historical incidents
- Pattern detection and trend analysis
- Automated solution recommendations based on similar past issues

## Gmail Configuration

**Required**: Gmail app password (not account password)

Steps:
1. Enable 2FA on Gmail account
2. Generate app password: https://myaccount.google.com/apppasswords
3. Store in `manifests/secrets.yaml` under `smtp-password`

## Quick Reference

```bash
# Deploy everything
kubectl apply -f manifests/

# Check system status
kubectl get all -n analysis-agent

# View recent reports
kubectl exec -it <agent-pod> -n analysis-agent -- ls -lh /agent-memory/reports/

# Tail all logs
kubectl logs -f -n analysis-agent --all-containers=true

# Delete everything
kubectl delete namespace analysis-agent
```
