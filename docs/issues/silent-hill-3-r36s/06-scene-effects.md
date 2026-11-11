# Preserve representative gameplay and cutscene rendering

Local GitHub issue draft 06. Structure approved 2026-11-11; publication withheld at user's request. No labels assigned.

## What to build

Play repeatable scene set with correct lighting, fog, transparency, reflections, fades and interface presentation.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC06, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Compare indoor flashlight, fog, retained shadows, palette-dependent hair alpha, transparency/reflections and real-time cutscenes against trusted baseline captures.
- [ ] Exercise map/inventory, transitions and frame snapshots with consistent coordinate, depth, clipping and readback behavior; preview persistence remains separate save/load acceptance.
- [ ] Verify cold/warm shader-cache behavior after renderer changes; no stale-cache workaround or repeated material GL/shader faults.
- [ ] Record scene/checkpoint/camera and build identities so same cases can gate later resolution and performance changes.

## Blocked by

- [05: Reach menus and first playable scene through native GLES3](05-first-gameplay.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
