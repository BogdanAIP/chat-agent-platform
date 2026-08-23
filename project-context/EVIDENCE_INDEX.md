# Evidence Index

## Purpose

This file is the durable index for accepted physical/target evidence. It exists to keep exact historical SHAs, machine-local result paths and stage-specific measurements out of the long-lived architecture documents unless they are needed to define a current invariant.

Use this separation:

```text
ARCHITECTURE.md / CONTROL_PLANE.md
  durable component and authority rules

CURRENT_STATE.md / ROADMAP.md
  current accepted boundary, active work and residual risks

EVIDENCE_INDEX.md
  exact accepted heads, result locations and scoped measurements

historical STAGE*.md documents
  detailed qualification design/history for the named stage only
```

Exact code/tests/current CI and the original physical result remain more authoritative than this index. This file is a navigation and anti-staleness layer, not a substitute for primary evidence.

## Maintenance rules

- Add a row when a physical/target qualification becomes accepted.
- Keep one concise row per accepted gate; detailed attempt history remains in the stage document or PR.
- Never change an accepted SHA to make it look current. Acceptance is always scoped to the exact tested head.
- If a later test supersedes an accepted gate, retain the old row and mark it superseded with the replacement evidence.
- Synthetic/unit-policy cases must not be described as physical observations.
- Machine-local result paths are evidence locators, not portable installation requirements.
- Architecture-changing lessons discovered by physical tests must be copied into the durable architecture document as invariants; the raw counters stay here/stage evidence.

## Accepted evidence

| Gate | Exact accepted code/qualification head | Physical/target evidence | Scope |
|---|---|---|---|
| Stage 25 local vision benchmark | `5c6f2a5` (recorded by merged #73) | target-laptop grounding benchmark recorded in Stage 25 evidence | bounded browser grounding benchmark; not universal visual accuracy |
| Stage 25.1 same-session vision foundation | `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c` | `%LOCALAPPDATA%\ChatAgentPlatform\stage25\runtime\...` recorded by #74 | local F16 same-session browser foundation |
| Stage 25.2 semantic-first vision escalation | `41ef3f4032ae9169d940b3a04e5bdfe75170ca85` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage25\runtime\stage25-2-public-escalation-20260818-161812\result.json` | five-tool browser semantic->vision path |
| Stage 26.1A OpenAdapt qualification | `f8e8f606db845821b8fa24c09f9032015fb0e79e` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\openadapt-qualification\qualification-20260818-170434\result.json` | pinned Flow/Capture qualification |
| Stage 26.1B Windows Capture | `7a9daa9329d81994833c22b4ca2e321927527dcc` | `%LOCALAPPDATA%\ChatAgentPlatform\stage26\capture-qualification\capture-20260818-194033\result.json` | bounded physical-user capture fixture |
| Stage 26.1C typed Windows executor | `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b` | result recorded in #83 / stage document | hardened typed executor boundary |
| Stage 26.1D warm latency baseline | `114e865090d39d218418958c40cf359b5f6808da` | result recorded in #84 / stage document | desktop-wide UIA bottleneck baseline |
| Stage 26.1E window-scoped UIA | `66390aca1dadf57c4f11568ec311ad6fcdbd7596` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\window-scoped-uia-benchmark\benchmark-20260819-141531\result.json` | controlled WinForms role/name path; 97 scoped resolutions |
| Stage 26.2A production Windows runtime | `6ae5c3a9e624c8c341857c025625b203b796b41c` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\production-windows-runtime-benchmark\benchmark-20260819-155739\result.json` | production-owned Windows primitives |
| Stage 26.2B DesktopState | `dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-observation-qualification\observation-20260819-184904\result.json` | bounded exact-window read-only observation |
| Stage 26.2C desktop Grounder | `eadf8ff5a873936441891a66b616c83c62736152` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054\result.json` | proposal-only native-window grounding |
| Stage 26.2D Windows vision routing | `1c74713edcd6321d5583a39234929169e68b5ac1` | result recorded in #90 / stage document | one controlled structure-first visual fallback path |
| Stage 26.2E VS Code real-app E2E | `457db0b634f2e47f53d41e359a238840fa3ca2ee` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448` | one isolated VS Code text-edit task with independent verification/rollback |
| Transport Supervisor hard local tunnel kill/recovery | `b03442b66b05bf0f51000ff43f2f386e1495a1ec` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-qualification\run-20260823-115911` | exact owned tunnel PID `6812` killed; replacement PID `4828`; same supervisor PID; recovery receipt `0 -> 1`; runtime returned `READY`; later supervisor heartbeat verified |
| Transport Supervisor external network disconnect/reconnect | `5c9e5b7bcd93fa054d99ef449d43d6d12df8c127` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-network-qualification\run-20260823-145633` | 45 s offline observation: local runtime stayed ready with no supervisor/tunnel PID churn and no recovery increase; after reconnect supervisor PID `19872` stayed stable, stale control-plane state became `REMOTE_TUNNEL_DISCONNECTED -> restart_runtime`, tunnel PID `19664 -> 15156`, recovery `0 -> 1`, then final `READY` / `openai_ready=true`; stored run was a false-negative only because the superseded harness required zero post-reconnect recovery |
| Transport Supervisor Windows sleep/resume | `809abf1abd8b8e79fb387feb78f347432229099c` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-sleep-resume-qualification\run-20260823-165435` | physical Modern Standby `506 -> 507`, verified `20.329 s`; desired running state preserved; supervisor PID `3904` stable; tunnel PID `3540` stable; seamless resume with recovery `0 -> 0`; runtime/OpenAI readiness and later supervisor heartbeat verified after required external VPN/network path was restored before confirmation |
| Ordinary-Chat frozen semantic action compatibility | `1b78ae37952c7f7a61b0e3497622395deac661e2` | target Windows ordinary ChatGPT / `Chat Local Bridge Test`: `workspace_read` reached Filesystem and returned exact-path `ENOENT`; `web_open(example.com)` succeeded; `web_observe` returned `Example Domain` | five exact legacy `_1mcp_` action IDs accepted as inbound aliases while public `tools/list` remains canonical five; no 1MCP hop restored |

## Not yet accepted

The following are current work and must not be added to the accepted table until their own gates pass:

- Stage 26.3 Verified Procedure Runtime / ordinary-Chat autonomous multi-transition execution (#92);
- remaining Transport Supervisor v1 (#94) gates: reboot/logon, fresh ordinary-Chat E2E, idle resource/latency evidence and final product-integration cleanup;
- broad cross-application Windows accuracy;
- release-grade distribution/maintenance and clean-user stable release.

## Evidence-to-architecture rule

Physical tests frequently discover durable architecture facts. Keep the distinction explicit:

```text
physical observation
  -> exact evidence stays in this index / stage record
  -> generalized safety/architecture lesson is promoted to ARCHITECTURE.md or CONTROL_PLANE.md
  -> current development implication is reflected in CURRENT_STATE.md / ROADMAP.md
```

Example: VS Code/Monaco proved that a real keyboard target can be a hidden/zero-size focused accessibility textbox. The exact run belongs in this evidence index; the durable rule is that focused semantic identity and top-level native window geometry are separate evidence channels.
