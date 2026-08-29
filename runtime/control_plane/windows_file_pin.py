from __future__ import annotations

import errno
import os
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Callable, Iterator


_GENERIC_READ = 0x80000000
_DELETE = 0x00010000
_FILE_READ_ATTRIBUTES = 0x00000080
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_OPEN_EXISTING = 3
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_DISPOSITION_INFO_CLASS = 4
_RESERVED_PARENT = ".chat-agent-platform"
_RESERVED_STAGE = "stage26-3a"


def _win32_api():
    if os.name != "nt":
        raise OSError(errno.ENOTSUP, "verified Windows file pin requires Windows")

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    create_file = kernel32.CreateFileW
    create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create_file.restype = wintypes.HANDLE

    close_handle = kernel32.CloseHandle
    close_handle.argtypes = [wintypes.HANDLE]
    close_handle.restype = wintypes.BOOL

    set_file_information = kernel32.SetFileInformationByHandle
    set_file_information.argtypes = [
        wintypes.HANDLE,
        wintypes.INT,
        wintypes.LPVOID,
        wintypes.DWORD,
    ]
    set_file_information.restype = wintypes.BOOL

    class FileDispositionInfo(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

    return ctypes, create_file, close_handle, set_file_information, FileDispositionInfo


@contextmanager
def _open_pinned_handle(
    path: Path,
    *,
    desired_access: int,
    share_mode: int,
    directory: bool,
) -> Iterator[tuple[object, tuple[object, object, object]]]:
    ctypes, create_file, close_handle, set_file_information, disposition_type = _win32_api()
    flags = _FILE_FLAG_BACKUP_SEMANTICS if directory else _FILE_FLAG_OPEN_REPARSE_POINT
    handle = create_file(
        str(path),
        desired_access,
        share_mode,
        None,
        _OPEN_EXISTING,
        flags,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        code = ctypes.get_last_error()
        raise OSError(code, ctypes.FormatError(code), str(path))

    try:
        yield handle, (set_file_information, disposition_type, ctypes)
    finally:
        # A close failure can only retain protection longer than requested. It
        # must not mask the primary mutation/verification result; process exit is
        # the final OS cleanup boundary for an otherwise leaked handle.
        close_handle(handle)


def _infer_workspace_root(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("pinned path must be pathlib.Path")
    absolute = path.resolve(strict=False)
    if (
        absolute.parent.name != _RESERVED_STAGE
        or absolute.parent.parent.name != _RESERVED_PARENT
    ):
        raise ValueError("pinned path is outside the verified workspace artifact layout")
    return absolute.parent.parent.parent


def _namespace_components(workspace_root: Path, path: Path) -> tuple[Path, ...]:
    if not isinstance(workspace_root, Path) or not isinstance(path, Path):
        raise TypeError("workspace_root and pinned path must be pathlib.Path")
    root = workspace_root.resolve(strict=False)
    absolute = path.resolve(strict=False)
    try:
        relative_parent = absolute.parent.relative_to(root)
    except ValueError as exc:
        raise ValueError("pinned path escaped configured workspace root") from exc

    components = [root]
    current = root
    for part in relative_parent.parts:
        current = current / part
        components.append(current)
    return tuple(components)


@contextmanager
def _pin_namespace(workspace_root: Path, path: Path) -> Iterator[None]:
    with ExitStack() as stack:
        for directory in _namespace_components(workspace_root, path):
            stack.enter_context(
                _open_pinned_handle(
                    directory,
                    desired_access=_FILE_READ_ATTRIBUTES,
                    share_mode=_FILE_SHARE_READ | _FILE_SHARE_WRITE,
                    directory=True,
                )
            )
        yield


@contextmanager
def pin_file_for_verified_link(
    path: Path,
    *,
    workspace_root: Path | None = None,
) -> Iterator[None]:
    """Pin staging plus its trusted namespace during hard-link delivery."""

    root = _infer_workspace_root(path) if workspace_root is None else workspace_root
    with _pin_namespace(root, path), _open_pinned_handle(
        path,
        desired_access=_GENERIC_READ,
        share_mode=_FILE_SHARE_READ,
        directory=False,
    ):
        yield


@contextmanager
def pin_file_for_verified_delete(
    path: Path,
    *,
    workspace_root: Path | None = None,
) -> Iterator[Callable[[], None]]:
    """Pin one exact path and expose a handle-bound delete-on-close operation."""

    root = _infer_workspace_root(path) if workspace_root is None else workspace_root
    with _pin_namespace(root, path), _open_pinned_handle(
        path,
        desired_access=_GENERIC_READ | _DELETE,
        share_mode=_FILE_SHARE_READ,
        directory=False,
    ) as (handle, api):
        set_file_information, disposition_type, ctypes = api

        def mark_delete() -> None:
            disposition = disposition_type(True)
            if not set_file_information(
                handle,
                _FILE_DISPOSITION_INFO_CLASS,
                ctypes.byref(disposition),
                ctypes.sizeof(disposition),
            ):
                code = ctypes.get_last_error()
                raise OSError(code, ctypes.FormatError(code), str(path))

        yield mark_delete
