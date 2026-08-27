from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Any


class RecheckError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise RecheckError(f"JSON root must be an object: {path}")
    return value


def _run_git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RecheckError(f"git {' '.join(args)} failed ({completed.returncode}): {detail}")
    return completed.stdout


def _safe_repo_asset(source_root: Path, relative: str) -> Path:
    raw = relative.replace("\\", "/")
    rel = PurePosixPath(raw)
    if rel.is_absolute() or not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
        raise RecheckError(f"unsafe source asset path: {relative}")
    candidate = source_root.joinpath(*rel.parts)
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(source_root)
    except ValueError as exc:
        raise RecheckError(f"source asset escaped source root: {relative}") from exc
    if not resolved.is_file():
        raise RecheckError(f"source asset is not a file: {relative}")
    return resolved


def _safe_record_path(raw: str, root: Path, *, label: str) -> Path:
    candidate = Path(raw).resolve(strict=True)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise RecheckError(f"{label} escaped its recorded root: {candidate}") from exc
    if not candidate.is_file():
        raise RecheckError(f"{label} is not a file: {candidate}")
    return candidate


def _recheck_source(initial: dict[str, Any], expected_head: str) -> dict[str, bool | str]:
    source_root = Path(str(initial["source_root"])).resolve(strict=True)
    if not source_root.is_dir():
        raise RecheckError("recorded source root is not a directory")

    current_head = _run_git(source_root, "rev-parse", "HEAD").strip()
    status_lines = [
        line
        for line in _run_git(source_root, "status", "--porcelain=v1", "--untracked-files=all").splitlines()
        if line
    ]
    head_pass = current_head == expected_head == str(initial.get("expected_head"))
    clean_pass = not status_lines

    hashes_pass = True
    for group_name in ("critical_assets", "lockfiles"):
        group = initial.get(group_name)
        if not isinstance(group, dict):
            raise RecheckError(f"initial source provenance missing {group_name}")
        for relative, record in group.items():
            if not isinstance(record, dict):
                raise RecheckError(f"invalid source provenance record: {relative}")
            current = _safe_repo_asset(source_root, str(relative))
            expected_sha = str(record.get("sha256") or "")
            if len(expected_sha) != 64 or _sha256(current) != expected_sha:
                hashes_pass = False

    return {
        "current_head": current_head,
        "source_head_pass": head_pass,
        "source_clean_pass": clean_pass,
        "source_hashes_pass": hashes_pass,
    }


def _recheck_installed(initial: dict[str, Any], expected_head: str) -> bool:
    if str(initial.get("exact_head")) != expected_head or not bool(initial.get("all_match")):
        return False
    source_root = Path(str(initial["source_root"])).resolve(strict=True)
    installed_root = Path(str(initial["installed_root"])).resolve(strict=True)
    assets = initial.get("assets")
    if not isinstance(assets, list) or len(assets) < 8:
        return False

    for record in assets:
        if not isinstance(record, dict) or not bool(record.get("match")):
            return False
        source = _safe_record_path(str(record["source"]), source_root, label="installed-record source")
        installed = _safe_record_path(
            str(record["installed"]), installed_root, label="installed-record installed file"
        )
        source_sha = _sha256(source)
        installed_sha = _sha256(installed)
        if source_sha != str(record.get("source_sha256")):
            return False
        if installed_sha != str(record.get("installed_sha256")):
            return False
        if source_sha != installed_sha:
            return False
    return True


