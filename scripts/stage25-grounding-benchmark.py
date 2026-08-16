#!/usr/bin/env python
"""Run Stage 25 Direct and/or faithful Mark-Grid grounding against a local server."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

from PIL import Image

from runtime.local_vision_adapter.grounding_runner import (
    load_fixture_cases,
    run_direct_case,
    run_mark_grid_case,
    summarize_results,
)
from runtime.local_vision_adapter.provider import LlamaCppLoopbackClient


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument(
        "--method",
        choices=("direct", "mark-grid", "both"),
        default="both",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=300.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.image.is_file():
        raise SystemExit(f"image not found: {args.image}")
    if not args.cases.is_file():
        raise SystemExit(f"cases not found: {args.cases}")

    cases = load_fixture_cases(args.cases)
    client = LlamaCppLoopbackClient(
        port=args.port,
        timeout_seconds=args.timeout_seconds,
    )

    with Image.open(args.image) as opened:
        source = opened.convert("RGB")

    selected_methods = (
        ("direct", "mark-grid") if args.method == "both" else (args.method,)
    )

    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "image": {
            "path": str(args.image.resolve()),
            "width": source.width,
            "height": source.height,
            "sha256": sha256_file(args.image),
        },
        "cases_path": str(args.cases.resolve()),
        "server_url": client.url,
        "methods": {},
    }

    for method in selected_methods:
        rows = []
        for index, case in enumerate(cases, start=1):
            print(
                f"[{method}] {index}/{len(cases)} {case['id']}: {case['instruction']}",
                flush=True,
            )
            if method == "direct":
                row = run_direct_case(
                    client=client,
                    source=source,
                    case=case,
                )
            else:
                row = run_mark_grid_case(
                    client=client,
                    source=source,
                    case=case,
                    artifact_dir=args.artifacts,
                )
            rows.append(row)
            point_hit = row["score"]["point_hit"]
            false_click = row["score"]["false_click"]
            abstained = row["score"]["abstained"]
            print(
                "  "
                f"hit={point_hit} false_click={false_click} abstained={abstained} "
                f"error={row.get('parse_error')} latency={row['latency_seconds']}s",
                flush=True,
            )

        payload["methods"][method] = {
            "summary": summarize_results(rows),
            "cases": rows,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n===== STAGE 25 GROUNDING BENCHMARK SUMMARY =====")
    for method, value in payload["methods"].items():
        summary = value["summary"]
        print(
            f"{method}: point_accuracy={summary['point_accuracy']} "
            f"false_clicks={summary['false_clicks']} abstains={summary['abstains']} "
            f"errors={summary['malformed_or_provider_errors']} "
            f"mean_latency={summary['mean_latency_seconds']}s"
        )
    print(f"OUTPUT={args.output}")
    print("STAGE25_GROUNDING_BENCHMARK_CLIENT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
