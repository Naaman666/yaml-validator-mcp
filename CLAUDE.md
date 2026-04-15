# CLAUDE.md – yaml-validator-mcp

## Git Workflow

### Branches
- `main` – stable releases only, updated exclusively via PR from `develop`
- `develop` – active development, this is the default target branch

### Rules for Claude

1. **Never push or commit directly to `main`.**
2. All work must be done on a **feature branch** branched off `develop`.
   - Naming pattern: `claude/<short-description>-<id>` (e.g. `claude/add-schema-validation-XYz1`)
3. PRs always target **`develop`**, never `main`.
4. The `develop` → `main` merge is performed manually by the maintainer only.

### Workflow Steps

```
git checkout develop
git pull origin develop
git checkout -b claude/<feature-name>-<id>
# ... work, commits ...
git push -u origin claude/<feature-name>-<id>
# open PR targeting develop
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
