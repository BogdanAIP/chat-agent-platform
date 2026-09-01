from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
NONCE_RE = re.compile(r"^[0-9a-f]{64}$")
BRANCH_REF_RE = re.compile(r"^refs/heads/[A-Za-z0-9._/-]{1,220}$")
EXPECTED_REPOSITORY = "BogdanAIP/chat-agent-platform"
SHARD_BYTES = 1_000_000
MAX_SOURCE_SHARDS = 18
MAX_RECORD_BYTES = 950_000
LFS_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"


@dataclass(frozen=True)
class TreeEntry:
    mode: str
    kind: str
    oid: str
    path: str


@dataclass(frozen=True)
class Attachment:
    filename: str
    sha256: str
    bytes: int


def run_git(cwd: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "Never"
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        reason = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {reason[:1000]}")
    return completed.stdout


def run_git_status(cwd: Path, *args: str) -> tuple[int, bytes, bytes]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GCM_INTERACTIVE"] = "Never"
    completed = subprocess.run(
        ["git", "-C", str(cwd), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def configured_origin(repo: Path) -> str:
    value = run_git(repo, "config", "--get", "remote.origin.url").decode("utf-8", errors="strict").strip()
    if not value:
        raise RuntimeError("local repository has no origin URL")
    return value


def canonical_github_origin(value: str) -> str:
    candidates = (
        r"https://github\.com/BogdanAIP/chat-agent-platform(?:\.git)?/?",
        r"git@github\.com:BogdanAIP/chat-agent-platform(?:\.git)?",
        r"ssh://git@github\.com/BogdanAIP/chat-agent-platform(?:\.git)?/?",
    )
    if not any(re.fullmatch(pattern, value, re.IGNORECASE) for pattern in candidates):
        raise RuntimeError("origin does not identify the fixed experiment repository")
    # The experiment is public and intentionally fetches from GitHub rather than
    # trusting credentials or bytes in the developer checkout.
    return "https://github.com/BogdanAIP/chat-agent-platform.git"


def init_remote_store(path: Path, remote_url: str) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        ["git", "init", "--bare", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace")[:1000])
    run_git(path, "remote", "add", "origin", remote_url)


def fetch_exact_branches(
    store: Path,
    *,
    base_ref: str,
    head_ref: str,
    expected_base: str,
    expected_head: str,
) -> None:
    for value, label in ((base_ref, "base ref"), (head_ref, "head ref")):
        if BRANCH_REF_RE.fullmatch(value) is None or ".." in value or "//" in value:
            raise RuntimeError(f"invalid {label}")
    run_git(
        store,
        "fetch",
        "--force",
        "--no-tags",
        "origin",
        f"+{base_ref}:refs/cap/base",
        f"+{head_ref}:refs/cap/head",
    )
    actual_base = run_git(store, "rev-parse", "refs/cap/base^{commit}").decode().strip()
    actual_head = run_git(store, "rev-parse", "refs/cap/head^{commit}").decode().strip()
    if actual_base != expected_base:
        raise RuntimeError(f"remote base moved: expected={expected_base} actual={actual_base}")
    if actual_head != expected_head:
        raise RuntimeError(f"remote head moved: expected={expected_head} actual={actual_head}")
    run_git(store, "cat-file", "-e", f"{expected_base}^{{commit}}")
    run_git(store, "cat-file", "-e", f"{expected_head}^{{commit}}")


def parse_tree(raw: bytes) -> list[TreeEntry]:
    result: list[TreeEntry] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        meta, raw_path = record.split(b"\t", 1)
        mode, kind, oid = meta.decode("ascii").split(" ", 2)
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if path.startswith("/") or "\x00" in path or any(part in {".", ".."} for part in path.split("/")):
            raise RuntimeError("unsafe path in Git tree")
        result.append(TreeEntry(mode=mode, kind=kind, oid=oid, path=path))
    return sorted(result, key=lambda item: item.path.encode("utf-8", errors="surrogateescape"))


def tree_entries(store: Path, ref: str) -> list[TreeEntry]:
    return parse_tree(run_git(store, "ls-tree", "-rz", "--full-tree", "-r", ref))


def blob_bytes(store: Path, oid: str) -> bytes:
    if SHA_RE.fullmatch(oid) is None:
        raise RuntimeError("invalid blob id")
    return run_git(store, "cat-file", "blob", oid)


def classify_blob(mode: str, kind: str, raw: bytes | None) -> str:
    if mode == "160000" or kind == "commit":
        return "submodule"
    if mode == "120000":
        return "symlink"
    if raw is None:
        return "unsupported"
    if raw.startswith(LFS_PREFIX) and b"oid sha256:" in raw[:1024]:
        return "lfs_pointer"
    if b"\x00" in raw[:8192]:
        return "binary"
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "non_utf8"
    return "utf8_text"


def changed_paths(store: Path, base: str, head: str) -> list[str]:
    raw = run_git(store, "diff", "--name-only", "-z", "--find-renames", base, head, "--")
    values = [item.decode("utf-8", errors="surrogateescape") for item in raw.split(b"\0") if item]
    return sorted(set(values), key=lambda value: value.encode("utf-8", errors="surrogateescape"))


def read_text_at(store: Path, ref: str, path: str) -> tuple[str, str, int] | None:
    code, out, _ = run_git_status(store, "ls-tree", "-z", ref, "--", path)
    if code != 0 or not out:
        return None
    entries = parse_tree(out)
    exact = [item for item in entries if item.path == path]
    if len(exact) != 1 or exact[0].kind != "blob":
        return None
    entry = exact[0]
    raw = blob_bytes(store, entry.oid)
    if classify_blob(entry.mode, entry.kind, raw) != "utf8_text":
        return None
    return raw.decode("utf-8"), entry.oid, len(raw)


def source_record(*, namespace: str, entry: TreeEntry, text: str, byte_count: int) -> str:
    meta = json.dumps(
        {
            "namespace": namespace,
            "path": entry.path,
            "mode": entry.mode,
            "blob": entry.oid,
            "bytes": byte_count,
        },
        sort_keys=True,
        ensure_ascii=True,
        separators=(",", ":"),
    )
    return f"===== SOURCE {meta} =====\n{text.rstrip()}\n===== END SOURCE {entry.oid} =====\n"


def pack_records(records: Iterable[str], *, max_bytes: int = SHARD_BYTES) -> list[str]:
    shards: list[str] = []
    current: list[str] = []
    current_bytes = 0
    for record in records:
        encoded = record.encode("utf-8")
        if len(encoded) > min(MAX_RECORD_BYTES, max_bytes):
            raise RuntimeError(f"SNAPSHOT_OVERSIZE: one source record is {len(encoded)} bytes")
        if current and current_bytes + len(encoded) > max_bytes:
            shards.append("\n".join(current))
            current = []
            current_bytes = 0
        current.append(record)
        current_bytes += len(encoded)
    if current:
        shards.append("\n".join(current))
    if len(shards) > MAX_SOURCE_SHARDS:
        raise RuntimeError(f"SNAPSHOT_OVERSIZE: requires {len(shards)} source shards > {MAX_SOURCE_SHARDS}")
    return shards


def write_text(path: Path, text: str) -> Attachment:
    raw = text.encode("utf-8")
    path.write_bytes(raw)
    return Attachment(filename=path.name, sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def classify_local(repo: Path, store: Path, remote_head: str) -> dict[str, object]:
    local_head = run_git(repo, "rev-parse", "HEAD^{commit}").decode().strip()
    dirty_raw = run_git(repo, "status", "--porcelain=v2", "--untracked-files=normal")
    dirty = bool(dirty_raw.strip())

    if local_head == remote_head:
        relation = "MATCH"
    else:
        # Import the local commit into a parity-only ref after the remote snapshot
        # authority has already been fetched. This ref is never used for snapshot bytes.
        run_git(store, "fetch", "--force", "--no-tags", str(repo), f"+{local_head}:refs/cap/local-head")
        code_remote_ancestor, _, _ = run_git_status(store, "merge-base", "--is-ancestor", remote_head, local_head)
        code_local_ancestor, _, _ = run_git_status(store, "merge-base", "--is-ancestor", local_head, remote_head)
        if code_remote_ancestor == 0:
            relation = "LOCAL_AHEAD"
        elif code_local_ancestor == 0:
            relation = "REMOTE_AHEAD"
        else:
            relation = "DIVERGED"

    return {
        "classification": "DIRTY" if dirty else relation,
        "commit_relation": relation,
        "dirty": dirty,
        "local_head": local_head,
        "remote_target_head": remote_head,
    }


def build_snapshot(
    *,
    developer_repo: Path,
    remote_url: str,
    base_ref: str,
    head_ref: str,
    base_sha: str,
    head_sha: str,
    snapshot_nonce: str,
    output_dir: Path,
    repository: str = EXPECTED_REPOSITORY,
    pr_number: int = 0,
    identity_mode: str = "frozen_remote_range",
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    store = output_dir / "remote.git"
    init_remote_store(store, remote_url)
    fetch_exact_branches(
        store,
        base_ref=base_ref,
        head_ref=head_ref,
        expected_base=base_sha,
        expected_head=head_sha,
    )

    base_tree = run_git(store, "rev-parse", f"{base_sha}^{{tree}}").decode().strip()
    head_tree = run_git(store, "rev-parse", f"{head_sha}^{{tree}}").decode().strip()
    entries = tree_entries(store, head_sha)
    inventory: list[dict[str, object]] = []
    records: list[str] = []

    for entry in entries:
        raw = blob_bytes(store, entry.oid) if entry.kind == "blob" else None
        category = classify_blob(entry.mode, entry.kind, raw)
        byte_count = len(raw) if raw is not None else 0
        inventory.append(
            {
                "path": entry.path,
                "mode": entry.mode,
                "kind": entry.kind,
                "object": entry.oid,
                "bytes": byte_count,
                "category": category,
            }
        )
        if category == "utf8_text" and raw is not None:
            records.append(
                source_record(
                    namespace="HEAD",
                    entry=entry,
                    text=raw.decode("utf-8"),
                    byte_count=byte_count,
                )
            )

    changed = changed_paths(store, base_sha, head_sha)
    base_entry_by_path = {item.path: item for item in tree_entries(store, base_sha)}
    for path in changed:
        entry = base_entry_by_path.get(path)
        if entry is None or entry.kind != "blob":
            continue
        raw = blob_bytes(store, entry.oid)
        if classify_blob(entry.mode, entry.kind, raw) == "utf8_text":
            records.append(
                source_record(
                    namespace="BASE_CHANGED",
                    entry=entry,
                    text=raw.decode("utf-8"),
                    byte_count=len(raw),
                )
            )

    shards = pack_records(records)
    diff = run_git(
        store,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--find-renames",
        "--unified=80",
        base_sha,
        head_sha,
        "--",
    ).decode("utf-8", errors="replace")

    policy_files: dict[str, str] = {}
    for label, ref, path in (
        ("BASE_AGENTS", base_sha, "AGENTS.md"),
        ("BASE_CODE_REVIEW_SKILL", base_sha, ".agents/skills/code-review/SKILL.md"),
        ("HEAD_STAGE_RESEARCH_SKILL", head_sha, ".agents/skills/stage-research/SKILL.md"),
        ("HEAD_SOURCE_CODE_RESEARCH_SKILL", head_sha, ".agents/skills/source-code-research/SKILL.md"),
    ):
        value = read_text_at(store, ref, path)
        policy_files[label] = value[0] if value is not None else f"<UNAVAILABLE {path} @ {ref}>"

    parity = classify_local(developer_repo, store, head_sha)
    nonce_hash = hashlib.sha256(snapshot_nonce.encode("ascii")).hexdigest()

    semantic_omissions = [item for item in inventory if item["category"] in {"submodule", "lfs_pointer", "non_utf8", "binary"}]
    manifest_core = {
        "schema_version": 1,
        "kind": "SNAPSHOT_MANIFEST_V1",
        "repository": repository,
        "pr_number": pr_number,
        "identity_mode": identity_mode,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "base_tree": base_tree,
        "head_tree": head_tree,
        "base_ref": base_ref,
        "head_ref": head_ref,
        "remote_url_sha256": hashlib.sha256(remote_url.encode("utf-8")).hexdigest(),
        "snapshot_nonce": snapshot_nonce,
        "snapshot_nonce_sha256": nonce_hash,
        "changed_files": changed,
        "head_inventory": inventory,
        "semantic_omission_count": len(semantic_omissions),
        "semantic_omissions": semantic_omissions,
        "local_parity": parity,
    }

    change_body = [
        "SNAPSHOT_CHANGE_V1",
        f"repository={repository}",
        f"pr_number={pr_number}",
        f"base_sha={base_sha}",
        f"head_sha={head_sha}",
        "",
        "===== CHANGED FILES =====",
        *changed,
        "===== END CHANGED FILES =====",
        "",
        "===== EXACT BASE..HEAD DIFF =====",
        diff.rstrip(),
        "===== END EXACT BASE..HEAD DIFF =====",
    ]
    change_text = "\n".join(change_body) + "\n"

    policy_sections = []
    for label, value in policy_files.items():
        policy_sections.extend((f"===== {label} =====", value.rstrip(), f"===== END {label} =====", ""))
    policy_text = "SNAPSHOT_POLICY_V1\n\n" + "\n".join(policy_sections)

    attachments: list[Attachment] = []
    change_attachment = write_text(output_dir / "snapshot-change.txt", change_text)
    policy_attachment = write_text(output_dir / "snapshot-policy.txt", policy_text)
    source_attachments = [
        write_text(output_dir / f"snapshot-source-{index:02d}.txt", text)
        for index, text in enumerate(shards, start=1)
    ]

    source_digest_material = "\n".join(
        f"{item.filename}\t{item.sha256}\t{item.bytes}" for item in [change_attachment, policy_attachment, *source_attachments]
    ).encode("utf-8")
    snapshot_content_sha256 = hashlib.sha256(source_digest_material).hexdigest()
    manifest_core["snapshot_content_sha256"] = snapshot_content_sha256
    manifest_core["attachment_count_without_manifest"] = 2 + len(source_attachments)

    manifest_text = json.dumps(manifest_core, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    manifest_attachment = write_text(output_dir / "snapshot-manifest.txt", manifest_text)
    attachments = [manifest_attachment, change_attachment, policy_attachment, *source_attachments]
    if len(attachments) > 20:
        raise RuntimeError(f"SNAPSHOT_OVERSIZE: {len(attachments)} attachments > 20")

    index = {
        "schema_version": 1,
        "kind": "SNAPSHOT_ATTACHMENT_INDEX_V1",
        "repository": repository,
        "pr_number": pr_number,
        "identity_mode": identity_mode,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "snapshot_nonce_sha256": nonce_hash,
        "snapshot_content_sha256": snapshot_content_sha256,
        "local_parity": parity,
        "semantic_omission_count": len(semantic_omissions),
        "attachments": [item.__dict__ for item in attachments],
    }
    (output_dir / "snapshot-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return index


def main() -> int:
    parser = argparse.ArgumentParser(description="Build experiment-only remote-verified whole-repository review snapshot")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--snapshot-nonce", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--pr-number", type=int, default=0)
    parser.add_argument("--identity-mode", choices=("frozen_remote_range", "live_pr"), default="frozen_remote_range")
    args = parser.parse_args()

    if SHA_RE.fullmatch(args.base_sha) is None or SHA_RE.fullmatch(args.head_sha) is None or args.base_sha == args.head_sha:
        raise SystemExit("base/head must be distinct exact lowercase 40-hex SHAs")
    if NONCE_RE.fullmatch(args.snapshot_nonce) is None:
        raise SystemExit("snapshot nonce must be 64 lowercase hex characters")
    if args.pr_number < 0:
        raise SystemExit("pr number must be non-negative")

    repo = Path(args.repo_root).resolve()
    output = Path(args.output_dir).resolve()
    origin = canonical_github_origin(configured_origin(repo))
    index = build_snapshot(
        developer_repo=repo,
        remote_url=origin,
        base_ref=args.base_ref,
        head_ref=args.head_ref,
        base_sha=args.base_sha,
        head_sha=args.head_sha,
        snapshot_nonce=args.snapshot_nonce,
        output_dir=output,
        repository=EXPECTED_REPOSITORY,
        pr_number=args.pr_number,
        identity_mode=args.identity_mode,
    )
    parity = index["local_parity"]
    print("SNAPSHOT_SOURCE=remote_git_only")
    print(f"SNAPSHOT_BASE={index['base_sha']}")
    print(f"SNAPSHOT_HEAD={index['head_sha']}")
    print(f"SNAPSHOT_CONTENT_SHA256={index['snapshot_content_sha256']}")
    print(f"SNAPSHOT_ATTACHMENT_COUNT={len(index['attachments'])}")
    print(f"SNAPSHOT_SEMANTIC_OMISSION_COUNT={index['semantic_omission_count']}")
    print(f"LOCAL_PARITY_CLASSIFICATION={parity['classification']}")
    print(f"LOCAL_COMMIT_RELATION={parity['commit_relation']}")
    print(f"LOCAL_WORKTREE_DIRTY={str(parity['dirty'])}")
    print(f"LOCAL_HEAD={parity['local_head']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
