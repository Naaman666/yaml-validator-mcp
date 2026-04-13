# yaml-validator-mcp

MCP server for deterministic YAML validation and auto-fixing. AI models see YAML as plain text — they can't parse or detect structural errors. This server provides parser-based validation and automatic formatting that any MCP-compatible client can call.

## Features

- **3-layer validation** (`yaml_validate`): syntax parse (ruamel.yaml, YAML 1.2), lint (yamllint), and optional JSON Schema validation
- **Auto-fix** (`yaml_fix`): normalize indentation, add `---` marker, remove trailing whitespace, preserve comments
- **Comment preservation**: ruamel.yaml round-trip keeps all comments intact
- **Structured output**: JSON with `valid`, `syntax_ok`, `errors[]`, `warnings[]`

## Installation

> **Note:** This package is not yet published to PyPI. Install it directly from GitHub using one of the methods below.

### Prerequisite: install `uv` (provides the `uvx` command)

`uvx` ships with [`uv`](https://docs.astral.sh/uv/). If you see
`The term 'uvx' is not recognized...`, install `uv` first:

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```
or
```powershell
winget install --id=astral-sh.uv -e
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Any platform (via pip):**
```bash
pip install uv
```

After installing, restart your terminal so `uvx` is on `PATH`.

### Run with uvx (recommended, from GitHub)

```bash
uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp
```

### Install with pip (from GitHub)

```bash
pip install git+https://github.com/Naaman666/yaml-validator-mcp.git
```

Then run:

```bash
yaml-validator-mcp
```

### Install from a local clone

```bash
git clone https://github.com/Naaman666/yaml-validator-mcp.git
cd yaml-validator-mcp
pip install .
```

## Configuration

### Claude Code

Add to your Claude Code MCP config:

```json
{
  "mcpServers": {
    "yaml-validator": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Naaman666/yaml-validator-mcp.git",
        "yaml-validator-mcp"
      ]
    }
  }
}
```

### Antigravity

```json
{
  "mcpServers": {
    "yaml-validator": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Naaman666/yaml-validator-mcp.git",
        "yaml-validator-mcp"
      ],
      "transport": "stdio"
    }
  }
}
```

## Tools

### `yaml_validate`

Three-layer deterministic validation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Raw YAML string |
| `lint_level` | str | No | `"default"` / `"relaxed"` / raw yamllint config string |
| `schema` | dict | No | JSON Schema for structure validation |

**Example output:**

```json
{
  "valid": false,
  "syntax_ok": true,
  "errors": [
    {"line": 3, "column": 5, "message": "wrong indentation: expected 2 but found 4", "rule": "indentation"}
  ],
  "warnings": []
}
```

### `yaml_fix`

Auto-fix YAML with comment preservation. Post-fix validation runs automatically.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Raw YAML string |
| `lint_level` | str | No | Post-fix lint level |
| `schema` | dict | No | Post-fix schema validation |

**Example output:**

```json
{
  "fixed_content": "---\nname: test\nvalue: 1\n",
  "fix_error": null,
  "validation": {
    "valid": true,
    "syntax_ok": true,
    "errors": [],
    "warnings": []
  }
}
```

If the input is unparseable, `fix_error` contains the error message and `fixed_content` returns the original input unchanged.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest --cov=server --cov-report=term-missing -v

# Type check
mypy --strict server.py

# Lint YAML fixtures
yamllint tests/fixtures/valid/
```

## License

MIT
