# Stage 12 REAPER Acceptance

Status: **passed**

A real Windows machine with an installed REAPER instance executed the versioned
`scripts/verify-reaper-stage12.ps1` acceptance flow against `main` commit
`cc3fb864e83705dd4cb5453298970bd6dc76eed3`.

## Evidence

- acceptance contract: `stage12-acceptance-v1`
- verified UTC: `2026-08-08T06:47:48.2439077Z`
- execution path: `reaper.cli.reascript`
- fixture: generated 997 Hz stereo WAV, 48 kHz, 2 s
- project artifact: `art_1ba425fa5619411fa71ff87416d19c4d`
- project SHA-256: `fd18502d8bcfe185ac008b9637b9e834b4744cad481554fd22a1169ba50808b5`
- render artifact: `art_73cc3d3bdfa14c338422c04721474223`
- render SHA-256: `d6bc02917a7aec05ac1e4c90a22ae2e70e10e97bd5bd862a37ff3098c3be7fd8`
- rendered sample rate: 48000 Hz
- rendered duration: 2.0 s
- measured integrated loudness: -21.1 LUFS
- measured true peak: -21.1 dBTP

The local executable path is intentionally not versioned because it is machine
specific. The acceptance script validated that the generated `.rpp` and rendered
WAV were both present in the Artifact Store and that their returned SHA-256 values
matched the manifest.

## Exit-gate conclusion

Stage 12's real-user E2E gate is satisfied. The adapter has now been exercised
through Project Binding → locked capability selection → PEP → Artifact Store →
REAPER ReaScript/CLI → rendered WAV validation → Artifact Store registration on an
actual REAPER installation, so Stage 13 may begin.
