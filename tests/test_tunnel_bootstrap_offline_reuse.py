from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TUNNEL_BOOTSTRAP = ROOT / "scripts" / "bootstrap-tunnel-runtime.ps1"


class TunnelBootstrapOfflineReuseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = TUNNEL_BOOTSTRAP.read_text(encoding="utf-8")

    def test_verified_local_install_is_checked_before_network_release_fetch(self):
        install_start = self.source.index("function Install-ChatOfficialTunnelClient")
        install_body = self.source[install_start:]
        local_check = install_body.index("Test-ChatVerifiedInstalledTunnelClient")
        network_fetch = install_body.index("Get-ChatOfficialTunnelRelease")
        self.assertLess(local_check, network_fetch)
        self.assertIn("TUNNEL_NETWORK_FETCH_REQUIRED=False", install_body)
        self.assertIn("TUNNEL_NETWORK_FETCH_REQUIRED=True", install_body)

    def test_local_reuse_is_fail_closed_and_bound_to_pinned_release_evidence(self):
        guard_start = self.source.index("function Test-ChatVerifiedInstalledTunnelClient")
        install_start = self.source.index("function Install-ChatOfficialTunnelClient")
        guard = self.source[guard_start:install_start]

        for expected in (
            "$metadata.schema_version",
            "$metadata.version",
            "$metadata.asset",
            "$metadata.archive_sha256",
            "$metadata.binary_sha256",
            "$AcceptedArchiveSha256[$arch]",
            "Get-FileHash -LiteralPath $TunnelExe -Algorithm SHA256",
            "& $TunnelExe help quickstart",
            "TUNNEL_BINARY_SOURCE=verified-local-install",
            "TUNNEL_BINARY_VERIFIED=True",
        ):
            self.assertIn(expected, guard)

        self.assertIn("-not $ForceUpdate", self.source)
        self.assertNotIn("Invoke-RestMethod", guard)
        self.assertNotIn("Invoke-WebRequest", guard)

    def test_force_update_still_requires_the_official_network_path(self):
        install_start = self.source.index("function Install-ChatOfficialTunnelClient")
        install_body = self.source[install_start:]
        self.assertIn("-not $ForceUpdate -and", install_body)
        self.assertIn("Get-ChatOfficialTunnelRelease", install_body)
        self.assertIn("SHA256SUMS.txt", self.source)


if __name__ == "__main__":
    unittest.main()
