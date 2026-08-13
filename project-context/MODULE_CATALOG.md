# Module Catalog

Research baseline: 2026-08-10. Runtime status synchronized 2026-08-13.

## Status meanings

- **ACCEPTED-INFRASTRUCTURE** — accepted real bridge/runtime path.
- **CI-ACCEPTED** — real Windows module acceptance passed harmless operations.
- **CHAT-E2E-ACCEPTED** — ordinary Chat through the real tunnel completed the target harmless operation.
- **ACCEPTED-CANDIDATE** — evidence is strong enough to proceed to focused audit/real workflow benchmarking, but the module is not product-promoted yet.
- **EXPERIMENTAL** — active engineering candidate; do not describe as accepted/default.
- **LOCAL-TEST-REQUIRED** — promising but requires the real installed application/workflow.
- **SECURITY-REVIEW-REQUIRED** — useful but broad/high-consequence surface needs reduction/scoping.
- **SUPPLY-PIN-REQUIRED** — choose an immutable install artifact/version before promotion.
- **THIN-ADAPTER-FALLBACK** — custom focused adapter allowed only after a measured gap.

| Capability | Candidate | Status | Current decision |
|---|---|---|---|
| Direct local MCP runtime | `@1mcp/agent@0.34.4` | ACCEPTED-INFRASTRUCTURE | Keep for accepted direct/reference profiles while adaptive is evaluated. |
| Adaptive local MCP runtime | `@1mcp/agent@0.35.0-beta.3` + hash-guarded compatibility package | CI-ACCEPTED (runtime) / EXPERIMENTAL (product) | Full lifecycle passes locally/remotely and standalone manager/bootstrap integration passes locally. Integrated-head CI and ordinary-Chat E2E remain. |
| Files | `@modelcontextprotocol/server-filesystem@2026.7.10` | CHAT-E2E-ACCEPTED (direct) | Scoped read-only direct profile passed real ordinary-Chat marker read. Adaptive local read/lifecycle acceptance now passes. |
| Browser | `@playwright/mcp@0.0.78` | CI-ACCEPTED (direct) | Isolated/headless direct profile passed Windows navigation/close. Local browser profile readiness passed; ordinary-Chat browser call was blocked by stale Chat action snapshot, not local Playwright readiness. |
| Windows desktop fallback | `sbroenne/mcp-windows` | LOCAL-TEST-REQUIRED / SECURITY-REVIEW-REQUIRED | Semantic Windows UI Automation fallback; broad screenshot/mouse/keyboard/app-launch surface must not be baseline. |
| REAPER | `TwelveTake-Studios/reaper-mcp` | LOCAL-TEST-REQUIRED / SUPPLY-PIN-REQUIRED | Choose immutable published/release artifact and benchmark a real REAPER workflow. |
| OriginPro | `youngminsw/Origin-Pro-MCP` | LOCAL-TEST-REQUIRED / SECURITY-REVIEW-REQUIRED / SUPPLY-PIN-REQUIRED | Source and PyPI versions differ; pin one artifact and benchmark installed Origin. |
| Origin fallback | official OriginLab `originpro` API | THIN-ADAPTER-FALLBACK | Use only for measured gap in ready-made Origin MCP. |
| FFmpeg/media | `kevinwatt/ffmpeg-mcp-lite==0.2.2` | ACCEPTED-CANDIDATE | Audit path/overwrite behavior and benchmark representative local media tasks. |
| FFmpeg fallback | native FFmpeg CLI behind focused allowlisted adapter | THIN-ADAPTER-FALLBACK | Only if ready-made MCP fails measured requirements; never expose arbitrary shell as media API. |
| Blender | `dcc-mcp/dcc-mcp-blender` | SECURITY-REVIEW-REQUIRED | Broad professional surface; raw Python/script tools must be removed from baseline if selected. |
| Blender alternative | `djeada/blender-mcp-server` | LOCAL-TEST-REQUIRED | Smaller surface; compare real workflow coverage/maintenance. |
| GitHub | existing ChatGPT GitHub connection | do not duplicate | Do not route GitHub through laptop unless local Git specifically requires it. |

