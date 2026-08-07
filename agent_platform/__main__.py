from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .audit import write_capability_audit
from .bootstrap import build_bootstrap_context
from .errors import PlatformError
from .service import build_runtime_profile, inspect_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Chat Agent Platform vertical slice")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="Write the local runtime capability profile")
    probe.add_argument("--project-id")

    bootstrap = subparsers.add_parser("bootstrap", help="Resolve project and load minimal context")
    bootstrap.add_argument("--project-id")
    bootstrap.add_argument("--capability", required=True)

    audit = subparsers.add_parser("audit", help="Generate the capability audit Markdown view")
    audit.add_argument("--project-id")

    inspect = subparsers.add_parser("inspect", help="Import and inspect a local media artifact")
    inspect.add_argument("--project-id")
    inspect.add_argument("--file", required=True, type=Path)
    inspect.add_argument(
        "--data-class",
        choices=["public", "project", "private", "sensitive"],
        default="project",
    )
    inspect.add_argument("--requested-risk-hint")

    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    try:
        if args.command == "probe":
            result = build_runtime_profile(repo_root, args.project_id)
            output = repo_root / "runtime" / "capability-profile.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        elif args.command == "bootstrap":
            result = build_bootstrap_context(
                repo_root, project_id=args.project_id, capability=args.capability
            )
        elif args.command == "audit":
            output = write_capability_audit(repo_root, project_id=args.project_id)
            result = {"status": "success", "output": str(output)}
        else:
            result = inspect_file(
                repo_root,
                args.file,
                project_id=args.project_id,
                data_class=args.data_class,
                requested_risk_hint=args.requested_risk_hint,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except PlatformError as exc:
        print(json.dumps({"status": "error", "error": exc.as_dict()}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
