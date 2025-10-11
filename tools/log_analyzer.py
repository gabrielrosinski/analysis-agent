"""
Log Analyzer Tool for Kagent DevOps RCA Agent

Provides intelligent analysis of container logs including:
- Error and warning extraction
- Pattern matching for common issues
- Exit code interpretation
- Log timestamp analysis
- Stack trace parsing
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class LogAnalyzer:
    """Analyzes container logs to extract insights and identify issues."""

    # Common log level patterns
    LOG_LEVEL_PATTERNS = {
        'ERROR': r'(?i)(error|err|fatal|critical|crit|exception)',
        'WARNING': r'(?i)(warning|warn)',
        'INFO': r'(?i)(info|information)',
        'DEBUG': r'(?i)(debug|trace)',
    }

    # Common error patterns
    ERROR_PATTERNS = {
        'connection_refused': r'(?i)connection refused',
        'connection_timeout': r'(?i)(connection.*timeout|timeout.*connection)',
        'no_such_host': r'(?i)(no such host|name resolution failed|could not resolve)',
        'permission_denied': r'(?i)permission denied',
        'out_of_memory': r'(?i)(out of memory|oom|cannot allocate memory)',
        'file_not_found': r'(?i)(no such file|file not found|cannot find)',
        'port_in_use': r'(?i)(address already in use|port.*already in use)',
        'authentication_failed': r'(?i)(auth.*failed|authentication.*failed|invalid credentials)',
        'database_error': r'(?i)(database.*error|sql.*error|connection pool)',
        'network_unreachable': r'(?i)network.*unreachable',
        'disk_full': r'(?i)(no space left|disk.*full)',
        'certificate_error': r'(?i)(certificate.*error|tls.*error|ssl.*error)',
    }

    # Exit code meanings
    EXIT_CODES = {
        0: "Success - Normal exit",
        1: "General error - Application-specific error",
        2: "Misuse of shell command",
        126: "Command cannot execute - Permission problem",
        127: "Command not found",
        128: "Invalid exit argument",
        130: "Terminated by Ctrl+C (SIGINT)",
        137: "Killed (SIGKILL) - Often OOMKilled in Kubernetes",
        143: "Terminated (SIGTERM) - Graceful shutdown signal",
    }

    def __init__(self):
        """Initialize log analyzer."""
        pass

    def extract_errors(self, logs: str, limit: int = 50) -> str:
        """
        Extract error lines from logs.

        Args:
            logs: Raw log content
            limit: Maximum number of error lines to return

        Returns:
            Formatted error lines or message if none found
        """
        if not logs:
            return "No logs provided"

        lines = logs.split('\n')
        error_pattern = re.compile(self.LOG_LEVEL_PATTERNS['ERROR'])

        errors = []
        for i, line in enumerate(lines, 1):
            if error_pattern.search(line):
                errors.append(f"Line {i}: {line.strip()}")

        if not errors:
            return "No error lines found in logs"

        if len(errors) > limit:
            return f"Found {len(errors)} error lines (showing first {limit}):\n\n" + "\n".join(errors[:limit])

        return f"Found {len(errors)} error line(s):\n\n" + "\n".join(errors)

    def extract_warnings(self, logs: str, limit: int = 50) -> str:
        """
        Extract warning lines from logs.

        Args:
            logs: Raw log content
            limit: Maximum number of warning lines to return

        Returns:
            Formatted warning lines or message if none found
        """
        if not logs:
            return "No logs provided"

        lines = logs.split('\n')
        warning_pattern = re.compile(self.LOG_LEVEL_PATTERNS['WARNING'])

        warnings = []
        for i, line in enumerate(lines, 1):
            if warning_pattern.search(line):
                warnings.append(f"Line {i}: {line.strip()}")

        if not warnings:
            return "No warning lines found in logs"

        if len(warnings) > limit:
            return f"Found {len(warnings)} warning lines (showing first {limit}):\n\n" + "\n".join(warnings[:limit])

        return f"Found {len(warnings)} warning line(s):\n\n" + "\n".join(warnings)

    def identify_patterns(self, logs: str) -> str:
        """
        Identify known error patterns in logs.

        Args:
            logs: Raw log content

        Returns:
            Formatted list of identified patterns
        """
        if not logs:
            return "No logs provided"

        matches = {}
        for pattern_name, pattern in self.ERROR_PATTERNS.items():
            regex = re.compile(pattern)
            found = regex.findall(logs)
            if found:
                matches[pattern_name] = len(found)

        if not matches:
            return "No known error patterns identified in logs"

        result = "**Identified Error Patterns:**\n\n"
        for pattern_name, count in sorted(matches.items(), key=lambda x: x[1], reverse=True):
            friendly_name = pattern_name.replace('_', ' ').title()
            result += f"- **{friendly_name}**: {count} occurrence(s)\n"

        return result

    def parse_stack_traces(self, logs: str) -> str:
        """
        Extract stack traces from logs.

        Args:
            logs: Raw log content

        Returns:
            Formatted stack traces or message if none found
        """
        if not logs:
            return "No logs provided"

        # Common stack trace patterns
        # Python: "Traceback (most recent call last):"
        # Java: lines starting with "at " or "Caused by:"
        # Go: "panic:" followed by goroutine dump

        stack_traces = []
        lines = logs.split('\n')

        # Python stack traces
        i = 0
        while i < len(lines):
            if 'Traceback' in lines[i] or 'traceback' in lines[i]:
                trace = [lines[i]]
                i += 1
                while i < len(lines) and (lines[i].startswith('  ') or lines[i].startswith('\t') or 'File' in lines[i] or 'Error' in lines[i]):
                    trace.append(lines[i])
                    i += 1
                stack_traces.append('\n'.join(trace))
            i += 1

        # Java/Kotlin stack traces
        i = 0
        while i < len(lines):
            if re.match(r'^\s*(Exception|Error)', lines[i]) or 'Caused by:' in lines[i]:
                trace = [lines[i]]
                i += 1
                while i < len(lines) and (re.match(r'^\s*at ', lines[i]) or re.match(r'^\s*\.\.\.', lines[i]) or 'Caused by:' in lines[i]):
                    trace.append(lines[i])
                    i += 1
                stack_traces.append('\n'.join(trace))
            i += 1

        # Go panics
        i = 0
        while i < len(lines):
            if 'panic:' in lines[i]:
                trace = [lines[i]]
                i += 1
                while i < len(lines) and (lines[i].startswith('goroutine') or re.match(r'^\s+', lines[i])):
                    trace.append(lines[i])
                    if 'goroutine' in lines[i] and i > 0:
                        break
                    i += 1
                stack_traces.append('\n'.join(trace))
            i += 1

        if not stack_traces:
            return "No stack traces found in logs"

        result = f"**Found {len(stack_traces)} Stack Trace(s):**\n\n"
        for idx, trace in enumerate(stack_traces, 1):
            result += f"### Stack Trace {idx}\n```\n{trace}\n```\n\n"

        return result

    def analyze_exit_code(self, exit_code: int) -> str:
        """
        Interpret container exit code.

        Args:
            exit_code: Container exit code

        Returns:
            Human-readable explanation of exit code
        """
        explanation = self.EXIT_CODES.get(exit_code, "Unknown exit code")

        result = f"**Exit Code {exit_code}:** {explanation}\n\n"

        # Add specific guidance
        if exit_code == 137:
            result += "**Analysis:** Container was killed, likely by OOM (Out of Memory) killer.\n"
            result += "**Investigation:** Check memory limits and actual memory usage.\n"
            result += "**Solution:** Increase memory limits or optimize application memory usage.\n"

        elif exit_code == 143:
            result += "**Analysis:** Container received SIGTERM, typically during graceful shutdown.\n"
            result += "**Investigation:** Check if application handles SIGTERM properly.\n"
            result += "**Note:** This can be normal during rolling updates or pod termination.\n"

        elif exit_code == 1:
            result += "**Analysis:** Application exited with error status.\n"
            result += "**Investigation:** Check application logs for error messages.\n"
            result += "**Action:** Review the error logs to identify the specific failure.\n"

        elif exit_code == 127:
            result += "**Analysis:** Command not found in container.\n"
            result += "**Investigation:** Check container ENTRYPOINT/CMD in Dockerfile.\n"
            result += "**Solution:** Ensure the binary exists in the container image.\n"

        return result

    def summarize_logs(self, logs: str, tail_lines: int = 50) -> str:
        """
        Create a summary of logs with key statistics.

        Args:
            logs: Raw log content
            tail_lines: Number of recent lines to include

        Returns:
            Formatted log summary
        """
        if not logs:
            return "No logs provided"

        lines = logs.split('\n')
        total_lines = len(lines)

        # Count log levels
        level_counts = Counter()
        for line in lines:
            for level, pattern in self.LOG_LEVEL_PATTERNS.items():
                if re.search(pattern, line):
                    level_counts[level] += 1
                    break

        # Count error patterns
        pattern_counts = {}
        for pattern_name, pattern in self.ERROR_PATTERNS.items():
            count = len(re.findall(pattern, logs))
            if count > 0:
                pattern_counts[pattern_name] = count

        # Build summary
        result = "# Log Summary\n\n"
        result += f"**Total Lines:** {total_lines}\n\n"

        if level_counts:
            result += "## Log Level Distribution\n"
            for level, count in level_counts.most_common():
                result += f"- {level}: {count}\n"
            result += "\n"

        if pattern_counts:
            result += "## Error Patterns Detected\n"
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
                friendly_name = pattern.replace('_', ' ').title()
                result += f"- {friendly_name}: {count}\n"
            result += "\n"

        # Add tail of logs
        if total_lines > 0:
            result += f"## Last {min(tail_lines, total_lines)} Lines\n\n```\n"
            result += '\n'.join(lines[-tail_lines:])
            result += "\n```\n"

        return result

    def find_repeated_errors(self, logs: str, min_occurrences: int = 3) -> str:
        """
        Find errors that repeat multiple times (potential loops or persistent issues).

        Args:
            logs: Raw log content
            min_occurrences: Minimum number of occurrences to report

        Returns:
            Formatted list of repeated error messages
        """
        if not logs:
            return "No logs provided"

        lines = logs.split('\n')
        error_pattern = re.compile(self.LOG_LEVEL_PATTERNS['ERROR'])

        # Extract error messages (strip timestamps and common prefixes)
        error_messages = []
        for line in lines:
            if error_pattern.search(line):
                # Try to extract the error message without timestamp
                # Common formats: "2024-01-01 12:00:00 ERROR message" or "[ERROR] message"
                cleaned = re.sub(r'^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}[.,\d]*\s*', '', line)
                cleaned = re.sub(r'^\[.*?\]\s*', '', cleaned)
                cleaned = re.sub(r'^[A-Z]+\s*:\s*', '', cleaned)
                if cleaned:
                    error_messages.append(cleaned.strip())

        if not error_messages:
            return "No error messages found in logs"

        # Count occurrences
        message_counts = Counter(error_messages)
        repeated = {msg: count for msg, count in message_counts.items() if count >= min_occurrences}

        if not repeated:
            return f"No errors repeated {min_occurrences}+ times"

        result = f"**Repeated Errors (occurring {min_occurrences}+ times):**\n\n"
        for msg, count in sorted(repeated.items(), key=lambda x: x[1], reverse=True):
            result += f"- **{count} times:** {msg[:200]}{'...' if len(msg) > 200 else ''}\n"

        result += f"\n**Analysis:** Repeated errors suggest a persistent issue or error loop.\n"

        return result


def log_tool(action: str, **kwargs) -> str:
    """
    Kagent tool function for log analysis operations.

    Actions:
    - extract_errors: Extract error lines (requires: logs; optional: limit=50)
    - extract_warnings: Extract warning lines (requires: logs; optional: limit=50)
    - identify_patterns: Identify known error patterns (requires: logs)
    - parse_stack_traces: Extract stack traces (requires: logs)
    - analyze_exit_code: Interpret exit code (requires: exit_code)
    - summarize: Create log summary (requires: logs; optional: tail_lines=50)
    - find_repeated: Find repeated error messages (requires: logs; optional: min_occurrences=3)

    Args:
        action: Action to perform
        **kwargs: Action-specific parameters

    Returns:
        String result from the action

    Examples:
        log_tool(action="extract_errors", logs=pod_logs, limit=20)
        log_tool(action="identify_patterns", logs=pod_logs)
        log_tool(action="analyze_exit_code", exit_code=137)
        log_tool(action="summarize", logs=pod_logs)
    """
    analyzer = LogAnalyzer()

    try:
        if action == "extract_errors":
            logs = kwargs.get("logs")
            limit = kwargs.get("limit", 50)
            if logs is None:
                return "ERROR: 'logs' parameter required for extract_errors action"
            return analyzer.extract_errors(logs, limit)

        elif action == "extract_warnings":
            logs = kwargs.get("logs")
            limit = kwargs.get("limit", 50)
            if logs is None:
                return "ERROR: 'logs' parameter required for extract_warnings action"
            return analyzer.extract_warnings(logs, limit)

        elif action == "identify_patterns":
            logs = kwargs.get("logs")
            if logs is None:
                return "ERROR: 'logs' parameter required for identify_patterns action"
            return analyzer.identify_patterns(logs)

        elif action == "parse_stack_traces":
            logs = kwargs.get("logs")
            if logs is None:
                return "ERROR: 'logs' parameter required for parse_stack_traces action"
            return analyzer.parse_stack_traces(logs)

        elif action == "analyze_exit_code":
            exit_code = kwargs.get("exit_code")
            if exit_code is None:
                return "ERROR: 'exit_code' parameter required for analyze_exit_code action"
            return analyzer.analyze_exit_code(int(exit_code))

        elif action == "summarize":
            logs = kwargs.get("logs")
            tail_lines = kwargs.get("tail_lines", 50)
            if logs is None:
                return "ERROR: 'logs' parameter required for summarize action"
            return analyzer.summarize_logs(logs, tail_lines)

        elif action == "find_repeated":
            logs = kwargs.get("logs")
            min_occurrences = kwargs.get("min_occurrences", 3)
            if logs is None:
                return "ERROR: 'logs' parameter required for find_repeated action"
            return analyzer.find_repeated_errors(logs, min_occurrences)

        else:
            return f"ERROR: Unknown action '{action}'. Valid actions: extract_errors, extract_warnings, identify_patterns, parse_stack_traces, analyze_exit_code, summarize, find_repeated"

    except Exception as e:
        logger.exception("Log tool error")
        return f"ERROR: Log tool failed: {e}"


if __name__ == "__main__":
    # Test the tool with sample logs
    print("Testing Log Analyzer Tool")
    print("=" * 60)

    analyzer = LogAnalyzer()

    # Sample logs
    sample_logs = """
