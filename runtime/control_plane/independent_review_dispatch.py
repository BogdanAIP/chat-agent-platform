from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from ._verified_workspace_artifact_support import _acquire_task_lock, _safe_child
from .independent_review_state import (
    STATE_DIRECTORY,
    PreparedReviewOperation,
    ReviewIdentity,
    ReviewStateError,
    _load_genesis,
    _load_state,
    _lock_id,
    _review_root,
    _validate_review_run_id,
    parse_review_identity,
    review_operation_key,
)


DISPATCH_SCHEMA_VERSION = 1
DISPATCH_KIND = "independent-review-dispatch"
DISPATCH_DIRECTORY = "dispatch"
PUBLIC_WEB_EVIDENCE = "public-web"
DIRECT_FILE_EVIDENCE = "direct-file"
MAX_DISPATCH_BYTES = 96_000
MAX_EVIDENCE_BYTES = 5_000_000
EVIDENCE_CHUNK_BYTES = 512_000
MAX_GIT_STDERR_BYTES = 8_192
_PUBLIC_GITHUB_API = "https://api.github.com/repos/{repository}"
_REVIEW_RUN_ID_RE = re.compile(r"^[0-9a-f]{64}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,120}$")


@dataclass(frozen=True)
class ReviewDispatch:
    identity: ReviewIdentity
    operation_key: str
    review_run_id: str
    evidence_mode: str
    request_text: str
    completion_marker: str
    evidence_filename: str | None
    evidence_sha256: str | None
    evidence_bytes: int


def _encode_json(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _dispatch_root(state_root: Path) -> Path:
    review_root = _review_root(state_root)
    root = _safe_child(review_root, review_root / DISPATCH_DIRECTORY)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _dispatch_path(state_root: Path, review_run_id: str) -> Path:
    run_id = _validate_review_run_id(review_run_id)
    root = _dispatch_root(state_root)
    return _safe_child(root, root / f"{run_id}.json")


def _evidence_path(state_root: Path, review_run_id: str) -> Path:
    run_id = _validate_review_run_id(review_run_id)
    root = _dispatch_root(state_root)
    return _safe_child(root, root / f"{run_id}.evidence.txt")


def _exclusive_create(path: Path, payload: bytes, *, maximum_bytes: int, label: str) -> None:
    if not payload or len(payload) > maximum_bytes:
        raise ReviewStateError(f"{label} exceeds the accepted encoded bound")
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        raise


def _bounded_read(path: Path, *, maximum_bytes: int, label: str) -> bytes:
    try:
        with path.open("rb") as handle:
            payload = handle.read(maximum_bytes + 1)
    except FileNotFoundError as exc:
        raise ReviewStateError(f"{label} does not exist") from exc
    if not payload or len(payload) > maximum_bytes:
        raise ReviewStateError(f"{label} exceeds the accepted encoded bound")
    return payload


def _git_bytes(repo_root: Path, *args: str, maximum_bytes: int) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    if completed.returncode != 0:
        reason = completed.stderr[:MAX_GIT_STDERR_BYTES].decode("utf-8", errors="replace").strip()
        raise ReviewStateError(f"private review evidence git read failed: {reason or 'unknown error'}")
    if len(completed.stdout) > maximum_bytes:
        raise ReviewStateError("private review evidence exceeds the accepted bound")
    return completed.stdout


def _git_text(repo_root: Path, *args: str, maximum_bytes: int) -> str:
    return _git_bytes(repo_root, *args, maximum_bytes=maximum_bytes).decode("utf-8", errors="replace")


def _optional_git_blob(repo_root: Path, ref: str, path: str, *, maximum_bytes: int) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref}:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
    )
    if completed.returncode != 0:
        return f"<UNAVAILABLE {path} @ {ref}>\n"
    if len(completed.stdout) > maximum_bytes:
        raise ReviewStateError(f"private review evidence file is too large: {path}")
    return completed.stdout.decode("utf-8", errors="replace")


