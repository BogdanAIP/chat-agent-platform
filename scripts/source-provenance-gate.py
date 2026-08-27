from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


_HEX_COMMIT = re.compile(r"^[0-9a-f]{40,64}$")


class ProvenanceError(RuntimeError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run_git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise ProvenanceError(f"git {' '.join(args)} failed ({completed.returncode}): {detail}")
    return completed


def _normalize_relative_path(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ProvenanceError("asset path must be a non-empty relative path")
    raw = value.strip().replace("\\", "/")
    candidate = PurePosixPath(raw)
    if candidate.is_absolute() or raw.startswith("/"):
        raise ProvenanceError(f"asset path must be relative: {value}")
    if any(part in {"", ".", ".."} for part in candidate.parts):
        raise ProvenanceError(f"asset path contains unsafe traversal or empty component: {value}")
    normalized = candidate.as_posix()
    if normalized == ".git" or normalized.startswith(".git/"):
        raise ProvenanceError(".git paths are not valid provenance assets")
    return normalized


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dedupe(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = _normalize_relative_path(value)
        if normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def _asset_record(repo: Path, expected_head: str, relative_path: str) -> dict[str, Any]:
    local_path = repo.joinpath(*PurePosixPath(relative_path).parts)
    if not local_path.is_file():
        raise ProvenanceError(f"provenance asset is missing or not a file: {relative_path}")

    _run_git(repo, "ls-files", "--error-unmatch", "--", relative_path)
    expected_blob = _run_git(repo, "rev-parse", f"{expected_head}:{relative_path}").stdout.strip()
    # --path applies the repository's clean filters/attributes before hashing,
    # so a clean Windows checkout using CRLF conversion still compares to the
    # committed Git blob while the separate SHA-256 below records local bytes.
    local_blob = _run_git(
        repo,
        "hash-object",
        f"--path={relative_path}",
        "--",
        str(local_path),
    ).stdout.strip()
    return {
        "git_blob_expected": expected_blob,
        "git_blob_local_clean_filtered": local_blob,
        "matches_expected_blob": local_blob == expected_blob,
        "sha256": _sha256(local_path),
        "size": local_path.stat().st_size,
    }


def collect_source_provenance(
    *,
    repo_root: Path,
    expected_head: str,
    critical_assets: Iterable[str],
    lockfiles: Iterable[str] = (),
) -> dict[str, Any]:
    repo = repo_root.resolve()
    if not repo.is_dir():
        raise ProvenanceError(f"repository root does not exist: {repo}")
    if not _HEX_COMMIT.fullmatch(expected_head):
        raise ProvenanceError("expected head must be a full lowercase hexadecimal commit id")

    top_level = Path(_run_git(repo, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    if top_level != repo:
        raise ProvenanceError(f"repo-root is not the Git worktree root: expected={repo} actual={top_level}")

    actual_head = _run_git(repo, "rev-parse", "HEAD").stdout.strip()
    status_lines = [
        line
        for line in _run_git(repo, "status", "--porcelain=v1", "--untracked-files=all").stdout.splitlines()
        if line
    ]

    unstaged = _run_git(repo, "diff", "--no-ext-diff", "--quiet", "--", check=False)
    staged = _run_git(repo, "diff", "--cached", "--no-ext-diff", "--quiet", "--", check=False)
    if unstaged.returncode not in (0, 1):
        raise ProvenanceError(f"git diff failed with exit code {unstaged.returncode}")
    if staged.returncode not in (0, 1):
        raise ProvenanceError(f"git diff --cached failed with exit code {staged.returncode}")

    untracked = [line for line in status_lines if line.startswith("?? ")]
    tracked_status = [line for line in status_lines if not line.startswith("?? ")]
    tracked_diff_empty = unstaged.returncode == 0 and staged.returncode == 0 and not tracked_status
    untracked_empty = not untracked
    working_tree_clean = not status_lines

    assets = _dedupe(critical_assets)
    locks = _dedupe(lockfiles)
    if not assets:
        raise ProvenanceError("at least one critical asset must be bound")
    overlap = set(assets).intersection(locks)
    if overlap:
        raise ProvenanceError(f"paths cannot be both critical assets and lockfiles: {sorted(overlap)}")

    asset_records = {path: _asset_record(repo, expected_head, path) for path in assets}
    lock_records = {path: _asset_record(repo, expected_head, path) for path in locks}
    asset_blobs_match = all(record["matches_expected_blob"] for record in asset_records.values())
    lock_blobs_match = all(record["matches_expected_blob"] for record in lock_records.values())

    git_version = _run_git(repo, "--version").stdout.strip()
    passed = bool(
        actual_head == expected_head
        and working_tree_clean
        and tracked_diff_empty
        and untracked_empty
        and asset_blobs_match
        and lock_blobs_match
    )

    reasons: list[str] = []
    if actual_head != expected_head:
        reasons.append("head_mismatch")
    if not tracked_diff_empty:
        reasons.append("tracked_diff_present")
    if not untracked_empty:
        reasons.append("untracked_files_present")
    if not asset_blobs_match:
        reasons.append("critical_asset_blob_mismatch")
    if not lock_blobs_match:
        reasons.append("lockfile_blob_mismatch")

    return {
        "schema_version": 1,
        "status": "pass" if passed else "fail",
        "reason": "source_provenance_verified" if passed else ",".join(reasons) or "source_provenance_failed",
        "captured_at": _utc_now(),
        "source_root": str(repo),
        "expected_head": expected_head,
        "actual_head": actual_head,
        "working_tree_clean": working_tree_clean,
        "tracked_diff_empty": tracked_diff_empty,
        "untracked_empty": untracked_empty,
        "status_porcelain": status_lines,
        "critical_assets": asset_records,
        "lockfiles": lock_records,
        "runtime": {
            "python": sys.version.splitlines()[0],
            "git": git_version,
        },
    }


def _write_result(path: Path, result: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind physical acceptance to an exact clean Git worktree and critical source hashes.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--asset", action="append", default=[])
    parser.add_argument("--lockfile", action="append", default=[])
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    try:
        # Evidence output belongs outside the source checkout so the gate cannot
        # make the tree dirty merely by recording its own result.
        try:
            output.relative_to(repo)
        except ValueError:
            pass
        else:
            raise ProvenanceError("provenance output must be outside the repository source root")

        result = collect_source_provenance(
            repo_root=repo,
            expected_head=args.expected_head,
            critical_assets=args.asset,
            lockfiles=args.lockfile,
        )
    except BaseException as exc:
        result = {
            "schema_version": 1,
            "status": "fail",
            "reason": "source_provenance_runtime_error",
            "captured_at": _utc_now(),
            "source_root": str(repo),
            "expected_head": args.expected_head,
            "actual_head": None,
            "working_tree_clean": False,
            "tracked_diff_empty": False,
            "untracked_empty": False,
            "status_porcelain": [],
            "critical_assets": {},
            "lockfiles": {},
            "runtime": {"python": sys.version.splitlines()[0]},
            "error": f"{type(exc).__name__}: {exc}",
        }

    _write_result(output, result)
    print(f"SOURCE_PROVENANCE_RESULT={output}")
    print(f"EXPECTED_HEAD={result.get('expected_head')}")
    print(f"ACTUAL_HEAD={result.get('actual_head')}")
    print(f"WORKING_TREE_CLEAN={result.get('working_tree_clean')}")
    print(f"TRACKED_DIFF_EMPTY={result.get('tracked_diff_empty')}")
    print(f"UNTRACKED_EMPTY={result.get('untracked_empty')}")
    print(f"SOURCE_PROVENANCE_GATE={'PASS' if result.get('status') == 'pass' else 'FAIL'}")
    if result.get("error"):
        print(f"SOURCE_PROVENANCE_ERROR={result['error']}")
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
