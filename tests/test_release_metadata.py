import ast
import pathlib
import re
import tomllib
import unittest


class ReleaseMetadataTests(unittest.TestCase):
    def setUp(self):
        self.repo = pathlib.Path(__file__).resolve().parents[1]

    def test_rust_and_python_oracle_versions_match(self):
        cargo = tomllib.loads((self.repo / "Cargo.toml").read_text(encoding="utf-8"))
        pyproject = tomllib.loads((self.repo / "pyproject.toml").read_text(encoding="utf-8"))
        init_tree = ast.parse(
            (self.repo / "agent_platform" / "__init__.py").read_text(encoding="utf-8")
        )
        oracle = None
        for node in init_tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__version__":
                        oracle = ast.literal_eval(node.value)
        self.assertIsInstance(oracle, str, "agent_platform.__version__ must exist")
        rust_version = cargo["workspace"]["package"]["version"]
        python_package_version = pyproject["project"]["version"]
        self.assertEqual(rust_version, python_package_version)
        self.assertEqual(rust_version, oracle)

    def test_project_license_metadata_is_standard_mit(self):
        cargo = tomllib.loads((self.repo / "Cargo.toml").read_text(encoding="utf-8"))
        pyproject = tomllib.loads((self.repo / "pyproject.toml").read_text(encoding="utf-8"))
        license_text = (self.repo / "LICENSE").read_text(encoding="utf-8")

        self.assertEqual(cargo["workspace"]["package"]["license"], "MIT")
        self.assertEqual(pyproject["project"]["license"], "MIT")
        self.assertIn("LICENSE", pyproject["project"]["license-files"])
        self.assertTrue(license_text.startswith("MIT License\n"))

    def test_release_workflow_is_tag_gated_and_immutable(self):
        workflow = (self.repo / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        assembler = (
            self.repo / "scripts" / "assemble-release-package.sh"
        ).read_text(encoding="utf-8")
        self.assertIn('tags:\n      - "v*.*.*"', workflow)
        self.assertIn("git merge-base --is-ancestor", workflow)
        self.assertIn('git checkout --detach "$tag_sha"', workflow)
        self.assertIn("git rev-parse HEAD", workflow)
        self.assertIn("GH_REPO: ${{ github.repository }}", workflow)
        self.assertIn("--verify-tag", workflow)
        self.assertIn("--generate-notes", workflow)
        self.assertIn("bash scripts/assemble-release-package.sh", workflow)
        self.assertIn("sha256sum -c SHA256SUMS", assembler)
        self.assertIn("cargo build -p agent-platform --release --locked", workflow)
        self.assertNotIn("cargo build --workspace --release --locked", workflow)
        self.assertIn("agent-platform.cdx.json", workflow)
        self.assertNotIn("--clobber", workflow)
        self.assertIn("already exists; refusing to overwrite", workflow)

    def test_release_first_party_actions_are_sha_pinned(self):
        workflow = (self.repo / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        first_party_uses = re.findall(r"uses:\s+(actions/[\w-]+)@([^\s#]+)", workflow)
        self.assertTrue(first_party_uses, "release workflow must use first-party actions")
        for action, ref in first_party_uses:
            self.assertRegex(
                ref,
                r"^[0-9a-f]{40}$",
                f"{action} must be pinned to an immutable commit SHA",
            )

    def test_release_provenance_is_fail_closed_and_least_privilege(self):
        workflow = (self.repo / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("permissions:\n  contents: read\n", workflow)
        self.assertIn(
            "permissions:\n      contents: write\n      id-token: write\n      attestations: write",
            workflow,
        )
        self.assertIn(
            "actions/attest-build-provenance@4d101475d8b20a2381f78447822ac1eab6504dd8",
            workflow,
        )
        self.assertIn("subject-checksums: runtime/release/SHA256SUMS", workflow)
        attest_index = workflow.index("name: Attest release artifact provenance")
        publish_index = workflow.index("name: Create immutable GitHub Release assets")
        self.assertLess(attest_index, publish_index)


if __name__ == "__main__":
    unittest.main()
