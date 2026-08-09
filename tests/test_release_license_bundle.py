import pathlib
import tomllib
import unittest


class ReleaseLicenseBundleTests(unittest.TestCase):
    def setUp(self):
        self.repo = pathlib.Path(__file__).resolve().parents[1]

    def test_notice_policy_matches_dependency_license_policy(self):
        deny = tomllib.loads((self.repo / "deny.toml").read_text(encoding="utf-8"))
        about = tomllib.loads((self.repo / "about.toml").read_text(encoding="utf-8"))

        self.assertEqual(set(about["accepted"]), set(deny["licenses"]["allow"]))
        self.assertEqual(about["targets"], ["x86_64-pc-windows-msvc"])
        self.assertFalse(about["ignore-build-dependencies"])
        self.assertTrue(about["ignore-dev-dependencies"])
        self.assertFalse(about["ignore-transitive-dependencies"])

    def test_cargo_about_delivery_is_checksum_pinned(self):
        script = (self.repo / "scripts" / "generate-third-party-licenses.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('version="0.9.1"', script)
        self.assertIn(
            'expected_sha256="c0e7dc6f5d74b0beec5c0053d39ab24514c717d19acd91886907a22457ea9e98"',
            script,
        )
        self.assertIn("sha256sum --check --strict", script)
        self.assertIn("--workspace", script)
        self.assertIn("--all-features", script)
        self.assertIn("--locked", script)
        self.assertIn("--fail", script)
        self.assertNotIn("cargo install", script)

    def test_shared_assembler_requires_exact_release_contents(self):
        script = (self.repo / "scripts" / "assemble-release-package.sh").read_text(
            encoding="utf-8"
        )
        for required in (
            "agent-platform.exe",
            "agent-platform.cdx.json",
            "LICENSE",
            "THIRD_PARTY_LICENSES.html",
        ):
            self.assertIn(required, script)
        self.assertIn("unexpected release ZIP contents", script)
        self.assertIn("sha256sum -c SHA256SUMS", script)

    def test_release_uses_shared_assembler_and_does_not_publish_raw_exe(self):
        workflow = (self.repo / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("needs: [validate, windows-binary, sbom, licenses]", workflow)
        self.assertIn("release-licenses", workflow)
        self.assertIn("THIRD_PARTY_LICENSES.html", workflow)
        self.assertIn("runtime/release/LICENSE", workflow)
        self.assertIn("bash scripts/generate-third-party-licenses.sh", workflow)
        self.assertIn(
            'bash scripts/assemble-release-package.sh "$RELEASE_TAG" runtime/release',
            workflow,
        )

        release_start = workflow.index('gh release create "$RELEASE_TAG"')
        release_end = workflow.index("--verify-tag", release_start)
        release_block = workflow[release_start:release_end]
        self.assertNotIn("runtime/release/agent-platform.exe", release_block)
        self.assertIn("windows-x86_64.zip", release_block)
        self.assertIn("agent-platform.cdx.json", release_block)
        self.assertIn("runtime/release/LICENSE", release_block)
        self.assertIn("THIRD_PARTY_LICENSES.html", release_block)
        self.assertIn("SHA256SUMS", release_block)

    def test_notice_workflow_executes_shared_generator(self):
        workflow = (
            self.repo / ".github" / "workflows" / "license-notices.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("bash scripts/generate-third-party-licenses.sh", workflow)
        self.assertIn("Third Party Licenses", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)

    def test_release_package_e2e_is_non_publishing_and_uses_shared_assembler(self):
        workflow = (
            self.repo / ".github" / "workflows" / "release-package-e2e.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("needs: [windows-binary, sbom, licenses]", workflow)
        self.assertIn("bash scripts/assemble-release-package.sh", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("id-token: write", workflow)
        self.assertNotIn("attestations: write", workflow)
        self.assertNotIn("gh release create", workflow)


if __name__ == "__main__":
    unittest.main()
