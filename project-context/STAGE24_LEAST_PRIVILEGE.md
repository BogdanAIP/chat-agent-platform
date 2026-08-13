# Stage 24 — Windows lifecycle + adaptive ordinary-Chat capability surface

This file describes the current Stage 24 scope. Earlier Stage 24 work began with mutually exclusive direct profiles; real Chat action-snapshot evidence changed the target architecture. Direct profiles remain accepted diagnostics/fallback, while the scalable adaptive path is still experimental.

## Goal

Keep the accepted bridge:

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> local 1MCP
  -> replaceable local MCP backends
```

and make it practical on Windows without introducing another AI planner, custom cloud ingress, project-owned generic gateway or mandatory paid service.

Stage 24 must also solve capability scaling: future Browser/Files/REAPER/Origin/FFmpeg/Blender backends should not require one separate ChatGPT app/plugin each.

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
- local MCP/tunnel readiness passed.

These profiles intentionally isolate capability classes for deterministic acceptance and conservative fallback. They do **not** define a permanent rule that legitimate workflows may never use multiple backends together.

## Measured snapshot problem

After the local runtime switched successfully from `files-readonly` to `browser-isolated`, the existing Chat app still exposed the previously scanned filesystem actions.

Therefore:

- local profile lifecycle and Chat action discovery are separate concerns;
- silently swapping direct tool surfaces behind one scanned Chat app is unreliable;
- one frozen Chat app/plugin per backend does not scale.

## Adaptive target — not yet accepted

Stage 24 now evaluates a stable 1MCP Lazy Loading surface:

```text
tool_list
tool_schema
tool_invoke
```

plus only lifecycle controls for a locally pre-approved catalog:

```text
mcp_list
mcp_status
mcp_enable
mcp_disable
mcp_reload
```

Ordinary Chat must not receive arbitrary catalog install/uninstall/update/edit/search controls.

Current adaptive catalog contains disabled Filesystem + Playwright backends. The experimental runtime line is `@1mcp/agent@0.35.0-beta.3`, Lazy Loading ON, Async Loading OFF. Direct profiles remain on accepted `0.34.4`.

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

Avoid an unnecessarily broad always-on local-data + open-network baseline. Do not turn that into a blanket prohibition on useful combinations.

## Windows lifecycle manager

The accepted thin manager remains:

```text
chat-platform.ps1
  -> serialized public lifecycle facade
  -> chat-platform-controller.ps1

chat-platform-tray.ps1
  -> UI only
  -> consumes manager/controller status
```

Bootstrap installs the verified official tunnel-client and standalone manager bundle under LocalAppData, stores the runtime key through DPAPI, creates the official tunnel profile through `tunnel-client init`, runs a reference readiness smoke test and leaves the platform stopped.

Adaptive is now installed as an opt-in manager profile with a required scoped FilesRoot. `reference` remains the default until ordinary-Chat acceptance.

## Adaptive runtime evidence

The previous functional baseline failed after Filesystem enable because beta.3's synchronous lifecycle never refreshed the lazy registry. Source/runtime diagnosis also found that disable reconciliation lost disabled entries before unloading them.

The current hash-guarded compatibility package fixes only those two upstream gaps. Local 2026-08-13 acceptance now proves:

- Filesystem and Playwright each enable, publish approved lazy tools, execute a real harmless operation and disable in one MCP session;
- forbidden filesystem/browser tools are absent at runtime;
- the exact eight-tool top-level Chat surface does not change across lifecycle transitions;
- catalog entries remain pre-approved but disabled after unload;
- backend processes are gone after disable;
- direct fallback profiles still switch and start successfully.

Commit `3b12fc9...` passed the initial adaptive runtime, direct profiles, CI and security remotely. The installed manager/bootstrap/tunnel/no-console path then passed locally. Integrated head `19ba303...` passed Chat Profile Acceptance, CI, module candidates, CodeQL and Secret History Scan. Only the ordinary-Chat one-snapshot E2E remains. The compatibility package is not a new broker and must fail closed if the pinned upstream files drift.

## Stage 24 acceptance criteria

1. direct reference/files/browser regressions stay green;
2. adaptive Filesystem enable -> ready -> lazy discovery -> read -> disable -> cleanup passes in one MCP session;
3. adaptive Playwright enable -> ready -> lazy discovery -> navigate -> close -> disable -> cleanup passes under the same stable contract;
4. only approved lazy/lifecycle tools are Chat-facing;
5. adaptive lifecycle is integrated into standalone manager/bootstrap/status/start/stop/toggle/tray without visible console regression;
6. exact final functional HEAD passes CI, Chat Profile Acceptance, CodeQL and Secret History Scan;
7. real ordinary Chat proves one stable action snapshot can select/use backends without per-backend plugin creation or routine Refresh;
8. only then Stage 24 is accepted and integrated to `main`.

## Outside Stage 24 unless required by the acceptance above

- authenticated browser-session reuse;
- general filesystem writes;
- arbitrary shell/PowerShell exposure;
- Windows desktop automation as a baseline;
- automatic installation of arbitrary MCP servers from ordinary Chat;
- generic workflow/policy/secret platform;
- mandatory paid cloud/browser service.
