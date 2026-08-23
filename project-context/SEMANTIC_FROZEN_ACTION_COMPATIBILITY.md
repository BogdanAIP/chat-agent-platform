# Semantic Frozen-Action Compatibility

Status: **PHYSICAL E2E ACCEPTED ON TARGET WINDOWS / TEMPORARY MIGRATION COMPATIBILITY**.

## Why this exists

The normal public `semantic` path is already direct stdio:

```text
ordinary ChatGPT
  -> Chat Local Bridge Test
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> semantic-projection
```

The live semantic server publishes exactly five canonical tools:

- `workspace_read`;
- `workspace_write`;
- `web_open`;
- `web_observe`;
- `web_interact`.

A fresh ordinary-Chat test in August 2026 showed that the existing `Chat Local Bridge Test` app still invoked the old Stage 24 1MCP-qualified action IDs even after Refresh:

```text
semantic-projection_1mcp_workspace_read
semantic-projection_1mcp_workspace_write
semantic-projection_1mcp_web_open
semantic-projection_1mcp_web_observe
semantic-projection_1mcp_web_interact
```

The direct semantic runtime correctly rejected those names with JSON-RPC `-32602` / `Tool ... not found` because they were no longer part of the public inventory.

## Compatibility decision

PR #97 adds a narrow compatibility proxy in the credential-scrubbing launcher.

It rewrites **only** the five exact reviewed frozen action IDs above to their canonical names on inbound `tools/call` requests. It does not:

- publish the legacy aliases in `tools/list`;
- add a generic invocation tool;
- strip arbitrary prefixes;
- dispatch arbitrary tool names;
- reintroduce 1MCP into the normal semantic path.

The public inventory remains exactly five canonical tools.

## Hosted acceptance

Hosted candidate `1b78ae37952c7f7a61b0e3497622395deac661e2` passed the complete PR matrix, including:

- Direct Semantic Tunnel Acceptance;
- Semantic Projection Acceptance;
- Semantic Dependency Reproducibility;
- Stage 25.1 Security Regressions;
- CodeQL Security;
- Secret History Scan;
- `ci`;
- Chat Profile Acceptance.

Direct tunnel acceptance on the official `tunnel-client v0.0.11` recorded:

```text
DIRECT_SEMANTIC_TOOL_COUNT=5
DIRECT_SEMANTIC_FILESYSTEM=PASS
DIRECT_SEMANTIC_BROWSER=PASS
DIRECT_SEMANTIC_LEGACY_ACTION_COMPAT=PASS
DIRECT_SEMANTIC_NEGATIVE_CASES=PASS
DIRECT_SEMANTIC_TUNNEL_ACCEPTANCE=PASS
DIRECT_SEMANTIC_1MCP_USED=False
DIRECT_SEMANTIC_TUNNEL=PASS
```

## Target-Windows ordinary-Chat E2E — PASSED

The target machine installed the exact semantic bundle from:

```text
1b78ae37952c7f7a61b0e3497622395deac661e2
```

The installed runtime then reported:

```text
tunnel_running=true
tunnel_ready=true
mcp_ready=true
runtime_ready=true
openai_ready=true
active_profile=semantic
active_count=1
conflict=false
tunnel_binding=direct-stdio
health_code=READY
```

An ordinary ChatGPT conversation using only `Chat Local Bridge Test` semantic tools then executed the frozen action snapshot successfully:

```text
workspace_read(input.txt)
=> ENOENT: no such file or directory, open 'C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\executor-qualification\input.txt'

web_open(https://example.com)
=> success

web_observe
=> Example Domain
```

The `workspace_read` result is an application-level Filesystem `ENOENT`, not a tool-routing failure. It proves that the old frozen action ID reached the canonical semantic Filesystem implementation. `web_open` and `web_observe` completed end-to-end through the same compatibility boundary.

The prior failure mode:

```text
Tool semantic-projection_1mcp_* not found
```

was not observed.

## Architectural scope

This layer is migration compatibility, not a new permanent public contract. The canonical five tool names remain authoritative.

The compatibility aliases may be removed only after a separate ordinary-Chat migration test proves that a newly created or explicitly rebound ChatGPT app no longer invokes any of the five old `_1mcp_` IDs. A UI Refresh alone is not sufficient evidence because the August 2026 target test showed that Refresh did not clear the stale identifiers.

Until that removal gate passes, keeping the exact allowlist is preferred to breaking existing connected ChatGPT app snapshots during transport/runtime upgrades.

## Performance scope

The compatibility operation is a fixed lookup/rewrite across five exact strings before the canonical MCP call. It is not expected to be a material latency contributor compared with tunnel, browser, Filesystem, grounding or model work. Performance is therefore not the removal criterion; removal is governed by contract cleanliness and verified app migration.
