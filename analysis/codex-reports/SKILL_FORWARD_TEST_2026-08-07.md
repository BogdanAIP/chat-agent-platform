# Skill Forward Test — 2026-08-07

## Scope

Independent agents used the generated skills without receiving expected answers.
All tests were read-only with respect to versioned files.

## media-inspection

Result: passed. The agent selected the Rust typed path, returned 1.25 s, 48 kHz,
stereo, `pcm_s16le`, −21.8 LUFS, artifact ID, SHA-256 and validated provenance.

Observed friction: harmless PowerShell profile warnings appeared in redirected output;
they did not affect the capability.

## mastering

Result: passed for its intentionally limited assessment role. The agent refused to
claim a professional master from a 1.25-second tone, separated measurable facts from
artistic conclusions, and did not render or overwrite media.

Observed limitation: a strict read-only prompt prevented Artifact Store import. This
is expected; normal assessment may create a non-destructive local artifact copy.

## github-development

Result: passed with one instruction correction. The agent verified local build/test
evidence, identified missing Git author identity and missing remote, and did not
commit or push. It incorrectly treated the blank source handoff template and absent
pytest as blockers. The skill now says to copy rather than overwrite the template
and to use the unittest-based `scripts/verify.ps1` path.

## Conclusion

The skills generalize to independent sessions. Corrections were applied where the
forward test exposed ambiguous instructions.

