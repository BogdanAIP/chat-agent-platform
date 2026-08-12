# Known Issues

Only unresolved issues for the accepted bridge architecture are listed here.

1. **Stage 24 still needs final real ordinary-Chat acceptance.** Filesystem and Playwright are Windows/1MCP accepted, but the final current-profile path must still be exercised from ordinary Chat through the real Secure MCP Tunnel for both `files-readonly` and `browser-isolated`, including tool-surface switching.

2. **The new bootstrap still needs one clean real-machine acceptance run.** CI can parse and contract-test download/profile/manager behavior, but it cannot use the user's real provisioned OpenAI tunnel ID/runtime key. The real Windows bootstrap is therefore an explicit acceptance gate before calling Stage 24 complete.

3. **npm execution is version-pinned but not yet fully dependency-locked for distribution.** The current bridge uses pinned top-level `npx -y package@version` commands. A stable distribution should move to a reproducible local dependency installation/lock strategy so normal lifecycle is less dependent on registry resolution and transitive version ranges.

4. **Runtime-key rotation is not yet a first-class manager action.** DPAPI storage exists, but a dedicated `Set/RotateTunnelKey` operation and repair/uninstall flow should be added before the first stable release.

5. **Application candidates are not product-accepted yet.** REAPER, Origin, FFmpeg, Blender and Windows UI still require real workflow benchmarks and their own narrow security profiles.

6. **Universal Plus availability must not be promised.** The user's actual ChatGPT surface passed the custom MCP tunnel round trip, but product/plan availability rules may vary or change.

7. **Legacy external rollback infrastructure may still exist operationally.** Yandex and older Tailscale resources are no longer repository dependencies, but their live retirement is separate from repository cleanup.

8. **No first stable release is published.** The previous release pipeline packaged the superseded universal binary and was correctly removed. A new release format should package/bootstrap only the thin bridge manager after Stage 24/25 behavior stabilizes.

9. **Repository/runtime maintenance cleanup remains.** Historical feature branches and superseded PRs do not affect the active product but should be pruned/closed after the current Stage 24 branch is accepted.
