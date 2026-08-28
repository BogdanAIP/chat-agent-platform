# Evidence Index

## Purpose

This is the durable index for **accepted physical/target evidence**. It keeps exact historical qualification heads, machine-local result paths and scoped physical measurements out of live architecture/state documents.

Use this separation:

```text
ARCHITECTURE.md / CONTROL_PLANE.md
  durable architecture/authority rules

CURRENT_STATE.md / ROADMAP.md
  current accepted boundary / release direction

EVIDENCE_INDEX.md
  exact accepted physical/target heads, result locations and scoped measurements

Stage records / PR discussions
  detailed qualification design and invalid-attempt history
```

Exact code/tests/current CI and original physical results remain more authoritative than this navigation index.

## Maintenance rules

- Add a row only when a physical/target qualification becomes accepted.
- Keep one concise row per accepted gate; invalid-attempt detail belongs in Stage/PR records.
- Never rewrite a historical accepted SHA to make it look current.
- Retain older scope when newer evidence strengthens/supersedes it; add a new row.
- Synthetic/unit/state-machine acceptance is **not** physical evidence and must not be inserted into this table as if it were.
- Machine-local paths are evidence locators, not portable product requirements.
- Promote generalized lessons into architecture/policy owners; keep raw counters/locators here.

## Accepted physical / target evidence

