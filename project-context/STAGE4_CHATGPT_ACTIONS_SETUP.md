# Stage 4 — one-time ChatGPT Actions setup

This is the current fallback/primary user path when custom MCP developer mode is not available on the user's ChatGPT plan. It does **not** change the transport architecture: GPT Actions and MCP call the same permanent Yandex Function, which rendezvous with the explicitly enabled local `agent-platform.exe` through the same outbound long-poll channel.

## Preconditions

Run the real Yandex provisioning/acceptance script first. It must finish with `stage4-yandex-acceptance-v1` / `status=success`.

That script leaves:

- the Yandex Function URL already inserted into `runtime/relay/actions-openapi.json`;
- the GPT Actions bearer token in the Windows clipboard exactly once;
- the local agent token only in Windows Credential Manager;
- the local relay switched off again by default unless `-LeaveRelayOn` was explicitly requested.

Neither token is written into the OpenAPI schema or acceptance JSON.

## Create the private GPT Action once

In ChatGPT web:

1. Open the GPT creation/editing UI available to the paid account.
2. Create a private GPT for this project (for example `Agent Platform Local`).
3. In **Actions**, create/import an action schema.
4. Paste the complete contents of `runtime/relay/actions-openapi.json`.
5. Configure action authentication as an API key / bearer token.
6. Paste the token currently in the Windows clipboard. Do not copy it into project files, notes, commits or chat messages.
7. Keep the GPT private unless there is a deliberate later decision to publish it.
8. Save the GPT.

UI wording can change, but the required technical properties are fixed: OpenAPI schema from the generated file + bearer authentication using the separately generated remote token.

## Normal use

The cloud endpoint may remain deployed all the time; the Windows worker does not.

Before local work:

```text
agent-platform relay start
```

Optional check:

```text
agent-platform relay status
```

In a normal ChatGPT conversation, invoke the private GPT using `@` and request one of the currently exposed Stage 4 operations. The conversation can remain the primary project context while the GPT Action supplies the remote tool call.

After local work:

```text
agent-platform relay stop
```

A stopped relay sends no polling requests. The Yandex Function remains reachable but returns `AGENT_OFFLINE` immediately for local operations.

## Stage 4 acceptance calls

Before exposing any higher-value local capability, verify both through ChatGPT itself:

1. `local_ping` with a distinctive message;
2. `runtime_self_test`.

Expected facts:

- `local_ping` returns `pong=true` and `executed_locally=true`;
- `runtime_self_test` returns `status=success`, `ping=pong`, successful controlled write/read and cleanup;
- after `relay stop`, the same remote call returns `AGENT_OFFLINE` rather than creating a pending local task.

Only this ChatGPT-originated round trip closes the final Stage 4 exit gate. The automated provisioning script proves the real Yandex→Windows transport before this manual UI step, but it does not pretend to be ChatGPT-originated evidence.

## Rotation / recovery

If the GPT Actions bearer token is lost, do not retrieve the local agent token or reuse it. Create a new Yandex Function version via the deployment script, which rotates both independent tokens, then replace the GPT Action bearer token with the newly copied value.

If local access should be disabled temporarily, use `relay stop`; token rotation is not necessary.

If the integration is retired, remove the GPT Action, run `relay remove-token`, and then remove the dedicated Yandex Function/bucket/service account through an explicit operations cleanup procedure. Cloud resource deletion is intentionally not part of ordinary `relay stop`.