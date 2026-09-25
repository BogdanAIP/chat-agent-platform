"""Unwired WinApp UIA Invoke candidate for later exact-window qualification.

The caller must already own CAP authorization and operation identity. This
executor supplies one delivery receipt, never task/effect verification. It is
intentionally absent from the public Chat and procedure registries.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Callable, Mapping

from .observation import ControlObservation, DesktopState
from .routing import DesktopClickRequest


_SAFE_TEXT = re.compile(r"[^\x00-\x1f\x7f]{1,256}\Z")
_MAX_JSON_BYTES = 2 * 1024 * 1024
_TIMEOUT_SECONDS = 20
_MAX_OBSERVATION_AGE_SECONDS = 5.0


class WinAppCandidateRefused(RuntimeError):
    """No mutation was requested by this candidate."""


class WinAppDeliveryUnknown(RuntimeError):
    """Invoke was requested; an external effect may already have happened."""


WinAppRunner = Callable[[tuple[str, ...]], Mapping[str, Any]]
WindowObserver = Callable[[], DesktopState]


def _run_winapp_json(binary: Path, args: tuple[str, ...]) -> Mapping[str, Any]:
    """Run a fixed candidate command via an explicitly configured executable."""

    if os.name != "nt":
        raise WinAppCandidateRefused("WinApp requires a local Windows installation")
    try:
        resolved = binary.resolve(strict=True)
        if resolved.name.casefold() != "winapp.exe" or not resolved.is_file():
            raise WinAppCandidateRefused("configured WinApp executable is invalid")
        completed = subprocess.run(
            (str(resolved), *args), shell=False, capture_output=True,
            encoding="utf-8", timeout=_TIMEOUT_SECONDS, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        raise WinAppCandidateRefused("WinApp command failed or timed out") from exc
    if completed.returncode != 0:
        raise WinAppCandidateRefused("WinApp command returned nonzero status")
    if len(completed.stdout.encode("utf-8")) > _MAX_JSON_BYTES:
        raise WinAppCandidateRefused("WinApp JSON output exceeds candidate limit")
    try:
        result = json.loads(completed.stdout)
    except (ValueError, TypeError) as exc:
        raise WinAppCandidateRefused("WinApp command returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise WinAppCandidateRefused("WinApp command returned invalid JSON shape")
    return result


def _recent(state: DesktopState) -> datetime:
    if not isinstance(state, DesktopState):
        raise WinAppCandidateRefused("CAP desktop observation is missing")
    try:
        captured = datetime.fromisoformat(state.observed_at.replace("Z", "+00:00"))
        if captured.tzinfo is None:
            raise ValueError("missing timezone")
        age = (datetime.now(timezone.utc) - captured).total_seconds()
    except (AttributeError, ValueError, TypeError) as exc:
        raise WinAppCandidateRefused("CAP desktop observation is invalid") from exc
    if not -2.0 <= age <= _MAX_OBSERVATION_AGE_SECONDS:
        raise WinAppCandidateRefused("CAP desktop observation is stale")
    return captured.astimezone(timezone.utc)


def _identity(state: DesktopState) -> tuple[object, ...]:
    return (
        state.session_id, state.application_identity, state.executable_name,
        state.process_id, state.process_generation, state.window_handle,
        state.window_instance, state.window_title, state.window_bounds,
        state.coordinate_space,
    )


def _normal(value: str) -> str:
    return " ".join(value.casefold().split())


def _valid_selector(value: object) -> bool:
    # argv is never handed to a shell, but a leading dash is still a CLI option.
    return (isinstance(value, str) and bool(value.strip())
            and not value.startswith("-") and _SAFE_TEXT.fullmatch(value) is not None)


def _matches_control(element: Mapping[str, Any], control: ControlObservation, hwnd: int) -> bool:
    bounds = control.bounds
    if bounds is None or not all(isinstance(element.get(key), str) for key in ("type", "name")):
        return False
    if element.get("automationId") is not None and not isinstance(element["automationId"], str):
        return False
    # WinApp scrubs per-element windowHandle from search JSON; explicit -w and
    # checked status bind the window. Still reject any conflicting non-null HWND.
    window_handle = element.get("windowHandle")
    if window_handle is not None and (type(window_handle) is not int or window_handle != hwnd):
        return False
    if (
        _normal(element["type"]) != _normal(control.role)
        or _normal(element["name"]) != _normal(control.name)
        or (element.get("automationId") or "") != control.automation_id
        or element.get("isEnabled") is not True
        or element.get("isOffscreen") is not False
        or element.get("isInvokable") is not True
    ):
        return False
    for key, expected in (
        ("x", bounds.left), ("y", bounds.top),
        ("width", bounds.width), ("height", bounds.height),
    ):
        measured = element.get(key)
        if isinstance(measured, bool) or not isinstance(measured, (int, float)):
            return False
        if not math.isfinite(measured) or abs(measured - expected) > 0.5:
            return False
    return _valid_selector(element.get("selector"))


class WinAppInvokeCandidate:
    """One private structural executor, suitable only for a CAP-authorized call."""

    def __init__(
        self,
        *,
        binary: Path,
        observe_window: WindowObserver,
        run_cli: WinAppRunner | None = None,
    ) -> None:
        binary = Path(binary)
        if not binary.is_absolute() or binary.name.casefold() != "winapp.exe":
            raise ValueError("WinApp executable must be an absolute winapp.exe path")
        self._binary = binary
        self._observe_window = observe_window
        self._run_cli = run_cli or (lambda args: _run_winapp_json(self._binary, args))

    def _read(self, args: tuple[str, ...]) -> Mapping[str, Any]:
        try:
            result = self._run_cli(args)
        except Exception as exc:
            raise WinAppCandidateRefused("WinApp read failed") from exc
        if not isinstance(result, Mapping):
            raise WinAppCandidateRefused("WinApp read returned an invalid shape")
        return result

    def _check_status(self, state: DesktopState) -> None:
        status = self._read(("ui", "status", "-w", str(state.window_handle), "--json"))
        process_name = status.get("processName")
        if not isinstance(process_name, str) or not process_name:
            raise WinAppCandidateRefused("WinApp process identity missing")
        expected = state.executable_name.casefold().removesuffix(".exe")
        actual = process_name.casefold().removesuffix(".exe")
        if (
            type(status.get("processId")) is not int
            or status["processId"] != state.process_id
            or type(status.get("hwnd")) is not int
            or status["hwnd"] != state.window_handle
            or actual != expected
            or status.get("windowTitle") != state.window_title
        ):
            raise WinAppCandidateRefused("WinApp window identity differs from CAP")

    def __call__(
        self,
        request: DesktopClickRequest,
        control: ControlObservation,
        state: DesktopState,
    ) -> Mapping[str, Any]:
        captured_before = _recent(state)
        if (
            not isinstance(request, DesktopClickRequest)
            or not isinstance(control, ControlObservation)
            or not state.executable_name
            or not state.process_generation
            or not state.application_identity
            or type(state.process_id) is not int or state.process_id <= 0
            or type(state.window_handle) is not int or state.window_handle <= 0
            or request.window_name != state.window_title
            or request.role is None
            or _normal(request.role) != _normal(control.role)
            or _normal(request.structural_name or request.target_text) != _normal(control.name)
            or (request.automation_id is not None and request.automation_id != control.automation_id)
            or control.enabled is not True or control.visible is not True
            or control.bounds is None
            or sum(c.observation_fingerprint == control.observation_fingerprint for c in state.controls) != 1
        ):
            raise WinAppCandidateRefused("CAP did not bind one actionable target in this window")
        query = control.automation_id or control.name
        if not _valid_selector(query):
            raise WinAppCandidateRefused("target does not have a bounded WinApp query")

        self._check_status(state)
        search = self._read(("ui", "search", query, "-w", str(state.window_handle),
                             "--max", "50", "--json"))
        matches = search.get("matches")
        if (
            not isinstance(matches, list)
            or type(search.get("matchCount")) is not int
            or search["matchCount"] != len(matches)
            or search.get("hasMore") is not False
        ):
            raise WinAppCandidateRefused("WinApp search was incomplete")
        exact = [m for m in matches if isinstance(m, Mapping)
                 and _matches_control(m, control, state.window_handle)]
        if len(exact) != 1:
            raise WinAppCandidateRefused("WinApp target was absent or ambiguous")
        selector = exact[0]["selector"]

        try:
            fresh = self._observe_window()
        except Exception as exc:
            raise WinAppCandidateRefused("CAP re-observation failed") from exc
        captured_after = _recent(fresh)
        if captured_after <= captured_before or _identity(fresh) != _identity(state) or sum(
            c.observation_fingerprint == control.observation_fingerprint
            for c in fresh.controls
        ) != 1:
            raise WinAppCandidateRefused("CAP window or target changed before action")
        self._check_status(fresh)

        # From this call onward even an exception/timeout may mean the Invoke
        # reached the provider. Never retry without independent reconciliation.
        try:
            result = self._run_cli(("ui", "invoke", selector, "-w", str(state.window_handle),
                                    "--action", "invoke", "--json"))
            if (
                not isinstance(result, Mapping)
                or result.get("requestedAction") != "invoke"
                or result.get("performedAction") != "invoke"
                or result.get("pattern") != "InvokePattern"
                or result.get("elementId") != selector
                or type(result.get("hwnd")) is not int
                or result["hwnd"] != state.window_handle
            ):
                raise ValueError("WinApp action reply was incomplete or mismatched")
        except Exception as exc:
            raise WinAppDeliveryUnknown(
                "WinApp invoke outcome is uncertain; reconcile before any new action"
            ) from exc
        return {
            "status": "delivered", "operation": "uia_invoke",
            "outcome_verified": False,
            "window_handle": state.window_handle,
            "process_id": state.process_id,
            "process_generation": state.process_generation,
            "target_fingerprint": control.observation_fingerprint,
            "backend": "winapp-cli-candidate",
        }
