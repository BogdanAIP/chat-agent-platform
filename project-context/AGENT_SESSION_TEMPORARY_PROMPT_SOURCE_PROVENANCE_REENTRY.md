# Agent Session Temporary-Chat prompt/source provenance re-entry

Status: **STAGE RESEARCH BRIEF — NARROW**

Research date: **2026-09-05**

Triggering PR: **#149**

Triggering reviewed HEAD: `8fae2b16989f828b1ad4e4ddbf439b9a54c959ef`

Accepted BASE: `90a8e16e6a1badecd3315968339ca691634b7ee4`

Applicable repository skills at the triggering HEAD:

- `.agents/skills/stage-research/SKILL.md` v1.2
- `.agents/skills/code-review/SKILL.md` v1.1

This brief is a fresh-review-triggered re-entry for two release-critical provenance gaps in the first `chatgpt-temporary` adapter. It does not broaden the product scope, add a persistent session, change the generic Delegation identity model, add another public tool, or authorize Prime/existing-session work.

## 1. Triggering review findings

Fresh ordinary-ChatGPT semantic review of exact HEAD `8fae2b16989f828b1ad4e4ddbf439b9a54c959ef` reported two P1 findings.

### A. Worker-visible prompt was not bound exactly before Send

The launch projection carried a correct `prompt_sha256`, but the live composer checks only required four marker substrings. Therefore the composer body could change while preserving those markers and still reach browser/project Send authority and `button.click()` under the digest of the original intended prompt.

Development-side falsification confirms the mechanism: `content.js` hashes `intent.prompt`, while `policy.hasExpectedPrompt()` checks only `WORKER_TASK_V1`, delegation id, delivery id and task digest markers in the current composer.

### B. Physical exact-source proof had a mutable-worktree TOCTOU

The launcher ran one clean exact-HEAD source gate, then rebuilt extension expected hashes and launched the Python controller from the same mutable worktree. A concurrent edit after the gate could therefore become either:

- newly trusted expected extension bytes; or
- actually imported controller/delegation bytes;

before another repository source gate ran. The post-result gate can reject qualification evidence, but cannot undo a Send or durable state transition already produced by changed bytes.

Development-side falsification confirms the launcher currently computes expected runtime asset hashes from the worktree and starts `python -m runtime.agent_sessions.chatgpt_temporary_controller` with `WorkingDirectory=$RepoRoot` after the point-in-time gate.

## 2. Exact stage question

> What is the smallest fail-closed correction that binds one Temporary worker Send to the exact intended worker-visible prompt and to exact reviewed runtime source bytes, without introducing a generic runtime framework or changing the ephemeral one-shot profile?

Required invariants:

- exact delegation/delivery/task/head/prompt correlation before the one physical Send;
- current worker-visible composer must match the intended prompt before Send authority is requested and again immediately before click;
- no changed worktree Python source may execute on the qualified path after the exact-head gate;
- expected extension attestation must be derived from exact reviewed source, not from mutable post-gate worktree bytes;
- changed installed/executing extension bytes must still fail closed before Send/capture;
- all previous one-Send, browser-lifetime, ACK-loss, timeout/result and result-correlation guarantees remain intact.

Out of scope:

- persistent conversations;
- Prime runtime integration;
- existing-session return delivery;
- a generic build system, package manager or universal executable attestation framework;
- defending against a fully privileged malicious local administrator who can alter the running launcher process or Git object database.

## 3. Architecture lineage

### Bounded Agent Session / Delegation lifecycle — `KEEP`

The generic deterministic identity, private run capability, durable lifecycle and result correlation remain unchanged.

### First-provider browser launch/delivery ownership — `KEEP`

The live MV3 owner, opaque launch handle, durable browser claim and project-local one-Send authority remain unchanged.

### Runtime/source provenance — `REFINE`

Keep exact-head/source provenance as a project-owned acceptance boundary, but stop treating a mutable post-gate worktree as the qualified execution source. The physical launcher will derive its controller source and expected extension source from the named reviewed Git commit itself.

### Worker prompt correlation — `REFINE`

Keep the existing `prompt_sha256` identity/provenance field, but require the actual live composer text to equal the intended prompt (with only CRLF/CR -> LF browser text normalization) before authority and immediately before the physical click. Marker presence remains useful parsing evidence but is not prompt equivalence.

No external runtime component replaces a project-owned role and no new durable state owner is introduced.

## 4. Research Scope Expansion Gate

The source correction materially relies on three bounded mechanisms.

### Named-tree archive

Domain: Git object/tree provenance and reproducible source materialization.

Required guarantee: produce runtime source from the immutable reviewed commit/tree rather than the developer worktree after the gate.

Primary evidence: official `git archive` documentation states that `git archive <tree-ish> [<path>...]` creates an archive from the named tree/commit, and commit/tag archives retain the commit identity in archive metadata. Source: `https://git-scm.com/docs/git-archive`.

### Isolated Python import from ZIP

Domain: Python import-path isolation and archive import.

Required guarantee: the controller must not import project modules from the mutable current directory, user site, `PYTHONPATH`, or developer worktree.

Primary evidence:

- Python command-line documentation states `-I` isolated mode excludes the current directory and user site-packages and ignores `PYTHON*` environment variables: `https://docs.python.org/3/using/cmdline.html`.
- Python `zipimport` documentation states ZIP paths on `sys.path` can directly provide `.py` modules/packages and do not need extracted `.pyc` mutation: `https://docs.python.org/3/library/zipimport.html`.

### Read-share-only source handles during the effectful run

Domain: Windows/.NET file-sharing semantics.

