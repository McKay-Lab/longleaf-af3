"""User configuration for longleaf-af3."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

import tomli_w


def config_file_path() -> Path:
    """Return the path to config.toml in the repo root."""
    return Path(__file__).resolve().parent.parent.parent / "config.toml"


@dataclass
class Config:
    email: str
    onyen: str
    work_dir: str

    def default_work_dir(self) -> str:
        """Construct the default Longleaf work directory from ONYEN."""
        o = self.onyen
        return f"/work/users/{o[0]}/{o[1]}/{o}/af3"


def save_config(config: Config, path: Path | None = None) -> None:
    """Write config to a TOML file."""
    if path is None:
        path = config_file_path()
    data = {
        "user": {
            "email": config.email,
            "onyen": config.onyen,
            "work_dir": config.work_dir,
        }
    }
    path.write_bytes(tomli_w.dumps(data).encode())


def load_config(path: Path | None = None) -> Config:
    """Load config from a TOML file."""
    if path is None:
        path = config_file_path()
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}\nRun 'af3 init' first.")
    data = tomllib.loads(path.read_text())
    user = data["user"]
    return Config(email=user["email"], onyen=user["onyen"], work_dir=user["work_dir"])
