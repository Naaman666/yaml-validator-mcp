"""yaml-validator-mcp: MCP server for deterministic YAML validation and auto-fixing."""

from __future__ import annotations

import io
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import jsonschema
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from yamllint import linter as yamllint_linter
from yamllint.config import YamlLintConfig


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _parse_yaml(content: str) -> tuple[Any, str | None]:
    """Parse YAML content with ruamel.yaml (YAML 1.2).

    Returns (parsed_data, error_message).  On success error_message is None.
    Multi-document YAML is supported: returns a list of documents.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    try:
        # Try multi-document load first to handle `---` separated docs
        docs = list(yaml.load_all(content))
        if len(docs) <= 1:
            return docs[0] if docs else None, None
        return docs, None
    except YAMLError as exc:
        return None, str(exc)


def _build_yamllint_config(lint_level: str) -> YamlLintConfig:
    """Build a YamlLintConfig from a lint level string.

    Raises ValueError with an actionable message on invalid config.
    """
    if lint_level in ("default", "relaxed"):
        return YamlLintConfig(f"extends: {lint_level}")
    # Treat as raw yamllint config string
    try:
        return YamlLintConfig(lint_level)
    except Exception as exc:
        raise ValueError(
            f"Invalid yamllint config string: {exc}. "
            "Use 'default', 'relaxed', or a valid yamllint YAML config string "
            "(e.g. 'extends: default\\nrules:\\n  line-length: disable')."
        ) from exc


def _run_yamllint(
    content: str, lint_level: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
    """Run yamllint on content.

    Returns (errors, warnings, config_error).
    If config_error is not None, errors/warnings will be empty and
    config_error contains an actionable message.
    """
    try:
        config = _build_yamllint_config(lint_level)
    except ValueError as exc:
        return [], [], str(exc)

    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for problem in yamllint_linter.run(content, config):
        entry: dict[str, Any] = {
            "line": problem.line,
            "column": problem.column,
            "message": problem.message,
            "rule": problem.rule,
        }
        if problem.level == "error":
            errors.append(entry)
        else:
            warnings.append(entry)

    return errors, warnings, None


def _validate_schema(
    data: Any, schema: dict[str, Any]
) -> list[dict[str, Any]]:
    """Validate parsed YAML data against a JSON Schema (Draft 7).

    Returns a list of schema validation errors.
    """
    validator = jsonschema.Draft7Validator(schema)
    errors: list[dict[str, Any]] = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        errors.append({
            "path": list(error.path),
            "message": error.message,
            "schema_path": list(error.schema_path),
        })
    return errors


def _run_actionlint(content: str) -> dict[str, Any]:
    """Run actionlint on a GitHub Actions workflow YAML string.

    Returns a dict with keys:
      available (bool): whether the actionlint binary was found in PATH
      errors (list): each entry has line, column, message, rule
      tool_error (str|None): message if actionlint could not be executed
    """
    binary = shutil.which("actionlint")
    if binary is None:
        return {
            "available": False,
            "errors": [],
            "tool_error": (
                "actionlint binary not found in PATH. Install one of: "
                "'pip install actionlint-py' (bundles the binary, cross-platform), "
                "'go install github.com/rhysd/actionlint/cmd/actionlint@latest', "
                "'brew install actionlint' (macOS), or download a release from "
                "https://github.com/rhysd/actionlint/releases."
            ),
        }

    # actionlint only recognises files placed under .github/workflows/,
    # so build that directory structure inside a tempdir.
    with tempfile.TemporaryDirectory() as tmp:
        wf_dir = Path(tmp) / ".github" / "workflows"
        wf_dir.mkdir(parents=True)
        wf_file = wf_dir / "workflow.yml"
        wf_file.write_text(content, encoding="utf-8")

        try:
            proc = subprocess.run(
                [binary, "-format", "{{json .}}", str(wf_file)],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return {
                "available": True,
                "errors": [],
                "tool_error": f"actionlint execution failed: {exc}",
            }

        raw = proc.stdout.strip() or "[]"
        try:
            items = json.loads(raw)
        except json.JSONDecodeError as exc:
            return {
                "available": True,
                "errors": [],
                "tool_error": (
                    f"actionlint returned invalid JSON: {exc}. "
                    f"Stderr: {proc.stderr.strip()[:500]}"
                ),
            }

        errors: list[dict[str, Any]] = []
        for item in items:
            errors.append({
                "line": item.get("line"),
                "column": item.get("column"),
                "message": item.get("message", ""),
                "rule": item.get("kind", "actionlint"),
            })

        return {
            "available": True,
            "errors": errors,
            "tool_error": None,
        }


def _fix_yaml(content: str) -> tuple[str, str | None]:
    """Fix YAML content using ruamel.yaml round-trip.

    Returns (fixed_content, fix_error).
    If fix_error is not None, fixed_content is the original content.
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096

    try:
        data = yaml.load(content)
    except YAMLError as exc:
        return content, str(exc)

    # Ensure document-start marker
    yaml.explicit_start = True

    buf = io.StringIO()
    try:
        yaml.dump(data, buf)
    except YAMLError as exc:
        return content, str(exc)

    fixed = buf.getvalue()

    # Remove trailing whitespace from each line
    fixed = "\n".join(line.rstrip() for line in fixed.splitlines())
    if fixed and not fixed.endswith("\n"):
        fixed += "\n"

    return fixed, None


# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    name="yaml-validator",
    instructions=(
        "YAML validation and auto-fix server. Use yaml_validate to check YAML "
        "syntax, lint rules, and schema conformance. Use yaml_fix to auto-format "
        "YAML with comment preservation. Use gha_validate for GitHub Actions "
        "workflow-specific checks (expressions, matrix refs, shellcheck in run "
        "blocks) — it requires the `actionlint` binary in PATH."
    ),
)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def yaml_validate(
    content: str,
    lint_level: str = "default",
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate a YAML string with three layers: syntax parse, yamllint, and optional JSON Schema.

    Args:
        content: Raw YAML string to validate.
        lint_level: 'default', 'relaxed', or a raw yamllint config string.
        schema: Optional JSON Schema dict for structure validation.

    Returns a dict with keys: valid, syntax_ok, errors, warnings.
    """
    result: dict[str, Any] = {
        "valid": True,
        "syntax_ok": True,
        "errors": [],
        "warnings": [],
    }

    # Layer 1: Syntax parse
    parsed, syntax_error = _parse_yaml(content)
    if syntax_error is not None:
        result["valid"] = False
        result["syntax_ok"] = False
        result["errors"].append({
            "line": None,
            "column": None,
            "message": syntax_error,
            "rule": "syntax",
        })
        # Early return – don't run lint or schema on broken YAML
        return result

    # Layer 2: Lint
    lint_errors, lint_warnings, config_error = _run_yamllint(content, lint_level)
    if config_error is not None:
        result["valid"] = False
        result["errors"].append({
            "line": None,
            "column": None,
            "message": config_error,
            "rule": "yamllint-config",
        })
        return result

    if lint_errors:
        result["valid"] = False
    result["errors"].extend(lint_errors)
    result["warnings"].extend(lint_warnings)

    # Layer 3: Schema validation (optional)
    if schema is not None:
        schema_errors = _validate_schema(parsed, schema)
        if schema_errors:
            result["valid"] = False
            for err in schema_errors:
                result["errors"].append({
                    "line": None,
                    "column": None,
                    "message": err["message"],
                    "rule": "schema",
                    "path": err["path"],
                    "schema_path": err["schema_path"],
                })

    return result


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def yaml_fix(
    content: str,
    lint_level: str = "default",
    schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Auto-fix a YAML string: normalize indentation, add document-start marker, remove trailing whitespace, and preserve comments.

    Args:
        content: Raw YAML string to fix.
        lint_level: Post-fix lint level for validation.
        schema: Optional JSON Schema dict for post-fix validation.

    Returns a dict with keys: fixed_content, fix_error, validation.
    """
    fixed_content, fix_error = _fix_yaml(content)

    if fix_error is not None:
        return {
            "fixed_content": fixed_content,
            "fix_error": fix_error,
            "validation": None,
        }

    # Post-fix validation
    validation = yaml_validate(fixed_content, lint_level=lint_level, schema=schema)

    return {
        "fixed_content": fixed_content,
        "fix_error": None,
        "validation": validation,
    }


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def gha_validate(content: str) -> dict[str, Any]:
    """Validate a GitHub Actions workflow YAML using actionlint.

    Complements yaml_validate: catches Actions-specific issues that neither
    YAML parsing nor yamllint can see — invalid ``${{ expression }}`` syntax,
    undefined matrix/needs references, shellcheck findings in ``run:`` blocks,
    unknown step keys, malformed step IDs, workflow_call input typing, etc.

    Deterministic and offline: does NOT perform any network lookup. This
    means it does NOT verify that an action's SHA or tag actually exists on
    GitHub — use Renovate or Dependabot for that.

    Args:
        content: Raw workflow YAML string (contents of a file under
            ``.github/workflows/``).

    Returns a dict with keys:
        valid (bool): True if no errors from actionlint (and YAML parses).
            When ``available`` is False, ``valid`` is True — the missing
            tool is reported via ``tool_error`` rather than treated as an
            error, mirroring how ``yaml_validate`` treats a missing schema.
        syntax_ok (bool): whether YAML itself parsed cleanly.
        available (bool): whether actionlint was found and executable.
        errors (list): each entry has line, column, message, rule.
        tool_error (str|None): actionable message if actionlint could not
            be invoked (not installed, timed out, bad JSON, etc.).
    """
    result: dict[str, Any] = {
        "valid": True,
        "syntax_ok": True,
        "available": True,
        "errors": [],
        "tool_error": None,
    }

    # YAML parse first: gives a cleaner error than actionlint's own parser,
    # and matches the layered style of yaml_validate.
    _, syntax_error = _parse_yaml(content)
    if syntax_error is not None:
        result["valid"] = False
        result["syntax_ok"] = False
        result["errors"].append({
            "line": None,
            "column": None,
            "message": syntax_error,
            "rule": "syntax",
        })
        return result

    al = _run_actionlint(content)
    result["available"] = al["available"]
    result["tool_error"] = al["tool_error"]

    if al["tool_error"] is not None:
        # Linter unavailable or failed to run: we can't make a verdict, but
        # the YAML itself parsed. Keep valid=True so callers can distinguish
        # "clean under actionlint" from "linter unavailable"; the client
        # should branch on `available` / `tool_error`.
        return result

    result["errors"].extend(al["errors"])
    if al["errors"]:
        result["valid"] = False

    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
