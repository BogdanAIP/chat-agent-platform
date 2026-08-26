# PR #111 Physical Gate Failure and Resolution — 2026-08-26

Status: **INITIAL RUN FAILED; REBIND DIAGNOSIS PASSED; FINAL PHYSICAL GATE ACCEPTED**.

Exact runtime/worktree head remained unchanged throughout diagnosis and retry:

```text
1521e3128a7694be43518c3ee0188cb79f0ca0f5
```

Initial qualification root:

```text
C:\Users\eahra\AppData\Local\ChatAgentPlatform\stage26\stage26-3b-browser-interact-20260826-125609
```

## Initial ordinary-Chat run

Observed through `Chat Local Bridge Test`:

```text
TYPE_PASS                              PASS
CHECKBOX_PASS                          BLOCKED
ALREADY_SATISFIED_ZERO_ACTION          NOT REACHABLE
MISSING_EXPECTED_ZERO_ACTION           PASS
DELIVERED_BUT_WRONG_EXPECTED_FAIL      NOT REACHABLE
AMBIGUOUS_DELETE_ABSTAIN               NOT REACHABLE AS SPECIFIED
OVERALL                                FAIL / BLOCKED
```

The live exact-head public six-tool server already declared `web_interact.expected`, and the backend required it for click/type+submit. However the already-bound ChatGPT app definition rejected the field before the call reached the runtime:

```text
Additional properties are not allowed ('expected' was unexpected)
```

Click without `expected` reached the backend and was correctly refused before delivery. The failure therefore did not prove that the exact-head runtime omitted ExpectedEffect support.

## Rebind diagnosis

`Chat Local Bridge Test` was fully reconnected/rebound, permissions were settled before execution, and a fresh ordinary Chat conversation was used while the exact runtime head stayed unchanged.

A diagnostic checkbox interaction then accepted the explicit `expected` argument and returned:

```text
browser_verification.status = pass
verification.status         = pass
verification.reason         = expected_effect_verified
Agree.checked               = true
```

This isolates the initial failure to stale client-visible app/action-schema state rather than an implementation difference in PR #111.

## Final physical gate

The full ordinary-Chat target-Windows interaction gate was then rerun on the same exact head and passed:

```text
TYPE_PASS                           PASS
CHECKBOX_PASS                       PASS
ALREADY_SATISFIED_ZERO_ACTION       PASS
MISSING_EXPECTED_ZERO_ACTION        PASS
DELIVERED_BUT_WRONG_EXPECTED_FAIL   PASS
AMBIGUOUS_DELETE_ABSTAIN            PASS
DELIVERY_NOT_SUCCESS_PROVED         PASS
OVERALL_GATE                        PASS
```

Key independent evidence:

- typed value became `PHYSICAL_TYPED_OK` with Browser verification PASS;
- first `Agree` click reached `checked=true` with `expected_effect_verified`;
- repeated already-satisfied `checked=true` was refused before delivery and remained checked;
- click without `expected` was refused before delivery and `Unsafe status` remained `SAFE`;
- click with deliberately wrong `enabled=false` expectation was physically delivered, toggled the checkbox to unchecked, remained enabled, and returned `expected_effect_failed`, proving delivery is not success;
- ambiguous duplicate `Delete` targets produced semantic-ambiguity abstention with zero arbitrary mutation and `Delete status=DELETE_NOT_CLICKED`.

PR #111 was subsequently squash-merged into `main` as:

```text
f7bba9eddd7c449306b7c9de18bc9e19849fd86f
```

The failed first attempt remains useful migration evidence, but it grants no acceptance credit by itself. Acceptance comes from the final full physical PASS on the unchanged exact runtime head.