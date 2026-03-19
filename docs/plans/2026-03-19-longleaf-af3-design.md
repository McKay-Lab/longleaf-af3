# longleaf-af3: Shared AlphaFold 3 Submission Tool for Longleaf

## Overview

A CLI tool that lets McKay lab members easily validate and submit AlphaFold 3 jobs to UNC's Longleaf HPC cluster. Users write AF3 input JSONs (with schema validation to catch errors early), and the tool handles SLURM resource estimation, script generation, and job submission.

## Project Structure

```
longleaf-af3/
├── README.md
├── pyproject.toml
├── config.toml.example
├── .gitignore
├── examples/
│   ├── simple_dimer.json
│   ├── trimer_with_dna.json
│   └── modified_protein.json
├── src/
│   └── longleaf_af3/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── schema.py
│       ├── resources.py
│       └── submit.py
└── schema/
    └── af3_input.schema.json
```

## CLI Commands

### `af3 init`

One-time setup per user:

- Prompts for email address (for SLURM notifications)
- Auto-detects ONYEN from `$USER`, constructs `/work/users/{first}/{second}/{onyen}/af3` as default work directory
- Saves to `config.toml` in the repo root (gitignored)

### `af3 validate input.json`

- Validates input JSON against AF3 JSON schema
- Checks structure, valid modification types, chain ID format, bonded atom pair references
- Reports clear, actionable error messages

### `af3 submit input.json [--mem 256G] [--time 2-00:00:00] [--partition a100-gpu] [--seeds 5] [--dry-run]`

- Runs validation first
- Estimates SLURM resources from input JSON (residue/base count heuristic)
- Prints estimated resources, CLI flags override estimates
- Copies input JSON to user's work directory on Longleaf
- Generates and submits SLURM script via `sbatch`
- `--dry-run` prints the SLURM script without submitting

### `af3 status`

- Runs `squeue -u $USER` filtered to AF3 jobs
- Optionally checks for completed output directories

## Resource Estimation

Based on total residues + bases across all chains:

| Size   | Threshold      | Memory | Time | Partition          |
|--------|----------------|--------|------|--------------------|
| Small  | <500 residues  | 64G    | 6h   | a100-gpu,l40-gpu   |
| Medium | 500-2000       | 128G   | 12h  | a100-gpu,l40-gpu   |
| Large  | >2000          | 256G   | 24h  | a100-gpu,l40-gpu   |

Constants: 32 CPUs, 1 GPU, `gpu_access` QOS.

Time scales by `num_seeds / 5` relative to baseline.

## Hardcoded Longleaf Paths

- AF3 container: `/nas/longleaf/containers/alphafold/3.0.1`
- AF3 databases: `/datacommons/alphafold/db_3.0.1`
- Singularity image, code, weights paths derived from container path

These are updated in the repo when Longleaf upgrades AF3.

## User Config

`config.toml` (gitignored):

```toml
[user]
email = "onyen@email.unc.edu"
onyen = "onyen"
work_dir = "/work/users/o/n/onyen/af3"
```

`config.toml.example` is committed as a template.

## Examples

Three example input JSONs using publicly available sequences:

- `simple_dimer.json`: two-protein complex
- `trimer_with_dna.json`: protein-DNA complex
- `modified_protein.json`: protein with PTMs and ligands

## Dependencies

- Python 3.12+
- `jsonschema` for validation
- `tomli` / `tomllib` for config parsing
- `tomli-w` for writing config
- No other external dependencies; SLURM interaction is via subprocess
