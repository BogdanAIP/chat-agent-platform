# Stage 23 Module Catalog

Research snapshot: 2026-08-10.

Status meanings:

- **ACCEPTED-CANDIDATE** — quality/cost/licensing look strong enough for technical acceptance tests; not automatically exposed to ChatGPT yet.
- **LOCAL-TEST-REQUIRED** — promising but must be tested against the user's real installed application before promotion.
- **SECURITY-REVIEW-REQUIRED** — technically strong but exposes a broad or dangerous surface that must be reduced before promotion.
- **SUPPLY-PIN-REQUIRED** — upstream source is promising, but the desired source version is not yet the same version available from the normal package channel; choose and test an immutable install source before promotion.
- **THIN-ADAPTER-FALLBACK** — a small project-owned adapter is allowed only if the better ready-made candidate fails measured requirements.
- **RESEARCH** — no candidate promoted yet.

| Capability | Candidate | Cost model | License / owner | Status | Decision |
|---|---|---|---|---|---|
| MCP aggregation | `@1mcp/agent@0.34.4` | local, no SaaS required | Apache-2.0, 1mcp-app | accepted infrastructure | Keep. Already passed ChatGPT E2E through Secure MCP Tunnel. |
| Files | `@modelcontextprotocol/server-filesystem@2026.7.10` | local, free | MIT, Model Context Protocol project | ACCEPTED-CANDIDATE | Use scoped roots. Candidate profile disables create/write/edit/move so Stage 23 acceptance is read-only. Do not promote until the real 1MCP compatibility test is green. |
| Browser | `@playwright/mcp@0.0.78` | local, free | Apache-2.0, Microsoft | ACCEPTED-CANDIDATE | Primary browser foundation: structured accessibility snapshots, isolated/headless test mode, no paid browser cloud required. Real-session permissions belong to Stage 24. |
| Windows desktop fallback | `sbroenne/mcp-windows` | local, free | MIT | LOCAL-TEST-REQUIRED / SECURITY-REVIEW-REQUIRED | Strong semantic Windows UI Automation fallback. Keep screenshot/mouse/keyboard as fallback only; never expose the whole desktop surface by default. |
| REAPER | `TwelveTake-Studios/reaper-mcp` | local, free beyond REAPER itself | MIT | LOCAL-TEST-REQUIRED / SUPPLY-PIN-REQUIRED | GitHub release `v1.6.4` exists and is the desired source line, while the package-channel evidence inspected still shows PyPI `1.6.0`. Choose either the verified PyPI build or an immutable `v1.6.4` source/release install and benchmark exactly that artifact. |
| OriginPro | `youngminsw/Origin-Pro-MCP` | local, no extra SaaS; requires installed/licensed Origin | MIT | LOCAL-TEST-REQUIRED / SECURITY-REVIEW-REQUIRED / SUPPLY-PIN-REQUIRED | Source `main` is `0.3.1` at commit `1e9741af96c45bcac9e619c3ba32264bac6950e7`, but PyPI currently publishes `0.1.0`. Do not use an unpinned `uvx` and assume it matches source. Benchmark either published `0.1.0` or the exact source commit after review. |
| OriginPro fallback | official OriginLab `originpro` external Python API | no extra service fee beyond installed Origin | OriginLab vendor API | THIN-ADAPTER-FALLBACK | Use only if the ready-made Origin MCP fails compatibility, safety or workflow quality. Do not build an adapter pre-emptively. |
| FFmpeg/media | `kevinwatt/ffmpeg-mcp-lite` `0.2.2` | local, free; requires local FFmpeg | MIT | ACCEPTED-CANDIDATE | PyPI `0.2.2` is verified. Small typed surface for info/convert/compress/trim/merge/audio/frames/subtitles. Audit all tools and run real media tests before promotion. |
| FFmpeg fallback | native FFmpeg CLI behind a small allowlisted adapter | local, free | FFmpeg project + project adapter | THIN-ADAPTER-FALLBACK | Only build if `ffmpeg-mcp-lite` fails measured needs. Never expose arbitrary shell as the media API. |
| Blender | `dcc-mcp/dcc-mcp-blender` | local, free | MIT source/PyPI; Blender Extension distribution GPL-3.0-or-later | SECURITY-REVIEW-REQUIRED | Very broad and active 200+ tool ecosystem with E2E CI and progressive skills, but includes raw Python/script execution. Interesting for deep Blender work only after a reduced tool profile is proven. |
| Blender alternative | `djeada/blender-mcp-server` | local, free | MIT | LOCAL-TEST-REQUIRED | Smaller 22-tool surface is attractive for a safer baseline. Compare actual workflow coverage and maintenance against DCC-MCP before selection. |
| GitHub | existing ChatGPT GitHub connection | existing product connection | external connector | do not duplicate | Do not route GitHub through the laptop unless a local Git operation specifically requires it. |

## Primary-source evidence

### 1MCP

Repository: `https://github.com/1mcp-app/agent`

- Apache-2.0.
- Aggregates multiple MCP servers.
- Supports server tags/filters, progressive/lazy discovery, environment substitution and per-server `disabledTools`.
- The bridge remains pinned to the already accepted stable `0.34.4` until a deliberate upgrade test.
- Important Windows detail verified from the pinned source: a stdio server does not inherit the whole parent environment by default. The array env form, for example `"env": ["NAME"]`, imports only the named variable and is preferred over broad inheritance.

