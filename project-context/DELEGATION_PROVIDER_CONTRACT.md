# CAP Delegation Provider Contract (Draft v0.2)

## Purpose

This document freezes the architectural boundary between CAP control semantics and execution providers.

The goal is not to create a new agent runtime. The goal is to make explicit the delegation boundary and trust semantics established by the bounded Agent Session work.

This document clarifies existing architecture. It does not replace ARCHITECTURE.md, CONTROL_PLANE.md, ADR decisions, or CURRENT_STATE.md.

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

Delegation
 |
 v
Provider execution
 |
 v
Provider result
 |
 v
CAP result integrity / provenance checks
 |
 v
Recorded delegation outcome

ExpectedEffect-based verification and Verified Effect belong to CAP verification flows where an external effect is being evaluated.

## Required concepts

### DelegationIdentity

Identifies the CAP-owned operation context.

It must not depend on a provider session identifier.

### Provider session reference

References an external execution session.

Examples:

- Temporary Chat session;
- Codex session;
- future bounded execution adapter.

### Delivery claim

A provider execution attempt must have a single owner.

Duplicate execution attempts must fail closed.

### Provider result

A provider result proves that the provider returned a correlated result.

It does not by itself prove that the requested external effect occurred.

### Verified effect

Verified Effect is produced only by CAP verification flows after checking evidence against an ExpectedEffect definition.

## Non-goals

This contract does not define:

- multi-agent orchestration;
- scheduler behavior;
- worker pools;
- provider memory;
- planner logic.

## Initial implementation target

The first implementation remains the existing ChatGPT Temporary provider.

Future execution adapters may be evaluated against this boundary without changing CAP trust semantics.
