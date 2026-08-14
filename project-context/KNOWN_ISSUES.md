# Known Issues

Only unresolved issues for the current bridge architecture are listed here.

1. **The generic adaptive Chat-facing contract is not product-accepted.** Adaptive 1MCP lifecycle mechanics are green locally/remotely, but real ordinary Chat blocked lifecycle plus `tool_schema`/`tool_invoke` before MCP while read-only list/status/discovery calls worked. The exact product-admission cause is not isolated; do not weaken truthful annotations to bypass it.

2. **Large typed action surfaces are effectively truncated in the tested Chat app.** A 34-tool local surface appeared as 20 Chat-facing actions; a reduced 24-tool local surface allowed later Playwright actions such as `browser_navigate`/`browser_click` to become callable. This is measured behavior, not an officially documented universal 20-tool limit. The scalable typed publication mechanism is still unresolved.

3. **Chat action snapshots still require explicit refresh/new-chat behavior when the published typed surface changes.** Local backend/profile changes alone do not guarantee an already-scanned Chat app sees the new action set. Official OpenAI documentation describes MCP app tools as a frozen reviewed snapshot. 1MCP tags/presets/filtering can narrow local runtime exposure but do not by themselves update that snapshot. The final scaling design must avoid routine user Refresh work.

4. **OpenAI Tool Search is not currently a documented escape hatch for this ordinary-Chat custom MCP path.** Tool Search is documented for the OpenAI API/Agents SDK and is architecturally relevant to large tool ecosystems, but Stage 24 must not assume that capability exists in the user's ordinary Chat app surface until the product path actually exposes and accepts it.

5. **OpenAI safety can block composite workflows independently of app permission mode.** Under `Allow all actions`, one long local-file -> browser -> write workflow was blocked even though the same typed `read_text_file`, `browser_navigate` and `write_file` calls passed sequentially. The exact safety heuristic is external/opaque and must not be confused with local backend failure.

6. **Authorization policy is not finalized.** `Allow read actions` correctly produced a one-time approval card for isolated `write_file`, but permanent per-write/per-click confirmation would create unacceptable approval friction. The final policy should combine scoped/reversible local boundaries with confirmation for genuinely consequential effects.

7. **The scalable semantic typed capability projection is not implemented yet.** The strongest current direction is a small stable set of concrete semantic actions with truthful schemas/consequence classes projected onto a larger approved backend catalog. It must not become a second planner, generic gateway or renamed `tool_invoke`.

8. **npm execution is top-level version pinned but not fully dependency locked for stable distribution.** Later distribution hardening should move normal lifecycle away from repeated `npx -y` dependency resolution.

9. **Runtime-key rotation/repair/uninstall are not first-class manager flows yet.** DPAPI storage exists; stable distribution still needs explicit maintenance operations.

10. **Professional application candidates are not product-accepted.** REAPER, Origin, FFmpeg, Blender and Windows UI require real workflow benchmarks and scoped promotion.

11. **Local inference is planned but unaccepted.** LM Studio/`llmster` is the first runtime-manager candidate and `LiquidAI/LFM2.5-VL-3B` is the first preferred vision candidate, but target Windows model/runtime/quantization benchmarks have not run yet.

12. **Universal ChatGPT plan/product availability must not be promised.** The user's actual surface passes the required tunnel/typed-tool tests, but Chat product capabilities and limits may vary/change.

13. **No first stable release exists.** Old release machinery belonged to the superseded universal binary; the new release format should package only the thin bridge plus accepted focused capability/runtime assets after behavior stabilizes.

14. **Repository maintenance cleanup remains.** Historical feature branches/superseded PRs can be pruned after the active Stage 24 work is accepted.

## Closed on 2026-08-14

The installed/source split-brain on fixed port `3050` is no longer an open issue. Real target-machine installed -> source -> installed handoff/status/stop passed, an unowned foreign `3050` listener is fail-closed, and functional head `ffcc2e407...` adds a real Windows occupied-port regression with the full CI/profile/security suite green.
