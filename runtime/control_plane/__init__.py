"""Deterministic verified-procedure Control Plane.

Ordinary ChatGPT remains the general planner.  This package only progresses
explicitly registered procedures through bounded, current-state-verified
transitions.  It does not expose generic code execution or persist private
reasoning.
"""

import copy
import errno
import os
import threading
from contextlib import ExitStack, contextmanager
from pathlib import Path

from .file_artifact_observation import (
    FILE_ARTIFACT_CAPABILITY,
    FileArtifactObservationStream,
)
from .verification import (
    ExpectedEffect,
    FinishGateResult,
    FinishStatus,
    ObservationRef,
    ObservationSnapshot,
    PredicateOperator,
    StatePredicate,
    VerificationResult,
    VerificationStatus,
    evaluate_finish_gate,
    verify_expected_effect,
)

# Stage 26.3C binds stage-create delivery to an in-process proof before the
# procedure module imports its internal create helper by value. On Windows the
# proof owns the newly-created file handle and trusted descendant namespace
# until the staged_verified receipt is durably checkpointed. Hosted non-Windows
# tests keep only an in-process marker and make no Windows pinning claim.
from . import _verified_workspace_artifact_support as _workspace_artifact_support
from . import windows_file_pin as _windows_file_pin


# A Win32 share-mode pin blocks rename/delete replacement but does not make
# reparse metadata immutable: FILE_WRITE_ATTRIBUTES is not governed by the
# sharing flags. The first staging leaf is therefore created relative to the
# already-open, already-checked stage-directory handle instead of resolving the
# parent string path a second time. This is intentionally limited to the first
# staging create; the accepted three-action procedure graph is unchanged.
_FILE_TRAVERSE = 0x00000020
_SYNCHRONIZE = 0x00100000
_FILE_ATTRIBUTE_NORMAL = 0x00000080
_FILE_CREATE = 2
_FILE_NON_DIRECTORY_FILE = 0x00000040
_FILE_SYNCHRONOUS_IO_NONALERT = 0x00000020
_OBJ_CASE_INSENSITIVE = 0x00000040
_STATUS_OBJECT_NAME_COLLISION = -1073741771  # 0xC0000035 as signed NTSTATUS


@contextmanager
def _create_new_pinned_handle_at(parent_handle, path: Path):
    """Create exactly one leaf relative to one retained directory handle."""

    if os.name != "nt":
        raise OSError(errno.ENOTSUP, "handle-relative staging create requires Windows")
    if not isinstance(path, Path):
        raise TypeError("pinned create path must be pathlib.Path")
    leaf = path.name
    if (
        not leaf
        or leaf in {".", ".."}
        or any(character in leaf for character in ("/", "\\", ":", "\x00"))
    ):
        raise ValueError("handle-relative staging create requires one simple leaf name")

    import ctypes
    from ctypes import wintypes

    class UnicodeString(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.USHORT),
            ("MaximumLength", wintypes.USHORT),
            ("Buffer", wintypes.LPWSTR),
        ]

    class ObjectAttributes(ctypes.Structure):
        _fields_ = [
            ("Length", wintypes.ULONG),
            ("RootDirectory", wintypes.HANDLE),
            ("ObjectName", ctypes.POINTER(UnicodeString)),
            ("Attributes", wintypes.ULONG),
            ("SecurityDescriptor", wintypes.LPVOID),
            ("SecurityQualityOfService", wintypes.LPVOID),
        ]

    class IoStatusUnion(ctypes.Union):
        _fields_ = [("Status", wintypes.LONG), ("Pointer", wintypes.LPVOID)]

    class IoStatusBlock(ctypes.Structure):
        _anonymous_ = ("value",)
        _fields_ = [("value", IoStatusUnion), ("Information", ctypes.c_size_t)]

    ntdll = ctypes.WinDLL("ntdll", use_last_error=True)
    nt_create_file = ntdll.NtCreateFile
    nt_create_file.argtypes = [
        ctypes.POINTER(wintypes.HANDLE),
        wintypes.ULONG,
        ctypes.POINTER(ObjectAttributes),
        ctypes.POINTER(IoStatusBlock),
        wintypes.LPVOID,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.ULONG,
        wintypes.LPVOID,
        wintypes.ULONG,
    ]
    nt_create_file.restype = wintypes.LONG

    rtl_nt_status_to_dos_error = ntdll.RtlNtStatusToDosError
    rtl_nt_status_to_dos_error.argtypes = [wintypes.LONG]
    rtl_nt_status_to_dos_error.restype = wintypes.ULONG

    encoded_length = len(leaf.encode("utf-16-le"))
    leaf_buffer = ctypes.create_unicode_buffer(leaf)
    object_name = UnicodeString(
        encoded_length,
        encoded_length + 2,
        ctypes.cast(leaf_buffer, wintypes.LPWSTR),
    )
    attributes = ObjectAttributes(
        ctypes.sizeof(ObjectAttributes),
        parent_handle,
        ctypes.pointer(object_name),
        _OBJ_CASE_INSENSITIVE,
        None,
        None,
    )
    io_status = IoStatusBlock()
    handle = wintypes.HANDLE()
    status = int(
        nt_create_file(
            ctypes.byref(handle),
            _windows_file_pin._GENERIC_READ
            | _windows_file_pin._GENERIC_WRITE
            | _windows_file_pin._DELETE
            | _SYNCHRONIZE,
            ctypes.byref(attributes),
            ctypes.byref(io_status),
            None,
            _FILE_ATTRIBUTE_NORMAL,
            _windows_file_pin._FILE_SHARE_READ,
            _FILE_CREATE,
            _FILE_NON_DIRECTORY_FILE
            | _windows_file_pin._FILE_FLAG_OPEN_REPARSE_POINT
            | _FILE_SYNCHRONOUS_IO_NONALERT,
            None,
            0,
        )
    )
    if status < 0:
        code = int(rtl_nt_status_to_dos_error(status))
        if status == _STATUS_OBJECT_NAME_COLLISION or code in {
            _windows_file_pin._ERROR_FILE_EXISTS,
            _windows_file_pin._ERROR_ALREADY_EXISTS,
        }:
            raise FileExistsError(code, ctypes.FormatError(code), str(path))
        raise OSError(code, ctypes.FormatError(code), str(path))

    (
        api_ctypes,
        _,
        close_handle,
        set_file_information,
        duplicate_handle,
        get_current_process,
        disposition_type,
    ) = _windows_file_pin._win32_api()
    try:
        yield handle, (
            set_file_information,
            duplicate_handle,
            get_current_process,
            disposition_type,
            api_ctypes,
            close_handle,
        )
    finally:
        close_handle(handle)


