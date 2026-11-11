# Launch reproducible Linux ARM64 runtime diagnostics

Published as [#2](https://github.com/ktodorow/sh3-nx-r36s/issues/2) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Build native runtime in reusable Docker Linux ARM64 environment and launch its diagnostics through installed PortMaster package.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC02, AC03, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Read or create project build guide before build work; reuse compatible existing environment, pin inputs and provide scoped cleanup preserving source, final artifacts and evidence.
- [ ] Generate matching game code and compile compatible AArch64 artifacts, preserving translated guest semantics and required compiler assumptions; inspect complete dependency closure.
- [ ] On current R36S, verify guest address reservation/commit behavior and relevant thread, signal and timer diagnostics independently of game rendering; reserve versus resident memory remains explicit.
- [ ] Keep private dependencies port-local, retain firmware graphics provider initially, collect actual runtime results and clean frontend return. G2 requires passing runtime evidence, not just successful linking.

## Blocked by

- [01: Validate Game data and record current R36S target](01-preflight.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
