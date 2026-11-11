# Sustain hot sessions and repeated transitions within memory limits

Local GitHub issue draft 16. Structure approved 2026-11-11; publication withheld at user's request. No labels assigned.

## What to build

Continue selected profile through repeatable gameplay/movie/save/load loops and long hot session without OOM, corruption or resource growth.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC03, AC05, AC10, AC11, AC12, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Record baseline, warmed and peak process/system memory, relevant GPU/texture/decoder/guest-heap telemetry and thermal/clock behavior; distinguish virtual reservation from residency.
- [ ] Repeat representative room transitions, combat, saves/loads, movies and exits using safe preserved checkpoints; verify no unbounded growth, OOM or reproducible audio races.
- [ ] Retain prior valid saves and confirm clean frontend return after soak. No blind quarantine reduction or gameplay timing change counts as memory fix.
- [ ] State observed duration, loops, pass/fail and untested limits. Successful controls/saves/all movies/cleanup plus bounded hot-session evidence establishes G5 for campaign sign-off.

## Blocked by

- [14: Select verified 30 FPS profile with conditional 320×240 fallback](14-verified-profile.md)
- [15: Return cleanly from complete sessions and failure paths](15-session-cleanup.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
