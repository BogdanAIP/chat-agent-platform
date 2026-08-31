from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from ._verified_workspace_artifact_support import _acquire_task_lock, _safe_child


STATE_SCHEMA_VERSION = 1
GENESIS_KIND = "independent-review-genesis"
STATE_KIND = "independent-review-state"
STATE_DIRECTORY = "independent-review-v1"
REVIEW_SKILL = "code-review"
REVIEW_CONTEXT = "ordinary_chat_fresh"
MAX_RESULT_BYTES = 256_000
MAX_GENESIS_BYTES = 16_384
# json.dumps(..., ensure_ascii=False) can expand a one-byte ASCII control
# character into a six-byte \u00XX escape. The review result dominates the
# mutable checkpoint size, so six times the accepted raw result bound plus a
# generous fixed envelope safely covers the serializer's worst-case expansion
# while keeping corrupted/untrusted persisted state bounded on load.
MAX_STATE_BYTES = MAX_RESULT_BYTES * 6 + 65_536
MAX_REJECTED_CANDIDATES = 100_000
MAX_REPORTED_FINDINGS = 10_000

_REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SKILL_VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_REVIEW_RUN_ID_RE = re.compile(r"^[0-9a-f]{64}$")
_HEADER_LINE_RE = re.compile(r"^([a-z_]+)=(.*)$")
_FINDING_HEADING_RE = re.compile(
    r"^(?:#{1,6}\s*)?FINDING\s+#?([1-9][0-9]*)\s*:?\s*$",
    re.IGNORECASE,
)
_FINDING_FIELD_RE = re.compile(
    r"^(severity|location|introduced_by|failure_mechanism|consequence|supporting_evidence|"
    r"falsification_attempt|why_it_survives)\s*=\s*(.*)$"
)
_ALLOWED_STATUS = {"PASS", "FINDINGS", "ABSTAIN", "STALE"}
_ALLOWED_VALIDITY = {"CURRENT", "STALE_BASE_CHANGE", "STALE_MATERIAL_CHANGE"}
_COMPLETING_STATUS = {"PASS", "FINDINGS"}
_REQUIRED_FINDING_FIELDS = (
    "severity",
    "location",
    "introduced_by",
    "failure_mechanism",
    "consequence",
    "supporting_evidence",
    "falsification_attempt",
    "why_it_survives",
)
_SEVERITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

_IDENTITY_KEYS = (
    "repository",
    "pr_number",
    "base_sha",
    "head_sha",
    "review_skill",
    "review_skill_version",
)
_RESULT_HEADER_KEYS = {
    "repository",
    "pr_number",
    "base_sha",
    "head_sha",
    "review_policy_ref",
    "review_skill",
    "review_skill_version",
    "review_context",
    "status",
    "review_validity",
    "reported_findings",
    "rejected_candidates",
    "reviewed_at",
}


@dataclass(frozen=True)
class ReviewIdentity:
    repository: str
    pr_number: int
    base_sha: str
    head_sha: str
    review_skill: str
    review_skill_version: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "repository": self.repository,
            "pr_number": self.pr_number,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "review_skill": self.review_skill,
            "review_skill_version": self.review_skill_version,
        }


@dataclass(frozen=True)
class PreparedReviewOperation:
    """Trusted-Control-Plane view; never return this object directly to Chat."""

    identity: ReviewIdentity
    operation_key: str
    review_run_id: str = field(repr=False)
    dispatch_state: str = "prepared"
    result_state: str = "open"
    created: bool = False


@dataclass(frozen=True)
class ParsedReviewResult:
    payload: str
    header: Mapping[str, Any]
    body_sha256: str


class ReviewStateError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ReviewStateError(
            f"{label} keys mismatch: missing={missing or 'none'} unexpected={unexpected or 'none'}"
        )


def _parse_positive_int(value: Any, label: str, *, maximum: int) -> int:
    if type(value) is not int or value < 1 or value > maximum:
        raise ReviewStateError(f"{label} must be a positive bounded integer")
    return value


def _parse_positive_int_from_header(value: str, label: str) -> int:
    if not value or not value.isascii() or not value.isdigit():
        raise ReviewStateError(f"{label} must be a positive integer")
    return _parse_positive_int(int(value), label, maximum=2_147_483_647)


def _parse_nonnegative_int(value: str, label: str, *, maximum: int) -> int:
    if not value or not value.isascii() or not value.isdigit():
        raise ReviewStateError(f"{label} must be a non-negative integer")
    parsed = int(value)
    if parsed > maximum:
        raise ReviewStateError(f"{label} exceeds the accepted bound")
    return parsed


def _parse_timestamp(value: Any, label: str) -> str:
    if type(value) is not str or not value or len(value) > 128:
        raise ReviewStateError(f"{label} must be a bounded ISO-8601 timestamp")
    candidate = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ReviewStateError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ReviewStateError(f"{label} must include a timezone")
    return value


