# yaml-validator-mcp

MCP server for deterministic YAML validation and auto-fixing. AI models see YAML as plain text — they can't parse or detect structural errors. This server provides parser-based validation and automatic formatting that any MCP-compatible client can call.

## Features

- **3-layer validation** (`yaml_validate`): syntax parse (ruamel.yaml, YAML 1.2), lint (yamllint), and optional JSON Schema validation
- **Auto-fix** (`yaml_fix`): normalize indentation, add `---` marker, remove trailing whitespace, preserve comments
- **Comment preservation**: ruamel.yaml round-trip keeps all comments intact
- **Structured output**: JSON with `valid`, `syntax_ok`, `errors[]`, `warnings[]`

## Installation

# With uvx (recommended)
```bash
uvx yaml-validator-mcp
```

# With pip
```bash
pip install yaml-validator-mcp
```

## Configuration

### Claude Code

Add to your Claude Code MCP config:

```json
{
  "mcpServers": {
    "yaml-validator": {
      "command": "uvx",
      "args": ["yaml-validator-mcp"]
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
      "args": ["yaml-validator-mcp"],
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
