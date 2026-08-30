from __future__ import annotations

import errno
import os
import stat as stat_module
import threading
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator


_GENERIC_READ = 0x80000000
_GENERIC_WRITE = 0x40000000
_DELETE = 0x00010000
_FILE_READ_ATTRIBUTES = 0x00000080
_FILE_SHARE_READ = 0x00000001
_FILE_SHARE_WRITE = 0x00000002
_CREATE_NEW = 1
_OPEN_EXISTING = 3
_ERROR_FILE_EXISTS = 80
_ERROR_ALREADY_EXISTS = 183
_FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
_FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
_FILE_DISPOSITION_INFO_CLASS = 4
_DUPLICATE_SAME_ACCESS = 0x00000002
_RESERVED_PARENT = ".chat-agent-platform"
_RESERVED_STAGE = "stage26-3a"
_DEFAULT_MAX_VERIFY_BYTES = 16384
_STAGE_CREATE_LOCAL = threading.local()


@dataclass(frozen=True)
class PinnedFileSnapshot:
    stat: os.stat_result
    data: bytes | None


@dataclass
class _StageCreateDeliveryProof:
    path: Path | None
    stack: ExitStack | None


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
    flags = _FILE_FLAG_OPEN_REPARSE_POINT
    if directory:
        flags |= _FILE_FLAG_BACKUP_SEMANTICS
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


@contextmanager
def _create_new_pinned_handle(path: Path) -> Iterator[tuple[object, tuple[object, ...]]]:
    """Create one new file and retain the original restrictive Win32 handle."""

    (
        ctypes,
        create_file,
        close_handle,
        set_file_information,
        duplicate_handle,
        get_current_process,
        disposition_type,
    ) = _win32_api()
    handle = create_file(
        str(path),
        _GENERIC_READ | _GENERIC_WRITE,
        _FILE_SHARE_READ,
        None,
        _CREATE_NEW,
        _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        code = ctypes.get_last_error()
        if code in {_ERROR_FILE_EXISTS, _ERROR_ALREADY_EXISTS}:
            raise FileExistsError(code, ctypes.FormatError(code), str(path))
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
        close_handle(handle)


def _write_and_flush_handle(handle: object, path: Path, data: bytes) -> None:
    if os.name != "nt":
        raise OSError(errno.ENOTSUP, "verified Windows file pin requires Windows")
    if not isinstance(data, bytes):
        raise TypeError("pinned create data must be bytes")

    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    write_file = kernel32.WriteFile
    write_file.argtypes = [
        wintypes.HANDLE,
        wintypes.LPCVOID,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
        wintypes.LPVOID,
    ]
    write_file.restype = wintypes.BOOL
    flush_file_buffers = kernel32.FlushFileBuffers
    flush_file_buffers.argtypes = [wintypes.HANDLE]
    flush_file_buffers.restype = wintypes.BOOL

    offset = 0
    while offset < len(data):
        chunk = data[offset : offset + 65536]
        buffer = ctypes.create_string_buffer(chunk, len(chunk))
        written = wintypes.DWORD()
        if not write_file(
            handle,
            buffer,
            len(chunk),
            ctypes.byref(written),
            None,
        ):
            code = ctypes.get_last_error()
            raise OSError(code, ctypes.FormatError(code), str(path))
        if written.value <= 0:
            raise OSError(errno.EIO, "zero-byte Win32 write", str(path))
        offset += int(written.value)

    if not flush_file_buffers(handle):
        code = ctypes.get_last_error()
        raise OSError(code, ctypes.FormatError(code), str(path))


def _handle_file_attributes(handle: object, path: Path) -> int:
    if os.name != "nt":
        raise OSError(errno.ENOTSUP, "verified Windows file pin requires Windows")

    import ctypes
    from ctypes import wintypes

    class ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    get_file_information = kernel32.GetFileInformationByHandle
    get_file_information.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(ByHandleFileInformation),
    ]
    get_file_information.restype = wintypes.BOOL

    info = ByHandleFileInformation()
    if not get_file_information(handle, ctypes.byref(info)):
        code = ctypes.get_last_error()
        raise OSError(code, ctypes.FormatError(code), str(path))
    return int(info.dwFileAttributes)


