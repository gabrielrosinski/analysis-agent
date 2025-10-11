# Custom Tools for Kagent DevOps RCA Agent

This directory contains custom Python tools that extend the Kagent agent's investigation capabilities. Each tool provides a specific set of functions for root cause analysis.

## Tool Overview

### 1. Memory Manager (`memory_manager.py`)

Manages the agent's persistent markdown-based knowledge base stored at `/agent-memory/`.

**Functions:**
- `list`: List all memory files
- `read`: Read file content
- `write`: Write file content
- `append`: Append to existing file
- `search`: Search for term in file
- `save_report`: Save incident report with timestamp
- `recent_reports`: Get list of recent reports

**Usage Example:**
```python
memory_tool(action="read", filename="known-issues.md")
memory_tool(action="save_report", alert_name="PodCrashLoop", content="# Report...")
memory_tool(action="search", filename="known-issues.md", search_term="OOMKilled")
```

**Memory Structure:**
```
/agent-memory/
├── discovered-tools.md    # DevOps tools in cluster
├── known-issues.md        # Solved incident patterns
├── github-repos.md        # Linked repositories
├── helm-charts.md         # Deployed Helm releases
├── namespace-map.md       # Cluster topology
└── reports/               # Incident reports
```

---

### 2. Helm Analyzer (`helm_analyzer.py`)

Analyzes Helm releases, configurations, and deployment history.

**Functions:**
- `list`: List Helm releases (optionally by namespace or all)
- `details`: Get release details
- `values`: Get release values/configuration
- `manifest`: Get rendered Kubernetes manifests
- `history`: Get deployment history
- `compare`: Compare two revisions
- `health`: Check release health status

**Usage Example:**
```python
helm_tool(action="list", all_namespaces=True)
helm_tool(action="details", release="prometheus", namespace="monitoring")
helm_tool(action="values", release="myapp", namespace="production")
helm_tool(action="history", release="myapp", namespace="production", limit=5)
helm_tool(action="health", release="myapp", namespace="production")
```

**Requirements:**
- `helm` CLI installed in container
- `kubectl` CLI for resource health checks
- Kubernetes RBAC permissions to list resources

---

### 3. Log Analyzer (`log_analyzer.py`)

Parses and analyzes container logs to extract insights.

**Functions:**
- `extract_errors`: Extract error lines
- `extract_warnings`: Extract warning lines
- `identify_patterns`: Identify known error patterns
- `parse_stack_traces`: Extract stack traces (Python, Java, Go)
- `analyze_exit_code`: Interpret container exit codes
- `summarize`: Create log summary with statistics
- `find_repeated`: Find repeated error messages

**Usage Example:**
```python
log_tool(action="extract_errors", logs=pod_logs, limit=20)
log_tool(action="identify_patterns", logs=pod_logs)
log_tool(action="analyze_exit_code", exit_code=137)
log_tool(action="summarize", logs=pod_logs)
log_tool(action="find_repeated", logs=pod_logs, min_occurrences=3)
```

**Detected Patterns:**
- Connection errors (refused, timeout, unreachable)
- Authentication failures
- File/path errors
- Memory issues (OOM)
- Database errors
- Certificate/TLS errors
- Disk space issues

**Exit Code Interpretations:**
- `0`: Success
- `1`: Application error
- `137`: Killed (often OOMKilled)
- `143`: Terminated (SIGTERM)
- `127`: Command not found

---

### 4. GitHub API (`github_api.py`)

Integrates with GitHub API to fetch commit and workflow information.

**Functions:**
- `recent_commits`: Get recent commits for a repository
- `commit_details`: Get detailed commit information
- `workflow_runs`: Get GitHub Actions workflow runs
- `failed_workflows`: Get recent failed workflows
- `check_repo`: Check if repository exists

**Usage Example:**
```python
github_tool(action="recent_commits", owner="myorg", repo="myapp", limit=5)
github_tool(action="commit_details", owner="myorg", repo="myapp", commit_sha="abc123")
github_tool(action="workflow_runs", owner="myorg", repo="myapp", branch="main")
github_tool(action="failed_workflows", owner="myorg", repo="myapp")
```

**Configuration:**
- Set `GITHUB_TOKEN` environment variable for API access
- Token required for private repositories
- Public repos have rate limits without token

---

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

**Dependencies:**
- `requests` - For GitHub API calls
- `PyYAML` - For YAML parsing
- Python 3.11+ standard library modules

