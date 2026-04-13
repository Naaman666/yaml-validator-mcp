# yaml-validator-mcp

*[Magyar verzió / Hungarian version](README.hu.md)*

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

You have two options to register the MCP server.

**Option A — CLI (recommended):** run one command from any shell. This edits the right config file for you.

```bash
# User scope (available in every project on your machine)
claude mcp add yaml-validator -s user -- uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp

# or project scope (committed to .mcp.json in the current repo — shared with your team)
claude mcp add yaml-validator -s project -- uvx --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp
```

Verify:
```bash
claude mcp list
```

**Option B — edit the config file by hand:**

- **User-scoped config** (applies to all projects): `~/.claude.json`
  - Windows: `C:\Users\<YourName>\.claude.json`
  - macOS / Linux: `~/.claude.json`
- **Project-scoped config** (per-repo, commit to git): `.mcp.json` in the project root.

Open the file (create it if it does not exist) and add the `mcpServers` block below. If the file already has other content, merge the `mcpServers` key into the existing JSON object — do not overwrite the whole file.

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

Restart Claude Code after editing.

### Antigravity

Open the config via the UI: **Agent pane → additional options menu → MCP Servers → Manage MCP Servers → View raw config**.

Or edit the file directly:

- **Windows:** `%USERPROFILE%\.gemini\antigravity\mcp_config.json`
- **macOS / Linux:** `~/.gemini/antigravity/mcp_config.json`

Add (or merge) the `mcpServers` block:

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

Restart Antigravity after editing.

## Usage

Once the MCP server is registered and the client is restarted, the LLM
automatically sees the `yaml_validate` and `yaml_fix` tools — you don't
need to call them manually. Just ask in natural language and the model
will invoke the tools when relevant.

### Typical workflow

1. Open Claude Code (or Antigravity) in the repo whose YAML files you
   want to check.
2. Ask in plain text what you want to do.
3. On first tool call the client asks permission to run the MCP tool —
   approve it.
4. The model reads the file(s), passes the content to the MCP tool, and
   reports the structured result back to you.

### Example prompts

**Validate all workflow files in a repo:**

```
Check every YAML file under .github/workflows/ using the yaml-validator MCP.
List errors per file with line numbers.
```

**Auto-fix a single file and save it back:**

```
Run yaml_fix on .github/workflows/deploy.yml, show me the diff,
and if it looks good, write the fixed content back to the file.
```

**Batch auto-fix (fix all workflow files, show diffs, save only if no regressions):**

```
For every YAML file under .github/workflows/, run yaml_fix. For each file
show me a unified diff and the post-fix validation result. Only write the
file back if validation.valid is true and the diff is non-empty.
```

**Dry-run fix (preview only, never save):**

```
Run yaml_fix on docker-compose.yml but do NOT write anything. Just show me
the fixed_content and the validation block.
```

**Fix then re-validate with a stricter lint level:**

```
Run yaml_fix on .github/workflows/ci.yml, then run yaml_validate on the
fixed content with lint_level="default". Report remaining warnings so I
know what the fixer could not auto-correct (e.g. truthy keys).
```

**Combined validate-and-fix workflow (the everyday prompt):**

```
For every YAML file under .github/ (recursively):
  1. Run yaml_validate with default lint level.
  2. If valid is false OR there are warnings, run yaml_fix on it.
  3. Show me a table: file | before:errors | before:warnings |
     after:errors | after:warnings | action (none/fixed/still-broken).
  4. For files where yaml_fix reduced errors or warnings to 0, write the
     fixed_content back. For anything still broken, list the remaining
     problems with line numbers — do NOT overwrite those files.
```

**Summary table across many files:**

```
List every YAML file under .github/, run yaml_validate (default lint level)
on each, and give me a table: file | valid | errors | warnings.
```

**Relaxed lint level (fewer style complaints):**

```
Validate docker-compose.yml with yaml-validator using lint_level="relaxed".
```

**JSON Schema validation (e.g. GitHub Actions schema):**

```
Fetch the official GitHub Actions workflow JSON Schema and run yaml_validate
on .github/workflows/ci.yml with that schema. Report any structural errors.
```

### Tips

- You don't have to name the tool in every sentence — *"check my workflow
  YAMLs for errors"* is enough; the model figures out that it needs
  `yaml_validate`.
- You **can** name it explicitly (`"use the yaml-validator MCP"`) when
  multiple similar tools are registered — this removes ambiguity.
- The first call shows a permission prompt. You can pre-approve the
  server in Claude Code settings if you use it often.
- For bulk operations, ask the model to **list files first**, then run
  the tool in a loop and present a table — this keeps the interaction
  tidy.

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
