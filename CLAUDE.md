# CLAUDE.md – yaml-validator-mcp

This file provides guidance to Claude when working with this repository.

## Project Overview

A Model Context Protocol (MCP) server that validates YAML files. Exposes validation tools for use by AI assistants and other MCP clients.

## Development Setup

```bash
pip install -e .[dev]
```

## Common Commands

```bash
# Run tests
pytest

# Type checking
mypy --strict server.py

# Lint
yamllint .
actionlint
```

## Code Style

- Language: Python 3.11+
- Tests: `pytest` (~95% coverage)
- Type checking: `mypy --strict`
- Lint: `yamllint`, `actionlint`
- Follow the existing patterns and conventions in the codebase.
- Keep functions small and focused on a single responsibility.
- Write clear, self-documenting code; only add comments where the logic is non-obvious.
- Do not add unnecessary error handling, logging, or abstractions.

## Git Workflow

Only two persistent branches exist: `develop` (active work) and `main` (stable releases).

- **Humans:** always commit directly to `develop`. Never commit or push to `main`. Do not create feature or topic branches.
- **AI agents (Claude, Codex, etc.):** open pull requests from a short-lived `claude/*` or `codex/*` branch. The PR must always target `develop`, never `main`. The branch is deleted after merge.
