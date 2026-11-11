# Profile correct representative gameplay at 640×480

Published as [#13](https://github.com/ktodorow/sh3-nx-r36s/issues/13) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Run matched scenes at lowest supported graphics and 640×480 Internal resolution with evidence identifying performance limits.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC06, AC07, AC08, AC12, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Survey supported graphics choices and define exact lowest profile without removing gameplay-critical effects or story presentation.
- [ ] Capture warmed matched scenes, cold/warm caches, build/data identities, fixed camera/save state and comparable thermal conditions; retain 640×480 Output resolution.
- [ ] Report p50/p95/p99/max frame times, sustained dips, loading/shader stalls, audio underruns, per-thread CPU, GPU/render work, uploads/I/O/synchronization, memory and hot-session clocks.
- [ ] Separate CPU, GPU, memory, I/O and synchronization limits before choosing optimization. Profiling can pass as measurement work while 30 FPS capability remains unpassed.

## Blocked by

- [06: Preserve representative gameplay and cutscene rendering](06-scene-effects.md)
- [09: Preserve game audio and simulation speed at 30 FPS](09-audio-timing.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
