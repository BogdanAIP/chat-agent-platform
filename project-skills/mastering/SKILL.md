---
name: mastering
description: Assess source audio, collect mastering intent, define measurable technical and quality targets, and prepare a safe artifact-based mastering plan for the Chat Agent Platform. Use for mastering, loudness targets, delivery masters, streaming preparation, mix assessment, reference-track comparison, or mastering workflow requests. Until the REAPER adapter and benchmark corpus pass their roadmap gates, use this skill for assessment and planning only and do not claim that a professional master was rendered.
---

# Mastering

Separate assessment, processing, and quality acceptance. Current project capability
supports assessment only.

## Assessment

1. Bind the project and use `$media-inspection` on the source.
2. Record format, sample rate, channels, duration, integrated loudness, LRA, and
   artifact SHA-256.
3. Collect intended destination, genre/context, desired dynamics, available mix
   headroom, reference tracks, alternate versions, and delivery formats.
4. Identify technical blockers without diagnosing artistic quality from LUFS alone.

## Plan

Define:

- immutable source artifact;
- processing stages as intent, not fixed plugin settings;
- technical delivery constraints;
- loudness/true-peak targets appropriate to destination;
- A/B and reference comparison method;
- technical validation and listening acceptance;
- output naming, provenance, and retention.

## Guardrails

- Do not overwrite the mix or treat loudness normalization as mastering.
- Do not promise a rendered master before the REAPER adapter and benchmark gates.
- Do not infer clipping, distortion, tonal balance, or musical quality from one metric.
- Keep paid API/plugin use behind cost policy and explicit capability selection.
- Preserve source artifacts and create new output artifact IDs for future renders.

