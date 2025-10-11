# Kagent DevOps RCA System - Development Plan

> **Project Goal**: Build an AI-powered Root Cause Analysis agent for Kubernetes using Kagent framework that automatically investigates alerts, identifies root causes, and provides actionable solutions.

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Phase 0: Project Setup](#phase-0-project-setup--prerequisites)
- [Phase 1: Foundation & Storage](#phase-1-foundation--storage)
- [Phase 2: Webhook Service](#phase-2-webhook-service)
- [Phase 3: Agent Intelligence & Tools](#phase-3-agent-intelligence--tools)
- [Phase 4: Notifier Service](#phase-4-notifier-service)
- [Phase 5: Testing & Refinement](#phase-5-testing--refinement)
- [Phase 6: Future Enhancements](#phase-6-future-enhancements)

---

## Architecture Overview

### System Flow
```
┌─────────────┐
│ Prometheus  │
│ AlertManager│
└──────┬──────┘
       │ Webhook
       ↓
┌─────────────────┐
│ Webhook Service │ (Lightweight receiver)
└────────┬────────┘
         │ Trigger
         ↓
┌─────────────────────────────────────────┐
│         Kagent AI Agent                  │
│  ┌─────────────────────────────────┐   │
│  │ Investigation & Analysis        │   │
│  │  - Kubernetes inspection        │   │
│  │  - Prometheus queries           │   │
│  │  - GitHub API calls             │   │
│  │  - Helm chart analysis          │   │
│  │  - Log correlation              │   │
│  │  - Memory read/write            │   │
│  └─────────────────────────────────┘   │
│                                          │
│  ┌─────────────────────────────────┐   │
│  │ Root Cause Analysis             │   │
│  │  - Timeline reconstruction      │   │
│  │  - Pattern matching             │   │
│  │  - Diff analysis                │   │
│  │  - Solution generation          │   │
│  └─────────────────────────────────┘   │
└────────┬────────────────────────────────┘
         │ Report
         ↓
┌─────────────────┐
│ Notifier Service│ (Email sender)
└────────┬────────┘
         │
         ↓
    DevOps Team
```

### Components
1. **Webhook Service**: FastAPI receiver for AlertManager webhooks
2. **Kagent AI Agent**: Intelligent investigator with custom tools
3. **Notifier Service**: Email reports via Gmail
4. **Persistent Memory**: Markdown files for agent knowledge base

---

## Phase 0: Project Setup & Prerequisites

**Goal**: Establish development environment and install prerequisites

### 0.1 Project Structure
Create the following directory structure:

```
analysis-agent/
├── development_plan.md          # This file
├── README.md                     # Quick start guide
├── .gitignore                    # Git ignore file
├── agents/                       # Kagent agent definitions
│   └── devops-rca-agent.yaml
├── services/                     # Python microservices
│   ├── webhook/
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   └── notifier/
│       ├── main.py
│       ├── requirements.txt
│       ├── Dockerfile
│       └── README.md
├── tools/                        # Custom Python tools for Kagent
│   ├── __init__.py
│   ├── github_api.py
│   ├── helm_analyzer.py
│   ├── log_analyzer.py
│   └── memory_manager.py
├── manifests/                    # Kubernetes manifests
│   ├── namespace.yaml
│   ├── rbac.yaml
│   ├── storage.yaml
│   ├── alertmanager-config.yaml
│   └── deployments/
│       ├── webhook-deployment.yaml
│       ├── notifier-deployment.yaml
│       └── services.yaml
├── memory-templates/             # Agent memory markdown templates
│   ├── README.md
│   ├── discovered-tools.md
│   ├── namespace-map.md
│   ├── known-issues.md
│   ├── github-repos.md
│   └── helm-charts.md
├── docs/                         # Documentation
│   ├── PREREQUISITES.md
│   ├── KAGENT_INSTALLATION.md
│   ├── GITHUB_API_SETUP.md
│   ├── GMAIL_SETUP.md
│   ├── TESTING_STRATEGY.md
│   └── FUTURE_MCP.md
├── tests/                        # Test scenarios
│   ├── test-alerts/
│   │   ├── crashloop-alert.json
│   │   ├── oom-alert.json
│   │   └── imagepull-alert.json
│   ├── create-test-failure.sh
│   └── verify-agent.sh
└── examples/                     # Example failure scenarios
    ├── crashloop-scenario/
    ├── imagepull-scenario/
    └── oom-scenario/
```

### 0.2 Prerequisites Documentation

**Files to Create**:

#### `docs/PREREQUISITES.md`
- Kubernetes 1.28+ (K3s for local development)
- Helm 3.x
- Prometheus + AlertManager configured
- Grafana (optional but recommended)
- Docker / Podman
- kubectl CLI
- Python 3.11+

#### `docs/KAGENT_INSTALLATION.md`
- How to install Kagent operator
- Verify installation
- Basic agent examples
- Troubleshooting

#### `docs/GITHUB_API_SETUP.md`
- Create fine-grained Personal Access Token
- Required permissions
- Store as Kubernetes secret

#### `docs/GMAIL_SETUP.md`
- Enable 2FA on Gmail
- Generate app password
- Store as Kubernetes secret

### 0.3 Local K3s Setup

**Create script**: `scripts/setup-k3s.sh`
```bash
#!/bin/bash
# Install K3s locally
curl -sfL https://get.k3s.io | sh -

# Install Prometheus stack
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace

# Install Kagent operator
# (Instructions in KAGENT_INSTALLATION.md)
```

### Deliverables
- [ ] Complete directory structure
- [ ] All documentation files created
- [ ] K3s installed and running
- [ ] Prometheus + AlertManager deployed
- [ ] Kagent operator installed and verified

---

## Phase 1: Foundation & Storage

**Goal**: Set up Kubernetes resources and agent memory structure

### 1.1 Namespace & RBAC

**File**: `manifests/namespace.yaml`
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: analysis-agent
  labels:
    app: devops-rca
    monitoring: enabled
```

**File**: `manifests/rbac.yaml`
- ServiceAccount for webhook service
- ServiceAccount for notifier service
- ServiceAccount for Kagent agent (with cluster-wide read permissions)
- ClusterRole: Read access to all namespaces, pods, events, configmaps
- ClusterRoleBinding: Bind to agent service account

**Permissions needed**:
```yaml
rules:
- apiGroups: [""]
  resources: ["pods", "services", "events", "configmaps", "secrets", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets", "statefulsets"]
  verbs: ["get", "list"]
- apiGroups: ["batch"]
  resources: ["jobs", "cronjobs"]
  verbs: ["get", "list"]
# Add more as needed for Helm, ArgoCD CRDs
```

### 1.2 Persistent Storage

**File**: `manifests/storage.yaml`

```yaml
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: agent-memory-pvc
  namespace: analysis-agent
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: local-path  # K3s default
```

### 1.3 Memory Templates

Create initial markdown templates that the agent will read/update:

**File**: `memory-templates/discovered-tools.md`
```markdown
# Discovered Tools & Services

Last updated: [timestamp]

## CI/CD Tools
- **GitHub Actions**: Detected workflows in repositories
- **ArgoCD**: Applications and sync status

## Container Registry
- **Docker Hub**: Public images
- **GitHub Container Registry**: Private images

## Monitoring & Observability
- **Prometheus**: metrics-server.monitoring.svc
- **Grafana**: grafana.monitoring.svc
- **AlertManager**: alertmanager.monitoring.svc

## Namespaces
| Namespace | Purpose | Key Services |
|-----------|---------|--------------|
| production | Production apps | api-service, frontend |
| monitoring | Observability | prometheus, grafana |
| analysis-agent | RCA System | webhook, notifier |

## Notes
- Add new discoveries here during investigations
```

**File**: `memory-templates/known-issues.md`
```markdown
# Known Issues & Solutions

## Issue Patterns

### Pattern: ImagePullBackOff
**Symptoms**: Pod stuck in ImagePullBackOff
**Common Causes**:
1. Invalid image tag
2. Registry authentication failure
3. Registry unreachable
4. Image doesn't exist

**Investigation Steps**:
1. Check image exists: `docker manifest inspect <image>`
2. Verify pull secrets
3. Test registry connectivity
4. Check image tag in deployment

**Solutions**:
- Fix image tag in deployment/Helm values
- Update imagePullSecrets
- Use different registry

---

### Pattern: CrashLoopBackOff
**Symptoms**: Container repeatedly crashes
**Common Causes**:
1. Application error (check logs)
2. Failed health probes
3. OOMKilled (check exit code 137)
4. Missing dependencies (DB, API)

**Investigation Steps**:
1. Check container exit code
2. Review logs (current + previous)
3. Check resource limits vs usage
4. Verify dependent services

---

## Solved Incidents

[Agent will add solved incidents here over time]
```

**File**: `memory-templates/github-repos.md`
```markdown
# GitHub Repositories

## Discovered Repositories

| Service | Repository | Branch | Workflows |
|---------|------------|--------|-----------|
| payment-service | github.com/org/payment-service | main | build-deploy.yml |

## Notes
- Update this as new repos are discovered
- Add workflow names for quick reference
```

### 1.4 Initialize Storage

**Create script**: `scripts/init-memory.sh`
```bash
#!/bin/bash
# Initialize agent memory with templates

kubectl create namespace analysis-agent

# Create PVC
kubectl apply -f manifests/storage.yaml

# Wait for PVC to be bound
kubectl wait --for=condition=Bound pvc/agent-memory-pvc -n analysis-agent

# Copy templates to PVC using a temporary pod
kubectl run memory-init \
  --image=busybox \
  --restart=Never \
  -n analysis-agent \
  --overrides='
{
  "spec": {
    "volumes": [{
      "name": "memory",
      "persistentVolumeClaim": {"claimName": "agent-memory-pvc"}
    }],
    "containers": [{
      "name": "init",
      "image": "busybox",
      "command": ["sleep", "300"],
      "volumeMounts": [{
        "name": "memory",
        "mountPath": "/agent-memory"
      }]
    }]
  }
}'

# Copy templates
kubectl cp memory-templates/ analysis-agent/memory-init:/agent-memory/

# Cleanup
kubectl delete pod memory-init -n analysis-agent
```

### 1.5 Basic Kagent Agent (Hello World)

**File**: `agents/devops-rca-agent.yaml`

```yaml
apiVersion: kagent.ai/v1alpha1
kind: Agent
metadata:
  name: devops-rca-agent
  namespace: analysis-agent
spec:
  description: "DevOps Root Cause Analysis AI Agent - MVP"

  instructions: |
    You are a DevOps SRE expert. For now, just acknowledge alerts.
    In later phases, you'll perform full investigations.

    When triggered, respond with:
    - Alert received confirmation
    - Basic alert details
    - Next steps message

  tools:
    - kubernetes

  memory:
    persistentVolume:
      claimName: agent-memory-pvc
      mountPath: /agent-memory
```

### Deliverables
- [ ] Namespace created
- [ ] RBAC configured
- [ ] PVC created and bound
- [ ] Memory templates initialized in PVC
- [ ] Basic Kagent agent deployed and running
- [ ] Agent can read memory files

### Testing Phase 1
```bash
# Verify namespace
kubectl get ns analysis-agent

# Verify PVC
kubectl get pvc -n analysis-agent

# Verify agent
kubectl get agents -n analysis-agent

# Test agent (if Kagent CLI available)
kagent invoke devops-rca-agent "Hello, can you read your memory?"
```

---

## Phase 2: Webhook Service

**Goal**: Create AlertManager webhook receiver that triggers the agent

### 2.1 Webhook Service Implementation

**File**: `services/webhook/requirements.txt`
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
httpx==0.25.1
python-json-logger==2.0.7
```

**File**: `services/webhook/main.py`

```python
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import httpx
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DevOps RCA Webhook Service", version="0.1.0")

# AlertManager alert model
class Alert(BaseModel):
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str
    fingerprint: str

class AlertManagerWebhook(BaseModel):
    version: str
    groupKey: str
    status: str
    receiver: str
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    alerts: List[Alert]

# In-memory cache to prevent duplicate processing
recent_alerts = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "webhook"}

@app.post("/api/v1/webhook/alertmanager")
async def receive_alert(webhook: AlertManagerWebhook):
    """
    Receive webhook from AlertManager and trigger Kagent agent
    """
    logger.info(f"Received webhook: {webhook.groupKey}")
    logger.info(f"Status: {webhook.status}, Alerts: {len(webhook.alerts)}")

    # Process each alert
    results = []
    for alert in webhook.alerts:
        # Only process firing alerts (not resolved)
        if alert.status != "firing":
            logger.info(f"Skipping resolved alert: {alert.fingerprint}")
            continue

        # Check if we've processed this recently (simple deduplication)
        if alert.fingerprint in recent_alerts:
            logger.info(f"Duplicate alert ignored: {alert.fingerprint}")
            continue

        # Mark as processed
        recent_alerts[alert.fingerprint] = datetime.utcnow()

        # Log alert details
        logger.info(f"Processing alert: {alert.labels.get('alertname', 'unknown')}")
        logger.info(f"Severity: {alert.labels.get('severity', 'unknown')}")
        logger.info(f"Namespace: {alert.labels.get('namespace', 'unknown')}")

        # Trigger Kagent agent
        try:
            result = await trigger_agent(alert, webhook)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to trigger agent: {e}")
            results.append({"error": str(e)})

    return {
        "status": "processed",
        "alerts_received": len(webhook.alerts),
        "alerts_processed": len(results),
        "results": results
    }

async def trigger_agent(alert: Alert, webhook: AlertManagerWebhook):
    """
    Trigger Kagent agent to investigate the alert
    """
    # Build investigation prompt for the agent
    prompt = f"""
ALERT RECEIVED - INVESTIGATE AND ANALYZE

Alert Name: {alert.labels.get('alertname', 'Unknown')}
Severity: {alert.labels.get('severity', 'unknown')}
Status: {alert.status}
Started At: {alert.startsAt}

Labels:
{format_dict(alert.labels)}

Annotations:
{format_dict(alert.annotations)}

Generator URL: {alert.generatorURL}

INSTRUCTIONS:
1. Read your memory to understand the system context
2. Investigate this alert using your tools
3. Determine the root cause
4. Generate a detailed report
5. Send the report via the notifier service
6. Update your memory with findings

Begin investigation now.
"""

    # TODO: Call Kagent agent API
    # For MVP, we'll use Kagent's API or CLI
    # Example: POST to Kagent agent endpoint

    kagent_url = "http://kagent-api.analysis-agent.svc.cluster.local/api/v1/agents/devops-rca-agent/invoke"

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                kagent_url,
                json={"prompt": prompt}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to invoke Kagent agent: {e}")
        # For MVP, just log - we'll improve error handling later
        return {"status": "failed", "error": str(e)}

def format_dict(d: Dict) -> str:
    """Format dictionary for readable output"""
    return "\n".join([f"  {k}: {v}" for k, v in d.items()])

@app.post("/api/v1/webhook/test")
async def test_webhook(request: Request):
    """
    Test endpoint for manual alert submission
    """
    body = await request.json()
    logger.info(f"Test webhook received: {body}")
    return {"status": "test_received", "data": body}

@app.get("/")
async def root():
    return {
        "service": "DevOps RCA Webhook Service",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "alertmanager": "/api/v1/webhook/alertmanager",
            "test": "/api/v1/webhook/test"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 2.2 Webhook Docker Image

**File**: `services/webhook/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 webhook && chown -R webhook:webhook /app
USER webhook

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 2.3 Kubernetes Deployment

**File**: `manifests/deployments/webhook-deployment.yaml`

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: webhook-service
  namespace: analysis-agent
  labels:
    app: webhook-service
spec:
  replicas: 2  # HA for webhook receiver
  selector:
    matchLabels:
      app: webhook-service
  template:
    metadata:
      labels:
        app: webhook-service
    spec:
      serviceAccountName: webhook-sa
      containers:
      - name: webhook
        image: your-dockerhub/analysis-agent-webhook:v0.1.0  # Update after building
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: LOG_LEVEL
          value: "INFO"
        - name: KAGENT_API_URL
          value: "http://kagent-api.analysis-agent.svc.cluster.local"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: webhook-service
  namespace: analysis-agent
spec:
  selector:
    app: webhook-service
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
    name: http
  type: ClusterIP
```

### 2.4 AlertManager Configuration

**File**: `manifests/alertmanager-config.yaml`

```yaml
# This is a ConfigMap patch for AlertManager
# Apply after Prometheus stack is installed

apiVersion: v1
kind: ConfigMap
metadata:
  name: alertmanager-config-patch
  namespace: monitoring
data:
  alertmanager.yml: |
    global:
      resolve_timeout: 5m

    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 10s
      group_interval: 10s
      repeat_interval: 12h
      receiver: 'devops-rca-agent'

      # Route critical alerts immediately to RCA agent
      routes:
      - match:
          severity: critical
        receiver: 'devops-rca-agent'
        continue: true  # Also send to other receivers

      - match:
          severity: warning
        receiver: 'devops-rca-agent'
        group_wait: 30s

    receivers:
    - name: 'devops-rca-agent'
      webhook_configs:
      - url: 'http://webhook-service.analysis-agent.svc.cluster.local:8080/api/v1/webhook/alertmanager'
        send_resolved: true
        http_config:
          follow_redirects: true
```

**Apply with**:
```bash
# Patch AlertManager configuration
kubectl apply -f manifests/alertmanager-config.yaml -n monitoring

# Reload AlertManager
kubectl rollout restart statefulset/alertmanager-prometheus-kube-prometheus-alertmanager -n monitoring
```

### Deliverables
- [ ] Webhook service code complete
- [ ] Docker image built and pushed
- [ ] Webhook deployment created
- [ ] Service exposed in cluster
- [ ] AlertManager configured to send webhooks
- [ ] Test webhook with sample alert

### Testing Phase 2
```bash
# Build and push Docker image
cd services/webhook
docker build -t your-dockerhub/analysis-agent-webhook:v0.1.0 .
docker push your-dockerhub/analysis-agent-webhook:v0.1.0

# Deploy
kubectl apply -f manifests/deployments/webhook-deployment.yaml

# Check status
kubectl get pods -n analysis-agent
kubectl logs -f deployment/webhook-service -n analysis-agent

# Test with curl
kubectl port-forward svc/webhook-service 8080:8080 -n analysis-agent

# Send test alert
curl -X POST http://localhost:8080/api/v1/webhook/test \
  -H "Content-Type: application/json" \
  -d '{
    "test": "alert",
    "severity": "critical"
  }'
```

---

## Phase 3: Agent Intelligence & Tools

**Goal**: Implement custom Python tools and configure intelligent agent

### 3.1 Custom Python Tools

#### Tool 1: Memory Manager

**File**: `tools/memory_manager.py`

```python
"""
Memory Manager Tool for Kagent Agent
Allows agent to read/write to its persistent memory
"""

import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import re

class MemoryManager:
    def __init__(self, memory_path: str = "/agent-memory"):
        self.memory_path = Path(memory_path)
        if not self.memory_path.exists():
            raise Exception(f"Memory path does not exist: {memory_path}")

    def read_file(self, filename: str) -> str:
        """Read a file from agent memory"""
        file_path = self.memory_path / filename
        if not file_path.exists():
            return f"File not found: {filename}"

        with open(file_path, 'r') as f:
            return f.read()

    def write_file(self, filename: str, content: str) -> str:
        """Write or update a file in agent memory"""
        file_path = self.memory_path / filename

        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            f.write(content)

        return f"File written: {filename}"

    def append_to_file(self, filename: str, content: str) -> str:
        """Append content to an existing file"""
        file_path = self.memory_path / filename

        with open(file_path, 'a') as f:
            f.write(f"\n{content}")

        return f"Content appended to: {filename}"

    def list_files(self, pattern: str = "*") -> List[str]:
        """List files in memory matching pattern"""
        files = list(self.memory_path.glob(pattern))
        return [str(f.relative_to(self.memory_path)) for f in files]

    def search(self, query: str, case_sensitive: bool = False) -> List[dict]:
        """Search for text across all memory files"""
        results = []

        for md_file in self.memory_path.glob("**/*.md"):
            with open(md_file, 'r') as f:
                content = f.read()

                if case_sensitive:
                    matches = re.finditer(query, content)
                else:
                    matches = re.finditer(query, content, re.IGNORECASE)

                for match in matches:
                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1

                    # Get surrounding context
                    lines = content.split('\n')
                    context_start = max(0, line_num - 2)
                    context_end = min(len(lines), line_num + 2)
                    context = '\n'.join(lines[context_start:context_end])

                    results.append({
                        "file": str(md_file.relative_to(self.memory_path)),
                        "line": line_num,
                        "match": match.group(),
                        "context": context
                    })

        return results

    def add_known_issue(
        self,
        pattern_name: str,
        symptoms: str,
        root_cause: str,
        solution: str
    ) -> str:
        """Add a new pattern to known-issues.md"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        entry = f"""
---

### Pattern: {pattern_name}
**Date Added**: {timestamp}

**Symptoms**: {symptoms}

**Root Cause**: {root_cause}

**Solution**: {solution}

"""
        return self.append_to_file("known-issues.md", entry)

    def save_report(self, incident_id: str, report_content: str) -> str:
        """Save incident report"""
        reports_dir = self.memory_path / "reports"
        reports_dir.mkdir(exist_ok=True)

        filename = f"reports/{incident_id}.md"
        return self.write_file(filename, report_content)

# Kagent tool interface
def memory_tool(action: str, **kwargs) -> str:
    """
    Kagent tool interface for memory operations

    Actions:
    - read: Read file (requires: filename)
    - write: Write file (requires: filename, content)
    - append: Append to file (requires: filename, content)
    - list: List files (optional: pattern)
    - search: Search content (requires: query)
    - add_issue: Add known issue pattern
    - save_report: Save incident report
    """
    manager = MemoryManager()

    if action == "read":
        return manager.read_file(kwargs['filename'])

    elif action == "write":
        return manager.write_file(kwargs['filename'], kwargs['content'])

    elif action == "append":
        return manager.append_to_file(kwargs['filename'], kwargs['content'])

    elif action == "list":
        pattern = kwargs.get('pattern', '*')
        files = manager.list_files(pattern)
        return "\n".join(files)

    elif action == "search":
        results = manager.search(kwargs['query'])
        return str(results)

    elif action == "add_issue":
        return manager.add_known_issue(
            kwargs['pattern_name'],
            kwargs['symptoms'],
            kwargs['root_cause'],
            kwargs['solution']
        )

    elif action == "save_report":
        return manager.save_report(kwargs['incident_id'], kwargs['report_content'])

    else:
        return f"Unknown action: {action}"
```

#### Tool 2: Helm Analyzer

**File**: `tools/helm_analyzer.py`

```python
"""
Helm Analyzer Tool for Kagent Agent
Analyzes Helm releases and charts
"""

import subprocess
import json
import yaml
from typing import Dict, List, Optional

class HelmAnalyzer:
    def __init__(self):
        self.helm_bin = "helm"

    def _run_command(self, cmd: List[str]) -> str:
        """Run helm command and return output"""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            raise Exception(f"Helm command failed: {result.stderr}")

        return result.stdout

    def list_releases(self, namespace: str = None) -> List[Dict]:
        """List all Helm releases"""
        cmd = [self.helm_bin, "list", "-o", "json"]

        if namespace:
            cmd.extend(["-n", namespace])
        else:
            cmd.append("--all-namespaces")

        output = self._run_command(cmd)
        return json.loads(output) if output else []

    def get_values(self, release: str, namespace: str) -> Dict:
        """Get deployed values for a release"""
        cmd = [
            self.helm_bin, "get", "values",
            release, "-n", namespace,
            "-o", "json"
        ]

        output = self._run_command(cmd)
        return json.loads(output) if output else {}

    def get_manifest(self, release: str, namespace: str) -> str:
        """Get rendered Kubernetes manifests"""
        cmd = [
            self.helm_bin, "get", "manifest",
            release, "-n", namespace
        ]

        return self._run_command(cmd)

    def get_history(self, release: str, namespace: str) -> List[Dict]:
        """Get release history"""
        cmd = [
            self.helm_bin, "history",
            release, "-n", namespace,
            "-o", "json"
        ]

        output = self._run_command(cmd)
        return json.loads(output) if output else []

    def get_values_for_revision(
        self,
        release: str,
        namespace: str,
        revision: int
    ) -> Dict:
        """Get values for a specific revision"""
        cmd = [
            self.helm_bin, "get", "values",
            release, "-n", namespace,
            "--revision", str(revision),
            "-o", "json"
        ]

        output = self._run_command(cmd)
        return json.loads(output) if output else {}

    def compare_revisions(
        self,
        release: str,
        namespace: str,
        rev1: int,
        rev2: int
    ) -> Dict:
        """Compare values between two revisions"""
        values1 = self.get_values_for_revision(release, namespace, rev1)
        values2 = self.get_values_for_revision(release, namespace, rev2)

        changes = self._deep_diff(values1, values2)

        return {
            "release": release,
            "namespace": namespace,
            "revision_old": rev1,
            "revision_new": rev2,
            "changes": changes
        }

    def _deep_diff(self, dict1: Dict, dict2: Dict, path: str = "") -> List[Dict]:
        """Deep diff between two dictionaries"""
        changes = []

        # Check all keys in dict2 (new/changed)
        for key, value2 in dict2.items():
            current_path = f"{path}.{key}" if path else key

            if key not in dict1:
                changes.append({
                    "path": current_path,
                    "type": "added",
                    "new_value": value2
                })
            elif dict1[key] != value2:
                if isinstance(value2, dict) and isinstance(dict1[key], dict):
                    # Recursive diff for nested dicts
                    nested = self._deep_diff(dict1[key], value2, current_path)
                    changes.extend(nested)
                else:
                    changes.append({
                        "path": current_path,
                        "type": "changed",
                        "old_value": dict1[key],
                        "new_value": value2
                    })

        # Check for removed keys
        for key, value1 in dict1.items():
            if key not in dict2:
                current_path = f"{path}.{key}" if path else key
                changes.append({
                    "path": current_path,
                    "type": "removed",
                    "old_value": value1
                })

        return changes

    def get_release_info(self, release: str, namespace: str) -> Dict:
        """Get comprehensive release information"""
        releases = self.list_releases(namespace)

        for rel in releases:
            if rel['name'] == release:
                return {
                    "name": rel['name'],
                    "namespace": rel['namespace'],
                    "revision": rel['revision'],
                    "status": rel['status'],
                    "chart": rel['chart'],
                    "app_version": rel['app_version'],
                    "updated": rel['updated']
                }

        return {}

# Kagent tool interface
def helm_tool(action: str, **kwargs) -> str:
    """
    Kagent tool interface for Helm operations

    Actions:
    - list: List releases (optional: namespace)
    - get_values: Get release values (requires: release, namespace)
    - get_manifest: Get rendered manifests (requires: release, namespace)
    - get_history: Get release history (requires: release, namespace)
    - compare: Compare revisions (requires: release, namespace, rev1, rev2)
    - get_info: Get release info (requires: release, namespace)
    """
    analyzer = HelmAnalyzer()

    try:
        if action == "list":
            releases = analyzer.list_releases(kwargs.get('namespace'))
            return json.dumps(releases, indent=2)

        elif action == "get_values":
            values = analyzer.get_values(kwargs['release'], kwargs['namespace'])
            return json.dumps(values, indent=2)

        elif action == "get_manifest":
            return analyzer.get_manifest(kwargs['release'], kwargs['namespace'])

        elif action == "get_history":
            history = analyzer.get_history(kwargs['release'], kwargs['namespace'])
            return json.dumps(history, indent=2)

        elif action == "compare":
            diff = analyzer.compare_revisions(
                kwargs['release'],
                kwargs['namespace'],
                kwargs['rev1'],
                kwargs['rev2']
            )
            return json.dumps(diff, indent=2)

        elif action == "get_info":
            info = analyzer.get_release_info(kwargs['release'], kwargs['namespace'])
            return json.dumps(info, indent=2)

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        return f"Error: {str(e)}"
```

#### Tool 3: GitHub API (Optional for MVP)

**File**: `tools/github_api.py`

```python
"""
GitHub API Tool for Kagent Agent
Fetches commit history and workflow runs
"""

import httpx
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta

class GitHubAPI:
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def get_recent_commits(
        self,
        owner: str,
        repo: str,
        hours: int = 24
    ) -> List[Dict]:
        """Get commits from the last N hours"""
        since = datetime.utcnow() - timedelta(hours=hours)
        since_iso = since.isoformat() + "Z"

        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        params = {"since": since_iso, "per_page": 50}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            commits = response.json()

            return [
                {
                    "sha": c["sha"][:7],
                    "message": c["commit"]["message"].split("\n")[0],
                    "author": c["commit"]["author"]["email"],
                    "date": c["commit"]["author"]["date"],
                    "url": c["html_url"]
                }
                for c in commits
            ]

    async def get_workflow_runs(
        self,
        owner: str,
        repo: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent GitHub Actions workflow runs"""
        url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs"
        params = {"per_page": limit}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            runs = response.json()["workflow_runs"]

            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "status": r["status"],
                    "conclusion": r["conclusion"],
                    "created_at": r["created_at"],
                    "head_branch": r["head_branch"],
                    "head_sha": r["head_sha"][:7],
                    "url": r["html_url"]
                }
                for r in runs
            ]

# Kagent tool interface
async def github_tool(action: str, **kwargs) -> str:
    """
    Kagent tool interface for GitHub API

    Actions:
    - get_commits: Get recent commits (requires: owner, repo, hours)
    - get_workflows: Get workflow runs (requires: owner, repo, limit)
    """
    api = GitHubAPI()

    try:
        if action == "get_commits":
            commits = await api.get_recent_commits(
                kwargs['owner'],
                kwargs['repo'],
                kwargs.get('hours', 24)
            )
            return str(commits)

        elif action == "get_workflows":
            workflows = await api.get_workflow_runs(
                kwargs['owner'],
                kwargs['repo'],
                kwargs.get('limit', 10)
            )
            return str(workflows)

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        return f"Error: {str(e)}"
```

#### Tool 4: Log Analyzer

**File**: `tools/log_analyzer.py`

```python
"""
Log Analyzer Tool for Kagent Agent
Parses and analyzes container logs
"""

import re
from typing import List, Dict, Optional
from datetime import datetime

class LogAnalyzer:
    # Common error patterns
    ERROR_PATTERNS = [
        r"(?i)error:?\s+(.+)",
        r"(?i)exception:?\s+(.+)",
        r"(?i)fatal:?\s+(.+)",
        r"(?i)panic:?\s+(.+)",
        r"(?i)failed:?\s+(.+)",
        r"(?i)cannot\s+(.+)",
    ]

    # Exit code meanings
    EXIT_CODES = {
        0: "Success",
        1: "General error",
        2: "Misuse of shell command",
        126: "Command cannot execute",
        127: "Command not found",
        128: "Invalid exit argument",
        130: "Terminated by Ctrl+C",
        137: "Killed (SIGKILL) - likely OOMKilled",
        143: "Terminated (SIGTERM)"
    }

    def extract_errors(self, logs: str) -> List[Dict]:
        """Extract error messages from logs"""
        errors = []

        for line_num, line in enumerate(logs.split('\n'), 1):
            for pattern in self.ERROR_PATTERNS:
                match = re.search(pattern, line)
                if match:
                    errors.append({
                        "line": line_num,
                        "message": line.strip(),
                        "extracted": match.group(1) if match.lastindex else line
                    })
                    break  # Only match one pattern per line

        return errors

    def find_stack_traces(self, logs: str) -> List[str]:
        """Extract stack traces from logs"""
        traces = []
        lines = logs.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect stack trace start (common patterns)
            if re.search(r'(?i)(traceback|stack trace|at\s+\w+\.\w+)', line):
                trace = [line]
                i += 1

                # Collect following lines that look like stack frames
                while i < len(lines):
                    next_line = lines[i]
                    if re.search(r'^\s+(at|File|line|\.+)', next_line) or next_line.strip().startswith('->'):
                        trace.append(next_line)
                        i += 1
                    else:
                        break

                traces.append('\n'.join(trace))

            i += 1

        return traces

    def analyze_exit_code(self, exit_code: int) -> Dict:
        """Analyze container exit code"""
        description = self.EXIT_CODES.get(exit_code, "Unknown error")

        analysis = {
            "exit_code": exit_code,
            "description": description,
            "category": "unknown"
        }

        if exit_code == 0:
            analysis["category"] = "success"
        elif exit_code == 137:
            analysis["category"] = "oom_killed"
            analysis["recommendation"] = "Increase memory limits or investigate memory leak"
        elif exit_code == 143:
            analysis["category"] = "terminated"
            analysis["recommendation"] = "Check if pod was manually terminated or evicted"
        elif exit_code in [1, 2]:
            analysis["category"] = "application_error"
            analysis["recommendation"] = "Check application logs for error details"
        elif exit_code in [126, 127]:
            analysis["category"] = "command_error"
            analysis["recommendation"] = "Check container command and entrypoint configuration"

        return analysis

    def extract_timestamps(self, logs: str) -> List[Dict]:
        """Extract and parse timestamps from logs"""
        timestamp_patterns = [
            r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)',  # ISO 8601
            r'(\d{4}/\d{2}/\d{2}\s+\d{2}:\d{2}:\d{2})',              # 2024/10/11 14:30:00
            r'(\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2})',                # 11/Oct/2024:14:30:00
        ]

        timestamps = []

        for line_num, line in enumerate(logs.split('\n'), 1):
            for pattern in timestamp_patterns:
                match = re.search(pattern, line)
                if match:
                    timestamps.append({
                        "line": line_num,
                        "timestamp": match.group(1),
                        "log_line": line.strip()
                    })
                    break

        return timestamps

    def find_connection_errors(self, logs: str) -> List[Dict]:
        """Find database/network connection errors"""
        connection_patterns = [
            r'(?i)connection\s+(refused|timeout|reset|failed)',
            r'(?i)(cannot|failed to)\s+connect',
            r'(?i)no route to host',
            r'(?i)name or service not known',
            r'(?i)network\s+unreachable',
        ]

        errors = []

        for line_num, line in enumerate(logs.split('\n'), 1):
            for pattern in connection_patterns:
                if re.search(pattern, line):
                    errors.append({
                        "line": line_num,
                        "type": "connection_error",
                        "message": line.strip()
                    })
                    break

        return errors

    def summarize_logs(self, logs: str) -> Dict:
        """Generate comprehensive log summary"""
        return {
            "total_lines": len(logs.split('\n')),
            "errors": self.extract_errors(logs),
            "stack_traces": self.find_stack_traces(logs),
            "connection_errors": self.find_connection_errors(logs),
            "timestamps": self.extract_timestamps(logs)
        }

# Kagent tool interface
def log_tool(action: str, **kwargs) -> str:
    """
    Kagent tool interface for log analysis

    Actions:
    - extract_errors: Extract error messages (requires: logs)
    - find_traces: Find stack traces (requires: logs)
    - analyze_exit: Analyze exit code (requires: exit_code)
    - find_connections: Find connection errors (requires: logs)
    - summarize: Full log summary (requires: logs)
    """
    analyzer = LogAnalyzer()

    try:
        if action == "extract_errors":
            errors = analyzer.extract_errors(kwargs['logs'])
            return str(errors)

        elif action == "find_traces":
            traces = analyzer.find_stack_traces(kwargs['logs'])
            return '\n---\n'.join(traces)

        elif action == "analyze_exit":
            analysis = analyzer.analyze_exit_code(int(kwargs['exit_code']))
            return str(analysis)

        elif action == "find_connections":
            errors = analyzer.find_connection_errors(kwargs['logs'])
            return str(errors)

        elif action == "summarize":
            summary = analyzer.summarize_logs(kwargs['logs'])
            return str(summary)

        else:
            return f"Unknown action: {action}"

    except Exception as e:
        return f"Error: {str(e)}"
```

### 3.2 Update Kagent Agent Configuration

**File**: `agents/devops-rca-agent.yaml` (Updated)

```yaml
apiVersion: kagent.ai/v1alpha1
kind: Agent
metadata:
  name: devops-rca-agent
  namespace: analysis-agent
spec:
  description: "DevOps Root Cause Analysis AI Agent - Full Intelligence"

  instructions: |
    You are an expert DevOps SRE investigating production incidents in Kubernetes.

    **Your Mission**: When you receive an alert, perform a thorough investigation to identify
    the root cause and provide actionable solutions.

    **Investigation Process**:

    1. **Understand the Alert**
       - What failed? (pod, service, node)
       - When did it start?
       - What's the severity?
       - Which namespace/application?

    2. **Check Your Memory First**
       - Use memory_tool to read your knowledge base
       - Have you seen this issue before? Check known-issues.md
       - What do you know about this service? Check discovered-tools.md

    3. **Gather Evidence** (use all available tools):

       a) Kubernetes Resources:
          - kubectl describe pod [podname] -n [namespace]
          - kubectl get events -n [namespace] --sort-by='.lastTimestamp'
          - kubectl logs [podname] -n [namespace] --previous (if crashed)
          - kubectl get pod [podname] -n [namespace] -o yaml

       b) Analyze Logs:
          - Use log_tool to extract errors, stack traces
          - Look for connection errors, exceptions
          - Analyze exit codes if container crashed

       c) Helm Configuration:
          - Use helm_tool to get current values
          - Check history for recent changes
          - Compare current vs previous revision

       d) Prometheus Metrics (if relevant):
          - Query pod CPU/memory usage
          - Check for metric spikes around alert time
          - Compare with normal baseline

       e) GitHub (if available):
          - Check recent commits (last 24h)
          - Look for recent deployments
          - Check CI/CD workflow status

    4. **Build Timeline**
       - Chronologically order all events
       - Identify when things went wrong
       - What changed before the failure?

    5. **Root Cause Analysis**
       - Determine PRIMARY cause (the main issue)
       - Identify CONTRIBUTING factors (secondary issues)
       - Provide EVIDENCE for your conclusion
       - Consider multiple root causes if applicable

    6. **Generate Solutions**
       - Provide step-by-step remediation instructions
       - Include exact kubectl/helm commands
       - Explain WHY each solution works
       - Provide verification steps
       - Include rollback procedure if applicable
       - Suggest prevention measures

    7. **Create Report**
       Use this markdown format:

       ```markdown
       # Incident Report: [Alert Name]

       **Generated**: [timestamp]
       **Incident ID**: [unique ID]
       **Severity**: [critical/warning/info]

       ## Executive Summary
       [2-3 sentence overview of what happened and root cause]

       ## Alert Details
       - **Alert Name**:
       - **Severity**:
       - **Started At**:
       - **Namespace**:
       - **Affected Resource**:
       - **Status**:

       ## Investigation Timeline
       [Chronological list of events leading to failure]

       ## Root Cause Analysis

       ### Primary Cause
       [Main issue that caused the failure]

       ### Contributing Factors
       [Secondary issues that contributed]

       ### Evidence
       [Logs, metrics, configuration excerpts supporting your conclusion]

       ## Solutions

       ### Solution 1: [Immediate Fix]
       **Steps**:
       1. [Step with command]
       2. [Step with command]

       **Why this works**: [Explanation]

       **Verification**:
       - [How to verify it's fixed]

       ### Solution 2: [Root Fix] (if different from immediate)
       [Same format as above]

       ## Rollback Procedure
       [If applicable, how to rollback to previous working state]

       ## Prevention Recommendations
       1. [Long-term fix]
       2. [Process improvement]
       3. [Monitoring enhancement]

       ## Impact Assessment
       - **Affected Services**:
       - **User Impact**:
       - **Duration**:

       ## Supporting Evidence
       ### Relevant Logs
       ```
       [Key log excerpts]
       ```

       ### Configuration
       ```yaml
       [Relevant config]
       ```

       ### Metrics
       [Description of relevant metrics]
       ```

    8. **Update Memory**
       - Add new services/tools discovered to discovered-tools.md
       - If this is a new pattern, add to known-issues.md
       - Save report to memory using save_report

    9. **Send Notification**
       - Call notifier service with the report
       - Include severity for proper routing

    **Important Guidelines**:
    - Be thorough but concise
    - Provide exact commands, not placeholders
    - Support conclusions with evidence
    - Consider multiple root causes if applicable
    - Update your memory after each investigation

  tools:
    - name: kubernetes
      type: builtin

    - name: prometheus
      type: builtin

    - name: memory_tool
      type: python
      module: tools.memory_manager
      function: memory_tool

    - name: helm_tool
      type: python
      module: tools.helm_analyzer
      function: helm_tool

    - name: log_tool
      type: python
      module: tools.log_analyzer
      function: log_tool

    # Uncomment when GitHub token is configured
    # - name: github_tool
    #   type: python
    #   module: tools.github_api
    #   function: github_tool

  memory:
    persistentVolume:
      claimName: agent-memory-pvc
      mountPath: /agent-memory

  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "1Gi"
      cpu: "500m"