def parse_review_identity(value: Mapping[str, Any], *, exact_keys: bool = True) -> ReviewIdentity:
    if type(value) is not dict:
        raise ReviewStateError("review identity must be a plain object")
    if exact_keys:
        _require_exact_keys(value, set(_IDENTITY_KEYS), "review identity")
    else:
        missing = set(_IDENTITY_KEYS) - set(value)
        if missing:
            raise ReviewStateError(f"review identity is missing required keys: {sorted(missing)}")

    repository = value.get("repository")
    if type(repository) is not str or _REPOSITORY_RE.fullmatch(repository) is None:
        raise ReviewStateError("repository must be a bounded owner/repository identifier")
    owner, name = repository.split("/", 1)
    if owner in {".", ".."} or name in {".", ".."}:
        raise ReviewStateError("repository contains an invalid path segment")
    repository = repository.lower()

    pr_number = _parse_positive_int(value.get("pr_number"), "pr_number", maximum=2_147_483_647)

    base_sha = value.get("base_sha")
    head_sha = value.get("head_sha")
    if type(base_sha) is not str or _SHA_RE.fullmatch(base_sha) is None:
        raise ReviewStateError("base_sha must be a 40-character lowercase hex SHA")
    if type(head_sha) is not str or _SHA_RE.fullmatch(head_sha) is None:
        raise ReviewStateError("head_sha must be a 40-character lowercase hex SHA")
    if base_sha == head_sha:
        raise ReviewStateError("base_sha and head_sha must be distinct")

    review_skill = value.get("review_skill")
    if review_skill != REVIEW_SKILL:
        raise ReviewStateError(f"review_skill must be {REVIEW_SKILL}")
    review_skill_version = value.get("review_skill_version")
    if type(review_skill_version) is not str or _SKILL_VERSION_RE.fullmatch(review_skill_version) is None:
        raise ReviewStateError("review_skill_version must be a canonical major.minor version")

    return ReviewIdentity(
        repository=repository,
        pr_number=pr_number,
        base_sha=base_sha,
        head_sha=head_sha,
        review_skill=review_skill,
        review_skill_version=review_skill_version,
    )


def review_operation_key(identity: ReviewIdentity) -> str:
    canonical = json.dumps(identity.as_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(("cap-independent-review-v1\0" + canonical).encode("ascii")).hexdigest()


def _lock_id(operation_key: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{64}", operation_key):
        raise ReviewStateError("invalid independent-review operation key")
    # The accepted Stage 26.3C lock helper uses a 32-hex namespace. State files
    # remain bound to the complete 256-bit operation key, so a lock-prefix
    # collision can only serialize unrelated operations; it cannot mix state.
    return operation_key[:32]


def _review_root(state_root: Path) -> Path:
    configured = state_root.resolve()
    root = _safe_child(configured, configured / STATE_DIRECTORY)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _genesis_path(root: Path, operation_key: str) -> Path:
    return _safe_child(root, root / f"{operation_key}.genesis.json")


def _state_path(root: Path, operation_key: str) -> Path:
    return _safe_child(root, root / f"{operation_key}.state.json")


def _state_temp_paths(root: Path, operation_key: str) -> tuple[Path, ...]:
    prefix = f".{operation_key}.state."
    values: list[Path] = []
    for candidate in root.iterdir():
        name = candidate.name
        if name.startswith(prefix) and name.endswith(".tmp"):
            values.append(candidate)
    return tuple(sorted(values, key=lambda path: path.name))


def _encode_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _exclusive_create_file(path: Path, data: bytes) -> None:
    """Accepted Stage 26.3C exclusive-create/fsync mechanic for private state.

    Do not import the workspace-artifact helper by value here: on Windows the
    package intentionally replaces that symbol with a workspace-namespace
    pinned consequence primitive. Independent-review metadata lives under the
    private procedure state root, not under the workspace artifact layout.
    """

    if len(data) > MAX_GENESIS_BYTES:
        raise ReviewStateError("independent-review genesis exceeds the accepted encoded bound")
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _load_json_object(
    path: Path,
    label: str,
    *,
    maximum_bytes: int,
) -> dict[str, Any]:
    try:
        with path.open("rb") as handle:
            raw = handle.read(maximum_bytes + 1)
    except FileNotFoundError as exc:
        raise ReviewStateError(f"{label} does not exist") from exc
    if len(raw) > maximum_bytes:
        raise ReviewStateError(f"{label} exceeds the accepted encoded bound")
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ReviewStateError(f"{label} is invalid") from exc
    if type(value) is not dict:
        raise ReviewStateError(f"{label} must be a plain object")
    return value


def _write_state_checkpoint(root: Path, operation_key: str, state: Mapping[str, Any]) -> None:
    """Accepted sibling-temp + flush/fsync + replace process-crash mechanic."""

    destination = _state_path(root, operation_key)
    temporary = _safe_child(root, root / f".{operation_key}.state.{secrets.token_hex(8)}.tmp")
    payload = _encode_json(state)
    if len(payload) > MAX_STATE_BYTES:
        raise ReviewStateError("independent-review state exceeds the accepted encoded bound")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _build_genesis(identity: ReviewIdentity, operation_key: str, review_run_id: str) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "kind": GENESIS_KIND,
        "operation_key": operation_key,
        "identity": identity.as_dict(),
        "review_run_id": review_run_id,
        "created_at": _utc_now(),
    }


def _build_initial_state(identity: ReviewIdentity, operation_key: str, review_run_id: str) -> dict[str, Any]:
    now = _utc_now()
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "kind": STATE_KIND,
        "operation_key": operation_key,
        "identity": identity.as_dict(),
        "review_run_id": review_run_id,
        "revision": 1,
        "dispatch_state": "prepared",
        "result_state": "open",
        "result_source": None,
        "result_body_sha256": None,
        "result_payload": None,
        "result_recorded_at": None,
        "recovery_reason": None,
        "created_at": now,
        "updated_at": now,
    }


