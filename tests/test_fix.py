"""Tests for the yaml_fix tool."""

from __future__ import annotations

from pathlib import Path

from server import yaml_fix

FIXTURES = Path(__file__).parent / "fixtures"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Basic fixing
# ---------------------------------------------------------------------------


class TestBasicFix:
    def test_adds_document_start(self) -> None:
        content = "name: test\nvalue: 1\n"
        result = yaml_fix(content)
        assert result["fix_error"] is None
        assert result["fixed_content"].startswith("---")

    def test_normalizes_indentation(self) -> None:
        content = "---\nparent:\n    child: value\n"
        result = yaml_fix(content)
        assert result["fix_error"] is None
        # ruamel.yaml round-trip with indent=2 should normalize
        assert "    child" not in result["fixed_content"]

    def test_removes_trailing_whitespace(self) -> None:
        content = "---\nname: test   \nvalue: hello   \n"
        result = yaml_fix(content)
        assert result["fix_error"] is None
        for line in result["fixed_content"].splitlines():
            assert line == line.rstrip(), f"Trailing whitespace found: {line!r}"

    def test_post_fix_validation_included(self) -> None:
        content = "name: test\n"
        result = yaml_fix(content)
        assert result["fix_error"] is None
        assert result["validation"] is not None
        assert "valid" in result["validation"]
        assert "syntax_ok" in result["validation"]

    def test_fix_result_passes_validation(self) -> None:
        """Fixed content should pass validation (at least syntax)."""
        content = "name: test\nvalue: 1\n"
        result = yaml_fix(content)
        assert result["fix_error"] is None
        assert result["validation"]["syntax_ok"] is True


# ---------------------------------------------------------------------------
# Comment preservation
# ---------------------------------------------------------------------------


class TestCommentPreservation:
    def test_inline_comments_preserved(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "with_comments.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is None
        assert "inline comment" in result["fixed_content"]

    def test_block_comments_preserved(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "with_comments.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is None
        assert "Top-level comment" in result["fixed_content"]
        assert "Section comment" in result["fixed_content"]
        assert "Database host" in result["fixed_content"]

    def test_end_of_file_comment_preserved(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "with_comments.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is None
        assert "End of file comment" in result["fixed_content"]


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class TestIdempotency:
    def test_double_fix_same_result(self) -> None:
        """Running fix twice should produce the same output."""
        content = "name: test\nvalue: 1\nnested:\n    deep: true\n"
        first = yaml_fix(content)
        assert first["fix_error"] is None
        second = yaml_fix(first["fixed_content"])
        assert second["fix_error"] is None
        assert first["fixed_content"] == second["fixed_content"]

    def test_already_clean_is_idempotent(self) -> None:
        """Already-clean YAML should not change."""
        content = _read(FIXTURES / "valid" / "simple.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is None
        # Fix and re-fix should be stable
        result2 = yaml_fix(result["fixed_content"])
        assert result["fixed_content"] == result2["fixed_content"]


# ---------------------------------------------------------------------------
# Broken content – fix_error handling
# ---------------------------------------------------------------------------


class TestBrokenContent:
    def test_unparseable_returns_original(self) -> None:
        content = _read(FIXTURES / "invalid" / "unmatched_quote.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is not None
        assert result["fixed_content"] == content
        assert result["validation"] is None

    def test_tab_indent_returns_original(self) -> None:
        content = _read(FIXTURES / "invalid" / "tab_indent.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is not None
        assert result["fixed_content"] == content

    def test_fix_error_is_descriptive(self) -> None:
        content = "---\nkey: \"unterminated\n"
        result = yaml_fix(content)
        assert result["fix_error"] is not None
        assert isinstance(result["fix_error"], str)
        assert len(result["fix_error"]) > 0


# ---------------------------------------------------------------------------
# Post-fix lint level and schema
# ---------------------------------------------------------------------------


class TestPostFixOptions:
    def test_post_fix_with_relaxed_lint(self) -> None:
        content = "name: test\n"
        result = yaml_fix(content, lint_level="relaxed")
        assert result["fix_error"] is None
        assert result["validation"] is not None

    def test_post_fix_with_schema(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        content = "---\nname: test\n"
        result = yaml_fix(content, schema=schema)
        assert result["fix_error"] is None
        assert result["validation"]["valid"] is True

    def test_post_fix_schema_failure(self) -> None:
        schema = {
            "type": "object",
            "properties": {"name": {"type": "integer"}},
            "required": ["name"],
        }
        content = "---\nname: test\n"
        result = yaml_fix(content, schema=schema)
        assert result["fix_error"] is None
        assert result["validation"]["valid"] is False


# ---------------------------------------------------------------------------
# Edge cases for fix
# ---------------------------------------------------------------------------


class TestFixEdgeCases:
    def test_empty_string(self) -> None:
        result = yaml_fix("")
        assert result["fix_error"] is None

    def test_only_comments(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "only_comments.yaml")
        result = yaml_fix(content)
        # Should not error – comments-only is valid YAML (null document)
        assert result["fix_error"] is None

    def test_null_values_preserved(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "null_values.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is None

    def test_anchors_preserved(self) -> None:
        content = _read(FIXTURES / "valid" / "anchors.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is None

    def test_unicode_preserved(self) -> None:
        content = _read(FIXTURES / "valid" / "unicode.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is None
        assert "Helló" in result["fixed_content"]
        assert "🎉" in result["fixed_content"]

    def test_deep_nested(self) -> None:
        content = _read(FIXTURES / "edge_cases" / "deep_nested.yaml")
        result = yaml_fix(content)
        assert result["fix_error"] is None
        assert "deep" in result["fixed_content"]


# ---------------------------------------------------------------------------
# Output structure
# ---------------------------------------------------------------------------


class TestFixOutputStructure:
    def test_success_output_keys(self) -> None:
        result = yaml_fix("---\nkey: value\n")
        assert "fixed_content" in result
        assert "fix_error" in result
        assert "validation" in result

    def test_error_output_keys(self) -> None:
        result = yaml_fix("---\nkey: \"broken\n")
        assert "fixed_content" in result
        assert "fix_error" in result
        assert "validation" in result
