# Evidence Index

## Purpose

This file is the durable index for accepted physical/target evidence. It keeps exact historical SHAs, machine-local result paths and stage-specific measurements out of long-lived architecture/live-context documents unless they define a current invariant.

Use this separation:

```text
ARCHITECTURE.md / CONTROL_PLANE.md
  durable component and authority rules

CURRENT_STATE.md / ROADMAP.md
  current accepted boundary and active direction

EVIDENCE_INDEX.md
  exact accepted heads, result locations and scoped measurements

historical STAGE*.md documents / PR discussions
  detailed qualification design and attempt history
```

Exact code/tests/current CI and the original physical result remain more authoritative than this index. This file is navigation and anti-staleness infrastructure, not a substitute for primary evidence.

## Maintenance rules

- Add a row when a physical/target qualification becomes accepted.
- Keep one concise row per accepted gate; detailed invalid-attempt history belongs in the stage document or PR.
- Never rewrite an accepted SHA to make it look current.
- If later evidence supersedes an older scope, retain the old row and record the newer scope separately.
- Synthetic/unit-policy cases must not be described as physical observations.
- Machine-local result paths are evidence locators, not portable installation requirements.
- Architecture lessons discovered by physical tests move into durable architecture/policy docs; raw counters stay here or in stage evidence.

## Accepted evidence

