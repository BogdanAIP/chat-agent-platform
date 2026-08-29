from __future__ import annotations

import errno
import os
import stat as stat_module
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
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
_DUPLICATE_SAME_ACCESS = 0x00000002
_RESERVED_PARENT = ".chat-agent-platform"
_RESERVED_STAGE = "stage26-3a"
_DEFAULT_MAX_VERIFY_BYTES = 16384


@dataclass(frozen=True)
class PinnedFileSnapshot:
    stat: os.stat_result
    data: bytes | None


class VerifiedDeletePin:
    def __init__(self, snapshot: PinnedFileSnapshot, mark_delete: Callable[[], None]) -> None:
        self.snapshot = snapshot
        self._mark_delete = mark_delete

    def __call__(self) -> None:
        self._mark_delete()


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

    duplicate_handle = kernel32.DuplicateHandle
    duplicate_handle.argtypes = [
        wintypes.HANDLE,
        wintypes.HANDLE,
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.DWORD,
        wintypes.BOOL,
        wintypes.DWORD,
    ]
    duplicate_handle.restype = wintypes.BOOL

    get_current_process = kernel32.GetCurrentProcess
    get_current_process.argtypes = []
    get_current_process.restype = wintypes.HANDLE

    class FileDispositionInfo(ctypes.Structure):
        _fields_ = [("DeleteFile", wintypes.BOOLEAN)]

    return (
        ctypes,
        create_file,
        close_handle,
        set_file_information,
        duplicate_handle,
        get_current_process,
        FileDispositionInfo,
    )


@contextmanager
def _open_pinned_handle(
    path: Path,
    *,
    desired_access: int,
    share_mode: int,
    directory: bool,
) -> Iterator[tuple[object, tuple[object, ...]]]:
    (
        ctypes,
        create_file,
        close_handle,
        set_file_information,
        duplicate_handle,
        get_current_process,
        disposition_type,
    ) = _win32_api()
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
        yield handle, (
            set_file_information,
            duplicate_handle,
            get_current_process,
            disposition_type,
            ctypes,
            close_handle,
        )
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


def _snapshot_from_open_handle(
    handle: object,
    api: tuple[object, ...],
    *,
    path: Path,
    max_bytes: int,
) -> PinnedFileSnapshot:
    if type(max_bytes) is not int or max_bytes < 0:
        raise ValueError("max_bytes must be a non-negative integer")

    _, duplicate_handle, get_current_process, _, ctypes, close_handle = api
    from ctypes import wintypes
    import msvcrt

    process = get_current_process()
    duplicate = wintypes.HANDLE()
    if not duplicate_handle(
        process,
        handle,
        process,
        ctypes.byref(duplicate),
        0,
        False,
        _DUPLICATE_SAME_ACCESS,
    ):
        code = ctypes.get_last_error()
        raise OSError(code, ctypes.FormatError(code), str(path))

    duplicate_value = duplicate.value
    fd: int | None = None
    try:
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        fd = msvcrt.open_osfhandle(int(duplicate_value), flags)
        duplicate_value = None
        stat = os.fstat(fd)
        if not stat_module.S_ISREG(stat.st_mode):
            return PinnedFileSnapshot(stat=stat, data=None)
        if stat.st_size > max_bytes:
            return PinnedFileSnapshot(stat=stat, data=None)
        os.lseek(fd, 0, os.SEEK_SET)
        data = bytearray()
        while len(data) <= max_bytes:
            chunk = os.read(fd, min(65536, max_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) != stat.st_size:
            return PinnedFileSnapshot(stat=stat, data=None)
        return PinnedFileSnapshot(stat=stat, data=bytes(data))
    finally:
        if fd is not None:
            os.close(fd)
        elif duplicate_value is not None:
            close_handle(duplicate)


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
    max_bytes: int = _DEFAULT_MAX_VERIFY_BYTES,
) -> Iterator[VerifiedDeletePin]:
    """Pin, snapshot and delete one exact file object without reopening its path."""

    root = _infer_workspace_root(path) if workspace_root is None else workspace_root
    with _pin_namespace(root, path), _open_pinned_handle(
        path,
        desired_access=_GENERIC_READ | _DELETE,
        share_mode=_FILE_SHARE_READ,
        directory=False,
    ) as (handle, api):
        set_file_information, _, _, disposition_type, ctypes, _ = api
        snapshot = _snapshot_from_open_handle(
            handle,
            api,
            path=path,
            max_bytes=max_bytes,
        )

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

        yield VerifiedDeletePin(snapshot, mark_delete)
