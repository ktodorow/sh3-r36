# Render game-derived shader and indexed-draw samples on R36S

Published as [#3](https://github.com/ktodorow/sh3-nx-r36s/issues/3) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Use installed launcher to render and collect known game-derived shader/geometry samples on hardware GLES.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC02, AC06, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Record actual SDL/EGL backend, hardware renderer, GLES/GLSL versions, relevant extensions and limits; no version spoofing or software-renderer pass.
- [ ] Exercise representative generated vertex/fragment shaders and precision, indexed/base-vertex draws, coordinate/depth conventions, culling, scissor and depth/stencil results against independent expectations.
- [ ] Select supported core/extension paths or verify required fallback through rendered output; report unsupported required operations as unresolved blockers.
- [ ] Retain desktop comparison route. Diagnostics stay under existing launcher/game-directory public boundary; fixtures and triangle-only success cannot pass game-derived operations.

## Blocked by

- [02: Launch reproducible Linux ARM64 runtime diagnostics](02-native-runtime.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
