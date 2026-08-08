# Stage 15 Production Mastering Workflow

Status: **passed in Windows CI**

Stage 15 closes the first persistent production audio workflow. It is deliberately
named a **technical delivery master**: the workflow guarantees measurable delivery
properties and safe automation boundaries, but does not claim to replace artistic
mastering decisions such as tonal shaping, multiband dynamics, reference taste or
human review.

## Public capability

`audio.mastering_produce` / CLI `produce-master` runs through:

`Project Binding → locked capability selection → PEP → source SHA-256 → persistent
job → Artifact Store → Stage 13 decision → Stage 11 processing → final inspection →
Stage 13 re-decision → final quality gate → Artifact Store → persisted result`.

Profiles are inherited from Stage 13: `music-balanced`, `music-loud`, `speech`.

## Idempotency and recovery

The deterministic job key is derived from workflow version, exact source SHA-256,
profile and data class. Repeating the same successful request returns the same job,
master artifact ID and SHA-256 rather than generating another master.

Persistent checkpoints record source registration, analysis and the final validated
result. A process that reaches the final quality checkpoint can complete the job
without re-creating the master. Failures are stored as structured job errors; the
Stage 14 transition rules decide whether resume is allowed.

The workflow has no external side effect and no separate daemon/service. A narrow
crash window between local Artifact Store publication and the following job
checkpoint can leave an additional local artifact, but Artifact Store integrity is
preserved; no external publication or destructive action is repeated. Exactly-once
coordination across two independent stores is not claimed.

## Safe automatic processing

Stage 13 is authoritative for whether automatic processing is allowed. A source that
requires review cannot become a successful automatic master. The current automatic
actions are intentionally constrained:

- `preserve`: lossless WAV conversion when source metrics already satisfy the profile;
- `normalize_loudness`: Stage 11 two-pass EBU R128 loudnorm to the selected target.

Arbitrary FFmpeg arguments, plug-in chains, EQ/compression presets and shell commands
are not exposed.

## Final quality gate

Before the result is accepted as a master, the generated WAV is inspected again and
must satisfy all of the following:

- sample rate at least 44.1 kHz;
- validated mono/stereo path;
- duration drift no more than 100 ms;
- Stage 13 safe-auto envelope still passes;
- Stage 13 now recommends `preserve` (the output is within target tolerance);
- measured true peak stays within the selected target ceiling tolerance;
- final WAV is imported into Artifact Store and returned with SHA-256 provenance.

## Real Windows benchmark

Windows CI run #119 completed successfully after strict rustfmt/Clippy. The Stage 15
integration suite creates real PCM 24-bit WAV programs with FFmpeg inside isolated
temporary Project Bindings and covers:

1. **quiet dynamic 48 kHz stereo** → `normalize_loudness` → final decision
   `preserve`, target loudness tolerance and true-peak ceiling pass;
2. exact repeat of that source/profile/data class → same job ID, same master artifact
   ID, same SHA-256, unchanged Artifact Store item count;
3. **already compliant 48 kHz stereo** → lossless `preserve` path and final
   `preserve` decision;
4. **32 kHz mono source** → automatic mastering is rejected for review, persisted job
   is non-retryable `MASTERING_REVIEW_REQUIRED`, and no successful master artifact is
   registered.

The complete pre-existing Rust tests, contracts, Python oracle/parity and release
build remain green.

## Exit-gate conclusion

Stage 15's technical production-mastering gate is satisfied: the workflow is
policy-gated, persistent, source-hash idempotent, uses real audio processing, blocks
unsafe automation, validates the generated master again and preserves Artifact Store
provenance. More subjective/reference-based mastering belongs to a separate
professional capability with its own benchmark and must not weaken this gate.
