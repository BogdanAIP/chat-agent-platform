# Bridge Acceptance Evidence

This file contains only evidence that actually ran. Target architecture belongs in `ARCHITECTURE.md`; current unresolved work belongs in `CURRENT_STATE.md`.

## 2026-08-10 — reference E2E accepted

The user's ordinary ChatGPT surface completed:

```text
ChatGPT Chat
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official openai/tunnel-client on Windows
  -> local 1MCP
  -> Sequential Thinking MCP
  -> response back to the same ChatGPT conversation
```

This proves the project does not need a custom public gateway, polling relay, VPS/Yandex backend or project-owned MCP aggregation implementation for ordinary ChatGPT ↔ local MCP reachability.

## 2026-08-12 — standalone Windows bootstrap accepted

On the target Windows machine:

- reviewed official tunnel-client artifact/profile path passed;
- standalone manager bundle under LocalAppData installed and verified;
- DPAPI-protected runtime key was reused;
- reference MCP + Secure MCP Tunnel readiness smoke passed;
- cleanup left platform stopped;
- tray remained resident without leaving a separate Windows Terminal/npm/npx console window.

## 2026-08-12 — direct files-readonly ordinary-Chat E2E accepted

The installed manager started exactly one `files-readonly` runtime with MCP and tunnel ready. Ordinary Chat through `Chat Local Bridge Test` read `hello.txt` from the single allowed root and returned exact content:

```text
CHAT_LOCAL_FILES_E2E_OK
```

This accepts the direct read-only Filesystem path.

## 2026-08-12 — browser local readiness accepted, ordinary-Chat call NOT accepted

The manager stopped `files-readonly` and started exactly one `browser-isolated` runtime. Playwright health and MCP/tunnel readiness were green.

However, the already-connected Chat app still exposed only the previously discovered filesystem actions. Therefore no browser call was made through that stale Chat action snapshot.

Evidence conclusion:

- local profile switching works;
- Chat-visible action discovery is not automatically synchronized with local direct-profile switching;
- this is the measured reason for the Stage 24 stable adaptive-surface experiment.

## Adaptive acceptance — NOT PASSED YET

Latest functional CI baseline `9799bec...` proves only partial adaptive behavior:

- adaptive runtime starts;
- `mcp_list` sees disabled Filesystem + Playwright;
- Filesystem enable reaches/loading path;
- transient 503/loading is handled by retry;
- Lazy Loading still fails to publish `read_text_file` before timeout.

Do not cite adaptive Filesystem/Browser invocation, disable cleanup, manager integration or ordinary-Chat one-snapshot behavior as accepted until those tests actually pass.
