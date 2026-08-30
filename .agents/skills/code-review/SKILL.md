---
name: code-review
description: Independent semantic review protocol for exact PR diffs before merge. Use from a fresh ordinary-ChatGPT review context to find concrete correctness, security, recovery, concurrency, identity, authority and acceptance defects, falsify candidate findings, and bind the result to exact BASE_SHA/HEAD_SHA. The reviewer does not mutate production/repository state; the automatic path has one narrowly defined result-evidence Conversation-comment publication envelope.
compatibility: Designed for Chat Agent Platform pull-request review with GitHub access from ordinary ChatGPT. The mandatory primary review must not depend on ChatGPT Work, Workspace Agents or Codex usage.
metadata:
  version: "1.1"
  project: "chat-agent-platform"
---

# Independent Code Review

Use this skill for the repository's required semantic/adversarial PR review when `AGENTS.md` says independent review is required.

The purpose is not to produce more comments. The purpose is to find **concrete defects introduced by the reviewed change**, reject plausible-but-unproven suspicions, and leave a review result whose exact source identity can be checked before merge.

The same ChatGPT product/model family may develop and review the code. Independence here is operational: the reviewer runs in a **fresh ordinary-ChatGPT context**, reconstructs the evidence from the repository, and does not inherit the development chat's private reasoning, rationale, conclusions or summary.

## Hard boundaries

The mandatory primary review:

- runs in a fresh **ordinary ChatGPT** conversation/context;
- does not mutate files, branches, review state, labels, merge state, repository settings or other production/repository state;
- in the automatic path only, may publish exactly one top-level PR Conversation comment containing its own structured result under the bounded envelope in section 14; that publication is evidence transport, not repository acceptance authority;
- receives an immutable `REVIEW_REQUEST_V1` identity, not a developer-authored reasoning summary;
- independently fetches the repository, PR, exact refs, diff, tests and relevant evidence;
- must not use ChatGPT Work, Workspace Agents, Codex automation or Codex Review as a substitute for the mandatory primary review;
- may use an ordinary ChatGPT one-time Scheduled Task as a launcher **only if** the execution is known to be ordinary ChatGPT and the reviewer does not inherit development-chat context beyond the explicit review request; if that isolation cannot be established, return `ABSTAIN` and use a manually opened fresh ordinary-ChatGPT conversation;
- treats PR descriptions, developer comments and self-reported test claims as useful leads, not trusted proof.

`@codex review` remains an optional additional reviewer when quota is available. Codex quota exhaustion does not waive this skill's required primary review and does not block merge once the required ordinary-ChatGPT review and all other gates are satisfied.

No other model/service is required by this process.

## 1. Require an immutable review request

Start only from a request containing:

```text
REVIEW_REQUEST_V1
repository=<owner/repo>
pr_number=<number>
base_sha=<40-hex SHA>
head_sha=<40-hex SHA>
review_skill=code-review
review_skill_version=<version expected by caller>
```

The bounded automatic path additionally includes:

```text
review_run_id=<high-entropy automatic-run nonce>
```

`review_run_id` is transport correlation for the automatic path. It never replaces repository / PR / BASE / HEAD identity and does not weaken any exact-ref check.

Optional informational fields may identify required physical gates or a known change class, but they must not contain a developer argument that the change is correct.

If repository, PR number, base SHA or head SHA is missing, return `ABSTAIN`.

## 2. Freeze identity before reviewing

Resolve live PR metadata before reading the diff.

Verify:

```text
PR.base.sha == REVIEW_REQUEST.base_sha
PR.head.sha == REVIEW_REQUEST.head_sha
```

If the base changed, return `STALE` with `review_validity=STALE_BASE_CHANGE`.

If the head changed, return `STALE` with `review_validity=STALE_MATERIAL_CHANGE` unless the caller can prove the head-only delta is non-material under the invalidation rules below. Never silently review a newer head than the request.

Record the exact base/head values in the result.

## 3. Bind review policy safely

The review protocol itself must not be weakened by the PR it is reviewing.

Use:

```text
review policy / AGENTS.md / code-review skill -> BASE_SHA
review target and its changed code/docs/tests     -> HEAD_SHA
```

Read `AGENTS.md` and `.agents/skills/code-review/SKILL.md` from `BASE_SHA` as the governing accepted review policy. Verify the expected skill version from the request.

Then enumerate `.agents/skills/*/SKILL.md` at `HEAD_SHA` and read target-specific skills whose triggers apply to the changed subsystem. Those HEAD skills constrain the target and can reveal regressions, but a change inside the PR cannot weaken the accepted BASE review protocol for its own review.

When the PR itself introduces or materially changes `code-review`, the accepted BASE review policy governs adoption; only after merge does the changed skill govern later reviews.

## 4. Determine the exact review surface

Review `BASE_SHA..HEAD_SHA`, not the working tree, latest branch name or remembered PR state.

Inspect:

