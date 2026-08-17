# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Real F16 visual grounding is not yet wired into the same-session browser bridge.** The same-session capture/freshness/action boundary, focused llama.cpp lifecycle owner and model-neutral production grounder are each implemented/proved separately, but the real runtime-backed chain has not yet run end-to-end.

2. **Present-target visual accuracy is still limited.** Accepted target evidence remains 3/5 present-target HIT. Gamma repeated-row and tiny-indicator cases safely abstain and are deliberately not promoted for production clicks.

3. **The target laptop has not yet run the final Stage 25.1 production chain.** Synthetic lifecycle and deterministic bridge tests are green, but the exact real path `Chrome -> same-session PNG -> reviewed F16 runtime -> production authorization -> freshness -> action/ABSTAIN` still requires target Windows acceptance.

4. **Browser network policy is not a complete DNS/redirect sandbox.** Direct literal private/link-local/metadata/non-public destinations are blocked while loopback remains allowed. General hostnames can still resolve/redirect in ways that require a stronger backend/network boundary if future threat models demand it. Playwright origin filters are defense-in-depth only.

5. **Vision Python dependency reproducibility is not yet release-grade.** The current dependency graph is intentionally tiny and exactly pins `Pillow==12.3.0`, but stable distribution still needs an explicit Python artifact/hash/update policy.

6. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP lifecycle mechanics remain useful diagnostic infrastructure, but generic `tool_schema`/`tool_invoke` is not the accepted ordinary-Chat product surface.

7. **Large typed action surfaces can be truncated in the tested Chat app.** A 34-tool local surface appeared as 20 actions in prior testing. This is measured behavior, not a universal official limit; keep the public semantic surface small.

8. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.** Server-side profile changes do not silently replace a frozen reviewed Chat action snapshot.

9. **OpenAI safety can block composite workflows independently of app permission mode.** Do not confuse a pre-MCP product safety decision with backend failure.

10. **Authorization policy is not fully finalized for future consequential capabilities.** Favor scoped/reversible boundaries and confirmations where consequence justifies them rather than permanent approval friction for every low-risk operation.

11. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs maintenance operations.

12. **Professional application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and broader Windows UI need real workflow benchmarks and scoped promotion.

13. **Repository metadata still contains historical wording.** The GitHub repository description still refers to a removed Rust-first core. Current connector access does not expose a repository-description mutation; code/docs are authoritative until metadata is corrected through an available GitHub UI/API path.

14. **No first stable release exists.** Do not package the current branch as stable until real Stage 25.1 target integration and remaining distribution/reproducibility work are complete.

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