def _validate_review_run_id(value: Any) -> str:
    if type(value) is not str or _REVIEW_RUN_ID_RE.fullmatch(value) is None:
        raise ReviewStateError("review_run_id must be a 64-character lowercase hex capability")
    return value


def _validate_genesis(value: Mapping[str, Any], identity: ReviewIdentity, operation_key: str) -> str:
    expected_keys = {
        "schema_version",
        "kind",
        "operation_key",
        "identity",
        "review_run_id",
        "created_at",
    }
    _require_exact_keys(value, expected_keys, "independent-review genesis")
    if value["schema_version"] != STATE_SCHEMA_VERSION or value["kind"] != GENESIS_KIND:
        raise ReviewStateError("independent-review genesis schema mismatch")
    if value["operation_key"] != operation_key:
        raise ReviewStateError("independent-review genesis operation key mismatch")
    if parse_review_identity(value["identity"], exact_keys=True) != identity:
        raise ReviewStateError("independent-review genesis identity mismatch")
    review_run_id = _validate_review_run_id(value["review_run_id"])
    _parse_timestamp(value["created_at"], "genesis.created_at")
    return review_run_id


def _finding_field_marker(line: str) -> tuple[str, str] | None:
    normalized = line.strip().replace("**", "").replace("__", "").replace("`", "")
    match = _FINDING_FIELD_RE.fullmatch(normalized)
    if match is None:
        return None
    return match.group(1), match.group(2).strip()


def _finding_heading_number(line: str) -> int | None:
    normalized = line.strip().replace("**", "").replace("__", "").replace("`", "")
    match = _FINDING_HEADING_RE.fullmatch(normalized)
    if match is None:
        return None
    return int(match.group(1))


def _markdown_schema_visibility(lines: list[str]) -> list[bool]:
    """Mark schema-eligible lines, excluding fenced Markdown code blocks."""

    visible: list[bool] = []
    fence_char: str | None = None
    fence_length = 0
    for line in lines:
        leading_spaces = len(line) - len(line.lstrip(" "))
        stripped = line.lstrip(" ") if leading_spaces <= 3 else line

        if fence_char is None:
            if leading_spaces <= 3:
                match = re.match(r"^(`{3,}|~{3,})(.*)$", stripped)
                if match is not None:
                    token = match.group(1)
                    fence_char = token[0]
                    fence_length = len(token)
                    visible.append(False)
                    continue
            visible.append(True)
            continue

        visible.append(False)
        if leading_spaces <= 3 and re.fullmatch(
            rf"{re.escape(fence_char)}{{{fence_length},}}\s*",
            stripped,
        ) is not None:
            fence_char = None
            fence_length = 0
    return visible


def _substantive_inline_finding_value(value: str) -> str:
    cleaned = value.replace("**", "").replace("__", "").replace("`", "").strip()
    if not cleaned or not any(character.isalnum() for character in cleaned):
        return ""
    return cleaned


