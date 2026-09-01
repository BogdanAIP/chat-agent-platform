# CAP Temporary Reviewer — automatic physical experiment

Status: **EXPERIMENT ONLY — NO PRODUCTION AUTHORITY**

This probe answers one question before any new automatic-reviewer architecture is selected:

> Can a fully automatically launched non-personalized Temporary Chat perform a real independent semantic review of a public CAP PR, without ChatGPT plugins and without manual prompt/result copy-paste?

It deliberately does **not** implement or authorize production `launch_independent_review_v1`, Native Messaging, result publication, a new public tool, a scheduler, or a new reviewer security-context decision.

## Controls

The launcher has three fixed controls. The control identity is selected locally; the review prompt itself does not reveal the known historical outcome.

### `pass142`

Already merged final head of PR #142:

```text
repository=BogdanAIP/chat-agent-platform
pr_number=142
base_sha=8318a592848cad66bb6d8e56b10b04b646bc9137
head_sha=858dcb7dd065717ea0d59b1e7b931b13a844f8d4
review_skill=code-review
review_skill_version=1.1
known accepted outcome=no surviving findings
```

### `stale140`

Historical intermediate head of PR #140:

```text
repository=BogdanAIP/chat-agent-platform
pr_number=140
base_sha=b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
head_sha=7077ecb8496ee89530cbe5efaa1b2112e7be330f
review_skill=code-review
review_skill_version=1.0
known expected protocol outcome=STALE because live PR #140 advanced materially
```

This control now exists to verify exact live-identity discipline, not defect detection.

### `findings146`

Live experiment-only PR #146 reproduces the exact historical `BASE..HEAD` range above under a new current PR identity:

```text
repository=BogdanAIP/chat-agent-platform
pr_number=146
base_sha=b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
head_sha=7077ecb8496ee89530cbe5efaa1b2112e7be330f
review_skill=code-review
review_skill_version=1.0
known historical outcome=multiple confirmed findings existed in this exact diff
```

PR #146 is a Draft experiment control and is never to be merged. Its prompt does not disclose the historical defects or finding count. It exists because BASE v1.0 correctly forbids semantic review of the same superseded head under the original PR #140 identity.

## Target-Windows observations

### `pass142`

The first physical run on 2026-09-01 used run id:

```text
tmprev-dca1dbf983014bce8341623c8b8fb943
```

Observed automatically:

```text
collector ready
 -> non-personalized Temporary Chat launched
 -> REVIEW_REQUEST_V1 delivered without clipboard/manual paste
 -> Send occurred without user click
 -> reviewer independently used built-in web/public GitHub evidence
 -> final reviewer response returned REVIEW_RESULT_V1 status=PASS
```

The semantic outcome matched the known accepted PR #142 outcome. The original capture heuristic recorded `UNSTRUCTURED` because it treated an eight-second pause between web-search phases as terminal and captured a progress response before the actual final result existed.

### `stale140`

The second physical run used run id:

```text
tmprev-0269cce47a08437c92084f43e60affa5
```

The reviewer independently discovered that the supplied `7077ecb...` head was no longer the live head of PR #140 and correctly returned:

```text
status=STALE
review_validity=STALE_MATERIAL_CHANGE
```

It also appended the exact run-bound completion marker. This is positive evidence that a plugin-free Temporary Chat can reconstruct live GitHub identity and obey the governing BASE policy instead of blindly reviewing a stale requested head. It is not evidence about finding-recall quality because BASE v1.0 requires termination before semantic findings on that stale identity.

The collector marked this completed response `unstructured` due to brittle rendered-text field matching. The experiment parser is now field-based and tolerates Markdown escaping/whitespace; unstructured captures also print exact identity diagnostics.

These observations are **transport/protocol evidence, not production acceptance**.

## Automatic path

After one-time extension setup, one PowerShell command performs the experiment:

