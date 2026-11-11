# Complete all-original-FMV playback and lifecycle coverage

Published as [#12](https://github.com/ktodorow/sh3-nx-r36s/issues/12) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Play every inventoried original FMV with correct media timing and reliable return to game.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC05, AC11, AC12. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Record per-movie/required-variant content, aspect, audio/subtitle timing, cadence/duration, natural finish and supported skip results on R36S.
- [ ] Test end-of-media when frames arrive late or are dropped; completion cannot depend on display of last frame. Subtitles follow media clock.
- [ ] Exercise repeated movie/game transitions and supported pause/resume behavior where present; preserve rendering/audio/input state and release decoder resources.
- [ ] Cover failures without silent successful skip or lost story content. Keep movie inventory reconciled with later campaign/ending checklist; this does not yet prove every campaign trigger.

## Blocked by

- [11: Play first original FMV and return to gameplay](11-first-fmv.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
