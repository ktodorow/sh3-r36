# Resume saved progress and settings after cold restart

Published as [#8](https://github.com/ktodorow/sh3-nx-r36s/issues/8) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Save progress, exit, cold-launch and resume correct game state with intact previews and settings.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC10, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Establish writable save/config/mapping/cache/log ownership while preserving original Game data, existing saves and unrelated ports.
- [ ] Round-trip saves after room transitions; verify thumbnails identify saved state and progression resumes after cold restart.
- [ ] Verify settings and supported mappings persist; exercise resolution-change persistence when that setting becomes available and record it for final integration recheck.
- [ ] Trigger safe write-failure cases through observable public behavior; preserve previous valid save and show useful failure. Device evidence is required for real persistence.

## Blocked by

- [05: Reach menus and first playable scene through native GLES3](05-first-gameplay.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
