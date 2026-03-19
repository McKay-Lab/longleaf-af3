"""Tests for SLURM resource estimation."""

from longleaf_af3.resources import estimate_resources


def test_small_job() -> None:
    data = {
        "sequences": [{"protein": {"id": "A", "sequence": "MKTL"}}],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.mem == "64G"
    assert res.time == "6:00:00"
    assert res.partition == "a100-gpu,l40-gpu"


def test_medium_job() -> None:
    data = {
        "sequences": [{"protein": {"id": "A", "sequence": "M" * 1000}}],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.mem == "128G"
    assert res.time == "12:00:00"
    assert res.partition == "a100-gpu,l40-gpu"


def test_large_job() -> None:
    data = {
        "sequences": [{"protein": {"id": "A", "sequence": "M" * 2500}}],
        "modelSeeds": [1],
    }
    res = estimate_resources(data)
    assert res.mem == "256G"
    assert res.time == "24:00:00"
    assert res.partition == "a100-gpu"


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
