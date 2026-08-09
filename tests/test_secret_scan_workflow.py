import pathlib
import unittest


class SecretScanWorkflowTests(unittest.TestCase):
    def test_secret_scan_is_history_complete_pinned_and_redacted(self):
        repo = pathlib.Path(__file__).resolve().parents[1]
        workflow = (repo / ".github" / "workflows" / "secret-scan.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn('version="8.30.1"', workflow)
        self.assertIn(
            'expected_sha256="551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb"',
            workflow,
        )
        self.assertIn("sha256sum --check --strict", workflow)
        self.assertIn('--redact=100', workflow)
        self.assertIn('--log-opts="--all"', workflow)
        self.assertNotIn("upload-artifact", workflow)
        self.assertNotIn("GITLEAKS_LICENSE", workflow)


if __name__ == "__main__":
    unittest.main()