```

### Deliverables
- [ ] All 4 custom Python tools implemented
- [ ] Tools packaged and available to agent
- [ ] Kagent agent updated with tool definitions
- [ ] Agent instructions refined
- [ ] Tools tested individually
- [ ] Agent can invoke all tools

### Testing Phase 3
```bash
# Test tools independently first
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

# Deploy updated agent
kubectl apply -f agents/devops-rca-agent.yaml

# Test agent with tools
kagent invoke devops-rca-agent "List files in your memory"
kagent invoke devops-rca-agent "List all Helm releases in namespace production"
```

---

## Phase 4: Notifier Service

**Goal**: Implement email notification service for sending reports

### 4.1 Notifier Service Implementation

**File**: `services/notifier/requirements.txt`
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
aiosmtplib==3.0.1
email-validator==2.1.0
markdown2==2.4.12
jinja2==3.1.2
python-multipart==0.0.6
```

**File**: `services/notifier/main.py`

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import markdown2
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DevOps RCA Notifier Service", version="0.1.0")

# Configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USERNAME)

# Recipient configuration
RECIPIENTS_CRITICAL = os.getenv("RECIPIENTS_CRITICAL", "devops@example.com").split(",")
RECIPIENTS_WARNING = os.getenv("RECIPIENTS_WARNING", "devops@example.com").split(",")
RECIPIENTS_INFO = os.getenv("RECIPIENTS_INFO", "devops@example.com").split(",")

