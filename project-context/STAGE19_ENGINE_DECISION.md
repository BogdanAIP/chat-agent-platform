# Stage 19 Reference Mastering Engine Decision

Status: implementation in progress.

The proven gap after Stage 15 is reference-based matching: technical delivery mastering can enforce loudness, true peak, duration and format, but it does not intentionally match a separate reference track's tonal/dynamic character.

Stage 19 therefore uses a replaceable edge-engine boundary:

- core orchestration, Project Binding, policy, Artifact Store, jobs, idempotency and final QC remain Rust;
- the selected candidate engine is Matchering 2.0.6, invoked through a fixed Python adapter process;
- the dedicated engine environment is pinned to Python 3.10 because Matchering 2.0.6 upstream explicitly classifies Python 3.8, 3.9 and 3.10; the user's/core Python runtime does not become a Matchering dependency;
- Matchering is optional and separately installed; it is not added to the core `pyproject.toml`, Cargo graph or default runtime dependency set;
- no arbitrary Python, shell or Matchering options are exposed through the capability;
- target/reference hashes are part of the idempotency key;
- the external engine's output is not trusted directly: it must be PCM 24-bit WAV, pass duration/media validation, then pass the existing Stage 13/15 technical delivery quality gate before registration as a successful master;
- the real E2E uses deliberately different low/high-frequency balances and requires both loudness distance and objective low/high tonal-balance distance to the reference to improve;
- a dedicated Windows E2E installs the pinned Matchering version and tests the actual engine; default core CI still compiles the Rust integration and syntax-checks the adapter without silently simulating Matchering;
- the adapter boundary is intentionally replaceable if maintenance, licensing, compatibility or benchmark quality becomes unacceptable.

Matchering 2.0.6 upstream describes its algorithm as matching RMS, frequency response, peak amplitude and stereo width to the supplied reference. The platform does not blindly adopt that claim as its own quality result: Stage 19 has a separate reproducible benchmark and post-processing QC.

Matchering is GPL-3.0 upstream. This implementation keeps it as a separately installed optional edge process rather than vendoring or bundling its source/package into the core project. If a future distribution model bundles Matchering with the product, licensing/distribution obligations must be reviewed before that change is shipped.

This document does not mark Stage 19 done. Completion requires both normal core CI and the real pinned Matchering E2E to pass, followed by benchmark/results documentation.
