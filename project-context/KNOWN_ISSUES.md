# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Adaptive 1MCP lifecycle/discovery is not accepted.** On functional baseline `9799bec...`, `mcp_list` sees disabled Filesystem/Playwright backends and Filesystem enable enters loading, but Lazy Loading never publishes `read_text_file` before timeout (`tools: []`, `loading retries=49`). Investigate upstream lifecycle/loading/capability refresh before introducing custom infrastructure.

2. **Ordinary Chat action snapshots do not automatically follow local direct-profile switching.** This was proven when Chat retained `filesystem_*` after the local runtime switched successfully to `browser-isolated`. Separate per-capability Chat apps are not the target solution; Stage 24 adaptive work is intended to provide one stable action contract.

3. **Adaptive is not yet integrated/accepted in the standalone Windows manager/bootstrap.** `start-chat-profile.ps1` knows the experimental `adaptive` profile, but the authoritative controller currently accepts only `reference`, `files-readonly`, and `browser-isolated`. Do not document adaptive as installed/default until runtime acceptance and manager integration are complete.

4. **Final ordinary-Chat browser/adaptive E2E is still required.** Local browser readiness is proven, but the stale action snapshot prevented the intended browser call through the existing Chat app. Final Stage 24 acceptance must prove the stable Chat-facing model on the real user surface.

5. **npm execution is top-level version pinned but not fully dependency locked for stable distribution.** Stage 26 should move normal lifecycle away from repeated `npx -y` dependency resolution.

6. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs explicit maintenance operations.

7. **Application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and Windows UI require real workflow benchmarks and scoped promotion into the local backend catalog.

8. **Universal ChatGPT plan availability must not be promised.** The user's actual surface passed the tunnel E2E, but product availability may vary/change.

9. **No first stable release exists.** Old release machinery belonged to the superseded universal binary; a new release format should package only the thin bridge after behavior stabilizes.

10. **Repository maintenance cleanup remains.** Historical feature branches/superseded PRs can be pruned after the active Stage 24 work is accepted.
