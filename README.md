# yaml-validator-mcp

MCP server for deterministic YAML validation and auto-fixing. AI models see YAML as plain text — they can't parse or detect structural errors. This server provides parser-based validation and automatic formatting that any MCP-compatible client can call.

## Features

- **3-layer validation** (`yaml_validate`): syntax parse (ruamel.yaml, YAML 1.2), lint (yamllint), and optional JSON Schema validation
- **Auto-fix** (`yaml_fix`): normalize indentation, add `---` marker, remove trailing whitespace, preserve comments
- **GitHub Actions linting** (`gha_validate`, optional): wraps [`actionlint`](https://github.com/rhysd/actionlint) for workflow-specific checks (expressions, matrix refs, shellcheck in `run:` blocks) — catches issues YAML-level validation can't see
- **Comment preservation**: ruamel.yaml round-trip keeps all comments intact
- **Structured output**: JSON with `valid`, `syntax_ok`, `errors[]`, `warnings[]`

### What the YAML tools do **not** check

`yaml_validate` and `yaml_fix` are deterministic, offline, YAML-only. By design they do **not**:

- verify that a value exists in the outside world — e.g. a GitHub Action SHA (`uses: actions/checkout@<40-hex>`), a `python-version`, a `runs-on` runner label, a Docker image tag, or a URL. A 40-character hex string is a syntactically valid YAML scalar, so the parser accepts it whether or not the commit actually exists on GitHub.
- perform any network I/O (no GitHub API, no DNS, no registry lookups). This keeps the tools fast, reproducible, and usable offline / in air-gapped CI.
- understand workflow/application semantics — e.g. "does this `needs:` reference point to a real job?", "is this `${{ expression }}` well-formed?", "does this shell command have quoting issues?".

For GitHub Actions workflow files use the complementary **`gha_validate`** tool (see below), which wraps `actionlint` and does catch these Actions-specific problems. For verifying that a pinned action SHA or tag actually exists, use **Renovate** or **Dependabot** — those tools talk to the GitHub API and are designed for that job.

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

To also enable `gha_validate` (GitHub Actions linter), pull in
`actionlint-py` in the same uvx invocation:

```json
{
  "mcpServers": {
    "yaml-validator": {
      "command": "uvx",
      "args": [
        "--with", "actionlint-py",
        "--from", "git+https://github.com/Naaman666/yaml-validator-mcp.git",
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

For `gha_validate` support, add `"--with", "actionlint-py"` to the
`args` array (same pattern as the Claude Code example above).

Restart Antigravity after editing.

## Usage

Once the MCP server is registered and the client is restarted, the LLM
automatically sees the `yaml_validate`, `yaml_fix`, and (if `actionlint`
is available) `gha_validate` tools — you don't need to call them
manually. Just ask in natural language and the model will invoke the
tools when relevant.

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

**GitHub Actions workflow lint (`gha_validate`):**

```
Run gha_validate on every file under .github/workflows/. Report any
errors with file, line, column, rule, and message. If actionlint is
unavailable (available=false), tell me once and stop — don't retry
per file.
```

**Combined validate-and-fix workflow (the everyday prompt):**

```
For every YAML file under .github/ (recursively):

  1. Run yaml_validate with default lint level. Record before:errors,
     before:warnings. If the file is under .github/workflows/, ALSO
     run gha_validate and record before:gha_errors. If the first
     gha_validate call reports available=false, note it once and
     skip gha checks for remaining files (actionlint is not
     installed — only yaml-level checks will run).

  2. If yaml_validate.valid is false, there are any yaml warnings,
     OR gha_validate reports errors:

     a) Run yaml_fix on the file (this auto-handles `---` document
        marker, indentation normalisation, trailing whitespace).

     b) Then apply these GitHub-Actions-friendly manual transforms
        (use Edit, do NOT call yaml_fix again):

        - If a bare `on:` key sits at column 0, quote it as `"on":`
          to silence the YAML 1.1 truthy ambiguity (`on` parses as
          boolean true otherwise).

        - For every `uses: <owner>/<repo>@<40-char-sha> # vX.Y.Z`
          line: hoist the version comment to the line ABOVE as
          `# <owner>/<repo> vX.Y.Z`, leave the `uses:` line bare.
          This fixes both yamllint `comments` (1-space) warnings and
          `line-length` errors caused by SHA + inline comment combos.
          See "Renovate compatibility" below — the hoisted format
          requires a custom regex manager so Renovate can still bump
          the SHA + version together.

        - For any line longer than 80 chars inside a `run: |` shell
          block: break it with backslash continuation (`\`) before a
          natural boundary (`&&`, `||`, `|`, `>`). Indent the
          continuation by +2 spaces. No semantic change.

        - For any remaining inline `# comment` with only 1 space
          before `#` (not `uses:` lines, those were already hoisted):
          add a second space — but only if it does NOT push the line
          over 80 chars. If it would, hoist that comment too.

     c) NOTE: yaml_fix and the manual transforms CANNOT auto-correct
        gha_validate errors (undefined `${{ expressions }}`,
        shellcheck findings in `run:` blocks, unknown step keys,
        matrix typos). Those require human review — they surface in
        step 6.

  3. Run yaml_validate again on the modified content. For workflow
     files, re-run gha_validate too.

  4. Show me a table:
       file | before e/w/g | after e/w/g | action

     where e = yaml errors, w = yaml warnings, g = gha errors (use
     `—` for non-workflow files or when actionlint is unavailable).

     Action is one of:
       - `none`: all counters zero before AND after (already clean)
       - `fixed`: yaml errors=0, yaml warnings=0, gha errors=0 after
         — file written back
       - `partially-fixed`: yaml errors=0 and yaml warnings=0 after,
         but gha errors remain OR yaml issues only partially
         improved — file written back (yaml_fix did its job);
         remaining issues listed in step 6
       - `still-broken`: yaml syntax error remains, or no yaml-level
         improvement at all — file NOT touched

  5. For `fixed` and `partially-fixed`, write the modified content
     back to disk.

  6. For `still-broken` and `partially-fixed`, list the remaining
     issues with line numbers and rule names:
       - yaml errors and warnings (from yaml_validate)
       - gha_validate errors (from actionlint) — these always need
         manual fixing, since yaml_fix cannot alter workflow
         semantics
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

