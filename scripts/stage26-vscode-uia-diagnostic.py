from __future__ import annotations

import importlib.util
import json
import os
import secrets
import subprocess
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

from runtime.windows.observation import DesktopState, _query_process_identity, observe_bound_window
from runtime.windows.window_scoped_uia import WindowScopedUiaResolver


SAMPLE_COUNT = 4
SAMPLE_INTERVAL_SECONDS = 0.75
QUALIFICATION_PREFIX = "chat-agent-stage26e-vscode-diag-"
EXPECTED_EXECUTABLE = "code.exe"
EDITOR_ROLES = {"textbox", "document", "pane", "custom", "group", "edit"}


def _load_stage_driver() -> Any:
    path = Path(__file__).with_name("stage26-vscode-real-app-e2e.py")
    spec = importlib.util.spec_from_file_location("stage26_vscode_real_app_e2e", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load Stage 26.2E driver helpers")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _resolve_vscode() -> Path:
    candidates: list[Path] = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "Microsoft VS Code" / "Code.exe")
    if program_files:
        candidates.append(Path(program_files) / "Microsoft VS Code" / "Code.exe")
    if program_files_x86:
        candidates.append(Path(program_files_x86) / "Microsoft VS Code" / "Code.exe")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise RuntimeError("VS Code Code.exe was not found in standard install locations")


def _control_mapping(item: Any) -> dict[str, Any]:
    return {
        "role": item.role,
        "name": item.name,
        "automation_id": item.automation_id,
        "bounds": item.bounds.to_mapping() if item.bounds is not None else None,
        "visible": item.visible,
        "enabled": item.enabled,
        "focused": item.focused,
        "observation_fingerprint": item.observation_fingerprint,
    }


def _focus_evidence(state: DesktopState) -> dict[str, Any]:
    value = state.freshness_evidence.get("focus_evidence")
    return dict(value) if isinstance(value, dict) else {}


def _focused_controls(state: DesktopState) -> list[dict[str, Any]]:
    return [_control_mapping(item) for item in state.controls if item.focused is True][:8]


def _editor_candidates(state: DesktopState, unique_filename: str) -> list[dict[str, Any]]:
    filename = unique_filename.casefold()
    tokens = (filename, "editor", "text area", "monaco", "code editor")
    candidates: list[dict[str, Any]] = []
    for item in state.controls:
        name = item.name.casefold()
        role = item.role.casefold()
        if item.visible is False:
            continue
        if role not in EDITOR_ROLES and not any(token in name for token in tokens):
            continue
        candidates.append(_control_mapping(item))
    return candidates[:48]


def _named_controls(state: DesktopState) -> list[dict[str, Any]]:
    return [
        _control_mapping(item)
        for item in state.controls
        if item.visible is not False and bool(item.name.strip())
    ][:80]


def _sample(state: DesktopState, unique_filename: str, ordinal: int) -> dict[str, Any]:
    return {
        "sample": ordinal,
        "observed_at": state.observed_at,
        "control_count": len(state.controls),
        "focused_control_fingerprint": state.focused_control,
        "focus_evidence": _focus_evidence(state),
        "focused_controls": _focused_controls(state),
        "editor_candidates": _editor_candidates(state, unique_filename),
        "named_controls": _named_controls(state),
    }