def _absolute_lexical(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("pinned path must be pathlib.Path")
    return Path(os.path.abspath(os.fspath(path)))


def _infer_workspace_root(path: Path) -> Path:
    absolute = _absolute_lexical(path)
    if (
        absolute.parent.name != _RESERVED_STAGE
        or absolute.parent.parent.name != _RESERVED_PARENT
    ):
        raise ValueError("pinned path is outside the verified workspace artifact layout")
    return absolute.parent.parent.parent


def _namespace_components(workspace_root: Path, path: Path) -> tuple[Path, ...]:
    if not isinstance(workspace_root, Path) or not isinstance(path, Path):
        raise TypeError("workspace_root and pinned path must be pathlib.Path")
    root = _absolute_lexical(workspace_root)
    absolute = _absolute_lexical(path)
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
    root = _absolute_lexical(workspace_root)
    with ExitStack() as stack:
        for directory in _namespace_components(root, path):
            # The configured workspace root itself is a capability boundary and
            # is not claimed against external relocation here. Descendant
            # namespace components are opened with DELETE access while refusing
            # FILE_SHARE_DELETE, so another actor cannot rename/delete/repoint
            # them during a consequence-bearing path resolution window.
            desired_access = _FILE_READ_ATTRIBUTES
            if directory != root:
                desired_access |= _DELETE
            handle, _ = stack.enter_context(
                _open_pinned_handle(
                    directory,
                    desired_access=desired_access,
                    share_mode=_FILE_SHARE_READ | _FILE_SHARE_WRITE,
                    directory=True,
                )
            )
            if _handle_file_attributes(handle, directory) & _FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError("workspace namespace component is a reparse point")
        yield


def stage_create_delivery_proof_live() -> bool:
    """Return whether this thread still owns a pre-receipt stage-create proof."""

    return getattr(_STAGE_CREATE_LOCAL, "proof", None) is not None


def mark_portable_stage_create_delivery_proof(path: Path) -> None:
    """Mark non-Windows hosted delivery as in-process only; it carries no OS pin claim."""

    if stage_create_delivery_proof_live():
        raise RuntimeError("another stage-create delivery proof is already live")
    _STAGE_CREATE_LOCAL.proof = _StageCreateDeliveryProof(
        path=_absolute_lexical(path),
        stack=None,
    )


def release_stage_create_delivery_proof() -> None:
    proof = getattr(_STAGE_CREATE_LOCAL, "proof", None)
    if proof is None:
        return
    _STAGE_CREATE_LOCAL.proof = None
    if proof.stack is not None:
        proof.stack.close()


def create_file_in_pinned_namespace(path: Path, data: bytes) -> None:
    """Create staging and retain its exact object/namespace pin until receipt commit."""

    # Infer only from the lexical staging path that the procedure already built
    # under its configured workspace root. Do not call Path.resolve() here:
    # following a raced junction while reconstructing trust would let an
    # attacker redefine the capability root before the first physical effect.
    if stage_create_delivery_proof_live():
        raise RuntimeError("another stage-create delivery proof is already live")
    root = _infer_workspace_root(path)
    stack = ExitStack()
    try:
        stack.enter_context(_pin_namespace(root, path))
        handle, _ = stack.enter_context(_create_new_pinned_handle(path))
        if _handle_file_attributes(handle, path) & _FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("created staging file is a reparse point")
        _write_and_flush_handle(handle, path, data)
        _STAGE_CREATE_LOCAL.proof = _StageCreateDeliveryProof(
            path=_absolute_lexical(path),
            stack=stack,
        )
    except BaseException:
        stack.close()
        raise


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


def _same_snapshot(left: PinnedFileSnapshot, right: PinnedFileSnapshot) -> bool:
    if left.data is None or right.data is None or left.data != right.data:
        return False
    for name in ("st_dev", "st_ino", "st_size"):
        if getattr(left.stat, name) != getattr(right.stat, name):
            return False
    left_birth = getattr(left.stat, "st_birthtime_ns", None)
    right_birth = getattr(right.stat, "st_birthtime_ns", None)
    return type(left_birth) is int and left_birth == right_birth


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
    """Pin verified state, then revalidate the exact object before handle deletion."""

    root = _infer_workspace_root(path) if workspace_root is None else workspace_root
    with _pin_namespace(root, path):
        read_context = _open_pinned_handle(
            path,
            desired_access=_GENERIC_READ,
            share_mode=_FILE_SHARE_READ,
            directory=False,
        )
        read_handle, read_api = read_context.__enter__()
        read_open = True
        try:
            entry_snapshot = _snapshot_from_open_handle(
                read_handle,
                read_api,
                path=path,
                max_bytes=max_bytes,
            )
            delivered = False

            def mark_delete() -> None:
                nonlocal read_open, delivered
                if delivered:
                    raise RuntimeError("verified delete delivery may run only once")
                if read_open:
                    read_context.__exit__(None, None, None)
                    read_open = False

                with _open_pinned_handle(
                    path,
                    desired_access=_GENERIC_READ | _DELETE,
                    share_mode=_FILE_SHARE_READ,
                    directory=False,
                ) as (delete_handle, delete_api):
                    delivery_snapshot = _snapshot_from_open_handle(
                        delete_handle,
                        delete_api,
                        path=path,
                        max_bytes=max_bytes,
                    )
                    if not _same_snapshot(entry_snapshot, delivery_snapshot):
                        raise RuntimeError(
                            "verified file changed before handle-bound delete delivery"
                        )
                    set_file_information, _, _, disposition_type, ctypes, _ = delete_api
                    disposition = disposition_type(True)
                    if not set_file_information(
                        delete_handle,
                        _FILE_DISPOSITION_INFO_CLASS,
                        ctypes.byref(disposition),
                        ctypes.sizeof(disposition),
                    ):
                        code = ctypes.get_last_error()
                        raise OSError(code, ctypes.FormatError(code), str(path))
                    delivered = True

            yield VerifiedDeletePin(entry_snapshot, mark_delete)
        finally:
            if read_open:
                read_context.__exit__(None, None, None)