class NotificationRequest(BaseModel):
    subject: str
    report_markdown: str
    severity: str = "warning"  # critical, warning, info
    recipients: Optional[List[EmailStr]] = None
    incident_id: Optional[str] = None
    grafana_url: Optional[str] = None

class NotificationResponse(BaseModel):
    status: str
    message: str
    sent_to: List[str]
    timestamp: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "notifier"}

@app.post("/api/v1/send-report", response_model=NotificationResponse)
async def send_report(request: NotificationRequest):
    """
    Send incident report via email
    """
    logger.info(f"Sending report: {request.subject}")

    # Determine recipients based on severity
    if request.recipients:
        recipients = request.recipients
    else:
        recipients = get_recipients_by_severity(request.severity)

    # Convert markdown to HTML
    html_body = markdown_to_html(
        request.report_markdown,
        request.severity,
        request.incident_id,
        request.grafana_url
    )

    # Send email
    try:
        await send_email(
            subject=request.subject,
            html_body=html_body,
            recipients=recipients
        )

        logger.info(f"Report sent successfully to {len(recipients)} recipients")

        return NotificationResponse(
            status="sent",
            message=f"Report sent to {len(recipients)} recipients",
            sent_to=recipients,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@app.post("/api/v1/test-email")
async def test_email(recipients: List[EmailStr]):
    """
    Test email configuration
    """
    html_body = """
    <html>
    <body>
        <h2>DevOps RCA System - Test Email</h2>
        <p>This is a test email from the notifier service.</p>
        <p>If you received this, email configuration is working correctly!</p>
        <p><strong>Timestamp:</strong> {}</p>
    </body>
    </html>
    """.format(datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))

    try:
        await send_email(
            subject="DevOps RCA System - Test Email",
            html_body=html_body,
            recipients=recipients
        )

        return {
            "status": "success",
            "message": f"Test email sent to {recipients}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_recipients_by_severity(severity: str) -> List[str]:
    """Get recipient list based on severity"""
    if severity == "critical":
        return RECIPIENTS_CRITICAL
    elif severity == "warning":
        return RECIPIENTS_WARNING
    else:
        return RECIPIENTS_INFO

def markdown_to_html(
    markdown_text: str,
    severity: str,
    incident_id: Optional[str] = None,
    grafana_url: Optional[str] = None
) -> str:
    """
    Convert markdown report to styled HTML email
    """
    # Convert markdown to HTML
    html_content = markdown2.markdown(
        markdown_text,
        extras=["fenced-code-blocks", "tables", "header-ids"]
    )

    # Severity-based styling
    severity_colors = {
        "critical": "#d32f2f",
        "warning": "#f57c00",
        "info": "#1976d2"
    }

    severity_color = severity_colors.get(severity, "#1976d2")

    # Build complete HTML email
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            border-left: 4px solid {severity_color};
            padding-left: 20px;
            margin-bottom: 30px;
        }}
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            background-color: {severity_color};
            color: white;
            font-weight: bold;
            text-transform: uppercase;
            font-size: 12px;
            margin-bottom: 10px;
        }}
        h1 {{
            color: {severity_color};
            margin: 10px 0;
        }}
        h2 {{
            color: #555;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        h3 {{
            color: #666;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 3px solid {severity_color};
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        .solution {{
            background-color: #e8f5e9;
            border-left: 4px solid #4caf50;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .warning {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .timeline {{
            border-left: 3px solid #2196F3;
            padding-left: 20px;
            margin: 20px 0;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f5f5f5;
            font-weight: bold;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #777;
            font-size: 12px;
        }}
        .action-buttons {{
            margin: 20px 0;
        }}
        .button {{
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            background-color: {severity_color};
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }}
        .button:hover {{
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="severity-badge">{severity}</span>
            <h1>DevOps Incident Report</h1>
            {f'<p><strong>Incident ID:</strong> {incident_id}</p>' if incident_id else ''}
        </div>

        <div class="content">
            {html_content}
        </div>

        {f'''
        <div class="action-buttons">
            <a href="{grafana_url}" class="button">View in Grafana</a>
        </div>
        ''' if grafana_url else ''}

        <div class="footer">
            <p>This report was automatically generated by the DevOps RCA AI Agent.</p>
            <p>Generated at: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}</p>
        </div>
    </div>
</body>
</html>
    """

    return html

async def send_email(
    subject: str,
    html_body: str,
    recipients: List[str]
):
    """
    Send HTML email via SMTP
    """
    # Create message
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SMTP_FROM
    message["To"] = ", ".join(recipients)

    # Attach HTML body
    html_part = MIMEText(html_body, "html")
    message.attach(html_part)

    # Send via SMTP
    async with aiosmtplib.SMTP(
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        use_tls=False,  # We'll use STARTTLS
        timeout=30
    ) as smtp:
        await smtp.connect()
        await smtp.starttls()
        await smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        await smtp.send_message(message)
        logger.info(f"Email sent successfully to {recipients}")

@app.get("/")
async def root():
    return {
        "service": "DevOps RCA Notifier Service",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "send_report": "/api/v1/send-report",
            "test_email": "/api/v1/test-email"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 4.2 Notifier Dockerfile

**File**: `services/notifier/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 notifier && chown -R notifier:notifier /app
USER notifier

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 4.3 Gmail Secrets

**File**: `manifests/secrets.yaml`

```yaml
---
apiVersion: v1
kind: Secret
metadata:
  name: gmail-credentials
  namespace: analysis-agent
type: Opaque
stringData:
  smtp-username: "your-email@gmail.com"
  smtp-password: "your-app-password"  # Gmail app password, not account password
  smtp-from: "devops-rca@yourcompany.com"

  # Recipients
  recipients-critical: "oncall@example.com,sre-team@example.com"
  recipients-warning: "devops@example.com"
  recipients-info: "devops-alerts@example.com"
```

**Note**: Before applying, edit with your actual credentials.

### 4.4 Notifier Deployment

**File**: `manifests/deployments/notifier-deployment.yaml`

```yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: notifier-service
  namespace: analysis-agent
  labels:
    app: notifier-service
spec:
  replicas: 1
  selector:
    matchLabels:
      app: notifier-service
  template:
    metadata:
      labels:
        app: notifier-service
    spec:
      serviceAccountName: notifier-sa
      containers:
      - name: notifier
        image: your-dockerhub/analysis-agent-notifier:v0.1.0
        ports:
        - containerPort: 8080
          name: http
        env:
        - name: SMTP_HOST
          value: "smtp.gmail.com"
        - name: SMTP_PORT
          value: "587"
        - name: SMTP_USERNAME
          valueFrom:
            secretKeyRef:
              name: gmail-credentials
              key: smtp-username
        - name: SMTP_PASSWORD
          valueFrom:
            secretKeyRef:
              name: gmail-credentials
              key: smtp-password
        - name: SMTP_FROM
          valueFrom:
            secretKeyRef:
              name: gmail-credentials
              key: smtp-from
        - name: RECIPIENTS_CRITICAL
          valueFrom:
            secretKeyRef:
              name: gmail-credentials
              key: recipients-critical
        - name: RECIPIENTS_WARNING
          valueFrom:
            secretKeyRef:
              name: gmail-credentials
              key: recipients-warning
        - name: RECIPIENTS_INFO
          valueFrom:
            secretKeyRef:
              name: gmail-credentials
              key: recipients-info
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: notifier-service
  namespace: analysis-agent
spec:
  selector:
    app: notifier-service
  ports:
  - protocol: TCP
    port: 8080
    targetPort: 8080
    name: http
  type: ClusterIP
```

### Deliverables
- [ ] Notifier service code complete
- [ ] Gmail app password generated
- [ ] Secrets created with credentials
- [ ] Docker image built and pushed
- [ ] Notifier deployment created
- [ ] Test email sent successfully

### Testing Phase 4
```bash
# Generate Gmail app password first
# 1. Enable 2FA on Gmail account
# 2. Go to: https://myaccount.google.com/apppasswords
# 3. Create app password for "Mail"
# 4. Use that password in secrets.yaml

# Create secret
kubectl apply -f manifests/secrets.yaml

# Build and deploy
cd services/notifier
docker build -t your-dockerhub/analysis-agent-notifier:v0.1.0 .
docker push your-dockerhub/analysis-agent-notifier:v0.1.0

kubectl apply -f manifests/deployments/notifier-deployment.yaml

# Test email
kubectl port-forward svc/notifier-service 8080:8080 -n analysis-agent

curl -X POST http://localhost:8080/api/v1/test-email \
  -H "Content-Type: application/json" \
  -d '["your-email@example.com"]'

# Check inbox!
```

---

## Phase 5: Testing & Refinement

**Goal**: End-to-end testing with real failure scenarios

### 5.1 Create Test Alert Payloads

**File**: `tests/test-alerts/crashloop-alert.json`

```json
{
  "version": "4",
  "groupKey": "{}:{alertname=\"KubePodCrashLooping\"}",
  "status": "firing",
  "receiver": "devops-rca-agent",
  "groupLabels": {
    "alertname": "KubePodCrashLooping"
  },
  "commonLabels": {
    "alertname": "KubePodCrashLooping",
    "namespace": "production",
    "pod": "payment-service-7d9f8-xyz",
    "severity": "critical"
  },
  "commonAnnotations": {
    "description": "Pod production/payment-service-7d9f8-xyz is crash looping",
    "runbook_url": "https://runbooks.example.com/KubePodCrashLooping",
    "summary": "Pod is in CrashLoopBackOff state"
  },
  "externalURL": "http://alertmanager.monitoring:9093",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "KubePodCrashLooping",
        "container": "payment",
        "namespace": "production",
        "pod": "payment-service-7d9f8-xyz",
        "severity": "critical"
      },
      "annotations": {
        "description": "Pod production/payment-service-7d9f8-xyz is crash looping",
        "runbook_url": "https://runbooks.example.com/KubePodCrashLooping",
        "summary": "Pod is in CrashLoopBackOff state"
      },
      "startsAt": "2025-10-11T14:30:00.000Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://prometheus:9090/graph?g0.expr=...",
      "fingerprint": "abc123def456"
    }
  ]
}
```

**File**: `tests/test-alerts/oom-alert.json`

```json
{
  "version": "4",
  "groupKey": "{}:{alertname=\"KubePodOOMKilled\"}",
  "status": "firing",
  "receiver": "devops-rca-agent",
  "groupLabels": {
    "alertname": "KubePodOOMKilled"
  },
  "commonLabels": {
    "alertname": "KubePodOOMKilled",
    "namespace": "production",
    "pod": "api-service-5f8b9-abc",
    "severity": "warning"
  },
  "commonAnnotations": {
    "description": "Container in pod production/api-service-5f8b9-abc was OOMKilled",
    "summary": "Container exceeded memory limit"
  },
  "externalURL": "http://alertmanager.monitoring:9093",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "KubePodOOMKilled",
        "container": "api",
        "namespace": "production",
        "pod": "api-service-5f8b9-abc",
        "severity": "warning"
      },
      "annotations": {
        "description": "Container in pod production/api-service-5f8b9-abc was OOMKilled",
        "summary": "Container exceeded memory limit"
      },
      "startsAt": "2025-10-11T15:00:00.000Z",
      "endsAt": "0001-01-01T00:00:00Z",
      "generatorURL": "http://prometheus:9090/graph?g0.expr=...",
      "fingerprint": "def456ghi789"
    }
  ]
}
```

### 5.2 Create Test Failure Scenarios

**File**: `examples/crashloop-scenario/bad-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crashloop-test
  namespace: production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crashloop-test
  template:
    metadata:
      labels:
        app: crashloop-test
    spec:
      containers:
      - name: app
        image: busybox
        command: ["sh", "-c", "echo 'Starting...'; sleep 2; echo 'ERROR: Database connection failed'; exit 1"]
```

**File**: `examples/oom-scenario/memory-hog.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oom-test
  namespace: production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: oom-test
  template:
    metadata:
      labels:
        app: oom-test
    spec:
      containers:
      - name: app
        image: progrium/stress
        args: ["--vm", "1", "--vm-bytes", "150M", "--vm-hang", "0"]
        resources:
          limits:
            memory: "128Mi"
          requests:
            memory: "64Mi"
```

### 5.3 Testing Scripts

**File**: `tests/create-test-failure.sh`

```bash
#!/bin/bash
set -e

echo "Creating test failure scenario..."

# Create production namespace if it doesn't exist
kubectl create namespace production --dry-run=client -o yaml | kubectl apply -f -

# Choose scenario
echo "Select test scenario:"
echo "1) CrashLoop"
echo "2) OOMKilled"
echo "3) ImagePullBackOff"
read -p "Enter choice (1-3): " choice

case $choice in
  1)
    echo "Deploying CrashLoop scenario..."
    kubectl apply -f examples/crashloop-scenario/bad-deployment.yaml
    echo "Wait 2-3 minutes for AlertManager to fire alert"
    ;;
  2)
    echo "Deploying OOM scenario..."
    kubectl apply -f examples/oom-scenario/memory-hog.yaml
    echo "Wait 2-3 minutes for OOM kill and alert"
    ;;
  3)
    echo "Deploying ImagePull scenario..."
    kubectl create deployment imagepull-test --image=nonexistent/image:badtag -n production
    echo "Wait 1-2 minutes for ImagePullBackOff alert"
    ;;
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac

echo ""
echo "Monitoring pod status..."
kubectl get pods -n production -w
```

**File**: `tests/send-test-alert.sh`

```bash
#!/bin/bash
set -e

# Send test alert directly to webhook service
# Useful for testing without waiting for real failures

WEBHOOK_URL=${1:-"http://localhost:8080/api/v1/webhook/alertmanager"}
ALERT_FILE=${2:-"tests/test-alerts/crashloop-alert.json"}

echo "Sending test alert to: $WEBHOOK_URL"
echo "Alert payload: $ALERT_FILE"

# Port forward if testing locally
if [[ $WEBHOOK_URL == *"localhost"* ]]; then
  echo "Starting port-forward..."
  kubectl port-forward svc/webhook-service 8080:8080 -n analysis-agent &
  PF_PID=$!
  sleep 2
fi

# Send alert
curl -X POST "$WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d @"$ALERT_FILE" \
  -v

# Cleanup port-forward
if [[ ! -z "$PF_PID" ]]; then
  kill $PF_PID 2>/dev/null || true
fi

echo ""
echo "Alert sent! Check agent logs:"
echo "kubectl logs -f deployment/webhook-service -n analysis-agent"
```

**File**: `tests/verify-agent.sh`

```bash
#!/bin/bash
set -e

echo "Verifying DevOps RCA Agent setup..."
echo ""

# Check namespace
echo "1. Checking namespace..."
kubectl get namespace analysis-agent || {
  echo "❌ Namespace not found"
  exit 1
}
echo "✅ Namespace exists"

# Check PVC
echo "2. Checking storage..."
kubectl get pvc agent-memory-pvc -n analysis-agent || {
  echo "❌ PVC not found"
  exit 1
}
echo "✅ PVC exists"

# Check agent
echo "3. Checking Kagent agent..."
kubectl get agents devops-rca-agent -n analysis-agent || {
  echo "❌ Agent not found"
  exit 1
}
echo "✅ Agent deployed"

# Check webhook service
echo "4. Checking webhook service..."
kubectl get deployment webhook-service -n analysis-agent || {
  echo "❌ Webhook service not found"
  exit 1
}
kubectl get pods -n analysis-agent -l app=webhook-service | grep Running || {
  echo "❌ Webhook pods not running"
  exit 1
}
echo "✅ Webhook service running"

# Check notifier service
echo "5. Checking notifier service..."
kubectl get deployment notifier-service -n analysis-agent || {
  echo "❌ Notifier service not found"
  exit 1
}
kubectl get pods -n analysis-agent -l app=notifier-service | grep Running || {
  echo "❌ Notifier pods not running"
  exit 1
}
echo "✅ Notifier service running"

# Check secrets
echo "6. Checking secrets..."
kubectl get secret gmail-credentials -n analysis-agent || {
  echo "⚠️  Gmail credentials not configured"
}
echo "✅ Secrets configured"

# Check AlertManager config
echo "7. Checking AlertManager..."
kubectl get pod -n monitoring -l app=alertmanager | grep Running || {
  echo "⚠️  AlertManager not found in monitoring namespace"
}
echo "✅ AlertManager running"

echo ""
echo "==================================="
echo "✅ All checks passed!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Create a test failure: ./tests/create-test-failure.sh"
echo "2. Or send test alert: ./tests/send-test-alert.sh"
echo "3. Monitor logs: kubectl logs -f -n analysis-agent -l app=webhook-service"
```

### 5.4 End-to-End Test

**Create**: `tests/e2e-test.md`

```markdown
# End-to-End Test Plan

## Test 1: CrashLoop Investigation

### Setup
1. Deploy CrashLoop test deployment
   ```bash
   kubectl apply -f examples/crashloop-scenario/bad-deployment.yaml
   ```

2. Wait for pod to crash and AlertManager to fire

### Expected Flow
1. Prometheus detects pod CrashLoopBackOff
2. AlertManager sends webhook to webhook-service
3. Webhook service triggers Kagent agent
4. Agent investigates:
   - Reads memory
   - Describes pod
   - Gets logs
   - Checks events
   - Analyzes exit code
5. Agent determines root cause
6. Agent generates report
7. Agent saves report to memory
8. Agent calls notifier service
9. Email received with detailed report

### Verification
- [ ] Alert received by webhook service
- [ ] Agent logs show investigation
- [ ] Report saved in /agent-memory/reports/
- [ ] Email received with correct information
- [ ] Root cause correctly identified
- [ ] Solutions provided are actionable

---

## Test 2: OOMKilled Investigation

### Setup
1. Deploy memory-intensive pod with low limits
   ```bash
   kubectl apply -f examples/oom-scenario/memory-hog.yaml
   ```

### Expected Flow
[Similar to Test 1, but with OOM-specific analysis]

### Verification
- [ ] Exit code 137 detected
- [ ] Memory limits identified as too low
- [ ] Solution recommends increasing memory
- [ ] Helm values checked (if deployed via Helm)

---

## Test 3: Manual Alert Submission

### Setup
1. Port-forward webhook service
2. Send test alert JSON

### Expected Flow
[Same investigation flow]

### Verification
- [ ] Alert parsed correctly
- [ ] All alert labels/annotations used in investigation
```

### Deliverables
- [ ] All test scenarios created
- [ ] Test scripts written and executable
- [ ] E2E test plan documented
- [ ] CrashLoop test passed
- [ ] OOM test passed
- [ ] Reports generated correctly
- [ ] Emails received with proper formatting
- [ ] Agent memory updated after investigations

### Testing Phase 5

```bash
# Make scripts executable
chmod +x tests/*.sh
chmod +x tests/create-test-failure.sh

# Verify setup
./tests/verify-agent.sh

# Run E2E test
./tests/create-test-failure.sh
# Choose option 1 (CrashLoop)

# Monitor
kubectl logs -f -n analysis-agent -l app=webhook-service
kubectl logs -f -n analysis-agent -l app=kagent

# Check memory
kubectl exec -it <agent-pod> -n analysis-agent -- ls -la /agent-memory/reports/

# Verify email received
# Check inbox for incident report
```

---

## Phase 6: Future Enhancements

**Goal**: Plan for MCP server integration and advanced features

### 6.1 MCP Server Integration

**Planned MCP Servers**:

1. **GitHub Actions MCP Server**
   - Real-time workflow monitoring
   - Trigger workflow reruns
   - Access to workflow artifacts
   - Advanced commit analysis

2. **ArgoCD MCP Server**
   - Application sync/diff operations
   - Trigger manual syncs
   - Rollback applications
   - Advanced GitOps correlation

3. **Slack MCP Server**
   - Send notifications to Slack channels
   - Interactive incident reports
   - Threaded discussions
   - Incident status updates

### 6.2 Advanced Features

1. **Predictive Analysis**
   - Pattern learning from historical incidents
   - Proactive alerting before failures
   - Trend analysis

2. **Auto-Remediation** (with approval)
   - Automatic rollbacks for known issues
   - Self-healing for common problems
   - Require human approval for critical actions

3. **Multi-Cluster Support**
   - Monitor multiple Kubernetes clusters
   - Cross-cluster correlation
   - Centralized reporting

4. **RAG System for Reports**
   - Store reports in vector database
   - Semantic search across incidents
   - Learn from past solutions

### 6.3 Documentation to Create

**File**: `docs/FUTURE_MCP.md`
- MCP architecture overview
- How to add new MCP servers
- Integration patterns
- Security considerations

---

## Appendix

### A. Quick Reference Commands

```bash
# Deploy everything
kubectl apply -f manifests/

# Check status
kubectl get all -n analysis-agent

# View logs
kubectl logs -n analysis-agent -l app=webhook-service
kubectl logs -n analysis-agent -l app=notifier-service

# Access agent memory
kubectl exec -it <agent-pod> -n analysis-agent -- ls /agent-memory/

# Port forward services
kubectl port-forward svc/webhook-service 8080:8080 -n analysis-agent
kubectl port-forward svc/notifier-service 8081:8080 -n analysis-agent

# Test webhook
curl -X POST http://localhost:8080/api/v1/webhook/test -d '{"test": "alert"}'

# Test notifier
curl -X POST http://localhost:8081/api/v1/test-email -d '["your@email.com"]'
```

### B. Troubleshooting

Common issues and solutions:

1. **Webhook not receiving alerts**
   - Check AlertManager configuration
   - Verify webhook service is accessible from monitoring namespace
   - Check webhook service logs

2. **Agent not investigating**
   - Verify Kagent operator is running
   - Check agent RBAC permissions
   - Review agent logs

3. **Emails not sending**
   - Verify Gmail app password is correct
   - Check SMTP settings
   - Ensure outbound port 587 is not blocked
   - Review notifier service logs

4. **Memory not persisting**
   - Check PVC is bound
   - Verify storage class exists
   - Check volume mounts in agent pod

### C. Project Timeline

**Estimated Timeline** (flexible, no strict deadline):

- **Phase 0**: 1-2 days (setup, prerequisites)
- **Phase 1**: 2-3 days (foundation, storage, basic agent)
- **Phase 2**: 2-3 days (webhook service)
- **Phase 3**: 3-5 days (tools and agent intelligence)
- **Phase 4**: 2-3 days (notifier service)
- **Phase 5**: 3-5 days (testing, refinement)
- **Total**: ~2-3 weeks for MVP

**Phase 6** (future): Ongoing enhancements

---

## Summary

This development plan provides a complete roadmap for building a Kagent-based DevOps Root Cause Analysis system. The MVP focuses on:

✅ Alert-driven investigation (no continuous scanning)
✅ Intelligent AI agent with custom tools
✅ Automated report generation
✅ Email notifications to DevOps team
✅ Persistent memory for knowledge accumulation
✅ Simple, maintainable architecture

**Next Steps**:
1. Review this plan
2. Set up development environment (Phase 0)
3. Begin implementation phase by phase
4. Test thoroughly with real scenarios
5. Iterate and improve based on results

**Success Criteria**:
- Agent successfully investigates alerts
- Root causes accurately identified
- Solutions are actionable and correct
- Reports are comprehensive and clear
- System is easy to deploy and maintain

Good luck with your implementation! 🚀