### Renovate compatibility

The combined prompt's manual cleanup hoists `# vX.Y.Z` version
comments from the `uses:` line to the line above:

```yaml
# Before — Renovate's default action-pin updater understands this:
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2

# After the cleanup — Renovate's default updater no longer sees
# the version comment:
# actions/checkout v4.2.2
- uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
```

If you use Renovate, add a `customManagers` entry to your
`renovate.json` so it can still bump SHA + version together for the
hoisted format:

```json
{
  "customManagers": [
    {
      "customType": "regex",
      "fileMatch": ["^\\.github/workflows/[^/]+\\.ya?ml$"],
      "matchStrings": [
        "#\\s+(?<depName>[\\w.-]+/[\\w.-]+)\\s+(?<currentValue>v[\\d.]+[\\w.+-]*)\\s*\\n\\s*(?:-\\s+)?uses:\\s+(?<packageName>[\\w.-]+/[\\w.-]+)@(?<currentDigest>[a-f0-9]{40})"
      ],
      "datasourceTemplate": "github-tags",
      "versioningTemplate": "semver-coerced"
    }
  ]
}
```

The pattern is multiline: it captures the comment line and the
following `uses:` line as one match.

**Dependabot users** need a similar opt-in: Dependabot recognises
inline `# vX.Y.Z` only, and currently has no equivalent
custom-regex hook. Two workarounds: (a) skip the hoisting transform
for repos using Dependabot and rely on a `.yamllint` config relax
instead, or (b) accept manual SHA bumps for hoisted entries.

If future cleanup transforms break other automation tooling, this
section is the place to document the per-tool fix.

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

### `gha_validate`

