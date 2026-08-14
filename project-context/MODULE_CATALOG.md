# Module Catalog

Research baseline: 2026-08-10. Runtime/product status synchronized 2026-08-14.

## Status meanings

- **ACCEPTED-INFRASTRUCTURE** — accepted real bridge/runtime path.
- **CI-ACCEPTED** — real Windows/module acceptance passed applicable harmless operations.
- **CHAT-E2E-ACCEPTED** — ordinary Chat through the real tunnel completed the target operation.
- **ACCEPTED-CANDIDATE** — evidence is strong enough to proceed to focused audit/real workflow benchmarking, but the module is not product-promoted yet.
- **EXPERIMENTAL** — active engineering candidate; do not describe as accepted/default.
- **DIAGNOSTIC** — useful for testing/runtime evidence but not the promoted product-facing contract.
- **LOCAL-TEST-REQUIRED** — promising but requires the real installed application/model/workflow.
- **SECURITY-REVIEW-REQUIRED** — useful but broad/high-consequence surface needs reduction/scoping.
- **SUPPLY-PIN-REQUIRED** — choose an immutable install artifact/version before promotion.
- **THIN-ADAPTER-FALLBACK** — custom focused adapter allowed only after a measured gap.

| Capability | Candidate | Status | Current decision |
|---|---|---|---|
| Direct local MCP runtime | `@1mcp/agent@0.34.4` | ACCEPTED-INFRASTRUCTURE | Keep for accepted direct/reference/typed experiments. |
| Adaptive local MCP runtime | `@1mcp/agent@0.35.0-beta.3` + hash-guarded compatibility package | CI-ACCEPTED / DIAGNOSTIC | Lifecycle mechanics pass locally/remotely. Generic Chat-facing lifecycle/schema/invocation contract is not product-accepted after real pre-MCP blocking. |
| Files | `@modelcontextprotocol/server-filesystem@2026.7.10` | CHAT-E2E-ACCEPTED | Direct read-only path passed. Synthetic combined typed ordinary-Chat read/write also passed. Scope/root/write policy remains task/profile dependent. |
| Browser | `@playwright/mcp@0.0.78` | CHAT-E2E-ACCEPTED | Fresh-snapshot typed `browser_navigate` passed. Combined typed ordinary-Chat navigate/find/click also passed with Filesystem in one conversation. |
| Local model runtime manager | LM Studio / `llmster` | ACCEPTED-CANDIDATE / LOCAL-TEST-REQUIRED | Stage 25 first runtime-manager candidate. Benchmark headless/server, model discovery, estimate-before-load, GPU selection, JIT/TTL/auto-evict and cleanup on target Windows. Keep replaceable. |
| Local vision model | `LiquidAI/LFM2.5-VL-3B` | ACCEPTED-CANDIDATE / LOCAL-TEST-REQUIRED | Official 2026-08-12 release. First preferred `local-vision` candidate for screen/UI, OCR/document/chart, grounding and multi-image tasks. Benchmark actual GGUF/ONNX/runtime variants on target hardware before promotion. |
| Windows desktop fallback | `sbroenne/mcp-windows` | LOCAL-TEST-REQUIRED / SECURITY-REVIEW-REQUIRED | Semantic Windows UI Automation fallback; broad screenshot/mouse/keyboard/app-launch surface must not be baseline. |
| REAPER | `TwelveTake-Studios/reaper-mcp` | LOCAL-TEST-REQUIRED / SUPPLY-PIN-REQUIRED | Choose immutable published/release artifact and benchmark a real REAPER workflow. |
| OriginPro | `youngminsw/Origin-Pro-MCP` | LOCAL-TEST-REQUIRED / SECURITY-REVIEW-REQUIRED / SUPPLY-PIN-REQUIRED | Source and PyPI versions differed in Stage 23 research; pin one artifact and benchmark installed Origin. |
| Origin fallback | official OriginLab `originpro` API | THIN-ADAPTER-FALLBACK | Use only for measured gap in ready-made Origin MCP. |
| FFmpeg/media | `kevinwatt/ffmpeg-mcp-lite==0.2.2` | ACCEPTED-CANDIDATE | Audit path/overwrite behavior and benchmark representative local media tasks. |
| FFmpeg fallback | native FFmpeg CLI behind focused allowlisted adapter | THIN-ADAPTER-FALLBACK | Only if ready-made MCP fails measured requirements; never expose arbitrary shell as media API. |
| Blender | `dcc-mcp/dcc-mcp-blender` | SECURITY-REVIEW-REQUIRED | Broad professional surface; raw Python/script tools must be removed from baseline if selected. |
| Blender alternative | `djeada/blender-mcp-server` | LOCAL-TEST-REQUIRED | Smaller surface; compare real workflow coverage/maintenance. |
| GitHub | existing ChatGPT GitHub connection | do not duplicate | Do not route GitHub through laptop unless local Git specifically requires it. |

## 1MCP evidence

Repository: `1mcp-app/agent`, Apache-2.0.

Accepted direct baseline `0.34.4` passed ordinary Chat -> Secure MCP Tunnel -> 1MCP E2E and remains the direct/reference/typed-experiment baseline.

Adaptive pins `0.35.0-beta.3` with Lazy Loading ON and Async Loading OFF through `runtime/1mcp-adaptive-shim`. The compatibility package fixes two measured upstream lifecycle gaps: lazy-registry refresh after synchronous backend lifecycle and disabled-entry reconciliation during unload.

