from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


_TASK_ID_RE = re.compile(r"^[0-9a-f]{32}$")


class TaskLock:
    """Process-local cooperating-runner lock for one bounded state operation.

    This is a reusable local-state primitive. It does not grant capability
    authority and it does not claim distributed or machine-failure semantics.
    """

    def __init__(self, handle: Any, backend: str) -> None:
        self._handle = handle
        self._backend = backend
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        handle = self._handle
        self._handle = None
        if handle is None:
            return
        try:
            handle.seek(0)
            if self._backend == "windows":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except (OSError, ValueError):
            pass
        finally:
            try:
                handle.close()
            except Exception:
                pass

    def __enter__(self) -> "TaskLock":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()


def safe_child(root: Path, child: Path) -> Path:
    """Resolve one path strictly below a configured local-state root."""

    root = root.resolve()
    resolved = child.resolve(strict=False)
    if resolved == root or not resolved.is_relative_to(root):
        raise ValueError("procedure path escaped its configured root")
    return resolved


def task_lock_path(state_root: Path, task_id: str) -> Path:
    if not _TASK_ID_RE.fullmatch(task_id):
        raise ValueError("invalid task id")
    return safe_child(state_root, state_root / f".{task_id}.lock")


def acquire_task_lock(state_root: Path, task_id: str) -> TaskLock:
    """Acquire the accepted single-machine cooperating-runner lock.

    The contract is intentionally narrow: one 32-hex operation namespace,
    fail-closed non-blocking acquisition, Windows/POSIX local filesystem only.
    """

    state_root.mkdir(parents=True, exist_ok=True)
    path = task_lock_path(state_root, task_id)
    handle = path.open("a+b")
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"\x00")
            handle.flush()
        handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return TaskLock(handle, "windows")

        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return TaskLock(handle, "posix")
    except (OSError, ImportError) as exc:
        handle.close()
        raise BlockingIOError("task_already_running") from exc
