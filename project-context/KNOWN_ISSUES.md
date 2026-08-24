# Known Issues

Only unresolved issues for the **current** architecture are listed here. Historical findings that are now closed are summarized at the end.

1. **Present-target browser visual capability remains intentionally limited.** Stage 25 blocks difficult/repeated/tiny classes rather than promoting unsafe clicks.

2. **Browser screenshot -> coordinate action is not atomic.** Freshness is rechecked, but capture and action remain separate calls with a narrow TOCTOU window.

3. **Loopback vision endpoint ownership is PID-checked, not cryptographically authenticated.** A same-user process/port race remains theoretically possible.

4. **Browser network policy is not a complete DNS/redirect sandbox.** DNS rebinding/redirect/private-network isolation remains residual work.

5. **Python/model/OpenAdapt dependency reproducibility is not release-grade.** Stable distribution still needs exact artifact/hash/update policy rather than relying on user-global Python environments.

6. **Pinned semantic npm graph includes deprecated transitive dependencies.** Keep dependency remediation separate from capability architecture changes and rerun the full acceptance matrix after any graph change.

7. **Generic adaptive Chat-facing actions remain unaccepted.** 1MCP is an optional internal Extension Manager; generic `tool_schema` / `tool_invoke` and raw backend catalogs are not the ordinary-Chat product contract.

8. **Large exported action surfaces can be truncated or become difficult to govern in ChatGPT.** Keep the public semantic surface small and project-owned. The accepted normal public inventory is exactly six tools: `workspace_read`, `workspace_write`, `web_open`, `web_observe`, `web_interact`, `procedure_run`.

9. **ChatGPT MCP app definitions are frozen snapshots and do not automatically track the live server.** Existing app instances may keep historical action IDs or schemas after runtime upgrades. The launcher can rewrite a bounded stale inbound `tools/call` name, but it cannot update ChatGPT's frozen action snapshot, connection state or permissions before a call reaches MCP. The accepted Stage 26.3A run established the operational rule: synchronize/reconnect the app and settle the intended permission mode before a long run; do not change app binding/permissions mid-task. See `SEMANTIC_FROZEN_ACTION_COMPATIBILITY.md`.

10. **Compatibility aliases are migration debt, not a permanent contract.** The launcher currently retains exact inbound mappings for historical `semantic-projection_1mcp_*` and former `procedure-qualification-projection_1mcp_*` snapshots. Remove them only after a newly created or explicitly rebound ChatGPT app proves stable canonical six-tool calls across read, write, browser and `procedure_run`.

11. **Authorization policy is not accepted for arbitrary Windows consequence classes.** Stage 26.2E proves one harmless isolated real-app VS Code text edit, not universal desktop authority.

12. **Runtime-key rotation/repair/uninstall are not complete first-class lifecycle flows yet.** Distribution hardening remains Stage 27 work.

13. **OpenAdapt procedural substrate is qualified but broader procedural-memory integration is incomplete.** Stage 26.3A physically accepts one deterministic `procedure_run` Control Plane slice, but general ProgramGraph reuse, learned procedure retrieval/promotion and transferable skill lifecycle remain later work.

14. **The first procedure must not silently become generally product-trusted.** Stage 26.3A admits only the explicitly registered bounded `verified_workspace_artifact_v1` candidate path. Adding procedures requires separate policy/evidence rather than generic dispatch.

15. **Advanced completion verification remains incomplete.** Stage 26.3A proves one bounded file artifact procedure with exact content/object verification. Stage 26.3B must broaden postconditions for browser/UI/application/process/window/structured-output states without treating action delivery as completion.

16. **Human demonstration privacy/retention is unresolved.** Long-lived arbitrary desktop capture is not accepted until deletion, encryption and redaction policy is defined and tested.

17. **Private reasoning must never enter task/procedural memory.** Store structured/user-visible goal summaries, observed state, transitions, receipts and verification only.

18. **The 97/97 Stage 26.1E fixture result is not global Windows accuracy.** It proves one controlled role+name path; real apps/custom controls require separate evidence.

19. **`AutomationId` lacks dedicated accepted physical coverage across varied real applications.** Do not claim broad structural reliability from synthetic tests alone.

20. **One real-application E2E is not broad Windows coverage.** Stage 26.2E physically passed isolated VS Code, but OriginPro/Reaper/custom apps and other control shapes remain separately unqualified.

21. **Arbitrary human “show me once” transfer is not accepted.** Capture/compiler candidates exist; candidate trust, verifier-controlled replay and changed-task reuse remain Stage 26.4 work.

22. **Public desktop capability names are still intentionally undecided.** The accepted public semantic surface contains six tools because `procedure_run` is explicit. Future Windows/computer-use exposure still requires a dedicated ADR; do not overload `web_interact` or publish raw backend tool catalogs merely to preserve a count.

23. **Specialized tiny reasoning is not committed to the release path.** TRM/STARM/FPRM or another structured reasoner is optional after real verified procedure-state data and measured need.

24. **Future local general planning is deliberately deferred, not rejected.** Track P remains non-release-critical shadow/proposal research and may never bypass deterministic authorization/verifier boundaries.

25. **Multi-chat orchestration is a separate upper layer.** It is not Windows/procedure safety core and must not become a substitute for the deterministic Control Plane.

26. **No first stable release exists.** Stage 26.3B/26.4, distribution hardening and clean-user release gates remain incomplete.

27. **Normal bootstrap can reuse a locally verified pinned tunnel-client, but first installation still needs the upstream release path.** The 2026-08-24 physical run exposed a transient GitHub Release API `Unicorn` response; bootstrap now avoids that dependency when the installed v0.0.11 binary and metadata hashes already verify. Supply-chain checks remain fail-closed when local evidence does not match.

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
- The normal Stage 26.3A route is direct stdio and does not require 1MCP for bootstrap/start/status/health/smoke.
- The deterministic Stage 26.3A Control Plane slice is implemented and physically accepted on exact runtime head `300db9956dfbdf0300ecc59f017d6f3280d4353a`.
- The old separate `procedure-qualification` public profile/route is removed. Stage 26.3A acceptance used the normal `semantic` route.
- The persistent tunnel id is neutral platform state in `state/tunnel.json`; legacy `local-1mcp.yaml` is migration fallback only.
- The baseline installed bundle excludes adaptive/1MCP runtime assets; optional 1MCP regression lives in `Optional Extension Manager Acceptance`.
- A transient GitHub Release API failure no longer blocks bootstrap when the already installed pinned tunnel-client can be independently verified from local metadata and hashes.
- The 2026-08-24 ChatGPT reconnect/permission-session interruption is closed as a Stage 26.3A blocker: after reconnecting `Chat Local Bridge Test`, setting app-specific `Allow all actions` before the run, and starting a fresh conversation, the full long-horizon six-tool ordinary-Chat E2E completed successfully.
- Stage 26.3A zero-overwrite is physically accepted: first procedure task `497ecb591779219ef0ee1e55ea7ad0b8` completed three verified actions; second task `02b09a4909b6d71e0578c19b2d395cb8` abstained at preflight with `action_count=0` and `target_already_exists`; independent reread proved unchanged content/SHA.