## 1MCP evidence

Repository: `1mcp-app/agent`, Apache-2.0.

Accepted direct baseline `0.34.4` already passed ordinary Chat -> Secure MCP Tunnel -> 1MCP E2E.

Stage 24 adaptive experiment pins `0.35.0-beta.3` and uses:

- Lazy Loading meta-tools;
- Async Loading disabled for the experiment;
- internal management execution enabled but Chat-facing publication limited to list/status/enable/disable/reload;
- Filesystem and Playwright registered `disabled: true`.

Previous adaptive functional CI evidence (`c7af0b0...`, same runtime as `9799bec...`):

- `mcp_list` returned both disabled backends correctly;
- enable path entered Filesystem loading;
- transient 503/loading responses were retried;
- lazy `tool_list` remained empty and `read_text_file` did not appear before timeout (`loading retries=49`).

Diagnosis found two exact beta.3 gaps: the synchronous load/unload path does not refresh the lazy registry, and disabled entries are filtered before disable reconciliation. Beta.4 does not change the relevant files. `runtime/1mcp-adaptive-shim` hash-checks those pristine built files, restores disabled-entry reconciliation and performs refresh-only lazy registry updates.

Local 2026-08-13 evidence passes both backend lifecycles, real invocations, exact frozen Chat surface, runtime disabled-tool enforcement, disabled catalog state and process cleanup. Commit `3b12fc9...` passed the same adaptive acceptance plus all profile/CI/security checks remotely.

## Filesystem MCP evidence

- package: `@modelcontextprotocol/server-filesystem@2026.7.10`;
- explicit allowed root;
- direct profile disables create/write/edit/move;
- Windows discovery/read acceptance passed;
- real ordinary-Chat `files-readonly` E2E returned `CHAT_LOCAL_FILES_E2E_OK`.

## Playwright MCP evidence

- package: `@playwright/mcp@0.0.78`;
- isolated/headless Chrome;
- service workers/codegen and dangerous evaluate/file-upload/direct-network tools disabled in the accepted profile;
- Windows direct navigation/content/close acceptance passed;
- local `browser-isolated` + tunnel readiness passed;
- ordinary-Chat browser E2E via the existing app was not completed because Chat retained the old filesystem action snapshot.

## Professional application candidates

### REAPER

`TwelveTake-Studios/reaper-mcp` is the current ready-made-first candidate. GitHub release `v1.6.4` existed in the Stage 23 research while package-channel evidence was older; choose one immutable artifact before testing. Benchmark real editing/routing/FX/render workflows, not a synthetic ping.

### OriginPro

`youngminsw/Origin-Pro-MCP` remains the primary candidate; source and PyPI versions observed during Stage 23 differed. Pin a specific artifact/commit and test the installed Origin. Official OriginLab `originpro` is the fallback foundation only if the ready-made MCP has a measured gap.

### FFmpeg

`ffmpeg-mcp-lite==0.2.2` remains the first candidate. Audit path confinement, overwrite/output behavior and representative convert/trim/merge/audio/subtitle tasks before promotion.

### Blender

Compare a reduced DCC-MCP profile against `djeada/blender-mcp-server`. DCC-MCP's raw Python/script execution must not be part of a least-privilege default surface.

### Windows UI Automation

Use `sbroenne/mcp-windows` only as fallback where specialized APIs/MCPs do not expose the operation cleanly. Full desktop input/screenshot/app-launch capability is high privilege.

## Promotion order

1. Finish Stage 24 adaptive lifecycle/discovery acceptance with Filesystem + Playwright.
2. Integrate accepted adaptive behavior into the standalone manager and prove the one-snapshot ordinary-Chat workflow.
3. Benchmark REAPER, Origin, FFmpeg, Blender and Windows UI candidates on real tasks.
4. Promote successful candidates into the pre-approved local backend catalog with scoped tools/lifecycle evidence.
5. Adding a promoted backend should normally **not** require a new ChatGPT plugin/app or permanent process.
