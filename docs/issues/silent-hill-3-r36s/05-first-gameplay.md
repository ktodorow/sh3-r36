# Reach menus and first playable scene through native GLES3

Local GitHub issue draft 05. Structure approved 2026-11-11; publication withheld at user's request. No labels assigned.

## What to build

From Ports, enter readable game menus, start game, render first interactive scene at 640×480 and exit to frontend.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC02, AC03, AC06, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Connect verified GLES paths to actual game renderer, preserving desktop baseline and handling required context/loading/shader/resource semantics.
- [ ] Use 640×480 Internal resolution and Output resolution with correct 4:3 presentation and readable initial menus/HUD.
- [ ] Capture actual scene, input response, build/data identities, shader/GL failures and cold/warm runs; compare against trusted original/desktop baseline.
- [ ] Record first playable checkpoint and reusable scene evidence. This milestone does not pass complete effects, physical-control matrix, campaign, movies or 30 FPS acceptance.

## Blocked by

- [03: Render game-derived shader and indexed-draw samples on R36S](03-gles-shaders-draws.md)
- [04: Render game-derived texture and framebuffer samples on R36S](04-gles-resources.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
