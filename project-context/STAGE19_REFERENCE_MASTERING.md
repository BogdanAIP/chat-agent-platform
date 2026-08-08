# Stage 19 Reference Mastering — acceptance evidence

Status: **done**.

## Capability

- Capability: `audio.reference_master`
- Executor: `edge.python.matchering`
- Engine: Matchering `2.0.6`
- Dedicated edge runtime: Python `3.10`
- Core remains Rust-first; Matchering is not part of the Cargo graph or core `pyproject.toml`.

The Rust workflow keeps Project Binding, capability selection, policy enforcement, persistent jobs, idempotency, Artifact Store and final QC. The Python edge adapter exposes only `probe` and `process`; it accepts fixed absolute TARGET/REFERENCE/output file arguments and technically rejects every Matchering version except `2.0.6`.

## Processing contract

1. TARGET and REFERENCE SHA-256 values are included in the persistent job identity.
2. Both inputs are imported into Artifact Store and technically inspected before the external engine is used.
3. Matchering must produce a non-empty PCM 24-bit WAV with duration integrity.
4. The Matchering result is not accepted directly. It goes through the established two-pass EBU R128 technical delivery normalization/QC.
5. Final sample rate must equal the original TARGET sample rate exactly; mono/stereo, duration, safe-auto profile envelope, LUFS and true-peak checks remain enforced.
6. Only after all checks pass is the final master registered in Artifact Store.
7. Exact repeat of TARGET + REFERENCE + profile + data class returns the existing persistent job/master artifact instead of processing again.

## Real benchmark

The dedicated Windows E2E generates a 24-second PCM 24-bit stereo TARGET and REFERENCE with intentionally different 220 Hz / 4.2 kHz balances and slow program-level macro-dynamics. The benchmark requires:

- real Matchering import/probe and processing;
- integrated-loudness distance to the REFERENCE to improve after Matchering;
- measured high/low tonal-balance distance to the REFERENCE to improve;
- final `music-balanced` decision to be `preserve` with no review flag;
- final 48 kHz TARGET rate to remain 48 kHz;
- final LUFS/true-peak/duration/channel QC to pass;
- repeated request to reuse the same job, artifact ID and SHA-256 with no manifest growth.

A separate 32 kHz TARGET case is rejected before reference processing and persists a non-retryable failed job.

## Defect found by the benchmark

The real E2E exposed an actual delivery defect rather than being weakened to fit the implementation:

- Matchering can emit 44.1 kHz from a 48 kHz TARGET;
- FFmpeg `loudnorm` can otherwise choose a 192 kHz output rate during true-peak processing.

The shared Stage 11 normalizer was hardened so normal `normalize_loudness` preserves its input rate, while a typed `normalize_loudness_at_sample_rate` path lets Stage 19 explicitly restore the original TARGET rate. Stage 11 regression now asserts 48 kHz → 48 kHz normalization.

## Exit gate evidence

Code head: `1cb74fe5771bf9e143a9cdecdbc632e4eeb15ec2`.

- Normal Windows CI: run **#159**, run id `31262535449` — success. Strict fmt/Clippy, all Rust tests, contracts, Python oracle/parity, adapter syntax and release build passed.
- Real Stage 19 Matchering E2E: run **#36**, run id `31262535446` — success. Pinned Matchering installation/probe and both ignored real integration cases passed on a clean Windows runner.

This closes the Stage 19 exit gate for the reference-mastering capability. It does not claim that automated reference matching replaces human artistic judgment for every recording; the platform guarantees the measured benchmark and technical delivery envelope above.
