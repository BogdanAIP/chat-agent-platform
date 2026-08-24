# Document Status

This file classifies repository documentation by authority. Exact code, tests, current CI and physical evidence outrank prose when they disagree.

## Current authoritative documents

Read these first for current development:

- `START_HERE.md`
- `CONTINUATION_CONTEXT.md`
- `CURRENT_STATE.md`
- `ARCHITECTURE.md`
- `CONTROL_PLANE.md`
- `DECISIONS.md`
- `MODULE_SELECTION_POLICY.md`
- `ROADMAP.md`
- `EVIDENCE_INDEX.md`
- `TYPED_CAPABILITY_PROJECTION.md`
- `STAGE26_3A_IMPLEMENTATION_NOTES.md`
- `STAGE26_3A_PROCEDURE_RUN_SURFACE.md`

Current architecture notes that must remain synchronized:

```text
ordinary Chat public semantic surface = exactly six tools
normal semantic transport = direct stdio
persistent tunnel anchor = state/tunnel.json
1MCP = optional replaceable internal Extension Manager
1MCP absence/failure must not block normal semantic bootstrap/start/health
raw third-party MCP tools are not automatically Chat-facing
```

The authoritative 1MCP/extension boundary is recorded in `DECISIONS.md` ADR-031 and `MODULE_SELECTION_POLICY.md`.

## Accepted historical evidence documents

Stage-specific documents remain authoritative only for the exact accepted scope/head/evidence they record. They do not override the current public semantic inventory or current transport/extension architecture.

Historical five-tool Stage 24/25 references are evidence of the accepted file/browser foundation, not a current product-mode alternative.

Historical `local-1mcp` references may describe earlier transport/aggregation architecture. They are not the current normal semantic source of truth. Existing `local-1mcp.yaml` is retained only for bounded tunnel-id migration compatibility and optional Extension Manager work.

## Active Stage 26.3A documentation rule

Stage 26.3A is not physically accepted until the target Windows machine passes the recorded ordinary-Chat physical gates on one exact PR head.

Hosted acceptance must establish at least:

- exact six-tool canonical inventory;
- real `procedure_run` behavior and negative ABSTAIN behavior;
- direct Secure MCP Tunnel behavior;
- installed-layout six-tool Control Plane closure;
- neutral `state/tunnel.json` tunnel-anchor contract with legacy migration only;
- normal bootstrap has no mandatory 1MCP/npx preflight;
- normal bootstrap smoke uses `semantic` + `direct-stdio`, not `reference`/1MCP.

Optional Extension Manager/adaptive regressions remain useful evidence but are not evidence that 1MCP belongs in the normal semantic critical path.

## Update rule

When current architecture changes, update the smallest set of authoritative documents that a fresh chat would rely on, especially `CONTINUATION_CONTEXT.md`, `CURRENT_STATE.md`, `ARCHITECTURE.md`, `DECISIONS.md` and the relevant stage contract. Do not rewrite historical evidence merely to make old terminology look current.
