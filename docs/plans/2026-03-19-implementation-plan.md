# longleaf-af3 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool (`af3`) that validates AF3 input JSONs and submits SLURM jobs to Longleaf HPC.

**Architecture:** A `uv`-managed Python package with `argparse` CLI, JSON Schema validation via `jsonschema`, TOML config for user settings, and subprocess-based SLURM submission. All Longleaf-specific paths are constants in the submit module.

**Tech Stack:** Python 3.12+, jsonschema, tomli-w, argparse, subprocess

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `config.toml.example`
- Create: `src/longleaf_af3/__init__.py`

**Step 1: Initialize git repo**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && git init`

**Step 2: Create `pyproject.toml`**

```toml
[project]
name = "longleaf-af3"
version = "0.1.0"
description = "Submit AlphaFold 3 jobs to UNC Longleaf HPC"
requires-python = ">=3.12"
dependencies = [
    "jsonschema>=4.23",
    "tomli-w>=1.1",
]

[project.scripts]
af3 = "longleaf_af3.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"
```

**Step 3: Create `.gitignore`**

```
config.toml
__pycache__/
*.pyc
.venv/
dist/
*.egg-info/
logs/
```

**Step 4: Create `config.toml.example`**

```toml
[user]
email = "onyen@email.unc.edu"
onyen = "onyen"
work_dir = "/work/users/o/n/onyen/af3"
```

**Step 5: Create `src/longleaf_af3/__init__.py`**

Empty file.

**Step 6: Run `uv sync` to set up the project**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv sync`
Expected: dependencies installed, `.venv` created

**Step 7: Commit**

```bash
git add pyproject.toml .gitignore config.toml.example src/longleaf_af3/__init__.py uv.lock
git commit -m "feat: initial project scaffolding"
```

---

### Task 2: Config Module

**Files:**
- Create: `src/longleaf_af3/config.py`
- Create: `tests/test_config.py`

**Step 1: Write tests for config**

```python
"""Tests for config module."""

import os
from pathlib import Path

import pytest

from longleaf_af3.config import Config, load_config, save_config


def test_save_and_load_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config = Config(email="test@unc.edu", onyen="testuser", work_dir="/work/users/t/e/testuser/af3")
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_config.py -v`
Expected: FAIL (module not found)

**Step 3: Implement config module**

```python
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
    data = {"user": {"email": config.email, "onyen": config.onyen, "work_dir": config.work_dir}}
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
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_config.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add src/longleaf_af3/config.py tests/test_config.py
git commit -m "feat: add config module for user settings"
```

---

### Task 3: JSON Schema and Validation

**Files:**
- Create: `schema/af3_input.schema.json`
- Create: `src/longleaf_af3/schema.py`
- Create: `tests/test_schema.py`

**Step 1: Write tests for schema validation**

```python
"""Tests for AF3 input JSON schema validation."""

import json
from pathlib import Path

import pytest

from longleaf_af3.schema import validate_input


def _make_minimal_input() -> dict:
    """A minimal valid AF3 input."""
    return {
        "name": "test",
        "sequences": [
            {"protein": {"id": "A", "sequence": "MKTL"}}
        ],
        "modelSeeds": [1],
        "dialect": "alphafold3",
        "version": 1,
    }


def test_valid_minimal_input() -> None:
    errors = validate_input(_make_minimal_input())
    assert errors == []


def test_valid_protein_with_id_list() -> None:
    data = _make_minimal_input()
    data["sequences"][0]["protein"]["id"] = ["A", "B"]
    errors = validate_input(data)
    assert errors == []


def test_valid_dna_chain() -> None:
    data = _make_minimal_input()
    data["sequences"].append({"dna": {"id": "I", "sequence": "ATCG"}})
    errors = validate_input(data)
    assert errors == []


def test_valid_rna_chain() -> None:
    data = _make_minimal_input()
    data["sequences"].append({"rna": {"id": "R", "sequence": "AUCG"}})
    errors = validate_input(data)
    assert errors == []


def test_valid_ligand() -> None:
    data = _make_minimal_input()
    data["sequences"].append({"ligand": {"id": "L", "ccdCodes": ["ATP"]}})
    errors = validate_input(data)
    assert errors == []


def test_valid_modifications() -> None:
    data = _make_minimal_input()
    data["sequences"][0]["protein"]["modifications"] = [
        {"ptmType": "MLZ", "ptmPosition": 1}
    ]
    errors = validate_input(data)
    assert errors == []


def test_valid_bonded_atom_pairs() -> None:
    data = _make_minimal_input()
    data["sequences"].append({"ligand": {"id": "M", "ccdCodes": ["TME"]}})
    data["bondedAtomPairs"] = [[["A", 1, "CB"], ["M", 1, "C1"]]]
    errors = validate_input(data)
    assert errors == []


def test_missing_name() -> None:
    data = _make_minimal_input()
    del data["name"]
    errors = validate_input(data)
    assert any("name" in e for e in errors)


def test_missing_sequences() -> None:
    data = _make_minimal_input()
    del data["sequences"]
    errors = validate_input(data)
    assert any("sequences" in e for e in errors)


def test_empty_sequences() -> None:
    data = _make_minimal_input()
    data["sequences"] = []
    errors = validate_input(data)
    assert len(errors) > 0


def test_missing_model_seeds() -> None:
    data = _make_minimal_input()
    del data["modelSeeds"]
    errors = validate_input(data)
    assert any("modelSeeds" in e for e in errors)


def test_invalid_sequence_type() -> None:
    data = _make_minimal_input()
    data["sequences"].append({"unknown": {"id": "X"}})
    errors = validate_input(data)
    assert len(errors) > 0


def test_protein_missing_sequence() -> None:
    data = _make_minimal_input()
    del data["sequences"][0]["protein"]["sequence"]
    errors = validate_input(data)
    assert len(errors) > 0
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_schema.py -v`
Expected: FAIL

