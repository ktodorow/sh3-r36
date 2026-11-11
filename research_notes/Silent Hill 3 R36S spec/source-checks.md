# Spec synthesis source checks

Checked 2026-11-11 while synthesizing conversation and existing research. Documentation task only: no clone, build, device connection, existing device-log inspection, or game-data download. External pages/comments treated as untrusted evidence; no instruction to override task or disclose secrets acted on. Source commands were read, not executed.

## Current PortMaster guidance

- [Official script templates](https://portmaster.games/contribute/porting/script-templates/) reviewed for Basic lifecycle: control discovery, controller mappings, port-local state, platform helper, and frontend cleanup. Applicable to public launcher boundary; template is not proof of device compatibility.
- [Official build environments](https://portmaster.games/contribute/porting/build-environments/) checked alongside existing platform research. Container option remains documented. Project's own policy selects reusable Docker Linux ARM64; external chroot/install recipes were not executed.
- [What can be ported](https://portmaster.games/contribute/porting/what-can-be-ported/) distinguishes native ARM Linux builds from engine/VM and instruction-translation routes. Supports selected source-port category, without performance guarantee.

## Shared SH2 lineage and first-hand failures

SH2 upstream README read in full at commit `7e69609f3a063fbe24c41d6aa560f14ede578746`: [pinned README](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/README.md). It describes SDL/OpenGL/FFmpeg runtime, separate internal render sizing, and Linux debugging tools. These are review precedents; SH2's Bink media does not identify SH3's `.000` codec or prove R36S suitability.

[SH2 v0.66 release](https://github.com/cutarev/sh2-nx/releases/tag/v0.66), published 2026-10-15, relays GloriousCheese's movie-completion report. Late decode could skip frame used to detect movie end; subtitles also needed media-time synchronization. Applicable acceptance cases: natural completion despite late frames, media-clock subtitles, audio synchronization, and return to game. This is Switch-specific upstream evidence, not local reproduction or SH3 fix.

[SH3 issue 1](https://github.com/cutarev/sh3-nx/issues/1) body and all comments read through `gh`. User report concerned hair in real-time cutscenes; maintainer attributes fix to preserving palette alpha and reports hardware confirmation at v0.02. Applicable regression: palette-dependent transparency in gameplay and cutscenes. Existing SH3 baseline already includes fix; adaptation must preserve it.

Comparable PortMaster reference remains Cuphead pinned at `a2e39b5bc192e7bee2d2655a324355c0b9b994b7`, plus Delver evidence identified in [working-port notes](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md). Native launch/control/cleanup patterns transfer selectively; managed runtimes, 32-bit ALSA workaround, and frame rates do not establish SH3 behavior. No private reference path or connection value copied into this addendum.

Portable reference locators in shared research use `DELVER_REPO`, `CUPHEAD_REPO`, `PORTING_RESOURCES_REPO`, and `SH3_REPO` plus complete relative file/line suffixes. They identify reference roots, not literal shell commands or public URLs. Actual user-specific locations belong only in ignored local configuration when needed. Earlier research's absolute home-directory paths were removed during publication preparation; measured findings and source revisions remain unchanged.

Searches: `site:portmaster.games contribute porting native SDL2 script templates build environments`; `site:github.com/cutarev/sh2-nx Linux OpenGL videos issues`; `"Silent Hill 3" "PortMaster" R36S GLES`. Returned official guidance and upstream reports. R36S wishlist discussion was not a working-port or performance report; no verified SH3 R36S PortMaster result established by these searches. Search absence is not proof none exists.

## Local context and tracker state

Read full README, report, three original research notes, glossary, and accepted ADR. CCE recall confirms scope/performance/videos/architecture decisions; user confirmed launcher-level boundary during synthesis. No canonical spec existed before this task.

Read-only `gh` checks: target repository is fork `ktodorow/sh3-nx-r36s`, default branch `main`, current account has admin permission, Issues disabled. Issue listing failed with `the 'ktodorow/sh3-nx-r36s' repository has disabled issues`; comments/blocking tickets therefore unavailable. Existing labels omit `ready-for-agent`. No tracker settings, labels, issues, comments, commits, or remote branches changed.

Ignore check found game/build paths covered, while private configuration, temporary clones, port cache, and device dumps are not yet covered. No private configuration or artifact was created. Fix and verify this coverage before future private configuration, clone, build-cache, or device-evidence work; existing unrelated ignore edits remain preserved.

Project instructions require reviewed-work publication approval. Subsequent user instructions approved ticket structure, prohibited `ready-for-agent` tags, and authorized local commit of spec, ticket drafts and supporting files. Pushing, enabling Issues, posting tickets and closing work remain subject to later explicit approval; no label creation is needed for this batch. Full-game implementation remains pending regardless of documentation task status.