Required guarantee: once the exact runtime archive/extension snapshot has been selected for the physical run, concurrent writes/deletes cannot replace those selected files during the authority window while other processes may still read them.

Primary evidence: .NET `FileShare.Read` permits other readers but not writers for an open file handle. Source: `https://learn.microsoft.com/en-us/dotnet/api/system.io.fileshare`.

This is a qualification-local execution fence, not a new durable lock service.

## 5. Materially distinct approaches

### A — repeat the worktree provenance gate immediately before launch/Send

Strength: smallest code change and reuses the existing gate.

Failure: remains point-in-time evidence. A write can still occur after the last check but before Python import/extension hashing or an effect. Repeating the same observation narrows but does not remove the TOCTOU class found by review.

Decision: **REJECT as the complete fix**. Retain pre/post gates as additional evidence only.

### B — detached Git worktree at the reviewed commit

Official Git worktree documentation supports detached throwaway worktrees for testing without disturbing current development (`git worktree add --detach`). Source: `https://git-scm.com/docs/git-worktree`.

Strength: isolates execution from the actively edited main worktree and preserves normal checkout behavior.

Failure/cost: it is still a writable filesystem tree and adds linked-worktree administration/cleanup. Additional locking is still required for the exact authority window, and Python import-path isolation remains necessary.

Decision: **NOT SELECTED** for this narrow qualification path.

### C — exact reviewed Git archive + isolated Python ZIP import + exact extension snapshot — SELECTED

Mechanism:

```text
clean exact-HEAD gate proves launcher invocation context
 -> git archive exact EXPECTED_HEAD runtime/
 -> record archive SHA-256
 -> hold archive read-share-only for the effectful run
 -> Python starts in -I/-B mode and imports CAP runtime only from that archive
 -> materialize extension snapshot from the same archive
 -> derive expected extension hashes from archive entries, not worktree files
 -> hold selected extension files read-share-only during the run
 -> browser live runtime attestation must match those exact archived bytes
 -> Send/capture only after the existing runtime/head/prompt gates
```

Strengths:

- concurrent developer-worktree writes after the initial gate cannot alter controller imports or redefine expected extension bytes;
- one reviewed commit is the source for both controller and extension expectations;
- no new persistent service/state owner;
- the existing browser runtime-attestation protocol remains the executing-extension proof;
- the existing pre/post source gates remain useful whole-worktree evidence without being the sole effect fence.

Operational cost: physical qualification must load/use the exact extension snapshot path printed by the launcher (or byte-identical executing extension), rather than assuming the mutable repository path is the source of truth.

Decision: **SELECTED / NARROW**.

## 6. Prompt-equivalence rule

For this adapter, the exact pre-Send worker-visible prompt is the editor value/text observed from the real composer.

The only canonicalization allowed for comparison is newline representation:

```text
CRLF -> LF
CR   -> LF
```

No whitespace collapsing, marker-only acceptance, prefix/suffix allowance or task-body omission is permitted.

Required ordering:

```text
current editor text == intended prompt
 -> intended prompt digest == launch prompt_sha256
 -> fresh/non-personalized/no-plugin qualification
 -> browser/project authority request
 ... async authority boundary ...
 -> current editor text == intended prompt again
 -> immediate button.click()
```

If the composer changes after authority but before click, fail closed and do not Send. Consuming a claim without an external Send is preferable to sending semantically different instructions under the original prompt identity.

## 7. Failure matrix

| Boundary | Possible failure | Required result |
|---|---|---|
| before initial source gate | dirty/wrong HEAD | fail before controller/browser launch |
| after source gate, developer worktree changes | repo bytes differ | qualified controller/expected extension remain from exact archive; post gate may also fail evidence |
| archive generation | Git/archive failure | fail before browser preflight |
| archive selected, concurrent archive write attempted | selected source mutation | denied while read-share-only handle is live |
| extension snapshot differs from archive | stale/edited snapshot | fail before controller/preflight authority |
| installed/executing extension differs | runtime attestation mismatch | fail before Send/capture |
| composer correct, then edited before authority request | prompt mutation | no authority request |
| composer changes during async authority path | prompt mutation | authority may become locally claimed, but pre-click exact check blocks physical Send |
| composer correct at authority, edited before click | prompt mutation | no click / zero physical Send |
| result/capture after runtime change | changed extension bytes/generation | existing capture re-attestation fails closed |

Maximum additional physical Send for every provenance failure cell above: **zero**.

## 8. Acceptance shields

Focused tests must prove:

- a composer with correct delegation/delivery/task markers but altered task/instruction body is rejected;
- extra prefix/suffix instructions are rejected;
- exact intended composer is accepted;
- exact prompt is checked again in the synchronous pre-click path;
- expected extension asset hashes are sourced from the exact archive, never from `$RepoRoot` after the initial source gate;
- controller process uses Python isolated mode and imports the runtime from the exact archive rather than `-m` from `$RepoRoot`;
- the controller working directory is outside the repository source root;
- runtime archive and selected extension snapshot files are held read-share-only through the effectful run;
- existing runtime-attestation, one-Send, ACK-loss, browser-loss and result-capture tests remain green;
- physical qualification uses the exact snapshot path and still proves normal A plus browser-loss B1/B2 on the eventual reviewed HEAD.

## 9. Decision

**NARROW**.

Fix only these two provenance defects. Do not use this review cycle to introduce a universal execution runtime, persistent Agent Session, scheduler, return-delivery mechanism or Prime integration.

Any code change moves HEAD and makes the review on `8fae2b16989f828b1ad4e4ddbf439b9a54c959ef` stale. After focused tests and exact-head hosted CI, freeze the new head and run a genuinely fresh ordinary-ChatGPT semantic review again before physical qualification.