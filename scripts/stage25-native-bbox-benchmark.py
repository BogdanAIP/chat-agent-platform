#!/usr/bin/env python
"""Run the Stage 25 native LFM2.5-VL-450M bbox+zoom candidate."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image

from runtime.local_vision_adapter.grounding_runner import load_fixture_cases, summarize_results
from runtime.local_vision_adapter.native_bbox import (
    NativeBBoxLoopbackClient,
    run_native_bbox_zoom_case,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_checkpoint(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    os.replace(temp_path, path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument(
        "--case-id",
        action="append",
        default=[],
        help="Run only the named fixture case. Repeat to select multiple cases.",
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.image.is_file():
        raise SystemExit(f"image not found: {args.image}")
    if not args.cases.is_file():
        raise SystemExit(f"cases not found: {args.cases}")

    cases = load_fixture_cases(args.cases)
    if args.case_id:
        requested = set(args.case_id)
        known = {str(case["id"]) for case in cases}
        unknown = sorted(requested - known)
        if unknown:
            raise SystemExit(f"unknown case id(s): {', '.join(unknown)}")
        cases = [case for case in cases if str(case["id"]) in requested]

    client = NativeBBoxLoopbackClient(
        port=args.port,
        timeout_seconds=args.timeout_seconds,
    )

    with Image.open(args.image) as opened:
        source = opened.convert("RGB")

    rows: list[dict] = []
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "completed": False,
        "image": {
            "path": str(args.image.resolve()),
            "width": source.width,
            "height": source.height,
            "sha256": sha256_file(args.image),
        },
        "cases_path": str(args.cases.resolve()),
        "selected_case_ids": [str(case["id"]) for case in cases],
        "server_url": client.url,
        "method": "native-bbox-450m-zoom",
        "summary": None,
        "cases": rows,
    }
    write_checkpoint(args.output, payload)

    for index, case in enumerate(cases, start=1):
        print(
            f"[native-bbox] {index}/{len(cases)} {case['id']}: {case['instruction']}",
            flush=True,
        )
        row = run_native_bbox_zoom_case(
            client=client,
            source=source,
            case=case,
            artifact_dir=args.artifacts,
        )
        rows.append(row)
        payload["summary"] = summarize_results(rows)
        write_checkpoint(args.output, payload)

        score = row["score"]
        print(
            "  "
            f"decision={row['decision']} hit={score['point_hit']} "
            f"false_click={score['false_click']} abstained={score['abstained']} "
            f"error={row.get('parse_error')} latency={row['latency_seconds']}s",
            flush=True,
        )

    payload["completed"] = True
    write_checkpoint(args.output, payload)

    summary = payload["summary"]
    print("\n===== STAGE 25 NATIVE BBOX SUMMARY =====")
    print(
        f"point_accuracy={summary['point_accuracy']} "
        f"false_clicks={summary['false_clicks']} abstains={summary['abstains']} "
        f"errors={summary['malformed_or_provider_errors']} "
        f"mean_latency={summary['mean_latency_seconds']}s"
    )
    print(f"OUTPUT={args.output}")
    print("STAGE25_NATIVE_BBOX_CLIENT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
