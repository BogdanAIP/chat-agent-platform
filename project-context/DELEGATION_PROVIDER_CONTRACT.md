# CAP Delegation Provider Contract (Draft v0.1)

## Purpose

This document freezes the architectural boundary between CAP control semantics and execution providers.

The goal is not to create a new agent runtime. The goal is to make explicit the contract already implemented by the bounded Agent Session work.

## Ownership model

CAP owns:

- delegation identity;
- authority and scope;
- operation correlation;
- expected effect definition;
- verification decisions;
- reconciliation decisions.

A provider owns:

- execution mechanics;
- transport/session details;
- provider-specific state;
- provider receipts and observations.

## Core flow

```
Delegation
    |
    v
Provider execution
    |
    v
Provider result
    |
    v
Evidence collection
    |
    v
CAP verification
    |
    v
Verified effect
```

## Required concepts

### DelegationIdentity

Identifies the CAP-owned operation context.

It must not depend on a provider session identifier.

### Provider session reference

References an external execution session.

Examples:

- Temporary Chat session;
- Codex session;
- future bounded provider.

### Delivery claim

A provider execution attempt must have a single owner.

Duplicate execution attempts must fail closed.

### Provider result

A provider result proves only that the provider returned a result.

It does not prove that the requested effect occurred.

### Verified effect

Only CAP can produce this state after checking evidence against the expected effect.

## Non-goals

This contract does not define:

- multi-agent orchestration;
- scheduler behavior;
- worker pools;
- provider memory;
- planner logic.

## Initial implementation target

The first implementation remains the existing ChatGPT Temporary provider.

Future providers must prove compatibility with this contract without changing CAP trust semantics.
