# Stage 23 Module Catalog

Research snapshot: 2026-08-10.

Status meanings:

- **ACCEPTED-CANDIDATE** — quality/cost/licensing look strong enough for technical acceptance tests; not automatically exposed to ChatGPT yet.
- **LOCAL-TEST-REQUIRED** — promising but must be tested against the user's real installed application before promotion.
- **THIN-ADAPTER** — prefer a small project-owned MCP wrapper around an official local API/CLI.
- **RESEARCH** — no candidate promoted yet.

| Capability | Candidate | Cost model | License / owner | Status | Decision |
|---|---|---|---|---|---|
| MCP aggregation | `@1mcp/agent@0.34.4` | local, no SaaS required | Apache-2.0, 1mcp-app | accepted infrastructure | Keep. Already passed ChatGPT E2E through Secure MCP Tunnel. |
| Files | `@modelcontextprotocol/server-filesystem@2026.7.10` | local, free | MIT in server README, Model Context Protocol project | ACCEPTED-CANDIDATE | Use scoped roots. Candidate profile disables create/write/edit/move so Stage 23 tests are read-only. |
| Browser | `@playwright/mcp@0.0.78` | local, free | Apache-2.0, Microsoft | ACCEPTED-CANDIDATE | Best current browser foundation: structured accessibility snapshots, isolated/headless test mode, no paid browser cloud required. Production permissions belong to Stage 24. |
| Windows desktop fallback | `sbroenne/mcp-windows` v1.3.18 | local, free | MIT | LOCAL-TEST-REQUIRED | Strong fallback because it uses Windows UI Automation by semantic element names. High privilege; never default until Stage 24 and real Origin/REAPER tests. |
| REAPER | `TwelveTake-Studios/reaper-mcp` v1.6.4 | local, free beyond REAPER itself | MIT | LOCAL-TEST-REQUIRED | Primary REAPER candidate. 176 tools and maintained file-based bridge. Benchmark on real project before considering old project code. |
| OriginPro | official `originpro` external Python API | no extra service fee beyond installed Origin | OriginLab vendor API | THIN-ADAPTER | Prefer a small MCP adapter over UI automation. Official API reads/writes data and creates/exports graphs via Origin Automation Server COM; requires Origin 2021+. |
| FFmpeg/media | native FFmpeg CLI | local, free | FFmpeg project | THIN-ADAPTER | Do not adopt a weak arbitrary-command MCP. First search further; if no mature constrained MCP exists, expose only a small allowlisted media tool set. |
| Blender | existing Blender MCP ecosystem | local candidates exist | varies | RESEARCH | Compare maintained projects and tool surface before selecting one. No project-owned Blender layer yet. |
| GitHub | existing ChatGPT GitHub connection | existing product connection | external connector | do not duplicate | Do not route GitHub through the laptop unless a local Git operation specifically requires it. |

## Primary-source evidence

### 1MCP

Repository: `https://github.com/1mcp-app/agent`

- Apache-2.0.
- Aggregates multiple MCP servers.
- Supports server tags/filters, progressive/lazy discovery, environment substitution and per-server `disabledTools`.
- Current repository main is already ahead on a beta line; the bridge remains pinned to the accepted stable `0.34.4` until a deliberate upgrade test.

### Filesystem MCP

Repository: `https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem`
Package channel: `https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem`

- npm package: `@modelcontextprotocol/server-filesystem`.
- Published stable version selected for tests: `2026.7.10`.
- The source-tree package metadata may be ahead/behind the npm release numbering; install pinning follows the real npm supply channel, not an unreleased source-tree version string.
- Supports explicit allowed directories / MCP Roots.
- Tools carry read-only/destructive annotations.
- README license: MIT.

### Microsoft Playwright MCP

Repository: `https://github.com/microsoft/playwright-mcp`
Package channel: `https://www.npmjs.com/package/@playwright/mcp`

- Apache-2.0.
- Published stable version selected for tests: `0.0.78`.
- Repository `main` package metadata was observed ahead at `0.0.79`; that unreleased source version is not used as an install pin.
- Uses structured accessibility snapshots rather than pixel-only interaction.
- Supports headless, isolated profiles, browser selection, origin controls and optional connection to an existing browser through its extension.
- Upstream explicitly notes that Playwright MCP itself is not a security boundary; Stage 24 must provide the boundary.

### Windows MCP

Repository: `https://github.com/sbroenne/mcp-windows`

- MIT.
- Latest release observed: `v1.3.18`, with standalone Windows x64/arm64 artifacts and published SHA256 checksums.
- Semantic Windows UI Automation is primary; coordinate mouse/screenshot control is fallback.
- This capability can control the desktop and is therefore high-risk even though the software is free.

### TwelveTake REAPER MCP

Repository: `https://github.com/TwelveTake-Studios/reaper-mcp`

- MIT.
- README version observed: `1.6.4`.
- Uses a maintained file-based bridge inside REAPER; deprecated HTTP mode is not selected.
- Published package can be launched with `uvx`/`pipx`.
- Contains high-level production helpers in addition to low-level track/FX operations.

### OriginPro

Vendor documentation: `https://docs.originlab.com/externalpython/`

OriginLab documents `originpro` as its preferred high-level external Python package. It uses the Origin Automation Server COM interface, supports reading/writing/modifying data and creating/exporting graphs, is Windows-only, and requires a local Origin 2021 or later installation.

## Promotion order

1. Prove read-only Filesystem candidate in CI and then on the user's chosen workspace root.
2. Prove isolated/headless Playwright candidate in CI; Stage 24 defines real-browser permissions before user-session use.
3. Benchmark TwelveTake REAPER MCP on a real REAPER project.
4. Prototype the smallest Origin `originpro` MCP adapter needed for real spectroscopy workflows.
5. Test Windows MCP only as fallback for operations that Origin/REAPER/vendor APIs cannot expose cleanly.
6. Continue FFmpeg and Blender selection research before writing new implementation.
