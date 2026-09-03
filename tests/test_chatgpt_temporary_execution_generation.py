from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "runtime" / "agent_sessions" / "chatgpt_temporary_extension"
GENERATION_INPUTS = (
    "manifest.json",
    "policy.js",
    "background.js",
    "content.js",
)
GENERATION_RE = re.compile(
    r'CAPChatGPTTemporaryExecutionGeneration\s*=\s*"([0-9a-f]{64})"'
)


def normalized_repo_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def git_blob_sha(path: Path) -> str:
    data = normalized_repo_bytes(path)
    payload = f"blob {len(data)}\0".encode("ascii") + data
    return hashlib.sha1(payload).hexdigest()


def expected_generation() -> str:
    blobs = {name: git_blob_sha(EXTENSION / name) for name in GENERATION_INPUTS}
    canonical = json.dumps(blobs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


class ChatGPTTemporaryExecutionGenerationTests(unittest.TestCase):
    def test_generation_marker_cryptographically_binds_current_runtime_sources(self) -> None:
        source = (EXTENSION / "execution_generation.js").read_text(encoding="utf-8")
        match = GENERATION_RE.search(source)
        self.assertIsNotNone(match)
        self.assertEqual(expected_generation(), match.group(1))

    def test_generation_executes_before_policy_content_and_background_logic(self) -> None:
        manifest = json.loads((EXTENSION / "manifest.json").read_text(encoding="utf-8"))
        scripts = manifest["content_scripts"][0]["js"]
        self.assertEqual(
            ["execution_generation.js", "policy.js", "content.js"],
            scripts,
        )
        background = (EXTENSION / "background.js").read_text(encoding="utf-8")
        self.assertTrue(background.startswith('importScripts("execution_generation.js");'))
        self.assertIn("execution_generation: EXECUTION_GENERATION", background)
        self.assertIn("message.execution_generation === EXECUTION_GENERATION", background)
        content = (EXTENSION / "content.js").read_text(encoding="utf-8")
        self.assertIn("execution_generation: executionGeneration", content)
        self.assertIn("response.execution_generation !== executionGeneration", content)


if __name__ == "__main__":
    unittest.main()