def _delete_created_handle(handle, path: Path) -> None:
    """Best-effort exact-object compensation before any staging bytes are written."""

    (
        ctypes,
        _,
        _,
        set_file_information,
        _,
        _,
        disposition_type,
    ) = _windows_file_pin._win32_api()
    disposition = disposition_type(True)
    if not set_file_information(
        handle,
        _windows_file_pin._FILE_DISPOSITION_INFO_CLASS,
        ctypes.byref(disposition),
        ctypes.sizeof(disposition),
    ):
        code = ctypes.get_last_error()
        raise OSError(code, ctypes.FormatError(code), str(path))


def _create_file_in_verified_parent(path: Path, data: bytes) -> None:
    """Create staging under the retained verified parent without parent re-resolution."""

    if _windows_file_pin.stage_create_delivery_proof_live():
        raise RuntimeError("another stage-create delivery proof is already live")
    root = _windows_file_pin._infer_workspace_root(path)
    stack = ExitStack()
    created_handle = None
    try:
        pinned_directories = []
        for directory in _windows_file_pin._namespace_components(root, path):
            desired_access = _windows_file_pin._FILE_READ_ATTRIBUTES | _FILE_TRAVERSE
            if directory != root:
                desired_access |= _windows_file_pin._DELETE
            handle, _ = stack.enter_context(
                _windows_file_pin._open_pinned_handle(
                    directory,
                    desired_access=desired_access,
                    share_mode=(
                        _windows_file_pin._FILE_SHARE_READ
                        | _windows_file_pin._FILE_SHARE_WRITE
                    ),
                    directory=True,
                )
            )
            if (
                _windows_file_pin._handle_file_attributes(handle, directory)
                & _windows_file_pin._FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise ValueError("workspace namespace component is a reparse point")
            pinned_directories.append((directory, handle))

        if not pinned_directories or pinned_directories[-1][0] != path.parent:
            raise RuntimeError("verified parent handle was not retained")
        parent_handle = pinned_directories[-1][1]
        created_handle, _ = stack.enter_context(
            _windows_file_pin._create_new_pinned_handle_at(parent_handle, path)
        )

        # The final stage directory was empty before the first leaf. Re-check the
        # retained directory objects immediately after rooted creation and before
        # writing bytes. Once this leaf exists, Windows no longer permits turning
        # that non-empty directory into a directory reparse point.
        for directory, handle in pinned_directories:
            if (
                _windows_file_pin._handle_file_attributes(handle, directory)
                & _windows_file_pin._FILE_ATTRIBUTE_REPARSE_POINT
            ):
                _delete_created_handle(created_handle, path)
                raise ValueError("workspace namespace component changed to a reparse point")

        if (
            _windows_file_pin._handle_file_attributes(created_handle, path)
            & _windows_file_pin._FILE_ATTRIBUTE_REPARSE_POINT
        ):
            _delete_created_handle(created_handle, path)
            raise ValueError("created staging file is a reparse point")

        _windows_file_pin._write_and_flush_handle(created_handle, path, data)
        _windows_file_pin._STAGE_CREATE_LOCAL.proof = (
            _windows_file_pin._StageCreateDeliveryProof(
                path=_windows_file_pin._absolute_lexical(path),
                stack=stack,
            )
        )
    except BaseException:
        stack.close()
        raise


# Keep the helper discoverable for Windows adversarial tests, then make the
# actual package binding use the rooted primitive before the procedure imports
# the support helper by value.
_windows_file_pin._create_new_pinned_handle_at = _create_new_pinned_handle_at
_windows_file_pin.create_file_in_pinned_namespace = _create_file_in_verified_parent

_original_portable_workspace_create = _workspace_artifact_support._exclusive_create_file
if os.name == "nt":
    _workspace_artifact_support._exclusive_create_file = (
        _windows_file_pin.create_file_in_pinned_namespace
    )
else:
    def _portable_workspace_create_with_delivery_proof(path, data):
        if _windows_file_pin.stage_create_delivery_proof_live():
            raise RuntimeError("another stage-create delivery proof is already live")
        _original_portable_workspace_create(path, data)
        _windows_file_pin.mark_portable_stage_create_delivery_proof(path)

    _workspace_artifact_support._exclusive_create_file = (
        _portable_workspace_create_with_delivery_proof
    )

from . import verified_workspace_artifact as _workspace_artifact


# A prepared stage_create has no durable file identity before its transition
# receipt. Fresh post-restart bytes therefore cannot authenticate themselves as
# the object created by the dead process. Only the still-live in-process
# delivery proof may authorize CONFIRMED_APPLIED; a missing staging+target pair
# remains safe to confirm as NOT_APPLIED and retry within the existing budget.
_original_workspace_direct_reconciliation_status = (
    _workspace_artifact._direct_reconciliation_status
)
_original_workspace_reconciliation_predicates = (
    _workspace_artifact._reconciliation_predicates
)
_original_workspace_write_checkpoint = _workspace_artifact._write_checkpoint
_original_workspace_run = _workspace_artifact.run_verified_workspace_artifact
_WORKSPACE_CHECKPOINT_LOCAL = threading.local()


def _bound_workspace_direct_reconciliation_status(
    transition_id,
    snapshot,
    *,
    content_size,
    expected_sha,
    staging_identity,
    target_identity=None,
):
    if (
        transition_id == "stage_create"
        and not _windows_file_pin.stage_create_delivery_proof_live()
    ):
        if (
            _workspace_artifact._is_missing(snapshot, "staging")
            and _workspace_artifact._is_missing(snapshot, "target")
        ):
            return _workspace_artifact.ReconciliationStatus.CONFIRMED_NOT_APPLIED
        return _workspace_artifact.ReconciliationStatus.STILL_UNKNOWN
    return _original_workspace_direct_reconciliation_status(
        transition_id,
        snapshot,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=staging_identity,
        target_identity=target_identity,
    )


def _bound_workspace_reconciliation_predicates(
    transition_id,
    status,
    snapshot,
    *,
    content_size,
    expected_sha,
    staging_identity,
    target_identity,
):
    if (
        transition_id == "stage_create"
        and status is _workspace_artifact.ReconciliationStatus.CONFIRMED_APPLIED
        and not _windows_file_pin.stage_create_delivery_proof_live()
    ):
        return None
    return _original_workspace_reconciliation_predicates(
        transition_id,
        status,
        snapshot,
        content_size=content_size,
        expected_sha=expected_sha,
        staging_identity=staging_identity,
        target_identity=target_identity,
    )


def _restore_last_durable_task_state(task_state):
    last_durable = getattr(_WORKSPACE_CHECKPOINT_LOCAL, "last_durable", None)
    if last_durable is None:
        return False
    task_state.clear()
    task_state.update(copy.deepcopy(last_durable))
    return True


def _write_checkpoint_with_recovery_and_stage_create_proof(state_root, task_state):
    """Never let an exception path overwrite the last resumable prepared state."""

    last_durable = getattr(_WORKSPACE_CHECKPOINT_LOCAL, "last_durable", None)
    preserve = bool(getattr(_WORKSPACE_CHECKPOINT_LOCAL, "preserve", False))
    terminalizing_prepared = (
        last_durable is not None
        and task_state.get("status") == "failed"
        and last_durable.get("status") == "running"
        and isinstance(last_durable.get("prepared_intent"), dict)
    )
    if preserve or terminalizing_prepared:
        _restore_last_durable_task_state(task_state)
        _WORKSPACE_CHECKPOINT_LOCAL.preserve = True

    try:
        _original_workspace_write_checkpoint(state_root, task_state)
    except Exception:
        if _restore_last_durable_task_state(task_state):
            _WORKSPACE_CHECKPOINT_LOCAL.preserve = True
        raise

    _WORKSPACE_CHECKPOINT_LOCAL.last_durable = copy.deepcopy(task_state)
    if (
        _windows_file_pin.stage_create_delivery_proof_live()
        and (
            task_state.get("prepared_intent") is None
            or task_state.get("status") != "running"
        )
    ):
        # Release only after the durable write succeeds. The normal success path
        # therefore keeps the exact created object/namespace pinned through the
        # fresh AFTER, Kernel result, staged_verified receipt and checkpoint.
        _windows_file_pin.release_stage_create_delivery_proof()


def _run_workspace_artifact_with_stage_create_proof_cleanup(*args, **kwargs):
    if getattr(_WORKSPACE_CHECKPOINT_LOCAL, "active", False):
        raise RuntimeError("nested workspace-artifact execution is unsupported")
    _WORKSPACE_CHECKPOINT_LOCAL.active = True
    _WORKSPACE_CHECKPOINT_LOCAL.last_durable = None
    _WORKSPACE_CHECKPOINT_LOCAL.preserve = False
    try:
        return _original_workspace_run(*args, **kwargs)
    finally:
        # A failed checkpoint or a post-effect ordinary exception must leave the
        # last successfully written running+prepared state as the durable truth.
        # The next process then reconciles before any further mutation. The
        # stage-create live proof is process-local and is deliberately discarded
        # at this boundary, so restart cannot adopt current bytes as ownership.
        _windows_file_pin.release_stage_create_delivery_proof()
        _WORKSPACE_CHECKPOINT_LOCAL.last_durable = None
        _WORKSPACE_CHECKPOINT_LOCAL.preserve = False
        _WORKSPACE_CHECKPOINT_LOCAL.active = False


_workspace_artifact._direct_reconciliation_status = (
    _bound_workspace_direct_reconciliation_status
)
_workspace_artifact._reconciliation_predicates = _bound_workspace_reconciliation_predicates
_workspace_artifact._write_checkpoint = _write_checkpoint_with_recovery_and_stage_create_proof
_workspace_artifact.run_verified_workspace_artifact = (
    _run_workspace_artifact_with_stage_create_proof_cleanup
)

PROCEDURE_ID = _workspace_artifact.PROCEDURE_ID
PROCEDURE_VERSION = _workspace_artifact.PROCEDURE_VERSION
run_verified_workspace_artifact = _workspace_artifact.run_verified_workspace_artifact

from .windows_observation import (
    WINDOWS_DESKTOP_CAPABILITY,
    WindowsDesktopObservationStream,
)
from .windows_transition import (
    WINDOWS_DESKTOP_EFFECT_ID,
    build_windows_desktop_effect,
    verify_windows_desktop_transition,
)
from .working_state import (
    AttemptIntent,
    AttemptRecord,
    BudgetKind,
    BudgetState,
    FailureCategory,
    FailureReason,
    GuardDecision,
    GuardStatus,
    LoopGuard,
    LoopGuardPolicy,
    MutatingOutcome,
    ReconciliationRecord,
    ReconciliationStatus,
    StagnationReport,
    WorkingState,
    reconciliation_effect_id,
)

__all__ = [
    "AttemptIntent",
    "AttemptRecord",
    "BudgetKind",
    "BudgetState",
    "ExpectedEffect",
    "FailureCategory",
    "FailureReason",
    "FILE_ARTIFACT_CAPABILITY",
    "FileArtifactObservationStream",
    "FinishGateResult",
    "FinishStatus",
    "GuardDecision",
    "GuardStatus",
    "LoopGuard",
    "LoopGuardPolicy",
    "MutatingOutcome",
    "ObservationRef",
    "ObservationSnapshot",
    "PredicateOperator",
    "PROCEDURE_ID",
    "PROCEDURE_VERSION",
    "ReconciliationRecord",
    "ReconciliationStatus",
    "StagnationReport",
    "StatePredicate",
    "VerificationResult",
    "VerificationStatus",
    "WINDOWS_DESKTOP_CAPABILITY",
    "WINDOWS_DESKTOP_EFFECT_ID",
    "WindowsDesktopObservationStream",
    "WorkingState",
    "build_windows_desktop_effect",
    "evaluate_finish_gate",
    "reconciliation_effect_id",
    "run_verified_workspace_artifact",
    "verify_expected_effect",
    "verify_windows_desktop_transition",
]
