# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Real F16 same-session acceptance is safety-clean but not yet behavior-complete.** The second target-laptop run on HEAD `59b87af94f3482d4f3ab5737ffe3183c83649137` produced a complete six-case result before the old wrapper was manually terminated: 2/3 expected HIT, 3/3 correct ABSTAIN, 0 safe misses, 0 false clicks and 1 infrastructure error. Search icon and state-disambiguated Send were correctly clicked; repeated-row, tiny and absent-target were correctly blocked. The first labeled Send case timed out before inference during the cold runtime `Start` path, so this run does not establish a model miss for that target.

2. **Present-target visual accuracy is still limited.** Accepted Stage 25 evidence remains 3/5 present-target HIT. The Stage 25.1 real run cannot replace that denominator yet because the labeled Send case was lost to the cold-Start infrastructure timeout rather than grounded and scored. Gamma repeated-row and tiny-indicator remain deliberately non-promoted.

3. **Cold runtime `Start` exposed a descendant-stdio settlement defect in the Node runner.** In the real run, llama.cpp loaded the reviewed F16 model/mmproj and listened on `127.0.0.1:3068` about one second after process creation, yet the first `RuntimeBackedVisualGrounder` call consumed the full 150-second child timeout. The llama log shows the first inference only after that timeout, while subsequent warm `Start` calls were fast. The runner previously waited for child `close`, which can be delayed on Windows when a long-lived descendant retains inherited stdio handles. Runtime controller actions now settle on the controller process `exit` after a bounded drain window; a Windows regression reproduces a parent-exited/descendant-stdio-held process tree.

4. **The target wrapper had a real long-run stdout/stderr buffering defect.** `test-stage25-1-real-f16-browser.ps1` redirected Node stdout/stderr but did not drain either pipe until after process exit. The second run wrote its complete `result.json` but still required manual termination of the old wrapper/process path. The wrapper now inherits console output directly and the Node harness emits live per-case progress, removing the buffered-output deadlock class. The next target run must prove clean autonomous exit.

5. **The first target-laptop run's RAM-admission hypothesis was superseded.** The second run started the reviewed runtime successfully under the real Playwright load; a later diagnostic snapshot showed 1.439 GB free physical RAM while the already-running model continued inference. Therefore the `1.50 GB` cold-start threshold must not be lowered merely to address the earlier generic `vision-runtime-start-failed`. Keep the current admission policy unless completed target evidence justifies a change.

6. **Browser network policy is not a complete DNS/redirect sandbox.** Direct literal private/link-local/metadata/non-public destinations are blocked while loopback remains allowed. General hostnames can still resolve/redirect in ways that require a stronger backend/network boundary if future threat models demand it. Playwright origin filters are defense-in-depth only.

7. **Vision Python dependency reproducibility is not yet release-grade.** The current dependency graph is intentionally tiny and exactly pins `Pillow==12.3.0`, but stable distribution still needs an explicit Python artifact/hash/update policy.

8. **Pinned semantic npm graph currently includes deprecated transitive `glob@10.5.0`.** `npm ci` emits a deprecation/security-maintenance warning for this transitive package, but all current CI/security/semantic acceptance remains green. Treat this as a post-Stage-25.1 supply-chain follow-up: identify the owning direct dependency and upgrade through a dedicated dependency PR with the full locked acceptance matrix. Do not mutate the dependency graph immediately before the real F16 target-laptop gate merely to silence the warning.

9. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP lifecycle mechanics remain useful diagnostic infrastructure, but generic `tool_schema`/`tool_invoke` is not the accepted ordinary-Chat product surface.

10. **Large typed action surfaces can be truncated in the tested Chat app.** A 34-tool local surface appeared as 20 actions in prior testing. This is measured behavior, not a universal official limit; keep the public semantic surface small.

11. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.** Server-side profile changes do not silently replace a frozen reviewed Chat action snapshot.

12. **OpenAI safety can block composite workflows independently of app permission mode.** Do not confuse a pre-MCP product safety decision with backend failure.

13. **Authorization policy is not fully finalized for future consequential capabilities.** Favor scoped/reversible boundaries and confirmations where consequence justifies them rather than permanent approval friction for every low-risk operation.

14. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs maintenance operations.

15. **Professional application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and broader Windows UI need real workflow benchmarks and scoped promotion.

16. **Repository metadata still contains historical wording.** The GitHub repository description still refers to a removed Rust-first core. Current connector access does not expose a repository-description mutation; code/docs are authoritative until metadata is corrected through an available GitHub UI/API path.

17. **No first stable release exists.** Do not package the current branch as stable until real Stage 25.1 target integration and remaining distribution/reproducibility work are complete.

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
