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
| Transport Supervisor Windows reboot/logon | `27de6f6cec35df9bf0153da034d3c71da2747d44` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-reboot-qualification\run-20260823-180950` | physical reboot proven by boot time `2026-08-22T03:21:03Z -> 2026-08-23T15:31:36.5Z`; current-user task principal SID and logon trigger verified; post-logon supervisor PID `8176`, tunnel PID `14480`; bounded recovery delta `+1`; final runtime/OpenAI readiness and later supervisor heartbeat verified. First Verify attempt exposed locale-dependent DateTime parsing only; rerun with `en-US` culture passed without mutating platform state. |
| Transport Supervisor fresh ordinary-Chat post-reboot semantic E2E | `27de6f6cec35df9bf0153da034d3c71da2747d44` | target Windows ordinary ChatGPT / `Chat Local Bridge Test`; challenge nonce `CHATGPT_POST_REBOOT_E2E_FD724E488E864D06A2A19867949FA77D` created at `2026-08-23T15:54:49.4949688Z` under the configured workspace | same post-reboot runtime served `web_open(https://example.com)` + `web_observe` -> `Example Domain`; initial `workspace_read` was blocked by an external OpenAI safety layer before tool execution, then without any platform mutation a workspace-only diagnostic passed `roots`, `search`, and `read_text`, returning the exact fresh nonce from `chatgpt-e2e-challenge.txt`; no Chat Local Bridge Test tools other than the requested semantic tools were used |
| Transport Supervisor idle resources / recovery latency | `61d262fa58a76a03c46acc9e2929de18c69e6506` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-resource-latency-qualification\run-20260823-195439` | 60 s physical idle sample kept supervisor PID `8176` and tunnel PID `9672` stable; average whole-machine CPU `0.0195%` supervisor and `0.0065%` tunnel; working sets `29,151,232` and `23,207,936` bytes; controlled exact owned tunnel kill `9672 -> 5904`; same supervisor PID; receipt `0 -> 1`; runtime/OpenAI `READY`; heartbeat verified; committed recovery transaction latency `48,428.476 ms` |
| Transport Supervisor console-free Scheduled Task launch | `d54e7f43c3572afd9491311848ce9449bd8e0d7d` | target Windows physical observation during exact supervisor reinstall/start | no new blank PowerShell/console window visibly flashed or remained open; task action used `wscript.exe`; installed launcher SHA256 matched reviewed source; exactly one supervisor process; runtime/OpenAI remained `READY` |
| Transport Supervisor persistent desired-state / runtime-owner split | `ffa5d83e8a871e36655bdb52098d427ce2505261` | target Windows physical gate; backup locator `C:\Users\eahra\AppData\Local\ChatAgentPlatform\desired-state-qualification-backup-20260823-210501` | legacy running installation migrated to `desired-state.json`; user Stop persisted `stopped` while owner receipt was absent; explicit supervisor restart PID `9180 -> 5080` did not resurrect runtime; user Start restored `running`, owner receipt, single supervisor, runtime/OpenAI `READY` |
| Ordinary-Chat frozen semantic action compatibility | `1b78ae37952c7f7a61b0e3497622395deac661e2` | target Windows ordinary ChatGPT / `Chat Local Bridge Test`: `workspace_read` reached Filesystem and returned exact-path `ENOENT`; `web_open(example.com)` succeeded; `web_observe` returned `Example Domain` | five exact legacy `_1mcp_` action IDs accepted as inbound aliases while public `tools/list` remains canonical five; no 1MCP hop restored |

## Not yet accepted

The following are current work and must not be added to the accepted table until their own gates pass:

- Stage 26.3 Verified Procedure Runtime / ordinary-Chat autonomous multi-transition execution (#92);
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
