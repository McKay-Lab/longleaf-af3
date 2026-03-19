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


def generate_slurm_script(
    job_name: str, config: Config, resources: SlurmResources
) -> str:
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
