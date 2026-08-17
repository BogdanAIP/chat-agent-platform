# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **Visual grounding is not yet integrated into the same live Playwright session.** Stage 25 #73 proved a safe local grounding candidate on a controlled fixture, but production code does not yet prove `same page/session -> capture -> vision -> freshness validation -> action`. A raw VLM coordinate must not be treated as an authorized click.

2. **Present-target visual grounding accuracy is still limited.** Current accepted target evidence is 3/5 present-target HIT with Gamma and tiny-indicator cases safely abstaining. Safety is good; coverage is not yet sufficient to make vision the primary browser grounding path.

3. **Current non-text consistency validation is benchmark-safe but not a complete production verifier.** Zero-overlap two-pass disagreement fails closed, but a single global IoU threshold would break valid inventory-backed text cases. Production validation needs target-class/context-aware policy.

4. **A focused local-vision lifecycle owner is not implemented yet.** The accepted F16 path can reduce free RAM substantially on the target laptop. The model must be started/admitted on demand and unloaded/cleaned deterministically instead of becoming an always-on background service.

5. **Browser stale-state and coordinate-space safety are not yet covered end-to-end.** Layout shift, scroll changes, navigation/page replacement, zoom/device scale, overlays, repeated icons/rows, canvas/WebGL and other visual-only states require integration tests before automatic visual action.

6. **Workspace containment lacks an explicit Windows link/junction regression.** Lexical traversal/absolute-path checks exist, but the project must prove that a permitted root cannot escape through a junction/symlink if the downstream Filesystem implementation changes or behaves unexpectedly.

7. **Browser network reachability policy is not finalized.** `web_open` accepts HTTP/HTTPS and the isolated Playwright profile is not a network sandbox. The project must explicitly decide/test localhost and private-network navigation behavior before visual auto-interaction broadens browser consequences.

8. **Tunnel credential inheritance into child processes is not explicitly regression-tested.** The direct controller temporarily sets `CONTROL_PLANE_API_KEY` for tunnel-client startup. Child semantic/backends should not receive that key unless required; add a negative test rather than assuming tunnel-client strips it.

9. **CodeQL coverage is narrower than the workflow name suggests.** Current CodeQL analyzes GitHub Actions only. The active implementation is primarily Node/Python/PowerShell; Node/Python static analysis and explicit PowerShell checks should be expanded.

10. **Dependency maintenance is incomplete for npm/Python.** Dependabot currently tracks GitHub Actions, while semantic projection uses exact top-level npm pins without a committed lockfile and Stage 25 Python dependency management is minimal. Stable distribution needs reproducible transitive dependency locking/update policy.

11. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP lifecycle mechanics remain useful diagnostic infrastructure, but generic `tool_schema`/`tool_invoke` is not the accepted ordinary-Chat product surface.

12. **Large typed action surfaces can be truncated in the tested Chat app.** A 34-tool local surface appeared as 20 actions in prior testing. This is measured behavior, not a universal official limit; keep the public semantic surface small.

13. **Chat action snapshots require explicit Refresh/review when exported tool definitions change.** Server-side profile changes do not silently replace a frozen reviewed Chat action snapshot.

14. **OpenAI safety can block composite workflows independently of app permission mode.** Do not confuse a pre-MCP product safety decision with backend failure.

15. **Authorization policy is not fully finalized.** Favor scoped/reversible boundaries and confirmations for consequential actions rather than permanent approval friction for every low-risk operation.

16. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs maintenance operations.

17. **Professional application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and broader Windows UI need real workflow benchmarks and scoped promotion.

18. **No first stable release exists.** Current work should not be packaged as a stable release until Stage 25.1 integration, dependency reproducibility and at least one broader capability path stabilize.

## Closed / superseded findings

- The scalable five-tool semantic typed projection is implemented and accepted; it is no longer an open issue.
- Local inference is no longer merely planned: llama.cpp + LFM2.5-VL-450M F16 has passed the Stage 25 target grounding safety benchmark.
- LM Studio/llmster and 450M Q4 remain historical research candidates, not the current accepted grounding runtime/model configuration.
- Installed/source split-brain on fixed port 3050 was closed by accepted single-owner/fail-closed lifecycle work. Normal semantic direct stdio no longer uses port 3050.
