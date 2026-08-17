# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Real F16 visual grounding is connected to the internal target harness but has not yet completed a same-session browser inference/action run.** The same-session capture/freshness/action boundary, focused llama.cpp lifecycle owner, production grounder and runtime-backed bridge are implemented and CI-proved, but the first target-laptop production-like attempt stopped before inference because every case hit `vision-runtime-start-failed`.

2. **Present-target visual accuracy is still limited.** Accepted target evidence remains 3/5 present-target HIT. Gamma repeated-row and tiny-indicator cases safely abstain and are deliberately not promoted for production clicks.

3. **The first target-laptop Stage 25.1 production-like run exposed a runtime-start/resource-admission blocker.** On HEAD `efc5a15e65e0f60c44f3194d7e95e448655eb951`, Doctor passed before Playwright with 1.939 GB free physical RAM and 9.226 GB free virtual memory, but the harness later observed a minimum of 1.38 GB free physical RAM while the Playwright/Chrome session was active. All six cases failed before inference with `vision-runtime-start-failed`; false clicks remained 0, `SAFETY_STOP=False`, the owned vision runtime was stopped after the test, and user Chrome remained running. The reviewed start floor is 1.50 GB, so browser-load admission is the leading explanation, but do not lower the floor until the next run captures the exact bounded Start stderr/stdout from the runtime-backed runner.

4. **Browser network policy is not a complete DNS/redirect sandbox.** Direct literal private/link-local/metadata/non-public destinations are blocked while loopback remains allowed. General hostnames can still resolve/redirect in ways that require a stronger backend/network boundary if future threat models demand it. Playwright origin filters are defense-in-depth only.

5. **Vision Python dependency reproducibility is not yet release-grade.** The current dependency graph is intentionally tiny and exactly pins `Pillow==12.3.0`, but stable distribution still needs an explicit Python artifact/hash/update policy.

6. **Pinned semantic npm graph currently includes deprecated transitive `glob@10.5.0`.** `npm ci` emits a deprecation/security-maintenance warning for this transitive package, but all current CI/security/semantic acceptance remains green. Treat this as a post-Stage-25.1 supply-chain follow-up: identify the owning direct dependency and upgrade through a dedicated dependency PR with the full locked acceptance matrix. Do not mutate the dependency graph immediately before the real F16 target-laptop gate merely to silence the warning.

7. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP lifecycle mechanics remain useful diagnostic infrastructure, but generic `tool_schema`/`tool_invoke` is not the accepted ordinary-Chat product surface.

8. **Large typed action surfaces can be truncated in the tested Chat app.** A 34-tool local surface appeared as 20 actions in prior testing. This is measured behavior, not a universal official limit; keep the public semantic surface small.

9. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.** Server-side profile changes do not silently replace a frozen reviewed Chat action snapshot.

10. **OpenAI safety can block composite workflows independently of app permission mode.** Do not confuse a pre-MCP product safety decision with backend failure.

11. **Authorization policy is not fully finalized for future consequential capabilities.** Favor scoped/reversible boundaries and confirmations where consequence justifies them rather than permanent approval friction for every low-risk operation.

12. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs maintenance operations.

13. **Professional application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and broader Windows UI need real workflow benchmarks and scoped promotion.

14. **Repository metadata still contains historical wording.** The GitHub repository description still refers to a removed Rust-first core. Current connector access does not expose a repository-description mutation; code/docs are authoritative until metadata is corrected through an available GitHub UI/API path.

15. **No first stable release exists.** Do not package the current branch as stable until real Stage 25.1 target integration and remaining distribution/reproducibility work are complete.

## Closed / superseded findings

- The scalable five-tool semantic typed projection is implemented and accepted.
- Local inference is no longer merely planned: llama.cpp + LFM2.5-VL-450M F16 passed the Stage 25 target grounding safety benchmark.
- LM Studio/llmster and 450M Q4 are historical research candidates, not the accepted baseline.
- Same-session capture/freshness/coordinate action is proved with one pinned Playwright MCP session; a second browser is unnecessary.
- Layout/scroll/overlay/navigation stale visual evidence and replayed tokens fail closed.
- Windows junction read/write escape attempts are explicitly regression-tested and blocked.
- Tunnel credential inheritance was tested, found real for the semantic stdio child, and closed with scrub-before-core-load launcher + sentinel regression.
- CodeQL now analyzes Actions, JavaScript/TypeScript and Python.
- Dependabot covers Actions, semantic npm and Python requirements.
- Semantic Node dependencies now use a committed lockfile and product/acceptance `npm ci`; unlocked install is refused when dependencies are absent.
- Direct private/link-local/metadata literal network destinations are now rejected before browser navigation while loopback remains available.
- Installed/source split-brain on fixed port 3050 was closed by accepted single-owner/fail-closed lifecycle work. Normal semantic direct stdio does not use port 3050.
