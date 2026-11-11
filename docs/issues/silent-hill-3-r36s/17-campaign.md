# Verify complete campaign progression on R36S

Local GitHub issue draft 17. Structure approved 2026-11-11; publication withheld at user's request. No labels assigned.

## What to build

Complete continuous normal campaign route from new game to ending/credits through installed package, preserving traceable checkpoints.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC04, AC05, AC06, AC08, AC09, AC10, AC11, AC12. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Derive complete ordered area/encounter/puzzle/real-time-cutscene checklist from trusted original/desktop baseline; record actual route, checkpoint saves, build/data/profile identities and evidence for each entry.
- [ ] Verify full progression, physical actions, rendering/audio/timing, in-context FMV triggers and save/resume across campaign rather than substituting isolated scene or movie probes.
- [ ] Keep task bounded to qualification and reproduced faults: create focused regression-fix tickets for newly found blockers, retain failing evidence, and recheck affected route after fixes before passing.
- [ ] Full campaign pass requires no unresolved progression/material presentation faults. A checklist draft or blocker report is not campaign completion; additional ending routes remain separate.

## Blocked by

- [16: Sustain hot sessions and repeated transitions within memory limits](16-hot-session.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
