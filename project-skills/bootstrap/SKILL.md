---
name: bootstrap
description: Bind the active Chat Agent Platform project, load only its minimal project context and relevant capability slice, verify runtime availability, and route safe local media inspection. Use for requests to start or resume work in this repository, analyze or inspect WAV/audio/media files, determine the active project, or choose the local media.inspect execution path.
---

# Bootstrap

Bind the project before selecting tools or touching artifacts. Treat repository files as
versioned state and the runtime profile as changeable local evidence.

## Workflow

1. From the repository root, run:

   ```powershell
   cargo run --quiet -- --repo-root . bootstrap --project-id demo --capability media.inspect
   ```

2. Stop on `PROJECT_BINDING_ERROR`; never guess a neighboring project.
3. Use only the returned `CURRENT_STATE.md`, `ARCHITECTURE.md`, and
   `CONSTRAINTS.md` context unless the task requires another document.
4. Check the returned capability requirement and runtime slice separately. If
   runtime status is `unknown`, run `cargo run --quiet -- --repo-root . probe --project-id demo`.
   Never edit requirements merely because the runtime is unavailable.
5. For a media inspection request, run:

   ```powershell
   cargo run --quiet -- --repo-root . inspect --project-id demo --file <absolute-media-path>
   ```

6. Report duration, sample rate, channels, codec, integrated LUFS, artifact ID,
   validation status, and any structured error. Do not pass binary media through chat.

## Guardrails

- Let the policy enforcement point derive effective risk; ignore model risk hints for authority.
- Do not expose arbitrary shell execution as a capability.
- Do not upload or stage artifacts externally.
- Do not edit Project Memory for a routine inspection.
- Do not claim hosted Chat/MCP availability from a local probe.
- Treat guarded operations as unsupported until prepare/confirm is implemented.
