"""Tests for SLURM script generation and submission."""

from longleaf_af3.config import Config
from longleaf_af3.resources import SlurmResources
from longleaf_af3.submit import generate_slurm_script


def _make_config() -> Config:
    return Config(
        email="test@unc.edu", onyen="testuser", work_dir="/work/users/t/e/testuser/af3"
    )


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
