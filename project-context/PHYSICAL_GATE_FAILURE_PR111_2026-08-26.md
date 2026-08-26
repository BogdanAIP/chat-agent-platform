# PR #111 Physical Gate Failure Record — 2026-08-26

Status: **PHYSICAL GATE NOT ACCEPTED**.

Exact runtime/worktree head:

```text
1521e3128a7694be43518c3ee0188cb79f0ca0f5
```

Qualification root:

```text
C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\stage26-3b-browser-interact-20260826-125609
```

Observed ordinary-Chat result through `Chat Local Bridge Test`:

```text
TYPE_PASS                              PASS
CHECKBOX_PASS                          BLOCKED
ALREADY_SATISFIED_ZERO_ACTION          NOT REACHABLE
MISSING_EXPECTED_ZERO_ACTION           PASS
DELIVERED_BUT_WRONG_EXPECTED_FAIL      NOT REACHABLE
AMBIGUOUS_DELETE_ABSTAIN               NOT REACHABLE AS SPECIFIED
OVERALL                                FAIL / BLOCKED
```

The live exact-head public six-tool server already declared `web_interact.expected`, and the backend required it for click/type+submit. However the already-bound ChatGPT app snapshot rejected the field before the MCP call reached the runtime:

```text
Additional properties are not allowed ('expected' was unexpected)
```

Click without `expected` reached the backend and was correctly refused before delivery, proving the runtime path was active while the ChatGPT-side action schema remained stale.

Classification:

```text
ChatGPT frozen app input-schema synchronization failure
!= runtime omitted expected
!= backend accepted an unsafe click
```

Required retry precondition:

1. reconnect/re-add/rebind `Chat Local Bridge Test` outside an active tool call;
2. settle app permissions before the run;
3. start a fresh ordinary Chat conversation;
4. keep exact runtime head unchanged;
5. rerun the same physical interaction gate and first prove that ordinary Chat accepts the `expected` argument.

No physical acceptance credit is granted from this failed attempt. The exact head remains a candidate until the full gate is reachable and passes.