# Silent Hill 3 R36S — local issue drafts

User approved 19-ticket structure on 2026-11-11 and subsequently authorized **local commit** of spec, ticket drafts and supporting files. These files are draft GitHub issue bodies, not published issues or replacement issue tracker. Keep all tickets unlabeled, including no `ready-for-agent` tag. Pushing, tracker settings, issue creation and closure remain unapproved.

Canonical [feature spec](../../specs/silent-hill-3-r36s.md) defines requirements. [Approved breakdown](../silent-hill-3-r36s-ticket-breakdown.md) preserves scope, acceptance mapping and capability handoffs. No implementation or device capability has passed by creating these drafts. Documentation-only validation uses scope, links and dependency checks; behavioral implementation follows project RED–GREEN–REFACTOR and actual R36S acceptance.

Draft numbers are stable local identifiers, not GitHub issue numbers. One file per issue; blocker links refer to files until future approved publication replaces them with real issue relationships and canonical spec links at verified pushed commit. Native blocker relationships preferred where supported. Source was spec file, so no parent issue is invented or published.

| Draft | Title | Blocked by |
| --- | --- | --- |
| 01 | [Validate Game data and record current R36S target](01-preflight.md) | None |
| 02 | [Launch reproducible Linux ARM64 runtime diagnostics](02-native-runtime.md) | 01 |
| 03 | [Render game-derived shader and indexed-draw samples on R36S](03-gles-shaders-draws.md) | 02 |
| 04 | [Render game-derived texture and framebuffer samples on R36S](04-gles-resources.md) | 02 |
| 05 | [Reach menus and first playable scene through native GLES3](05-first-gameplay.md) | 03, 04 |
| 06 | [Preserve representative gameplay and cutscene rendering](06-scene-effects.md) | 05 |
| 07 | [Play normal actions using R36S controls](07-physical-controls.md) | 05 |
| 08 | [Resume saved progress and settings after cold restart](08-persistence.md) | 05 |
| 09 | [Preserve game audio and simulation speed at 30 FPS](09-audio-timing.md) | 05 |
| 10 | [Identify original FMVs and measure native decode feasibility](10-original-media.md) | 02 |
| 11 | [Play first original FMV and return to gameplay](11-first-fmv.md) | 05, 09, 10 |
| 12 | [Complete all-original-FMV playback and lifecycle coverage](12-all-fmvs.md) | 11 |
| 13 | [Profile correct representative gameplay at 640×480](13-profile-640.md) | 06, 09 |
| 14 | [Select verified 30 FPS profile with conditional 320×240 fallback](14-verified-profile.md) | 08, 13 |
| 15 | [Return cleanly from complete sessions and failure paths](15-session-cleanup.md) | 07, 08, 12 |
| 16 | [Sustain hot sessions and repeated transitions within memory limits](16-hot-session.md) | 14, 15 |
| 17 | [Verify complete campaign progression on R36S](17-campaign.md) | 16 |
| 18 | [Verify remaining required ending paths and media coverage](18-endings.md) | 17 |
| 19 | [Qualify Full port against canonical R36S acceptance criteria](19-full-port-acceptance.md) | 18 |

Initial frontier: 01. After 02 passes, 03, 04 and 10 can proceed independently. After 05 passes, 06, 07, 08 and 09 can proceed independently. Prerequisite-free research can proceed earlier; dependent implementation still needs passing capability evidence.

Future publication must retain approved scopes and blocker graph, omit local-draft administration text from posted bodies, resolve local links to published references, and preserve latest no-label instruction. Project review gate remains in force; do not enable GitHub Issues or publish this batch without later explicit approval. Implementation tickets remain open until their own acceptance passes.
