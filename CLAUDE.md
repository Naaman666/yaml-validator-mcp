# CLAUDE.md – yaml-validator-mcp

## Git Workflow

### Rules for Claude

1. **Never push or commit directly to `main`.**
2. All work must be done on a **feature branch** branched off `main`.
   - Naming pattern: `claude/<short-description>-<id>` (e.g. `claude/add-schema-validation-XYz1`)
3. PRs always target **`main`**.

### Workflow Steps

```
git checkout main
git pull origin main
git checkout -b claude/<feature-name>-<id>
# ... work, commits ...
git push -u origin claude/<feature-name>-<id>
# open PR targeting main
```

## Project

- **Language:** Python 3.11+
- **Tests:** `pytest` (58 tests, 95% coverage)
- **Type checking:** `mypy --strict`
- **Lint:** `yamllint`, `actionlint`

## Code Style

- Follow the existing patterns and conventions in the codebase.
- Keep functions small and focused on a single responsibility.
- Write clear, self-documenting code; only add comments where the logic is non-obvious.
- Do not add unnecessary error handling, logging, or abstractions.
