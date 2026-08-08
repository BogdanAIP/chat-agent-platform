# Stage 4 — Yandex long-poll relay

## Why this transport exists

Hosted Chat cannot execute `agent-platform.exe` on the user's Windows machine directly. An earlier real experiment (`MusicVideoCompanion Local Agent v0.2.1`) proved a workable outbound-only shape: a Yandex Cloud Function exposes a permanent public URL while the Windows agent polls it and posts results back. That avoids inbound ports, NAT/router configuration and temporary third-party tunnels.

The old experiment polled once per second and kept state in the function-side implementation. Stage 4 keeps the proven `poll/result` behavior but hardens it for the current Rust platform.

## Architecture

```text
ChatGPT / MCP
      |
      | HTTPS
      v
Yandex Cloud Function (public permanent endpoint)
      |
      | small JSON state only
      v
mounted Object Storage bucket
      ^
      | outbound HTTPS long poll / result
      |
agent-platform.exe on Windows
      |
      +-- Project Binding
      +-- Capability lock
      +-- Policy Enforcement Point
      +-- Windows Credential Manager
      +-- local Rust capabilities
```

Yandex contains no FFmpeg/REAPER/Matchering business logic and does not store media payloads. The mounted bucket is only a rendezvous store for task/result/heartbeat JSON.

## Manual lifecycle

The relay is deliberately **off by default**. No Windows autostart is introduced.

- `agent-platform relay configure` stores the relay token in Windows Credential Manager.
- `agent-platform relay start --endpoint <https-url>` starts a hidden detached worker from the same binary.
- `agent-platform relay status` reports configured/running/stopping/stopped and heartbeat data.
- `agent-platform relay stop` requests shutdown. The worker exits after the current long poll, bounded by 30 seconds.
- `agent-platform relay remove-token` removes the saved Credential Manager entry.

A stopped worker sends no polls. Starting again reuses the Credential Manager token and does not require reconfiguration.

## Long polling

The worker requests `wait_seconds=25`; the function accepts at most 30 seconds. While the worker is enabled this reduces idle request rate drastically compared with the v0.2.1 one-second polling loop while retaining near-immediate task pickup.

The gateway records a heartbeat during polling. `tools/call` returns `AGENT_OFFLINE` immediately when the heartbeat is absent/stale instead of creating a task and waiting until its deadline.

## Stage 4 exposed operations

Only two low-risk operations are exported during transport validation:

- `local_ping`
- `runtime_self_test`

The relay request JSON Schema itself enumerates those operations. The Rust dispatcher has the same allowlist. Unknown operations cannot become arbitrary CLI/shell execution.

Higher-value capabilities (`audio.mastering_produce`, `audio.reference_master`, `audio.reaper_render`, media operations) remain local and are intentionally not exposed until the transport/auth E2E gate has passed.

## Authentication and secrets

The local worker uses `X-Agent-Token` against the cloud function. The token:

- is stored locally only in Windows Credential Manager;
- is resolved only for locked executor `rust.local.relay`;
- is never returned in tool results or runtime status;
- is passed to `curl` through stdin config, not a command-line argument and not a config file;
- is held in zeroized buffers where the existing Secret Store permits.

The gateway supports optional `MCP_TOKEN` / `X-MCP-Token` for the public MCP side. Until a ChatGPT-compatible production authentication path is proven, Stage 4 exports only the two low-risk tools above.

## Reliability / idempotency

Task IDs are `rly_<32 hex>` with a deadline. The local worker caches each completed `relay-response-v1` by task ID for 24 hours. If result upload fails and Yandex returns the same pending task, the cached response is posted again without re-executing the local operation.

Retryable network failures back off from 1 to 15 seconds. Status heartbeat older than 90 seconds is treated as stopped locally. Corrupt status/cache state fails closed.

## Cloud state

The Yandex Function uses a mounted Object Storage bucket (`/function/storage/relay` by default) as shared small-object state. This avoids relying on one warm function instance and avoids a VM, Redis or database. Recommended function execution timeout is at least 70 seconds, which covers a 25-second agent long poll and a <=60-second MCP call wait.

Suggested object layout:

```text
tasks/rly_*.json
results/rly_*.json
agents/<project>.json
```

Stale tasks and old results are cleaned opportunistically.

## Evidence and exit gate

Current code/CI can prove:

1. contracts and allowlist;
2. gateway agent authentication;
3. immediate offline response;
4. local threaded long-poll task/result rendezvous;
5. Rust policy/secret/lifecycle code compiles and passes strict Clippy/tests;
6. no new Rust transport dependency is required; the worker uses the OS `curl` already proven in the old Windows experiment.

Stage 4 remains **partial / E2E-ready** until one real path succeeds:

```text
ChatGPT MCP tools/call
  -> real Yandex Function URL
  -> mounted Object Storage task
  -> enabled Windows agent-platform relay worker
  -> local runtime_self_test
  -> result back through Yandex
  -> ChatGPT receives the local result
```

Only after that evidence may Stage 4 and the Hosted Chat -> local portion of Stage 0 be marked `done`.
