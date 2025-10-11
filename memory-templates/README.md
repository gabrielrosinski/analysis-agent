# Agent Memory Templates

This directory contains template markdown files that will be copied to the agent's persistent memory volume during initialization.

## Purpose

These templates provide the initial structure for the agent's knowledge base. The agent will read and update these files during incident investigations to build institutional knowledge over time.

## Files

- **discovered-tools.md** - Catalog of DevOps tools and services found in the cluster
- **known-issues.md** - Library of previously encountered issue patterns and solutions
- **github-repos.md** - Linked GitHub repositories and their workflows
- **helm-charts.md** - Deployed Helm releases and their configurations
- **namespace-map.md** - Cluster namespace topology and purpose

## Usage

These files are copied to `/agent-memory/` on the PersistentVolume during initialization via the `scripts/init-memory.sh` script.

The agent will:
1. Read these files at the start of each investigation
2. Update them with new discoveries
3. Reference them to detect patterns and provide better solutions

## Maintenance

- Templates should be kept simple and well-structured
- Use markdown formatting for easy readability
- Include clear section headers for agent parsing
- Update templates as the system evolves
