"""
Memory Manager Tool for Kagent DevOps RCA Agent

Provides read/write operations for the agent's persistent markdown-based knowledge base.
The knowledge base is stored at /agent-memory/ and includes:
- discovered-tools.md - Catalogued DevOps tools in cluster
- known-issues.md - Previously solved incident patterns
- github-repos.md - Linked GitHub repositories
- helm-charts.md - Deployed Helm releases
- namespace-map.md - Cluster topology
- reports/ - Saved incident reports
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages agent's persistent memory stored in markdown files."""

    def __init__(self, memory_path: str = "/agent-memory"):
        """
        Initialize memory manager.

        Args:
            memory_path: Path to agent memory directory (default: /agent-memory)
        """
        self.memory_path = Path(memory_path)
        self.reports_path = self.memory_path / "reports"

        # Ensure reports directory exists
        if self.memory_path.exists():
            self.reports_path.mkdir(exist_ok=True)

    def list_files(self) -> List[str]:
        """
        List all files in agent memory.

        Returns:
            List of relative file paths
        """
        if not self.memory_path.exists():
            return []

        files = []
        for item in self.memory_path.rglob("*.md"):
            relative_path = item.relative_to(self.memory_path)
            files.append(str(relative_path))

        return sorted(files)

    def read_file(self, filename: str) -> str:
        """
        Read content from a memory file.

        Args:
            filename: Relative path to file (e.g., "known-issues.md" or "reports/2025-10-11-incident-001.md")

        Returns:
            File content as string, or error message if file doesn't exist
        """
        file_path = self.memory_path / filename

        if not file_path.exists():
            return f"ERROR: File '{filename}' not found in memory. Available files: {', '.join(self.list_files())}"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Read {len(content)} bytes from {filename}")
            return content
        except Exception as e:
            logger.error(f"Failed to read {filename}: {e}")
            return f"ERROR: Failed to read file: {e}"

    def write_file(self, filename: str, content: str) -> str:
        """
        Write content to a memory file.

        Args:
            filename: Relative path to file
            content: Content to write

        Returns:
            Success message or error message
        """
        file_path = self.memory_path / filename

        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Wrote {len(content)} bytes to {filename}")
            return f"SUCCESS: Wrote {len(content)} bytes to {filename}"
        except Exception as e:
            logger.error(f"Failed to write {filename}: {e}")
            return f"ERROR: Failed to write file: {e}"

    def append_to_file(self, filename: str, content: str) -> str:
        """
        Append content to an existing memory file.

        Args:
            filename: Relative path to file
            content: Content to append

        Returns:
            Success message or error message
        """
        file_path = self.memory_path / filename

        if not file_path.exists():
            return f"ERROR: File '{filename}' not found. Use write_file to create it first."

        try:
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Appended {len(content)} bytes to {filename}")
            return f"SUCCESS: Appended {len(content)} bytes to {filename}"
        except Exception as e:
            logger.error(f"Failed to append to {filename}: {e}")
            return f"ERROR: Failed to append to file: {e}"

    def search_in_file(self, filename: str, search_term: str) -> str:
        """
        Search for a term in a memory file and return matching lines with context.

        Args:
            filename: Relative path to file
            search_term: Term to search for (case-insensitive)

        Returns:
            Matching lines with line numbers, or message if no matches
        """
        file_path = self.memory_path / filename

        if not file_path.exists():
            return f"ERROR: File '{filename}' not found"

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            matches = []
            search_term_lower = search_term.lower()

            for i, line in enumerate(lines, 1):
                if search_term_lower in line.lower():
                    matches.append(f"Line {i}: {line.rstrip()}")

            if not matches:
                return f"No matches found for '{search_term}' in {filename}"

            return f"Found {len(matches)} matches in {filename}:\n" + "\n".join(matches)

        except Exception as e:
            logger.error(f"Failed to search {filename}: {e}")
            return f"ERROR: Failed to search file: {e}"

    def save_report(self, alert_name: str, content: str) -> str:
        """
        Save an incident report with timestamp.

        Args:
            alert_name: Name of the alert (used in filename)
            content: Report content in markdown format

        Returns:
            Success message with filename, or error message
        """
        # Generate filename with timestamp
        timestamp = datetime.utcnow().strftime("%Y-%m-%d-%H%M%S")
        # Sanitize alert name for filename
        safe_alert_name = "".join(c if c.isalnum() or c in ('-', '_') else '-'
                                   for c in alert_name.lower())
        filename = f"reports/{timestamp}-{safe_alert_name}.md"

        result = self.write_file(filename, content)

        if result.startswith("SUCCESS"):
            return f"SUCCESS: Report saved as {filename}"
        return result

    def get_recent_reports(self, limit: int = 10) -> List[str]:
        """
        Get list of recent report filenames.

        Args:
            limit: Maximum number of reports to return

        Returns:
            List of report filenames, newest first
        """
        if not self.reports_path.exists():
            return []

        reports = sorted(self.reports_path.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        return [f"reports/{r.name}" for r in reports[:limit]]


def memory_tool(action: str, **kwargs) -> str:
    """
    Kagent tool function for memory management operations.

    Actions:
    - list: List all files in memory (no params)
    - read: Read file content (requires: filename)
    - write: Write file content (requires: filename, content)
    - append: Append to existing file (requires: filename, content)
    - search: Search for term in file (requires: filename, search_term)
    - save_report: Save incident report (requires: alert_name, content)
    - recent_reports: Get recent report list (optional: limit=10)

    Args:
        action: Action to perform
        **kwargs: Action-specific parameters

    Returns:
        String result from the action

    Examples:
        memory_tool(action="list")
        memory_tool(action="read", filename="known-issues.md")
        memory_tool(action="write", filename="discovered-tools.md", content="# Tools\\n...")
        memory_tool(action="search", filename="known-issues.md", search_term="OOMKilled")
        memory_tool(action="save_report", alert_name="KubePodCrashLooping", content="# Report\\n...")
    """
    manager = MemoryManager()

    try:
        if action == "list":
            files = manager.list_files()
            if not files:
                return "Memory directory is empty or not yet initialized"
            return "Available memory files:\n" + "\n".join(f"  - {f}" for f in files)

        elif action == "read":
            filename = kwargs.get("filename")
            if not filename:
                return "ERROR: 'filename' parameter required for read action"
            return manager.read_file(filename)

        elif action == "write":
            filename = kwargs.get("filename")
            content = kwargs.get("content")
            if not filename or content is None:
                return "ERROR: 'filename' and 'content' parameters required for write action"
            return manager.write_file(filename, content)

        elif action == "append":
            filename = kwargs.get("filename")
            content = kwargs.get("content")
            if not filename or content is None:
                return "ERROR: 'filename' and 'content' parameters required for append action"
            return manager.append_to_file(filename, content)

        elif action == "search":
            filename = kwargs.get("filename")
            search_term = kwargs.get("search_term")
            if not filename or not search_term:
                return "ERROR: 'filename' and 'search_term' parameters required for search action"
            return manager.search_in_file(filename, search_term)

        elif action == "save_report":
            alert_name = kwargs.get("alert_name")
            content = kwargs.get("content")
            if not alert_name or content is None:
                return "ERROR: 'alert_name' and 'content' parameters required for save_report action"
            return manager.save_report(alert_name, content)

        elif action == "recent_reports":
            limit = kwargs.get("limit", 10)
            reports = manager.get_recent_reports(limit)
            if not reports:
                return "No reports found in memory"
            return "Recent reports:\n" + "\n".join(f"  - {r}" for r in reports)

        else:
            return f"ERROR: Unknown action '{action}'. Valid actions: list, read, write, append, search, save_report, recent_reports"

    except Exception as e:
        logger.exception("Memory tool error")
        return f"ERROR: Memory tool failed: {e}"


if __name__ == "__main__":
    # Test the tool locally
    print("Testing Memory Manager Tool")
    print("=" * 60)

    # Test with a temporary directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test memory manager
        test_manager = MemoryManager(tmpdir)

        # Test write
        print("\n1. Writing test file...")
        result = test_manager.write_file("test.md", "# Test\n\nThis is a test file.")
        print(result)

        # Test list
        print("\n2. Listing files...")
        files = test_manager.list_files()
        print(f"Files: {files}")

        # Test read
        print("\n3. Reading file...")
        content = test_manager.read_file("test.md")
        print(f"Content:\n{content}")

        # Test append
        print("\n4. Appending to file...")
        result = test_manager.append_to_file("test.md", "\n\nAppended content.")
        print(result)

        # Test search
        print("\n5. Searching for 'Appended'...")
        result = test_manager.search_in_file("test.md", "Appended")
        print(result)

        # Test save report
        print("\n6. Saving report...")
        result = test_manager.save_report("TestAlert", "# Incident Report\n\nTest report content.")
        print(result)

        # Test recent reports
        print("\n7. Getting recent reports...")
        reports = test_manager.get_recent_reports()
        print(f"Reports: {reports}")

    print("\n" + "=" * 60)
    print("Testing memory_tool function interface")
    print("=" * 60)

    # Test tool function
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ['MEMORY_PATH'] = tmpdir

        print("\nTest: memory_tool(action='list')")
        print(memory_tool(action="list"))

        print("\nTest: memory_tool(action='write', ...)")
        print(memory_tool(action="write", filename="test.md", content="# Test"))

        print("\nTest: memory_tool(action='read', ...)")
        print(memory_tool(action="read", filename="test.md"))
