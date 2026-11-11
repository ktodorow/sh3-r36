# Select verified 30 FPS profile with conditional 320×240 fallback

Local GitHub issue draft 14. Structure approved 2026-11-11; publication withheld at user's request. No labels assigned.

## What to build

Select and persist evidence-backed lowest-graphics profile, preferring 640×480 and testing 320×240 when 640×480 is unstable.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC06, AC07, AC08, AC10, AC11. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Define user-approved treatment of rare loading/transition stalls before claiming stability; retain 30 FPS requirement rather than inventing numeric waiver.
- [ ] If 640×480 meets agreed target, retain preferred profile. Otherwise expose and measure matched 320×240 Internal resolution with fixed 640×480 Output resolution, correct 4:3 and readable UI.
- [ ] Recheck scene effects, save previews/settings across resolution changes, original simulation speed and audio at both supported modes; record chosen profile and paired evidence.
- [ ] Resolution reduction cannot pass CPU-bound slowdown. Turn any remaining measured bottleneck into bounded follow-up fix tickets that block this capability; do not promise unrestricted optimization within this ticket.

## Blocked by

- [08: Resume saved progress and settings after cold restart](08-persistence.md)
- [13: Profile correct representative gameplay at 640×480](13-profile-640.md)

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
