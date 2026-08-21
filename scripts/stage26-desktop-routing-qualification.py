from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import secrets
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Callable

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from openadapt_flow.backends.windows_backend import WindowsBackend
from openadapt_flow.backends.win_agent.server import AgentConfig, create_server

from runtime.local_vision_adapter.native_bbox import NativeBBoxLoopbackClient
from runtime.windows.actuation import bounded_input
from runtime.windows.grounder import ground_desktop_target
from runtime.windows.native_point_guard import (
    NativePointGuardError,
    require_foreground_hit_target,
)
from runtime.windows.observation import ControlObservation, Rect, observe_bound_window
from runtime.windows.routing import (
    DesktopClickRequest,
    ObservedDesktopFrame,
    VISION_FALLBACK_DISABLED,
    VISION_FALLBACK_ZERO_EXACT,
    execute_guarded_coordinate_click_with_backend,
    execute_structural_click_with_backend,
    route_desktop_click,
)
from runtime.windows.window_scoped_uia import WindowScopedUiaResolver


FIXTURE_WINDOW_NAME = "Stage 26 capture qualification fixture"
TARGET_VISIBLE_TEXT = "1. Benchmark start"
TARGET_UIA_NAME = "Stage 26 start button"
VISION_PORT = 3068


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _wait_state(
    path: Path,
    predicate: Callable[[dict[str, Any]], bool],
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                last = _read_json(path)
            except Exception:
                last = {}
            if predicate(last):
                return last
        time.sleep(0.05)
    raise TimeoutError(f"timed out waiting for fixture state: {last}")


def _capture_exact_window(bounds: Rect) -> bytes:
    if bounds.width <= 0 or bounds.height <= 0:
        raise RuntimeError("window bounds are empty")
    import mss
    import mss.tools

    monitor = {
        "left": bounds.left,
        "top": bounds.top,
        "width": bounds.width,
        "height": bounds.height,
    }
    with mss.MSS() as capture:
        shot = capture.grab(monitor)
        return mss.tools.to_png(shot.rgb, shot.size)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _control_center(control: ControlObservation) -> tuple[int, int]:
    if control.bounds is None:
        raise RuntimeError("target control has no bounds")
    return (
        int(round((control.bounds.left + control.bounds.right) / 2.0)),
        int(round((control.bounds.top + control.bounds.bottom) / 2.0)),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-state", required=True)
    parser.add_argument("--recorder-ready", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    fixture_state_path = Path(args.fixture_state).resolve()
    ready_path = Path(args.recorder_ready).resolve()
    result_path = run_dir / "desktop-routing-result.json"
    windows_dir = REPO_ROOT / "runtime" / "windows"
    router_path = windows_dir / "routing.py"
    guard_path = windows_dir / "native_point_guard.py"
    observer_path = windows_dir / "observation.py"
    grounder_path = windows_dir / "grounder.py"
    actuation_path = windows_dir / "actuation.py"
    driver_path = Path(__file__).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "schema_version": 3,
        "qualification_kind": "windows-structure-first-vision-routing",
        "router_source_sha256": _sha256(router_path),
        "native_point_guard_source_sha256": _sha256(guard_path),
        "observer_source_sha256": _sha256(observer_path),
        "grounder_source_sha256": _sha256(grounder_path),
        "actuation_source_sha256": _sha256(actuation_path),
        "driver_source_sha256": _sha256(driver_path),
        "fixture_process_id": None,
        "agent_loopback_pass": False,
        "agent_auth_required_pass": False,
        "legacy_capability_absent_pass": False,
        "native_point_guard_preflight_pass": False,
        "native_point_guard_wrong_window_refusal_pass": False,
        "native_point_guard_delivery_pass": False,
        "vision_disabled_probe": None,
        "role_conflict_probe": None,
        "positive_route": None,
        "positive_route_status": None,
        "positive_route_reason": None,
        "positive_consistency_iou": None,
        "vision_disabled_abstain_pass": False,
        "role_conflict_abstain_pass": False,
        "negative_zero_action_pass": False,
        "positive_visual_route_pass": False,
        "fresh_reobservation_pass": False,
        "guarded_click_receipt_pass": False,
        "fixture_start_postcondition_pass": False,
        "fixture_no_extra_mutation_pass": False,
        "single_action_pass": False,
        "structural_executor_calls": 0,
        "coordinate_executor_calls": 0,
        "grounder_calls": 0,
        "screenshot_paths": [],
        "screenshot_sha256": [],
        "resolver_stats": None,
        "pass": False,
        "error": None,
        "traceback": None,
    }

    resolver = WindowScopedUiaResolver()
    server = None
    server_thread: threading.Thread | None = None
    backend: WindowsBackend | None = None

    try:
        ready_path.write_text("READY\n", encoding="ascii")
        fixture = _wait_state(
            fixture_state_path,
            lambda item: item.get("recorder_ready") is True and item.get("cycle_ready") is True,
        )
        fixture_pid = fixture.get("fixture_pid")
        if isinstance(fixture_pid, bool) or not isinstance(fixture_pid, int) or fixture_pid <= 0:
            raise RuntimeError("fixture did not publish a valid process id")
        result["fixture_process_id"] = fixture_pid
        resolver.set_expected_process_id(fixture_pid)

        token = secrets.token_urlsafe(32)
        config = AgentConfig(
            host="127.0.0.1",
            port=0,
            token=token,
            allow_legacy_exec=False,
        )
        server = create_server(config, input_fn=bounded_input, uia_fn=resolver.perform)
        host, port = server.server_address[:2]
        result["agent_loopback_pass"] = str(host) == "127.0.0.1" and int(port) > 0
        if not result["agent_loopback_pass"]:
            raise RuntimeError("qualification agent was not loopback-bound")

        server_thread = threading.Thread(
            target=server.serve_forever,
            name="stage26-2d-routing-agent",
            daemon=True,
        )
        server_thread.start()
        base_url = f"http://127.0.0.1:{int(port)}"
        health = requests.get(f"{base_url}/health", timeout=10.0)
        health.raise_for_status()
        health_data = health.json()
        result["agent_auth_required_pass"] = health_data.get("auth_required") is True
        result["legacy_capability_absent_pass"] = "legacy_exec" not in (
            health_data.get("capabilities") or []
        )
        if not result["agent_auth_required_pass"] or not result["legacy_capability_absent_pass"]:
            raise RuntimeError("qualification agent security contract drifted")

        backend = WindowsBackend(
            server_url=base_url,
            auth_token=token,
            require_tls=False,
            allow_legacy_exec=False,
        )

        preflight_state = observe_bound_window(resolver, FIXTURE_WINDOW_NAME)
        start_controls = tuple(
            control
            for control in preflight_state.controls
            if control.name == TARGET_UIA_NAME and control.role == "button"
        )
        if len(start_controls) != 1:
            raise RuntimeError("preflight could not identify exactly one start-button UIA control")
        preflight_x, preflight_y = _control_center(start_controls[0])
        require_foreground_hit_target(preflight_state, preflight_x, preflight_y)
        result["native_point_guard_preflight_pass"] = True
        try:
            require_foreground_hit_target(
                replace(preflight_state, window_handle=preflight_state.window_handle + 1),
                preflight_x,
                preflight_y,
            )
        except NativePointGuardError:
            result["native_point_guard_wrong_window_refusal_pass"] = True
        if not result["native_point_guard_wrong_window_refusal_pass"]:
            raise RuntimeError("native point guard did not reject wrong-window authority")

        screenshot_index = 0

        def observe(need_screenshot: bool) -> ObservedDesktopFrame:
            nonlocal screenshot_index
            state = observe_bound_window(resolver, FIXTURE_WINDOW_NAME)
            if not need_screenshot:
                return ObservedDesktopFrame(state=state)
            png = _capture_exact_window(state.window_bounds)
            screenshot_index += 1
            path = run_dir / f"exact-window-{screenshot_index:02d}.png"
            path.write_bytes(png)
            result["screenshot_paths"].append(str(path))
            result["screenshot_sha256"].append(hashlib.sha256(png).hexdigest())
            bound = observe_bound_window(
                resolver,
                FIXTURE_WINDOW_NAME,
                screenshot_png=png,
                screenshot_source="mss_exact_bound_window",
            )
            if bound.window_bounds != state.window_bounds:
                raise RuntimeError("window bounds changed while capturing exact-window screenshot")
            return ObservedDesktopFrame(state=bound, screenshot_png=png)

        client = NativeBBoxLoopbackClient(port=VISION_PORT, timeout_seconds=120.0)

        def ground(frame, request, uia_evidence):
            result["grounder_calls"] += 1
            if frame.screenshot_png is None:
                raise RuntimeError("visual grounder was called without exact-window screenshot")
            return ground_desktop_target(
                client=client,
                window_png=frame.screenshot_png,
                target_text=request.target_text,
                desktop_state=frame.state,
                uia_evidence=uia_evidence,
            )

        def execute_structural(request, control, state):
            result["structural_executor_calls"] += 1
            assert backend is not None
            return execute_structural_click_with_backend(backend, request, control, state)

        def execute_coordinate(request, proposal, state):
            result["coordinate_executor_calls"] += 1
            assert backend is not None
            receipt = execute_guarded_coordinate_click_with_backend(
                backend,
                request,
                proposal,
                state,
            )
            result["native_point_guard_delivery_pass"] = True
            return receipt

        disabled_result = route_desktop_click(
            request=DesktopClickRequest(
                window_name=FIXTURE_WINDOW_NAME,
                target_text=TARGET_VISIBLE_TEXT,
                role="button",
                vision_fallback=VISION_FALLBACK_DISABLED,
            ),
            observe=observe,
            ground=ground,
            execute_structural=execute_structural,
            execute_coordinate=execute_coordinate,
        )
        result["vision_disabled_probe"] = disabled_result.to_mapping()
        result["vision_disabled_abstain_pass"] = bool(
            disabled_result.status == "abstain"
            and disabled_result.reason == "vision-fallback-not-promoted"
        )

        role_conflict_result = route_desktop_click(
            request=DesktopClickRequest(
                window_name=FIXTURE_WINDOW_NAME,
                target_text=TARGET_UIA_NAME,
                role="link",
                vision_fallback=VISION_FALLBACK_ZERO_EXACT,
            ),
            observe=observe,
            ground=ground,
            execute_structural=execute_structural,
            execute_coordinate=execute_coordinate,
        )
        result["role_conflict_probe"] = role_conflict_result.to_mapping()
        result["role_conflict_abstain_pass"] = bool(
            role_conflict_result.status == "abstain"
            and role_conflict_result.reason == "structural-role-conflict"
        )

        before_positive = _wait_state(
            fixture_state_path,
            lambda item: item.get("cycle_ready") is True,
        )
        result["negative_zero_action_pass"] = bool(
            result["vision_disabled_abstain_pass"]
            and result["role_conflict_abstain_pass"]
            and result["grounder_calls"] == 0
            and result["structural_executor_calls"] == 0
            and result["coordinate_executor_calls"] == 0
            and before_positive.get("start_clicked") is False
            and before_positive.get("text_ok") is False
            and before_positive.get("enter_pressed") is False
            and before_positive.get("scroll_seen") is False
            and before_positive.get("finish_clicked") is False
        )

        positive = route_desktop_click(
            request=DesktopClickRequest(
                window_name=FIXTURE_WINDOW_NAME,
                target_text=TARGET_VISIBLE_TEXT,
                role="button",
                vision_fallback=VISION_FALLBACK_ZERO_EXACT,
            ),
            observe=observe,
            ground=ground,
            execute_structural=execute_structural,
            execute_coordinate=execute_coordinate,
        )
        result["positive_route"] = positive.to_mapping()
        result["positive_route_status"] = positive.status
        result["positive_route_reason"] = positive.reason
        proposal = positive.proposal
        result["positive_consistency_iou"] = (
            proposal.consistency_iou if proposal is not None else None
        )
        result["positive_visual_route_pass"] = bool(
            positive.status == "delivered"
            and positive.route == "vision"
            and positive.reason == "vision-zero-exact-delivered"
            and proposal is not None
        )
        if not result["positive_visual_route_pass"]:
            raise RuntimeError(
                "positive visual route did not deliver: "
                f"status={positive.status} reason={positive.reason} "
                f"consistency_iou={result['positive_consistency_iou']}"
            )

        result["fresh_reobservation_pass"] = bool(
            positive.authorized_frame_digest == proposal.frame_digest
            and len(result["screenshot_sha256"]) >= 2
            and result["screenshot_sha256"][-1] == proposal.screenshot_digest
            and result["screenshot_sha256"][-2] == proposal.screenshot_digest
        )
        receipt = positive.receipt or {}
        result["guarded_click_receipt_pass"] = bool(
            receipt.get("status") == "delivered"
            and receipt.get("operation") == "physical_click"
            and receipt.get("outcome_verified") is False
        )

        after_positive = _wait_state(
            fixture_state_path,
            lambda item: item.get("start_clicked") is True,
        )
        result["fixture_start_postcondition_pass"] = after_positive.get("start_clicked") is True
        result["fixture_no_extra_mutation_pass"] = bool(
            after_positive.get("text_ok") is False
            and after_positive.get("enter_pressed") is False
            and after_positive.get("scroll_seen") is False
            and after_positive.get("finish_clicked") is False
        )
        result["single_action_pass"] = bool(
            result["structural_executor_calls"] == 0
            and result["coordinate_executor_calls"] == 1
            and result["grounder_calls"] == 1
        )
        result["resolver_stats"] = vars(resolver.stats).copy()

        result["pass"] = bool(
            result["agent_loopback_pass"]
            and result["agent_auth_required_pass"]
            and result["legacy_capability_absent_pass"]
            and result["native_point_guard_preflight_pass"]
            and result["native_point_guard_wrong_window_refusal_pass"]
            and result["native_point_guard_delivery_pass"]
            and result["negative_zero_action_pass"]
            and result["positive_visual_route_pass"]
            and result["fresh_reobservation_pass"]
            and result["guarded_click_receipt_pass"]
            and result["fixture_start_postcondition_pass"]
            and result["fixture_no_extra_mutation_pass"]
            and result["single_action_pass"]
            and resolver.stats.desktop_fallback_calls == 0
            and resolver.stats.window_binding_failures == 0
            and resolver.stats.window_binding_ambiguities == 0
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
        result["resolver_stats"] = vars(resolver.stats).copy()
    finally:
        if server is not None:
            try:
                server.shutdown()
            except Exception:
                pass
            try:
                server.server_close()
            except Exception:
                pass
        if server_thread is not None:
            server_thread.join(timeout=5.0)

    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("===== STAGE 26.2D WINDOWS VISION ROUTING =====")
    print(f"RESULT_PATH={result_path}")
    for key in (
        "router_source_sha256",
        "native_point_guard_source_sha256",
        "observer_source_sha256",
        "grounder_source_sha256",
        "actuation_source_sha256",
        "driver_source_sha256",
        "agent_loopback_pass",
        "agent_auth_required_pass",
        "legacy_capability_absent_pass",
        "native_point_guard_preflight_pass",
        "native_point_guard_wrong_window_refusal_pass",
        "native_point_guard_delivery_pass",
        "vision_disabled_abstain_pass",
        "role_conflict_abstain_pass",
        "negative_zero_action_pass",
        "positive_route_status",
        "positive_route_reason",
        "positive_consistency_iou",
        "positive_visual_route_pass",
        "fresh_reobservation_pass",
        "guarded_click_receipt_pass",
        "fixture_start_postcondition_pass",
        "fixture_no_extra_mutation_pass",
        "single_action_pass",
        "structural_executor_calls",
        "coordinate_executor_calls",
        "grounder_calls",
    ):
        print(f"{key.upper()}={result[key]}")
    print(f"SCREENSHOT_SHA256_JSON={json.dumps(result['screenshot_sha256'], separators=(',', ':'))}")
    if result.get("resolver_stats") is not None:
        for key in sorted(result["resolver_stats"]):
            print(f"{key.upper()}={result['resolver_stats'][key]}")
    print(f"ERROR={result['error']}")
    print(f"PASS={result['pass']}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