| Gate | Exact accepted code/qualification head | Physical/target evidence | Scope |
|---|---|---|---|
| Stage 25 local vision benchmark | `5c6f2a5` (recorded by merged #73) | target-laptop grounding benchmark recorded in Stage 25 evidence | bounded browser grounding benchmark; not universal visual accuracy |
| Stage 25.1 same-session vision foundation | `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c` | `%LOCALAPPDATA%\ChatAgentPlatform\stage25\runtime\...` recorded by #74 | local F16 same-session browser foundation |
| Stage 25.2 semantic-first vision escalation | `41ef3f4032ae9169d940b3a04e5bdfe75170ca85` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage25\runtime\stage25-2-public-escalation-20260818-161812\result.json` | bounded semantic-first browser -> local-vision escalation |
| Stage 26.1A OpenAdapt qualification | `f8e8f606db845821b8fa24c09f9032015fb0e79e` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\openadapt-qualification\qualification-20260818-170434\result.json` | pinned Flow/Capture qualification |
| Stage 26.1B Windows Capture | `7a9daa9329d81994833c22b4ca2e321927527dcc` | `%LOCALAPPDATA%\ChatAgentPlatform\stage26\capture-qualification\capture-20260818-194033\result.json` | bounded physical-user capture fixture |
| Stage 26.1C typed Windows executor | `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b` | result recorded in #83 / stage document | hardened typed executor boundary |
| Stage 26.1D warm latency baseline | `114e865090d39d218418958c40cf359b5f6808da` | result recorded in #84 / stage document | desktop-wide UIA bottleneck baseline |
| Stage 26.1E window-scoped UIA | `66390aca1dadf57c4f11568ec311ad6fcdbd7596` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\window-scoped-uia-benchmark\benchmark-20260819-141531\result.json` | controlled WinForms role/name path; scoped UIA replacement for desktop-wide scan |
| Stage 26.2A production Windows runtime | `6ae5c3a9e624c8c341857c025625b203b796b41c` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\production-windows-runtime-benchmark\benchmark-20260819-155739\result.json` | production-owned Windows primitives |
| Stage 26.2B DesktopState | `dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-observation-qualification\observation-20260819-184904\result.json` | bounded exact-window read-only observation |
| Stage 26.2C desktop Grounder | `eadf8ff5a873936441891a66b616c83c62736152` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054\result.json` | proposal-only native-window grounding |
| Stage 26.2D Windows vision routing | `1c74713edcd6321d5583a39234929169e68b5ac1` | result recorded in #90 / stage document | controlled structure-first visual fallback path |
| Stage 26.2E VS Code real-app E2E | `457db0b634f2e47f53d41e359a238840fa3ca2ee` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448` | one isolated VS Code text-edit task with independent verification/rollback |
| Transport Supervisor hard local tunnel kill/recovery | `b03442b66b05bf0f51000ff43f2f386e1495a1ec` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-qualification\run-20260823-115911` | exact owned tunnel killed/replaced; same supervisor; recovery receipt advanced; runtime returned READY; later heartbeat verified |
| Transport Supervisor external network disconnect/reconnect | `5c9e5b7bcd93fa054d99ef449d43d6d12df8c127` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-network-qualification\run-20260823-145633` | local runtime survived offline interval without PID churn; post-reconnect stale remote state caused one bounded runtime recovery then READY |
| Transport Supervisor Windows sleep/resume | `809abf1abd8b8e79fb387feb78f347432229099c` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-sleep-resume-qualification\run-20260823-165435` | physical Modern Standby/resume with stable supervisor/tunnel generations and no recovery churn |
| Transport Supervisor Windows reboot/logon | `27de6f6cec35df9bf0153da034d3c71da2747d44` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-reboot-qualification\run-20260823-180950` | physical reboot/logon lifecycle; final runtime/OpenAI readiness and later supervisor heartbeat verified |
| Transport Supervisor fresh ordinary-Chat post-reboot semantic E2E | `27de6f6cec35df9bf0153da034d3c71da2747d44` | target Windows ordinary ChatGPT / `Chat Local Bridge Test`; challenge/result recorded in PR/stage evidence | same post-reboot runtime served Browser + workspace semantic operations through the accepted route |
| Transport Supervisor idle resources / recovery latency | `61d262fa58a76a03c46acc9e2929de18c69e6506` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-resource-latency-qualification\run-20260823-195439` | physical idle sample + controlled owned tunnel kill/recovery and heartbeat evidence |
| Transport Supervisor console-free Scheduled Task launch | `d54e7f43c3572afd9491311848ce9449bd8e0d7d` | target Windows physical observation during exact supervisor reinstall/start | no new blank console window; installed launcher matched reviewed source; one supervisor; runtime READY |
| Transport Supervisor persistent desired-state / runtime-owner split | `ffa5d83e8a871e36655bdb52098d427ce2505261` | target Windows physical gate; backup locator recorded in PR evidence | Stop persisted stopped across supervisor restart; Start restored running/owner receipt/runtime READY |
| Ordinary-Chat frozen semantic action compatibility | `1b78ae37952c7f7a61b0e3497622395deac661e2` | target Windows ordinary ChatGPT / `Chat Local Bridge Test` | historical action aliases accepted inbound while canonical public inventory remained bounded; no 1MCP hop restored |
| Transport low-power Manual + OFF idle gate (PR #100) | `de0a1b32091ddfa3570c9f49631af2f1f0d4186f` | target Windows interactive physical observation; PR #100 conversation evidence | zero recurring platform runtime/tunnel work during observed Manual+OFF interval |
| Transport low-power Automatic dormant gate (PR #100) | `de0a1b32091ddfa3570c9f49631af2f1f0d4186f` | target Windows interactive physical observation | automatic mode stayed dormant after reconcile while runtime/tunnel remained ready |
| Transport low-power final truthful-green + ordinary-Chat ON/OFF gate (PR #100) | `092081be7d99dbeee6f092a6d48066d1a95e37c2` | PR #100 comments + ordinary ChatGPT / `Chat Local Bridge Test` | green required current local readiness/control-plane poll; Chat route succeeded ON and failed before local execution OFF |
| Stage 26.3A normal six-tool ordinary-Chat verified procedure runtime | `300db9956dfbdf0300ecc59f017d6f3280d4353a` | target Windows ordinary ChatGPT / `Chat Local Bridge Test`; workspace/result locators recorded in #92/stage evidence | all six semantic tools in one long-horizon task; verified artifact procedure completed then zero-overwrite abstention independently proved |
| Stage 26.3B file/artifact shared-kernel integration (PR #102) | `35b5a6c5b53c4fb5b423872b7d8b1afc8b18df98` | target-Windows ordinary-Chat completion + zero-overwrite gate recorded in #102 | rooted/race-aware file observation + shared Verification Kernel + independent Finish Gate; public six-tool surface preserved |
| Stage 26.3B production `web_open` verification (PR #107) | `64184713e97bf2e150614cd93c77509c244cddec` | ordinary-Chat target-Windows physical browser regression recorded in #107 | exact navigation final-state verification; delivered redirect with wrong postcondition fails closed |
| Stage 26.3B production `web_interact` verification (PR #111) | `1521e3128a7694be43518c3ee0188cb79f0ca0f5` | ordinary-Chat target-Windows physical regression recorded in #111 | fresh BEFORE/AFTER ExpectedEffect verification; already-satisfied/missing expected produces zero action; delivery alone is not success |
| Stage 26.3B Browser real-task L3 historical scope (PR #113) | `5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf` | target Windows ordinary ChatGPT randomized Case Desk + independent checker | exact target final state, one target save, one target audit mutation, `FINISH_GATE=done`, `NON_TARGET_MUTATION=none`; source-provenance closure later strengthened by #118 |
| Stage 26.3B Windows `DesktopState` shared-kernel verification (PR #114) | `ce3f533d12ab0a5ea0c9a4804accb32cf377ac0e` | target-Windows physical verifier qualification recorded in #114 | live process/HWND identity, freshness, positive PASS, wrong-effect FAIL, generation/HWND drift FAIL and stale/non-advancing UNKNOWN |
| Stage 26.3B Windows/application real-task L3 (PR #115) | `5ae5d5ac52f391b1a58662e94a976c6ab8d48c62` | target-Windows ordinary ChatGPT Case Desk + frozen Finish Gate recorded in #115 | five bounded verified transitions; exact target final state; unchanged decoys; exactly one intended save/mutation; source/install/runtime provenance; cleanup; `EXTERNAL_FINISH_GATE=DONE` |
| Stage 26.3B Browser stronger source-provenance repeat (PR #118) | `e29517fdf1c940d36bc822cfcc1a729ed7dd9574` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\stage26-3b-browser-real-task-20260828-005002-8BE43853` | target-Windows ordinary-Chat randomized Case Desk through six tools; source/install/full exact-lock Node tree revalidated after Browser actions; atomic frozen snapshot; target-only mutation history; `SAVE_COUNT=1`; `AUDIT_COUNT=1`; decoys unchanged; `EXTERNAL_FINISH_GATE=DONE`; fixture/guardian cleanup PASS. Accepted Browser route is headless Playwright/Chrome, not a visible headed-desktop Browser claim. |

## Not yet accepted / future scope

The following remain future work and must not be represented as accepted merely because adjacent foundation exists:

- Stage 26.3C WorkingState + typed recovery/reconciliation + LoopGuard/StagnationReport;
- broad cross-application Windows/Browser/Electron/Office accuracy;
- trusted-site full-browser/JS/CDP authority and complete Browser Network Gate;
- generic Local Execution Kernel / arbitrary Python authority;
- Track M Agent Session / Delegation runtime and multi-worker orchestration;
- release-grade distribution/maintenance and clean-user stable release.

Transport-call latency optimization is not a current acceptance blocker unless product evidence makes it one.

## Evidence-to-architecture rule

Physical tests frequently discover durable architecture facts. Keep the distinction explicit:

```text
physical observation
  -> exact evidence stays in this index / stage record
  -> generalized safety/architecture lesson is promoted to ARCHITECTURE.md or CONTROL_PLANE.md
  -> current development implication is reflected in CURRENT_STATE.md / ROADMAP.md
```

Examples:

- VS Code/Monaco proved that focused semantic identity and top-level native window geometry are separate evidence channels.
- Browser #118 proved that planner self-report is not completion evidence; independent audit/Finish Gate history remains authoritative.
- Browser #118 also exposed that runtime diagnostic output must be owned explicitly rather than inheriting arbitrary source CWD; the accepted run isolated runtime CWD and permanent hardening is tracked separately.
