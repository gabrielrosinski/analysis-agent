# GitHub Repositories

This file tracks GitHub repositories linked to services in the cluster and their CI/CD workflows.

## Discovered Repositories

| Service | Repository | Branch | Workflows | Last Commit | Notes |
|---------|------------|--------|-----------|-------------|-------|
| [Service name] | github.com/org/repo | main | build-deploy.yml | [To be populated] | [Notes] |

## Workflow Patterns

### Build and Deploy Workflows

[Will be populated as agent discovers workflow patterns]

### Common Workflow Issues

[Will be populated as agent encounters CI/CD failures]

## Repository Discovery

The agent discovers repositories by:
1. Analyzing pod annotations (e.g., `github.com/repository`)
2. Examining deployment labels
3. Investigating failed deployments and their sources
4. Checking ArgoCD applications for git sources

## Notes

- Add repositories manually if you want the agent to monitor them
- The agent will fetch recent commits during incident investigations
- Workflow status will be checked when investigating deployment issues
- Requires GitHub API token (optional for MVP)

## Configuration

To enable GitHub integration:
1. Create a GitHub Personal Access Token with `repo:read` permissions
2. Store in Kubernetes secret: `github-token`
3. Uncomment `github_tool` in agent configuration

## Example Entry

```
| payment-service | github.com/myorg/payment-service | main | build-deploy.yml, test.yml | 2025-10-11 14:15:00 | Production service |
```

---

[Agent will populate this file during investigations]
