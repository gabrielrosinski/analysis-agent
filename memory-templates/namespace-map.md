# Namespace Topology

This file maps the cluster's namespace structure, their purposes, and key services.

## Namespace Overview

### analysis-agent
**Purpose**: DevOps Root Cause Analysis System
**Created**: [Date]
**Services**:
- webhook-service: AlertManager webhook receiver
- notifier-service: Email notification sender
- devops-rca-agent: Kagent AI agent

**Resource Quotas**: [To be discovered]
**Network Policies**: [To be discovered]

---

### monitoring
**Purpose**: Observability and Alerting
**Created**: [To be discovered]
**Services**:
- prometheus: Metrics collection
- grafana: Visualization
- alertmanager: Alert routing

**Resource Quotas**: [To be discovered]
**Network Policies**: [To be discovered]

---

### production
**Purpose**: Production Applications
**Created**: [To be discovered]
**Services**: [To be discovered]

**Resource Quotas**: [To be discovered]
**Network Policies**: [To be discovered]

---

### [Other Namespaces]
[Will be discovered and documented by agent]

---

## Namespace Relationships

```
monitoring
    ↓ (alerts)
analysis-agent
    ↓ (investigates)
production, staging, development
    ↓ (monitors)
monitoring
```

## Cross-Namespace Communication

| From | To | Purpose | Port/Protocol |
|------|----|---------|--------------
| monitoring/alertmanager | analysis-agent/webhook-service | Send alerts | 8080/HTTP |
| analysis-agent/agent | All namespaces | Investigate issues | Various |

## Resource Distribution

[Will be populated with resource usage per namespace]

## Security Policies

### Network Policies
[To be discovered and documented]

### Pod Security Policies
[To be discovered and documented]

### Service Mesh Policies
[If applicable, to be discovered]

## Notes

- The agent scans all namespaces to build this map
- Cross-namespace dependencies are important for root cause analysis
- Resource quotas can cause Pending pod issues

---

[Agent will populate and update this file during investigations]
