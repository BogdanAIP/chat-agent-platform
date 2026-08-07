---
name: media-inspection
description: Safely import and inspect local audio or media artifacts through the Chat Agent Platform Rust core and FFmpeg/ffprobe, returning duration, sample rate, channels, codec, EBU R128 loudness, artifact identity, policy decision, and validation status. Use when asked to inspect, analyze, measure, validate, or report technical properties of a WAV, MP3, FLAC, M4A, or other local media file.
---

# Media Inspection

Use the typed `media.inspect` capability. Never replace it with arbitrary shell.

## Workflow

1. Resolve the repository and explicit project binding.
2. Run `agent-platform bootstrap --project-id demo --capability media.inspect`.
3. If runtime status is not `available`, run `agent-platform probe --project-id demo`.
4. Run:

   ```powershell
   agent-platform --repo-root <repo> inspect --project-id demo --file <absolute-path>
   ```

   Use `cargo run --quiet --manifest-path <repo>/Cargo.toml --` before a release
   binary is available.
5. Report duration, sample rate, channels, codec, integrated LUFS/LRA, true peak
   dBTP, artifact ID, SHA-256, validation status, and structured errors.
6. For a registered artifact, use `inspect-artifact --artifact-id <art_...>` instead
   of importing another copy. Treat a hash mismatch as a validation failure.

## Guardrails

- Let policy derive effective risk; do not trust model risk hints.
- Import into the bound Artifact Store before executor access.
- Do not upload, stage, overwrite, normalize, convert, or delete the source.
- Do not send binary payload through Chat or JSON.
- Do not edit Project Memory for routine inspection.
- Treat `integrated_lufs: null` with `below_measurement_floor` as valid silence.
