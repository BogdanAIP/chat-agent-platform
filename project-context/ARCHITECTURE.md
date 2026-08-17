# Architecture

## Product boundary

`chat-agent-platform` is a thin bridge that lets ordinary ChatGPT use scoped local Windows capabilities. Ordinary ChatGPT remains the only planner/orchestrator. Local components may provide deterministic execution or bounded specialist inference, but they must not become a second agent brain.

## Accepted ordinary-Chat path

```text
ordinary ChatGPT Chat
  -> OpenAI Secure MCP Tunnel
  -> official tunnel-client
  -> direct stdio semantic-projection
  -> focused task-active backends/adapters
```

The accepted public semantic surface is exactly:

```text
workspace_read
workspace_write
web_open
web_observe
web_interact
```

1MCP remains replaceable internal infrastructure for diagnostics, adaptive lifecycle experiments and aggregation where useful. The normal public `semantic` path is direct stdio.

## Capability projection rule

`semantic-projection` is a deterministic compatibility boundary. It may map one truthful semantic operation to one reviewed backend action or a small bounded deterministic sequence. It must not:

- decide user goals;
- execute arbitrary hidden plans;
- expose generic `tool_invoke` behavior under another name;
- dynamically route to arbitrary unreviewed models/endpoints;
- become a general process supervisor or model manager.

## Capability lifecycle

Use three independent states:

```text
AVAILABLE -> ACTIVE -> AUTHORIZED
```

A backend/model may exist on disk without running; start it only when a task needs it; authorize only operations within accepted scope. Concurrent backends are allowed when a real workflow requires them, but idle heavyweight processes should not remain loaded without need.

## Browser grounding architecture

Deterministic semantic DOM/accessibility grounding is always preferred when reliable structure exists.

Stage 25.1 introduces visual grounding only as an internal fallback:

```text
browser semantic operation
  -> semantic/accessibility grounding
       -> resolved target: act semantically
       -> unavailable/ambiguous:
            SAME Playwright page/session
            -> capture current viewport/page evidence
            -> bounded local visual grounding
            -> deterministic validation + freshness check
            -> resolved action OR ABSTAIN
            -> if resolved, act in SAME Playwright page/session
```

### Same-session invariants

Automatic visual interaction is forbidden unless all applicable invariants are proven:

1. capture and action belong to the same Playwright page/session;
2. the coordinate space is explicit and deterministic;
3. viewport dimensions, scroll position and relevant scale/zoom state are known;
4. no navigation/page replacement occurred between capture and action;
5. stale or ambiguous visual evidence produces ABSTAIN;
6. the action cannot silently fall back to a different page/browser instance;
7. page mutation is zero when grounding returns ABSTAIN/error.

If the pinned Playwright MCP cannot provide the required internal primitives safely, do not bypass it with unrestricted browser code/evaluate. Prefer the smallest reviewed focused adapter that preserves the same-session boundary.

### Internal grounding result

Production code should converge on a model-neutral internal result rather than exposing model-specific outputs:

```text
GroundingResult
  status = resolved | abstain | error
  source = semantic | vision
  target_kind = text | icon | repeated | tiny | state | unknown
  coordinate_space = css_viewport | semantic_ref
  semantic_ref? = bounded backend ref
  bbox? = validated rectangle
  point? = validated action point
  capture_context? = viewport/scroll/page freshness evidence
  reason = deterministic decision code
  diagnostics = non-authorizing evidence
```

Diagnostics must never authorize an action by themselves. A `refined_box` retained for debugging after ABSTAIN is not an actionable target.

## Local vision boundary

Accepted Stage 25 target-laptop grounding baseline after PR #73:

```text
runtime = llama.cpp b10448 / ad1de39e0
model = LiquidAI LFM2.5-VL-450M F16
projector = F16
CPU = 8 threads
ctx = 2048
```

The benchmark adapter performs bounded local inference and deterministic validation. The model never clicks.

Current target evidence: Search/Send/state HIT, Gamma/tiny safe ABSTAIN, absent Export CSV correct ABSTAIN, zero false clicks and zero provider/context errors. Present-target accuracy is 3/5, so vision remains fallback-quality rather than primary grounding.

Runtime/model identity must remain replaceable behind a provider-neutral interface. Product code must not hard-code `450M`/LiquidAI naming into the public semantic contract.

## Vision lifecycle boundary

Do not put full llama.cpp lifecycle/resource policy into `semantic-projection` or expand `chat-platform.ps1` into a model orchestration platform.

Preferred separation:

```text
semantic/browser grounding adapter
        -> focused vision-runtime owner
             -> resource admission
             -> approved model/runtime identity
             -> start/health
             -> inference
             -> idle TTL/unload
             -> crash/stale-process cleanup
```

The runtime owner is non-agentic and may choose only among explicitly reviewed local artifacts/configurations according to deterministic policy.

## Security boundaries

- tunnel reachability is outbound from the user machine;
- normal semantic transport is direct stdio, not local port 3050;
- secrets live outside repository content and tunnel keys are stored via Windows DPAPI;
- Filesystem roots and browser capability exposure remain explicitly scoped;
- raw Playwright evaluate/run-code/file-upload/network-request actions remain forbidden from the semantic surface;
- local inference binds only to loopback and must not expose arbitrary endpoint/model/prompt control to Chat;
- workspace containment must be tested against Windows links/junctions, not only lexical `..` traversal;
- browser navigation policy must explicitly address localhost/private-network targets before visual auto-interaction broadens consequences;
- child backends must not receive tunnel credentials unless required.

## Windows management

The public manager/tray owns lifecycle/configuration/diagnostics only. Installed/source copies coordinate through one authoritative runtime owner; ambiguous/unowned shared runtime state fails closed.

Direct semantic uses the exact owned tunnel-client command/health state as its managed boundary and does not require port 3050. Legacy/diagnostic 1MCP profiles retain their own accepted port/process checks.

## Testing rule

The next integration gate must exercise the real chain, not two independent unit tests:

```text
same Playwright page
-> semantic miss/ambiguity
-> capture
-> visual grounding
-> validation
-> action
-> observable result
```

and a negative twin:

```text
same Playwright page
-> uncertain/stale visual grounding
-> ABSTAIN
-> page remains unchanged
```

Changing exported Chat actions still requires explicit Refresh/review and fresh ordinary-Chat acceptance.

## Ownership

The repository owns thin integration assets only: pinned configs, lifecycle/bootstrap, deterministic compatibility adapters, focused missing-boundary adapters, tests and project context. It does not own a generic gateway, registry, vault, workflow brain or general AI runtime platform.
