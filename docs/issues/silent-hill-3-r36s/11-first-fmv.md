# Play first original FMV and return to gameplay

Published as [#11](https://github.com/ktodorow/sh3-nx-r36s/issues/11) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Trigger one original movie through real game flow, present synchronized video/audio, finish or skip, then continue gameplay.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC05, AC11, AC03. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Connect actual game-used movie boundary to validated decoder and SDL/GLES outputs, retaining original media cadence and correct aspect ratio.
- [ ] Exercise natural completion and supported skip independently, with synchronized audio and subtitles where applicable.
- [ ] Restore game rendering/audio/input state after playback; exit and failed playback release owned resources and return predictably.
- [ ] Record reproducible game checkpoint and target evidence. One movie passes only this slice, not all-FMV coverage.

## Blocked by

- [05: Reach menus and first playable scene through native GLES3](05-first-gameplay.md)
- [09: Preserve game audio and simulation speed at 30 FPS](09-audio-timing.md)
- [10: Identify original FMVs and measure native decode feasibility](10-original-media.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