def _normalize_remote(value: str) -> str | None:
    remote = value.strip()
    patterns = (
        r"https://github\.com/([^/]+/[^/]+?)(?:\.git)?$",
        r"git@github\.com:([^/]+/[^/]+?)(?:\.git)?$",
        r"ssh://git@github\.com/([^/]+/[^/]+?)(?:\.git)?$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, remote, re.IGNORECASE)
        if match is not None:
            return match.group(1).lower()
    return None


def _verify_local_repository(repo_root: Path, identity: ReviewIdentity) -> Path:
    resolved = repo_root.resolve()
    top = _git_text(resolved, "rev-parse", "--show-toplevel", maximum_bytes=16_384).strip()
    if Path(top).resolve() != resolved:
        raise ReviewStateError("private review evidence requires workspace root to be the exact Git repository root")
    remote = _git_text(resolved, "remote", "get-url", "origin", maximum_bytes=16_384).strip()
    if _normalize_remote(remote) != identity.repository:
        raise ReviewStateError("private review evidence repository identity does not match origin")
    for ref in (identity.base_sha, identity.head_sha):
        _git_bytes(resolved, "cat-file", "-e", f"{ref}^{{commit}}", maximum_bytes=1)
    return resolved


def default_public_repository_probe(repository: str) -> bool:
    request = urllib.request.Request(
        _PUBLIC_GITHUB_API.format(repository=repository),
        method="GET",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "ChatAgentPlatform-Reviewer/1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return int(response.status) == 200
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        return False


def _section(name: str, body: str) -> str:
    return f"\n===== {name} =====\n{body.rstrip()}\n===== END {name} =====\n"


def build_private_review_evidence(
    *,
    workspace_root: Path,
    identity: ReviewIdentity,
    review_run_id: str,
) -> bytes:
    repo = _verify_local_repository(workspace_root, identity)
    changed = _git_text(
        repo,
        "diff",
        "--name-status",
        "--find-renames",
        identity.base_sha,
        identity.head_sha,
        "--",
        maximum_bytes=512_000,
    )
    diff = _git_text(
        repo,
        "diff",
        "--no-ext-diff",
        "--find-renames",
        "--unified=80",
        identity.base_sha,
        identity.head_sha,
        "--",
        maximum_bytes=MAX_EVIDENCE_BYTES,
    )
    manifest = {
        "schema_version": 1,
        "kind": "REVIEW_EVIDENCE_PACKAGE_V1",
        "repository": identity.repository,
        "pr_number": identity.pr_number,
        "base_sha": identity.base_sha,
        "head_sha": identity.head_sha,
        "review_skill": identity.review_skill,
        "review_skill_version": identity.review_skill_version,
        "review_run_id_sha256": hashlib.sha256(review_run_id.encode("ascii")).hexdigest(),
        "repository_truth": "local_exact_git_objects",
        "developer_reasoning_included": False,
    }
    parts = [
        "REVIEW_EVIDENCE_PACKAGE_V1\n",
        json.dumps(manifest, ensure_ascii=False, sort_keys=True),
        "\n",
        _section("BASE_AGENTS_MD", _optional_git_blob(repo, identity.base_sha, "AGENTS.md", maximum_bytes=512_000)),
        _section(
            "BASE_CODE_REVIEW_SKILL",
            _optional_git_blob(repo, identity.base_sha, ".agents/skills/code-review/SKILL.md", maximum_bytes=1_000_000),
        ),
        _section(
            "HEAD_STAGE_RESEARCH_SKILL",
            _optional_git_blob(repo, identity.head_sha, ".agents/skills/stage-research/SKILL.md", maximum_bytes=1_000_000),
        ),
        _section(
            "HEAD_SOURCE_CODE_RESEARCH_SKILL",
            _optional_git_blob(repo, identity.head_sha, ".agents/skills/source-code-research/SKILL.md", maximum_bytes=1_000_000),
        ),
        _section("CHANGED_FILE_INVENTORY", changed),
        _section("EXACT_BASE_TO_HEAD_DIFF", diff),
    ]
    payload = "".join(parts).encode("utf-8")
    if not payload or len(payload) > MAX_EVIDENCE_BYTES:
        raise ReviewStateError("private review evidence package exceeds the accepted bound")
    return payload


def _public_review_request(identity: ReviewIdentity, review_run_id: str, completion_marker: str) -> str:
    return f"""REVIEW_REQUEST_V1
repository={identity.repository}
pr_number={identity.pr_number}
base_sha={identity.base_sha}
head_sha={identity.head_sha}
review_skill={identity.review_skill}
review_skill_version={identity.review_skill_version}
review_run_id={review_run_id}

Perform the repository's accepted BASE .agents/skills/code-review/SKILL.md independent semantic review exactly as governed by BASE_SHA.

This is the bounded automatic reviewer path in a fresh non-personalized Temporary Chat. Remain strictly read-only. Use built-in public web/repository-reading capabilities only; do not use apps/plugins, internal ChatGPT APIs, Work, Codex, or ask the user for repository evidence. Independently resolve live PR identity, BASE review policy, applicable HEAD skills, exact BASE_SHA..HEAD_SHA diff, relevant tests/CI and affected correctness/security/recovery/concurrency/identity/authority/acceptance paths.

Return the required REVIEW_RESULT_V1. For this automatic run include exactly review_run_id={review_run_id} in the structured header. Report only findings that survive the governing skill's falsification requirements. Do not mutate the repository or PR.

After the complete final result and finding bodies, append exactly this final line:
{completion_marker}
Do not emit that line in progress updates.""".strip()


def _private_review_request(identity: ReviewIdentity, review_run_id: str, completion_marker: str) -> str:
    return f"""REVIEW_REQUEST_V1
repository={identity.repository}
pr_number={identity.pr_number}
base_sha={identity.base_sha}
head_sha={identity.head_sha}
review_skill={identity.review_skill}
review_skill_version={identity.review_skill_version}
review_run_id={review_run_id}

Perform the attached REVIEW_EVIDENCE_PACKAGE_V1 under the accepted BASE code-review policy. This is the bounded automatic reviewer path in a fresh non-personalized Temporary Chat.

Treat the attached package as the sole source of repository/code truth. Do not use GitHub or web search to locate, reconstruct, or supplement this private repository, and never search unique repository names, internal identifiers, SHAs, or code snippets from the package. You MAY use built-in web search for generic public technical documentation needed to validate semantics, provided the query contains no private repository/code material.

Treat the package identity as frozen for this review. If the package is missing, unreadable, hash-incomplete or insufficient to support a required conclusion, return ABSTAIN rather than substituting public repository lookup. Search for concrete correctness/security/recovery/concurrency/identity/authority/acceptance defects introduced by the exact bundled diff and falsify candidates before reporting them.

Return the required REVIEW_RESULT_V1. For this automatic run include exactly review_run_id={review_run_id} in the structured header. Do not mutate external state.

After the complete final result and finding bodies, append exactly this final line:
{completion_marker}
Do not emit that line in progress updates.""".strip()


def _validate_dispatch_record(value: Mapping[str, Any]) -> ReviewDispatch:
    expected = {
        "schema_version",
        "kind",
        "identity",
        "operation_key",
        "review_run_id",
        "evidence_mode",
        "request_text",
        "completion_marker",
        "evidence_filename",
        "evidence_sha256",
        "evidence_bytes",
    }
    if type(value) is not dict or set(value) != expected:
        raise ReviewStateError("independent-review dispatch schema mismatch")
    if value["schema_version"] != DISPATCH_SCHEMA_VERSION or value["kind"] != DISPATCH_KIND:
        raise ReviewStateError("independent-review dispatch kind/version mismatch")
    identity = parse_review_identity(value["identity"], exact_keys=True)
    operation_key = review_operation_key(identity)
    if value["operation_key"] != operation_key:
        raise ReviewStateError("independent-review dispatch operation key mismatch")
    review_run_id = _validate_review_run_id(value["review_run_id"])
    mode = value["evidence_mode"]
    if mode not in {PUBLIC_WEB_EVIDENCE, DIRECT_FILE_EVIDENCE}:
        raise ReviewStateError("independent-review dispatch evidence mode is invalid")
    request_text = value["request_text"]
    completion = value["completion_marker"]
    if type(request_text) is not str or not request_text or len(request_text.encode("utf-8")) > 64_000:
        raise ReviewStateError("independent-review dispatch request text is invalid")
    if type(completion) is not str or completion != f"CAP_REVIEW_COMPLETE={review_run_id}":
        raise ReviewStateError("independent-review dispatch completion marker mismatch")
    if f"review_run_id={review_run_id}" not in request_text or completion not in request_text:
        raise ReviewStateError("independent-review dispatch request is not run-bound")
    filename = value["evidence_filename"]
    digest = value["evidence_sha256"]
    evidence_bytes = value["evidence_bytes"]
    if mode == PUBLIC_WEB_EVIDENCE:
        if filename is not None or digest is not None or evidence_bytes != 0:
            raise ReviewStateError("public review dispatch cannot contain private evidence metadata")
    else:
        if type(filename) is not str or _SAFE_FILENAME_RE.fullmatch(filename) is None:
            raise ReviewStateError("private review evidence filename is invalid")
        if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
            raise ReviewStateError("private review evidence digest is invalid")
        if type(evidence_bytes) is not int or not 1 <= evidence_bytes <= MAX_EVIDENCE_BYTES:
            raise ReviewStateError("private review evidence size is invalid")
    return ReviewDispatch(
        identity=identity,
        operation_key=operation_key,
        review_run_id=review_run_id,
        evidence_mode=mode,
        request_text=request_text,
        completion_marker=completion,
        evidence_filename=filename,
        evidence_sha256=digest,
        evidence_bytes=evidence_bytes,
    )


def _load_dispatch(state_root: Path, review_run_id: str) -> ReviewDispatch:
    raw = _bounded_read(
        _dispatch_path(state_root, review_run_id),
        maximum_bytes=MAX_DISPATCH_BYTES,
        label="independent-review dispatch",
    )
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ReviewStateError("independent-review dispatch is invalid") from exc
    dispatch = _validate_dispatch_record(value)
    if dispatch.review_run_id != review_run_id:
        raise ReviewStateError("independent-review dispatch run id mismatch")
    return dispatch


def _validate_dispatch_state_binding(dispatch: ReviewDispatch, *, state_root: Path, require_attempted: bool) -> None:
    root = _review_root(state_root)
    with _acquire_task_lock(root, _lock_id(dispatch.operation_key)):
        _, durable_run_id = _load_genesis(root, dispatch.identity, dispatch.operation_key)
        if durable_run_id != dispatch.review_run_id:
            raise ReviewStateError("independent-review dispatch capability does not match immutable genesis")
        state = _load_state(root, dispatch.identity, dispatch.operation_key, durable_run_id)
        if state["result_state"] != "open":
            raise ReviewStateError("independent-review dispatch result slot is closed")
        if require_attempted and state["dispatch_state"] != "dispatch-attempted":
            raise ReviewStateError("independent-review dispatch is not durably attempted")
        if not require_attempted and state["dispatch_state"] not in {"prepared", "dispatch-attempted"}:
            raise ReviewStateError("independent-review dispatch state is not usable")


def prepare_review_dispatch(
    prepared: PreparedReviewOperation,
    *,
    workspace_root: Path,
    state_root: Path,
    public_probe: Callable[[str], bool] = default_public_repository_probe,
) -> ReviewDispatch:
    if prepared.result_state != "open" or prepared.dispatch_state != "prepared":
        raise ReviewStateError("review dispatch can be prepared only for an open prepared operation")
    existing_path = _dispatch_path(state_root, prepared.review_run_id)
    if existing_path.exists():
        existing = _load_dispatch(state_root, prepared.review_run_id)
        if existing.identity != prepared.identity or existing.operation_key != prepared.operation_key:
            raise ReviewStateError("existing independent-review dispatch identity mismatch")
        _validate_dispatch_state_binding(existing, state_root=state_root, require_attempted=False)
        return existing

    completion = f"CAP_REVIEW_COMPLETE={prepared.review_run_id}"
    evidence_mode = PUBLIC_WEB_EVIDENCE if public_probe(prepared.identity.repository) else DIRECT_FILE_EVIDENCE
    evidence_filename: str | None = None
    evidence_sha256: str | None = None
    evidence_size = 0

    if evidence_mode == DIRECT_FILE_EVIDENCE:
        payload = build_private_review_evidence(
            workspace_root=workspace_root,
            identity=prepared.identity,
            review_run_id=prepared.review_run_id,
        )
        evidence_sha256 = hashlib.sha256(payload).hexdigest()
        evidence_size = len(payload)
        evidence_filename = f"cap-review-{prepared.review_run_id[:16]}.txt"
        evidence_path = _evidence_path(state_root, prepared.review_run_id)
        if evidence_path.exists():
            persisted = _bounded_read(
                evidence_path,
                maximum_bytes=MAX_EVIDENCE_BYTES,
                label="private review evidence",
            )
            if hashlib.sha256(persisted).hexdigest() != evidence_sha256 or persisted != payload:
                raise ReviewStateError("private review evidence residue does not match deterministic rebuild")
        else:
            _exclusive_create(
                evidence_path,
                payload,
                maximum_bytes=MAX_EVIDENCE_BYTES,
                label="private review evidence",
            )
        request_text = _private_review_request(prepared.identity, prepared.review_run_id, completion)
    else:
        request_text = _public_review_request(prepared.identity, prepared.review_run_id, completion)

    record = {
        "schema_version": DISPATCH_SCHEMA_VERSION,
        "kind": DISPATCH_KIND,
        "identity": prepared.identity.as_dict(),
        "operation_key": prepared.operation_key,
        "review_run_id": prepared.review_run_id,
        "evidence_mode": evidence_mode,
        "request_text": request_text,
        "completion_marker": completion,
        "evidence_filename": evidence_filename,
        "evidence_sha256": evidence_sha256,
        "evidence_bytes": evidence_size,
    }
    payload = _encode_json(record)
    try:
        _exclusive_create(
            existing_path,
            payload,
            maximum_bytes=MAX_DISPATCH_BYTES,
            label="independent-review dispatch",
        )
    except FileExistsError:
        pass
    persisted = _load_dispatch(state_root, prepared.review_run_id)
    if persisted.identity != prepared.identity or persisted.operation_key != prepared.operation_key:
        raise ReviewStateError("persisted independent-review dispatch identity mismatch")
    _validate_dispatch_state_binding(persisted, state_root=state_root, require_attempted=False)
    return persisted


def get_review_dispatch_chunk(
    *,
    review_run_id: str,
    cursor: int,
    state_root: Path,
) -> dict[str, Any]:
    run_id = _validate_review_run_id(review_run_id)
    if type(cursor) is not int or cursor < 0 or cursor > MAX_EVIDENCE_BYTES:
        raise ReviewStateError("review dispatch cursor is invalid")
    dispatch = _load_dispatch(state_root, run_id)
    _validate_dispatch_state_binding(dispatch, state_root=state_root, require_attempted=True)

    response: dict[str, Any] = {
        "schema_version": 1,
        "type": "review_dispatch_chunk_v1",
        "review_run_id": run_id,
        "evidence_mode": dispatch.evidence_mode,
        "request_text": dispatch.request_text if cursor == 0 else None,
        "completion_marker": dispatch.completion_marker if cursor == 0 else None,
        "evidence_filename": dispatch.evidence_filename,
        "evidence_sha256": dispatch.evidence_sha256,
        "evidence_bytes": dispatch.evidence_bytes,
        "cursor": cursor,
        "next_cursor": cursor,
        "done": True,
        "chunk_b64": "",
    }
    if dispatch.evidence_mode == PUBLIC_WEB_EVIDENCE:
        if cursor != 0:
            raise ReviewStateError("public review dispatch cursor must be zero")
        return response

    raw = _bounded_read(
        _evidence_path(state_root, run_id),
        maximum_bytes=MAX_EVIDENCE_BYTES,
        label="private review evidence",
    )
    if len(raw) != dispatch.evidence_bytes or hashlib.sha256(raw).hexdigest() != dispatch.evidence_sha256:
        raise ReviewStateError("private review evidence no longer matches immutable dispatch metadata")
    if cursor > len(raw):
        raise ReviewStateError("review dispatch cursor exceeds evidence size")
    chunk = raw[cursor : cursor + EVIDENCE_CHUNK_BYTES]
    next_cursor = cursor + len(chunk)
    response["chunk_b64"] = base64.b64encode(chunk).decode("ascii")
    response["next_cursor"] = next_cursor
    response["done"] = next_cursor == len(raw)
    return response


def cleanup_review_evidence(*, review_run_id: str, state_root: Path) -> bool:
    run_id = _validate_review_run_id(review_run_id)
    dispatch = _load_dispatch(state_root, run_id)
    path = _evidence_path(state_root, run_id)
    if dispatch.evidence_mode != DIRECT_FILE_EVIDENCE:
        return True
    try:
        path.unlink()
    except FileNotFoundError:
        return True
    return not path.exists()


def dispatch_install_state_root() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise ReviewStateError("LOCALAPPDATA is required for reviewer native host")
    return Path(local) / "ChatAgentPlatform" / "state" / "procedure-runtime"
