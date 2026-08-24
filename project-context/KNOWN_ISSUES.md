# Known Issues

Only unresolved issues for the **current** architecture are listed here. Historical findings that are now closed are summarized at the end.

1. **Present-target browser visual capability remains intentionally limited.** Stage 25 blocks difficult/repeated/tiny classes rather than promoting unsafe clicks.

2. **Browser screenshot -> coordinate action is not atomic.** Freshness is rechecked, but capture and action remain separate calls with a narrow TOCTOU window.

3. **Loopback vision endpoint ownership is PID-checked, not cryptographically authenticated.** A same-user process/port race remains theoretically possible.

4. **Browser network policy is not a complete DNS/redirect sandbox.** DNS rebinding/redirect/private-network isolation remains residual work.

5. **Python/model/OpenAdapt dependency reproducibility is not release-grade.** Stable distribution still needs exact artifact/hash/update policy rather than relying on user-global Python environments.

6. **Pinned semantic npm graph includes deprecated transitive dependencies.** Keep dependency remediation separate from capability architecture changes and rerun the full acceptance matrix after any graph change.

7. **Generic adaptive Chat-facing actions remain unaccepted.** 1MCP is now an optional internal Extension Manager; generic `tool_schema` / `tool_invoke` and raw backend catalogs are not the ordinary-Chat product contract.

8. **Large exported action surfaces can be truncated or become difficult to govern in ChatGPT.** Keep the public semantic surface small and project-owned. The current normal public inventory is exactly six tools: `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`, `procedure_run`.

9. **ChatGPT MCP app definitions are frozen snapshots and do not automatically track the live server.** Existing app instances may keep historical action IDs or schemas after runtime upgrades. The launcher can rewrite a bounded stale inbound `tools/call` name, but it cannot update ChatGPT's frozen action snapshot, connection state or permissions before a call reaches MCP. See `SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md`.

10. **A local READY route is not proof that the current ChatGPT app binding is usable.** On 2026-08-24 the normal six-tool physical route was `runtime_ready=true`, `mcp_ready=true`, `tunnel_ready=true`, `active_profile=semantic`, `tunnel_binding=direct-stdio`, and a fresh ordinary-Chat `workspace_read` succeeded. The next `workspace_write` reached ChatGPT's confirmation UI, then ChatGPT transitioned into `Connect / Add Chat Local Bridge Test` and the message ended with a stream error. This is an unresolved product-side app snapshot/connection/permission-session blocker; it is not evidence that the local semantic runtime crashed.

11. **Final Stage 26.3A ordinary-Chat acceptance therefore still requires an explicitly synchronized app binding.** Complete/review the current app connection and six-action snapshot before the long test, settle the intended permission mode before execution, then start a fresh conversation. Do not change app connection or permission policy mid-acceptance run.

12. **Write/modify confirmation policy can interrupt long autonomous tasks.** `workspace_write`, `web_interact` and `procedure_run` are intentionally annotated as mutating/destructive-capable actions. If ChatGPT is configured to ask for approval, a long-horizon test is not autonomous even when the local runtime is healthy. Permission policy must be decided explicitly by the user before a long unattended run.

13. **Authorization policy is not accepted for arbitrary Windows consequence classes.** Stage 26.2E proves one harmless isolated real-app VS Code text edit, not universal desktop authority.

14. **Runtime-key rotation/repair/uninstall are not complete first-class lifecycle flows yet.** Distribution hardening remains Stage 27 work.

15. **OpenAdapt procedural substrate is qualified but broader procedural-memory integration is incomplete.** Stage 26.3A now has a real deterministic `procedure_run` Control Plane slice, but general ProgramGraph reuse, learned procedure retrieval/promotion and transferable skill lifecycle remain later work.

16. **The first procedure must not silently become generally product-trusted.** Stage 26.3A admits only the explicitly registered bounded `verified_workspace_artifact_v1` candidate path. Adding procedures requires separate policy/evidence rather than generic dispatch.

17. **Human demonstration privacy/retention is unresolved.** Long-lived arbitrary desktop capture is not accepted until deletion, encryption and redaction policy is defined and tested.

18. **Private reasoning must never enter task/procedural memory.** Store structured/user-visible goal summaries, observed state, transitions, receipts and verification only.

19. **The 97/97 Stage 26.1E fixture result is not global Windows accuracy.** It proves one controlled role+name path; real apps/custom controls require separate evidence.