def _finding_blocks(payload: str, reported_findings: int) -> list[tuple[int, list[str]]]:
    lines = payload.splitlines()
    visibility = _markdown_schema_visibility(lines)
    headings: list[tuple[int, int]] = []
    for index, line in enumerate(lines):
        if not visibility[index]:
            continue
        number = _finding_heading_number(line)
        if number is not None:
            headings.append((index, number))

    if headings:
        if len(headings) != reported_findings:
            raise ReviewStateError("review result finding body count does not match reported_findings")
        numbers = [number for _, number in headings]
        if numbers != list(range(1, reported_findings + 1)):
            raise ReviewStateError("review result findings must be numbered sequentially from 1")
        blocks: list[tuple[int, list[str]]] = []
        for heading_index, (start, number) in enumerate(headings):
            end = headings[heading_index + 1][0] if heading_index + 1 < len(headings) else len(lines)
            blocks.append((number, lines[start + 1 : end]))
        return blocks

    severity_positions: list[int] = []
    for index, line in enumerate(lines):
        if not visibility[index]:
            continue
        marker = _finding_field_marker(line)
        if marker is not None and marker[0] == "severity":
            severity_positions.append(index)

    if len(severity_positions) != reported_findings:
        raise ReviewStateError("review result finding body count does not match reported_findings")
    blocks = []
    for index, start in enumerate(severity_positions):
        end = severity_positions[index + 1] if index + 1 < len(severity_positions) else len(lines)
        blocks.append((index + 1, lines[start:end]))
    return blocks


def _validate_finding_bodies(payload: str, reported_findings: int) -> None:
    blocks = _finding_blocks(payload, reported_findings)
    if reported_findings == 0:
        return

    severity_ranks: list[int] = []
    for number, block in blocks:
        visibility = _markdown_schema_visibility(block)
        markers: dict[str, str] = {}
        for block_index, line in enumerate(block):
            if not visibility[block_index]:
                continue
            marker = _finding_field_marker(line)
            if marker is None:
                continue
            field_name, inline_value = marker
            if field_name in markers:
                raise ReviewStateError(f"finding {number} duplicates required field {field_name}")
            markers[field_name] = inline_value

        missing = [field_name for field_name in _REQUIRED_FINDING_FIELDS if field_name not in markers]
        if missing:
            raise ReviewStateError(f"finding {number} is missing required fields: {missing}")

        field_text: dict[str, str] = {}
        for field_name in _REQUIRED_FINDING_FIELDS:
            text = _substantive_inline_finding_value(markers[field_name])
            if not text:
                raise ReviewStateError(
                    f"finding {number} field {field_name} must have substantive inline content"
                )
            field_text[field_name] = text

        severity = field_text["severity"].strip()
        if severity not in _SEVERITY_ORDER:
            raise ReviewStateError(f"finding {number} severity must be P0, P1, P2, or P3")
        severity_ranks.append(_SEVERITY_ORDER[severity])

    if severity_ranks != sorted(severity_ranks):
        raise ReviewStateError("review result findings must be listed in severity order")


def _require_completing_review_result(parsed: ParsedReviewResult, *, label: str) -> None:
    status = parsed.header["status"]
    validity = parsed.header["review_validity"]
    if status not in _COMPLETING_STATUS or validity != "CURRENT":
        raise ReviewStateError(
            f"{label} is non-completing ({status}); fresh manual review remains required"
        )


def _validate_state(
    value: Mapping[str, Any],
    identity: ReviewIdentity,
    operation_key: str,
    review_run_id: str,
) -> None:
    expected_keys = {
        "schema_version",
        "kind",
        "operation_key",
        "identity",
        "review_run_id",
        "revision",
        "dispatch_state",
        "result_state",
        "result_source",
        "result_body_sha256",
        "result_payload",
        "result_recorded_at",
        "recovery_reason",
        "created_at",
        "updated_at",
    }
    _require_exact_keys(value, expected_keys, "independent-review state")
    if value["schema_version"] != STATE_SCHEMA_VERSION or value["kind"] != STATE_KIND:
        raise ReviewStateError("independent-review state schema mismatch")
    if value["operation_key"] != operation_key:
        raise ReviewStateError("independent-review state operation key mismatch")
    if parse_review_identity(value["identity"], exact_keys=True) != identity:
        raise ReviewStateError("independent-review state identity mismatch")
    if _validate_review_run_id(value["review_run_id"]) != review_run_id:
        raise ReviewStateError("independent-review state nonce mismatch")
    if type(value["revision"]) is not int or value["revision"] < 1:
        raise ReviewStateError("independent-review state revision is invalid")

    dispatch_state = value["dispatch_state"]
    result_state = value["result_state"]
    if dispatch_state not in {"prepared", "dispatch-attempted", "automation-abandoned"}:
        raise ReviewStateError("independent-review dispatch state is invalid")
    if result_state not in {"open", "automatic-result-recorded", "manual-fallback-recorded"}:
        raise ReviewStateError("independent-review result state is invalid")

    _parse_timestamp(value["created_at"], "state.created_at")
    _parse_timestamp(value["updated_at"], "state.updated_at")

    if result_state == "open":
        if value["result_source"] is not None:
            raise ReviewStateError("open review state cannot have a result source")
        if any(value[key] is not None for key in ("result_body_sha256", "result_payload", "result_recorded_at")):
            raise ReviewStateError("open review state cannot contain result evidence")
        if dispatch_state == "automation-abandoned":
            raise ReviewStateError("abandoned automation must be terminal")
        if value["recovery_reason"] is not None:
            raise ReviewStateError("open review state cannot contain a recovery reason")
        return

    expected_source = "automatic" if result_state == "automatic-result-recorded" else "manual"
    if value["result_source"] != expected_source:
        raise ReviewStateError("recorded review result source is inconsistent")
    digest = value["result_body_sha256"]
    payload = value["result_payload"]
    if type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ReviewStateError("recorded review result digest is invalid")
    if type(payload) is not str or not payload:
        raise ReviewStateError("recorded review result payload is invalid")
    if hashlib.sha256(payload.encode("utf-8")).hexdigest() != digest:
        raise ReviewStateError("recorded review result digest mismatch")
    _parse_timestamp(value["result_recorded_at"], "state.result_recorded_at")

    parsed = parse_review_result(
        payload,
        expected_identity=identity,
        automatic=result_state == "automatic-result-recorded",
        expected_review_run_id=review_run_id if result_state == "automatic-result-recorded" else None,
    )
    _require_completing_review_result(parsed, label="recorded review result")
    if parsed.body_sha256 != digest:
        raise ReviewStateError("recorded review result validation digest mismatch")

    if dispatch_state == "automation-abandoned":
        if result_state != "manual-fallback-recorded":
            raise ReviewStateError("abandoned automation requires manual fallback")
        if value["recovery_reason"] != "state-missing-after-genesis":
            raise ReviewStateError("abandoned automation recovery reason is invalid")
    elif value["recovery_reason"] is not None:
        raise ReviewStateError("ordinary recorded result cannot contain a recovery reason")

    if result_state == "automatic-result-recorded" and dispatch_state != "dispatch-attempted":
        raise ReviewStateError("automatic result requires dispatch-attempted state")


