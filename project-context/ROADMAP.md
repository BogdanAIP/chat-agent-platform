# Roadmap — Chat-to-Local Bridge

## Goal

Keep ordinary ChatGPT as the intelligence layer while local capabilities remain replaceable MCP modules or focused adapters. Scale capability count without scaling ChatGPT app/plugin count, keeping hundreds of tools permanently visible, or running every local process all the time.

## Stage 21 — Native ChatGPT ↔ local MCP — DONE

Accepted 2026-08-10: Secure MCP Tunnel + official tunnel-client + local 1MCP + Sequential Thinking round trip from ordinary ChatGPT.

## Stage 22 — Remove superseded custom platform infrastructure — DONE

Removed the obsolete universal Rust/Python core and custom ingress/polling/media platform runtime. Historical implementation remains recoverable at `a446397d99276856c614bc49526cab422c7e74bd`.

## Stage 23 — Quality-first module selection — DONE

Accepted Windows candidates include Filesystem MCP `2026.7.10`, Microsoft Playwright MCP `0.0.78` and 1MCP baseline/adaptive lines.

## Stage 24 — Windows lifecycle + stable typed ordinary-Chat surface — DONE

Merged as `175d36236f80a1f99f091d4f031a1c6255f3652b` (#66).

Accepted exact public semantic surface:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

## Stage 24.1 — Direct semantic tunnel A/B — DONE

Merged as `df1d5e232b739b62e72ad81e5d82fd01be53e884` (#70).

Selected normal transport:

```text
ordinary ChatGPT
  -> Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> focused backends/adapters
```

1MCP remains internal replaceable infrastructure for diagnostics/adaptive/aggregation use.

## Stage 25 — Safe local vision grounding benchmark — DONE FOR GROUNDING BASELINE

PR #73 merged on 2026-08-17 as `acc6334ef0114d3ca6b6a243d904605cd00a321a`.

Selected target-laptop grounding baseline:

```text
runtime = llama.cpp b10448 / ad1de39e0
model = LFM2.5-VL-450M F16
mmproj = F16
CPU = 8 threads
ctx = 2048
```

Final target evidence with Chrome running:

- Search: HIT;
- Send: HIT;
- state-disambiguated Send: HIT;
- Gamma repeated-row action: safe ABSTAIN;
- tiny alert indicator: safe ABSTAIN;
- absent Export CSV: correct ABSTAIN;
- false clicks: 0;
- provider/context errors: 0.

Present-target accuracy is 3/5. This closes the benchmark safety gate, not production browser integration.

## Stage 25.1 — Same-session local vision fallback integration — ACTIVE

Goal: integrate local visual grounding behind the existing browser semantic path without creating a second planner, unsafe coordinate click path, or permanent heavyweight model process.

### P0 gates

1. **IN PROGRESS:** synchronize all authoritative documentation with merged #73 evidence.
2. **ACTIVE:** prove a same-Playwright-session capture/ground/action boundary.
3. **PENDING:** add real semantic->vision integration acceptance:
   - semantic miss/ambiguity -> visual HIT -> action -> observable page result;
   - uncertain/stale visual result -> ABSTAIN -> zero page mutation.

### P1 gates

4. **PENDING:** add focused vision-runtime lifecycle/resource admission:
   - approved artifact identity;
   - memory admission;
   - start/health;
   - idle unload/TTL;
   - crash/stale-process cleanup.
5. **PENDING:** strengthen production grounding verification per target class without a single global IoU threshold.
6. **PENDING:** add browser-state/adversarial tests: layout shift, navigation replacement, scroll, overlays, repeated icons/rows, tiny targets, canvas/WebGL where practical, and hostile UI text.
7. **PENDING:** add security regressions for Windows link/junction root containment, localhost/private-network navigation policy, and tunnel credential inheritance.
8. **PENDING:** broaden static analysis and dependency maintenance to the actual Node/Python code; keep PowerShell contract checks explicit.
9. **PENDING:** move stable installation toward locked/reproducible npm/Python dependency graphs.
10. **PENDING:** refactor common loopback inference transport and model-neutral naming after the P0/P1 contracts stabilize.

### Stage 25.1 architectural rule

```text
semantic DOM/accessibility first
  -> if resolved: act semantically
  -> if unavailable/ambiguous:
       SAME Playwright page/session
       -> capture
       -> local vision
       -> deterministic validation/freshness
       -> resolved action OR ABSTAIN
```

Never implement `VLM point -> blind click` across an unverified page/session boundary.

No new public Chat tool is required merely to add browser visual fallback. The existing five tools remain unchanged until a separate task class justifies a new reviewed action.

## Stage 26 — Professional application capability benchmarks

After Stage 25.1 is safe, benchmark and promote real workflows for REAPER, Origin, FFmpeg, Blender and Windows UI fallback behind the same stable semantic capability philosophy.

## Stage 27 — Distribution and maintenance hardening

After semantic, local vision and at least one professional backend stabilize:

- stable release artifact;
- reproducible dependency installation/locking;
- versioned bootstrap/update/repair/doctor/uninstall;
- runtime-key rotation;
- component upgrade/rollback rules;
- idle/process lifecycle policy and diagnostics;
- thin non-agentic controller/UI.

## Definition of Done

The product succeeds when ordinary ChatGPT can use useful local capabilities through a stable MCP bridge, starting only what tasks require, without a second AI planner, mandatory SaaS chain, project-owned generic gateway, one ChatGPT app per local tool, unsafe stale-coordinate browser action, or hard-coded local model/runtime identity.
