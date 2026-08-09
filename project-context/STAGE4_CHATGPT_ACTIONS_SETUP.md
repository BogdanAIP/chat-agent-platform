# Stage 4 — one-time ChatGPT Actions setup

This is the current fallback/primary user path when custom MCP developer mode is not available on the user's ChatGPT plan. It does **not** change the transport architecture: GPT Actions and MCP call the permanent Yandex API Gateway, which invokes the relay Cloud Function and rendezvous with the explicitly enabled local `agent-platform.exe` through Object Storage and the same outbound long-poll channel.

Direct GPT Actions calls to the raw Yandex Function URL are intentionally **not** used. Yandex Cloud Functions consume `Authorization` for platform invocation, so the arbitrary GPT Actions Bearer token must enter through API Gateway instead.

## Preconditions

Run the real Yandex provisioning/acceptance script first. It must finish with `stage4-yandex-acceptance-v1` / `status=success`.

The real transport acceptance passed on 2026-08-09 through:

```text
Yandex API Gateway
  -> Cloud Function
  -> Object Storage rendezvous
  -> outbound Windows relay
  -> local_ping + runtime_self_test
```

That script leaves:

- the API Gateway URL inserted into `runtime/relay/actions-openapi.json`;
- the GPT Actions bearer token in the Windows clipboard exactly once;
- the local agent token only in Windows Credential Manager;
- the local relay switched off again by default unless `-LeaveRelayOn` was explicitly requested;
- acceptance evidence at `runtime/stage4-yandex-acceptance.json` without either secret token.

Neither token is written into the OpenAPI schema or committed files.

## Create the private GPT Action once

In ChatGPT web:

1. Open the GPT creation/editing UI available to the paid account.
2. Create a private GPT for this project, for example `Agent Platform Local`.
3. In **Actions**, choose **Create new action**.
4. Paste the complete contents of local `runtime/relay/actions-openapi.json` into the schema field.
5. Configure authentication as **API key -> Bearer**.
6. Paste the token currently in the Windows clipboard. Do not copy it into project files, notes, commits, screenshots or chat messages.
7. Keep the GPT private unless there is a deliberate later decision to publish it.
8. Save/create the GPT.

The required technical properties are fixed even if UI wording changes: generated OpenAPI schema whose `servers[0].url` is the Yandex API Gateway + separate remote Bearer authentication.

## Normal use

The Yandex Gateway/Function may remain deployed all the time; the Windows worker does not.

Before local work, from the configured local repository/runtime:

```text
agent-platform relay start --project-id chat-agent-platform
```

Optional check:

```text
agent-platform relay status --project-id chat-agent-platform
```

In a normal ChatGPT conversation, invoke the private GPT and request one of the currently exposed Stage 4 operations. The conversation can remain the primary project context while the GPT Action supplies the remote tool call.

After local work:

```text
agent-platform relay stop --project-id chat-agent-platform
```

A stopped relay sends no polling requests. The API Gateway remains reachable but authenticated local operations return `AGENT_OFFLINE` instead of creating a permanently pending local task.

## Final Stage 4 acceptance calls

Before exposing any higher-value local capability, verify through **ChatGPT itself**:

1. start the Windows relay;
2. invoke `local_ping` from the private GPT Action with a distinctive message;
3. invoke `runtime_self_test` from the private GPT Action;
4. stop the relay;
5. optionally repeat `local_ping` and confirm `AGENT_OFFLINE`.

Expected facts:

- `local_ping` returns `pong=true` and `executed_locally=true`;
- `runtime_self_test` returns `status=success`, `ping=pong`, successful controlled write/read and cleanup;
- after `relay stop`, the same remote call reports the agent offline rather than executing locally.

Only this ChatGPT-originated round trip closes the final Stage 4 exit gate. The already-completed provisioning acceptance proves the real Yandex API Gateway -> Windows transport, but it does not pretend to be evidence that ChatGPT itself successfully originated the request.

## Rotation / recovery

Normal redeployments reuse the current two tokens so an already-configured private GPT does not break unnecessarily. Use the deployment/provisioning `-RotateTokens` switch when rotation is actually required.

If the GPT Actions bearer token is lost or suspected exposed:

1. rerun provisioning with `-RotateTokens`;
2. replace the GPT Action Bearer value with the newly copied token;
3. keep the new local agent token only in Credential Manager;
4. rerun the two acceptance calls.

If local access should be disabled temporarily, use `relay stop`; token rotation is not necessary.

If the integration is retired, remove the GPT Action, run `relay remove-token`, and remove the dedicated API Gateway/Function/bucket/service account only through an explicit cleanup procedure. Cloud resource deletion is intentionally not part of ordinary `relay stop`.