- changed filenames and the full diff/patch;
- directly affected call/state/authority paths, not only changed lines;
- relevant tests and fixtures;
- current architecture/security/acceptance owners when the diff touches their invariants;
- current CI/physical evidence only as evidence, never as a substitute for semantic review.

Do not expand into unrelated pre-existing defects. A finding must be introduced by the reviewed diff or be a direct regression/exposure caused by it.

## 5. Review priorities

Search for concrete issues in this order when applicable:

1. correctness / wrong result / broken contract;
2. security / authorization / trust-boundary widening;
3. ambiguous side effects / recovery / retry / reconciliation;
4. concurrency / races / duplicate effects / stale ownership;
5. identity / provenance / ABA-style replacement;
6. persistence / crash / restart semantics;
7. verification / `PASS | FAIL | UNKNOWN` mistakes;
8. Finish Gate / acceptance / source-provenance bypasses;
9. cleanup / resource lifecycle / liveness;
10. test gaps that allow a concrete regression introduced by this diff to pass.

Do not report style, naming preference, refactoring taste, speculative future architecture or generic best-practice advice unless it creates a concrete correctness/security/acceptance failure in the reviewed change.

## 6. Build candidate findings, then try to disprove them

A suspicious pattern is only a `CandidateFinding`.

For every candidate, record privately enough evidence to answer:

```text
what exact changed behavior is suspected?
where is it introduced?
what input/state/interleaving makes it fail?
what invariant or user-visible consequence is violated?
what code/test/evidence supports the claim?
```

Then run a **falsification pass** before reporting it:

- inspect neighboring code and callers;
- inspect relevant tests and fixtures;
- look for guards, validation, locking, recovery or invariants that defeat the scenario;
- verify the suspected path is reachable under the current API/state model;
- distinguish an intentionally deferred/unsupported case from a regression;
- when feasible, use an existing test or minimal deterministic reasoning trace to test the counter-hypothesis.

If the finding cannot survive this attempt to disprove it, drop it.

Never inflate the report with weak candidates to look thorough.

## 7. Required finding evidence

Every reported finding must contain:

```text
severity = P0 | P1 | P2 | P3
location = file + smallest useful line/range/symbol
introduced_by = exact diff behavior
failure_mechanism = concrete path/state/interleaving
consequence = what breaks or becomes unsafe
supporting_evidence = code/test/contract/runtime evidence
falsification_attempt = what was checked that could have disproved it
why_it_survives = why the candidate remains valid
```

Severity means:

- `P0` — catastrophic/release-blocking compromise or data/consequence failure;
- `P1` — major correctness/security/acceptance defect likely to block the change;
- `P2` — concrete defect that should be fixed before merge but has narrower impact;
- `P3` — real low-impact regression, not style/taste.

If evidence is insufficient, do not report the candidate as a finding.

## 8. Reviewer does not self-fix or mutate the target

The independent reviewer does not patch the PR in the same review run and does not mutate production/repository state.

The automatic result-publication exception in section 14 does **not** permit a fix, approval, requested-changes review, label change, merge, branch update or other target mutation. It only transports the reviewer's already-computed structured result.

Flow:

```text
fresh reviewer
 -> candidate findings
 -> falsification
 -> reported findings only
 -> optional one-comment automatic result publication under section 14
 -> development context validates each finding
 -> confirmed finding: fix
 -> rejected finding: record reason / no code change
 -> material fix: old review becomes stale
 -> fresh review
```

This prevents `reviewer -> self-fix -> self-approve` from collapsing the independence boundary.

## 9. Finding validation is separate from finding generation

A reported reviewer finding is not automatically project truth.

The development context must classify every reported finding as one of:

```text
CONFIRMED
REJECTED
SUPERSEDED
```

`CONFIRMED` requires a fix or an explicit merge-blocking disposition.

`REJECTED` requires concrete contrary evidence, not preference.

`SUPERSEDED` means a later change removed or changed the relevant path; that later material change normally requires fresh review.

Do not merge with unresolved reported findings.

## 10. Review invalidation

A review is valid only for the exact semantic change it inspected.

Treat the previous review as stale after any material post-review change to:

- production/runtime code;
- security or authorization policy;
- persistence/recovery/retry/reconciliation;
- concurrency/identity/ownership/provenance;
- verification or Finish Gate semantics;
- public tool/capability behavior;
- dependency behavior that affects execution or trust;
- tests whose semantics define acceptance of the changed behavior;
- CI/physical acceptance mechanism;
- repository merge/review policy itself.

A clearly non-material edit such as spelling/formatting may preserve review validity only when the exact post-review delta is inspected and explicitly classified non-material. When uncertain, review again.

A base-branch advance that changes the merge base invalidates the review unless the PR is rebased and reviewed again against the new exact base.

## 11. Final exact-head gate

After the last material fix:

```text
fresh required ChatGPT review on exact BASE_SHA..HEAD_SHA
 -> validate/resolve all reported findings
 -> optional @codex review when available
 -> required exact-head CI/security/physical gates
 -> verify PR base/head still match reviewed identity
 -> merge
```