2024-10-11 14:30:01 INFO Starting application
2024-10-11 14:30:02 INFO Connecting to database
2024-10-11 14:30:03 ERROR Connection refused: database:5432
2024-10-11 14:30:04 WARNING Retrying connection (attempt 1/3)
2024-10-11 14:30:05 ERROR Connection refused: database:5432
2024-10-11 14:30:06 WARNING Retrying connection (attempt 2/3)
2024-10-11 14:30:07 ERROR Connection refused: database:5432
2024-10-11 14:30:08 ERROR Failed to connect to database after 3 attempts
2024-10-11 14:30:09 FATAL Application startup failed
Traceback (most recent call last):
  File "app.py", line 42, in connect
    conn = database.connect()
  File "database.py", line 15, in connect
    raise ConnectionError("Connection refused")
ConnectionError: Connection refused
"""

    print("\n1. Extracting errors...")
    print(analyzer.extract_errors(sample_logs))

    print("\n2. Identifying patterns...")
    print(analyzer.identify_patterns(sample_logs))

    print("\n3. Parsing stack traces...")
    print(analyzer.parse_stack_traces(sample_logs))

    print("\n4. Finding repeated errors...")
    print(analyzer.find_repeated_errors(sample_logs, min_occurrences=2))

    print("\n5. Analyzing exit code 137...")
    print(analyzer.analyze_exit_code(137))

    print("\n6. Log summary...")
    print(analyzer.summarize_logs(sample_logs))

    print("\n" + "=" * 60)
    print("Testing log_tool function interface")
    print("=" * 60)

    print("\nTest: log_tool(action='extract_errors', ...)")
    print(log_tool(action="extract_errors", logs=sample_logs, limit=5))

    print("\nTest: log_tool(action='analyze_exit_code', exit_code=137)")
    print(log_tool(action="analyze_exit_code", exit_code=137))
