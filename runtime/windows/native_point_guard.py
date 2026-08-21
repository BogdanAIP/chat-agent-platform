from __future__ import annotations

import os
from typing import NamedTuple

from .observation import DesktopState


GA_ROOT = 2
SCREEN_COORDINATE_SPACE = "screen_physical_px"


class NativePointGuardError(RuntimeError):
    """Fail-closed native hit-test/foreground authorization error."""


class NativePointContext(NamedTuple):
    foreground_hwnd: int
    foreground_pid: int
    hit_hwnd: int
    hit_root_hwnd: int
    hit_pid: int


def native_point_context_authorized(
    *,
    expected_hwnd: int,
    expected_pid: int,
    foreground_hwnd: int,
    foreground_pid: int,
    hit_root_hwnd: int,
    hit_pid: int,
) -> bool:
    """Pure authorization predicate for one physical screen point.

    The target top-level window must be foreground and the actual root window
    under the click point must be the same HWND/PID. This rejects overlays,
    focus changes and foreign-process windows before coordinate mutation.
    """

    values = (
        expected_hwnd,
        expected_pid,
        foreground_hwnd,
        foreground_pid,
        hit_root_hwnd,
        hit_pid,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in values):
        return False
    return bool(
        foreground_hwnd == expected_hwnd
        and hit_root_hwnd == expected_hwnd
        and foreground_pid == expected_pid
        and hit_pid == expected_pid
    )


def observe_native_point_context(x: int, y: int) -> NativePointContext:
    """Observe current foreground and root HWND actually under a screen point."""

    if os.name != "nt":
        raise NativePointGuardError("native point guard requires Windows")
    if isinstance(x, bool) or isinstance(y, bool) or not isinstance(x, int) or not isinstance(y, int):
        raise NativePointGuardError("native point coordinates must be integers")

    import ctypes
    from ctypes import wintypes

    class POINT(ctypes.Structure):
        _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.WindowFromPoint.argtypes = [POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    foreground = int(user32.GetForegroundWindow() or 0)
    hit = int(user32.WindowFromPoint(POINT(x=x, y=y)) or 0)
    hit_root = int(user32.GetAncestor(hit, GA_ROOT) or 0) if hit else 0
    if foreground <= 0:
        raise NativePointGuardError("no foreground window is available")
    if hit <= 0 or hit_root <= 0:
        raise NativePointGuardError("no native window is present under the proposed click point")

    def pid_for(hwnd: int) -> int:
        pid = wintypes.DWORD()
        thread_id = int(user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid)))
        if thread_id <= 0 or int(pid.value) <= 0:
            error = ctypes.get_last_error()
            raise NativePointGuardError(
                f"GetWindowThreadProcessId failed for hwnd={hwnd} ({error})"
            )
        return int(pid.value)

    return NativePointContext(
        foreground_hwnd=foreground,
        foreground_pid=pid_for(foreground),
        hit_hwnd=hit,
        hit_root_hwnd=hit_root,
        hit_pid=pid_for(hit_root),
    )


def require_foreground_hit_target(state: DesktopState, x: int, y: int) -> NativePointContext:
    """Require the proposed screen point to hit the current bound foreground window."""

    if not isinstance(state, DesktopState):
        raise NativePointGuardError("native point guard requires DesktopState")
    if state.coordinate_space != SCREEN_COORDINATE_SPACE:
        raise NativePointGuardError("native point guard requires screen physical coordinates")
    if not (
        state.window_bounds.left <= x <= state.window_bounds.right
        and state.window_bounds.top <= y <= state.window_bounds.bottom
    ):
        raise NativePointGuardError("proposed click point is outside the observed window bounds")

    context = observe_native_point_context(x, y)
    if not native_point_context_authorized(
        expected_hwnd=state.window_handle,
        expected_pid=state.process_id,
        foreground_hwnd=context.foreground_hwnd,
        foreground_pid=context.foreground_pid,
        hit_root_hwnd=context.hit_root_hwnd,
        hit_pid=context.hit_pid,
    ):
        raise NativePointGuardError(
            "foreground or hit-tested root window no longer matches the authorized DesktopState"
        )
    return context
