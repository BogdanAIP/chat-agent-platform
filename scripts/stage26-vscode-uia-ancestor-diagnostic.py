from __future__ import annotations

import importlib.util
import json
import os
import secrets
import shutil
import subprocess
import tempfile
import time
import traceback
from pathlib import Path
from typing import Any

from runtime.windows.observation import (
    _normalize_text,
    _query_process_identity,
    _rect_from_value,
    _role_from_control_type,
    observe_bound_window,
)
from runtime.windows.window_scoped_uia import (
    MAX_WINDOW_CONTROL_SCAN,
    TREE_SCOPE_DESCENDANTS,
    WindowScopedUiaResolver,
    _upstream,
)


QUALIFICATION_PREFIX = "chat-agent-stage26e-vscode-ancestor-"
EXPECTED_EXECUTABLE = "code.exe"
MAX_READINESS_ATTEMPTS = 24
READINESS_INTERVAL_SECONDS = 0.75
CHAIN_STABLE_SAMPLES = 3
MAX_ANCESTOR_DEPTH = 12
MAX_CHILDREN_PER_ANCESTOR = 12
TRANSIENT_COM_HRESULT = -2147220991


def _load_script(filename: str, module_name: str) -> Any:
    path = Path(__file__).with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load helper script: {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _is_transition_com_error(exc: BaseException) -> bool:
    return type(exc).__name__ == "COMError" and bool(
        getattr(exc, "args", ()) and exc.args[0] == TRANSIENT_COM_HRESULT
    )


def _state_focused_proxy(state: Any, unique_filename: str) -> Any | None:
    if not state.focused_control:
        return None
    matches = [
        item
        for item in state.controls
        if item.observation_fingerprint == state.focused_control
    ]
    if len(matches) != 1:
        return None
    item = matches[0]
    if item.role.casefold() != "textbox":
        return None
    if item.name.casefold() != unique_filename.casefold():
        return None
    if item.enabled is not True or item.focused is not True:
        return None
    return item


def _element_membership(client: Any, root_element: Any, elements: Any, element: Any) -> tuple[str, int | None]:
    if bool(client.CompareElements(root_element, element)):
        return "bound_window", None
    matched_index: int | None = None
    for index in range(int(elements.Length)):
        if not bool(client.CompareElements(elements.GetElement(index), element)):
            continue
        if matched_index is not None:
            raise RuntimeError("UIA element matched multiple bound-window descendants")
        matched_index = index
    if matched_index is None:
        return "outside_bound_window", None
    return "descendant", matched_index


def _raw_element_mapping(auto: Any, upstream: Any, element: Any) -> dict[str, Any]:
    control = auto.Control.CreateControlFromElement(element)
    if control is None:
        return {
            "materialized": False,
            "role": None,
            "name": None,
            "automation_id": None,
            "bounds": None,
            "visible": None,
            "enabled": None,
            "focused": None,
        }

    def value(key: str, default: object = None) -> object:
        return upstream._control_value(control, key, default)

    control_type = str(value("ControlTypeName", "") or "")
    bounds = _rect_from_value(value("BoundingRectangle", None))
    offscreen = value("IsOffscreen", None)
    visible = None if offscreen is None else not bool(offscreen)
    if bounds is not None and (bounds.width == 0 or bounds.height == 0):
        visible = False
    return {
        "materialized": True,
        "role": _role_from_control_type(control_type),
        "name": _normalize_text(value("Name", "")),
        "automation_id": str(value("AutomationId", "") or ""),
        "bounds": bounds.to_mapping() if bounds is not None else None,
        "visible": visible,
        "enabled": None if value("IsEnabled", None) is None else bool(value("IsEnabled", None)),
        "focused": None
        if value("HasKeyboardFocus", None) is None
        else bool(value("HasKeyboardFocus", None)),
    }


def _child_summaries(
    *,
    client: Any,
    walker: Any,
    root_element: Any,
    elements: Any,
    auto: Any,
    upstream: Any,
    parent: Any,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    child = walker.GetFirstChildElement(parent)
    while child is not None and len(rows) < MAX_CHILDREN_PER_ANCESTOR:
        membership, source_index = _element_membership(client, root_element, elements, child)
        if membership == "outside_bound_window":
            raise RuntimeError("ancestor child escaped exact bound-window subtree")
        row = _raw_element_mapping(auto, upstream, child)
        row["membership"] = membership
        row["source_index"] = source_index
        rows.append(row)
        child = walker.GetNextSiblingElement(child)
    return rows


def _focused_ancestor_chain(
    resolver: WindowScopedUiaResolver,
    window_title: str,
    *,
    expected_hwnd: int,
    expected_pid: int,
) -> list[dict[str, Any]]:
    if os.name != "nt":
        raise RuntimeError("focused ancestor diagnostic requires Windows")

    try:
        import uiautomation as auto
        from uiautomation import uiautomation as auto_impl
    except Exception as exc:
        raise RuntimeError("UI Automation is unavailable") from exc

    import comtypes.client

    comtypes.client.gen_dir = None
    upstream = _upstream()

    with auto.UIAutomationInitializerInThread():
        windows = resolver._find_target_windows(auto, window_title)
        if len(windows) != 1:
            raise RuntimeError(f"expected one exact bound VS Code window, found {len(windows)}")
        window = windows[0]
        hwnd = int(upstream._control_value(window, "NativeWindowHandle", 0) or 0)
        pid = int(upstream._control_value(window, "ProcessId", 0) or 0)
        if hwnd != expected_hwnd or pid != expected_pid:
            raise RuntimeError("ancestor diagnostic exact PID/HWND binding changed")

        client = auto_impl._AutomationClient.instance().IUIAutomation
        root_element = window.Element
        elements = root_element.FindAll(
            TREE_SCOPE_DESCENDANTS,
            client.CreateTrueCondition(),
        )
        if int(elements.Length) > MAX_WINDOW_CONTROL_SCAN:
            raise RuntimeError("ancestor diagnostic exceeded bounded UIA control ceiling")

        focused_element = client.GetFocusedElement()
        membership, focused_index = _element_membership(
            client,
            root_element,
            elements,
            focused_element,
        )
        if membership != "descendant" or focused_index is None:
            raise RuntimeError("global focused element is not one exact bound-window descendant")

        walker = client.ControlViewWalker
        rows: list[dict[str, Any]] = []
        current = focused_element
        reached_bound_window = False

        for depth in range(MAX_ANCESTOR_DEPTH + 1):
            membership, source_index = _element_membership(
                client,
                root_element,
                elements,
                current,
            )
            if membership == "outside_bound_window":
                raise RuntimeError("focused ancestor escaped exact bound-window subtree")

            row = _raw_element_mapping(auto, upstream, current)
            row.update(
                {
                    "depth": depth,
                    "membership": membership,
                    "source_index": source_index,
                    "children": _child_summaries(
                        client=client,
                        walker=walker,
                        root_element=root_element,
                        elements=elements,
                        auto=auto,
                        upstream=upstream,
                        parent=current,
                    ),
                }
            )
            rows.append(row)

            if membership == "bound_window":
                reached_bound_window = True
                break
            current = walker.GetParentElement(current)
            if current is None:
                break

        if not reached_bound_window:
            raise RuntimeError("focused ancestor chain did not terminate at the exact bound window")
        return rows


def _chain_signature(chain: list[dict[str, Any]]) -> str:
    compact = [
        {
            "depth": row["depth"],
            "membership": row["membership"],
            "source_index": row["source_index"],
            "role": row["role"],
            "name": row["name"],
            "automation_id": row["automation_id"],
            "bounds": row["bounds"],
            "visible": row["visible"],
            "enabled": row["enabled"],
        }
        for row in chain
    ]
    return json.dumps(compact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> int:
    if os.name != "nt":
        raise RuntimeError("VS Code UIA ancestor diagnostic requires Windows")

    driver = _load_script("stage26-vscode-real-app-e2e.py", "stage26_vscode_real_app_e2e")
    baseline_diag = _load_script("stage26-vscode-uia-diagnostic.py", "stage26_vscode_uia_diagnostic")
    code_exe = baseline_diag._resolve_vscode()

    timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    output_root = Path(os.environ["LOCALAPPDATA"]) / "ChatAgentPlatform" / "stage26" / "real-app-e2e"
    run_dir = output_root / f"vscode-uia-ancestor-{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    result_path = run_dir / "result.json"

    app_root = (Path(tempfile.gettempdir()) / f"{QUALIFICATION_PREFIX}{secrets.token_hex(8)}").resolve()
    workspace_root = app_root / "workspace"
    user_data_root = app_root / "user-data"
    extensions_root = app_root / "extensions"
    settings_dir = user_data_root / "User"
    unique_filename = f"chat-agent-stage26e-ancestor-{secrets.token_hex(6)}.txt"
    target_file = workspace_root / unique_filename

    result: dict[str, Any] = {
        "schema_version": 1,
        "kind": "stage26-2e-vscode-focused-monaco-ancestor-diagnostic",
        "code_exe": str(code_exe),
        "app_root": str(app_root),
        "unique_filename": unique_filename,
        "window_title": None,
        "window_process_id": None,
        "window_handle": None,
        "process_generation": None,
        "attempts": [],
        "stable_chain_samples": [],
        "stable_chain_count": 0,
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
            "chat.disableAIFeatures": True,
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

        _session, _app_identity, executable, process_generation = _query_process_identity(bound_pid)
        if executable.casefold() != EXPECTED_EXECUTABLE:
            raise RuntimeError("diagnostic process is not Code.exe")
        result["process_generation"] = process_generation

        previous_signature: str | None = None
        stable_count = 0

        for attempt in range(1, MAX_READINESS_ATTEMPTS + 1):
            try:
                state = observe_bound_window(resolver, window_title)
            except Exception as exc:
                if not _is_transition_com_error(exc):
                    raise
                stable_count = 0
                previous_signature = None
                result["attempts"].append(
                    {
                        "attempt": attempt,
                        "status": "transition_com_error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                time.sleep(READINESS_INTERVAL_SECONDS)
                continue

            if (
                state.window_handle != bound_hwnd
                or state.process_id != bound_pid
                or state.executable_name.casefold() != EXPECTED_EXECUTABLE
                or state.process_generation != process_generation
            ):
                raise RuntimeError("diagnostic exact window/process identity changed")

            proxy = _state_focused_proxy(state, unique_filename)
            if proxy is None:
                stable_count = 0
                previous_signature = None
                result["attempts"].append(
                    {
                        "attempt": attempt,
                        "status": "focused_proxy_not_ready",
                        "control_count": len(state.controls),
                        "focused_control": state.focused_control,
                    }
                )
                time.sleep(READINESS_INTERVAL_SECONDS)
                continue

            chain = _focused_ancestor_chain(
                resolver,
                window_title,
                expected_hwnd=bound_hwnd,
                expected_pid=bound_pid,
            )
            if chain[0]["role"] != "textbox" or chain[0]["name"].casefold() != unique_filename.casefold():
                raise RuntimeError("raw focused element no longer matches the Monaco textbox proxy")

            signature = _chain_signature(chain)
            if signature == previous_signature:
                stable_count += 1
            else:
                stable_count = 1
                previous_signature = signature

            sample = {
                "attempt": attempt,
                "status": "ancestor_chain",
                "control_count": len(state.controls),
                "focused_proxy": proxy.to_mapping(),
                "stable_count": stable_count,
                "chain": chain,
            }
            result["attempts"].append(sample)
            result["stable_chain_samples"].append(sample)
            result["stable_chain_count"] = stable_count

            if stable_count >= CHAIN_STABLE_SAMPLES:
                break
            time.sleep(READINESS_INTERVAL_SECONDS)
        else:
            raise TimeoutError("timed out waiting for three stable focused Monaco ancestor chains")

        if result["stable_chain_count"] < CHAIN_STABLE_SAMPLES:
            raise RuntimeError("focused Monaco ancestor chain did not stabilize")
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
                    label="ancestor diagnostic isolated VS Code window close",
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
                temp_root = Path(tempfile.gettempdir()).resolve()
                if not app_root.name.startswith(QUALIFICATION_PREFIX):
                    raise RuntimeError("refusing ancestor diagnostic cleanup outside prefix")
                if app_root == temp_root or not app_root.is_relative_to(temp_root):
                    raise RuntimeError("refusing ancestor diagnostic cleanup outside TEMP")
                shutil.rmtree(app_root)
            result["app_root_cleanup_pass"] = not app_root.exists()
        except Exception as exc:
            result["app_root_cleanup_pass"] = False
            if result["error"] is None:
                result["error"] = f"app-root cleanup failed: {type(exc).__name__}: {exc}"

        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print("===== STAGE 26.2E VS CODE FOCUSED MONACO ANCESTOR DIAGNOSTIC =====")
    print(f"RESULT_PATH={result_path}")
    print(f"WINDOW_TITLE={result['window_title']}")
    print(f"WINDOW_PROCESS_ID={result['window_process_id']}")
    print(f"WINDOW_HANDLE={result['window_handle']}")
    print(f"PROCESS_GENERATION={result['process_generation']}")
    for item in result["attempts"]:
        attempt = item["attempt"]
        print(f"ATTEMPT_{attempt}_STATUS={item['status']}")
        if item["status"] == "transition_com_error":
            print(f"ATTEMPT_{attempt}_ERROR={item['error']}")
        elif item["status"] == "focused_proxy_not_ready":
            print(f"ATTEMPT_{attempt}_CONTROL_COUNT={item['control_count']}")
            print(f"ATTEMPT_{attempt}_FOCUSED_CONTROL={item['focused_control']}")
        else:
            print(f"ATTEMPT_{attempt}_CONTROL_COUNT={item['control_count']}")
            print(f"ATTEMPT_{attempt}_STABLE_COUNT={item['stable_count']}")
            print(f"ATTEMPT_{attempt}_FOCUSED_PROXY={item['focused_proxy']}")
            print(f"ATTEMPT_{attempt}_ANCESTOR_CHAIN={item['chain']}")
    print(f"STABLE_CHAIN_COUNT={result['stable_chain_count']}")
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
        result["stable_chain_count"] >= CHAIN_STABLE_SAMPLES
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
