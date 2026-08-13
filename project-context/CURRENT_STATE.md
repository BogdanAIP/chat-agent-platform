# Current State

Last synchronized with functional baseline `9799bec20ffeb92eebbba5061f32dff403bbe6f4` on 2026-08-13. Later documentation-only commits do not imply additional runtime acceptance. Always check the current PR HEAD and workflows.

## Accepted bridge

Stage 21 is complete. On 2026-08-10 ordinary ChatGPT successfully completed:

```text
ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client on Windows
  -> 1MCP
  -> Sequential Thinking
  -> result back to ChatGPT
```

Ordinary Chat remains the primary intelligence surface. Codex/Work may accelerate development but are not required product runtime components.

## Accepted module/direct-profile evidence

Stage 23 accepted on Windows through pinned `@1mcp/agent@0.34.4`:

- Filesystem `2026.7.10`: scoped root, write-capable tools hidden, real read call passed;
- Playwright MCP `0.0.78`: isolated/headless browser, navigation/content/close passed.

Stage 24 real-machine evidence already passed:

- standalone bootstrap and official tunnel-client verification;
- DPAPI runtime-key storage and standalone manager bundle;
- reference smoke with MCP + tunnel readiness;
- tray no-console fix: no persistent Windows Terminal/npm/npx window;
- direct `files-readonly` ordinary-Chat E2E returned the exact marker `CHAT_LOCAL_FILES_E2E_OK`;
- local switch to `browser-isolated` produced exactly one active browser profile with MCP/tunnel readiness.

## Chat action snapshot finding

After switching locally from `files-readonly` to `browser-isolated`, the already-connected `Chat Local Bridge Test` still exposed only the earlier `filesystem_*` actions. The browser backend was locally ready, but Chat did not automatically replace the action snapshot.

This invalidated the earlier target of silently switching arbitrary direct tool surfaces behind one already-scanned Chat app. Creating a separate Chat app/plugin snapshot for every future local capability is also rejected as the normal scalable UX.

## Stage 24 adaptive direction — experimental

Current target:

```text
ordinary ChatGPT
  -> one stable Chat-facing MCP action contract
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> one 1MCP runtime
  -> stable Lazy Loading meta-tools
  -> task-driven backend MCP lifecycle
```

Stable Chat-facing lazy tools:

- `tool_list`;
- `tool_schema`;
- `tool_invoke`.

Allowed lifecycle management surface for the pre-approved catalog:

- `mcp_list`;
- `mcp_status`;
- `mcp_enable`;
- `mcp_disable`;
- `mcp_reload`.

Do not publish arbitrary catalog-management tools such as install/uninstall/update/edit/search to ordinary Chat.

### Adaptive runtime configuration

`runtime/chat-profiles/adaptive/mcp.json` currently registers two disabled backends:

- Filesystem MCP `@modelcontextprotocol/server-filesystem@2026.7.10`;
- Playwright MCP `@playwright/mcp@0.0.78`.

Direct profiles remain on accepted `@1mcp/agent@0.34.4`.
Adaptive pins `@1mcp/agent@0.35.0-beta.3`, with Lazy Loading ON and Async Loading OFF, through `runtime/1mcp-adaptive-shim`. The local package verifies the pristine upstream built-file hashes before applying two narrow lifecycle fixes; it is not a project-owned gateway or fork.

Adaptive is supported by the locally installed manager but remains **not the default** and is **not ordinary-Chat accepted**.

## Adaptive blocker diagnosis and local resolution

Functional baseline: `9799bec20ffeb92eebbba5061f32dff403bbe6f4`.

Workflow results:

- `ci`: PASS;
- `CodeQL Security`: PASS;
- `Secret History Scan`: PASS;
- `Chat Profile Acceptance / windows-profiles`: PASS;
- `Chat Profile Acceptance / adaptive-runtime`: FAIL.

Observed adaptive sequence:

1. adaptive 1MCP started and reached runtime readiness;
2. `mcp_list` correctly returned `filesystem` and `playwright`, both `disabled`;
3. Filesystem activation entered backend loading;
4. the acceptance test correctly treated HTTP `503 service_unavailable` + `loading` as transitional;
5. after the wait window, `tool_list({server: "filesystem"})` still returned no tools;
6. failure: `read_text_file` never became visible; observed `tools: []`, `loading retries=49`.

Upstream/source and local runtime evidence resolved the failure boundary:

- synchronous `ServerManager.loadMcpServer` / `unloadMcpServer` did not refresh `LazyLoadingOrchestrator`;
- disable handling read only active transport config, which filters disabled entries, so the backend could not be found and unloaded;
- `0.35.0-beta.4` contains no relevant fix.

The current local compatibility package restores declared disabled entries for lifecycle reconciliation and refreshes only the lazy backend registry after every load attempt/unload. It deliberately does not mutate or notify the frozen top-level Chat tool list.

Local acceptance on 2026-08-13 passed Filesystem and Playwright sequentially in one MCP session: enable, lazy discovery, real read/navigation, disable, catalog retained as disabled, tool removal and process cleanup. The exact eight-tool Chat-facing allowlist remained unchanged across all four transitions, forbidden backend tools were absent, and accepted direct profiles still passed. Commit `3b12fc98e65017d3cd931369813e130119d8d614` then passed all remote runtime/profile/CI/security checks.

The following manager integration then passed locally on the target Windows machine:

- public `SetProfile adaptive` persists one scoped FilesRoot while the safe default remains `reference`;
- interrupted persisted `disabled:false` state resets to the reviewed all-disabled catalog on the next start;
- public status reports adaptive readiness/conflict correctly and Toggle performs cleanup;
- bootstrap installs and verifies adaptive config plus the three-file compatibility package under `%LOCALAPPDATA%`;
- the installed bundle works from outside the source checkout and completes the full same-session acceptance;
- installed adaptive MCP + Secure MCP Tunnel reach readiness, and installed tray/runtime remain resident without a visible Terminal/pwsh/cmd/npm/npx window;
- settings and runtime return to stopped state after acceptance.

Remote CI on the integrated manager head is now required. Adaptive remains opt-in until the final ordinary-Chat gate.

## Safety model

Use three separate concepts:

```text
AVAILABLE
ACTIVE
AUTHORIZED
```

A backend can be registered without running. Start only what the task needs. Multiple backends may be active simultaneously if the workflow actually requires them. Sensitive operations should be scoped/authorized; security must not become a blanket ban on useful multi-tool workflows.

The old direct `files-readonly` and `browser-isolated` separation remains valuable as diagnostic evidence and a conservative fallback, not as a permanent rule that Browser and Filesystem may never coexist.

## Remaining Stage 24 gates

1. keep all final CI/security checks green on the exact integrated manager/bootstrap functional HEAD;
2. real ordinary-Chat acceptance demonstrates that a single Chat-facing contract can use task-selected backends without creating a new plugin or requiring Refresh for every backend;
3. only then accept Stage 24 and integrate/merge to `main`.

## Work after Stage 24

Stage 25 benchmarks real professional modules (REAPER, Origin, FFmpeg, Blender, Windows UI fallback) as replaceable backends behind the stable bridge. Adding one of these backends should not normally require a new ChatGPT plugin/app. Backend processes should be task-driven, not all permanently resident.

## Legacy preservation

The complete pre-cleanup implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`. Historical Yandex/Tailscale paths are not active product dependencies.
