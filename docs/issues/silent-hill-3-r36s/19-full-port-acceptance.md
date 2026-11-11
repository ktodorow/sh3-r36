# Qualify Full port against canonical R36S acceptance criteria

Local GitHub issue draft 19. Structure approved 2026-11-11; publication withheld at user's request. No labels assigned.

## What to build

Produce final reproducible evidence that complete personal R36S port meets all canonical requirements on identified build and firmware.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC01, AC02, AC03, AC04, AC05, AC06, AC07, AC08, AC09, AC10, AC11, AC12, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Audit all thirteen criteria and six capability gates against actual passing evidence, including current target/dependency identity, campaign/endings, every original FMV and integrated controls/saves/audio/cleanup.
- [ ] Re-run performance and timing on campaign-discovered worst cases under agreed stability assessment; early representative samples or average FPS do not pass complete-game performance.
- [ ] Ensure final build/profile has current regression coverage for cold/warm launch, both resolution behaviors, write/runtime failures, bounded memory and clean frontend return; stale pre-fix evidence requires relevant recheck.
- [ ] Keep feature open while any criterion, unresolved blocker or missing hardware result remains. Prepare local closeout for explicit publication/closure review; public PortMaster submission and asset distribution remain out of scope.

## Blocked by

- [18: Verify remaining required ending paths and media coverage](18-endings.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
