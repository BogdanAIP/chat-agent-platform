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

One-time setup stores both pieces that should persist locally:

- public Yandex Function endpoint in `runtime/relay/config.json`;
- `secret://relay/agent_token` in Windows Credential Manager.

`runtime/relay/config.json` never contains the token.

Normal use after setup is intentionally only:

```text
agent-platform relay start
agent-platform relay status
agent-platform relay stop
```

- `relay configure --endpoint <https-url>` is the one-time configuration action and stores the token from a named environment variable through the existing Secret Store.
- `relay start` starts a hidden detached worker from the same `agent-platform.exe`; endpoint/token reference come from the saved local configuration. Explicit overrides exist for diagnostics only.
- `relay status` reports configured/running/stopping/stopped and heartbeat/task data.
- `relay stop` requests shutdown. The worker exits after the current long poll, bounded by 30 seconds, then sends an authenticated `offline` notification to Yandex.
- `relay remove-token` removes the saved Credential Manager entry and local relay configuration.

A stopped worker sends no polls. Starting again requires no Yandex URL and no token entry. A crash/power loss is detected by heartbeat TTL; an orderly `stop` marks the cloud side offline immediately.

## Long polling

The worker requests `wait_seconds=25`; the function accepts at most 30 seconds. While the worker is enabled this reduces idle request rate drastically compared with the v0.2.1 one-second polling loop while retaining approximately one-second task pickup with the current bucket scan interval.

The gateway refreshes heartbeat at most once per 10 seconds during polling. `tools/call` returns `AGENT_OFFLINE` immediately when heartbeat is absent/stale instead of creating a task and waiting until its deadline.

## Stage 4 exposed operations

Only two low-risk operations are exported during transport validation:

- `local_ping`
- `runtime_self_test`

The relay request JSON Schema itself enumerates those operations. The Rust dispatcher has the same allowlist. Unknown operations cannot become arbitrary CLI/shell execution.

Higher-value capabilities (`audio.mastering_produce`, `audio.reference_master`, `audio.reaper_render`, media operations) remain local and are intentionally not exposed until the transport/auth E2E gate has passed.

## Authentication and secrets

The local worker uses `X-Agent-Token` against the cloud function. The token:

- is stored locally only in Windows Credential Manager;
- uses the platform Secret Store reference `secret://relay/agent_token`;
- is resolved only for locked executor `rust.local.relay`;
- is never returned in tool results or runtime status;
- is passed to `curl` through stdin config, not a command-line argument and not a config file;
- is held in zeroized buffers where the existing Secret Store permits.

The gateway supports optional `MCP_TOKEN` / bearer authentication for the public MCP side. Until a ChatGPT-compatible production authentication path is proven, Stage 4 exports only the two low-risk tools above.

## Reliability / idempotency

Task IDs are `rly_<32 hex>` with a deadline. The local worker caches each completed `relay-response-v1` by task ID for 24 hours. If result upload/acknowledgement fails and Yandex returns the same pending task, the cached response is posted again without re-executing the local operation.

The Windows integration test intentionally simulates a lost first result acknowledgement and requires the second response for the same request ID to be identical to the cached first response.

Retryable network failures back off from 1 to 15 seconds. Status heartbeat older than 90 seconds is treated as stopped locally. Corrupt status/cache state fails closed.

## Cloud state and minimum runtime privilege

The Yandex Function uses a mounted Object Storage bucket (`/function/storage/relay`) as shared small-object state. This avoids relying on one warm function instance and avoids a VM, Redis, database or message broker. Function concurrency can remain one request per instance because separate instances rendezvous through the shared bucket.

The runtime service account needs only bucket role `storage.uploader`: read, write and overwrite. The gateway intentionally contains **no object-delete primitive**. It therefore does not need the broader `storage.editor` role just to maintain the relay queue.

Object layout:

```text
tasks/rly_*.json
results/rly_*.json
agents/<project>.json
```

State is append/overwrite:

- new tasks start with `status=pending`;
- successful result writes a result object and overwrites the task as `completed`;
- timed-out MCP calls overwrite the task as `timed_out`;
- orderly local shutdown overwrites heartbeat with `last_seen_unix_ms=0` and an empty operations list;
- completed/timed-out tasks are never offered by `poll` again;
- identical duplicate results are idempotently acknowledged; a different result for the same request ID is rejected.

Physical deletion of old task/result/heartbeat JSON is delegated to the lifecycle rule on the **dedicated relay bucket**, applied by Yandex Object Storage outside the Function runtime permission set.

## Repeatable Yandex deployment

`scripts/deploy-stage4-yandex.ps1` performs the cloud/bootstrap part in one run using the authenticated `yc` CLI:

1. create/reuse one dedicated service account;
2. create/reuse one private dedicated Object Storage bucket;
3. grant that service account only `storage.uploader` on that bucket;
4. install a one-day lifecycle rule for the dedicated bucket;
5. create a Cloud Function or, when `-FunctionId` is supplied, create a new version of the existing function while preserving its Function ID and public URL;
6. mount the bucket read/write at `/function/storage/relay`;
7. generate a random agent token, put it in the Function environment and immediately store the same token locally through `relay configure` into Windows Credential Manager;
8. expose the Function URL for MCP and verify its health endpoint;
9. leave the local relay switched **off** unless `-StartRelay` was explicitly supplied.

When an explicitly named pre-existing bucket is supplied, the script does not overwrite its lifecycle unless `-AdoptExistingBucket` is explicitly set. The default generated bucket is dedicated to the relay and is lifecycle-managed automatically.

## Evidence and exit gate

Hosted CI is required to prove:

1. relay contracts and exact two-operation allowlist;
2. strict Rust fmt/Clippy and all prior platform regressions;
3. gateway agent authentication and optional MCP bearer auth;
4. immediate `AGENT_OFFLINE` behavior;
5. no-delete `storage.uploader` cloud-state model;
6. PowerShell syntax of the deployment script;
7. real Windows Credential Manager storage of a unique relay secret;
8. one-time configure followed by `start` with no URL argument;
9. detached `agent-platform.exe` worker -> local fake HTTP gateway round trip;
10. retry of one request ID after a simulated lost ACK without local re-execution;
11. real policy-gated `runtime_self_test` through the worker;
12. `stop` -> cloud `offline` -> final local `stopped` state.

Stage 4 remains **partial / E2E-ready** even after hosted CI is green. The final exit gate is one real path:

```text
ChatGPT MCP tools/call
  -> real Yandex Function URL
  -> mounted Object Storage task
  -> explicitly enabled Windows agent-platform relay worker
  -> local runtime_self_test
  -> result back through Yandex
  -> ChatGPT receives the local result
```

Only after that evidence may Stage 4 and the Hosted Chat -> local portion of Stage 0 be marked `done`.