def _load_genesis(root: Path, identity: ReviewIdentity, operation_key: str) -> tuple[dict[str, Any], str]:
    value = _load_json_object(
        _genesis_path(root, operation_key),
        "independent-review genesis",
        maximum_bytes=MAX_GENESIS_BYTES,
    )
    return value, _validate_genesis(value, identity, operation_key)


def _load_state(
    root: Path,
    identity: ReviewIdentity,
    operation_key: str,
    review_run_id: str,
) -> dict[str, Any]:
    value = _load_json_object(
        _state_path(root, operation_key),
        "independent-review state",
        maximum_bytes=MAX_STATE_BYTES,
    )
    _validate_state(value, identity, operation_key, review_run_id)
    return value


def _paths_present(root: Path, operation_key: str) -> tuple[bool, bool, tuple[Path, ...]]:
    return (
        _genesis_path(root, operation_key).exists(),
        _state_path(root, operation_key).exists(),
        _state_temp_paths(root, operation_key),
    )


def prepare_review_operation(identity_value: Mapping[str, Any], *, state_root: Path) -> PreparedReviewOperation:
    """Create/load the private operation. Trusted Control Plane only; contains nonce."""

    identity = parse_review_identity(identity_value, exact_keys=True)
    operation_key = review_operation_key(identity)
    root = _review_root(state_root)
    with _acquire_task_lock(root, _lock_id(operation_key)):
        genesis_exists, state_exists, temp_paths = _paths_present(root, operation_key)
        if not genesis_exists and not state_exists:
            if temp_paths:
                raise ReviewStateError("independent-review residue exists without canonical operation state")
            review_run_id = secrets.token_hex(32)
            genesis = _build_genesis(identity, operation_key, review_run_id)
            _exclusive_create_file(_genesis_path(root, operation_key), _encode_json(genesis))
            _, persisted_run_id = _load_genesis(root, identity, operation_key)
            if persisted_run_id != review_run_id:
                raise ReviewStateError("new independent-review genesis nonce changed after persistence")
            _write_state_checkpoint(
                root,
                operation_key,
                _build_initial_state(identity, operation_key, review_run_id),
            )
            state = _load_state(root, identity, operation_key, review_run_id)
            return PreparedReviewOperation(
                identity=identity,
                operation_key=operation_key,
                review_run_id=review_run_id,
                dispatch_state=state["dispatch_state"],
                result_state=state["result_state"],
                created=True,
            )

        if not genesis_exists:
            raise ReviewStateError("independent-review state exists without immutable genesis")
        _, review_run_id = _load_genesis(root, identity, operation_key)
        if not state_exists:
            raise ReviewStateError("manual_recovery_required")
        state = _load_state(root, identity, operation_key, review_run_id)
        return PreparedReviewOperation(
            identity=identity,
            operation_key=operation_key,
            review_run_id=review_run_id,
            dispatch_state=state["dispatch_state"],
            result_state=state["result_state"],
            created=False,
        )


