from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PREPARE_WINDOWS_L3 = (ROOT / "scripts" / "prepare-windows-case-l3.ps1").read_text(
    encoding="utf-8"
)
CLI = (ROOT / "runtime" / "control_plane" / "cli.py").read_text(encoding="utf-8")


class WindowsL3ReviewProvenanceClosureTests(unittest.TestCase):
    def test_unconditional_reviewer_imports_are_bound_into_source_and_installed_provenance(self) -> None:
        self.assertIn("from runtime.control_plane.independent_review_procedures import", CLI)
        self.assertIn("from runtime.control_plane.independent_review_state import", CLI)

        for module in (
            "independent_review_procedures.py",
            "independent_review_state.py",
        ):
            source_path = f"runtime/control_plane/{module}"
            installed_path = f"runtime\\control_plane\\{module}"
            with self.subTest(module=module):
                self.assertIn(
                    f"'{source_path}'",
                    PREPARE_WINDOWS_L3,
                    "every module imported by the Windows L3 CLI path must be source-provenance bound",
                )
                self.assertGreaterEqual(
                    PREPARE_WINDOWS_L3.count(f"'{installed_path}'"),
                    2,
                    "installed mapping must bind both source and installed bytes for the imported module",
                )


if __name__ == "__main__":
    unittest.main()
