#!/usr/bin/env python3
"""Benchmark Python and Rust iSchedule generators with the same inputs."""

from __future__ import annotations

import argparse
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUST_ROOT = PROJECT_ROOT / "ischedule-rs"
PYTHON_MAIN = PROJECT_ROOT / "main.py"
CONFIG_PATH = PROJECT_ROOT / "config.json"
SCHEDULE_PATH = PROJECT_ROOT / "schedule.json"
RUST_BINARY = RUST_ROOT / "target" / "release" / "ischedule-rs"


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    timings: list[float]

    @property
    def mean(self) -> float:
        return statistics.mean(self.timings)

    @property
    def median(self) -> float:
        return statistics.median(self.timings)

    @property
    def minimum(self) -> float:
        return min(self.timings)

    @property
    def maximum(self) -> float:
        return max(self.timings)

    @property
    def stdev(self) -> float:
        return statistics.stdev(self.timings) if len(self.timings) > 1 else 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare iSchedule Python and Rust generator performance."
    )
    parser.add_argument(
        "-n",
        "--iterations",
        type=int,
        default=20,
        help="Measured iterations per implementation. Default: 20.",
    )
    parser.add_argument(
        "-w",
        "--warmup",
        type=int,
        default=3,
        help="Warmup iterations per implementation. Default: 3.",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip cargo release build and use the existing release binary.",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Keep generated benchmark output directory for inspection.",
    )
    return parser.parse_args()


def validate_environment(args: argparse.Namespace) -> None:
    if args.iterations <= 0:
        raise ValueError("--iterations must be positive")
    if args.warmup < 0:
        raise ValueError("--warmup cannot be negative")
    for path in [PYTHON_MAIN, CONFIG_PATH, SCHEDULE_PATH, RUST_ROOT]:
        if not path.exists():
            raise FileNotFoundError(path)
    if args.skip_build and not RUST_BINARY.exists():
        raise FileNotFoundError(
            f"{RUST_BINARY} does not exist; run without --skip-build first"
        )


def run_command(command: list[str], cwd: Path) -> None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        command_text = " ".join(command)
        raise RuntimeError(
            f"Command failed with exit code {completed.returncode}: {command_text}\n"
            f"{completed.stderr.strip()}"
        )


def timed_command(command: list[str], cwd: Path) -> float:
    start = time.perf_counter()
    run_command(command, cwd)
    return time.perf_counter() - start


def benchmark(
    name: str,
    command: list[str],
    cwd: Path,
    warmup: int,
    iterations: int,
) -> BenchmarkResult:
    for _ in range(warmup):
        run_command(command, cwd)

    timings = [timed_command(command, cwd) for _ in range(iterations)]
    return BenchmarkResult(name=name, timings=timings)


def build_rust_release(skip_build: bool) -> None:
    if skip_build:
        return
    run_command(["cargo", "build", "--release"], RUST_ROOT)


def print_result(result: BenchmarkResult) -> None:
    print(
        f"{result.name:<8} "
        f"mean={result.mean * 1000:>9.3f} ms  "
        f"median={result.median * 1000:>9.3f} ms  "
        f"min={result.minimum * 1000:>9.3f} ms  "
        f"max={result.maximum * 1000:>9.3f} ms  "
        f"stdev={result.stdev * 1000:>9.3f} ms"
    )


def main() -> int:
    args = parse_args()
    validate_environment(args)
    build_rust_release(args.skip_build)

    output_root = Path(
        tempfile.mkdtemp(prefix="ischedule-benchmark-", dir=os.environ.get("TMPDIR"))
    )
    python_output = output_root / "python"
    rust_output = output_root / "rust"
    python_output.mkdir()
    rust_output.mkdir()

    python_command = [
        sys.executable,
        str(PYTHON_MAIN),
        "-nl",
        "-c",
        str(CONFIG_PATH),
        "-s",
        str(SCHEDULE_PATH),
        "-o",
        str(python_output),
    ]
    rust_command = [
        str(RUST_BINARY),
        "--nolog",
        "--config",
        str(CONFIG_PATH),
        "--schedule",
        str(SCHEDULE_PATH),
        "--output",
        str(rust_output),
    ]

    try:
        python_result = benchmark(
            "Python", python_command, PROJECT_ROOT, args.warmup, args.iterations
        )
        rust_result = benchmark(
            "Rust", rust_command, PROJECT_ROOT, args.warmup, args.iterations
        )

        print(f"Iterations: {args.iterations}, warmup: {args.warmup}")
        print(f"Output dir: {output_root}")
        print_result(python_result)
        print_result(rust_result)
        speedup = python_result.mean / rust_result.mean
        faster_percent = (speedup - 1.0) * 100.0
        print(f"Speedup: {speedup:.2f}x")
        print(f"Rust is {faster_percent:.1f}% faster than Python")
    finally:
        if args.keep_output:
            print(f"Kept output dir: {output_root}")
        else:
            shutil.rmtree(output_root, ignore_errors=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
