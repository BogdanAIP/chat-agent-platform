from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .verification import ObservationRef, ObservationSnapshot


FILE_ARTIFACT_CAPABILITY = "filesystem.artifact"
DEFAULT_MAX_OBSERVED_BYTES = 16384
_MAX_SUBJECTS = 16


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _identity(value: os.stat_result) -> dict[str, int]:
    return {"device": int(value.st_dev), "inode": int(value.st_ino)}


def _missing_state() -> dict[str, Any]:
    return {
        "exists": False,
        "kind": "missing",
        "size": None,
        "sha256": None,
        "identity": None,
    }


def _kind(value: os.stat_result) -> str:
    mode = value.st_mode
    if stat.S_ISREG(mode):
        return "file"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISLNK(mode):
        return "symlink"
    return "other"


def _same_file_state(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev == right.st_dev
        and left.st_ino == right.st_ino
        and left.st_size == right.st_size
        and left.st_mtime_ns == right.st_mtime_ns
    )


def _observe_path(path: Path, *, max_bytes: int) -> tuple[dict[str, Any], bool, bool]:
    try:
        initial = os.lstat(path)
    except FileNotFoundError:
        return _missing_state(), True, False
    except OSError:
        return _missing_state(), False, True

    kind = _kind(initial)
    state: dict[str, Any] = {
        "exists": True,
        "kind": kind,
        "size": int(initial.st_size),
        "sha256": None,
        "identity": _identity(initial),
    }
    if kind != "file":
        return state, True, False

    flags = os.O_RDONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        descriptor = os.open(path, flags)
    except FileNotFoundError:
        return _missing_state(), False, True
    except OSError:
        state.pop("sha256")
        return state, False, False

    data = bytearray()
    complete = True
    ambiguous = False
    opened = initial
    finished = initial
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or not _same_file_state(initial, opened):
            return state, False, True
        while len(data) <= max_bytes:
            chunk = os.read(descriptor, min(65536, max_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) > max_bytes:
            complete = False
        finished = os.fstat(descriptor)
        if not _same_file_state(opened, finished):
            ambiguous = True
            complete = False
    except OSError:
        complete = False
        ambiguous = True
    finally:
        os.close(descriptor)

    try:
        final_path = os.lstat(path)
    except OSError:
        final_path = None
    if final_path is None or not _same_file_state(finished, final_path):
        ambiguous = True
        complete = False

    state = {
        "exists": True,
        "kind": "file",
        "size": int(finished.st_size),
        "identity": _identity(finished),
    }
    if complete:
        state["sha256"] = hashlib.sha256(bytes(data)).hexdigest()
    return state, complete, ambiguous


def observe_file_state(
    path: Path,
    *,
    max_bytes: int = DEFAULT_MAX_OBSERVED_BYTES,
) -> tuple[dict[str, Any], bool, bool]:
    """Observe one path with the same bounded non-following evidence contract."""

    if not isinstance(path, Path):
        raise TypeError("observed file path must be pathlib.Path")
    if type(max_bytes) is not int or max_bytes < 1 or max_bytes > 16 * 1024 * 1024:
        raise ValueError("file observation byte bound is invalid")
    return _observe_path(path, max_bytes=max_bytes)


class FileArtifactObservationStream:
    """Produce bounded, race-aware snapshots for one fixed set of rooted paths."""

    def __init__(
        self,
        *,
        root: Path,
        subject: str,
        paths: dict[str, Path],
        max_bytes: int = DEFAULT_MAX_OBSERVED_BYTES,
        stream_id: str | None = None,
    ) -> None:
        if type(subject) is not str or not subject.strip() or len(subject) > 512:
            raise ValueError("file observation subject must be bounded non-empty text")
        if type(paths) is not dict or not paths or len(paths) > _MAX_SUBJECTS:
            raise ValueError("file observation paths must be a bounded non-empty plain mapping")
        if type(max_bytes) is not int or max_bytes < 1 or max_bytes > 16 * 1024 * 1024:
            raise ValueError("file observation byte bound is invalid")

        resolved_root = Path(root).resolve(strict=True)
        if not resolved_root.is_dir():
            raise ValueError("file observation root must be an existing directory")
        normalized: dict[str, Path] = {}
        for name, value in paths.items():
            if type(name) is not str or not name or len(name) > 256:
                raise ValueError("file observation path labels must be bounded non-empty strings")
            if not isinstance(value, Path):
                raise TypeError("file observation paths must be pathlib.Path values")
            absolute = Path(os.path.abspath(value if value.is_absolute() else resolved_root / value))
            resolved_parent = absolute.parent.resolve(strict=False)
            resolved = resolved_parent / absolute.name
            if resolved == resolved_root or not resolved_parent.is_relative_to(resolved_root):
                raise ValueError("file observation path escaped its configured root")
            normalized[name] = resolved

        if stream_id is None:
            stream_id = secrets.token_hex(16)
        if type(stream_id) is not str or not stream_id.strip() or len(stream_id) > 512:
            raise ValueError("file observation stream_id must be bounded non-empty text")

        self._root = resolved_root
        self._subject = subject
        self._paths = normalized
        self._max_bytes = max_bytes
        self._stream_id = stream_id
        self._sequence = -1

    def observe(self) -> ObservationSnapshot:
        state: dict[str, Any] = {}
        complete = True
        ambiguous = False
        for name in sorted(self._paths):
            path = self._paths[name]
            try:
                current_parent = path.parent.resolve(strict=False)
            except OSError:
                item_state, item_complete, item_ambiguous = _missing_state(), False, True
            else:
                if not current_parent.is_relative_to(self._root):
                    item_state, item_complete, item_ambiguous = _missing_state(), False, True
                else:
                    item_state, item_complete, item_ambiguous = _observe_path(
                        path,
                        max_bytes=self._max_bytes,
                    )
                    try:
                        final_parent = path.parent.resolve(strict=False)
                    except OSError:
                        final_parent = None
                    if final_parent != current_parent or (
                        final_parent is not None and not final_parent.is_relative_to(self._root)
                    ):
                        item_complete = False
                        item_ambiguous = True
            state[name] = item_state
            complete = complete and item_complete
            ambiguous = ambiguous or item_ambiguous

        self._sequence += 1
        fingerprint_payload = {
            "state": state,
            "complete": complete,
            "ambiguous": ambiguous,
        }
        fingerprint = hashlib.sha256(
            json.dumps(
                fingerprint_payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        ref = ObservationRef(
            capability=FILE_ARTIFACT_CAPABILITY,
            subject=self._subject,
            stream_id=self._stream_id,
            sequence=self._sequence,
            fingerprint=fingerprint,
            observed_at=_utc_now(),
        )
        return ObservationSnapshot(
            ref=ref,
            state=state,
            complete=complete,
            ambiguous=ambiguous,
        )
