"""Tests for the gha_validate tool."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from server import gha_validate

FIXTURES = Path(__file__).parent / "fixtures" / "github-actions"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _actionlint_available() -> bool:
    return shutil.which("actionlint") is not None


requires_actionlint = pytest.mark.skipif(
    not _actionlint_available(),
    reason="actionlint binary not installed",
)


class TestCleanWorkflow:
    @requires_actionlint
    def test_valid_workflow_passes(self) -> None:
        result = gha_validate(_read(FIXTURES / "valid" / "clean.yml"))
        assert result["valid"] is True
        assert result["syntax_ok"] is True
        assert result["available"] is True
        assert result["errors"] == []
        assert result["tool_error"] is None


class TestBrokenWorkflow:
    @requires_actionlint
    def test_undefined_matrix_ref_flagged(self) -> None:
        result = gha_validate(
            _read(FIXTURES / "invalid" / "undefined-matrix.yml")
        )
        assert result["valid"] is False
        assert result["syntax_ok"] is True
        assert result["available"] is True
        assert len(result["errors"]) >= 1
        # actionlint uses kind="expression" for ${{ }} issues
        assert any(e["rule"] == "expression" for e in result["errors"])
        # error entries have structural fields populated
        for err in result["errors"]:
            assert "line" in err and "column" in err
            assert "message" in err and "rule" in err

    @requires_actionlint
    def test_unknown_step_key_flagged(self) -> None:
        result = gha_validate(
            _read(FIXTURES / "invalid" / "unknown-key.yml")
        )
        assert result["valid"] is False
        assert result["syntax_ok"] is True
        assert len(result["errors"]) >= 1


class TestSyntaxError:
    def test_yaml_syntax_error_short_circuits_actionlint(self) -> None:
        # Unclosed flow sequence — invalid YAML. Should report syntax_ok=False
        # and never invoke actionlint (so this test works even without the
        # binary).
        result = gha_validate("foo: [unclosed")
        assert result["valid"] is False
        assert result["syntax_ok"] is False
        assert len(result["errors"]) == 1
        assert result["errors"][0]["rule"] == "syntax"


class TestActionlintUnavailable:
    def test_missing_binary_reports_tool_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Force shutil.which to report the binary as missing, regardless of
        # whether it is actually installed.
        import server

        monkeypatch.setattr(server.shutil, "which", lambda _name: None)

        result = gha_validate(
            "---\nname: x\n\"on\": push\njobs: {}\n"
        )
        # syntax is fine — YAML parses
        assert result["syntax_ok"] is True
        # missing linter is NOT an error condition, it's a capability gap
        assert result["valid"] is True
        assert result["available"] is False
        assert result["tool_error"] is not None
        assert "actionlint" in result["tool_error"]
        # guidance on how to install should be included
        assert "install" in result["tool_error"].lower()
