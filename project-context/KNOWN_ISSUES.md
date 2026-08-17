# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **The real local VLM is not yet connected to the same-session browser bridge.** Windows CI proves the bridge with an injected deterministic grounder, but `semantic-projection` does not yet invoke the real llama.cpp/LFM2.5-VL-450M F16 path or automatically escalate `web_interact`.

2. **Present-target visual grounding accuracy is still limited.** Current accepted target evidence is 3/5 present-target HIT. Repeated-row Gamma and tiny-indicator cases safely abstain and remain explicitly unpromoted for production action.

3. **Real target-laptop lifecycle acceptance is still pending.** The focused runtime owner passes synthetic Windows lifecycle acceptance, but the real F16 model must still prove start/admission/health/idle-unload/cleanup with realistic Chrome usage on the target laptop.

4. **The current exact-screenshot freshness policy may over-abstain on dynamic pages.** It is safely strict and passes layout/scroll/overlay/navigation stale-state tests. Relax it only after a measured deterministic alternative exists.

5. **Tunnel credential inheritance into semantic/downstream child processes is not explicitly regression-tested.** The direct controller temporarily sets `CONTROL_PLANE_API_KEY` for tunnel-client startup. Test this boundary and scrub downstream environments if necessary rather than assuming the tunnel strips it.

6. **Browser localhost/private-network scope policy is not yet explicit enough.** `web_open` intentionally supports HTTP/HTTPS and accepted local-web workflows use localhost. The isolated Playwright profile is not a network sandbox. Define/test the scope without breaking intended local web capability, and keep vision from autonomously expanding navigation scope.

7. **Semantic npm dependencies are not reproducibly locked.** Exact top-level pins exist, but runtime/bootstrap/CI still use `npm install --package-lock=false`. Generate and commit a real lockfile, validate it, then move reviewed paths to `npm ci`.

8. **Python dependency reproducibility is minimal.** Stage 25 currently has a very small pinned requirements file, but release-grade dependency/update policy is still needed.

9. **Canvas/WebGL and hostile prompt-like on-screen text need additional visual fallback coverage.** Core stale-state safety is already proved for layout shift, scroll, overlay and navigation replacement.

10. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP lifecycle mechanics remain useful diagnostic infrastructure, but generic `tool_schema`/`tool_invoke` is not the accepted ordinary-Chat product surface.

11. **Large typed action surfaces can be truncated in the tested Chat app.** A 34-tool local surface appeared as 20 actions in prior testing. Keep the public semantic surface small.

12. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.** Server-side changes do not silently replace a frozen reviewed Chat action snapshot.

13. **OpenAI safety can block composite workflows independently of app permission mode.** Do not confuse a pre-MCP product safety decision with backend failure.

14. **Authorization policy is not fully finalized.** Favor scoped/reversible boundaries and confirmations for consequential actions rather than permanent approval friction for every low-risk operation.

15. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs maintenance operations.

16. **Professional application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and broader Windows UI need real workflow benchmarks and scoped promotion.

17. **No first stable release exists.** Do not package Stage 25.1 as stable before real-VLM browser integration, reproducible dependencies and at least one broader capability path stabilize.

## Closed / proved findings

- The scalable exact five-tool semantic typed projection is implemented and accepted.
- Local inference is no longer merely planned: llama.cpp + LFM2.5-VL-450M F16 passed the Stage 25 target grounding safety benchmark.
- LM Studio/llmster and 450M Q4 are historical research candidates, not the current accepted grounding baseline.
- Normal semantic direct stdio no longer depends on port 3050/1MCP.
- Same-session visual capture/freshness/coordinate action is proved without a second browser or unrestricted `browser_evaluate`.
- Replay, layout shift, scroll, overlay, navigation/page replacement, missing and ambiguous visual results all fail closed with no coordinate action.
- A focused vision-runtime owner is implemented and passes synthetic Windows lifecycle/tamper/foreign-process/ownership tests.
- A class-aware production grounding promotion policy exists; repeated-row and tiny targets remain forced ABSTAIN.
- Real Windows junction read/write escape from the allowed workspace did not reproduce on the current pinned Filesystem MCP stack; regression stays in CI.
- CodeQL now covers Actions, JavaScript/TypeScript and Python, and Dependabot now monitors Actions/npm/pip.
