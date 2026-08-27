import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREPARE = ROOT / "scripts" / "prepare-browser-real-task-gate.ps1"
CHECKER = ROOT / "scripts" / "check-browser-real-task-gate.ps1"


class BrowserL3ProvenanceContractTests(unittest.TestCase):
    def test_prepare_runs_clean_exact_head_source_provenance_before_fixture(self):
        text = PREPARE.read_text(encoding="utf-8")
        folded = text.casefold()
        provenance = folded.index("source provenance gate failed before browser l3 preparation")
        fixture = folded.index("start-process -filepath $node")
        self.assertLess(provenance, fixture)
        self.assertIn("'--repo-root', $sourceroot", folded)
        self.assertIn("'--expected-head', $expectedhead", folded)
        self.assertIn("'--lockfile', 'runtime/semantic-projection/package-lock.json'", folded)
        self.assertIn("runtime/semantic-projection/lib/browser-verification-bridge.mjs", folded)
        self.assertIn("runtime/control_plane/browser_transition.py", folded)
        self.assertIn("tests/fixtures/browser_real_task_server.mjs", folded)
        self.assertIn("-not [bool]$sourceprovenance.untracked_empty", folded)

    def test_prepare_binds_installed_browser_runtime_and_playwright_package(self):
        text = PREPARE.read_text(encoding="utf-8").casefold()
        self.assertIn("get-installedassetrecord", text)
        self.assertIn("get-directorydigest", text)
        self.assertIn("runtime\\semantic-projection\\lib\\browser-verification-bridge.mjs", text)
        self.assertIn("runtime\\control_plane\\browser_observation.py", text)
        self.assertIn("runtime\\semantic-projection\\package-lock.json", text)
        self.assertIn("node_modules\\@playwright\\mcp\\package.json", text)
        self.assertIn("$playwrightversion -ne '0.0.78'", text)
        self.assertIn("$playwrightlockrecord['integrity']", text)
        self.assertIn("playwright_mcp_lock_integrity", text)
        self.assertIn("playwright_mcp_directory_sha256", text)
        self.assertIn("installed approot bytes do not match the frozen browser l3 source head", text)

    def test_prepare_freezes_checker_and_provenance_code_outside_chat_workspace(self):
        text = PREPARE.read_text(encoding="utf-8").casefold()
        self.assertIn("$frozengateroot = join-path $qualificationroot 'frozen-gate'", text)
        self.assertIn("copy-item -literalpath $checkerscript -destination $frozencheckerpath", text)
        self.assertIn("copy-item -literalpath $sourceprovenancegate -destination $frozenprovenancepath", text)
        self.assertIn("frozen_checker_sha256", text)
        self.assertIn("frozen_provenance_gate_sha256", text)
        self.assertIn("fixture_process_start_time_ticks", text)
        self.assertIn("check_command=", text)
        self.assertIn("fixture-state is outside the chat workspace", text)
        self.assertIn("provenance evidence and frozen finish gate are outside the chat workspace", text)

    def test_checker_revalidates_source_installed_and_playwright_bytes_before_finish_gate(self):
        text = CHECKER.read_text(encoding="utf-8")
        folded = text.casefold()
        provenance = folded.index("browser l3 source provenance revalidation failed")
        finish = folded.index("finish_gate_not_done")
        self.assertLess(provenance, finish)
        self.assertIn("$frozenprovenancepath", folded)
        self.assertIn("'--expected-head', $expectedhead", folded)
        self.assertIn("installed browser l3 runtime byte drift", folded)
        self.assertIn("frozen browser finish gate checker hash drifted", folded)
        self.assertIn("frozen source provenance gate hash drifted", folded)
        self.assertIn("source lock integrity for @playwright/mcp drifted", folded)
        self.assertIn("installed @playwright/mcp package bytes drifted", folded)
        self.assertIn("playwright_mcp_provenance=pass", folded)
        self.assertIn("source_provenance_revalidated=pass", folded)
        self.assertIn("installed_runtime_revalidated=pass", folded)
        self.assertIn("provenance_revalidation=pass", folded)

    def test_checker_requires_exact_fixture_generation_one_save_and_cleanup(self):
        text = CHECKER.read_text(encoding="utf-8").casefold()
        provenance = text.index("browser l3 source provenance revalidation failed")
        finally_block = text.index("finally {")
        self.assertLess(provenance, finally_block)
        self.assertIn("fixture process was not live at finish gate proof time", text)
        self.assertIn("fixture process identity drifted", text)
        self.assertIn("fixture process generation drifted", text)
        self.assertIn("requires exactly one persisted save", text)
        self.assertIn("requires exactly one audit mutation", text)
        self.assertIn("only_target_ever_mutated=true", text)
        self.assertIn("decoys_unchanged=true", text)
        self.assertIn("external_finish_gate=done", text)
        self.assertIn("stop-process -id $fixturepid -force", text)
        self.assertIn("fixture_cleanup_pass=", text)
        self.assertIn("stage26_3b_browser_real_task_gate=pass", text)


if __name__ == "__main__":
    unittest.main()
