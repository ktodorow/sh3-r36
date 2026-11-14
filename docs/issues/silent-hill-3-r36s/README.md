# Silent Hill 3 R36S — implementation issues

User approved 19-ticket structure and publication on 2026-11-11. Current tracker check on 2026-11-14: #1–#9 closed; #10–#19 open. GitHub issue bodies and comments hold current task history; local files preserve approved scope.

Canonical [feature spec](../../specs/silent-hill-3-r36s.md) defines requirements. Issues link its [publication source revision](https://github.com/ktodorow/sh3-nx-r36s/blob/4bdb4560594373d824122d4907a88d009e7d7668/docs/specs/silent-hill-3-r36s.md). [Approved breakdown](../silent-hill-3-r36s-ticket-breakdown.md) preserves acceptance mapping and capability handoffs; [publication manifest](github-issues.json) records verified identifiers and edges.

No implementation or device capability passed by publishing these issues. Documentation-only validation checked scopes, links, labels, states and dependency graph. Behavioral implementation follows project RED–GREEN–REFACTOR and actual R36S acceptance.

## Current priority order

Owner instruction, 2026-11-14: performance first. Finish representative gameplay profiling and verified 30 FPS profile before starting original-movie implementation. Preserve 30 FPS target, intended game speed, approved resolution fallback and complete-story requirements in canonical spec.

| Rank | Priority | Issue and approved scope | Open blockers, checked 2026-11-14 |
| --- | --- | --- | --- |
| 1 | P0 — performance | [#13](https://github.com/ktodorow/sh3-r36/issues/13): [Profile representative gameplay and measured bottlenecks](13-profile-640.md) | None; #6 and #9 closed |
| 2 | P0 — performance | [#14](https://github.com/ktodorow/sh3-r36/issues/14): [Verify 30 FPS graphics/resolution profile](14-verified-profile.md) | #13 |
| 3 | P1 — gameplay stability | [#16](https://github.com/ktodorow/sh3-r36/issues/16): [Sustain hot sessions, memory and repeated transitions](16-hot-session.md) | #14, #15 |
| 4 | P1 — gameplay stability | [#17](https://github.com/ktodorow/sh3-r36/issues/17): [Verify campaign progression and later-area faults](17-campaign.md) | #16 |
| 5 | P1 — gameplay stability | [#15](https://github.com/ktodorow/sh3-r36/issues/15): [Verify clean exit and failure recovery](15-session-cleanup.md) | #12 |
| 6 | P2 — movies | [#10](https://github.com/ktodorow/sh3-r36/issues/10): [Identify movies and measure native decoding](10-original-media.md) | None; schedule after P0 |
| 7 | P2 — movies | [#11](https://github.com/ktodorow/sh3-r36/issues/11): [Integrate first original movie](11-first-fmv.md) | #10 |
| 8 | P2 — movies | [#12](https://github.com/ktodorow/sh3-r36/issues/12): [Verify all original movies and transitions](12-all-fmvs.md) | #11 |
| 9 | P3 — final coverage | [#18](https://github.com/ktodorow/sh3-r36/issues/18): [Verify remaining ending paths and media](18-endings.md) | #17 |
| 10 | P3 — final coverage | [#19](https://github.com/ktodorow/sh3-r36/issues/19): [Audit complete Full port acceptance](19-full-port-acceptance.md) | #18 |

Priority ranks engineering attention; native dependencies still gate implementation and completion. While #13/#14 remain open, prioritize their warm/cold frame-time gaps, shader/loading stalls, sustained performance and broader representative gameplay measurements. Use relevant hot-session and later-area observations in that performance evidence; they do not complete #16 or #17.

Original movies remain required, at lower scheduling priority. Integrated cleanup #15 includes movie failures; #16 and #17 inherit that prerequisite. After P0 passes, current dependency-respecting completion order is #10 → #11 → #12 → #15 → #16 → #17 → #18 → #19. Prerequisite-free investigation may proceed earlier; dependent implementation still requires actual passing capabilities. No blocking edge or acceptance criterion is removed by reprioritization.

Use `priority:P0` through `priority:P3` on open issues only to record scheduling priority; no triage/readiness label is implied. Existing issue numbers, titles, comments and closed tasks retain their identities. Latest performance handoff: [#13](https://github.com/ktodorow/sh3-r36/issues/13#issuecomment-6873391478), [#14](https://github.com/ktodorow/sh3-r36/issues/14#issuecomment-6873391751).

## Completed groundwork

Tracker state checked 2026-11-14. Closed milestones retain their original scope snapshots and dependency links; read published comments for acceptance evidence and remaining limits.

| Plan | GitHub issue | Approved scope snapshot | Blocked by |
| --- | --- | --- | --- |
| 01 | [#1](https://github.com/ktodorow/sh3-nx-r36s/issues/1) | [Validate Game data and record current R36S target](01-preflight.md) | None |
| 02 | [#2](https://github.com/ktodorow/sh3-nx-r36s/issues/2) | [Launch reproducible Linux ARM64 runtime diagnostics](02-native-runtime.md) | [#1](https://github.com/ktodorow/sh3-nx-r36s/issues/1) |
| 03 | [#3](https://github.com/ktodorow/sh3-nx-r36s/issues/3) | [Render game-derived shader and indexed-draw samples on R36S](03-gles-shaders-draws.md) | [#2](https://github.com/ktodorow/sh3-nx-r36s/issues/2) |
| 04 | [#4](https://github.com/ktodorow/sh3-nx-r36s/issues/4) | [Render game-derived texture and framebuffer samples on R36S](04-gles-resources.md) | [#2](https://github.com/ktodorow/sh3-nx-r36s/issues/2) |
| 05 | [#5](https://github.com/ktodorow/sh3-nx-r36s/issues/5) | [Reach menus and first playable scene through native GLES3](05-first-gameplay.md) | [#3](https://github.com/ktodorow/sh3-nx-r36s/issues/3), [#4](https://github.com/ktodorow/sh3-nx-r36s/issues/4) |
| 06 | [#6](https://github.com/ktodorow/sh3-nx-r36s/issues/6) | [Preserve representative gameplay and cutscene rendering](06-scene-effects.md) | [#5](https://github.com/ktodorow/sh3-nx-r36s/issues/5) |
| 07 | [#7](https://github.com/ktodorow/sh3-nx-r36s/issues/7) | [Play normal actions using R36S controls](07-physical-controls.md) | [#5](https://github.com/ktodorow/sh3-nx-r36s/issues/5) |
| 08 | [#8](https://github.com/ktodorow/sh3-nx-r36s/issues/8) | [Resume saved progress and settings after cold restart](08-persistence.md) | [#5](https://github.com/ktodorow/sh3-nx-r36s/issues/5) |
| 09 | [#9](https://github.com/ktodorow/sh3-nx-r36s/issues/9) | [Preserve game audio and simulation speed at 30 FPS](09-audio-timing.md) | [#5](https://github.com/ktodorow/sh3-nx-r36s/issues/5) |

Local plan numbers are distinct identifiers even when they currently match GitHub numbers. Follow mapped GitHub issues, read comments and verify blockers before work. Local blocker links remain links between approved snapshots; native GitHub relationships are verified live publication edges.

Open implementation issues remain open until their own acceptance passes and owner approves closure. Complete campaign, original movies, final performance profile and integrated long-session acceptance remain pending. Reprioritization does not certify Full port or close any implementation issue. No separate parent issue created.
