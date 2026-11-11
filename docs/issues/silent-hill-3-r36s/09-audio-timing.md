# Preserve game audio and simulation speed at 30 FPS

Published as [#9](https://github.com/ktodorow/sh3-nx-r36s/issues/9) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Play timed movement/combat/animation sequences with complete gameplay audio and intended game speed under 30 FPS presentation.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC08, AC11. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Compare movement, combat, animation and timers to trusted baseline using repeatable cases; frame cap cannot halve simulation speed.
- [ ] Verify music, speech and effects across representative transitions and repeated playback without reproducible looping races, underruns or drift.
- [ ] If Linux guest-thread/audio faults occur, establish reproduced cause before bounded scheduling changes; do not blindly constrain whole process or alter allocator lifetime policy.
- [ ] Keep gameplay clocks distinct from future movie clock. Repeat timing/audio cases at both supported resolutions during profile acceptance.

## Blocked by

- [05: Reach menus and first playable scene through native GLES3](05-first-gameplay.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
