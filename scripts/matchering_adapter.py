"""Constrained edge adapter for the optional Matchering reference-mastering engine.

This module is intentionally not part of the core Python package. The Rust platform
invokes it with a fixed verb and fixed file arguments; arbitrary Python code, shell
commands and Matchering options are not exposed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _matchering():
    try:
        import matchering as mg
    except Exception as exc:  # pragma: no cover - exercised by external probe
        raise RuntimeError(f"Matchering import failed: {exc}") from exc
    return mg


def _probe() -> int:
    mg = _matchering()
    version = getattr(mg, "__version__", None)
    print(
        json.dumps(
            {
                "status": "available",
                "engine": "matchering",
                "version": version or "unknown",
            }
        )
    )
    return 0


def _process(target: Path, reference: Path, output: Path) -> int:
    for label, path in (("target", target), ("reference", reference)):
        if not path.is_absolute():
            raise ValueError(f"{label} path must be absolute")
        if not path.is_file():
            raise FileNotFoundError(f"{label} file does not exist: {path}")
    if not output.is_absolute():
        raise ValueError("output path must be absolute")
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    mg = _matchering()
    mg.process(
        target=str(target),
        reference=str(reference),
        results=[mg.pcm24(str(output))],
    )
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("Matchering did not create a non-empty PCM24 WAV output")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest="verb", required=True)
    subparsers.add_parser("probe", add_help=False)
    process = subparsers.add_parser("process", add_help=False)
    process.add_argument("--target", type=Path, required=True)
    process.add_argument("--reference", type=Path, required=True)
    process.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    try:
        args = _parser().parse_args()
        if args.verb == "probe":
            return _probe()
        if args.verb == "process":
            return _process(args.target, args.reference, args.output)
        raise ValueError(f"unsupported adapter verb: {args.verb}")
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "error",
                    "engine": "matchering",
                    "message": str(exc),
                }
            ),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
