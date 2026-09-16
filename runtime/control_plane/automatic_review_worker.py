from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from runtime.agent_sessions import chatgpt_temporary, source_attestation
from runtime.control_plane.independent_review_delegation import (
    prepare_review_delegation,
    settle_review_from_delegation,
)
from runtime.control_plane.independent_review_state import (
    ReviewStateError,
    parse_review_identity,
    prepare_review_operation,
    review_operation_key,
)


_CONTROLLER_MODULE = "runtime.agent_sessions.chatgpt_temporary_authenticated_controller"
_CONTROLLER_PORT = chatgpt_temporary.COLLECTOR_PORT
_CONTROLLER_TIMEOUT_SECONDS = 1800
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_GENERATION_RE = re.compile(
    r'CAPChatGPTTemporaryExecutionGeneration\s*=\s*"([0-9a-f]{64})"'
)
_REPOSITORY = "BogdanAIP/chat-agent-platform"
_BRANCH = "main"


def _read_json(path: Path, *, label: str, maximum: int = 2_000_000) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ReviewStateError(f"{label} is unavailable") from exc
    if not raw or len(raw) > maximum:
        raise ReviewStateError(f"{label} has invalid size")
    try:
        value = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewStateError(f"{label} is invalid JSON") from exc
    if type(value) is not dict:
        raise ReviewStateError(f"{label} must be a JSON object")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    payload = json.dumps(
        dict(value),
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ).encode("utf-8")
    path.write_bytes(payload)


def _write_text(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8", newline="\n")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _installed_head(local_root: Path) -> str:
    state = _read_json(
        local_root / "state" / "platform-update.json",
        label="installed-version state",
        maximum=64_000,
    )
    expected = {
        "schema_version",
        "repository",
        "branch",
        "installed_commit_sha",
        "installed_at",
        "status",
        "target_commit_sha",
        "last_checked_at",
        "last_error",
    }
    if set(state) != expected:
        raise ReviewStateError("installed-version state keys mismatch")
    if state["schema_version"] != 1:
        raise ReviewStateError("installed-version state schema mismatch")
    if state["repository"] != _REPOSITORY or state["branch"] != _BRANCH:
        raise ReviewStateError("installed-version source identity mismatch")
    if state["status"] not in {"current", "update_available"}:
        raise ReviewStateError("installed runtime is not in a reviewer-safe update state")
    head = state["installed_commit_sha"]
    if type(head) is not str or _HEX40_RE.fullmatch(head) is None:
        raise ReviewStateError("installed runtime has no exact accepted-main identity")
    return head


def _expected_runtime_attestation(
    app_root: Path,
    *,
    expected_head: str,
) -> dict[str, Any]:
    extension_root = app_root / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"
    if not extension_root.is_dir():
        raise ReviewStateError("installed reviewer extension is unavailable")

    generation_path = extension_root / "execution_generation.js"
    try:
        generation_text = generation_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ReviewStateError("installed reviewer execution generation is unavailable") from exc
    match = _GENERATION_RE.search(generation_text)
    if match is None:
        raise ReviewStateError("installed reviewer execution generation is invalid")
    execution_generation = match.group(1)

    assets: dict[str, str] = {}
    for name in source_attestation.RUNTIME_ASSETS:
        path = extension_root / name
        if not path.is_file():
            raise ReviewStateError(f"installed reviewer extension asset is missing: {name}")
        assets[name] = _sha256_file(path)

    return {
        "schema_version": 1,
        "adapter_id": source_attestation.ADAPTER_ID,
        "expected_head": expected_head,
        "execution_generation": execution_generation,
        "assets": assets,
    }


def _controller_command(
    app_root: Path,
    *,
    identity_path: Path,
    task_path: Path,
    attestation_path: Path,
    state_root: Path,
    output_dir: Path,
) -> list[str]:
    bootstrap = (
        "import runpy,sys;"
        "root=sys.argv.pop(1);"
        "sys.path.insert(0,root);"
        f'runpy.run_module("{_CONTROLLER_MODULE}",run_name="__main__")'
    )
    return [
        sys.executable,
        "-I",
        "-B",
        "-S",
        "-c",
        bootstrap,
        str(app_root),
        "--identity-json",
        str(identity_path),
        "--task-file",
        str(task_path),
        "--runtime-attestation-json",
        str(attestation_path),
        "--state-root",
        str(state_root),
        "--output-dir",
        str(output_dir),
        "--port",
        str(_CONTROLLER_PORT),
        "--timeout-seconds",
        str(_CONTROLLER_TIMEOUT_SECONDS),
    ]


def _health() -> dict[str, Any] | None:
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{_CONTROLLER_PORT}/health",
            timeout=2.0,
        ) as response:
            if response.status != 200:
                return None
            raw = response.read(64_000)
    except (OSError, urllib.error.URLError):
        return None
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if type(value) is dict else None


def _assert_listener_owner(pid: int) -> None:
    """Defense-in-depth ownership proof before opening the browser preflight."""

    pwsh = "pwsh.exe"
    script = (
        "$expected=[int]$args[0];"
        f"$rows=@(Get-NetTCPConnection -State Listen -LocalAddress '127.0.0.1' -LocalPort {_CONTROLLER_PORT} "
        "-ErrorAction SilentlyContinue);"
        "if($rows.Count -ne 1){exit 11};"
        "if([int]$rows[0].OwningProcess -ne $expected){exit 12};"
        "exit 0"
    )
    try:
        completed = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script, str(pid)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewStateError("reviewer controller listener ownership could not be proven") from exc
    if completed.returncode != 0:
        raise ReviewStateError("reviewer controller does not own the pinned loopback listener")