| Gate | Exact accepted code/qualification head | Physical/target evidence | Scope |
|---|---|---|---|
| Stage 25 local vision benchmark | `5c6f2a5` | target-laptop benchmark recorded in Stage 25 evidence | bounded Browser grounding benchmark; not universal visual accuracy |
| Stage 25.1 same-session vision foundation | `edebbc9eda58637b2c9ea95fcab9f9fc4438fe6c` | `%LOCALAPPDATA%\ChatAgentPlatform\stage25\runtime\...` | local F16 same-session Browser foundation |
| Stage 25.2 semantic-first vision escalation | `41ef3f4032ae9169d940b3a04e5bdfe75170ca85` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage25\runtime\stage25-2-public-escalation-20260818-161812\result.json` | bounded semantic-first Browser -> local-vision escalation |
| Stage 26.1A OpenAdapt qualification | `f8e8f606db845821b8fa24c09f9032015fb0e79e` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\openadapt-qualification\qualification-20260818-170434\result.json` | pinned Flow/Capture qualification |
| Stage 26.1B Windows Capture | `7a9daa9329d81994833c22b4ca2e321927527dcc` | `%LOCALAPPDATA%\ChatAgentPlatform\stage26\capture-qualification\capture-20260818-194033\result.json` | bounded physical-user capture fixture |
| Stage 26.1C typed Windows executor | `4bf08dd9b8d1ff010f14723f9bb0384b97334a2b` | recorded in #83 / Stage record | hardened typed executor boundary |
| Stage 26.1D warm latency baseline | `114e865090d39d218418958c40cf359b5f6808da` | recorded in #84 / Stage record | desktop-wide UIA bottleneck baseline |
| Stage 26.1E window-scoped UIA | `66390aca1dadf57c4f11568ec311ad6fcdbd7596` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\window-scoped-uia-benchmark\benchmark-20260819-141531\result.json` | controlled WinForms role/name path |
| Stage 26.2A production Windows runtime | `6ae5c3a9e624c8c341857c025625b203b796b41c` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\production-windows-runtime-benchmark\benchmark-20260819-155739\result.json` | production-owned Windows primitives |
| Stage 26.2B DesktopState | `dcf20a7b15a4e0a353b1e75be50d4a2cbaa66c0a` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-observation-qualification\observation-20260819-184904\result.json` | bounded exact-window read-only observation |
| Stage 26.2C Desktop Grounder | `eadf8ff5a873936441891a66b616c83c62736152` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\desktop-grounder-qualification\grounder-20260820-050054\result.json` | proposal-only native-window grounding |
| Stage 26.2D Windows vision routing | `1c74713edcd6321d5583a39234929169e68b5ac1` | recorded in #90 / Stage record | controlled structure-first visual fallback path |
| Stage 26.2E VS Code real-app E2E | `457db0b634f2e47f53d41e359a238840fa3ca2ee` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\real-app-e2e\vscode-20260821-171448` | isolated VS Code text-edit task with independent artifact verification/rollback |
| Transport Supervisor hard tunnel kill/recovery | `b03442b66b05bf0f51000ff43f2f386e1495a1ec` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-qualification\run-20260823-115911` | owned tunnel killed/replaced; same supervisor; recovery receipt advanced; runtime READY |
| Transport Supervisor external network disconnect/reconnect | `5c9e5b7bcd93fa054d99ef449d43d6d12df8c127` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-network-qualification\run-20260823-145633` | local runtime survived offline interval; bounded post-reconnect recovery |
| Transport Supervisor sleep/resume | `809abf1abd8b8e79fb387feb78f347432229099c` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-sleep-resume-qualification\run-20260823-165435` | physical Modern Standby/resume with stable generations/no churn |
| Transport Supervisor reboot/logon | `27de6f6cec35df9bf0153da034d3c71da2747d44` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-reboot-qualification\run-20260823-180950` | physical reboot/logon; final runtime/OpenAI readiness + later heartbeat |
| Post-reboot ordinary-Chat semantic E2E | `27de6f6cec35df9bf0153da034d3c71da2747d44` | target Windows ordinary ChatGPT / `Chat Local Bridge Test` | same post-reboot runtime served Browser + workspace semantics |
| Transport idle resources / recovery latency | `61d262fa58a76a03c46acc9e2929de18c69e6506` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\transport-supervisor-resource-latency-qualification\run-20260823-195439` | physical idle sample + controlled tunnel kill/recovery |
| Transport console-free Scheduled Task launch | `d54e7f43c3572afd9491311848ce9449bd8e0d7d` | target-Windows physical observation | no new blank console; installed launcher matched reviewed source; runtime READY |
| Transport persistent desired-state/runtime-owner split | `ffa5d83e8a871e36655bdb52098d427ce2505261` | target-Windows physical gate | Stop persisted across supervisor restart; Start restored running/owner receipt/runtime READY |
| Ordinary-Chat frozen semantic action compatibility | `1b78ae37952c7f7a61b0e3497622395deac661e2` | target Windows ordinary ChatGPT / `Chat Local Bridge Test` | historical inbound action aliases worked while public inventory stayed bounded |
| Transport low-power Manual + OFF idle gate (#100) | `de0a1b32091ddfa3570c9f49631af2f1f0d4186f` | target-Windows interactive physical observation | zero recurring platform runtime/tunnel work during observed Manual+OFF interval |
| Transport low-power Automatic dormant gate (#100) | `de0a1b32091ddfa3570c9f49631af2f1f0d4186f` | target-Windows interactive physical observation | automatic mode dormant while runtime/tunnel remained ready |
| Transport low-power final truthful-green + ordinary-Chat ON/OFF (#100) | `092081be7d99dbeee6f092a6d48066d1a95e37c2` | #100 comments + ordinary ChatGPT / `Chat Local Bridge Test` | green required current readiness/control-plane poll; Chat succeeded ON and failed before local execution OFF |
| Stage 26.3A six-tool ordinary-Chat Verified Procedure Runtime | `300db9956dfbdf0300ecc59f017d6f3280d4353a` | target Windows ordinary ChatGPT / `Chat Local Bridge Test` | all six tools in one long-horizon task; verified artifact complete + zero-overwrite abstention independently proved |
| Stage 26.3B file/artifact shared-kernel integration (#102) | `35b5a6c5b53c4fb5b423872b7d8b1afc8b18df98` | target-Windows ordinary-Chat gate in #102 | rooted/race-aware file observation + shared Kernel + independent Finish Gate; six-tool surface preserved |
| Stage 26.3B `web_open` verification (#107) | `64184713e97bf2e150614cd93c77509c244cddec` | ordinary-Chat target-Windows Browser regression | exact navigation final-state verification; wrong redirect postcondition fails closed |
| Stage 26.3B `web_interact` verification (#111) | `1521e3128a7694be43518c3ee0188cb79f0ca0f5` | ordinary-Chat target-Windows Browser regression | fresh BEFORE/AFTER ExpectedEffect; already-satisfied/missing expected causes zero action |
| Stage 26.3B Browser real-task L3 historical scope (#113) | `5bb8897c6809cecd15f64da1a8ef6efd2fdf69bf` | target Windows ordinary ChatGPT randomized Case Desk + checker | exact target final state, one save/audit mutation, decoys unchanged; provenance later strengthened #118 |
| Stage 26.3B Windows DesktopState shared-kernel verification (#114) | `ce3f533d12ab0a5ea0c9a4804accb32cf377ac0e` | target-Windows physical verifier qualification | process/HWND identity/freshness; PASS/FAIL/UNKNOWN/generation drift cases |
| Stage 26.3B Windows/application real-task L3 (#115) | `5ae5d5ac52f391b1a58662e94a976c6ab8d48c62` | target-Windows ordinary ChatGPT Case Desk + frozen Finish Gate | five bounded verified transitions; exact target state; unchanged decoys; source/install/runtime provenance; cleanup; external DONE |
| Stage 26.3B Browser stronger source-provenance repeat (#118) | `e29517fdf1c940d36bc822cfcc1a729ed7dd9574` | `C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\stage26-3b-browser-real-task-20260828-005002-8BE43853` | six-tool randomized Browser task; source/install/full exact-lock dependency tree revalidated after actions; atomic frozen snapshot; target-only mutation history; cleanup PASS |

## Accepted non-physical foundations

Some accepted architecture/runtime foundations are intentionally absent from the physical table because their accepting PR did not change a production consequence path and required deterministic/hosted evidence only.

Most importantly:

- PR #124 accepted the Stage 26.3C **WorkingState / typed reconciliation / budgets / LoopGuard / StagnationReport L1 foundation** with deterministic/adversarial state-machine evidence.

Do **not** misread the absence of a physical row as “WorkingState does not exist”. Conversely, do not promote the #124 L1 foundation into a claim that production crash/restart effects are physically accepted.

## Not yet physically/production accepted

Future or incomplete evidence scopes include:

- Stage 26.3C **production** WorkingState/restart-reconciliation integration on consequence-bearing procedures/capabilities and broader cross-capability physical qualification;
- broad cross-application Windows/Browser/Electron/Office reliability;
- trusted-site full-browser/JS/CDP authority and complete Browser Network Gate;
- generic Local Execution Kernel / arbitrary Python authority;
- Track M Agent Session/Delegation runtime and multi-worker orchestration;
- release-grade distribution/maintenance and clean-user stable release.

A consequence-bearing Stage 26.3C production integration must earn its own target-Windows physical qualification before merge when the path changes real effects. Its active PR/design state belongs in `CURRENT_STATE.md`, not this evidence ledger.

## Evidence-to-architecture rule

```text
physical observation
 -> exact head/result stays here / Stage record
 -> generalized architecture/security lesson moves to its owner document
 -> current development implication moves to CURRENT_STATE.md / ROADMAP.md
```

Examples:

- VS Code/Monaco demonstrated that focused semantic identity and top-level native window geometry are separate evidence channels.
- Browser #118 demonstrated that planner self-report is not completion evidence and source/runtime provenance can invalidate an otherwise plausible run.
- Browser #118 also exposed that runtime diagnostic output must be owned explicitly rather than inherit arbitrary source CWD; permanent hardening is tracked as technical debt.
