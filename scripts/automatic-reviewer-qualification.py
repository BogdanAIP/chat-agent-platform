from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.control_plane.independent_review_delegation import (
    review_delegation_identity,
    review_delegation_state_root,
    settle_review_from_delegation,
)
from runtime.control_plane.independent_review_state import (
    ReviewStateError,
    mark_dispatch_attempted,
    parse_review_identity,
    prepare_review_operation,
    reconcile_independent_review_result,
)


def _identity(args: argparse.Namespace):
    return parse_review_identity(
        {
            "repository": args.repository,
            "pr_number": args.pr_number,
            "base_sha": args.base_sha,
            "head_sha": args.head_sha,
            "review_skill": args.review_skill,
            "review_skill_version": args.review_skill_version,
        },
        exact_keys=True,
    )


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def prepare(args: argparse.Namespace) -> int:
    identity = _identity(args)
    state_root = Path(args.reviewer_state_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    prepared = prepare_review_operation(identity.as_dict(), state_root=state_root)
    if prepared.result_state != "open":
        raise ReviewStateError("qualification review operation is already closed")
    if prepared.dispatch_state == "prepared":
        mark_dispatch_attempted(identity.as_dict(), state_root=state_root)
    elif prepared.dispatch_state != "dispatch-attempted":
        raise ReviewStateError("qualification review operation has invalid dispatch state")

    task, delegation_identity = review_delegation_identity(
        prepared.identity,
        review_run_id=prepared.review_run_id,
    )
    task_path = output_dir / "review-task.txt"
    task_path.write_text(task, encoding="utf-8", newline="\n")

    meta = {
        "schema_version": 1,
        "task_file": str(task_path),
        "parent_task_id": delegation_identity["parent_task_id"],
        "subgoal_id": delegation_identity["subgoal_id"],
        "worker_kind": delegation_identity["worker_kind"],
        "worker_profile": delegation_identity["worker_profile"],
        "result_contract_id": delegation_identity["result_contract_id"],
        "task_sha256": delegation_identity["task_sha256"],
        "review_operation_key": prepared.operation_key,
        "reviewer_state_root": str(state_root),
    }
    _write_json(output_dir / "prepare.json", meta)
    print(json.dumps(meta, ensure_ascii=False, sort_keys=True))
    return 0


def settle(args: argparse.Namespace) -> int:
    identity = _identity(args)
    reviewer_state_root = Path(args.reviewer_state_root).resolve()
    settlement = settle_review_from_delegation(
        identity.as_dict(),
        reviewer_state_root=reviewer_state_root,
        delegation_state_root=review_delegation_state_root(),
    )
    if settlement is None:
        print(json.dumps({"status": "pending"}, sort_keys=True))
        return 3
    if settlement.get("status") == "worker_terminal_noncompleting":
        print(json.dumps(settlement, ensure_ascii=False, sort_keys=True))
        return 3

    result = reconcile_independent_review_result(
        identity.as_dict(),
        state_root=reviewer_state_root,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result.get("result_state") == "automatic-result-recorded" else 3


def _add_identity(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--review-skill", default="code-review")
    parser.add_argument("--review-skill-version", default="1.1")
    parser.add_argument("--reviewer-state-root", required=True)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Exact-head automatic-reviewer qualification adapter"
    )
    sub = root.add_subparsers(dest="action", required=True)

    prepare_parser = sub.add_parser("prepare")
    _add_identity(prepare_parser)
    prepare_parser.add_argument("--output-dir", required=True)
    prepare_parser.set_defaults(handler=prepare)

    settle_parser = sub.add_parser("settle")
    _add_identity(settle_parser)
    settle_parser.set_defaults(handler=settle)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        return args.handler(args)
    except (ReviewStateError, OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "reason": type(exc).__name__}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