### Filesystem MCP

Repository: `https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem`
Package channel: `https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem`

- npm package: `@modelcontextprotocol/server-filesystem`.
- Published stable version selected for tests: `2026.7.10`.
- Install pinning follows the real npm supply channel, not an unreleased source-tree version string.
- Supports explicit allowed directories / MCP Roots.
- Tools carry read-only/destructive annotations.
- The Stage 23 profile additionally disables create/write/edit/move at the 1MCP layer.

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

- MIT and actively maintained in August 2026.
- Uses Windows UI Automation names/roles as the primary mechanism rather than screen coordinates.
- Provides structured UI snapshot/find/click/type/select/read/table/wait/batch operations.
- Screenshot, mouse, keyboard, clipboard and app-launch capabilities make the full server high privilege even though it is local and free.
- UAC/elevated windows remain a Windows security boundary; the project explicitly documents that a non-elevated server cannot automate secure-desktop UAC prompts.

### TwelveTake REAPER MCP

Repository: `https://github.com/TwelveTake-Studios/reaper-mcp`
GitHub release: `v1.6.4`, published 2026-08-08.

- MIT.
- 176 tools for track/FX/routing/automation/MIDI/rendering plus higher-level production workflows.
- The supported communication path is a local file-based bridge; deprecated HTTP mode is not selected.
- The REAPER bridge uses stock Lua and requires no cloud service or paid API.
- GitHub `v1.6.4` specifically improves long render timeout reporting.
- The PyPI project evidence inspected during this Stage still reported `1.6.0`; therefore an eventual config must not blindly claim `uvx twelvetake-reaper-mcp==1.6.4` until that exact package build is verified. A pinned GitHub release/source install remains possible if we deliberately choose it.

### Origin Pro MCP

Repository: `https://github.com/youngminsw/Origin-Pro-MCP`
Source commit selected for review: `1e9741af96c45bcac9e619c3ba32264bac6950e7` (`0.3.1`).
PyPI version verified on 2026-08-10: `0.1.0`.

- MIT, Python 3.10+, Windows runtime using `pywin32` and Origin COM Automation.
- The newer source line provides worksheet management, CSV/Excel import/export, matrices/3D, graph creation/layers/styling, fitting, FFT, smoothing, integration, differentiation, interpolation, peak finding, statistics and project operations.
- Includes guarded LabTalk, but raw LabTalk remains a high-risk capability and must not be in a least-privilege default profile.
- Ships extensive unit/integration/live test files for import/export, graphing, fitting and connection behavior.
- The repository README's simple `uvx origin-pro-mcp` path currently resolves the PyPI package, which is older than source `0.3.1`; Stage 23 must choose the artifact explicitly rather than conflating them.
- Upstream source documents Origin 2020 COM quirks; actual compatibility with the installed Origin must be measured locally.

Vendor fallback: OriginLab's official external Python `originpro` API remains the preferred foundation if a small custom compatibility adapter is eventually required.

### FFmpeg MCP Lite

Repository: `https://github.com/kevinwatt/ffmpeg-mcp-lite`
PyPI version verified: `0.2.2`.

- MIT, Python 3.10+, local FFmpeg/ffprobe.
- Small tool set: media info, conversion, compression, trim, merge, audio extraction, frame extraction and subtitle burn-in.
- The inspected conversion implementation builds an argv array and invokes FFmpeg via `asyncio.create_subprocess_exec`, avoiding shell-string execution for that operation.
- Repository includes pytest coverage and separates tools by operation.
- Before promotion Stage 23/24 must inspect the remaining operations for path confinement, overwrite semantics and output-directory behavior, then run real media tests.

### Blender candidates

`dcc-mcp/dcc-mcp-blender`:

- Active in August 2026, source/PyPI MIT; its Blender Extensions ZIP is GPL-3.0-or-later as required by that distribution channel.
- Embeds a Streamable HTTP MCP server in Blender and advertises 200+ tools with progressive skills and E2E CI.
- It also exposes raw scripting such as `execute_python` / script execution. Those tools are incompatible with a least-privilege default profile and must be disabled if this candidate is selected.

`djeada/blender-mcp-server`:

- MIT, smaller 22-tool surface across six namespaces.
- Candidate for a simpler baseline if it covers the real modeling/material/render/export workflows well enough.

## Promotion order

1. Get read-only Filesystem and isolated/headless Playwright green through real 1MCP acceptance on Windows.
2. Test the same two candidates locally through the existing Secure MCP Tunnel without adding them to the permanent default profile yet.
3. Choose an immutable REAPER artifact (published PyPI build or pinned GitHub release) and benchmark it on a real REAPER project.
4. Choose an immutable Origin-Pro-MCP artifact (published `0.1.0` or reviewed commit `1e9741a...`) and benchmark it on the installed Origin; only fall back to an `originpro` adapter if a measured gap remains.
5. Audit and benchmark verified PyPI `ffmpeg-mcp-lite==0.2.2` on representative media operations before recovering or writing any FFmpeg adapter.
6. Test Windows MCP only as fallback for operations that specialized APIs cannot expose cleanly.
7. Compare the reduced DCC-MCP Blender profile with the smaller `djeada` server before selecting a Blender default.
