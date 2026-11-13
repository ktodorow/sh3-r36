# Resume saved progress and settings after cold restart

Published as [#8](https://github.com/ktodorow/sh3-r36/issues/8) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history. Clarification on 2026-11-13 records owner's acceptance of room/play-time identification on original Load screen.

## What to build

Save progress, exit, cold-launch and resume correct game state with intact save identification and settings.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC10, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [x] Establish writable save/config/mapping/cache/log ownership while preserving original Game data, existing saves and unrelated ports.
- [x] Round-trip saves after room transitions; verify room/play time identifies saved state and progression resumes after cold restart. Preserve any preview images game provides.
- [x] Verify settings and supported mappings persist; exercise resolution-change persistence when that setting becomes available and record it for final integration recheck.
- [x] Trigger safe write-failure cases through observable public behavior; preserve previous valid save and show useful failure. Device evidence is required for real persistence.

Acceptance evidence: [issue #8 report](../../../reports/issue-08-persistence.md).
Owner confirms cold-load progression, Rendering Resolution512×256 and custom
Dash btn11 after device power cycles. Room/play-time identification accepted
explicitly on2026-11-13. Owner approved **"Publish and close #8"** after local
review on2026-11-13. GitHub issue records final commit, completion handoff and
verified state. Recheck persistence after final
resolution/input integration; fault injection runs in ARM64 Docker, while actual
R36S round trips establish real persistence.

## Blocked by

- [05: Reach menus and first playable scene through native GLES3](05-first-gameplay.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