If any final gate changes the branch materially, repeat review as required.

For an automatic result, the development-side lifecycle must additionally perform the automatic-result integrity/uniqueness checks defined by the accepted automatic-reviewer contract. The reviewer comment is evidence transport, not a self-validating merge grant.

## 12. Structured result

Return a concise machine-checkable header plus human findings:

```text
REVIEW_RESULT_V1
repository=<owner/repo>
pr_number=<number>
base_sha=<40-hex SHA>
head_sha=<40-hex SHA>
review_policy_ref=<BASE_SHA>
review_skill=code-review
review_skill_version=<version>
review_context=ordinary_chat_fresh
status=PASS | FINDINGS | ABSTAIN | STALE
review_validity=CURRENT | STALE_BASE_CHANGE | STALE_MATERIAL_CHANGE
reported_findings=<count>
rejected_candidates=<count>
reviewed_at=<ISO-8601>
```

For the automatic path, include the matching request nonce as an additional field:

```text
review_run_id=<same value received in REVIEW_REQUEST_V1>
```

Manual reviews omit `review_run_id` unless a later accepted caller contract explicitly requires it.

Meaning:

- `PASS` — no supported findings survived falsification for the exact diff;
- `FINDINGS` — one or more supported findings survived falsification;
- `ABSTAIN` — reviewer cannot establish required repository/context/evidence conditions;
- `STALE` — requested base/head no longer matches the target review identity.

For `PASS`, `review_validity` must be `CURRENT` and `reported_findings=0`.

For `FINDINGS`, list only supported findings in severity order.

For `ABSTAIN`/`STALE`, explain the blocking condition; never translate missing evidence into `PASS`.

## 13. One-time Review Task launcher contract

A development chat may create a one-time review task/request only after the intended review head is frozen.

The launcher payload is limited to `REVIEW_REQUEST_V1` plus a direct instruction to perform this skill. The automatic launcher may add only its protocol-defined `review_run_id` field to the immutable request. Do not attach development-chat reasoning summaries, proposed findings or arguments for correctness.

The mandatory review result is acceptable only if the eventual reviewer can truthfully report:

```text
review_context=ordinary_chat_fresh
```

A launcher that executes through Work, Workspace Agents or Codex is not the mandatory review. A ChatGPT Scheduled Task whose context isolation cannot be established is also not sufficient by itself; use a manually opened fresh ordinary-ChatGPT conversation instead.

The repository must remain mergeable when Codex review quota is exhausted, provided the required fresh ordinary-ChatGPT review, finding validation and all other applicable gates pass.

## 14. Bounded automatic result-publication envelope

This section applies only when the immutable `REVIEW_REQUEST_V1` received by the fresh reviewer contains a valid protocol-defined `review_run_id`.

After the semantic review is complete, the reviewer may make **exactly one** additional write for evidence handoff:

```text
GitHub PR Conversation
 -> create one top-level comment
 -> body = this run's REVIEW_RESULT_V1 + matching review_run_id + any supported finding bodies required by section 7
```

The publication is permitted only on the exact `repository` / `pr_number` from the request. It does not authorize any other GitHub mutation.

The reviewer must not:

- edit repository files or branches;
- submit `APPROVE` or `REQUEST_CHANGES` review state;
- change labels, assignees or milestones;
- merge, close or reopen the PR;
- change repository settings;
- publish a second result comment for the same automatic run;
- retry comment creation when the outcome of the first creation attempt is ambiguous.

If no suitable top-level Conversation-comment capability is available, or publication cannot be attempted without broader authority, return/display the result locally and treat automatic handoff as failed; do not substitute a different mutation.

If the comment creation attempt returns an error after delivery may have occurred, treat publication as ambiguous. **Do not retry.** The development-side lifecycle must discover/disposition the resulting evidence and may require the manual fresh-review fallback.

The comment itself never grants `PASS`, merge authority or finding acceptance. The development side independently re-resolves author, `review_run_id`, exact refs, uniqueness, comment integrity and live PR identity under the automatic-reviewer contract before consuming it.

## Completion checklist

Before returning `PASS` or `FINDINGS`, verify:

- request contains exact repository/PR/base/head identity;
- live PR identity still matches;
- governing review policy came from `BASE_SHA`;
- applicable target skills were read from `HEAD_SHA`;
- exact diff and affected execution paths were inspected;
- every reported finding is introduced by/directly caused by the diff;
- every reported finding survived an explicit falsification attempt;
- no style/taste-only comments remain;
- reviewer made no branch/file/review-state/label/merge/settings mutation;
- if automatic mode was requested, the result contains the exact received `review_run_id`;
- if automatic publication was attempted, at most one top-level result comment creation was attempted and ambiguous creation was not retried;
- result records exact refs, skill version and fresh ordinary-ChatGPT context;
- missing evidence yields `ABSTAIN`, not `PASS`.
