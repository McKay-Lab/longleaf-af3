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


def _partition(residues: int) -> str:
    """GPU partition based on total residues. Large jobs need A100 (80GB VRAM)."""
    if residues > 2000:
        return "a100-gpu"
    return "a100-gpu,l40-gpu"


def _format_time(hours: int) -> str:
    """Format hours as HH:MM:SS or D-HH:MM:SS."""
    if hours > 24:
        days = hours // 24
        remaining = hours % 24
        return f"{days}-{remaining:02d}:00:00"
    return f"{hours}:00:00"


def estimate_resources(data: dict) -> SlurmResources:
    """Estimate SLURM resources from an AF3 input dict."""
    residues = _count_residues(data)
    num_seeds = len(data.get("modelSeeds", [1]))
    seed_factor = max(1.0, num_seeds / 5.0)

    base_hours = _base_time_hours(residues)
    scaled_hours = math.ceil(base_hours * seed_factor)

    return SlurmResources(
        mem=_base_mem(residues),
        time=_format_time(scaled_hours),
        partition=_partition(residues),
    )
