# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Present-target visual capability is intentionally limited.** The accepted Stage 25 baseline remains 3/5 present-target HIT because repeated-row and tiny-indicator classes are deliberately blocked. Final reviewed Stage 25.1 acceptance on HEAD `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c` passed 3/3 expected HIT plus 3/3 required ABSTAIN with 0 false clicks and 0 errors. This is a safety/behavior gate, not universal visual accuracy.

2. **Freshness verification is not atomic with coordinate click.** Stage 25.1 re-captures the exact CSS viewport and requires identical dimensions plus SHA256 before `browser_mouse_click_xy`, but the final screenshot and click are still separate MCP calls. A narrow TOCTOU window remains.

3. **Loopback vision endpoint ownership is PID-checked but not cryptographically authenticated.** Production verifies that `127.0.0.1:3068` belongs to the exact controller PID before screenshot inference and fails closed on mismatch. A same-user process could theoretically race port reuse after that check.

4. **Browser network policy is not a complete DNS/redirect sandbox.** Direct literal private/link-local/metadata/non-public destinations are blocked while loopback remains allowed. DNS resolution/rebinding and redirect policy remain residual work.

5. **Vision Python dependency reproducibility is not release-grade.** `Pillow==12.3.0` is exact, but stable distribution still needs an explicit Python artifact/hash/update policy.

6. **Pinned semantic npm graph includes deprecated transitive `glob@10.5.0`.** Keep this as a post-Stage-25.1 supply-chain follow-up with a dedicated dependency PR and full locked acceptance matrix.

7. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP remains diagnostic infrastructure; generic `tool_schema`/`tool_invoke` is not the ordinary-Chat product surface.

8. **Large typed action surfaces can be truncated in the tested Chat app.** Keep the public semantic surface small.

9. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.**

10. **OpenAI safety can block composite workflows independently of app permission mode.**

11. **Authorization policy is not fully finalized for future consequential capabilities.**

12. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.**

13. **Professional application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and broader Windows UI still need real workflow benchmarks.

14. **Repository metadata still contains historical wording.** Code/docs are authoritative until metadata is corrected.

15. **No first stable release exists.**

## Closed / superseded findings

- Final reviewed real-F16 acceptance passed on HEAD `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c`: 3/3 HIT, 3/3 ABSTAIN, 0 false clicks, 0 errors, `acceptance_pass=true`, `TEST_EXIT_CODE=0`.
- RAM admission flapping is closed by measured calibration. Production `min_start_physical_gb=1.35`; runtime floor remains `0.50 GB`; target emergency cutoff remains `0.30 GB`. Final reviewed minimum was `0.60 GB` with `SAFETY_STOP=False`.
- Final cleanup is proved: runtime stopped and Chrome remained running.
- Listener identity gap is closed by PID-bound loopback verification before inference; residual non-cryptographic race remains above.
- Prepared visual tokens are TTL-purged and capped at 256; overflow/expiry fails closed.
- Installed semantic bootstrap/source drift and lockfile-application drift are closed; changed lockfile forces `npm ci`.
- Cold Start descendant-stdio and target wrapper buffering defects are closed.
- Chrome non-termination regression assertion was corrected during review.
- Junction containment, credential scrub-before-core-load, CodeQL/Dependabot coverage, literal private-network blocking and the five-tool semantic surface remain accepted and regression-tested.
