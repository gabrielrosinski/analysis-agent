"""
Custom Tools Package for Kagent DevOps RCA Agent

This package contains custom Python tools that extend the agent's investigation capabilities:
- memory_manager: Read/write agent's persistent knowledge base
- helm_analyzer: Analyze Helm releases and configurations
- log_analyzer: Parse and analyze container logs
- github_api: Fetch commit history and workflow runs

Each tool module exports a main function (e.g., memory_tool, helm_tool, log_tool, github_tool)
that serves as the entry point for the Kagent agent.
"""

__version__ = "0.1.0"

# Import tool functions for easy access
from .memory_manager import memory_tool
from .helm_analyzer import helm_tool
from .log_analyzer import log_tool
from .github_api import github_tool

__all__ = [
    "memory_tool",
    "helm_tool",
    "log_tool",
    "github_tool",
]
