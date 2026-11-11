# Silent Hill 3 R36S — implementation issues

User approved 19-ticket structure and publication. All 19 issues published on 2026-11-11, verified open and unlabeled, with 26 native GitHub blocking relationships. No `ready-for-agent` tags applied. GitHub issue bodies and comments hold current task history; local files preserve approved scope.

Canonical [feature spec](../../specs/silent-hill-3-r36s.md) defines requirements. Issues link its [publication source revision](https://github.com/ktodorow/sh3-nx-r36s/blob/4bdb4560594373d824122d4907a88d009e7d7668/docs/specs/silent-hill-3-r36s.md). [Approved breakdown](../silent-hill-3-r36s-ticket-breakdown.md) preserves acceptance mapping and capability handoffs; [publication manifest](github-issues.json) records verified identifiers and edges.

No implementation or device capability passed by publishing these issues. Documentation-only validation checked scopes, links, labels, states and dependency graph. Behavioral implementation follows project RED–GREEN–REFACTOR and actual R36S acceptance.

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
| 10 | [#10](https://github.com/ktodorow/sh3-nx-r36s/issues/10) | [Identify original FMVs and measure native decode feasibility](10-original-media.md) | [#2](https://github.com/ktodorow/sh3-nx-r36s/issues/2) |
| 11 | [#11](https://github.com/ktodorow/sh3-nx-r36s/issues/11) | [Play first original FMV and return to gameplay](11-first-fmv.md) | [#5](https://github.com/ktodorow/sh3-nx-r36s/issues/5), [#9](https://github.com/ktodorow/sh3-nx-r36s/issues/9), [#10](https://github.com/ktodorow/sh3-nx-r36s/issues/10) |
| 12 | [#12](https://github.com/ktodorow/sh3-nx-r36s/issues/12) | [Complete all-original-FMV playback and lifecycle coverage](12-all-fmvs.md) | [#11](https://github.com/ktodorow/sh3-nx-r36s/issues/11) |
| 13 | [#13](https://github.com/ktodorow/sh3-nx-r36s/issues/13) | [Profile correct representative gameplay at 640×480](13-profile-640.md) | [#6](https://github.com/ktodorow/sh3-nx-r36s/issues/6), [#9](https://github.com/ktodorow/sh3-nx-r36s/issues/9) |
| 14 | [#14](https://github.com/ktodorow/sh3-nx-r36s/issues/14) | [Select verified 30 FPS profile with conditional 320×240 fallback](14-verified-profile.md) | [#8](https://github.com/ktodorow/sh3-nx-r36s/issues/8), [#13](https://github.com/ktodorow/sh3-nx-r36s/issues/13) |
| 15 | [#15](https://github.com/ktodorow/sh3-nx-r36s/issues/15) | [Return cleanly from complete sessions and failure paths](15-session-cleanup.md) | [#7](https://github.com/ktodorow/sh3-nx-r36s/issues/7), [#8](https://github.com/ktodorow/sh3-nx-r36s/issues/8), [#12](https://github.com/ktodorow/sh3-nx-r36s/issues/12) |
| 16 | [#16](https://github.com/ktodorow/sh3-nx-r36s/issues/16) | [Sustain hot sessions and repeated transitions within memory limits](16-hot-session.md) | [#14](https://github.com/ktodorow/sh3-nx-r36s/issues/14), [#15](https://github.com/ktodorow/sh3-nx-r36s/issues/15) |
| 17 | [#17](https://github.com/ktodorow/sh3-nx-r36s/issues/17) | [Verify complete campaign progression on R36S](17-campaign.md) | [#16](https://github.com/ktodorow/sh3-nx-r36s/issues/16) |
| 18 | [#18](https://github.com/ktodorow/sh3-nx-r36s/issues/18) | [Verify remaining required ending paths and media coverage](18-endings.md) | [#17](https://github.com/ktodorow/sh3-nx-r36s/issues/17) |
| 19 | [#19](https://github.com/ktodorow/sh3-nx-r36s/issues/19) | [Qualify Full port against canonical R36S acceptance criteria](19-full-port-acceptance.md) | [#18](https://github.com/ktodorow/sh3-nx-r36s/issues/18) |

Initial implementation frontier: [#1](https://github.com/ktodorow/sh3-nx-r36s/issues/1). After runtime evidence passes, shader/draw, resource and original-media tracks can proceed independently. Prerequisite-free research may proceed earlier; dependent implementation requires actual passing capability evidence.

Local plan numbers are distinct identifiers even when they currently match GitHub numbers. Follow mapped GitHub issues, read comments and verify blockers before work. Local blocker links remain links between approved snapshots; native GitHub relationships are verified live publication edges.

All implementation issues remain open until their own acceptance passes. Complete campaign, original FMVs, controls, saves, audio, performance and memory acceptance remain pending. No separate parent issue created or closed.
