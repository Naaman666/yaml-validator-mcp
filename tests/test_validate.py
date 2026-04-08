"""Tests for the yaml_validate tool."""

from __future__ import annotations

from pathlib import Path

from server import yaml_validate

FIXTURES = Path(__file__).parent / "fixtures"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Valid YAML files
# ---------------------------------------------------------------------------


class TestValidYaml:
    def test_simple(self) -> None:
        result = yaml_validate(_read(FIXTURES / "valid" / "simple.yaml"))
        assert result["valid"] is True
        assert result["syntax_ok"] is True
        assert result["errors"] == []

    def test_nested(self) -> None:
        result = yaml_validate(_read(FIXTURES / "valid" / "nested.yaml"))
        assert result["valid"] is True
        assert result["syntax_ok"] is True

    def test_list(self) -> None:
        result = yaml_validate(_read(FIXTURES / "valid" / "list.yaml"))
        assert result["valid"] is True

    def test_multiline_block_scalar(self) -> None:
        result = yaml_validate(_read(FIXTURES / "valid" / "multiline.yaml"))
        assert result["valid"] is True

    def test_anchors(self) -> None:
        result = yaml_validate(_read(FIXTURES / "valid" / "anchors.yaml"))
        assert result["valid"] is True

    def test_unicode(self) -> None:
        result = yaml_validate(_read(FIXTURES / "valid" / "unicode.yaml"))
        assert result["valid"] is True

    def test_multi_document(self) -> None:
        """Multi-doc YAML is valid syntax."""
        content = _read(FIXTURES / "valid" / "multi_doc.yaml")
        result = yaml_validate(content, lint_level="relaxed")
        assert result["syntax_ok"] is True
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Syntax errors – early return, no lint/schema
# ---------------------------------------------------------------------------


class TestSyntaxErrors:
    def test_tab_indent(self) -> None:
        result = yaml_validate(_read(FIXTURES / "invalid" / "tab_indent.yaml"))
        assert result["valid"] is False
        assert result["syntax_ok"] is False
        assert len(result["errors"]) >= 1
        assert result["errors"][0]["rule"] == "syntax"

    def test_unmatched_quote(self) -> None:
        result = yaml_validate(_read(FIXTURES / "invalid" / "unmatched_quote.yaml"))
        assert result["valid"] is False
        assert result["syntax_ok"] is False

    def test_invalid_key_char(self) -> None:
        content = _read(FIXTURES / "invalid" / "invalid_key_char.yaml")
        result = yaml_validate(content)
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# Lint errors (default config)
# ---------------------------------------------------------------------------


class TestLintErrors:
    def test_bad_indent(self) -> None:
        result = yaml_validate(_read(FIXTURES / "invalid" / "bad_indent.yaml"))
        assert result["syntax_ok"] is True
        assert result["valid"] is False
        lint_rules = [e["rule"] for e in result["errors"]]
        assert "indentation" in lint_rules

    def test_trailing_whitespace(self) -> None:
        result = yaml_validate(_read(FIXTURES / "invalid" / "trailing_whitespace.yaml"))
        assert result["syntax_ok"] is True
        assert result["valid"] is False
        lint_rules = [e["rule"] for e in result["errors"]]
        assert "trailing-spaces" in lint_rules

    def test_no_doc_start(self) -> None:
        result = yaml_validate(_read(FIXTURES / "invalid" / "no_doc_start.yaml"))
        assert result["syntax_ok"] is True
        # document-start may be warning or error depending on yamllint config
        all_rules = (
            [e["rule"] for e in result["errors"]]
            + [w["rule"] for w in result["warnings"]]
        )
        assert "document-start" in all_rules

    def test_long_lines(self) -> None:
        result = yaml_validate(_read(FIXTURES / "invalid" / "long_lines.yaml"))
        assert result["syntax_ok"] is True
        # Default config has line-length rule
        rules = [e["rule"] for e in result["errors"]] + [w["rule"] for w in result["warnings"]]
        assert "line-length" in rules


# ---------------------------------------------------------------------------
# Lint levels
# ---------------------------------------------------------------------------


