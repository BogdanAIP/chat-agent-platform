## Goal

## Live source context

- [ ] Resolved live `main`, relevant open PRs and exact heads
- [ ] Read `AGENTS.md`, `project-context/START_HERE.md`, `project-context/CURRENT_STATE.md`, `project-context/ROADMAP.md`
- [ ] Read additional evidence/ADR/security/stage docs only because this change actually needs them

## Stage research / design basis

For a new release-critical stage/substage, major subsystem, new capability family or materially new recovery/security/authority architecture:

- [ ] Ran `.agents/skills/stage-research/SKILL.md` before production implementation
- [ ] Stage Research Brief records `PROCEED`, `NARROW`, or `DEFER`
- [ ] Audited the current implementation and relevant failure/evidence history
- [ ] Researched current strong approaches for this exact stage
- [ ] Actively researched known limitations, issue reports, postmortems and operational failure modes
- [ ] Recorded root causes/mitigations and how this implementation avoids repeating known external failures
- [ ] Compared research/current code with existing future ADRs
- [ ] Treated future ADR implementation details as revisable hypotheses rather than immutable specifications
- [ ] Chosen the smallest implementation slice consistent with the long-horizon product model and required guarantees

Research output should change implementation decisions, constraints or confidence; do not create a standalone research document merely to satisfy this checklist. Record the brief in the first implementation PR body or an existing authoritative architecture/stage owner when durable persistence is actually needed.

Narrow bug fixes, dependency bumps, isolated regressions and documentation-only corrections do not require the full skill unless they materially alter architecture, authority or a release-critical guarantee.

## Complexity check

- [ ] This adds a new capability/guarantee, or there is a clear reason existing mechanisms cannot express it
- [ ] Reused/consolidated existing runtime, assurance, CI and documentation mechanisms where practical
- [ ] Did not create a new Stage/CAP-specific framework/workflow/document owner without a concrete need
- [ ] Tests prefer observable behavior/instrumentation over source-text/order assertions where practical
- [ ] Historical evidence/SHAs stay in `EVIDENCE_INDEX.md` instead of being duplicated across live docs
- [ ] New infrastructure that replaces nothing has an explicit necessity justification

## Planner / authority impact

- [ ] No planner/Control Plane/public-authority change
- [ ] Deterministic Control Plane change: bounded authority and verification contracts updated/tested
- [ ] Public authority change: schema/security/physical acceptance requirements are explicit

Ordinary ChatGPT remains the only current general planner unless a separately accepted decision changes that. Discovery, model output, environmental content, evidence and events do not self-authorize consequence-bearing actions.

## Verification

- [ ] Relevant focused/unit/adversarial tests pass
- [ ] Required hosted checks pass on the exact functional head
- [ ] Required real Windows / ordinary-Chat physical acceptance is either evidenced or explicitly still required
- [ ] Synthetic/CI evidence is not mislabeled as physical evidence
- [ ] No invented counters or stale evidence are used as measurements

### Independent review gate

For runtime/security/recovery/authority changes:

- [ ] Codex Review / equivalent independent review completed when available and required for this change class
- [ ] Findings were fixed or explicitly dispositioned
- [ ] Material fixes were re-reviewed when appropriate
- [ ] Final required CI/physical evidence is from the exact post-review head
- [ ] Auto-merge was not allowed to merge an intermediate hardening head

If independent review is unavailable, record that explicitly; do not represent it as completed.

## Documentation impact

Update only the owner documents whose facts actually changed:

- `CURRENT_STATE.md` — accepted boundary / immediate work
- `ROADMAP.md` — release order
- `PROJECT_RISKS.md` — ranked risks
- `EVIDENCE_INDEX.md` — exact accepted evidence/SHAs/locators
- `TECH_DEBT.md` — existing compromises/close conditions
- architecture/ADR docs — durable boundaries or stage design

- [ ] No live-document update needed
- [ ] Relevant owner documents updated
- [ ] README and other public prose do not contradict current product truth

## Acceptance criteria

