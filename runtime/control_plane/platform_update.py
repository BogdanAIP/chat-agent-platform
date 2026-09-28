from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any


PROCEDURE_ID = "platform_update_v1"
_MAX_JSON_BYTES = 64 * 1024
_CHECK_TIMEOUT_SECONDS = 120


def _local_root(local_app_data: Path | None = None) -> Path:
    if local_app_data is None:
        raw = os.environ.get("LOCALAPPDATA")
        if not raw:
            raise RuntimeError("LOCALAPPDATA is required for platform update")
        local_app_data = Path(raw)
    return Path(local_app_data) / "ChatAgentPlatform"


def _paths(local_app_data: Path | None = None) -> dict[str, Path]:
    root = _local_root(local_app_data)
    return {
        "root": root,
        "updater": root / "app" / "scripts" / "chat-platform-update.ps1",
        "state": root / "state" / "platform-update.json",
        "result": root / "state" / "platform-update-result.json",
    }


def _require_windows() -> None:
    if os.name != "nt":
        raise RuntimeError("platform update procedure is available only on Windows")


def _pwsh() -> str:
    executable = shutil.which("pwsh.exe") or shutil.which("pwsh")
    if not executable:
        raise RuntimeError("PowerShell 7 (pwsh.exe) is required")
    return str(Path(executable).resolve())


def _require_updater(path: Path) -> Path:
    if not path.is_file():
        raise RuntimeError("installed platform updater is missing")
    return path.resolve()


def _read_bounded_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    if not path.is_file():
        raise RuntimeError(f"platform update state is not a regular file: {path.name}")
    size = path.stat().st_size
    if size > _MAX_JSON_BYTES:
        raise RuntimeError(f"platform update state exceeds {_MAX_JSON_BYTES} bytes: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"platform update state is invalid JSON: {path.name}") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"platform update state must be a JSON object: {path.name}")
    return value


def _parse_updater_stdout(stdout: str) -> dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("platform updater returned no JSON result")
    try:
        value = json.loads(lines[-1])
    except Exception as exc:
        raise RuntimeError("platform updater returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("platform updater result must be a JSON object")
    return value


def _fixed_argv(updater: Path, action: str) -> list[str]:
    return [
        _pwsh(),
        "-NoLogo",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(updater),
        "-Action",
        action,
    ]


def _check(paths: dict[str, Path]) -> dict[str, Any]:
    updater = _require_updater(paths["updater"])
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    completed = subprocess.run(
        _fixed_argv(updater, "Check"),
        cwd=str(updater.parent),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_CHECK_TIMEOUT_SECONDS,
        shell=False,
        creationflags=creationflags,
        check=False,
    )
    result = _parse_updater_stdout(completed.stdout)
    if completed.returncode not in {0, 3, 4} and result.get("status") != "error":
        raise RuntimeError(f"platform updater check failed with exit code {completed.returncode}")
    return {
        "schema_version": 1,
        "status": "completed",
        "action": "check",
        "updater": result,
    }


def _request_update(paths: dict[str, Path]) -> dict[str, Any]:
    updater = _require_updater(paths["updater"])
    creationflags = (
        getattr(subprocess, "CREATE_NO_WINDOW", 0)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0)
    )
    process = subprocess.Popen(
        _fixed_argv(updater, "Update"),
        cwd=str(updater.parent),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
        close_fds=True,
        creationflags=creationflags,
    )
    return {
        "schema_version": 1,
        "status": "accepted",
        "action": "request_update",
        "process_id": int(process.pid),
        "outcome_verified": False,
        "reconcile_with": "platform_update_v1:status",
    }


def _status(paths: dict[str, Path]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "completed",
        "action": "status",
        "state": _read_bounded_json(paths["state"]),
        "result": _read_bounded_json(paths["result"]),
    }


def run_platform_update(
    request: dict[str, Any],
    *,
    local_app_data: Path | None = None,
) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("request must be an object")
    if set(request) != {"procedure", "action"}:
        raise ValueError("platform update request accepts only procedure and action")
    if request.get("procedure") != PROCEDURE_ID:
        raise ValueError("unexpected procedure id")
    action = request.get("action")
    if action not in {"check", "request_update", "status"}:
        raise ValueError("unsupported platform update action")

    _require_windows()
    paths = _paths(local_app_data)
    if action == "check":
        return _check(paths)
    if action == "request_update":
        return _request_update(paths)
    return _status(paths)