class TestLintLevels:
    def test_relaxed_allows_more(self) -> None:
        """Relaxed config should allow things default doesn't."""
        content = _read(FIXTURES / "invalid" / "no_doc_start.yaml")
        strict_result = yaml_validate(content, lint_level="default")
        relaxed_result = yaml_validate(content, lint_level="relaxed")
        # Relaxed should have fewer or equal errors
        assert len(relaxed_result["errors"]) <= len(strict_result["errors"])

    def test_custom_config_string(self) -> None:
        """A raw yamllint config string should work."""
        content = _read(FIXTURES / "invalid" / "no_doc_start.yaml")
        custom_config = "extends: default\nrules:\n  document-start: disable"
        result = yaml_validate(content, lint_level=custom_config)
        assert result["syntax_ok"] is True
        lint_rules = [e["rule"] for e in result["errors"]]
        assert "document-start" not in lint_rules

    def test_invalid_config_string(self) -> None:
        """Invalid yamllint config should return actionable error."""
        result = yaml_validate("---\nkey: value\n", lint_level="not: valid: config: {{{}}")
        assert result["valid"] is False
        assert len(result["errors"]) >= 1
        assert result["errors"][0]["rule"] == "yamllint-config"
        assert "Invalid yamllint config" in result["errors"][0]["message"]


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    SIMPLE_SCHEMA: dict = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "version": {"type": "integer"},
        },
        "required": ["name", "version"],
    }

    def test_valid_schema(self) -> None:
        content = "---\nname: test\nversion: 1\n"
        result = yaml_validate(content, schema=self.SIMPLE_SCHEMA)
        assert result["valid"] is True

    def test_invalid_schema_missing_field(self) -> None:
        content = "---\nname: test\n"
        result = yaml_validate(content, schema=self.SIMPLE_SCHEMA)
        assert result["valid"] is False
        schema_errors = [e for e in result["errors"] if e["rule"] == "schema"]
        assert len(schema_errors) >= 1
        assert "version" in schema_errors[0]["message"]

    def test_invalid_schema_wrong_type(self) -> None:
        content = "---\nname: test\nversion: not_a_number\n"
        result = yaml_validate(content, schema=self.SIMPLE_SCHEMA)
        assert result["valid"] is False
        schema_errors = [e for e in result["errors"] if e["rule"] == "schema"]
        assert len(schema_errors) >= 1

    def test_no_schema_skips_validation(self) -> None:
        """Without schema, only syntax+lint run."""
        content = "---\nfoo: bar\n"
        result = yaml_validate(content)
        assert result["valid"] is True
        schema_errors = [e for e in result["errors"] if e["rule"] == "schema"]
        assert schema_errors == []

    def test_syntax_error_skips_schema(self) -> None:
        """Syntax error causes early return – schema is never checked."""
        content = "---\nkey: \"unmatched\nvalue: 1\n"
        result = yaml_validate(content, schema=self.SIMPLE_SCHEMA)
        assert result["valid"] is False
        assert result["syntax_ok"] is False
        schema_errors = [e for e in result["errors"] if e["rule"] == "schema"]
        assert schema_errors == []


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_file(self) -> None:
        result = yaml_validate("")
        assert result["syntax_ok"] is True

    def test_only_comments(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "only_comments.yaml")
        result = yaml_validate(content, lint_level="relaxed")
        assert result["syntax_ok"] is True

    def test_null_values(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "null_values.yaml")
        result = yaml_validate(content)
        assert result["syntax_ok"] is True
        assert result["valid"] is True

    def test_deep_nested(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "deep_nested.yaml")
        result = yaml_validate(content)
        assert result["valid"] is True

    def test_with_comments(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "with_comments.yaml")
        result = yaml_validate(content)
        assert result["valid"] is True


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------


class TestOutputStructure:
    def test_valid_output_has_all_keys(self) -> None:
        result = yaml_validate("---\nkey: value\n")
        assert "valid" in result
        assert "syntax_ok" in result
        assert "errors" in result
        assert "warnings" in result

    def test_errors_have_expected_shape(self) -> None:
        result = yaml_validate(_read(FIXTURES / "invalid" / "bad_indent.yaml"))
        for error in result["errors"]:
            assert "line" in error
            assert "column" in error
            assert "message" in error
            assert "rule" in error
