# Discovered Tools & Services

Last updated: [Will be updated by agent during first scan]

## CI/CD Tools

### GitHub Actions
- **Status**: Not yet discovered
- **Repositories**: [Will be populated during investigations]
- **Common Workflows**: [Will be identified]

### ArgoCD
- **Status**: Not yet discovered
- **Namespace**: [To be detected]
- **Applications**: [Will be listed]

## Container Registry

### Docker Hub
- **Type**: Public registry
- **Usage**: Public images

### GitHub Container Registry
- **Type**: Private registry
- **Usage**: [To be determined]

## Monitoring & Observability

### Prometheus
- **Status**: Expected to be present
- **Namespace**: monitoring
- **Service**: [To be discovered]

### Grafana
- **Status**: Expected to be present
- **Namespace**: monitoring
- **Dashboards**: [Will be cataloged]

### AlertManager
- **Status**: Required component
- **Namespace**: monitoring
- **Integration**: Connected to webhook service

## Namespaces

| Namespace | Purpose | Key Services | Last Seen |
|-----------|---------|--------------|-----------|
| analysis-agent | RCA System | webhook, notifier, agent | Active |
| monitoring | Observability | prometheus, grafana, alertmanager | [To be verified] |
| production | Production Apps | [To be discovered] | [To be verified] |

## Helm Releases

[Will be populated as agent discovers Helm deployments]

## Custom Resources

[Will be populated as agent discovers CRDs and custom resources]

## Notes

- This file is automatically updated by the agent during investigations
- Add manual entries here if you want the agent to know about specific tools
- The agent will verify and enrich information over time
