# Return cleanly from complete sessions and failure paths

Local GitHub issue draft 15. Structure approved 2026-11-11; publication withheld at user's request. No labels assigned.

## What to build

Cold/warm launch full integrated package, play/save/watch video, exit or encounter failure, then regain usable frontend.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC01, AC03, AC10, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Use installed PortMaster lifecycle and compatible private dependencies for actual integrated game, controls, writable state and decoder resources.
- [ ] Exercise bad/missing inputs, runtime failure, movie failure and orderly/physical exit; verify no owned helpers or mounts remain and frontend is usable.
- [ ] Preserve originals, prior valid saves/logs and unrelated ports; distinguish run failures from failed evidence collection and attempt collection after failures.
- [ ] Host fixtures cover launcher failure/cleanup behavior only. Actual R36S evidence covers normal and failing integrated sessions.

## Blocked by

- [07: Play normal actions using R36S controls](07-physical-controls.md)
- [08: Resume saved progress and settings after cold restart](08-persistence.md)
- [12: Complete all-original-FMV playback and lifecycle coverage](12-all-fmvs.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
