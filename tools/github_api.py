"""
GitHub API Tool for Kagent DevOps RCA Agent

Provides integration with GitHub API to:
- Fetch recent commits for a repository
- Get GitHub Actions workflow runs
- Check workflow status
- Correlate deployments with commits

Requires GitHub personal access token configured in environment or Kubernetes secret.
"""

import os
import json
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Try to import requests, but make it optional
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not available, GitHub API tool will have limited functionality")


class GitHubAPI:
    """GitHub API client for RCA investigations."""

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API client.

        Args:
            token: GitHub personal access token (reads from GITHUB_TOKEN env var if not provided)
        """
        self.token = token or os.environ.get('GITHUB_TOKEN', '')
        self.base_url = "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> tuple[Optional[Any], Optional[str]]:
        """
        Make a request to GitHub API.

        Args:
            endpoint: API endpoint (e.g., '/repos/owner/repo/commits')
            params: Query parameters

        Returns:
            Tuple of (response_data, error_message)
        """
        if not REQUESTS_AVAILABLE:
            return None, "ERROR: requests library not installed. Install with: pip install requests"

        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)

            if response.status_code == 401:
                return None, "ERROR: GitHub API authentication failed. Check GITHUB_TOKEN."

            if response.status_code == 404:
                return None, f"ERROR: Resource not found: {endpoint}"

            if response.status_code == 403:
                return None, "ERROR: GitHub API rate limit exceeded or access forbidden."

            if response.status_code != 200:
                return None, f"ERROR: GitHub API returned status {response.status_code}: {response.text}"

            return response.json(), None

        except requests.RequestException as e:
            return None, f"ERROR: Failed to connect to GitHub API: {e}"
        except json.JSONDecodeError as e:
            return None, f"ERROR: Failed to parse GitHub API response: {e}"

    def get_recent_commits(self, owner: str, repo: str, branch: str = "main", limit: int = 10, since_hours: Optional[int] = None) -> str:
        """
        Get recent commits for a repository.

        Args:
            owner: Repository owner (user or organization)
            repo: Repository name
            branch: Branch name (default: main)
            limit: Maximum number of commits to return
            since_hours: Only return commits from the last N hours (optional)

        Returns:
            Formatted commit history or error message
        """
        endpoint = f"/repos/{owner}/{repo}/commits"
        params = {
            'sha': branch,
            'per_page': limit,
        }

        if since_hours:
            since_time = datetime.utcnow() - timedelta(hours=since_hours)
            params['since'] = since_time.isoformat() + 'Z'

        data, error = self._make_request(endpoint, params)

        if error:
            return error

        if not data:
            return f"No commits found in {owner}/{repo} on branch {branch}"

        result = f"# Recent Commits: {owner}/{repo} (branch: {branch})\n\n"
        result += f"Showing {len(data)} commit(s):\n\n"

        for commit in data:
            sha = commit['sha'][:7]
            message = commit['commit']['message'].split('\n')[0]  # First line only
            author = commit['commit']['author']['name']
            date = commit['commit']['author']['date']
            url = commit['html_url']

            result += f"- **{sha}** - {message}\n"
            result += f"  - Author: {author}\n"
            result += f"  - Date: {date}\n"
            result += f"  - URL: {url}\n\n"

        return result

    def get_commit_details(self, owner: str, repo: str, commit_sha: str) -> str:
        """
        Get detailed information about a specific commit.

        Args:
            owner: Repository owner
            repo: Repository name
            commit_sha: Commit SHA (full or short)

        Returns:
            Formatted commit details or error message
        """
        endpoint = f"/repos/{owner}/{repo}/commits/{commit_sha}"

        data, error = self._make_request(endpoint)

        if error:
            return error

        result = f"# Commit Details: {commit_sha[:7]}\n\n"
        result += f"**Repository:** {owner}/{repo}\n"
        result += f"**Author:** {data['commit']['author']['name']} <{data['commit']['author']['email']}>\n"
        result += f"**Date:** {data['commit']['author']['date']}\n"
        result += f"**Message:**\n```\n{data['commit']['message']}\n```\n\n"

        # Files changed
        files = data.get('files', [])
        if files:
            result += f"**Files Changed ({len(files)}):**\n"
            for file in files[:20]:  # Limit to first 20 files
                status = file['status']
                filename = file['filename']
                additions = file.get('additions', 0)
                deletions = file.get('deletions', 0)
                result += f"- [{status}] {filename} (+{additions}/-{deletions})\n"

            if len(files) > 20:
                result += f"- ... and {len(files) - 20} more files\n"

        result += f"\n**URL:** {data['html_url']}\n"

        return result

    def get_workflow_runs(self, owner: str, repo: str, branch: Optional[str] = None, limit: int = 10) -> str:
        """
        Get recent GitHub Actions workflow runs.

        Args:
            owner: Repository owner
            repo: Repository name
            branch: Filter by branch (optional)
            limit: Maximum number of runs to return

        Returns:
            Formatted workflow runs or error message
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs"
        params = {'per_page': limit}

        if branch:
            params['branch'] = branch

        data, error = self._make_request(endpoint, params)

        if error:
            return error

        runs = data.get('workflow_runs', [])

        if not runs:
            return f"No workflow runs found in {owner}/{repo}"

        result = f"# GitHub Actions Workflow Runs: {owner}/{repo}\n\n"
        result += f"Showing {len(runs)} run(s):\n\n"

        for run in runs:
            run_id = run['id']
            workflow_name = run['name']
            status = run['status']
            conclusion = run.get('conclusion', 'N/A')
            branch = run['head_branch']
            commit_sha = run['head_sha'][:7]
            created_at = run['created_at']
            updated_at = run['updated_at']
            url = run['html_url']

            # Status emoji
            status_emoji = {
                'completed': '✅' if conclusion == 'success' else '❌',
                'in_progress': '🔄',
                'queued': '⏳',
            }.get(status, '❓')

            result += f"## {status_emoji} {workflow_name} (Run #{run_id})\n"
            result += f"- **Status:** {status}\n"
            if conclusion != 'N/A':
                result += f"- **Conclusion:** {conclusion}\n"
            result += f"- **Branch:** {branch}\n"
            result += f"- **Commit:** {commit_sha}\n"
            result += f"- **Created:** {created_at}\n"
            result += f"- **Updated:** {updated_at}\n"
            result += f"- **URL:** {url}\n\n"

        return result

    def get_failed_workflows(self, owner: str, repo: str, limit: int = 5) -> str:
        """
        Get recent failed workflow runs.

        Args:
            owner: Repository owner
            repo: Repository name
            limit: Maximum number of failed runs to return

        Returns:
            Formatted failed workflow runs or error message
        """
        endpoint = f"/repos/{owner}/{repo}/actions/runs"
        params = {
            'status': 'completed',
            'per_page': 50,  # Fetch more to filter for failures
        }

        data, error = self._make_request(endpoint, params)

        if error:
            return error

        runs = data.get('workflow_runs', [])

        # Filter for failures
        failed_runs = [r for r in runs if r.get('conclusion') in ('failure', 'timed_out', 'cancelled')][:limit]

        if not failed_runs:
            return f"No failed workflow runs found in {owner}/{repo} (recent runs all successful!)"

        result = f"# Failed GitHub Actions Workflows: {owner}/{repo}\n\n"
        result += f"Showing {len(failed_runs)} failed run(s):\n\n"

        for run in failed_runs:
            workflow_name = run['name']
            conclusion = run['conclusion']
            branch = run['head_branch']
            commit_sha = run['head_sha'][:7]
            created_at = run['created_at']
            url = run['html_url']

            result += f"## ❌ {workflow_name}\n"
            result += f"- **Conclusion:** {conclusion}\n"
            result += f"- **Branch:** {branch}\n"
            result += f"- **Commit:** {commit_sha}\n"
            result += f"- **Time:** {created_at}\n"
            result += f"- **URL:** {url}\n\n"

        return result

    def check_repository_exists(self, owner: str, repo: str) -> str:
        """
        Check if a repository exists and is accessible.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information or error message
        """
        endpoint = f"/repos/{owner}/{repo}"

        data, error = self._make_request(endpoint)

        if error:
            return error

        result = f"# Repository: {owner}/{repo}\n\n"
        result += f"**Full Name:** {data['full_name']}\n"
        result += f"**Description:** {data.get('description', 'No description')}\n"
        result += f"**Default Branch:** {data['default_branch']}\n"
        result += f"**Private:** {data['private']}\n"
        result += f"**Language:** {data.get('language', 'N/A')}\n"
        result += f"**Created:** {data['created_at']}\n"
        result += f"**Updated:** {data['updated_at']}\n"
        result += f"**URL:** {data['html_url']}\n"

        return result