```text
PowerShell launcher
 -> random run id + collector token
 -> experiment-only loopback collector on 127.0.0.1:3077
 -> exact REVIEW_REQUEST_V1 encoded into ChatGPT deep link
 -> https://chatgpt.com/?temporary-chat=true...
 -> extension requires positive Temporary-Chat UI evidence
 -> one Send attempt, marked before click
 -> fresh ChatGPT reviewer works using built-in web/public repository evidence
 -> reviewer ends its final response with the exact run-bound completion marker
 -> extension waits for that marker plus a short stable interval
 -> captures structured REVIEW_RESULT_V1 or completed unstructured response
 -> extension service worker POSTs only experiment evidence to 127.0.0.1:3077
 -> collector atomically writes result.json under LocalAppData
```

There is no clipboard step and no user prompt/result copy-paste.

## One-time Chrome setup

This is the only intentionally manual setup step for the physical experiment:

1. checkout or unpack the exact probe extension;
2. open `chrome://extensions`;
3. enable **Developer mode**;
4. choose **Load unpacked**;
5. select the extension directory.

If the extension is already loaded, use **Reload** after updating its files.

The extension has no `nativeMessaging`, filesystem, tabs, scripting or generic network permission. Its only host permission is:

```text
http://127.0.0.1:3077/*
```

The loopback collector is experiment-only. It accepts no command, procedure, path, URL, GitHub credential or MCP request. It can only record bounded probe events and one bounded captured assistant result for the exact random run id/token supplied by the launcher.

## Run

From repository root in PowerShell 7:

```powershell
./scripts/launch-temporary-reviewer-probe.ps1 -Control pass142
./scripts/launch-temporary-reviewer-probe.ps1 -Control stale140
./scripts/launch-temporary-reviewer-probe.ps1 -Control findings146
```

Expected early markers:

```text
TEMP_REVIEW_CONTROL=...
TEMP_REVIEW_TARGET_PR=...
TEMP_REVIEW_TARGET_BASE=...
TEMP_REVIEW_TARGET_HEAD=...
TEMP_REVIEW_RUN_ID=...
TEMP_REVIEW_EXTENSION_PATH=...
TEMP_REVIEW_OUTPUT_DIR=...
TEMP_REVIEW_COLLECTOR=ready
TEMP_REVIEW_LAUNCHING=non-personalized-temporary-chat
```

On completed capture:

```text
TEMP_REVIEW_CAPTURE=structured|unstructured
TEMP_REVIEW_STATUS=PASS|FINDINGS|ABSTAIN|STALE|UNSTRUCTURED
TEMP_REVIEW_RESULT_PATH=...
```

When a completed response fails structured identity parsing, the launcher also prints `TEMP_REVIEW_IDENTITY_DIAGNOSTICS=...` so parser/UI drift is observable rather than guessed.

## Fail-closed boundaries

The extension does not Send unless all of these are true:

- origin is exactly `https://chatgpt.com`;
- `temporary-chat=true` is present;
- experiment opt-in and run id/token are valid;
- the visible composer contains the matching run sentinel and `REVIEW_REQUEST_V1`;
- the request contains a valid exact repository/PR/BASE/HEAD/skill identity;
- a Temporary-Chat UI marker exists outside the composer;
- the Send control is enabled;
- that run id has not already caused a Send attempt in the tab session.

The attempt marker is written before `button.click()`. There is no automatic same-run review-request retry after an ambiguous click.

Result capture requires the exact run-bound completion marker at the end of the final assistant response. A completed response can still be recorded as `unstructured` when the protocol identity/status is invalid; browser capture is **not** production result authority.

## What this experiment can prove

It can provide physical evidence about:

- whether `temporary-chat=true` still reaches the expected real UI;
- whether the existing logged-in Plus browser session can be driven automatically;
- whether a Temporary Chat can obtain enough public GitHub/web evidence for the repository's real review protocol;
- whether it returns a structurally useful `REVIEW_RESULT_V1` without plugins;
- whether it obeys exact live-identity/staleness rules;
- whether review quality appears comparable on positive and live known-finding controls;
- where UI/transport failures occur without asking the user to paste anything.

It cannot by itself prove:

- that Temporary Chat is the final production reviewer security boundary;
- that absence of plugins is safely inferable forever from one DOM marker;
- that a Native Messaging handoff should be selected;
- that the automatic reviewer meets quality targets across representative PRs;
- any production launch, Send or result-authority acceptance.

Those decisions require fresh Stage Research after physical evidence exists.
