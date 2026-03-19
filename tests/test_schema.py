"""Tests for AF3 input JSON schema validation."""

from longleaf_af3.schema import validate_input


def _make_minimal_input() -> dict:
    """A minimal valid AF3 input."""
    return {
        "name": "test",
        "sequences": [{"protein": {"id": "A", "sequence": "MKTL"}}],
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