20. **`AutomationId` lacks dedicated accepted physical coverage across varied real applications.** Do not claim broad structural reliability from synthetic tests alone.

21. **One real-application E2E is not broad Windows coverage.** Stage 26.2E physically passed isolated VS Code, but OriginPro/Reaper/custom apps and other control shapes remain separately unqualified.

22. **Arbitrary human “show me once” transfer is not accepted.** Capture/compiler candidates exist; candidate trust, verifier-controlled replay and changed-task reuse remain Stage 26.4 work.

23. **Public desktop capability names are still intentionally undecided.** The current public semantic surface already contains six tools because `procedure_run` is now explicit. Future Windows/computer-use exposure still requires a dedicated ADR; do not overload `web_interact` or publish raw backend tool catalogs merely to preserve a count.

24. **Specialized tiny reasoning is not committed to the release path.** TRM/STARM/FPRM or another structured reasoner is optional after real verified procedure-state data and measured need.

25. **Future local general planning is deliberately deferred, not rejected.** Track P remains non-release-critical shadow/proposal research and may never bypass deterministic authorization/verifier boundaries.

26. **Multi-chat orchestration is a separate upper layer.** It is not Windows/procedure safety core and must not become a substitute for the deterministic Control Plane.

27. **No first stable release exists.** Final ordinary-Chat Stage 26.3A acceptance, verified reuse, distribution hardening and clean-user release gates remain incomplete.

28. **Normal bootstrap can reuse a locally verified pinned tunnel-client, but first installation still needs the upstream release path.** The 2026-08-24 physical run exposed a transient GitHub Release API `Unicorn` response; the bootstrap now avoids that dependency when the installed v0.0.11 binary and metadata hashes already verify. Supply-chain checks must remain fail-closed when local evidence does not match.

29. **Compatibility aliases are migration debt, not a permanent contract.** The launcher currently retains exact inbound mappings for historical `semantic-projection_1mcp_*` and former `procedure-qualification-projection_1mcp_*` snapshots. Remove them only after a newly created or explicitly rebound ChatGPT app proves stable canonical six-tool calls across read, write, browser and `procedure_run`.

## Closed / superseded findings

- Stage 25.1/25.2 browser semantic/vision foundations are merged/accepted; historical candidate-runtime rankings no longer define the active path.
- The assumption that Stage 26 must build its own recorder/compiler/skill store from scratch is superseded by exact OpenAdapt Flow/Capture qualification.
- Stage 26.1B bounded Windows Capture passed at `7a9daa9329d81994833c22b4ca2e321927527dcc`.
- Stage 26.1C bounded Windows executor passed at `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b`.
- Stage 26.1D isolated desktop-wide UIA traversal as the ~184 s blocker.
- Stage 26.1E replaced desktop-wide resolution with bounded exact-window UIA and passed the controlled scoped suite.
- Stage 26.2A promoted the accepted Windows executor/resolver into maintained runtime code.
- Stage 26.2B added canonical bounded `DesktopState` observation.
- Stage 26.2C added the proposal-only native Desktop Grounder.
- Stage 26.2D added bounded deterministic Windows UIA -> vision routing.
- Stage 26.2E physically accepted one isolated VS Code real-application E2E on exact runtime head `457db0b634f2e47f53d41e359a238840fa3ca2ee`.
- Transport Supervisor v1 is accepted and merged through PR #94; desired-state/runtime-owner split, console-free Scheduled Task launch and bounded recovery are no longer open architecture gaps.
- The normal Stage 26.3A route is now direct stdio and does not require 1MCP for bootstrap/start/status/health/smoke.
- The deterministic Stage 26.3A Control Plane slice is implemented: the canonical public surface contains six tools and `procedure_run` admits only the registered bounded `verified_workspace_artifact_v1` procedure.
- The old separate `procedure-qualification` public profile/route is removed. Stage 26.3A final acceptance uses the normal `semantic` route.
- The persistent tunnel id is now neutral platform state in `state/tunnel.json`; legacy `local-1mcp.yaml` is migration fallback only.
- The baseline installed bundle excludes adaptive/1MCP runtime assets; optional 1MCP regression lives in `Optional Extension Manager Acceptance`.
- A transient GitHub Release API failure no longer blocks bootstrap when the already installed pinned tunnel-client can be independently verified from local metadata and hashes.
