from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from openadapt_capture import CaptureSession
from openadapt_capture import Recorder as CaptureRecorder
from openadapt_flow.compiler import compile_recording
from openadapt_flow.desktop_record import record_desktop_capture


REQUIRED_FLOW_KINDS = {"click", "type", "key", "scroll"}
EXPECTED_TEXT = "CAPTURE_OK"
EXPECTED_KEY = "Enter"
EXPECTED_WINDOW_SCOPED_SURFACE = "rdp"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _read_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(json.loads(line))
    return events


def _count_key_recursive(value: Any, key: str) -> int:
    if isinstance(value, dict):
        count = 1 if key in value and value[key] not in (None, {}, []) else 0
        return count + sum(_count_key_recursive(v, key) for v in value.values())
    if isinstance(value, list):
        return sum(_count_key_recursive(v, key) for v in value)
    return 0


class _ReadyMarkerRecorder:
    """Real Capture Recorder with qualification-only policy overrides.

    Input is observed by OpenAdapt's native observer. We intentionally do not
    synthesize mouse/keyboard events: Capture filters injected input and this
    qualification must exercise the real physical-user-input path.
    """

    def __init__(
        self,
        *,
        task: str,
        capture_dir: str,
        window_title: str,
        ready: Path,
        ffmpeg_path: Path,
        ffprobe_path: Path,
    ) -> None:
        self._ready = ready
        self._inner = CaptureRecorder(
            capture_dir=capture_dir,
            task_description=task,
            capture_video=True,
            capture_audio=False,
            capture_images=False,
            capture_window_data=False,
            capture_structural_observations=True,
            capture_browser_events=False,
            capture_full_video=False,
            ffmpeg_path=str(ffmpeg_path),
            ffprobe_path=str(ffprobe_path),
            log_memory=False,
            plot_performance=False,
            screen_capture_fps=4.0,
            window={"owner": None, "title": window_title},
        )

    def __enter__(self) -> "_ReadyMarkerRecorder":
        self._inner.__enter__()
        return self

    def __exit__(self, *exc: Any) -> None:
        self._inner.__exit__(*exc)

    def wait_for_ready(self, timeout: float = 60.0) -> bool:
        ok = self._inner.wait_for_ready(timeout=timeout)
        if not ok:
            raise RuntimeError("OpenAdapt Capture did not become ready before timeout")
        self._ready.write_text("READY\n", encoding="ascii")
        return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--window-title", required=True)
    parser.add_argument("--fixture-state", required=True)
    parser.add_argument("--done", required=True)
    parser.add_argument("--recorder-ready", required=True)
    parser.add_argument("--ffmpeg", required=True)
    parser.add_argument("--ffprobe", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=240.0)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).resolve()
    raw_dir = run_dir / "raw-capture"
    recording_dir = run_dir / "flow-recording"
    bundle_dir = run_dir / "compiled-bundle"
    fixture_state_path = Path(args.fixture_state).resolve()
    done_path = Path(args.done).resolve()
    ready_path = Path(args.recorder_ready).resolve()
    ffmpeg_path = Path(args.ffmpeg).resolve()
    ffprobe_path = Path(args.ffprobe).resolve()
    result_path = run_dir / "driver-result.json"

    result: dict[str, Any] = {
        "schema_version": 1,
        "python_version": ".".join(map(str, sys.version_info[:3])),
        "window_title": args.window_title,
        "raw_capture_dir": str(raw_dir),
        "recording_dir": str(recording_dir),
        "bundle_dir": str(bundle_dir),
        "fixture_state": None,
        "raw_action_count": 0,
        "raw_action_types": [],
        "raw_structural_action_count": 0,
        "foreign_structural_window_count": 0,
        "foreign_structural_windows": [],
        "foreign_structural_window_pass": False,
        "flow_event_count": 0,
        "flow_event_kinds": [],
        "type_values": [],
        "key_values": [],
        "structural_event_count": 0,
        "window_capture": None,
        "window_scope_pass": False,
        "required_kinds_pass": False,
        "expected_text_pass": False,
        "expected_key_pass": False,
        "uia_evidence_pass": False,
        "fixture_sequence_pass": False,
        "video_evidence_pass": False,
        "compile_pass": False,
        "compiled_step_count": 0,
        "compiled_structural_count": 0,
        "compiled_surface": None,
        "window_scoped_surface_contract": EXPECTED_WINDOW_SCOPED_SURFACE,
        "surface_contract_pass": False,
        "native_windows_replay_claimed": False,
        "replay_execution": "SKIPPED_UNACCEPTED_WINDOWS_EXECUTOR",
        "bounded_replay_refusal": True,
        "pass": False,
        "error": None,
        "traceback": None,
    }

    run_dir.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + args.timeout_seconds
    done_seen_at: float | None = None

    def should_stop() -> bool:
        nonlocal done_seen_at
        if fixture_state_path.exists():
            try:
                state = _read_json(fixture_state_path)
            except Exception:
                state = {}
            if state.get("closed_early") and not done_path.exists():
                raise RuntimeError("qualification fixture was closed before completion")
        if done_path.exists():
            if done_seen_at is None:
                done_seen_at = time.monotonic()
            # Keep recording briefly after Finish so Capture has an after-frame
            # opportunity and sees the click release before teardown.
            if time.monotonic() - done_seen_at >= 1.5:
                return True
        if time.monotonic() >= deadline:
            raise TimeoutError("timed out waiting for the qualification fixture")
        return False

    task = (
        "Stage 26.1B bounded Windows capture qualification: click start, type "
        "CAPTURE_OK, press Enter, scroll the list, click finish"
    )

    def factory(task_description: str, capture_dir: str):
        return _ReadyMarkerRecorder(
            task=task_description,
            capture_dir=capture_dir,
            window_title=args.window_title,
            ready=ready_path,
            ffmpeg_path=ffmpeg_path,
            ffprobe_path=ffprobe_path,
        )

    try:
        if not ffmpeg_path.is_file() or not ffprobe_path.is_file():
            raise RuntimeError("pinned FFmpeg qualification runtime is missing")

        recording = record_desktop_capture(
            recording_dir,
            task_description=task,
            window={"owner": None, "title": args.window_title},
            capture_dir=raw_dir,
            ready_timeout_s=60.0,
            recorder_factory=factory,
            stop=should_stop,
            announce=False,
        )
        recording_dir = Path(recording)

        if not fixture_state_path.is_file():
            raise RuntimeError("fixture state file is missing after capture")
        fixture_state = _read_json(fixture_state_path)
        result["fixture_state"] = fixture_state
        result["fixture_sequence_pass"] = all(
            bool(fixture_state.get(name))
            for name in (
                "ready",
                "recorder_ready",
                "start_clicked",
                "text_ok",
                "enter_pressed",
                "scroll_seen",
                "finish_clicked",
            )
        ) and fixture_state.get("text_value") == EXPECTED_TEXT

        # Inspect the real raw Capture actions before relying on the Flow
        # conversion. Structural observations are optional, but any window
        # identity that is present must point at the bounded fixture.
        foreign_windows: list[str] = []
        with CaptureSession.load(raw_dir) as capture:
            raw_actions = list(capture.actions(include_moves=False))
            result["raw_action_count"] = len(raw_actions)
            result["raw_action_types"] = [action.type for action in raw_actions]
            raw_structural = [
                action.structural_observation
                for action in raw_actions
                if action.structural_observation is not None
            ]
            result["raw_structural_action_count"] = len(raw_structural)
            for observation in raw_structural:
                title = (
                    observation.window.title
                    if observation.window is not None
                    else None
                )
                if title and args.window_title.lower() not in title.lower():
                    foreign_windows.append(title)
        result["foreign_structural_windows"] = sorted(set(foreign_windows))
        result["foreign_structural_window_count"] = len(foreign_windows)
        result["foreign_structural_window_pass"] = len(foreign_windows) == 0

        video_files = list(raw_dir.glob("oa_recording-*.mp4"))
        result["video_evidence_pass"] = bool(
            len(video_files) == 1 and video_files[0].stat().st_size > 0
        )

        meta = _read_json(recording_dir / "meta.json")
        events = _read_events(recording_dir / "events.jsonl")
        result["flow_event_count"] = len(events)
        kinds = [str(event.get("kind")) for event in events]
        result["flow_event_kinds"] = kinds
        result["required_kinds_pass"] = REQUIRED_FLOW_KINDS.issubset(set(kinds))

        type_values = [
            str(event.get("text")) for event in events if event.get("kind") == "type"
        ]
        key_values = [
            str(event.get("key")) for event in events if event.get("kind") == "key"
        ]
        result["type_values"] = type_values
        result["key_values"] = key_values
        result["expected_text_pass"] = EXPECTED_TEXT in type_values
        result["expected_key_pass"] = EXPECTED_KEY in key_values

        structural_events = [
            event for event in events if isinstance(event.get("structural"), dict)
        ]
        result["structural_event_count"] = len(structural_events)
        result["uia_evidence_pass"] = bool(
            result["raw_structural_action_count"] > 0
            and any(
                event["structural"].get("automation_id")
                or (
                    event["structural"].get("role")
                    and event["structural"].get("name")
                )
                for event in structural_events
            )
        )

        window_capture = meta.get("window_capture")
        result["window_capture"] = window_capture
        result["window_scope_pass"] = bool(
            isinstance(window_capture, dict)
            and window_capture.get("coordinate_space") == "window_pixels"
            and args.window_title.lower()
            in str(window_capture.get("resolved_title") or "").lower()
        )

        # Do not lie about the upstream surface contract. Flow 1.31.0 stamps a
        # window-scoped Capture conversion as backend=rdp because this capture
        # mode was designed for one remote-client window. Compiling it as
        # target_surface="windows" would correctly refuse as contradictory.
        # Stage 26.1B qualifies recording/conversion/compiler evidence only;
        # native Windows replay remains a separate Stage 26.1C design decision.
        workflow = compile_recording(
            recording_dir,
            bundle_dir,
            name="stage26_1b_windows_capture_fixture",
        )
        workflow_data = workflow.model_dump(mode="json", exclude_none=True)
        result["compiled_step_count"] = len(workflow.steps)
        result["compiled_structural_count"] = _count_key_recursive(
            workflow_data, "structural"
        )
        result["compiled_surface"] = workflow_data.get("surface")
        result["surface_contract_pass"] = (
            result["compiled_surface"] == EXPECTED_WINDOW_SCOPED_SURFACE
            and (meta.get("backend_hints") or {}).get("backend")
            == EXPECTED_WINDOW_SCOPED_SURFACE
        )
        result["compile_pass"] = bool(
            (bundle_dir / "workflow.json").is_file()
            and (bundle_dir / "workflow.py").is_file()
            and len(workflow.steps) > 0
            and result["surface_contract_pass"]
        )

        result["pass"] = all(
            bool(result[name])
            for name in (
                "fixture_sequence_pass",
                "video_evidence_pass",
                "window_scope_pass",
                "foreign_structural_window_pass",
                "required_kinds_pass",
                "expected_text_pass",
                "expected_key_pass",
                "uia_evidence_pass",
                "compile_pass",
                "surface_contract_pass",
                "bounded_replay_refusal",
            )
        )
    except BaseException as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        result["traceback"] = traceback.format_exc()
    finally:
        result_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    print("===== STAGE 26.1B CAPTURE DRIVER =====")
    for key in (
        "raw_action_count",
        "raw_action_types",
        "raw_structural_action_count",
        "foreign_structural_window_count",
        "flow_event_count",
        "flow_event_kinds",
        "structural_event_count",
        "video_evidence_pass",
        "window_scope_pass",
        "foreign_structural_window_pass",
        "required_kinds_pass",
        "expected_text_pass",
        "expected_key_pass",
        "uia_evidence_pass",
        "fixture_sequence_pass",
        "compile_pass",
        "compiled_step_count",
        "compiled_structural_count",
        "compiled_surface",
        "surface_contract_pass",
        "native_windows_replay_claimed",
        "replay_execution",
        "bounded_replay_refusal",
        "error",
        "pass",
    ):
        print(f"{key.upper()}={result.get(key)}")
    print(f"DRIVER_RESULT_PATH={result_path}")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
