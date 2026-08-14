# Stage 24 — Windows lifecycle + scalable typed ordinary-Chat capability surface

This file describes the current Stage 24 scope. Earlier Stage 24 work began with mutually exclusive direct profiles and then evaluated a generic adaptive Lazy Loading surface. Real ordinary-Chat evidence changed the product target again: direct/combined concrete typed actions work, while the generic adaptive lifecycle/schema/invocation surface is not product-accepted.

## Goal

Keep the accepted bridge:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP / focused local adapters
  -> replaceable local capabilities
```

and make it practical on Windows without introducing another AI planner, custom cloud ingress, project-owned generic gateway or mandatory paid service.

Stage 24 must also solve capability scaling: future Browser/Files/REAPER/Origin/FFmpeg/Blender/vision backends should not require one separate ChatGPT app/plugin each or hundreds of simultaneously published tools.

## Accepted direct profiles

### `files-readonly`

- one Filesystem MCP;
- one explicit existing workspace root;
- broad/system roots rejected;
- create/write/edit/move disabled;
- real ordinary-Chat read E2E passed.

### `browser-isolated`

- one Playwright MCP;
- isolated/headless Chrome;
- unsafe code/evaluate/file-upload/direct-network tools disabled;
- local MCP/tunnel readiness passed;
- fresh ordinary-Chat typed `browser_navigate` E2E passed.

These profiles intentionally isolate capability classes for deterministic acceptance and conservative fallback. They do **not** define a permanent rule that legitimate workflows may never use multiple backends together.

## Measured Chat action behavior

### Frozen snapshot / refresh

After the local runtime switched successfully from `files-readonly` to `browser-isolated`, the existing Chat app still exposed the previously scanned filesystem actions. Refresh/new Chat was required to see the Browser surface.

Current OpenAI documentation likewise describes ChatGPT MCP app tools as a frozen reviewed snapshot: later server-side tool changes are not automatically enabled. Therefore local profile lifecycle and Chat action discovery are separate concerns, and 1MCP tags/presets/runtime filtering do not by themselves make an already-scanned app acquire new typed actions.

OpenAI Tool Search is relevant to large tool ecosystems in the API/Agents SDK, but it is not currently documented as available to the ordinary-Chat custom-MCP-app path used by this project. Stage 24 must not depend on it.

### Large typed surface pressure

A synthetic combined runtime exposed:

- 14 Filesystem typed actions;
- 20 Playwright typed actions;
- 34 local typed actions total.

The tested Chat app effectively surfaced 20 actions: all 14 Filesystem plus the first 6 Playwright actions. Later Playwright tools including `browser_navigate` and `browser_click` were unavailable.

A discriminator reduced Filesystem to 4 typed actions while keeping all 20 Playwright actions, for a 24-tool local total. After Refresh/new Chat, ordinary Chat successfully used typed Filesystem + Browser actions including `browser_navigate` and `browser_click`.

This is evidence of an **effective ~20-action snapshot truncation in the tested app**, not an officially documented universal OpenAI limit.

## Adaptive runtime — diagnostic, not accepted product contract

Current adaptive catalog contains disabled Filesystem + Playwright backends. The runtime line is `@1mcp/agent@0.35.0-beta.3`, Lazy Loading ON, Async Loading OFF, plus a hash-guarded compatibility package.

The local/CI lifecycle evidence is strong:

- Filesystem and Playwright each enable;
- approved lazy tools appear;
- real harmless operations execute;
- disable removes the backend capability;
- backend processes clean up;
- the exact generic top-level surface remains frozen.

However, the real ordinary-Chat generic-surface test saw the eight actions but only list/status/discovery calls reached MCP. Lifecycle plus `tool_schema`/`tool_invoke` were blocked before MCP execution.

Therefore Stage 24 does **not** promote generic adaptive invocation as the ordinary-Chat product boundary. Keep it as diagnostic/lifecycle infrastructure.

The exact OpenAI pre-MCP cause is not isolated. Do not claim one annotation alone caused it and do not mislabel the generic dispatcher to bypass review.

## Accepted typed multi-backend ordinary-Chat evidence

On synthetic scoped data, one ordinary Chat using one `Chat Local Bridge Test` app successfully executed:

- `list_allowed_directories`;
- `read_text_file`;
- `write_file`;
- `browser_navigate`;
- `browser_find`;
- `browser_click`;
- final file reread.

The browser transitioned from `example.com` to IANA and reported title `Example Domains`; the written marker was read back exactly.

No `tool_invoke`, `tool_schema`, `mcp_enable`, `mcp_disable` or `mcp_reload` was used.

This proves Filesystem + Browser are not inherently incompatible in one ordinary-Chat workflow when concrete typed actions are visible.

## Capability/lifecycle security model

Use:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

- registration does not imply a running process;
- activation follows the current task;
- sensitive operations remain scoped/confirmed as appropriate;
- sequential activation saves resources when task stages are sequential;
- multiple backends may remain active together when the workflow actually requires them.

Authorization should not mean a permission dialog for every low-risk step. Prefer scoped roots/workspaces, backups/git/rollback and bounded tools; reserve explicit confirmation for genuinely consequential/hard-to-reverse effects where practical.

Real Chat permission testing showed `Allow read actions` prompting once for isolated `write_file`, while `Allow all actions` allowed typed read/navigate/write without cards. OpenAI safety can still block a larger composite workflow under full access, so permission mode is not the only safety layer.

## Windows lifecycle manager — accepted for the measured split-brain defect

The thin manager remains:

```text
chat-platform.ps1
  -> serialized public lifecycle facade
  -> chat-platform-controller.ps1

