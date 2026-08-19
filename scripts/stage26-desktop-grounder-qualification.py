from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.local_vision_adapter.native_bbox import NativeBBoxLoopbackClient
from runtime.windows.grounder import DesktopGrounderError, locate_desktop_target
from runtime.windows.observation import DesktopState, Rect, observe_bound_window
from runtime.windows.window_scoped_uia import WindowScopedUiaResolver


FIXTURE_WINDOW_NAME = "Stage 26 capture qualification fixture"
TARGET_UIA_NAME = "Stage 26 start button"
TARGET_VISIBLE_TEXT = "1. Benchmark start"
ABSENT_TARGET_TEXT = "Stage 26 definitely absent target"
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


def _find_target_control(state: DesktopState):
    matches = [
        control
        for control in state.controls
        if control.name == TARGET_UIA_NAME and control.visible is not False
    ]
    if len(matches) != 1:
        raise RuntimeError(f"expected one visible target control, found {len(matches)}")
    target = matches[0]
    if target.bounds is None:
        raise RuntimeError("target control has no bounds")
    return target


def _point_inside(bounds: Rect, x: float, y: float) -> bool:
    return bounds.left <= x <= bounds.right and bounds.top <= y <= bounds.bottom


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--fixture-state", required=True)
    parser.add_argument("--recorder-ready", required=True)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    fixture_state_path = Path(args.fixture_state).resolve()
    ready_path = Path(args.recorder_ready).resolve()
    result_path = run_dir / "desktop-grounder-result.json"
    observer_path = REPO_ROOT / "runtime" / "windows" / "observation.py"
    grounder_path = REPO_ROOT / "runtime" / "windows" / "grounder.py"
    driver_path = Path(__file__).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "schema_version": 1,
        "qualification_kind": "proposal-only-native-desktop-grounder",
        "production_observer_path": str(observer_path),
        "production_grounder_path": str(grounder_path),
        "observer_source_sha256": _sha256(observer_path),
        "grounder_source_sha256": _sha256(grounder_path),
        "driver_source_sha256": _sha256(driver_path),
        "fixture_process_id": None,
        "target_uia_name": TARGET_UIA_NAME,
        "target_visible_text": TARGET_VISIBLE_TEXT,
        "desktop_state": None,
        "proposal": None,
        "same_frame_binding_pass": False,
        "coordinate_contract_pass": False,
        "target_point_inside_uia_pass": False,
        "target_evidence_binding_pass": False,
        "absent_target_abstain_pass": False,
        "stale_frame_rejection_pass": False,
        "proposal_only_contract_pass": False,
        "resolver_stats": None,
        "pass": False,
        "error": None,
        "traceback": None,
    }

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

        resolver = WindowScopedUiaResolver()
        resolver.set_expected_process_id(fixture_pid)

        initial = observe_bound_window(resolver, FIXTURE_WINDOW_NAME)
        screenshot = _capture_exact_window(initial.window_bounds)
        state = observe_bound_window(
            resolver,
            FIXTURE_WINDOW_NAME,
            screenshot_png=screenshot,
            screenshot_source="mss_exact_bound_window",
        )
        target = _find_target_control(state)

        client = NativeBBoxLoopbackClient(port=VISION_PORT, timeout_seconds=120.0)
        proposal = locate_desktop_target(
            client=client,
            window_png=screenshot,
            target_text=TARGET_VISIBLE_TEXT,
            desktop_state=state,
            uia_evidence=[target],
        )
        if proposal is None:
            raise RuntimeError("grounder abstained on the expected visible target")

        result["desktop_state"] = {
            "process_id": state.process_id,
            "window_handle": state.window_handle,
            "window_instance": state.window_instance,
            "window_bounds": state.window_bounds.to_mapping(),
            "frame_digest": state.frame_digest,
            "screenshot_digest": state.screenshot_digest,
            "control_count": len(state.controls),
        }
        result["proposal"] = proposal.to_mapping()
        result["resolver_stats"] = vars(resolver.stats).copy()

        result["same_frame_binding_pass"] = bool(
            proposal.frame_digest == state.frame_digest
            and proposal.screenshot_digest == state.screenshot_digest
            and proposal.window_instance == state.window_instance
            and proposal.session_id == state.session_id
            and proposal.application_identity == state.application_identity
            and proposal.process_id == state.process_id
            and proposal.process_generation == state.process_generation
            and proposal.window_handle == state.window_handle
        )
        result["coordinate_contract_pass"] = bool(
            proposal.image_coordinate_space == "window_physical_px"
            and proposal.coordinate_space == "screen_physical_px"
            and abs(
                proposal.screen_point.x
                - (proposal.window_point.x + state.window_bounds.left)
            ) < 1e-6
            and abs(
                proposal.screen_point.y
                - (proposal.window_point.y + state.window_bounds.top)
            ) < 1e-6
        )
        assert target.bounds is not None
        result["target_point_inside_uia_pass"] = _point_inside(
            target.bounds,
            proposal.screen_point.x,
            proposal.screen_point.y,
        )
        result["target_evidence_binding_pass"] = bool(proposal.uia_evidence_digest)
        result["proposal_only_contract_pass"] = bool(
            proposal.confidence is None
            and proposal.confidence_basis == "uncalibrated-model-proposal"
        )

        absent = locate_desktop_target(
            client=client,
            window_png=screenshot,
            target_text=ABSENT_TARGET_TEXT,
            desktop_state=state,
        )
        result["absent_target_abstain_pass"] = absent is None

        stale_state = replace(state, screenshot_digest="0" * 64)
        try:
            locate_desktop_target(
                client=client,
                window_png=screenshot,
                target_text=TARGET_VISIBLE_TEXT,
                desktop_state=stale_state,
            )
        except DesktopGrounderError as exc:
            result["stale_frame_rejection_pass"] = "screenshot-digest-mismatch" in str(exc)

        result["pass"] = bool(
            result["same_frame_binding_pass"]
            and result["coordinate_contract_pass"]
            and result["target_point_inside_uia_pass"]
            and result["target_evidence_binding_pass"]
            and result["absent_target_abstain_pass"]
            and result["stale_frame_rejection_pass"]
            and result["proposal_only_contract_pass"]
            and state.process_id == fixture_pid
            and resolver.stats.desktop_fallback_calls == 0
            and resolver.stats.window_binding_failures == 0
            and resolver.stats.window_binding_ambiguities == 0
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()

    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("===== STAGE 26.2C DESKTOP GROUNDER =====")
    print(f"RESULT_PATH={result_path}")
    print(f"OBSERVER_SOURCE_SHA256={result['observer_source_sha256']}")
    print(f"GROUNDER_SOURCE_SHA256={result['grounder_source_sha256']}")
    print(f"DRIVER_SOURCE_SHA256={result['driver_source_sha256']}")
    print(f"TARGET_UIA_NAME={result['target_uia_name']}")
    print(f"TARGET_VISIBLE_TEXT={result['target_visible_text']}")
    print(f"SAME_FRAME_BINDING_PASS={result['same_frame_binding_pass']}")
    print(f"COORDINATE_CONTRACT_PASS={result['coordinate_contract_pass']}")
    print(f"TARGET_POINT_INSIDE_UIA_PASS={result['target_point_inside_uia_pass']}")
    print(f"TARGET_EVIDENCE_BINDING_PASS={result['target_evidence_binding_pass']}")
    print(f"ABSENT_TARGET_ABSTAIN_PASS={result['absent_target_abstain_pass']}")
    print(f"STALE_FRAME_REJECTION_PASS={result['stale_frame_rejection_pass']}")
    print(f"PROPOSAL_ONLY_CONTRACT_PASS={result['proposal_only_contract_pass']}")
    print(f"ERROR={result['error']}")
    print(f"PASS={result['pass']}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