Local/remote lifecycle acceptance passes Filesystem + Playwright enable/discover/invoke/disable/cleanup with the exact frozen generic surface.

Real ordinary Chat then admitted list/status/discovery but blocked lifecycle plus `tool_schema`/`tool_invoke` before MCP. Therefore adaptive is **diagnostic lifecycle infrastructure**, not the accepted generic product-facing contract.

## Chat typed-surface evidence

A fresh typed direct Browser snapshot passed ordinary-Chat `browser_navigate`.

A combined local runtime exposed 14 Filesystem + 20 Playwright actions. The tested Chat app effectively surfaced 20 actions, leaving later browser actions unavailable. Reducing Filesystem to four typed actions produced a 24-tool local inventory; after Refresh/new Chat the ordinary-Chat app successfully used:

- `list_allowed_directories`;
- `read_text_file`;
- `write_file`;
- `browser_navigate`;
- `browser_find`;
- `browser_click`.

Do not treat the observed 20-action truncation as an official universal limit. It is a measured Stage 24 compatibility constraint that the scalable typed publication design must accommodate.

## Filesystem MCP evidence

- package: `@modelcontextprotocol/server-filesystem@2026.7.10`;
- explicit allowed root;
- direct `files-readonly` profile disables create/write/edit/move;
- Windows discovery/read acceptance passed;
- real ordinary-Chat direct read returned `CHAT_LOCAL_FILES_E2E_OK`;
- synthetic combined typed ordinary-Chat read/write passed in `chat-final-system-e2e`.

## Playwright MCP evidence

- package: `@playwright/mcp@0.0.78`;
- isolated/headless Chrome;
- service workers/codegen and unsafe code/evaluate/file-upload/direct-network tools disabled in the accepted direct config;
- Windows direct navigation/content/close acceptance passed;
- fresh ordinary-Chat typed `browser_navigate` passed;
- combined ordinary-Chat typed `browser_navigate` -> `browser_find` -> `browser_click` reached IANA `Example Domains`.

## LM Studio / llmster candidate evidence

Official LM Studio documentation currently provides the capabilities needed for the Stage 25 runtime-manager experiment:

- `lms server start/stop`;
- local model listing (`lms ls`) and loaded-model inspection (`lms ps`);
- model load/unload;
- GPU-offload and context-length controls;
- `lms load --estimate-only` resource estimation before loading, including vision-aware estimation;
- JIT loading;
- idle TTL;
- auto-eviction of JIT-loaded models.

This is research/candidate evidence only. Target Windows acceptance must verify exact installed LM Studio/llmster version and behavior.

Official docs:

- https://lmstudio.ai/docs/cli
- https://lmstudio.ai/docs/cli/local-models/load
- https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict

## LFM2.5-VL-3B candidate evidence

Liquid AI officially released `LFM2.5-VL-3B` on 2026-08-12. Official material describes:

- 3.1B-class vision-language model;
- screen/UI understanding;
- OCR/document/chart understanding;
- grounding;
- multi-image input;
- function-calling/tool-use improvements;
- day-one GGUF/llama.cpp and ONNX support;
- browser WebGPU demo.

The model is a preferred first benchmark candidate, not yet an accepted dependency. Do not hard-code its quantization/runtime before target-hardware measurements.

Official sources:

- https://www.liquid.ai/blog/lfm2-5-vl-3b
- https://docs.liquid.ai/lfm/models/lfm25-vl-3b
- https://huggingface.co/LiquidAI/LFM2.5-VL-3B
- https://huggingface.co/spaces/LiquidAI/LFM2.5-VL-3B-WebGPU

## Professional application candidates

### REAPER

`TwelveTake-Studios/reaper-mcp` is the current ready-made-first candidate. Choose one immutable artifact before testing. Benchmark real editing/routing/FX/render workflows, not a synthetic ping.

### OriginPro

`youngminsw/Origin-Pro-MCP` remains the primary candidate. Pin a specific artifact/commit and test the installed Origin. Official OriginLab `originpro` is the fallback foundation only if the ready-made MCP has a measured gap.

### FFmpeg

`ffmpeg-mcp-lite==0.2.2` remains the first candidate. Audit path confinement, overwrite/output behavior and representative convert/trim/merge/audio/subtitle tasks before promotion.

### Blender

Compare a reduced DCC-MCP profile against `djeada/blender-mcp-server`. DCC-MCP's raw Python/script execution must not be part of a least-privilege default surface.

### Windows UI Automation

Use `sbroenne/mcp-windows` only as fallback where specialized APIs/MCPs do not expose the operation cleanly. Full desktop input/screenshot/app-launch capability is high privilege.

## Promotion order

1. Complete Stage 24 single-owner target-machine acceptance and scalable typed Chat-facing capability publication.
2. Stage 25: benchmark LM Studio/llmster and `LFM2.5-VL-3B`, then expose the accepted result through a small stable `local-vision` typed boundary.
3. Stage 26: benchmark REAPER, Origin, FFmpeg, Blender and Windows UI candidates on real tasks.
4. Promote successful candidates with scoped tools/lifecycle evidence.
5. Adding a promoted backend/model should normally **not** require a new ChatGPT app/plugin, permanent process or hard-coded model runtime.