def mark_dispatch_attempted(identity_value: Mapping[str, Any], *, state_root: Path) -> dict[str, Any]:
    identity = parse_review_identity(identity_value, exact_keys=True)
    operation_key = review_operation_key(identity)
    root = _review_root(state_root)
    with _acquire_task_lock(root, _lock_id(operation_key)):
        _, review_run_id = _load_genesis(root, identity, operation_key)
        state = _load_state(root, identity, operation_key, review_run_id)
        if state["result_state"] != "open":
            raise ReviewStateError("independent-review result slot is already closed")
        if state["dispatch_state"] != "prepared":
            raise ReviewStateError("independent-review dispatch was already attempted or abandoned")
        updated = dict(state)
        updated["revision"] += 1
        updated["dispatch_state"] = "dispatch-attempted"
        updated["updated_at"] = _utc_now()
        _write_state_checkpoint(root, operation_key, updated)
        persisted = _load_state(root, identity, operation_key, review_run_id)
        return _public_state_summary(persisted, include_result=False)


def _result_header(payload: str, *, automatic: bool) -> dict[str, str]:
    if type(payload) is not str or not payload.strip():
        raise ReviewStateError("review result must be non-empty text")
    if len(payload.encode("utf-8")) > MAX_RESULT_BYTES:
        raise ReviewStateError("review result exceeds the accepted bound")

    lines = payload.splitlines()
    cursor = 0
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1

    outer_fence: tuple[str, int] | None = None
    if cursor < len(lines):
        fence_match = re.fullmatch(
            r"(`{3,}|~{3,})(?:text|plaintext)?\s*",
            lines[cursor].strip(),
            re.IGNORECASE,
        )
        if fence_match is not None:
            token = fence_match.group(1)
            outer_fence = (token[0], len(token))
            cursor += 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1

    if cursor >= len(lines) or lines[cursor].strip() != "REVIEW_RESULT_V1":
        raise ReviewStateError("review result must begin with REVIEW_RESULT_V1")
    marker_index = cursor

    required = set(_RESULT_HEADER_KEYS)
    allowed = set(required)
    if automatic:
        required.add("review_run_id")
        allowed.add("review_run_id")

    header: dict[str, str] = {}
    started = False
    for line in lines[marker_index + 1 :]:
        stripped = line.strip()
        if outer_fence is not None:
            fence_char, fence_length = outer_fence
            if re.fullmatch(
                rf"{re.escape(fence_char)}{{{fence_length},}}\s*",
                stripped,
            ) is not None:
                if started and required.issubset(header):
                    break
                raise ReviewStateError("review result header fence closed before completion")
        if not stripped:
            if started and required.issubset(header):
                break
            continue
        match = _HEADER_LINE_RE.fullmatch(stripped)
        if match is None:
            if started:
                break
            raise ReviewStateError("review result header is malformed")
        started = True
        key, raw_value = match.groups()
        if key in header:
            raise ReviewStateError(f"review result header duplicates {key}")
        if key not in allowed:
            raise ReviewStateError(f"review result header contains unsupported field {key}")
        header[key] = raw_value

    if set(header) != required:
        raise ReviewStateError(
            f"review result header fields mismatch: missing={sorted(required - set(header)) or 'none'} "
            f"unexpected={sorted(set(header) - required) or 'none'}"
        )
    return header


def _identity_from_result_header(header: Mapping[str, str]) -> ReviewIdentity:
    return parse_review_identity(
        {
            "repository": header["repository"],
            "pr_number": _parse_positive_int_from_header(header["pr_number"], "pr_number"),
            "base_sha": header["base_sha"],
            "head_sha": header["head_sha"],
            "review_skill": header["review_skill"],
            "review_skill_version": header["review_skill_version"],
        },
        exact_keys=True,
    )


