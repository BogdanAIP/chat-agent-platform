from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_HELPER = ROOT / "scripts" / "semantic-projection-runtime.ps1"


class SemanticProjectionRuntimeLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = RUNTIME_HELPER.read_text(encoding="utf-8")

    def test_dependency_readiness_is_bound_to_current_lock_hash(self) -> None:
        for marker in (
            "node_modules\\.chat-agent-platform-lock.sha256",
            "Get-FileHash -LiteralPath $lockPath -Algorithm SHA256",
            "Test-Path -LiteralPath $lockMarkerPath -PathType Leaf",
            "$appliedLockSha256 -ne $lockSha256",
            "Set-Content -LiteralPath $lockMarkerPath -Value $lockSha256",
        ):
            self.assertIn(marker, self.source)

    def test_missing_lock_still_refuses_unlocked_install(self) -> None:
        self.assertIn(
            "package-lock.json is missing; refusing unlocked installation",
            self.source,
        )
        self.assertIn("& $npm ci", self.source)
        self.assertIn("--ignore-scripts", self.source)


if __name__ == "__main__":
    unittest.main()