def _recheck_runtime(initial: dict[str, Any], source_root: Path) -> dict[str, bool | str | None]:
    expected_version = str(initial.get("expected_version") or "")
    initial_installed_version = str(initial.get("installed_version") or "")
    installed_version = metadata.version("openadapt-flow")
    version_pass = bool(
        initial.get("status") == "pass"
        and initial.get("version_match") is True
        and expected_version
        and installed_version == expected_version == initial_installed_version
    )

    from openadapt_flow.backends.win_agent import server

    server_file_raw = getattr(server, "__file__", None)
    if not server_file_raw:
        raise RecheckError("OpenAdapt win_agent server module has no source path")
    server_path = Path(server_file_raw).resolve(strict=True)
    initial_server_path = Path(str(initial.get("win_agent_server_path") or "")).resolve(strict=True)
    server_hash = _sha256(server_path)
    server_hash_pass = bool(
        server_path == initial_server_path
        and server_hash == str(initial.get("win_agent_server_sha256") or "")
    )

    lock_path = Path(str(initial.get("lockfile") or "")).resolve(strict=True)
    try:
        lock_path.relative_to(source_root)
    except ValueError as exc:
        raise RecheckError("runtime lockfile escaped source root") from exc
    lock_hash_pass = bool(
        lock_path.is_file()
        and _sha256(lock_path) == str(initial.get("lockfile_sha256") or "")
    )

    return {
        "runtime_version_pass": version_pass,
        "runtime_server_hash_pass": server_hash_pass,
        "runtime_lock_hash_pass": lock_hash_pass,
        "runtime_installed_version": installed_version,
        "runtime_server_path": str(server_path),
        "runtime_server_sha256": server_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Revalidate Windows L3 source, installed runtime and OpenAdapt provenance at Finish Gate time."
    )
    parser.add_argument("--qualification-root", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    qualification_root = Path(args.qualification_root).resolve(strict=True)
    output = Path(args.output).resolve(strict=False)
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": "fail",
        "expected_head": None,
        "current_head": None,
        "source_head_pass": False,
        "source_clean_pass": False,
        "source_hashes_pass": False,
        "installed_hashes_pass": False,
        "runtime_version_pass": False,
        "runtime_server_hash_pass": False,
        "runtime_lock_hash_pass": False,
        "runtime_installed_version": None,
        "runtime_server_path": None,
        "runtime_server_sha256": None,
        "python_executable": sys.executable,
        "error": None,
    }

    try:
        manifest = _load_json(qualification_root / "gate-manifest.json")
        expected_head = str(manifest["exact_head"])
        source_initial = _load_json(Path(str(manifest["source_provenance_path"])).resolve(strict=True))
        installed_initial = _load_json(
            Path(str(manifest["installed_runtime_provenance_path"])).resolve(strict=True)
        )
        runtime_initial = _load_json(Path(str(manifest["runtime_attestation_path"])).resolve(strict=True))

        source = _recheck_source(source_initial, expected_head)
        source_root = Path(str(source_initial["source_root"])).resolve(strict=True)
        installed_pass = _recheck_installed(installed_initial, expected_head)
        runtime = _recheck_runtime(runtime_initial, source_root)

        result.update(source)
        result.update(runtime)
        result["expected_head"] = expected_head
        result["installed_hashes_pass"] = installed_pass
        passed = bool(
            result["source_head_pass"]
            and result["source_clean_pass"]
            and result["source_hashes_pass"]
            and result["installed_hashes_pass"]
            and result["runtime_version_pass"]
            and result["runtime_server_hash_pass"]
            and result["runtime_lock_hash_pass"]
        )
        result["status"] = "pass" if passed else "fail"
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"WINDOWS_L3_PROVENANCE_RECHECK={output}")
    print(f"SOURCE_HEAD_PASS={result['source_head_pass']}")
    print(f"SOURCE_CLEAN_PASS={result['source_clean_pass']}")
    print(f"SOURCE_HASHES_PASS={result['source_hashes_pass']}")
    print(f"INSTALLED_HASHES_PASS={result['installed_hashes_pass']}")
    print(f"RUNTIME_VERSION_PASS={result['runtime_version_pass']}")
    print(f"RUNTIME_SERVER_HASH_PASS={result['runtime_server_hash_pass']}")
    print(f"RUNTIME_LOCK_HASH_PASS={result['runtime_lock_hash_pass']}")
    print(f"WINDOWS_L3_PROVENANCE_RECHECK_STATUS={result['status'].upper()}")
    if result.get("error"):
        print(f"WINDOWS_L3_PROVENANCE_RECHECK_ERROR={result['error']}")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
