from __future__ import annotations

import errno
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


_GENERIC_READ = 0x80000000
_FILE_SHARE_READ = 0x00000001
_OPEN_EXISTING = 3
_FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000


@contextmanager
def pin_file_for_verified_link(path: Path) -> Iterator[None]:
    """Keep one Windows file object non-replaceable during verified hard-link delivery.

    The procedure verifies the durable file identity again while this handle is
    live.  Sharing permits additional readers but denies write/delete access, so
    another process cannot replace, rename, delete or open the pinned source for
    writing until the link attempt has finished.
    """

    if not isinstance(path, Path):
        raise TypeError("pinned file path must be pathlib.Path")
    if os.name != "nt":
        raise OSError(errno.ENOTSUP, "verified hard-link source pin requires Windows")

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

    handle = create_file(
        str(path),
        _GENERIC_READ,
        _FILE_SHARE_READ,
        None,
        _OPEN_EXISTING,
        _FILE_FLAG_OPEN_REPARSE_POINT,
        None,
    )
    invalid_handle = ctypes.c_void_p(-1).value
    if handle == invalid_handle:
        code = ctypes.get_last_error()
        raise OSError(code, ctypes.FormatError(code), str(path))

    try:
        yield
    finally:
        if not close_handle(handle):
            code = ctypes.get_last_error()
            raise OSError(code, ctypes.FormatError(code), str(path))
