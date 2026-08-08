# Stage 19 Reference Mastering Engine Decision

Status: implementation in progress.

The proven gap after Stage 15 is reference-based matching: technical delivery mastering can enforce loudness, true peak, duration and format, but it does not intentionally match a separate reference track's tonal/dynamic character.

Stage 19 therefore uses a replaceable edge-engine boundary:

- core orchestration, Project Binding, policy, Artifact Store, jobs, idempotency and final QC remain Rust;
- the selected candidate engine is Matchering, invoked through a fixed Python adapter process;
- Matchering is optional and separately installed; it is not added to the core `pyproject.toml`, Cargo graph or default runtime dependency set;
- no arbitrary Python, shell or Matchering options are exposed through the capability;
- target/reference hashes are part of the idempotency key;
- the external engine's output is not trusted directly: it must pass media validation and the existing Stage 13/15 technical delivery quality gate before registration as a successful master;
- a dedicated Windows E2E installs a pinned Matchering version and tests the actual engine; default core CI does not silently simulate it;
- the adapter boundary is intentionally replaceable if maintenance, licensing, compatibility or benchmark quality becomes unacceptable.

Matchering is GPL-3.0 upstream. This implementation keeps it as a separately installed optional edge process rather than vendoring or bundling its source/package into the core project. If a future distribution model bundles Matchering with the product, licensing/distribution obligations must be reviewed before that change is shipped.

This document does not mark Stage 19 done. Completion requires both normal core CI and the real pinned Matchering E2E to pass, followed by benchmark/results documentation.