def parse_review_result(
    payload: str,
    *,
    expected_identity: ReviewIdentity,
    automatic: bool,
    expected_review_run_id: str | None = None,
) -> ParsedReviewResult:
    header = _result_header(payload, automatic=automatic)
    result_identity = _identity_from_result_header(header)
    if result_identity != expected_identity:
        raise ReviewStateError("review result identity does not match the durable operation")
    if header["review_policy_ref"] != expected_identity.base_sha:
        raise ReviewStateError("review result policy ref must equal the exact BASE_SHA")
    if header["review_context"] != REVIEW_CONTEXT:
        raise ReviewStateError("review result context is not ordinary_chat_fresh")

    status = header["status"]
    validity = header["review_validity"]
    if status not in _ALLOWED_STATUS or validity not in _ALLOWED_VALIDITY:
        raise ReviewStateError("review result status/validity is invalid")
    findings = _parse_nonnegative_int(
        header["reported_findings"],
        "reported_findings",
        maximum=MAX_REPORTED_FINDINGS,
    )
    rejected = _parse_nonnegative_int(
        header["rejected_candidates"],
        "rejected_candidates",
        maximum=MAX_REJECTED_CANDIDATES,
    )
    if status == "PASS" and (validity != "CURRENT" or findings != 0):
        raise ReviewStateError("PASS requires CURRENT validity and zero reported findings")
    if status == "FINDINGS" and (validity != "CURRENT" or findings < 1):
        raise ReviewStateError("FINDINGS requires CURRENT validity and at least one reported finding")
    if status == "STALE" and validity not in {"STALE_BASE_CHANGE", "STALE_MATERIAL_CHANGE"}:
        raise ReviewStateError("STALE requires a stale review_validity")
    if status in {"PASS", "FINDINGS"} and validity != "CURRENT":
        raise ReviewStateError("current review outcomes require CURRENT validity")
    _parse_timestamp(header["reviewed_at"], "reviewed_at")
    _validate_finding_bodies(payload, findings)

    if automatic:
        expected = _validate_review_run_id(expected_review_run_id)
        if _validate_review_run_id(header["review_run_id"]) != expected:
            raise ReviewStateError("review result run capability mismatch")

    normalized_header: dict[str, Any] = dict(header)
    normalized_header["repository"] = result_identity.repository
    normalized_header["pr_number"] = result_identity.pr_number
    normalized_header["reported_findings"] = findings
    normalized_header["rejected_candidates"] = rejected
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return ParsedReviewResult(payload=payload, header=normalized_header, body_sha256=digest)


def submit_independent_review_result(request: Mapping[str, Any], *, state_root: Path) -> dict[str, Any]:
    if type(request) is not dict:
        raise ReviewStateError("submit request must be a plain object")
    _require_exact_keys(request, {"review_run_id", "result"}, "submit request")
    review_run_id = _validate_review_run_id(request["review_run_id"])
    result_payload = request["result"]
    if type(result_payload) is not str:
        raise ReviewStateError("submit result must be text")

    header = _result_header(result_payload, automatic=True)
    identity = _identity_from_result_header(header)
    operation_key = review_operation_key(identity)
    root = _review_root(state_root)
    with _acquire_task_lock(root, _lock_id(operation_key)):
        _, durable_run_id = _load_genesis(root, identity, operation_key)
        if durable_run_id != review_run_id:
            raise ReviewStateError("submit capability does not match immutable genesis")
        state = _load_state(root, identity, operation_key, durable_run_id)
        parsed = parse_review_result(
            result_payload,
            expected_identity=identity,
            automatic=True,
            expected_review_run_id=durable_run_id,
        )
        _require_completing_review_result(parsed, label="automatic review result")

        if state["result_state"] == "automatic-result-recorded":
            if state["result_body_sha256"] == parsed.body_sha256 and state["result_payload"] == parsed.payload:
                return {
                    "schema_version": 1,
                    "status": "already_recorded",
                    "operation_key": operation_key,
                    "result_source": "automatic",
                    "result_body_sha256": parsed.body_sha256,
                }
            raise ReviewStateError("automatic result is already recorded with a different digest")
        if state["result_state"] == "manual-fallback-recorded":
            raise ReviewStateError("automatic submission is closed by manual fallback")
        if state["dispatch_state"] != "dispatch-attempted":
            raise ReviewStateError("automatic result cannot be recorded before dispatch-attempted")

        updated = _record_result(
            state,
            source="automatic",
            parsed=parsed,
            dispatch_state="dispatch-attempted",
            recovery_reason=None,
        )
        _write_state_checkpoint(root, operation_key, updated)
        persisted = _load_state(root, identity, operation_key, durable_run_id)
        return {
            "schema_version": 1,
            "status": "recorded",
            "operation_key": operation_key,
            "result_source": "automatic",
            "result_body_sha256": persisted["result_body_sha256"],
        }


