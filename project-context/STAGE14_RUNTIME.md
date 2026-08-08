# Stage 14 Persistent Job Runtime

Status: **passed in Windows CI**

Stage 14 selects the built-in Rust job state machine as the workflow runtime. No
Prefect, Node-RED, daemon, service, database, message broker or extra process is
introduced.

## Runtime contract

Persistent state uses `job-v1` and is stored under the bound project local root at
`runtime/jobs/<project_id>/`. Each job records capability, status, timestamps,
idempotency key, attempt number, optional checkpoint, result and structured error.
Writes are atomic and the store uses an inter-process lock.

Supported transitions:

- begin: create `queued` or return the existing job for the same idempotency key;
- resume: `queued → running`, or retry a retryable `failed → running` while
  incrementing `attempt` and preserving the checkpoint;
- checkpoint: only while `running`;
- succeed/fail: only while `running`;
- cancel: only from `queued` or `running`;
- succeeded/cancelled and non-retryable failures cannot be resumed.

Persisted JSON is validated against the embedded job contract on read and write.
Corrupt or identity-mismatched state fails closed and is preserved for diagnosis.

## Acceptance coverage

Windows CI run #109 passed:

1. concurrent idempotent begin from eight threads creates exactly one job;
2. reuse of the same idempotency key with another capability is denied;
3. checkpoint + retry + result survive construction of new `JobStore` instances;
4. retry increments `attempt` while retaining the checkpoint;
5. terminal and non-retryable transitions are denied;
6. corrupt state blocks the store operation and is not deleted;
7. a process-level integration test invokes the compiled `agent-platform` binary in
   separate processes for begin → resume → checkpoint → get → retryable failure →
   resume → succeed → get, proving persistence across process/session boundaries;
8. the complete existing Rust/contracts/Python/parity/release regression stays green.

## Exit-gate conclusion

The internal Rust runtime satisfies the Stage 14 need for persistence,
idempotency, checkpoints, retry/resume and cancellation without adding a separate
workflow service. Stage 15 can therefore use this runtime directly. An external
workflow engine remains unjustified unless a later real scenario exceeds these
capabilities.
