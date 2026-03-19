"""Tests for the CLI module."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from longleaf_af3.cli import main


def _write_valid_input(tmp_path: Path) -> Path:
    p = tmp_path / "test_input.json"
    p.write_text(
        json.dumps(
            {
                "name": "test",
                "sequences": [{"protein": {"id": "A", "sequence": "MKTL"}}],
                "modelSeeds": [1],
                "dialect": "alphafold3",
                "version": 1,
            }
        )
    )
    return p


def test_validate_valid_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    input_path = _write_valid_input(tmp_path)
    with patch("sys.argv", ["af3", "validate", str(input_path)]):
        main()
    captured = capsys.readouterr()
    assert "valid" in captured.out.lower()


def test_validate_invalid_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"name": "test"}))
    with patch("sys.argv", ["af3", "validate", str(p)]):
        with pytest.raises(SystemExit):
            main()


def test_init_creates_config(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    config_path = tmp_path / "config.toml"
    with (
        patch("sys.argv", ["af3", "init"]),
        patch("longleaf_af3.cli.config_file_path", return_value=config_path),
        patch("builtins.input", side_effect=["test@unc.edu"]),
        patch.dict(os.environ, {"USER": "testuser"}),
    ):
        main()
    assert config_path.exists()
    captured = capsys.readouterr()
    assert "testuser" in captured.out


def test_submit_dry_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = _write_valid_input(tmp_path)
    config_path = tmp_path / "config.toml"

    # Create config first
    with (
        patch("sys.argv", ["af3", "init"]),
        patch("longleaf_af3.cli.config_file_path", return_value=config_path),
        patch("builtins.input", side_effect=["test@unc.edu"]),
        patch.dict(os.environ, {"USER": "testuser"}),
    ):
        main()

    with (
        patch("sys.argv", ["af3", "submit", str(input_path), "--dry-run"]),
        patch("longleaf_af3.cli.config_file_path", return_value=config_path),
    ):
        main()
    captured = capsys.readouterr()
    assert "SBATCH" in captured.out
    assert "singularity exec" in captured.out
