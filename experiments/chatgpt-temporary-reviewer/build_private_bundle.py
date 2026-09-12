from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
HEX40_RE = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")
MAX_BUNDLE_BYTES = 900_000


def git_bytes(repo: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        reason = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {reason[:500]}")
    return completed.stdout


def git_text(repo: Path, *args: str) -> str:
    return git_bytes(repo, *args).decode("utf-8", errors="replace")


def optional_blob(repo: Path, ref: str, path: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{path}"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        return f"<UNAVAILABLE {path} at {ref}>\n"
    return completed.stdout.decode("utf-8", errors="replace")


def private_hash(nonce: str, value: str) -> str:
    return hashlib.sha1(f"{nonce}:{value}".encode("utf-8")).hexdigest()


def pseudonymize(text: str, nonce: str) -> str:
    mapping: dict[str, str] = {}

    def replace_sha(match: re.Match[str]) -> str:
        original = match.group(0)
        return mapping.setdefault(original, private_hash(nonce, original))

    text = HEX40_RE.sub(replace_sha, text)
    text = text.replace("https://github.com/BogdanAIP/chat-agent-platform", "https://private.invalid/PrivateControl/reviewer-fixture")
    text = text.replace("github.com/BogdanAIP/chat-agent-platform", "private.invalid/PrivateControl/reviewer-fixture")
    text = text.replace("BogdanAIP/chat-agent-platform", "PrivateControl/reviewer-fixture")
    return text


def section(name: str, body: str) -> str:
    return f"\n===== {name} =====\n{body.rstrip()}\n===== END {name} =====\n"


def build_bundle(repo: Path, base: str, head: str, nonce: str) -> str:
    git_bytes(repo, "cat-file", "-e", f"{base}^{{commit}}")
    git_bytes(repo, "cat-file", "-e", f"{head}^{{commit}}")

    changed = git_text(repo, "diff", "--name-status", "--find-renames", base, head, "--")
    diff = git_text(repo, "diff", "--no-ext-diff", "--find-renames", "--unified=80", base, head, "--")

    parts = [
        "REVIEW_EVIDENCE_BUNDLE_V1\n",
        "repository=PrivateControl/reviewer-fixture\n",
        "evidence_source=local_git_only\n",
        "external_network_used_by_builder=no\n",
        f"bundle_nonce={nonce}\n",
        f"base_sha={private_hash(nonce, base)}\n",
        f"head_sha={private_hash(nonce, head)}\n",
        "identity_note=Public repository identity and all 40-hex values are pseudonymized for this private-bundle control.\n",
        section("BASE_AGENTS_MD", optional_blob(repo, base, "AGENTS.md")),
        section("BASE_CODE_REVIEW_SKILL", optional_blob(repo, base, ".agents/skills/code-review/SKILL.md")),
        section("HEAD_STAGE_RESEARCH_SKILL", optional_blob(repo, head, ".agents/skills/stage-research/SKILL.md")),
        section("HEAD_SOURCE_CODE_RESEARCH_SKILL", optional_blob(repo, head, ".agents/skills/source-code-research/SKILL.md")),
        section("BASE_ARCHITECTURE_REUSE_BASELINE", optional_blob(repo, base, "project-context/ARCHITECTURE_REUSE_BASELINE.md")),
        section("CHANGED_FILE_INVENTORY", changed),
        section("EXACT_BASE_TO_HEAD_DIFF", diff),
    ]
    bundle = pseudonymize("".join(parts), nonce)
    encoded = bundle.encode("utf-8")
    if len(encoded) > MAX_BUNDLE_BYTES:
        raise RuntimeError(f"bundle too large: {len(encoded)} > {MAX_BUNDLE_BYTES}")
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an experiment-only local Git review evidence bundle")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--bundle-nonce", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if SHA_RE.fullmatch(args.base_sha) is None or SHA_RE.fullmatch(args.head_sha) is None:
        raise SystemExit("base/head must be exact lowercase 40-hex SHAs")
    if re.fullmatch(r"[0-9a-f]{64}", args.bundle_nonce) is None:
        raise SystemExit("bundle nonce must be 64 lowercase hex characters")

    repo = Path(args.repo_root).resolve()
    output = Path(args.output).resolve()
    bundle = build_bundle(repo, args.base_sha, args.head_sha, args.bundle_nonce)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(bundle, encoding="utf-8", newline="\n")
    print(f"PRIVATE_REVIEW_BUNDLE_BYTES={len(bundle.encode('utf-8'))}")
    print(f"PRIVATE_REVIEW_BUNDLE_SHA256={hashlib.sha256(bundle.encode('utf-8')).hexdigest()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
