#!/usr/bin/env python3
"""Run every script in CHECK_SCRIPTS against every target in a file and print one JSON array.

Each script takes one target as its only argument and prints one JSON row.

usage: run_checks.py -f FILE [-o [PATH]]
"""
import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CHECK_SCRIPTS = [
    "01_robots_check.py",
    "02_ping_check.py",
    "03_security_txt_check.py",
]
SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
TIMEOUT = 30
MAX_WORKERS = 8


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-f", "--file", required=True, help="text file of targets, one per line")
    parser.add_argument(
        "-o", "--output", nargs="?", const="", metavar="PATH",
        help="also save the JSON array; default name is <input-stem>.results.json",
    )
    return parser.parse_args()


def read_targets(path):
    """Targets from the file, skipping blank lines and # comments."""
    lines = (line.strip() for line in Path(path).read_text().splitlines())
    return [line for line in lines if line and not line.startswith("#")]


def check_name(script):
    """Check name for a script file: 01_robots_check.py -> 01-robots."""
    return Path(script).stem.removesuffix("_check").replace("_", "-")


def run_check(script, target):
    """Run one check script and return its JSON row, or an ERROR row on any failure."""
    name = check_name(script)
    error_row = {"check": name, "target": target, "status": 0, "result": "ERROR"}
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / script), target],
            capture_output=True, text=True, timeout=TIMEOUT,
        )
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"warning: {name} {target}: {e}", file=sys.stderr)
        return error_row
    if proc.returncode != 0:
        print(f"warning: {name} {target}: exit {proc.returncode}", file=sys.stderr)
        return error_row
    try:
        row = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(f"warning: {name} {target}: output is not JSON", file=sys.stderr)
        return error_row
    return row if isinstance(row, dict) else error_row


def run_all(targets):
    """Every check for every target, ordered by target then check."""
    jobs = [(script, target) for target in targets for script in CHECK_SCRIPTS]
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        return list(pool.map(lambda job: run_check(*job), jobs))


def output_path(arg, input_file):
    """The save path: PATH as given, or <input-stem>.results.json in the cwd."""
    return Path(arg) if arg else Path(f"{Path(input_file).stem}.results.json")


def main():
    args = parse_args()
    try:
        targets = read_targets(args.file)
    except OSError as e:
        sys.exit(f"error: cannot read {args.file}: {e.strerror}")
    print(f"running {len(CHECK_SCRIPTS)} checks on {len(targets)} targets", file=sys.stderr)
    text = json.dumps(run_all(targets), indent=2)
    print(text)
    if args.output is not None:
        path = output_path(args.output, args.file)
        try:
            path.write_text(text + "\n")
        except OSError as e:
            sys.exit(f"error: cannot write {path}: {e.strerror}")
        print(f"saved {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
