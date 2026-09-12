# CAP Temporary Reviewer — automatic physical experiment

Status: **EXPERIMENT ONLY — NO PRODUCTION AUTHORITY**

This probe answers transport/quality questions before any new automatic-reviewer architecture is selected. It deliberately does **not** implement or authorize production `launch_independent_review_v1`, result publication, Native Messaging, a new public tool, a scheduler, or a final reviewer security-context decision.

The common requirement is a fresh ordinary Temporary Chat with **without manual prompt/result copy-paste** after one-time unpacked-extension setup.

## Controls

### `pass142`

Merged PR #142 exact final identity:

```text
base=8318a592848cad66bb6d8e56b10b04b646bc9137
head=858dcb7dd065717ea0d59b1e7b931b13a844f8d4
review_skill_version=1.1
known accepted outcome=no surviving findings
```

Physical run `tmprev-dca1dbf983014bce8341623c8b8fb943` automatically launched Temporary Chat and returned `REVIEW_RESULT_V1 status=PASS`.

### `stale140`

Historical intermediate PR #140 identity:

```text
base=b10a5fa3122bb6c76c12d37d67911b88e5e1ce28
head=7077ecb8496ee89530cbe5efaa1b2112e7be330f
review_skill_version=1.0
```

Physical run `tmprev-0269cce47a08437c92084f43e60affa5` independently discovered that the requested head was superseded and correctly returned `STALE / STALE_MATERIAL_CHANGE`.

### `findings146`

Experiment-only live PR #146 reproduced the same exact historical defective `BASE..HEAD` range under a current PR identity. Physical run `tmprev-52933398b0074575b1e0b2fb87ae1036` completed as:

```text
TEMP_REVIEW_CAPTURE=structured
TEMP_REVIEW_STATUS=FINDINGS
```

The reviewer returned `CURRENT`, **reported exactly four P1 findings**, rejected one candidate, and independently recovered the same four historical categories later recorded in merged PR #140 as `CONFIRMED -> FIXED MATERIALLY`:

1. GitHub mutation authority qualified by non-selection rather than write-action unreachability;
2. ambiguous result publication racing manual fallback;
3. missing direct POSIX/Python, W3C IndexedDB and Chrome service-worker evidence;
4. compound/non-canonical architecture-lineage decisions.

The review prompt did not disclose those defects or their count.

### `privatebundle140`

Private-repository simulation using no public repository lookup. The launcher builds `REVIEW_EVIDENCE_BUNDLE_V1` from local immutable Git objects only, pseudonymizes repository identity/40-hex values, and injects the complete text into the Temporary Chat composer before one Send.

The bundle carries a random `bundle_nonce`; the final result must echo it. This mode forbids external web/repository evidence and exists only to isolate bundle-only semantic quality.

### `libraryfile140`

Private-repository simulation using **ChatGPT Library as the file transport**.

The launcher builds the same pseudonymized `REVIEW_EVIDENCE_BUNDLE_V1` as a uniquely named supported text file:

```text
cap-private-review-tmprev-<run-id>.txt
```

Then one browser flow performs:

```text
local immutable Git objects
 -> loopback collector
 -> regular ChatGPT composer
 -> extension creates a browser File object and uploads it
 -> ChatGPT saves the upload to Library
 -> same tab navigates to non-personalized Temporary Chat
 -> extension opens Add from library
 -> selects the exact run-bound filename
 -> verifies the file is attached
 -> one automatic Send
 -> Temporary Chat performs semantic review
 -> extension captures the final result
 -> result.json
```

The random evidence nonce exists only inside the file. It is stored by the extension in tab-scoped `sessionStorage` after SHA-256 verification and is not placed into the review prompt or URL. A completed Library result is structured only when it contains:

```text
LIBRARY_PRIVATE_REVIEW_RESULT_V1
evidence_nonce=<exact nonce read from the attached file>
evidence_source=library_file
external_research_used=no|yes
status=PASS|FINDINGS|ABSTAIN
reported_findings=<count>
```

