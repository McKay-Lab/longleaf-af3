"""Tests for config module."""

from pathlib import Path

import pytest

from longleaf_af3.config import Config, load_config, save_config


def test_save_and_load_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config = Config(
        email="test@unc.edu", onyen="testuser", work_dir="/work/users/t/e/testuser/af3"
    )
    save_config(config, config_path)
    loaded = load_config(config_path)
    assert loaded.email == "test@unc.edu"
    assert loaded.onyen == "testuser"
    assert loaded.work_dir == "/work/users/t/e/testuser/af3"


def test_load_missing_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    with pytest.raises(FileNotFoundError):
        load_config(config_path)


def test_default_work_dir() -> None:
    config = Config(email="test@unc.edu", onyen="seanjohn", work_dir="")
    assert config.default_work_dir() == "/work/users/s/e/seanjohn/af3"


def test_config_file_path() -> None:
    from longleaf_af3.config import config_file_path

    result = config_file_path()
    assert result.name == "config.toml"
