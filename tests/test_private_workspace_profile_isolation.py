from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEGACY_PROFILE_START = (ROOT / "scripts" / "start-chat-profile.ps1").read_text(
    encoding="utf-8"
)
SEMANTIC_LAUNCHER = (
    ROOT
    / "runtime"
    / "semantic-projection"
    / "bin"
    / "semantic-projection-launcher.mjs"
).read_text(encoding="utf-8")


class PrivateWorkspaceProfileIsolationTests(unittest.TestCase):
    def test_semantic_launcher_enforces_lifetime_disjointness_before_child_start(self):
        self.assertIn("export function assertPrivateWorkspaceIsolation", SEMANTIC_LAUNCHER)
        self.assertIn("fs.realpathSync.native", SEMANTIC_LAUNCHER)
        self.assertIn("function canonicalPotentialDirectory", SEMANTIC_LAUNCHER)
        self.assertIn("CHAT_LOCAL_FILES_ROOT", SEMANTIC_LAUNCHER)
        self.assertIn("CHAT_PROCEDURE_STATE_ROOT", SEMANTIC_LAUNCHER)
        self.assertIn(
            "const managerStatePath = path.join(paths.platformRoot, 'state');",
            SEMANTIC_LAUNCHER,
        )
        self.assertIn("private manager state", SEMANTIC_LAUNCHER)
        self.assertIn("configured independent-review state", SEMANTIC_LAUNCHER)
        self.assertIn("configuredReviewRoot", SEMANTIC_LAUNCHER)
        self.assertIn("protectedRoots", SEMANTIC_LAUNCHER)
        self.assertIn("isInsideOrEqual(protectedRoot.root, workspaceRoot)", SEMANTIC_LAUNCHER)
        self.assertIn("isInsideOrEqual(workspaceRoot, protectedRoot.root)", SEMANTIC_LAUNCHER)
        self.assertIn("qualification worktrees remain valid workspaces", SEMANTIC_LAUNCHER)

        guard = SEMANTIC_LAUNCHER.index(
            "const paths = assertPrivateWorkspaceIsolation(options);"
        )
        inventory = SEMANTIC_LAUNCHER.index("await assertExpectedSemanticInventory({")
        child = SEMANTIC_LAUNCHER.index(
            "const child = spawn(process.execPath, [semanticEntry]"
        )
        self.assertLess(guard, inventory)
        self.assertLess(guard, child)

    def test_legacy_file_profiles_resolve_physical_root_and_block_private_state_overlap(self):
        self.assertIn("function Resolve-PhysicalDirectoryPath", LEGACY_PROFILE_START)
        self.assertIn("function Resolve-PotentialPhysicalDirectoryPath", LEGACY_PROFILE_START)
        self.assertIn("fs.realpathSync.native(process.argv[1])", LEGACY_PROFILE_START)
        self.assertIn("function Test-PathsOverlap", LEGACY_PROFILE_START)
        self.assertIn(
            "Join-Path $env:LOCALAPPDATA 'ChatAgentPlatform\\state'",
            LEGACY_PROFILE_START,
        )
        self.assertIn("private manager state", LEGACY_PROFILE_START)
        self.assertIn("$env:CHAT_PROCEDURE_STATE_ROOT", LEGACY_PROFILE_START)
        self.assertIn("'independent-review-v1'", LEGACY_PROFILE_START)
        self.assertIn("configured independent-review state", LEGACY_PROFILE_START)
        self.assertIn("return $physicalFull", LEGACY_PROFILE_START)

        resolve = LEGACY_PROFILE_START.index(
            "$env:CHAT_LOCAL_FILES_ROOT = Resolve-SafeFilesRoot -Path $FilesRoot"
        )
        start = LEGACY_PROFILE_START.index("& $startBridge @bridgeArgs")
        self.assertLess(resolve, start)
        self.assertIn("$Profile -in @('files-readonly', 'adaptive')", LEGACY_PROFILE_START)


if __name__ == "__main__":
    unittest.main()
