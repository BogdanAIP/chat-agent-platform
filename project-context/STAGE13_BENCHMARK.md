# Stage 13 Audio Analysis Benchmark

Status: **passed in Windows CI**

Stage 13 validates a mastering **decision layer**, not subjective artistic mastering.
The capability is `audio.mastering_analyze` and runs through Project Binding →
locked tool selection → PEP → Artifact Store → FFmpeg EBU R128 inspection → typed
decision → Artifact Store metadata.

## Decision profiles

- `music-balanced`: -14 LUFS target, -1 dBTP ceiling, preferred LRA 2.5–14 LU.
- `music-loud`: -10 LUFS target, -1 dBTP ceiling, preferred LRA 1.5–10 LU.
- `speech`: -16 LUFS target, -1 dBTP ceiling, preferred LRA 1–12 LU.

The profile never silently overrides measured source data. The result reports the
measured source metrics, selected target, loudness delta, proposed action,
`auto_mastering_allowed`, `requires_review`, quality flags and human-readable
reasons.

## Safety gates

Automatic processing is blocked and review is required for conditions including:

- unmeasurable integrated loudness or true peak;
- sample rate below 44.1 kHz;
- material outside the validated mono/stereo path;
- loudness range outside the selected profile envelope;
- likely clipping / effectively zero true-peak headroom.

Loudness outside tolerance or a true-peak ceiling violation can recommend a
technical loudness normalization only when the material otherwise remains inside
the safe automatic envelope.

## Real benchmark corpus

`crates/agent-platform/tests/stage13_audio_analysis.rs` generates actual PCM 24-bit
WAV files with FFmpeg and analyzes them through the public policy-gated operation.
The corpus contains four technical cases rather than one test tone:

1. quiet 48 kHz stereo program;
2. nominal 48 kHz stereo program;
3. hot 48 kHz stereo program;
4. 32 kHz mono program that must trigger the delivery-floor review gate.

A second integration case analyzes the same WAV under `music-balanced` and
`music-loud` and verifies that measured source loudness stays identical while the
target changes from -14 to -10 LUFS.

Unit tests separately cover preserve, safe-normalize, forced-review and unsupported
profile rejection.

## Acceptance result

Windows CI run #95 completed successfully with strict rustfmt, Clippy, Rust tests,
contract fixtures, Python oracle/parity, the real FFmpeg benchmark corpus and the
release build. No new runtime dependency, daemon or external service was added.

This closes Stage 13's technical-metrics/decision-quality gate. It does **not** claim
that LUFS/true-peak analysis alone is equivalent to professional artistic mastering;
that distinction is preserved for the production mastering workflow and additional
professional capabilities.