GitHub Actions workflow linter (wraps [`actionlint`](https://github.com/rhysd/actionlint)). Catches Actions-specific issues that `yaml_validate` cannot see — invalid `${{ expression }}` syntax, undefined `matrix.*` / `needs.*` references, shellcheck findings in `run:` blocks, unknown step keys, malformed step IDs, `workflow_call` input typing, etc.

Like the other tools, this is **deterministic and offline** — it does not hit the GitHub API, so it cannot tell you whether a pinned action SHA actually exists on GitHub. Use Renovate/Dependabot for that.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content` | str | Yes | Raw workflow YAML (content of a file under `.github/workflows/`) |

**Requires** the `actionlint` binary in `PATH`. Install one of:

```bash
pip install actionlint-py        # bundles the binary, cross-platform
# or
brew install actionlint           # macOS
# or
go install github.com/rhysd/actionlint/cmd/actionlint@latest
```

Or install this package with the `gha` extra to pull in `actionlint-py`:

```bash
pip install "yaml-validator-mcp[gha] @ git+https://github.com/Naaman666/yaml-validator-mcp.git"
# or with uvx — either syntax works:
uvx --with actionlint-py --from git+https://github.com/Naaman666/yaml-validator-mcp.git yaml-validator-mcp
uvx --from "yaml-validator-mcp[gha] @ git+https://github.com/Naaman666/yaml-validator-mcp.git" yaml-validator-mcp
```

**Example output (clean workflow):**

```json
{
  "valid": true,
  "syntax_ok": true,
  "available": true,
  "errors": [],
  "tool_error": null
}
```

**Example output (undefined matrix reference):**

```json
{
  "valid": false,
  "syntax_ok": true,
  "available": true,
  "errors": [
    {"line": 10, "column": 23, "message": "property \"does-not-exist\" is not defined in object type {}", "rule": "expression"}
  ],
  "tool_error": null
}
```

If `actionlint` is not installed, `available` is `false`, `tool_error` contains install instructions, and `valid` stays `true` (a missing linter is a capability gap, not a lint failure — branch on `available`/`tool_error` in the client).

## Development

```bash
# Install with dev dependencies (includes actionlint-py for gha_validate tests)
pip install -e ".[dev]"

# Run tests
pytest --cov=server --cov-report=term-missing -v

# Type check
mypy --strict server.py

# Lint YAML fixtures
yamllint tests/fixtures/valid/
```

## Reliability and scope

These tools are **deterministic parsers and linters**, not probabilistic
detectors. There is no heuristic, no ML, no LLM reasoning inside. That
shapes how you should think about reliability:

- **Within the configured scope, the false-negative / false-positive
  rate is effectively zero.** The underlying engines — ruamel.yaml
  (YAML 1.2 parser), yamllint (rule-based linter), jsonschema (Draft 7),
  and actionlint — are mature, widely deployed projects. If you hit a
  genuine in-scope miss or a spurious match, it is almost always an
  upstream bug reproducible with a one-line YAML example; report it
  to the relevant project (yamllint, actionlint, jsonschema), not here.

- **"Pass" is not "correct".** A clean `valid: true` result means
  *"no rule in the applied ruleset matched anything in this file"*.
  It does **not** mean "this YAML does what you intend" or "this
  workflow is safe to run". Application-level correctness (is the
  `needs:` graph right? does the `if:` condition match your intent?
  will the shell command do the right thing for your data?) is out
  of scope — there is no model here that understands your intent.

- **Detection coverage ≠ fix coverage.** `yaml_fix` only automatically
  corrects a *strict subset* of what `yaml_validate` detects. The
  combined prompt documents the remaining manual transforms (`on:`
  quoting, `uses:` hoisting, shell line breaks, comment spacing).
  A summary of the most common issues:

  | Issue | `yaml_validate` detects? | `yaml_fix` auto-fixes? |
  |---|:---:|:---:|
  | Tab indentation | ✅ | ✅ (ruamel round-trip) |
  | Missing `---` marker | ✅ | ✅ |
  | Trailing whitespace | ✅ | ✅ |
  | Wrong indent width | ✅ | ✅ |
  | `on:` truthy warning | ✅ | ❌ (manual) |
  | `line-length` > 80 | ✅ | ❌ (manual) |
  | Inline-comment 1-space | ✅ | ❌ (manual) |
  | Undefined `${{ matrix.x }}` | ❌ (`gha_validate`) | ❌ |
  | Shellcheck finding in `run:` | ❌ (`gha_validate`) | ❌ |
  | Non-existent action SHA | ❌ (Renovate / Dependabot) | ❌ |
  | Missing required key | only with JSON Schema | ❌ |

- **Out-of-scope gaps are listed upfront** in [*What the YAML tools
  do **not** check*](#what-the-yaml-tools-do-not-check) at the top of
  this README. If something important to your workflow is in that
  list, pair this MCP with the tool named there (`gha_validate`,
  Renovate, Dependabot, JSON Schema).

**Bottom line:** think of this MCP as a precise ruler, not a smart
reviewer. It reliably measures the things it was built to measure,
and honestly reports nothing about the things it wasn't.

## License

MIT
