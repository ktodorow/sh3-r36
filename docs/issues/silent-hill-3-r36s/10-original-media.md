# Identify original FMVs and measure native decode feasibility

Published as [#10](https://github.com/ktodorow/sh3-nx-r36s/issues/10) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Inventory owner-supplied original movies and run repeatable target decode measurements without modifying media.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC05, AC11, AC12, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Identify actual containers/codecs, variants, dimensions, cadence, duration and audio/subtitle sources; extension and inherited comments are not codec proof.
- [ ] Trace movie calls used by matching game and review shared SH2 precedent before selecting narrow integration; choose decoder from actual support evidence.
- [ ] Compile decoder dependencies only in reusable Docker Linux ARM64 environment and measure original-media decode time, audio handling and peak memory on current R36S.
- [ ] Preserve source cadence/content and original assets. Unsupported or too-slow decode remains explicit blocker; do not substitute offline transcodes or treat inventory report alone as decoder capability pass.

## Blocked by

- [02: Launch reproducible Linux ARM64 runtime diagnostics](02-native-runtime.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
