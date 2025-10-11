# Helm Charts

This file tracks Helm releases deployed in the cluster, their configurations, and deployment history.

## Deployed Releases

| Release | Namespace | Chart | App Version | Status | Updated | Notes |
|---------|-----------|-------|-------------|--------|---------|-------|
| [Name] | [Namespace] | [Chart name-version] | [App version] | deployed | [Date] | [Notes] |

## Release History

### [Release Name]

- **Current Revision**: [Number]
- **Last Deployment**: [Date/Time]
- **Recent Changes**: [What changed in last deployment]
- **Known Issues**: [Any recurring issues]

## Common Helm Patterns

### Configuration Changes

[Will be populated as agent observes Helm-related incidents]

### Rollback Procedures

[Will be documented as agent performs or recommends rollbacks]

## Helm Discovery

The agent discovers Helm releases by running:
```bash
helm list --all-namespaces
```

For each release, the agent can:
- Get current values: `helm get values <release> -n <namespace>`
- View history: `helm history <release> -n <namespace>`
- Compare revisions: `helm diff revision <release> <rev1> <rev2>`

## Important Releases

### Critical Services

[Will be marked by agent based on alert frequency and severity]

### Frequent Changes

[Releases that update frequently - may need special attention]

## Notes

- The agent checks Helm releases when investigating deployment issues
- Value changes between revisions are analyzed to find configuration-related root causes
- Rollback recommendations are based on revision history

---

[Agent will populate this file during investigations]
