from __future__ import annotations

import ctypes
import secrets
import time
from datetime import datetime, timezone
from typing import Any


KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
INPUT_KEYBOARD = 1
MAX_TEXT_CHARS = 65_536


def _agent_error(status: int, code: str, message: str) -> Exception:
    from openadapt_flow.backends.win_agent.server import AgentRequestError

    return AgentRequestError(status, code, message)


def _delivery_receipt(operation: str) -> dict[str, Any]:
    return {
        "status": "delivered",
        "receipt_id": secrets.token_hex(12),
        "operation": operation,
        "native": False,
        "target_fingerprint": None,
        "delivered_at": datetime.now(timezone.utc).isoformat(),
        "outcome_verified": False,
    }


def send_unicode_text(text: str, interval_s: float) -> None:
    """Deliver exact bounded Unicode text through Win32 SendInput.

    This is the same narrow mechanism physically accepted in Stage 26.1C.
    It does not use the clipboard, change keyboard layout, start processes, or
    expose a generic execution channel.
    """

    if not isinstance(text, str) or len(text) > MAX_TEXT_CHARS:
        raise _agent_error(
            400,
            "invalid_schema",
            "text exceeds the bounded string contract",
        )
    if isinstance(interval_s, bool) or not isinstance(interval_s, (int, float)):
        raise _agent_error(400, "invalid_schema", "interval_s must be numeric")
    if not 0 <= float(interval_s) <= 1:
        raise _agent_error(
            400,
            "invalid_schema",
            "interval_s must be between 0 and 1",
        )
    if not text:
        return

    from ctypes import wintypes

    ULONG_PTR = ctypes.c_size_t

    class MOUSEINPUT(ctypes.Structure):
        _fields_ = [
            ("dx", wintypes.LONG),
            ("dy", wintypes.LONG),
            ("mouseData", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class KEYBDINPUT(ctypes.Structure):
        _fields_ = [
            ("wVk", wintypes.WORD),
            ("wScan", wintypes.WORD),
            ("dwFlags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ULONG_PTR),
        ]

    class HARDWAREINPUT(ctypes.Structure):
        _fields_ = [
            ("uMsg", wintypes.DWORD),
            ("wParamL", wintypes.WORD),
            ("wParamH", wintypes.WORD),
        ]

    class INPUTUNION(ctypes.Union):
        _fields_ = [
            ("mi", MOUSEINPUT),
            ("ki", KEYBDINPUT),
            ("hi", HARDWAREINPUT),
        ]

    class INPUT(ctypes.Structure):
        _anonymous_ = ("u",)
        _fields_ = [("type", wintypes.DWORD), ("u", INPUTUNION)]

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.SendInput.argtypes = (
        wintypes.UINT,
        ctypes.POINTER(INPUT),
        ctypes.c_int,
    )
    user32.SendInput.restype = wintypes.UINT

    for character in text:
        encoded = character.encode("utf-16-le")
        code_units = [
            int.from_bytes(encoded[index : index + 2], "little")
            for index in range(0, len(encoded), 2)
        ]
        inputs: list[INPUT] = []
        for code_unit in code_units:
            inputs.append(
                INPUT(
                    type=INPUT_KEYBOARD,
                    ki=KEYBDINPUT(
                        wVk=0,
                        wScan=code_unit,
                        dwFlags=KEYEVENTF_UNICODE,
                        time=0,
                        dwExtraInfo=0,
                    ),
                )
            )
            inputs.append(
                INPUT(
                    type=INPUT_KEYBOARD,
                    ki=KEYBDINPUT(
                        wVk=0,
                        wScan=code_unit,
                        dwFlags=KEYEVENTF_UNICODE | KEYEVENTF_KEYUP,
                        time=0,
                        dwExtraInfo=0,
                    ),
                )
            )
        batch = (INPUT * len(inputs))(*inputs)
        ctypes.set_last_error(0)
        sent = int(user32.SendInput(len(inputs), batch, ctypes.sizeof(INPUT)))
        if sent != len(inputs):
            error = ctypes.get_last_error()
            raise OSError(error, f"SendInput delivered {sent}/{len(inputs)} events")
        if interval_s:
            time.sleep(float(interval_s))


def bounded_input(payload: dict[str, Any]) -> dict[str, Any]:
    """Project-owned bounded typed-input adapter.

    Only ``type_text`` is replaced with the layout-independent accepted Win32
    path.  Every other typed action delegates to the pinned OpenAdapt input
    implementation.  No legacy/generic exec path is introduced.
    """

    from openadapt_flow.backends.win_agent.server import _perform_input

    if payload.get("action") != "type_text":
        return _perform_input(payload)

    allowed = {"action", "text", "interval_s"}
    if set(payload) - allowed or "text" not in payload:
        raise _agent_error(400, "invalid_schema", "invalid type_text fields")

    text = payload.get("text")
    interval = payload.get("interval_s", 0.05)
    if not isinstance(text, str) or len(text) > MAX_TEXT_CHARS:
        raise _agent_error(
            400,
            "invalid_schema",
            "text exceeds the bounded string contract",
        )
    if isinstance(interval, bool) or not isinstance(interval, (int, float)):
        raise _agent_error(400, "invalid_schema", "interval_s must be numeric")
    if not 0 <= float(interval) <= 1:
        raise _agent_error(
            400,
            "invalid_schema",
            "interval_s must be between 0 and 1",
        )

    send_unicode_text(text, float(interval))
    return _delivery_receipt("physical_type_text")
