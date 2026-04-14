# CLAUDE.md

This file provides guidance to Claude when working with this repository.

## Project Overview

Describe the project purpose and goals here.

## Development Setup

```bash
# Install dependencies
npm install
# or
pip install -r requirements.txt
```

## Common Commands

```bash
# Run tests
npm test
# or
pytest

# Lint / format
npm run lint
# or
ruff check .
```

## Code Style

- Follow the existing patterns and conventions in the codebase.
- Keep functions small and focused on a single responsibility.
- Write clear, self-documenting code; only add comments where the logic is non-obvious.
- Do not add unnecessary error handling, logging, or abstractions.

## Architecture Notes

Describe key architectural decisions and important modules here.

## Git Workflow

- Always work on the `develop` branch.
- Never push/commit directly to `main`.
- Every commit should go to the `develop` branch.
