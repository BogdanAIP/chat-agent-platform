# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Present-target visual capability is intentionally limited.** Stage 25 baseline remains 3/5 present-target HIT because repeated-row and tiny-indicator classes are deliberately blocked. Stage 25.2 adds public semantic-first escalation only for a narrow text-labeled miss path; it does not promote repeated-row/tiny/icon-only classes automatically.

2. **Freshness verification is not atomic with coordinate click.** The exact CSS viewport is re-captured and dimensions + SHA256 must match before `browser_mouse_click_xy`, but screenshot and click are still separate MCP calls. A narrow TOCTOU window remains.

3. **Loopback vision endpoint ownership is PID-checked but not cryptographically authenticated.** Production verifies `127.0.0.1:3068` belongs to the exact controller PID before screenshot inference and fails closed on mismatch. A same-user process could theoretically race port reuse after that check.

4. **Browser network policy is not a complete DNS/redirect sandbox.** Direct literal private/link-local/metadata/non-public destinations are blocked while loopback remains allowed. DNS resolution/rebinding and redirect policy remain residual work.

5. **Vision Python dependency reproducibility is not release-grade.** `Pillow==12.3.0` is exact, but stable distribution still needs an explicit Python/model artifact/hash/update policy.

6. **Pinned semantic npm graph includes deprecated transitive `glob@10.5.0`.** Keep this as a dedicated dependency follow-up with the full locked acceptance matrix.

7. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP remains diagnostic infrastructure; generic `tool_schema`/`tool_invoke` is not the ordinary-Chat product surface.

8. **Large typed action surfaces can be truncated in the tested Chat app.** Keep the public semantic surface small.

9. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.** Stage 25.2 keeps five tool names but changes `web_interact` schema/behavior, so app-side action refresh remains an operational concern.

10. **OpenAI safety can block composite workflows independently of app permission mode.**

11. **Authorization policy is not fully finalized for future consequential capabilities.** Stage 25.2 authorization is intentionally narrow to single text-labeled browser clicks after a proven semantic miss.

12. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.**

13. **Professional application candidates are not product-accepted.** Origin, REAPER, FFmpeg, Blender and broader Windows UI still need real workflow benchmarks.

14. **Repository metadata still contains historical wording.** Code/docs are authoritative until metadata is corrected.

15. **No first stable release exists.** Browser semantic→vision escalation is accepted, but real desktop capability and distribution/maintenance hardening are still incomplete.

## Closed / superseded findings

- Stage 25.1 PR #74 was squash-merged to `main` as `bbf490778a4d883bc54aa58a1d14e8779b7a5c94` after full review, real target acceptance and green workflow families.
- Stage 25.2 final reviewed production-code HEAD `41ef3f4032ae9169d940b3a04e5bdfe75170ca85` passed the real public semantic→F16 target gate: 2 semantic HIT, 1 visual HIT, 2 correct ABSTAIN, 0 false clicks, 0 errors, `semantic_cases_started_vlm=0`, `acceptance_pass=true`, `TEST_EXIT_CODE=0`.
- Final Stage 25.2 target cleanup is proved: `VISION_RUNTIME_RUNNING_AFTER_TEST=False`, runtime state `stopped`, Chrome remained running; minimum observed free physical RAM was 1.04 GB with `SAFETY_STOP=False`.
- Semantic click authorization no longer accepts an exact candidate merely because its name matches. A single candidate must be an enabled button; disabled/non-button exact matches ABSTAIN without VLM. Duplicate same-name buttons resolve only when exactly one is enabled and the alternatives are disabled buttons.
- Planner-controlled redirection of visual grounding is closed at the router boundary. `targetText` is the authorization anchor; planner `target` and free-form `instruction` do not select a different visual target; the router generates a canonical instruction from `targetText`.
- `semanticName` cannot create an artificial semantic miss: if supplied for compatibility, it must normalize exactly to `targetText`.
- Semantic ambiguity and generic semantic click errors never trigger vision.
- Safe ABSTAIN is surfaced as a successful no-action result rather than a backend error.
- Installed semantic bootstrap/source drift is closed for the Stage 25.2 vision dependency closure: semantic router/bridge/grounder modules, focused vision scripts, runtime config and required Python adapter files are copied and asserted in standalone installed-layout acceptance.
- RAM admission flapping is closed by measured calibration. Production `min_start_physical_gb=1.35`; runtime floor remains `0.50 GB`; target emergency cutoff remains `0.30 GB`.
- Listener identity gap is narrowed by PID-bound loopback verification before inference; residual non-cryptographic race remains above.
- Prepared visual tokens are TTL-purged and capped at 256; overflow/expiry fails closed.
- Changed semantic lockfile forces `npm ci` through the applied lock-hash marker.
- Cold Start descendant-stdio, target wrapper buffering, junction containment, credential scrub-before-core-load, CodeQL coverage and literal private-network blocking remain accepted and regression-tested.
