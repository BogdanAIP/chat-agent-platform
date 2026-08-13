# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Adaptive 1MCP lifecycle/discovery is CI-accepted and locally manager-integrated but not the default or ordinary-Chat accepted yet.** The integrated manager/bootstrap head still needs remote CI; the real ordinary-Chat gate remains after that.

2. **Ordinary Chat action snapshots do not automatically follow local direct-profile switching.** This was proven when Chat retained `filesystem_*` after the local runtime switched successfully to `browser-isolated`. Separate per-capability Chat apps are not the target solution; Stage 24 adaptive work is intended to provide one stable action contract.

3. **Adaptive remains opt-in.** The standalone manager/bootstrap supports and locally accepts it, but `reference` intentionally remains the installed default until the real ordinary-Chat acceptance proves the stable action contract.

4. **Final ordinary-Chat browser/adaptive E2E is still required.** Local browser readiness is proven, but the stale action snapshot prevented the intended browser call through the existing Chat app. Final Stage 24 acceptance must prove the stable Chat-facing model on the real user surface.

5. **npm execution is top-level version pinned but not fully dependency locked for stable distribution.** Stage 26 should move normal lifecycle away from repeated `npx -y` dependency resolution.

6. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs explicit maintenance operations.

7. **Application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and Windows UI require real workflow benchmarks and scoped promotion into the local backend catalog.

8. **Universal ChatGPT plan availability must not be promised.** The user's actual surface passed the tunnel E2E, but product availability may vary/change.

9. **No first stable release exists.** Old release machinery belonged to the superseded universal binary; a new release format should package only the thin bridge after behavior stabilizes.

10. **Repository maintenance cleanup remains.** Historical feature branches/superseded PRs can be pruned after the active Stage 24 work is accepted.