chat-platform-tray.ps1
  -> UI only
  -> consumes manager/controller status
```

A real split-brain defect was found: the installed LocalAppData copy could leave a 1MCP runtime on `127.0.0.1:3050` while the source checkout believed its own known scopes were stopped.

The public manager now uses shared `%LOCALAPPDATA%\ChatAgentPlatform\state\manager-owner.json`, cross-copy lifecycle delegation and fail-closed behavior when the fixed MCP port is occupied without trustworthy ownership.

Target Windows acceptance on 2026-08-14 passed:

- installed start and source observation;
- installed -> source takeover;
- source observation from the installed copy;
- source -> installed takeover;
- foreign-owner Stop/cleanup;
- exactly one `3050` listener in each running state;
- fail-closed handling for an unrelated listener on `3050`.

The occupied-port diagnostic formatting defect found by the negative test was fixed in `923d2f9...`. Functional head `ffcc2e407...` adds a real Windows CI foreign-listener test and passes CI, Chat Profile Acceptance, Module Candidate Acceptance, CodeQL and Secret History Scan.

The measured installed/source split-brain blocker is closed. The foreign-owner `Toggle` branch remains regression-covered but was not separately repeated as a dedicated target-machine user action.

## Current typed scaling target — PROVISIONAL

The desired boundary is:

```text
ordinary ChatGPT
  -> small stable set of concrete semantic typed actions
  -> capability projection onto the larger approved local catalog
  -> tunnel / 1MCP / focused adapters
  -> replaceable task-active backends
```

The projection is a compatibility boundary, not a planner. It may map a fixed semantic action to one reviewed backend operation or a small deterministic backend sequence.

Requirements:

- preserve fixed truthful JSON schemas and side-effect semantics;
- keep each Chat-facing action within a coherent consequence/authorization class;
- route deterministically to approved backend capabilities;
- do not create one Chat app/plugin per backend;
- do not publish hundreds of unrelated tools simultaneously;
- do not hide arbitrary operations behind one opaque generic dispatcher or renamed `tool_invoke`;
- do not hard-code the observed ~20 action count as a universal constant;
- keep the project-owned projection as small/deterministic as possible;
- keep ChatGPT, not the local layer, as the planner.

## Stage 24 acceptance criteria

1. direct reference/files/browser regressions stay green;
2. adaptive Filesystem/Playwright local/CI lifecycle remains green as diagnostic infrastructure;
3. generic adaptive meta-tools are explicitly not promoted as the product contract;
4. installed/source manager copies coordinate one authoritative owner and stale foreign readiness cannot satisfy startup — **DONE**;
5. target-machine single-owner/fail-closed acceptance — **DONE**;
6. the scalable Chat-facing projection preserves concrete typed semantics and accommodates the observed frozen-snapshot/action-pressure constraint;
7. real ordinary Chat proves useful multi-backend operation through one product app without per-backend app creation, routine per-operation Refresh or opaque generic invocation;
8. exact final functional HEAD passes CI, Chat Profile Acceptance, Module Candidate Acceptance, CodeQL and Secret History Scan;
9. docs/PR evidence match that exact head;
10. only then Stage 24 is accepted and integrated to `main`.

## Outside Stage 24 unless required by acceptance

- authenticated browser-session reuse;
- arbitrary shell/PowerShell exposure;
- Windows desktop automation as a baseline;
- automatic installation of arbitrary MCP servers from ordinary Chat;
- generic workflow/policy/secret platform;
- mandatory paid cloud/browser service;
- production local model runtime/vision integration (planned for Stage 25).
