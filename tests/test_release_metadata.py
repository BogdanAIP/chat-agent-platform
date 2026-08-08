import ast
import pathlib
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

    def test_release_workflow_is_tag_gated_and_immutable(self):
        workflow = (self.repo / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('tags:\n      - "v*.*.*"', workflow)
        self.assertIn("git merge-base --is-ancestor", workflow)
        self.assertIn('git checkout --detach "$tag_sha"', workflow)
        self.assertIn('git rev-parse HEAD', workflow)
        self.assertIn("GH_REPO: ${{ github.repository }}", workflow)
        self.assertIn("--verify-tag", workflow)
        self.assertIn("--generate-notes", workflow)
        self.assertIn("sha256sum -c SHA256SUMS", workflow)
        self.assertIn("cargo build --workspace --release --locked", workflow)
        self.assertIn("agent-platform.cdx.json", workflow)
        self.assertNotIn("--clobber", workflow)
        self.assertIn("already exists; refusing to overwrite", workflow)


if __name__ == "__main__":
    unittest.main()