def reconcile_independent_review_result(request: Mapping[str, Any], *, state_root: Path) -> dict[str, Any]:
    if type(request) is not dict:
        raise ReviewStateError("reconcile request must be a plain object")
    allowed = set(_IDENTITY_KEYS) | {"manual_result"}
    unexpected = set(request) - allowed
    if unexpected:
        raise ReviewStateError(f"reconcile request contains unsupported fields: {sorted(unexpected)}")
    identity = parse_review_identity({key: request.get(key) for key in _IDENTITY_KEYS}, exact_keys=True)
    manual_payload = request.get("manual_result")
    if manual_payload is not None and type(manual_payload) is not str:
        raise ReviewStateError("manual_result must be text when supplied")

    operation_key = review_operation_key(identity)
    root = _review_root(state_root)
    with _acquire_task_lock(root, _lock_id(operation_key)):
        genesis_exists, state_exists, temp_paths = _paths_present(root, operation_key)
        if not genesis_exists and not state_exists:
            if temp_paths:
                raise ReviewStateError("independent-review residue exists without immutable genesis")
            raise ReviewStateError("independent-review operation does not exist")
        if not genesis_exists:
            raise ReviewStateError("independent-review state exists without immutable genesis")

        _, review_run_id = _load_genesis(root, identity, operation_key)
        if not state_exists:
            if manual_payload is None:
                return {
                    "schema_version": 1,
                    "status": "manual_recovery_required",
                    "operation_key": operation_key,
                    "automatic_submission_open": False,
                    "automatic_relaunch_allowed": False,
                    "temp_residue_count": len(temp_paths),
                }
            parsed_manual = parse_review_result(
                manual_payload,
                expected_identity=identity,
                automatic=False,
            )
            _require_completing_review_result(parsed_manual, label="manual recovery review result")
            terminal = _build_recovery_state(identity, operation_key, review_run_id, parsed_manual)
            _write_state_checkpoint(root, operation_key, terminal)
            persisted = _load_state(root, identity, operation_key, review_run_id)
            return _public_state_summary(persisted, include_result=True)

        state = _load_state(root, identity, operation_key, review_run_id)
        if state["result_state"] == "automatic-result-recorded":
            summary = _public_state_summary(state, include_result=True)
            if manual_payload is not None:
                summary["manual_result_recorded"] = False
                summary["manual_result_rejection"] = "automatic_result_already_authoritative"
            return summary
        if state["result_state"] == "manual-fallback-recorded":
            if manual_payload is not None:
                parsed_manual = parse_review_result(
                    manual_payload,
                    expected_identity=identity,
                    automatic=False,
                )
                _require_completing_review_result(parsed_manual, label="manual review result")
                if parsed_manual.body_sha256 != state["result_body_sha256"] or parsed_manual.payload != state["result_payload"]:
                    raise ReviewStateError("manual fallback is already recorded with a different digest")
            return _public_state_summary(state, include_result=True)

        if manual_payload is None:
            return {
                "schema_version": 1,
                "status": "pending",
                "operation_key": operation_key,
                "dispatch_state": state["dispatch_state"],
                "result_state": "open",
                "automatic_submission_open": state["dispatch_state"] == "dispatch-attempted",
            }

        parsed_manual = parse_review_result(
            manual_payload,
            expected_identity=identity,
            automatic=False,
        )
        _require_completing_review_result(parsed_manual, label="manual review result")
        updated = _record_result(
            state,
            source="manual",
            parsed=parsed_manual,
            dispatch_state=state["dispatch_state"],
            recovery_reason=None,
        )
        _write_state_checkpoint(root, operation_key, updated)
        persisted = _load_state(root, identity, operation_key, review_run_id)
        return _public_state_summary(persisted, include_result=True)


def _record_result(
    state: Mapping[str, Any],
    *,
    source: str,
    parsed: ParsedReviewResult,
    dispatch_state: str,
    recovery_reason: str | None,
) -> dict[str, Any]:
    if source not in {"automatic", "manual"}:
        raise ReviewStateError("invalid review result source")
    _require_completing_review_result(parsed, label="review result")
    now = _utc_now()
    updated = dict(state)
    updated["revision"] = int(state["revision"]) + 1
    updated["dispatch_state"] = dispatch_state
    updated["result_state"] = "automatic-result-recorded" if source == "automatic" else "manual-fallback-recorded"
    updated["result_source"] = source
    updated["result_body_sha256"] = parsed.body_sha256
    updated["result_payload"] = parsed.payload
    updated["result_recorded_at"] = now
    updated["recovery_reason"] = recovery_reason
    updated["updated_at"] = now
    return updated


def _build_recovery_state(
    identity: ReviewIdentity,
    operation_key: str,
    review_run_id: str,
    parsed_manual: ParsedReviewResult,
) -> dict[str, Any]:
    _require_completing_review_result(parsed_manual, label="manual recovery review result")
    now = _utc_now()
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "kind": STATE_KIND,
        "operation_key": operation_key,
        "identity": identity.as_dict(),
        "review_run_id": review_run_id,
        "revision": 1,
        "dispatch_state": "automation-abandoned",
        "result_state": "manual-fallback-recorded",
        "result_source": "manual",
        "result_body_sha256": parsed_manual.body_sha256,
        "result_payload": parsed_manual.payload,
        "result_recorded_at": now,
        "recovery_reason": "state-missing-after-genesis",
        "created_at": now,
        "updated_at": now,
    }


def _public_state_summary(state: Mapping[str, Any], *, include_result: bool) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": 1,
        "status": "recorded" if state["result_state"] != "open" else "open",
        "operation_key": state["operation_key"],
        "dispatch_state": state["dispatch_state"],
        "result_state": state["result_state"],
        "result_source": state["result_source"],
        "result_body_sha256": state["result_body_sha256"],
        "recovery_reason": state["recovery_reason"],
    }
    if include_result and state["result_state"] != "open":
        result["result"] = state["result_payload"]
    return result
