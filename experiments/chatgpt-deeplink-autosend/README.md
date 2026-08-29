# CAP ChatGPT Deep-Link AutoSend (experimental)

A minimal unpacked Chrome Manifest V3 extension for one narrow experiment:

```text
explicit ChatGPT deep link
 -> fresh ordinary Chat
 -> @Chat Local Bridge Test plugin chip
 -> extension verifies run id + plugin in composer
 -> exactly one Send attempt
```

It does **not** call the Local Bridge, any model API, Work, Codex, shell, filesystem, or network API. It has no extension permissions beyond the static content-script match for `https://chatgpt.com/*`.

The `cap_run_id` below is only a correlation/deduplication identifier. It is **not a secret, credential, capability token, or authorization grant**.

## Install for the physical probe

1. Open `chrome://extensions`.
2. Enable **Developer mode**.
3. Choose **Load unpacked**.
4. Select this directory: `experiments/chatgpt-deeplink-autosend`.
5. Keep the ChatGPT account logged in and the local `Chat Local Bridge Test` plugin available.

## Build a one-shot probe URL

Use a fresh run id for every intended new worker. Example:

```text
autosend-run-example-001
```

Prompt before URL encoding:

```text
@Chat Local Bridge Test DEEPLINK_AUTOSEND_GATE
CAP_AUTOSEND_RUN_ID=autosend-run-example-001

Use only Chat Local Bridge Test. Call workspace_read exactly once on stage26-3b-browser-real-task.txt. If the callable tool is exposed and the call reaches the bridge, report DEEPLINK_AUTOSEND_BRIDGE=PASS. A downstream bridge/tunnel error still counts as exposed. Do not modify any file or repository.
```

The launch URL must include all four pieces:

```text
https://chatgpt.com/?cap_autosend=1&cap_run_id=<RUN_ID>&cap_plugin=Chat%20Local%20Bridge%20Test&prompt=<URL_ENCODED_PROMPT>
```

The query run id must also appear literally in the visible prompt as:

```text
CAP_AUTOSEND_RUN_ID=<RUN_ID>
```

This duplicate binding is intentional. The extension refuses to click Send if the URL and visible composer do not agree.

## Fail-closed behavior

The extension does nothing when any of these is true:

- the page is not `https://chatgpt.com`;
- `cap_autosend=1` is absent;
- the run id is absent/invalid;
- the visible prompt lacks the matching `CAP_AUTOSEND_RUN_ID=...` sentinel;
- the expected plugin name is not visible in the same composer as Send;
- the reviewed `button[data-testid="send-button"]` control is absent or disabled;
- readiness is not achieved within 30 seconds;
- that run id already caused an attempt in the current tab session.

The one-shot marker is written **before** `button.click()`. An ambiguous click therefore never causes an automatic same-run retry.

## What this experiment intentionally does not solve

- Windows Task Scheduler integration;
- generating/rotating run ids;
- cross-browser-restart deduplication;
- deciding when a worker should wake;
- WorkingState/task lease ownership;
- detecting worker completion;
- rotating to another fresh chat;
- ChatGPT DOM compatibility beyond the physically qualified build.

Those remain blocked until the single-send physical gate is proven.

## Focused tests

The repository Python suite validates the narrow manifest and executes the JavaScript policy through Node:

```text
python -m unittest tests.test_chatgpt_deeplink_autosend_extension
```

A real ChatGPT physical probe is still required because the private ChatGPT composer DOM and plugin-chip behavior cannot be truthfully represented by a hosted unit test.
