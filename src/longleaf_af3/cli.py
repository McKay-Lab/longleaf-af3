"""CLI entry point for longleaf-af3."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from longleaf_af3.config import Config, config_file_path, load_config, save_config
from longleaf_af3.resources import estimate_resources
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

    path = config_file_path()
    save_config(config, path)
    print(f"Config saved to {path}")


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

    config = load_config(config_file_path())
    resources = estimate_resources(data)

    # Apply CLI overrides
    if args.mem:
        resources.mem = args.mem
    if args.time:
        resources.time = args.time
    if args.partition:
        resources.partition = args.partition

    print(f"Job: {data['name']}")
    print(
        f"Resources: {resources.mem} memory, {resources.time} time, {resources.partition}"
    )

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

    validate_parser = subparsers.add_parser(
        "validate", help="Validate an AF3 input JSON"
    )
    validate_parser.add_argument("input", help="Path to AF3 input JSON file")

    submit_parser = subparsers.add_parser(
        "submit", help="Validate and submit an AF3 job"
    )
    submit_parser.add_argument("input", help="Path to AF3 input JSON file")
    submit_parser.add_argument("--mem", help="Override memory (e.g., 256G)")
    submit_parser.add_argument("--time", help="Override time limit (e.g., 2-00:00:00)")
    submit_parser.add_argument(
        "--partition", help="Override partition (e.g., a100-gpu)"
    )
    submit_parser.add_argument(
        "--dry-run", action="store_true", help="Print SLURM script without submitting"
    )

    subparsers.add_parser("status", help="Check status of AF3 jobs")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "validate": cmd_validate,
        "submit": cmd_submit,
        "status": cmd_status,
    }
    commands[args.command](args)