Unlike `privatebundle140`, Library mode allows generic public technical research. The reviewer is instructed not to use GitHub/web to locate or reconstruct the private repository, and not to search for private identifiers or code snippets. It may use public web documentation for general engineering semantics.

This control first uses TXT because current ChatGPT documentation explicitly supports common text/document formats; ZIP support is not assumed by this experiment.

### `exact`

Bounded experiment-only self-review target mode for `BogdanAIP/chat-agent-platform`. It accepts only PR number, exact 40-hex BASE/HEAD and review skill version `1.0|1.1`. Repository identity and neutral semantic-review focus stay fixed in the launcher; there is no caller-supplied reasoning/focus field.

## Local evidence package

`build_private_bundle.py` performs local `git show` / `git diff` operations only. It has no GitHub/API/network client. The package contains:

- pseudonymized manifest identity and random nonce;
- `AGENTS.md` from BASE;
- `code-review` skill from BASE;
- applicable Stage Research/source-code-research skills from HEAD when present;
- baseline architecture owner;
- changed-file inventory;
- exact `BASE..HEAD` diff.

The builder is intentionally bounded to 900,000 bytes for this physical experiment.

## Extension/collector boundary

The extension has no `nativeMessaging`, filesystem, tabs, scripting, GitHub or generic network permission. Its only host permission is:

```text
http://127.0.0.1:3077/*
```

The service worker accepts only `event`, `capture`, or authenticated bundle fetch messages from `https://chatgpt.com`. The collector is loopback-only, requires the exact random collector token for `/bundle`, `/event` and `/capture`, and has no execution/GitHub/MCP backend.

For Library staging, the extension receives text bytes from the authenticated loopback collector, constructs an in-memory browser `File`, assigns it to ChatGPT's file input via `DataTransfer`, and dispatches the normal upload change event. It does not receive a local filesystem path or native filesystem authority.

## Result capture

All modes use a run-bound terminal marker. A protocol status is printed only when `capture_kind=structured`; malformed/unbound output is reported as `TEMP_REVIEW_STATUS=UNSTRUCTURED` with diagnostics.

The experiment collector is not production result authority. BASE `code-review` v1.1 still reserves authoritative automatic handoff for the accepted project-owned submit/reconcile state machine.

## Run

```powershell
./scripts/launch-temporary-reviewer-probe.ps1 -Control pass142
./scripts/launch-temporary-reviewer-probe.ps1 -Control stale140
./scripts/launch-temporary-reviewer-probe.ps1 -Control findings146
./scripts/launch-temporary-reviewer-probe.ps1 -Control privatebundle140
./scripts/launch-temporary-reviewer-probe.ps1 -Control libraryfile140
```

Expected Library markers begin with:

```text
TEMP_REVIEW_CONTROL=libraryfile140
TEMP_REVIEW_EVIDENCE_MODE=chatgpt_library_file
TEMP_REVIEW_LIBRARY_FILENAME=...
TEMP_REVIEW_LIBRARY_NONCE_DISCLOSED_TO_PROMPT=False
TEMP_REVIEW_COLLECTOR=ready
TEMP_REVIEW_LAUNCHING=regular-chat-library-stage-then-temporary-chat
```

A successful complete run should end with at least:

```text
TEMP_REVIEW_CAPTURE=structured
TEMP_REVIEW_STATUS=PASS|FINDINGS|ABSTAIN
TEMP_REVIEW_LIBRARY_FILE_ATTACHED=True
TEMP_REVIEW_LIBRARY_FILENAME_CAPTURED=...
TEMP_REVIEW_RESULT_PATH=...
```

## What this experiment can and cannot prove

It can provide physical evidence for automatic Temporary Chat launch, public-web review, stale identity discipline, known-finding recall, local bundle delivery, and ChatGPT Library file reuse in a fresh Temporary Chat.

It cannot by itself prove the final production reviewer security boundary, long-term DOM stability, safe private-code research policy, representative benchmark quality, production result handoff, or merge authority.

Those decisions require fresh Stage Research after physical evidence exists.