---

## Tool Function Signature

All tools follow the same function signature pattern:

```python
def tool_name(action: str, **kwargs) -> str:
    """
    Kagent tool function.

    Args:
        action: Action to perform (string)
        **kwargs: Action-specific parameters

    Returns:
        String result (success message, data, or error)
    """
```

**Why this pattern?**
- Kagent invokes tools with keyword arguments
- Single entry point per tool simplifies agent configuration
- Action-based routing allows multiple operations per tool
- String return values work well with LLM processing

---

## Testing Tools Independently

Each tool can be tested independently with its `__main__` block:

```bash
# Test memory manager
python3 memory_manager.py

# Test helm analyzer
python3 helm_analyzer.py

# Test log analyzer
python3 log_analyzer.py

# Test GitHub API (requires GITHUB_TOKEN)
export GITHUB_TOKEN=ghp_xxxxx
python3 github_api.py
```

---

## Adding New Tools

To add a new custom tool:

1. **Create tool module** (`tools/my_tool.py`):
   ```python
   def my_tool(action: str, **kwargs) -> str:
       """Tool function with action-based routing."""
       if action == "do_something":
           # Implementation
           return "Result"
       else:
           return f"ERROR: Unknown action '{action}'"
   ```

2. **Add to `__init__.py`**:
   ```python
   from .my_tool import my_tool
   __all__.append("my_tool")
   ```

3. **Update agent YAML** (`agents/devops-rca-agent.yaml`):
   ```yaml
   tools:
     - name: my_tool
       type: python
       module: tools.my_tool
       function: my_tool
   ```

4. **Update agent instructions** to explain when/how to use the tool

---

## Error Handling

All tools return errors as strings starting with `"ERROR:"`:

```python
if something_failed:
    return "ERROR: Description of what went wrong"
```

The agent can parse these error messages and adjust its investigation accordingly.

---

## Logging

Tools use Python's logging module:

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Operation successful")
logger.warning("Potential issue detected")
logger.error("Operation failed")
```

Logs are captured by the Kagent operator and can be viewed with:
```bash
kubectl logs -n kagent-system -l app=kagent-operator
```

---

## Security Considerations

- **Read-Only Operations**: Tools primarily perform read operations
- **No Cluster Modifications**: Tools don't modify Kubernetes resources
- **RBAC Enforcement**: Agent uses limited ServiceAccount permissions
- **Secret Handling**: GitHub tokens from secrets, not hardcoded
- **Input Validation**: All tools validate required parameters

---

## Tool Design Principles

1. **Single Responsibility**: Each tool has a focused purpose
2. **Action-Based Routing**: One function, multiple actions
3. **Error Transparency**: Clear error messages for debugging
4. **Self-Contained**: Minimal external dependencies
5. **Testable**: Can run independently for testing
6. **Documented**: Clear docstrings and examples

---

## Troubleshooting

### Tool Import Errors
```bash
# Ensure tools directory is in Python path
export PYTHONPATH=/path/to/analysis-agent:$PYTHONPATH
python3 -c "from tools import memory_tool; print('Success')"
```

### Missing Dependencies
```bash
# Install all dependencies
cd tools
pip install -r requirements.txt
```

### Permission Errors (Helm/kubectl)
```bash
# Check agent ServiceAccount permissions
kubectl auth can-i list pods --as=system:serviceaccount:analysis-agent:agent-sa --all-namespaces
kubectl auth can-i get secrets --as=system:serviceaccount:analysis-agent:agent-sa -n production
```

### GitHub API Rate Limits
```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/rate_limit
```

---

## Future Tool Ideas

Potential tools for future phases:

- **ArgoCD Tool**: Sync status, deployment history, diff analysis
- **Prometheus Tool**: Query metrics, identify anomalies
- **Slack Tool**: Send interactive notifications, receive feedback
- **Database Tool**: Connection testing, query analysis
- **Network Tool**: Connectivity testing, DNS resolution
- **Cost Tool**: Resource cost analysis, optimization suggestions

---

## Contributing

When contributing new tools:

1. Follow the existing tool pattern
2. Include comprehensive docstrings
3. Add test cases in `__main__` block
4. Update this README with tool documentation
5. Update agent instructions in `agents/devops-rca-agent.yaml`

---

**Version:** 0.1.0

**Last Updated:** 2025-10-11
