# Play normal actions using R36S controls

Published as [#7](https://github.com/ktodorow/sh3-nx-r36s/issues/7) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Navigate menus and perform normal gameplay actions using handheld controls and PortMaster mappings.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC09, AC03. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Record physical control/action matrix for movement, camera, combat, weapon/search actions, map, inventory, pause, confirm/cancel and exit.
- [ ] Verify both sticks, d-pad, face/shoulder buttons, digital-trigger axis expectations and stick clicks where used; keyboard must not be required for normal play.
- [ ] Check platform/positional button conventions on actual hardware. Remapping choices flow into persistence acceptance rather than being assumed saved.
- [ ] Demonstrate predictable orderly exit and frontend return using physical controls; fixture success cannot pass this matrix.

## Blocked by

- [05: Reach menus and first playable scene through native GLES3](05-first-gameplay.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