**Step 3: Create the JSON schema file**

Create `schema/af3_input.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AlphaFold 3 Input",
  "type": "object",
  "required": ["name", "sequences", "modelSeeds", "dialect", "version"],
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1
    },
    "sequences": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "oneOf": [
          {
            "required": ["protein"],
            "properties": {
              "protein": { "$ref": "#/$defs/proteinChain" }
            },
            "additionalProperties": false
          },
          {
            "required": ["dna"],
            "properties": {
              "dna": { "$ref": "#/$defs/nucleotideChain" }
            },
            "additionalProperties": false
          },
          {
            "required": ["rna"],
            "properties": {
              "rna": { "$ref": "#/$defs/nucleotideChain" }
            },
            "additionalProperties": false
          },
          {
            "required": ["ligand"],
            "properties": {
              "ligand": { "$ref": "#/$defs/ligandChain" }
            },
            "additionalProperties": false
          }
        ]
      }
    },
    "modelSeeds": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "integer" }
    },
    "dialect": {
      "type": "string",
      "const": "alphafold3"
    },
    "version": {
      "type": "integer"
    },
    "bondedAtomPairs": {
      "type": "array",
      "items": {
        "type": "array",
        "items": {
          "type": "array",
          "prefixItems": [
            { "type": "string" },
            { "type": "integer" },
            { "type": "string" }
          ],
          "minItems": 3,
          "maxItems": 3
        },
        "minItems": 2,
        "maxItems": 2
      }
    }
  },
  "additionalProperties": false,
  "$defs": {
    "chainId": {
      "oneOf": [
        { "type": "string", "minLength": 1 },
        { "type": "array", "items": { "type": "string", "minLength": 1 }, "minItems": 1 }
      ]
    },
    "modification": {
      "type": "object",
      "required": ["ptmType", "ptmPosition"],
      "properties": {
        "ptmType": { "type": "string" },
        "ptmPosition": { "type": "integer", "minimum": 1 }
      },
      "additionalProperties": false
    },
    "proteinChain": {
      "type": "object",
      "required": ["id", "sequence"],
      "properties": {
        "id": { "$ref": "#/$defs/chainId" },
        "sequence": { "type": "string", "pattern": "^[A-Z]+$" },
        "modifications": {
          "type": "array",
          "items": { "$ref": "#/$defs/modification" }
        }
      },
      "additionalProperties": false
    },
    "nucleotideChain": {
      "type": "object",
      "required": ["id", "sequence"],
      "properties": {
        "id": { "$ref": "#/$defs/chainId" },
        "sequence": { "type": "string", "minLength": 1 },
        "modifications": {
          "type": "array",
          "items": { "$ref": "#/$defs/modification" }
        }
      },
      "additionalProperties": false
    },
    "ligandChain": {
      "type": "object",
      "required": ["id"],
      "properties": {
        "id": { "$ref": "#/$defs/chainId" },
        "ccdCodes": {
          "type": "array",
          "items": { "type": "string" },
          "minItems": 1
        },
        "smiles": { "type": "string" }
      },
      "additionalProperties": false
    }
  }
}
```