def main() -> int:
    if os.name != "nt":
        raise RuntimeError("VS Code UIA diagnostic requires Windows")

    driver = _load_stage_driver()
    code_exe = _resolve_vscode()
    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    output_root = Path(os.environ["LOCALAPPDATA"]) / "ChatAgentPlatform" / "stage26" / "real-app-e2e"
    run_dir = output_root / f"vscode-uia-diagnostic-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "result.json"

    app_root = (Path(tempfile.gettempdir()) / f"{QUALIFICATION_PREFIX}{secrets.token_hex(8)}").resolve()
    workspace_root = app_root / "workspace"
    user_data_root = app_root / "user-data"
    extensions_root = app_root / "extensions"
    settings_dir = user_data_root / "User"
    unique_filename = f"chat-agent-stage26e-diag-{secrets.token_hex(6)}.txt"
    target_file = workspace_root / unique_filename

    result: dict[str, Any] = {
        "schema_version": 1,
        "kind": "stage26-2e-vscode-uia-read-only-diagnostic",
        "code_exe": str(code_exe),
        "app_root": str(app_root),
        "unique_filename": unique_filename,
        "window_title": None,
        "window_process_id": None,
        "window_handle": None,
        "process_generation": None,
        "samples": [],
        "keyboard_action_count": 0,
        "pointer_action_count": 0,
        "cleanup_match_count": 0,
        "cleanup_validated_match_count": 0,
        "cleanup_pass": False,
        "cli_returncode": None,
        "cli_exit_pass": False,
        "app_root_cleanup_pass": False,
        "resolver_stats": None,
        "error": None,
        "traceback": None,
    }

    resolver = WindowScopedUiaResolver()
    cli_process: subprocess.Popen[bytes] | None = None
    bound_hwnd: int | None = None
    bound_pid: int | None = None
    process_generation: str | None = None

    try:
        temp_root = Path(tempfile.gettempdir()).resolve()
        if app_root == temp_root or not app_root.is_relative_to(temp_root):
            raise RuntimeError("diagnostic app root escaped OS TEMP")
        if not app_root.name.startswith(QUALIFICATION_PREFIX):
            raise RuntimeError("diagnostic app root prefix mismatch")

        workspace_root.mkdir(parents=True, exist_ok=False)
        settings_dir.mkdir(parents=True, exist_ok=False)
        extensions_root.mkdir(parents=True, exist_ok=False)
        target_file.write_bytes(b"")
        settings = {
            "files.autoSave": "off",
            "workbench.startupEditor": "none",
            "window.restoreWindows": "none",
            "editor.accessibilitySupport": "on",
            "security.workspace.trust.enabled": False,
            "extensions.autoCheckUpdates": False,
            "extensions.autoUpdate": False,
            "update.mode": "none",
        }
        (settings_dir / "settings.json").write_text(
            json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        if driver._matching_vscode_windows(unique_filename):
            raise RuntimeError("diagnostic randomized window already exists")

        cli_process = subprocess.Popen(
            [
                str(code_exe),
                "--wait",
                "--new-window",
                "--disable-extensions",
                "--user-data-dir",
                str(user_data_root),
                "--extensions-dir",
                str(extensions_root),
                "--goto",
                f"{target_file}:1:1",
            ],
            cwd=str(workspace_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
        )

        window = driver._wait_unique_vscode_window(unique_filename, 90.0)
        bound_hwnd = int(window["hwnd"])
        bound_pid = int(window["pid"])
        window_title = str(window["title"])
        result["window_title"] = window_title
        result["window_process_id"] = bound_pid
        result["window_handle"] = bound_hwnd
        resolver.set_expected_process_id(bound_pid)

        for ordinal in range(1, SAMPLE_COUNT + 1):
            state = observe_bound_window(resolver, window_title)
            if state.window_handle != bound_hwnd or state.process_id != bound_pid:
                raise RuntimeError("diagnostic exact-window identity changed")
            if state.executable_name.casefold() != EXPECTED_EXECUTABLE:
                raise RuntimeError("diagnostic process is not Code.exe")
            process_generation = state.process_generation
            result["process_generation"] = process_generation
            result["samples"].append(_sample(state, unique_filename, ordinal))
            if ordinal != SAMPLE_COUNT:
                time.sleep(SAMPLE_INTERVAL_SECONDS)

        result["resolver_stats"] = vars(resolver.stats).copy()
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        result["resolver_stats"] = vars(resolver.stats).copy()
    finally:
        try:
            if bound_hwnd is not None and bound_pid is not None and process_generation is not None:
                matches, validated = driver._validated_cleanup_matches(
                    unique_filename,
                    expected_hwnd=bound_hwnd,
                    expected_pid=bound_pid,
                    expected_process_generation=process_generation,
                )
            else:
                matches, validated = driver._validated_cleanup_matches(unique_filename)
            result["cleanup_match_count"] = len(matches)
            result["cleanup_validated_match_count"] = len(validated)
            if not matches:
                result["cleanup_pass"] = True
            elif len(matches) == 1 and len(validated) == 1:
                driver._post_close(int(validated[0]["hwnd"]))
                driver._wait_until(
                    lambda: not driver._matching_vscode_windows(unique_filename),
                    timeout=15.0,
                    label="diagnostic isolated VS Code window close",
                )
                result["cleanup_pass"] = True
        except Exception as exc:
            if result["error"] is None:
                result["error"] = f"cleanup failed: {type(exc).__name__}: {exc}"

        if cli_process is not None:
            try:
                returncode = int(cli_process.wait(timeout=10.0))
                result["cli_returncode"] = returncode
                result["cli_exit_pass"] = returncode == 0
            except subprocess.TimeoutExpired:
                cli_process.terminate()
                try:
                    cli_process.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    cli_process.kill()
                    cli_process.wait(timeout=5.0)
                result["cli_returncode"] = cli_process.poll()
                result["cli_exit_pass"] = False

        try:
            if app_root.exists():
                if not app_root.name.startswith(QUALIFICATION_PREFIX):
                    raise RuntimeError("refusing diagnostic cleanup outside prefix")
                temp_root = Path(tempfile.gettempdir()).resolve()
                if app_root == temp_root or not app_root.is_relative_to(temp_root):
                    raise RuntimeError("refusing diagnostic cleanup outside TEMP")
                import shutil

                shutil.rmtree(app_root)
            result["app_root_cleanup_pass"] = not app_root.exists()
        except Exception as exc:
            result["app_root_cleanup_pass"] = False
            if result["error"] is None:
                result["error"] = f"app-root cleanup failed: {type(exc).__name__}: {exc}"

        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("===== STAGE 26.2E VS CODE UIA READ-ONLY DIAGNOSTIC =====")
    print(f"RESULT_PATH={result_path}")
    print(f"WINDOW_TITLE={result['window_title']}")
    print(f"WINDOW_PROCESS_ID={result['window_process_id']}")
    print(f"WINDOW_HANDLE={result['window_handle']}")
    print(f"PROCESS_GENERATION={result['process_generation']}")
    for sample in result["samples"]:
        print(f"SAMPLE_{sample['sample']}_CONTROL_COUNT={sample['control_count']}")
        print(f"SAMPLE_{sample['sample']}_FOCUS_EVIDENCE={sample['focus_evidence']}")
        print(f"SAMPLE_{sample['sample']}_FOCUSED_CONTROLS={sample['focused_controls']}")
        print(f"SAMPLE_{sample['sample']}_EDITOR_CANDIDATES={sample['editor_candidates']}")
        print(f"SAMPLE_{sample['sample']}_NAMED_CONTROLS={sample['named_controls']}")
    print(f"KEYBOARD_ACTION_COUNT={result['keyboard_action_count']}")
    print(f"POINTER_ACTION_COUNT={result['pointer_action_count']}")
    print(f"CLEANUP_MATCH_COUNT={result['cleanup_match_count']}")
    print(f"CLEANUP_VALIDATED_MATCH_COUNT={result['cleanup_validated_match_count']}")
    print(f"CLEANUP_PASS={result['cleanup_pass']}")
    print(f"CLI_RETURNCODE={result['cli_returncode']}")
    print(f"CLI_EXIT_PASS={result['cli_exit_pass']}")
    print(f"APP_ROOT_CLEANUP_PASS={result['app_root_cleanup_pass']}")
    print(f"RESOLVER_STATS={result['resolver_stats']}")
    print(f"ERROR={result['error']}")
    diagnostic_pass = bool(
        result["samples"]
        and result["keyboard_action_count"] == 0
        and result["pointer_action_count"] == 0
        and result["cleanup_pass"]
        and result["cli_exit_pass"]
        and result["app_root_cleanup_pass"]
        and result["error"] is None
    )
    print(f"DIAGNOSTIC_PASS={diagnostic_pass}")
    return 0 if diagnostic_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
