# longleaf-af3

Submit AlphaFold 3 jobs to UNC's Longleaf HPC cluster.

## Prerequisites

1. **Longleaf account.** Request one at [UNC ITS Service Request](https://tdx.unc.edu/TDClient/33/Portal/Requests/ServiceDet?ID=45) (takes ~5 business days).
2. **GPU access.** Email research@unc.edu and request access to the `a100-gpu` and `l40-gpu` partitions. Mention you need it for AlphaFold 3 structure prediction.
3. **SSH access.** See the [SSH setup guide](docs/ssh-setup.md) for key-based login from your laptop.
4. **uv** (Python package manager). Install on Longleaf:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Note: off-campus users must connect through the [UNC VPN](https://help.unc.edu/sp?id=kb_article_view&sysparm_article=KB0010155) first.

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

This creates a `config.toml` with your ONYEN and email. `uv run` automatically installs dependencies on first use, no separate install step needed.

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
- `modified_protein.json` -- nucleosome with H3K4me3 modification and Widom 601 DNA

The input JSON follows the [AlphaFold 3 input format](https://github.com/google-deepmind/alphafold3/blob/main/docs/input.md). Key fields:

- `name`: job name (used for output directory naming)
- `sequences`: array of protein, DNA, RNA, or ligand chains
- `modelSeeds`: list of random seeds (more seeds = more predictions)
- `dialect`: must be `"alphafold3"`
- `version`: schema version (use `1`, or `2` for bonded atom pairs)

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

| Total residues | Memory | Time | GPU |
|---------------|--------|------|-----|
| <500          | 64G    | 6h   | A100 or L40S |
| 500-2000      | 128G   | 12h  | A100 or L40S |
| >2000         | 256G   | 24h  | A100 only |

Large jobs (>2000 residues) are steered to A100 GPUs (80GB VRAM) since they won't fit on L40S (48GB). Time scales with the number of seeds. Override any estimate with `--mem`, `--time`, or `--partition`.

## Output

Results are written to your work directory under `output_<job_name>/`. Each seed/sample combination produces a structure file and confidence metrics.