**Step 4: Implement schema validation module**

```python
"""AF3 input JSON schema validation."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema


def _load_schema() -> dict:
    """Load the AF3 JSON schema."""
    schema_path = Path(__file__).resolve().parent.parent.parent / "schema" / "af3_input.schema.json"
    return json.loads(schema_path.read_text())


def validate_input(data: dict) -> list[str]:
    """Validate an AF3 input dict against the schema. Returns a list of error messages."""
    schema = _load_schema()
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    return [_format_error(e) for e in errors]


def _format_error(error: jsonschema.ValidationError) -> str:
    """Format a validation error into a readable message."""
    path = ".".join(str(p) for p in error.absolute_path)
    if path:
        return f"{path}: {error.message}"
    return error.message
```

**Step 5: Run tests to verify they pass**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_schema.py -v`
Expected: all PASS

**Step 6: Commit**

```bash
git add schema/af3_input.schema.json src/longleaf_af3/schema.py tests/test_schema.py
git commit -m "feat: add JSON schema validation for AF3 inputs"
```

---

### Task 4: Resource Estimation

**Files:**
- Create: `src/longleaf_af3/resources.py`
- Create: `tests/test_resources.py`

**Step 1: Write tests for resource estimation**

```python
"""Tests for SLURM resource estimation."""

from longleaf_af3.resources import SlurmResources, estimate_resources


