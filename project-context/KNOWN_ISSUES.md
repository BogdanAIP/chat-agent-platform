# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Present-target visual capability is intentionally limited for unpromoted target classes.** The accepted Stage 25 baseline remains 3/5 present-target HIT because repeated-row and tiny-indicator classes are deliberately blocked. Stage 25.1 real same-session acceptance passed all currently promoted behavior: 3/3 expected HIT plus 3/3 required ABSTAIN, with 0 false clicks and 0 errors. Do not reinterpret the six-case safety/behavior gate as universal visual accuracy.

2. **Browser network policy is not a complete DNS/redirect sandbox.** Direct literal private/link-local/metadata/non-public destinations are blocked while loopback remains allowed. General hostnames can still resolve/redirect in ways that require a stronger backend/network boundary if future threat models demand it. Playwright origin filters are defense-in-depth only.

3. **Vision Python dependency reproducibility is not yet release-grade.** The current dependency graph is intentionally tiny and exactly pins `Pillow==12.3.0`, but stable distribution still needs an explicit Python artifact/hash/update policy.

4. **Pinned semantic npm graph currently includes deprecated transitive `glob@10.5.0`.** `npm ci` emits a deprecation/security-maintenance warning for this transitive package, but all current CI/security/semantic acceptance remains green. Treat this as a post-Stage-25.1 supply-chain follow-up: identify the owning direct dependency and upgrade through a dedicated dependency PR with the full locked acceptance matrix.

5. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP lifecycle mechanics remain useful diagnostic infrastructure, but generic `tool_schema`/`tool_invoke` is not the accepted ordinary-Chat product surface.

6. **Large typed action surfaces can be truncated in the tested Chat app.** A 34-tool local surface appeared as 20 actions in prior testing. This is measured behavior, not a universal official limit; keep the public semantic surface small.

7. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.** Server-side profile changes do not silently replace a frozen reviewed Chat action snapshot.

8. **OpenAI safety can block composite workflows independently of app permission mode.** Do not confuse a pre-MCP product safety decision with backend failure.

9. **Authorization policy is not fully finalized for future consequential capabilities.** Favor scoped/reversible boundaries and confirmations where consequence justifies them rather than permanent approval friction for every low-risk operation.

10. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs maintenance operations.

11. **Professional application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and broader Windows UI need real workflow benchmarks and scoped promotion.

12. **Repository metadata still contains historical wording.** The GitHub repository description still refers to a removed Rust-first core. Current connector access does not expose a repository-description mutation; code/docs are authoritative until metadata is corrected through an available GitHub UI/API path.

13. **No first stable release exists.** Do not package the current branch as stable until the Stage 25.1 foundation is merged and remaining distribution/reproducibility work is completed.

## Closed / superseded findings

- Stage 25.1 real F16 same-session acceptance passed on target Windows HEAD `956ca9e7d4b23c4af3b0f51c50f2450f4066abba` with user Chrome open: 3/3 expected HIT, 3/3 correct ABSTAIN, 0 safe misses, 0 false clicks, 0 errors, `safety_pass=true`, `acceptance_pass=true`.
- The cold runtime `Start` descendant-stdio settlement defect is closed. The Node runner no longer waits indefinitely for long-lived descendant-held stdio after the controller process exits; Windows regression marker `RUNTIME_BACKED_VISUAL_GROUNDER_DESCENDANT_STDIO=PASS` covers this case. The final real run completed the first labeled Send grounding in about 18.8 s instead of the prior 150 s timeout.
- The target wrapper stdout/stderr buffering defect is closed. The final real run exited autonomously with `TEST_EXIT_CODE=0`; no manual termination was required.
- The earlier RAM-admission hypothesis is superseded. Final target Doctor reported 2.704 GB free physical RAM before the run, minimum observed free physical RAM was 1.2 GB while the model was already running, `SAFETY_STOP=False`, and the reviewed start threshold did not need weakening.
- Final target cleanup is proved: `VISION_RUNTIME_RUNNING_AFTER_TEST=False`, state `stopped`, `CHROME_RUNNING_AFTER_TEST=True`, and the isolated worktree wrapper reported `CHROME_RUNNING_AFTER=True`.
- The scalable five-tool semantic typed projection is implemented and accepted.
- Local inference is no longer merely planned: llama.cpp + LFM2.5-VL-450M F16 passed the Stage 25 target grounding safety benchmark.
- LM Studio/llmster and 450M Q4 are historical research candidates, not the accepted baseline.
- Same-session capture/freshness/coordinate action is proved with one pinned Playwright MCP session; a second browser is unnecessary.
- Layout/scroll/overlay/navigation stale visual evidence and replayed tokens fail closed.
- Windows junction read/write escape attempts are explicitly regression-tested and blocked.
- Tunnel credential inheritance was tested, found real for the semantic stdio child, and closed with scrub-before-core-load launcher + sentinel regression.
- CodeQL analyzes Actions, JavaScript/TypeScript and Python.
- Dependabot covers Actions, semantic npm and Python requirements.
- Semantic Node dependencies use a committed lockfile and product/acceptance `npm ci`; unlocked install is refused when dependencies are absent.
- Direct private/link-local/metadata literal network destinations are rejected before browser navigation while loopback remains available.
- Installed/source split-brain on fixed port 3050 was closed by accepted single-owner/fail-closed lifecycle work. Normal semantic direct stdio does not use port 3050.
