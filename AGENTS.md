# AGENTS.md

This file provides guidance to AI coding agents (e.g. ChatGPT Codex) when working with this repository.

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

- Always work on the `develop` branch.
- Never push/commit directly to `main`.
- Every commit should go to the `develop` branch.
- Only two branches are used: `develop` (active work) and `main` (stable releases).
- Do not create feature branches, topic branches, or any other branches.
