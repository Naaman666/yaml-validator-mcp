"""yaml-validator-mcp: MCP server for deterministic YAML validation and auto-fixing."""

from __future__ import annotations

import io
from typing import Any

import jsonschema
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError
from yamllint import linter as yamllint_linter
from yamllint.config import YamlLintConfig


# ---------------------------------------------------------------------------
# Pydantic input models
# ---------------------------------------------------------------------------

class ValidateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., description="Raw YAML string to validate")
    lint_level: str = Field(
        default="default",
        description=(
            "Lint strictness: 'default', 'relaxed', or a raw yamllint "
            "config string (e.g. 'extends: default\\nrules:\\n  line-length: disable')"
        ),
    )
    schema_: dict[str, Any] | None = Field(
        default=None,
        alias="schema",
        description="Optional JSON Schema dict for structure validation",
    )


class FixInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(..., description="Raw YAML string to fix")
    lint_level: str = Field(
        default="default",
        description="Post-fix lint level (same options as yaml_validate)",
    )
    schema_: dict[str, Any] | None = Field(
        default=None,
        alias="schema",
        description="Optional JSON Schema dict for post-fix structure validation",
    )


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
        "YAML with comment preservation."
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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Entry point for the MCP server (stdio transport)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
