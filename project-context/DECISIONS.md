# Decisions

Historical ADRs for superseded architectures remain in Git history. Only decisions listed here are active. A decision marked **PROVISIONAL** is the current direction but must not be reported as accepted until its acceptance gate passes.

## ADR-010 — Off-the-shelf MCP bridge — ACCEPTED

```text
ordinary ChatGPT Chat -> standard MCP -> mature reachability -> mature local MCP runtime -> replaceable modules
```

ChatGPT is the intelligence/orchestration layer. Infrastructure selection order is official/vendor, mature OSS, mature generic adapter, then the smallest project-owned missing adapter.

## ADR-011 — OpenAI Secure MCP Tunnel is primary ChatGPT reachability — ACCEPTED

Accepted by real E2E on 2026-08-10. Public Funnel/Yandex/custom ingress is not required for normal operation.

## ADR-012 — Superseded universal core removed from active tree — ACCEPTED

The old Rust/Python universal platform, relay/gateway and media platform core are historical only. Recover exact pieces only for a later measured gap. Historical source: `a446397d99276856c614bc49526cab422c7e74bd`.

## ADR-013 — 1MCP is replaceable infrastructure — ACCEPTED

`@1mcp/agent@0.34.4` is the accepted direct Windows baseline. 1MCP is not product identity. A different/newer line may be evaluated for measured compatibility/lifecycle requirements without making multiple gateways permanent dependencies.

## ADR-014 — Privileged capabilities require scoped acceptance — ACCEPTED

Filesystem, shell, browser, application control, credentials and devices require scoped configuration and negative tests before promotion. Security reviews capability risk; it does not mandate permanent isolation of every pair of tools regardless of task.

## ADR-015 — Thin Windows bootstrap/manager is integration code — ACCEPTED

Bootstrap/controller/tray may install, configure, start/stop, report health and coordinate accepted components. They must not become a planner, workflow engine, generic MCP gateway, registry, vault or authorization platform. Runtime secrets remain local and use DPAPI; tunnel profiles are created with the official CLI.

## ADR-016 — Stable Chat-facing adaptive tool contract — PROVISIONAL

### Evidence

The real 2026-08-12 profile switch showed that an existing Chat app retained its previously discovered `filesystem_*` action snapshot after the local runtime changed to the browser profile. Therefore direct backend tool lists cannot be assumed to mutate transparently for an already-connected Chat app.

Creating one Chat app/plugin snapshot for every future backend also does not scale.

### Decision under acceptance

Evaluate one stable Chat-facing 1MCP Lazy Loading surface:

```text
tool_list
tool_schema
tool_invoke
```

with only pre-approved lifecycle controls:

```text
mcp_list
mcp_status
mcp_enable
mcp_disable
mcp_reload
```

Backends are registered locally and disabled until a task activates them. Ordinary Chat must not receive generic catalog install/uninstall/update/edit/search controls.

### Acceptance status

Not accepted yet. Current 1MCP `0.35.0-beta.3` adaptive test sees the disabled catalog and enters Filesystem loading after enable, but Lazy Loading does not publish `read_text_file` before timeout. Resolve or disprove this mechanism before promoting ADR-016 to ACCEPTED.

Do not write a project-owned universal broker merely to preserve ADR-016; if upstream 1MCP cannot satisfy the measured contract after investigation, revisit the decision with evidence.

## ADR-017 — Task-driven capability lifecycle and authorization — PROVISIONAL

Use separate states:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

The platform should not keep every backend process running. Sequential tasks should normally activate backends sequentially. Workflows that genuinely require multiple capabilities may keep multiple backends active together.

Avoid an unnecessarily broad always-on local-data + open-network baseline, but do not convert that safety principle into a blanket architectural prohibition on Browser + Filesystem or other legitimate combinations.

Promotion to ACCEPTED occurs with successful adaptive lifecycle/security acceptance.
