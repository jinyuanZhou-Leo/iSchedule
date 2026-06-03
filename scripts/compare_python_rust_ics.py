#!/usr/bin/env python3
"""Compare Python and Rust ICS output while ignoring nondeterministic fields."""

from __future__ import annotations

import argparse
import difflib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUST_ROOT = PROJECT_ROOT / "ischedule-rs"
PYTHON_MAIN = PROJECT_ROOT / "main.py"
RUST_BINARY = RUST_ROOT / "target" / "release" / "ischedule-rs"
IGNORED_PREFIXES = ("UID:", "DTSTAMP:")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify Rust ICS output matches Python output except UID and DTSTAMP."
    )
    parser.add_argument("-c", "--config", type=Path, default=PROJECT_ROOT / "config.json")
    parser.add_argument("-s", "--schedule", type=Path, default=PROJECT_ROOT / "schedule.json")
    parser.add_argument("--skip-build", action="store_true")
    parser.add_argument("--keep-output", action="store_true")
    return parser.parse_args()


def run(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        command_text = " ".join(command)
        raise RuntimeError(
            f"Command failed with exit code {completed.returncode}: {command_text}\n"
            f"{completed.stdout}{completed.stderr}"
        )


def generate_outputs(args: argparse.Namespace, output_root: Path) -> tuple[Path, Path]:
    python_output = output_root / "python"
    rust_output = output_root / "rust"
    python_output.mkdir()
    rust_output.mkdir()

    if not args.skip_build:
        run(["cargo", "build", "--release"], RUST_ROOT)

    run(
        [
            sys.executable,
            str(PYTHON_MAIN),
            "-nl",
            "-c",
            str(args.config),
            "-s",
            str(args.schedule),
            "-o",
            str(python_output),
        ],
        PROJECT_ROOT,
    )
    run(
        [
            str(RUST_BINARY),
            "--nolog",
            "--config",
            str(args.config),
            "--schedule",
            str(args.schedule),
            "--output",
            str(rust_output),
        ],
        PROJECT_ROOT,
    )
    return python_output, rust_output


def unfold_ics_lines(content: str) -> list[str]:
    lines: list[str] = []
    for raw_line in content.replace("\r\n", "\n").split("\n"):
        if not raw_line:
            continue
        if raw_line.startswith((" ", "\t")) and lines:
            lines[-1] += raw_line[1:]
        else:
            lines.append(raw_line)
    return lines


def normalized_lines(path: Path) -> list[str]:
    lines = unfold_ics_lines(path.read_text())
    return [line for line in lines if not line.startswith(IGNORED_PREFIXES)]


def compare_outputs(python_output: Path, rust_output: Path) -> bool:
    python_files = sorted(path.relative_to(python_output) for path in python_output.glob("*.ics"))
    rust_files = sorted(path.relative_to(rust_output) for path in rust_output.glob("*.ics"))
    if python_files != rust_files:
        print("Generated file lists differ:")
        print(f"Python: {python_files}")
        print(f"Rust:   {rust_files}")
        return False

    ok = True
    for relative_path in python_files:
        python_lines = normalized_lines(python_output / relative_path)
        rust_lines = normalized_lines(rust_output / relative_path)
        if python_lines != rust_lines:
            ok = False
            print(f"Mismatch: {relative_path}")
            print(
                "\n".join(
                    difflib.unified_diff(
                        python_lines,
                        rust_lines,
                        fromfile=f"python/{relative_path}",
                        tofile=f"rust/{relative_path}",
                        lineterm="",
                    )
                )
            )
    return ok


def main() -> int:
    args = parse_args()
    output_root = Path(tempfile.mkdtemp(prefix="ischedule-align-"))
    try:
        python_output, rust_output = generate_outputs(args, output_root)
        if compare_outputs(python_output, rust_output):
            print("Python and Rust ICS outputs match, ignoring UID and DTSTAMP.")
            return 0
        return 1
    finally:
        if args.keep_output:
            print(f"Kept output dir: {output_root}")
        else:
            shutil.rmtree(output_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
