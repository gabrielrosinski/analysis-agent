"""
Helm Analyzer Tool for Kagent DevOps RCA Agent

Provides analysis of Helm releases, configurations, and deployment history.
Uses kubectl and helm CLI commands to gather information about Helm-managed applications.
"""

import subprocess
import json
import yaml
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class HelmAnalyzer:
    """Analyzes Helm releases and their configurations."""

    def __init__(self):
        """Initialize Helm analyzer."""
        pass

    def _run_command(self, cmd: List[str]) -> tuple[str, str, int]:
        """
        Run a shell command and return output.

        Args:
            cmd: Command as list of strings

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", 1
        except Exception as e:
            return "", str(e), 1

    def list_releases(self, namespace: Optional[str] = None, all_namespaces: bool = False) -> str:
        """
        List Helm releases.

        Args:
            namespace: Specific namespace to query (optional)
            all_namespaces: List releases from all namespaces

        Returns:
            Formatted list of releases or error message
        """
        cmd = ["helm", "list", "--output", "json"]

        if all_namespaces:
            cmd.append("--all-namespaces")
        elif namespace:
            cmd.extend(["--namespace", namespace])

        stdout, stderr, code = self._run_command(cmd)

        if code != 0:
            return f"ERROR: Failed to list Helm releases: {stderr}"

        try:
            releases = json.loads(stdout) if stdout else []

            if not releases:
                return "No Helm releases found"

            # Format output
            result = f"Found {len(releases)} Helm release(s):\n\n"
            for r in releases:
                result += f"- **{r.get('name')}** (namespace: {r.get('namespace')})\n"
                result += f"  - Chart: {r.get('chart')}\n"
                result += f"  - App Version: {r.get('app_version')}\n"
                result += f"  - Status: {r.get('status')}\n"
                result += f"  - Updated: {r.get('updated')}\n"
                result += f"  - Revision: {r.get('revision')}\n\n"

            return result

        except json.JSONDecodeError as e:
            return f"ERROR: Failed to parse Helm output: {e}"

    def get_release_details(self, release: str, namespace: str) -> str:
        """
        Get detailed information about a Helm release.

        Args:
            release: Release name
            namespace: Namespace where release is deployed

        Returns:
            Formatted release details or error message
        """
        cmd = ["helm", "status", release, "--namespace", namespace, "--output", "json"]

        stdout, stderr, code = self._run_command(cmd)

        if code != 0:
            return f"ERROR: Failed to get release details: {stderr}"

        try:
            data = json.loads(stdout)

            result = f"# Helm Release: {release}\n\n"
            result += f"**Namespace:** {namespace}\n"
            result += f"**Status:** {data.get('info', {}).get('status')}\n"
            result += f"**Description:** {data.get('info', {}).get('description')}\n"
            result += f"**First Deployed:** {data.get('info', {}).get('first_deployed')}\n"
            result += f"**Last Deployed:** {data.get('info', {}).get('last_deployed')}\n"
            result += f"**Notes:**\n```\n{data.get('info', {}).get('notes', 'No notes')}\n```\n"

            return result

        except json.JSONDecodeError as e:
            return f"ERROR: Failed to parse release details: {e}"

    def get_values(self, release: str, namespace: str, all_values: bool = False) -> str:
        """
        Get Helm release values (configuration).

        Args:
            release: Release name
            namespace: Namespace where release is deployed
            all_values: Get all values including defaults (False = only user-provided values)

        Returns:
            YAML-formatted values or error message
        """
        cmd = ["helm", "get", "values", release, "--namespace", namespace]

        if all_values:
            cmd.append("--all")

        stdout, stderr, code = self._run_command(cmd)

        if code != 0:
            return f"ERROR: Failed to get release values: {stderr}"

        if not stdout or stdout.strip() == "null":
            return f"No custom values set for release '{release}' (using chart defaults)"

        return f"# Values for {release}\n\n```yaml\n{stdout}\n```"

    def get_manifest(self, release: str, namespace: str) -> str:
        """
        Get rendered Kubernetes manifests for a Helm release.

        Args:
            release: Release name
            namespace: Namespace where release is deployed

        Returns:
            Kubernetes manifests or error message
        """
        cmd = ["helm", "get", "manifest", release, "--namespace", namespace]

        stdout, stderr, code = self._run_command(cmd)

        if code != 0:
            return f"ERROR: Failed to get release manifest: {stderr}"

        # Truncate if too large
        max_length = 5000
        if len(stdout) > max_length:
            return f"# Manifest for {release} (truncated)\n\n```yaml\n{stdout[:max_length]}\n...\n[Truncated - manifest too large]\n```"

        return f"# Manifest for {release}\n\n```yaml\n{stdout}\n```"

    def get_history(self, release: str, namespace: str, limit: int = 10) -> str:
        """
        Get deployment history for a Helm release.

        Args:
            release: Release name
            namespace: Namespace where release is deployed
            limit: Maximum number of revisions to show

        Returns:
            Formatted release history or error message
        """
        cmd = ["helm", "history", release, "--namespace", namespace, "--output", "json", "--max", str(limit)]

        stdout, stderr, code = self._run_command(cmd)

        if code != 0:
            return f"ERROR: Failed to get release history: {stderr}"

        try:
            history = json.loads(stdout)

            if not history:
                return f"No history found for release '{release}'"

            result = f"# Release History: {release}\n\n"
            result += f"Showing last {min(len(history), limit)} revision(s):\n\n"

            for h in reversed(history):  # Show newest first
                result += f"## Revision {h.get('revision')}\n"
                result += f"- **Updated:** {h.get('updated')}\n"
                result += f"- **Status:** {h.get('status')}\n"
                result += f"- **Chart:** {h.get('chart')}\n"
                result += f"- **App Version:** {h.get('app_version')}\n"
                result += f"- **Description:** {h.get('description')}\n\n"

            return result

        except json.JSONDecodeError as e:
            return f"ERROR: Failed to parse release history: {e}"

    def compare_revisions(self, release: str, namespace: str, revision1: int, revision2: int) -> str:
        """
        Compare two revisions of a Helm release.

        Args:
            release: Release name
            namespace: Namespace where release is deployed
            revision1: First revision number
            revision2: Second revision number

        Returns:
            Comparison of values between revisions
        """
        # Get values for both revisions
        cmd1 = ["helm", "get", "values", release, "--namespace", namespace, "--revision", str(revision1)]
        cmd2 = ["helm", "get", "values", release, "--namespace", namespace, "--revision", str(revision2)]

        stdout1, stderr1, code1 = self._run_command(cmd1)
        stdout2, stderr2, code2 = self._run_command(cmd2)

        if code1 != 0 or code2 != 0:
            return f"ERROR: Failed to get revision values: {stderr1 or stderr2}"

        result = f"# Revision Comparison: {release}\n\n"
        result += f"## Revision {revision1} Values\n```yaml\n{stdout1 or 'null'}\n```\n\n"
        result += f"## Revision {revision2} Values\n```yaml\n{stdout2 or 'null'}\n```\n\n"
        result += "**Note:** Use diff tools to identify specific changes between these values.\n"

        return result

    def check_release_health(self, release: str, namespace: str) -> str:
        """
        Check health of a Helm release by examining its resources.

        Args:
            release: Release name
            namespace: Namespace where release is deployed

        Returns:
            Health status of release resources
        """
        # Get release status first
        cmd = ["helm", "status", release, "--namespace", namespace, "--output", "json"]
        stdout, stderr, code = self._run_command(cmd)

        if code != 0:
            return f"ERROR: Failed to check release health: {stderr}"

        try:
            data = json.loads(stdout)
            status = data.get('info', {}).get('status')

            result = f"# Health Check: {release}\n\n"
            result += f"**Helm Status:** {status}\n\n"

            if status != "deployed":
                result += f"**WARNING:** Release is not in 'deployed' state. Current state: {status}\n\n"

            # Get pods managed by this release
            cmd_pods = ["kubectl", "get", "pods", "-n", namespace,
                        "-l", f"app.kubernetes.io/instance={release}",
                        "--output", "json"]

            pods_out, pods_err, pods_code = self._run_command(cmd_pods)

            if pods_code == 0 and pods_out:
                pods_data = json.loads(pods_out)
                pods = pods_data.get('items', [])

                result += f"## Pod Health ({len(pods)} pod(s))\n\n"

                for pod in pods:
                    pod_name = pod['metadata']['name']
                    phase = pod['status'].get('phase', 'Unknown')
                    result += f"- **{pod_name}:** {phase}\n"

                    # Check container statuses
                    container_statuses = pod['status'].get('containerStatuses', [])
                    for cs in container_statuses:
                        container_name = cs['name']
                        ready = cs['ready']
                        restart_count = cs['restartCount']

                        result += f"  - Container `{container_name}`: Ready={ready}, Restarts={restart_count}\n"

                        # Check for issues
                        if not ready or restart_count > 0:
                            state = cs.get('state', {})
                            if 'waiting' in state:
                                reason = state['waiting'].get('reason', 'Unknown')
                                message = state['waiting'].get('message', '')
                                result += f"    - **Issue:** {reason} - {message}\n"

                result += "\n"

            else:
                result += f"**Note:** Could not retrieve pod information (release may not manage pods)\n\n"

            return result

        except json.JSONDecodeError as e:
            return f"ERROR: Failed to parse health check data: {e}"


def helm_tool(action: str, **kwargs) -> str:
    """
    Kagent tool function for Helm analysis operations.

    Actions:
    - list: List Helm releases (optional: namespace, all_namespaces=True)
    - details: Get release details (requires: release, namespace)
    - values: Get release values (requires: release, namespace; optional: all_values=True)
    - manifest: Get rendered manifests (requires: release, namespace)
    - history: Get deployment history (requires: release, namespace; optional: limit=10)
    - compare: Compare two revisions (requires: release, namespace, revision1, revision2)
    - health: Check release health (requires: release, namespace)

    Args:
        action: Action to perform
        **kwargs: Action-specific parameters

    Returns:
        String result from the action

    Examples:
        helm_tool(action="list", all_namespaces=True)
        helm_tool(action="details", release="prometheus", namespace="monitoring")
        helm_tool(action="values", release="nginx", namespace="default")
        helm_tool(action="history", release="myapp", namespace="production", limit=5)
        helm_tool(action="health", release="myapp", namespace="production")
    """
    analyzer = HelmAnalyzer()

    try:
        if action == "list":
            namespace = kwargs.get("namespace")
            all_namespaces = kwargs.get("all_namespaces", False)
            return analyzer.list_releases(namespace, all_namespaces)

        elif action == "details":
            release = kwargs.get("release")
            namespace = kwargs.get("namespace")
            if not release or not namespace:
                return "ERROR: 'release' and 'namespace' parameters required for details action"
            return analyzer.get_release_details(release, namespace)

        elif action == "values":
            release = kwargs.get("release")
            namespace = kwargs.get("namespace")
            all_values = kwargs.get("all_values", False)
            if not release or not namespace:
                return "ERROR: 'release' and 'namespace' parameters required for values action"
            return analyzer.get_values(release, namespace, all_values)

        elif action == "manifest":
            release = kwargs.get("release")
            namespace = kwargs.get("namespace")
            if not release or not namespace:
                return "ERROR: 'release' and 'namespace' parameters required for manifest action"
            return analyzer.get_manifest(release, namespace)

        elif action == "history":
            release = kwargs.get("release")
            namespace = kwargs.get("namespace")
            limit = kwargs.get("limit", 10)
            if not release or not namespace:
                return "ERROR: 'release' and 'namespace' parameters required for history action"
            return analyzer.get_history(release, namespace, limit)

        elif action == "compare":
            release = kwargs.get("release")
            namespace = kwargs.get("namespace")
            revision1 = kwargs.get("revision1")
            revision2 = kwargs.get("revision2")
            if not all([release, namespace, revision1, revision2]):
                return "ERROR: 'release', 'namespace', 'revision1', and 'revision2' parameters required for compare action"
            return analyzer.compare_revisions(release, namespace, int(revision1), int(revision2))

        elif action == "health":
            release = kwargs.get("release")
            namespace = kwargs.get("namespace")
            if not release or not namespace:
                return "ERROR: 'release' and 'namespace' parameters required for health action"
            return analyzer.check_release_health(release, namespace)

        else:
            return f"ERROR: Unknown action '{action}'. Valid actions: list, details, values, manifest, history, compare, health"

    except Exception as e:
        logger.exception("Helm tool error")
        return f"ERROR: Helm tool failed: {e}"


if __name__ == "__main__":
    # Test the tool locally
    print("Testing Helm Analyzer Tool")
    print("=" * 60)

    analyzer = HelmAnalyzer()

    # Test list releases
    print("\n1. Listing all Helm releases...")
    print(analyzer.list_releases(all_namespaces=True))

    # Test with tool function interface
    print("\n" + "=" * 60)
    print("Testing helm_tool function interface")
    print("=" * 60)

    print("\nTest: helm_tool(action='list', all_namespaces=True)")
    print(helm_tool(action="list", all_namespaces=True))