def github_tool(action: str, **kwargs) -> str:
    """
    Kagent tool function for GitHub API operations.

    Actions:
    - recent_commits: Get recent commits (requires: owner, repo; optional: branch, limit, since_hours)
    - commit_details: Get commit details (requires: owner, repo, commit_sha)
    - workflow_runs: Get workflow runs (requires: owner, repo; optional: branch, limit)
    - failed_workflows: Get failed workflows (requires: owner, repo; optional: limit)
    - check_repo: Check if repository exists (requires: owner, repo)

    Environment:
    - GITHUB_TOKEN: GitHub personal access token (optional for public repos, required for private)

    Args:
        action: Action to perform
        **kwargs: Action-specific parameters

    Returns:
        String result from the action

    Examples:
        github_tool(action="recent_commits", owner="kubernetes", repo="kubernetes", limit=5)
        github_tool(action="commit_details", owner="myorg", repo="myapp", commit_sha="abc123")
        github_tool(action="workflow_runs", owner="myorg", repo="myapp", branch="main")
        github_tool(action="failed_workflows", owner="myorg", repo="myapp")
    """
    # Check for GitHub token
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        logger.warning("GITHUB_TOKEN not set - API rate limits will be restricted")

    api = GitHubAPI(token)

    try:
        if action == "recent_commits":
            owner = kwargs.get("owner")
            repo = kwargs.get("repo")
            branch = kwargs.get("branch", "main")
            limit = kwargs.get("limit", 10)
            since_hours = kwargs.get("since_hours")

            if not owner or not repo:
                return "ERROR: 'owner' and 'repo' parameters required for recent_commits action"

            return api.get_recent_commits(owner, repo, branch, limit, since_hours)

        elif action == "commit_details":
            owner = kwargs.get("owner")
            repo = kwargs.get("repo")
            commit_sha = kwargs.get("commit_sha")

            if not owner or not repo or not commit_sha:
                return "ERROR: 'owner', 'repo', and 'commit_sha' parameters required for commit_details action"

            return api.get_commit_details(owner, repo, commit_sha)

        elif action == "workflow_runs":
            owner = kwargs.get("owner")
            repo = kwargs.get("repo")
            branch = kwargs.get("branch")
            limit = kwargs.get("limit", 10)

            if not owner or not repo:
                return "ERROR: 'owner' and 'repo' parameters required for workflow_runs action"

            return api.get_workflow_runs(owner, repo, branch, limit)

        elif action == "failed_workflows":
            owner = kwargs.get("owner")
            repo = kwargs.get("repo")
            limit = kwargs.get("limit", 5)

            if not owner or not repo:
                return "ERROR: 'owner' and 'repo' parameters required for failed_workflows action"

            return api.get_failed_workflows(owner, repo, limit)

        elif action == "check_repo":
            owner = kwargs.get("owner")
            repo = kwargs.get("repo")

            if not owner or not repo:
                return "ERROR: 'owner' and 'repo' parameters required for check_repo action"

            return api.check_repository_exists(owner, repo)

        else:
            return f"ERROR: Unknown action '{action}'. Valid actions: recent_commits, commit_details, workflow_runs, failed_workflows, check_repo"

    except Exception as e:
        logger.exception("GitHub tool error")
        return f"ERROR: GitHub tool failed: {e}"


if __name__ == "__main__":
    # Test the tool locally
    print("Testing GitHub API Tool")
    print("=" * 60)

    # Check if token is available
    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print("\nWARNING: GITHUB_TOKEN not set. Testing with public repository (rate limits apply).\n")

    api = GitHubAPI(token)

    # Test with a public repository (kubernetes/kubernetes)
    print("\n1. Checking if kubernetes/kubernetes repository exists...")
    print(api.check_repository_exists("kubernetes", "kubernetes"))

    print("\n2. Getting recent commits from kubernetes/kubernetes...")
    print(api.get_recent_commits("kubernetes", "kubernetes", "master", limit=3))

    print("\n" + "=" * 60)
    print("Testing github_tool function interface")
    print("=" * 60)

    print("\nTest: github_tool(action='recent_commits', ...)")
    print(github_tool(action="recent_commits", owner="kubernetes", repo="kubernetes", branch="master", limit=2))

    if token:
        print("\n\nNote: Full testing requires a valid GITHUB_TOKEN environment variable.")
    else:
        print("\n\nNote: Set GITHUB_TOKEN environment variable to test with private repositories.")
