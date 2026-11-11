# Render game-derived texture and framebuffer samples on R36S

Published as [#4](https://github.com/ktodorow/sh3-nx-r36s/issues/4) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Launch resource-operation samples, capture correct images and readback, then return to frontend with format and memory evidence.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC02, AC06, AC10, AC12, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Verify actual-use BGRA vertex/texture distinctions, packed formats, palette alpha, mip/update behavior and DXT1/3/5 support separately; preserve original data.
- [ ] For required unsupported formats, validate compatible conversion and record source, temporary and GPU memory costs; offline media/texture conversion is not silently approved.
- [ ] Exercise framebuffer attachments, depth/stencil, blit/copy, orientation and legal readback formats against independent reference images, including preview/fade source behavior.
- [ ] Verify required sampler/border/depth-clamp behavior where used. Together with shader/draw results, this provides G3 operation evidence, not complete renderer compatibility.

## Blocked by

- [02: Launch reproducible Linux ARM64 runtime diagnostics](02-native-runtime.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