def test_small_job() -> None:
    data = {
        "sequences": [{"protein": {"id": "A", "sequence": "MKTL"}}],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.mem == "64G"
    assert res.time == "6:00:00"


def test_medium_job() -> None:
    data = {
        "sequences": [{"protein": {"id": "A", "sequence": "M" * 1000}}],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.mem == "128G"
    assert res.time == "12:00:00"


def test_large_job() -> None:
    data = {
        "sequences": [{"protein": {"id": "A", "sequence": "M" * 2500}}],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.mem == "256G"
    assert res.time == "24:00:00"


def test_dna_counted() -> None:
    data = {
        "sequences": [
            {"protein": {"id": "A", "sequence": "M" * 400}},
            {"dna": {"id": "I", "sequence": "A" * 200}},
        ],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.mem == "128G"


def test_seed_scaling() -> None:
    data = {
        "sequences": [{"protein": {"id": "A", "sequence": "MKTL"}}],
        "modelSeeds": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    }
    res = estimate_resources(data)
    assert res.time == "12:00:00"


def test_multi_copy_chains() -> None:
    """Chain IDs as arrays should count each copy."""
    data = {
        "sequences": [{"protein": {"id": ["A", "B"], "sequence": "M" * 300}}],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.mem == "128G"


def test_defaults() -> None:
    data = {
        "sequences": [{"protein": {"id": "A", "sequence": "MKTL"}}],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.cpus == 32
    assert res.gpus == 1
    assert res.partition == "a100-gpu,l40-gpu"
    assert res.qos == "gpu_access"
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_resources.py -v`
Expected: FAIL

**Step 3: Implement resource estimation**

```python
"""Estimate SLURM resources from AF3 input JSON."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class SlurmResources:
    mem: str
    time: str
    cpus: int = 32
    gpus: int = 1
    partition: str = "a100-gpu,l40-gpu"
    qos: str = "gpu_access"


def _count_residues(data: dict) -> int:
    """Count total residues/bases across all chains, accounting for multi-copy IDs."""
    total = 0
    for entry in data.get("sequences", []):
        for chain_type in ("protein", "dna", "rna"):
            if chain_type in entry:
                chain = entry[chain_type]
                seq_len = len(chain.get("sequence", ""))
                chain_id = chain.get("id", "")
                copies = len(chain_id) if isinstance(chain_id, list) else 1
                total += seq_len * copies
    return total


def _base_time_hours(residues: int) -> int:
    """Base time in hours before seed scaling."""
    if residues < 500:
        return 6
    if residues <= 2000:
        return 12
    return 24


def _base_mem(residues: int) -> str:
    """Memory string based on total residues."""
    if residues < 500:
        return "64G"
    if residues <= 2000:
        return "128G"
    return "256G"


def _format_time(hours: int) -> str:
    """Format hours as HH:MM:SS or D-HH:MM:SS."""
    if hours >= 24:
        days = hours // 24
        remaining = hours % 24
        return f"{days}-{remaining:02d}:00:00"
    return f"{hours}:00:00"


def estimate_resources(data: dict) -> SlurmResources:
    """Estimate SLURM resources from an AF3 input dict."""
    residues = _count_residues(data)
    num_seeds = len(data.get("modelSeeds", [1]))
    seed_factor = num_seeds / 5.0

    base_hours = _base_time_hours(residues)
    scaled_hours = math.ceil(base_hours * seed_factor)

    return SlurmResources(
        mem=_base_mem(residues),
        time=_format_time(scaled_hours),
    )
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_resources.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add src/longleaf_af3/resources.py tests/test_resources.py
git commit -m "feat: add SLURM resource estimation from input JSON"
```

---

### Task 5: SLURM Script Generation and Submission

**Files:**
- Create: `src/longleaf_af3/submit.py`
- Create: `tests/test_submit.py`

**Step 1: Write tests for SLURM script generation**

```python
"""Tests for SLURM script generation and submission."""

from longleaf_af3.config import Config
from longleaf_af3.resources import SlurmResources
from longleaf_af3.submit import generate_slurm_script


def _make_config() -> Config:
    return Config(email="test@unc.edu", onyen="testuser", work_dir="/work/users/t/e/testuser/af3")


def _make_resources() -> SlurmResources:
    return SlurmResources(mem="128G", time="12:00:00")


def test_script_has_sbatch_directives() -> None:
    script = generate_slurm_script("my_job", _make_config(), _make_resources())
    assert "#!/bin/bash" in script
    assert "#SBATCH --mem=128G" in script
    assert "#SBATCH -t 12:00:00" in script
    assert "#SBATCH --gres=gpu:1" in script
    assert "#SBATCH -p a100-gpu,l40-gpu" in script
    assert "#SBATCH --qos=gpu_access" in script
    assert "#SBATCH --mail-user=test@unc.edu" in script


def test_script_has_singularity_command() -> None:
    script = generate_slurm_script("my_job", _make_config(), _make_resources())
    assert "singularity exec" in script
    assert "run_alphafold.py" in script
    assert "--json_path=/root/af_input/my_job.json" in script


def test_script_has_correct_paths() -> None:
    script = generate_slurm_script("my_job", _make_config(), _make_resources())
    assert "/work/users/t/e/testuser/af3" in script
    assert "output_my_job" in script


def test_script_has_module_load() -> None:
    script = generate_slurm_script("my_job", _make_config(), _make_resources())
    assert "module load singularity" in script
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_submit.py -v`
Expected: FAIL

**Step 3: Implement submit module**

```python
"""Generate SLURM scripts and submit AF3 jobs."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from longleaf_af3.config import Config
from longleaf_af3.resources import SlurmResources

AF3_RESOURCES_DIR = "/nas/longleaf/containers/alphafold/3.0.1"
AF3_IMAGE = f"{AF3_RESOURCES_DIR}/image/alphafold3.0.1-cuda12.6-ubuntu22.04.sif"
AF3_CODE_DIR = f"{AF3_RESOURCES_DIR}/code"
AF3_MODEL_PARAMETERS_DIR = f"{AF3_RESOURCES_DIR}/weights"
AF3_DATABASES_DIR = "/datacommons/alphafold/db_3.0.1"


def generate_slurm_script(job_name: str, config: Config, resources: SlurmResources) -> str:
    """Generate a SLURM submission script for an AF3 job."""
    work_dir = config.work_dir
    output_dir = f"{work_dir}/output_{job_name}"

    return f"""#!/bin/bash

#SBATCH -J af3_{job_name}
#SBATCH --ntasks=1
#SBATCH --cpus-per-task={resources.cpus}
#SBATCH --mem={resources.mem}
#SBATCH -t {resources.time}
#SBATCH -p {resources.partition}
#SBATCH --qos={resources.qos}
#SBATCH --gres=gpu:{resources.gpus}
#SBATCH --mail-type=begin,end,fail
#SBATCH --mail-user={config.email}
#SBATCH -o logs/af3_{job_name}_%j.out
#SBATCH -e logs/af3_{job_name}_%j.err

mkdir -p logs
mkdir -p {output_dir}

hostname
nvidia-smi

module load singularity

singularity exec \\
    --nv \\
    --bind {work_dir}:/root/af_input \\
    --bind {output_dir}:/root/af_output \\
    --bind {AF3_MODEL_PARAMETERS_DIR}:/root/models \\
    --bind {AF3_DATABASES_DIR}:/root/public_databases \\
    --bind {AF3_CODE_DIR}:/root/code \\
    {AF3_IMAGE} \\
    python /root/code/alphafold3/run_alphafold.py \\
    --json_path=/root/af_input/{job_name}.json \\
    --model_dir=/root/models \\
    --db_dir=/root/public_databases \\
    --output_dir=/root/af_output
"""


def submit_job(
    input_path: Path,
    config: Config,
    resources: SlurmResources,
    dry_run: bool = False,
) -> str:
    """Copy input JSON to work dir and submit the SLURM job.

    Returns the generated SLURM script (dry_run) or sbatch output.
    """
    data = json.loads(input_path.read_text())
    job_name = data["name"]

    script = generate_slurm_script(job_name, config, resources)

    if dry_run:
        return script

    work_dir = Path(config.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Copy input JSON to work directory
    shutil.copy2(input_path, work_dir / f"{job_name}.json")

    # Write SLURM script to temp file and submit
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(script)
        script_path = f.name

    result = subprocess.run(
        ["sbatch", script_path],
        capture_output=True,
        text=True,
        cwd=str(work_dir),
        check=False,
    )

    Path(script_path).unlink()

    if result.returncode != 0:
        raise RuntimeError(f"sbatch failed: {result.stderr}")

    return result.stdout.strip()
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_submit.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add src/longleaf_af3/submit.py tests/test_submit.py
git commit -m "feat: add SLURM script generation and job submission"
```

---

### Task 6: CLI Module

**Files:**
- Create: `src/longleaf_af3/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write tests for CLI**

```python
"""Tests for the CLI module."""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from longleaf_af3.cli import main


def _write_valid_input(tmp_path: Path) -> Path:
    p = tmp_path / "test_input.json"
    p.write_text(json.dumps({
        "name": "test",
        "sequences": [{"protein": {"id": "A", "sequence": "MKTL"}}],
        "modelSeeds": [1],
        "dialect": "alphafold3",
        "version": 1,
    }))
    return p


def test_validate_valid_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    input_path = _write_valid_input(tmp_path)
    with patch("sys.argv", ["af3", "validate", str(input_path)]):
        main()
    captured = capsys.readouterr()
    assert "valid" in captured.out.lower()


def test_validate_invalid_input(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"name": "test"}))
    with patch("sys.argv", ["af3", "validate", str(p)]):
        with pytest.raises(SystemExit):
            main()


def test_init_creates_config(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
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
```

**Step 2: Run tests to verify they fail**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_cli.py -v`
Expected: FAIL

**Step 3: Implement CLI**

```python
"""CLI entry point for longleaf-af3."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from longleaf_af3.config import Config, config_file_path, load_config, save_config
from longleaf_af3.resources import SlurmResources, estimate_resources
from longleaf_af3.schema import validate_input
from longleaf_af3.submit import submit_job


def cmd_init(args: argparse.Namespace) -> None:
    """Run the init command."""
    onyen = os.environ.get("USER", "")
    print(f"Detected ONYEN: {onyen}")

    email = input(f"Email for SLURM notifications [{onyen}@email.unc.edu]: ").strip()
    if not email:
        email = f"{onyen}@email.unc.edu"

    config = Config(email=email, onyen=onyen, work_dir="")
    config.work_dir = config.default_work_dir()

    print(f"Work directory: {config.work_dir}")

    save_config(config)
    print(f"Config saved to {config_file_path()}")


def cmd_validate(args: argparse.Namespace) -> None:
    """Run the validate command."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(input_path.read_text())
    errors = validate_input(data)

    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Valid AF3 input: {data.get('name', '(unnamed)')}")


def cmd_submit(args: argparse.Namespace) -> None:
    """Run the submit command."""
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(input_path.read_text())
    errors = validate_input(data)
    if errors:
        print(f"Validation failed with {len(errors)} error(s):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    config = load_config()
    resources = estimate_resources(data)

    # Apply CLI overrides
    if args.mem:
        resources.mem = args.mem
    if args.time:
        resources.time = args.time
    if args.partition:
        resources.partition = args.partition

    print(f"Job: {data['name']}")
    print(f"Resources: {resources.mem} memory, {resources.time} time, {resources.partition}")

    result = submit_job(input_path, config, resources, dry_run=args.dry_run)

    if args.dry_run:
        print("\n--- Generated SLURM script (dry run) ---")
        print(result)
    else:
        print(result)


def cmd_status(args: argparse.Namespace) -> None:
    """Run the status command."""
    user = os.environ.get("USER", "")
    result = subprocess.run(
        ["squeue", "-u", user, "--name=af3"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"squeue error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    print(result.stdout)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="af3",
        description="Submit AlphaFold 3 jobs to Longleaf HPC",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="One-time user setup")

    validate_parser = subparsers.add_parser("validate", help="Validate an AF3 input JSON")
    validate_parser.add_argument("input", help="Path to AF3 input JSON file")

    submit_parser = subparsers.add_parser("submit", help="Validate and submit an AF3 job")
    submit_parser.add_argument("input", help="Path to AF3 input JSON file")
    submit_parser.add_argument("--mem", help="Override memory (e.g., 256G)")
    submit_parser.add_argument("--time", help="Override time limit (e.g., 2-00:00:00)")
    submit_parser.add_argument("--partition", help="Override partition (e.g., a100-gpu)")
    submit_parser.add_argument("--dry-run", action="store_true", help="Print SLURM script without submitting")

    subparsers.add_parser("status", help="Check status of AF3 jobs")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "validate": cmd_validate,
        "submit": cmd_submit,
        "status": cmd_status,
    }
    commands[args.command](args)
```

**Step 4: Run tests to verify they pass**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/test_cli.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add src/longleaf_af3/cli.py tests/test_cli.py
git commit -m "feat: add CLI with init, validate, submit, status commands"
```

---

### Task 7: Example Input JSONs

**Files:**
- Create: `examples/simple_dimer.json`
- Create: `examples/trimer_with_dna.json`
- Create: `examples/modified_protein.json`

Use publicly available protein sequences from well-known structures.

**Step 1: Create `examples/simple_dimer.json`**

A barnase-barstar complex (PDB: 1BRS), a classic protein-protein interaction example:

```json
{
  "name": "barnase_barstar",
  "sequences": [
    {
      "protein": {
        "id": "A",
        "sequence": "AQVINTFDGVADYLQTYHKLPDNYITKSEAQALGWVASKGNLADVAPGKSIGGDIFSNREGKLPGKSGRTWREADINYTS"
      }
    },
    {
      "protein": {
        "id": "B",
        "sequence": "KKAVINGEQIRSISDLHQTLKKELALPEYYGENLDALWDCLTGWVEYPLVLEWRQFEQSKQLTENGAESVLQVFREAKAEGCDITIILS"
      }
    }
  ],
  "modelSeeds": [1, 2, 3],
  "dialect": "alphafold3",
  "version": 1
}
```

**Step 2: Create `examples/trimer_with_dna.json`**

A p53 DNA-binding domain tetramer with a response element (based on PDB: 1TSR concept, simplified):

```json
{
  "name": "p53_dbd_dna",
  "sequences": [
    {
      "protein": {
        "id": ["A", "B"],
        "sequence": "SSSVPSQKTYPQGLNGTVNLPGRNSFEVRVCSPHETSPLQKIDLVTTLTLGLHICQLACTSPALNKMFCQLAKTCPVQLWVSATPPAGSRVRAMAIYKKSQHMTEVVRRCPHHERCSETSQHSLPIDDLLRSQIRQHLHQILRGEVRRC"
      }
    },
    {
      "dna": {
        "id": "C",
        "sequence": "TAGACTTGCCTGGACTTGCCTAG"
      }
    },
    {
      "dna": {
        "id": "D",
        "sequence": "CTAGGCAAGTCCAGGCAAGTCTA"
      }
    }
  ],
  "modelSeeds": [1, 2, 3],
  "dialect": "alphafold3",
  "version": 1
}
```

**Step 3: Create `examples/modified_protein.json`**

An example with histone modifications and a ligand, using a histone H3-H4 tetramer with H3K4me3:

```json
{
  "name": "h3_h4_tetramer_k4me3",
  "sequences": [
    {
      "protein": {
        "id": ["A", "C"],
        "sequence": "MARTKQTARKSTGGKAPRKQLATKAARKSAPATGGVKKPHRYRPGTVALREIRRYQKSTELLIRKLPFQRLVREIAQDFKTDLRFQSSAVMALQEASEAYLVGLFEDTNLCAIHAKRVTIMPKDIQLARRIRGERA",
        "modifications": [
          {"ptmType": "M3L", "ptmPosition": 5}
        ]
      }
    },
    {
      "protein": {
        "id": ["B", "D"],
        "sequence": "MSGRGKGGKGLGKGGAKRHRKVLRDNIQGITKPAIRRLARRGGVKRISGLIYEETRGVLKVFLENVIRDAVTYTEHAKRKTVTAMDVVYALKRQGRTLYGFGG"
      }
    }
  ],
  "modelSeeds": [1, 2, 3, 4, 5],
  "dialect": "alphafold3",
  "version": 1
}
```

**Step 4: Validate examples against schema**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && for f in examples/*.json; do echo "--- $f ---"; uv run af3 validate "$f"; done`
Expected: all valid

**Step 5: Commit**

```bash
git add examples/
git commit -m "feat: add example AF3 input JSONs"
```

---

### Task 8: README

**Files:**
- Create: `README.md`

**Step 1: Write README**

```markdown
# longleaf-af3

Submit AlphaFold 3 jobs to UNC's Longleaf HPC cluster.

## Prerequisites

- Access to Longleaf with GPU partition (`a100-gpu` or `l40-gpu`)
- [uv](https://docs.astral.sh/uv/) installed on Longleaf

To install uv on Longleaf:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

Clone the repo on Longleaf:

```bash
git clone https://github.com/mckay-lab/longleaf-af3.git
cd longleaf-af3
```

Run one-time setup (saves your email and work directory):

```bash
uv run af3 init
```

This creates a `config.toml` with your ONYEN and email.

## Usage

### Validate an input JSON

```bash
uv run af3 validate my_input.json
```

### Submit a job

```bash
uv run af3 submit my_input.json
```

The tool automatically estimates memory and time based on your input size. Override with flags:

```bash
uv run af3 submit my_input.json --mem 256G --time 2-00:00:00
```

Preview the SLURM script without submitting:

```bash
uv run af3 submit my_input.json --dry-run
```

### Check job status

```bash
uv run af3 status
```

## Writing AF3 Input JSONs

See the `examples/` directory for templates:

- `simple_dimer.json` -- two-protein complex (barnase-barstar)
- `trimer_with_dna.json` -- protein-DNA complex (p53 with response element)
- `modified_protein.json` -- histone tetramer with H3K4me3 modification

The input JSON follows the [AlphaFold 3 input format](https://github.com/google-deepmind/alphafold3/blob/main/docs/input.md). Key fields:

- `name`: job name (used for output directory naming)
- `sequences`: array of protein, DNA, RNA, or ligand chains
- `modelSeeds`: list of random seeds (more seeds = more predictions)
- `dialect`: must be `"alphafold3"`
- `version`: schema version (use `1` or `2` for bonded atom pairs)

### Protein modifications

Add post-translational modifications using CCD codes:

```json
{
  "protein": {
    "id": "A",
    "sequence": "MARTKQTARKSTGG...",
    "modifications": [
      {"ptmType": "MLZ", "ptmPosition": 5}
    ]
  }
}
```

### Resource estimation

The tool estimates SLURM resources based on total residues/bases:

| Total residues | Memory | Time |
|---------------|--------|------|
| <500          | 64G    | 6h   |
| 500-2000      | 128G   | 12h  |
| >2000         | 256G   | 24h  |

Time scales with the number of seeds. Override any estimate with `--mem`, `--time`, or `--partition`.

## Output

Results are written to your work directory under `output_<job_name>/`. Each seed/sample combination produces a structure file and confidence metrics.
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with setup and usage instructions"
```

---

### Task 9: Final Integration Test

**Step 1: Run full test suite**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run pytest tests/ -v`
Expected: all PASS

**Step 2: Verify CLI works end-to-end**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run af3 validate examples/simple_dimer.json`
Expected: "Valid AF3 input: barnase_barstar"

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uv run af3 validate examples/modified_protein.json`
Expected: "Valid AF3 input: h3_h4_tetramer_k4me3"

**Step 3: Lint with ruff**

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uvx ruff check src/ tests/`
Fix any issues.

Run: `cd /Users/sean/code/mckay-lab-code/longleaf-af3 && uvx ruff format src/ tests/`

**Step 4: Commit any lint fixes**

```bash
git add -A
git commit -m "style: apply ruff formatting"
```