def _wait_for_controller(process: subprocess.Popen[bytes]) -> dict[str, Any]:
    deadline = time.monotonic() + 20.0
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise ReviewStateError("reviewer controller exited before becoming ready")
        value = _health()
        if (
            value is not None
            and value.get("adapter_id") == chatgpt_temporary.ADAPTER_ID
            and value.get("status") in {"preflight", "ready"}
        ):
            _assert_listener_owner(process.pid)
            return value
        time.sleep(0.2)
    raise ReviewStateError("reviewer controller did not become ready")


def _open_preflight(output_dir: Path) -> None:
    preflight = _read_json(output_dir / "preflight.json", label="reviewer preflight", maximum=64_000)
    if preflight.get("adapter_id") != chatgpt_temporary.ADAPTER_ID:
        raise ReviewStateError("reviewer preflight adapter mismatch")
    url = preflight.get("preflight_url")
    if type(url) is not str or re.fullmatch(
        r"https://chatgpt\.com/\?cap_agent_preflight=1#cap_preflight_id=[0-9a-f]{64}",
        url,
    ) is None:
        raise ReviewStateError("reviewer preflight URL is outside the accepted neutral shape")
    if any(marker in url for marker in ("cap_run_id", "cap_delegation_id", "cap_delivery_id", "prompt=", "temporary-chat")):
        raise ReviewStateError("reviewer preflight URL contains task/private launch material")
    try:
        os.startfile(url)  # type: ignore[attr-defined]
    except OSError as exc:
        raise ReviewStateError("reviewer browser preflight could not be opened") from exc


def _wait_terminal(
    process: subprocess.Popen[bytes],
    *,
    output_dir: Path,
) -> None:
    deadline = time.monotonic() + _CONTROLLER_TIMEOUT_SECONDS + 30
    result_path = output_dir / "result.json"
    while time.monotonic() < deadline:
        if result_path.is_file():
            return
        if process.poll() is not None:
            return
        time.sleep(0.5)


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
        process.wait(timeout=5)
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def _run(args: argparse.Namespace) -> int:
    if os.name != "nt":
        raise ReviewStateError("automatic reviewer worker requires Windows")

    identity = parse_review_identity(
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
    state_root = Path(args.state_root).resolve()

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        raise ReviewStateError("LOCALAPPDATA is unavailable")
    local_root = (Path(local_app_data) / "ChatAgentPlatform").resolve()
    expected_state_root = (local_root / "state").resolve()
    if state_root != expected_state_root and not state_root.is_relative_to(expected_state_root):
        raise ReviewStateError("reviewer state root must stay under the installed CAP state root")

    app_root = (local_root / "app").resolve()
    if not app_root.is_dir():
        raise ReviewStateError("installed Chat Agent Platform app root is unavailable")

    expected_head = _installed_head(local_root)
    prepared_review = prepare_review_operation(identity.as_dict(), state_root=state_root)
    if prepared_review.dispatch_state != "dispatch-attempted" or prepared_review.result_state != "open":
        raise ReviewStateError("reviewer worker requires one open dispatch-attempted review operation")

    task, delegation_identity = prepare_review_delegation(
        prepared_review.identity,
        review_run_id=prepared_review.review_run_id,
        state_root=state_root,
    )

    operation_key = review_operation_key(identity)
    output_dir = (local_root / "state" / "reviewer-worker-v1" / operation_key).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "preflight.json",
        "launch.json",
        "result.json",
        "controller.stdout.log",
        "controller.stderr.log",
    ):
        (output_dir / name).unlink(missing_ok=True)

    identity_path = output_dir / "identity.json"
    task_path = output_dir / "task.txt"
    attestation_path = output_dir / "expected-runtime-attestation.json"

    _write_json(identity_path, delegation_identity)
    _write_text(task_path, task)
    _write_json(
        attestation_path,
        _expected_runtime_attestation(app_root, expected_head=expected_head),
    )

    stdout_path = output_dir / "controller.stdout.log"
    stderr_path = output_dir / "controller.stderr.log"
    with stdout_path.open("wb") as stdout_handle, stderr_path.open("wb") as stderr_handle:
        process = subprocess.Popen(
            _controller_command(
                app_root,
                identity_path=identity_path,
                task_path=task_path,
                attestation_path=attestation_path,
                state_root=state_root,
                output_dir=output_dir,
            ),
            cwd=str(app_root),
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            close_fds=True,
            creationflags=int(getattr(subprocess, "CREATE_NO_WINDOW", 0)),
        )
        try:
            phase = _wait_for_controller(process)
            if phase.get("status") == "preflight":
                _open_preflight(output_dir)
            _wait_terminal(process, output_dir=output_dir)

            settled = settle_review_from_delegation(identity.as_dict(), state_root=state_root)
            if settled is not None and settled.get("status") in {"recorded", "already_recorded"}:
                return 0

            # The controller may have durably recorded the generic terminal
            # result immediately before process exit. Give settlement one final
            # bounded retry without granting any new launch/Send authority.
            time.sleep(0.2)
            settled = settle_review_from_delegation(identity.as_dict(), state_root=state_root)
            if settled is not None and settled.get("status") in {"recorded", "already_recorded"}:
                return 0
            return 3
        finally:
            _terminate(process)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="One-shot automatic independent-review worker owner")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", type=int, required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--review-skill", required=True)
    parser.add_argument("--review-skill-version", required=True)
    parser.add_argument("--state-root", required=True)
    return parser


def main() -> int:
    try:
        return _run(_parser().parse_args())
    except (ReviewStateError, OSError, ValueError):
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
