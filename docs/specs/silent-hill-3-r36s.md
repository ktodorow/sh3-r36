# Silent Hill 3 full port for R36S

Status: published planning spec. Scope, graphics route, and primary test boundary confirmed by user on 2026-11-11. User approved publication of spec, supporting files and 19 implementation issues. Implementation and device acceptance have not passed.

This is canonical feature spec. Research describes evidence and proposals; this spec defines requested behavior. Tracker issue must link this document and retain task history, prerequisite results, and remaining gaps.

## Problem Statement

Owner wants complete Silent Hill 3 on personal R36S running dArkOS, launched through PortMaster and playable with handheld controls. Existing Switch port shares ARM64 instruction family with R36S, but shared CPU architecture does not supply Linux runtime compatibility, supported graphics operations, enough memory, or required performance.

Existing source statically recompiles original PC executable to C and already has Linux host runtime. Current renderer requires desktop OpenGL/GLSL beyond unchanged GL4ES route. Upstream skips original videos and has limited campaign validation. A title screen, first room, renderer probe, or match with upstream's omissions would not deliver Full port.

## Solution

Deliver native Linux ARM64 Full port using direct GLES3 renderer, existing game/runtime foundations, and PortMaster launch integration. Prioritize personal R36S acceptance before public PortMaster submission.

Performance priority is stable 30 FPS with lowest supported graphics. Prefer 640×480 Internal resolution; use 320×240 when 640×480 cannot meet stability target. Keep 640×480 Output resolution, correct 4:3 presentation, readable interface, original game speed, and complete story. Lower resolution may reduce GPU work; CPU-bound slowdown still requires its own fix.

Full port includes complete campaign, original FMVs, real-time cutscenes, audio, handheld controls, and reliable save/load. Original Game data remains owner-supplied. Capability probes and intermediate builds are verification milestones inside this feature, not final deliverables.

### Acceptance criteria

| ID | Required outcome | Required evidence |
| --- | --- | --- |
| AC01 | Supported owner-supplied PC executable/data recognized; incomplete or wrong inputs produce useful failure instead of unexplained crash. | Matching executable size/hash and data inventory; launcher error cases. |
| AC02 | Native AArch64 Linux package runs on owner's recorded dArkOS environment with compatible dependencies and hardware GLES path. | Current device fingerprint, ELF/dependency checks, actual launch and renderer identity. |
| AC03 | PortMaster launch, game session, orderly exit, and failure cleanup return control to frontend without leaving owned processes or mounts. | Cold/warm launch, runtime-failure and exit evidence; cleanup record. |
| AC04 | Complete campaign can progress through all required areas, encounters, puzzles, real-time cutscenes, and ending paths without unresolved progression failures. | Campaign checklist tied to tested build and saves; crash/regression evidence for fixes. |
| AC05 | Every original FMV plays with correct content, aspect ratio, audio timing, supported subtitles/skip behavior, and reliable return to game. | Original-media inventory and per-movie playback/completion results. |
| AC06 | Game renders correctly at supported resolutions, including fog, flashlight, shadows where retained, transparency, palette alpha, reflections, fades, menus, and save previews. | Repeatable captured scenes compared with trusted desktop/original baseline; no unresolved material rendering faults. |
| AC07 | Stable 30 FPS target assessed at lowest supported graphics, first at 640×480 Internal resolution and then at 320×240 if needed. | Matched representative scenes after warm-up; frame-time distributions, sustained dips, CPU/GPU and thermal evidence. |
| AC08 | Movement, combat, animation, game timers, and audio retain intended speed at 30 FPS and both resolutions. | Timing comparisons and audiovisual checks; frame limiting must not halve simulation speed. |
| AC09 | All normal actions are reachable with R36S controls; menus, map, inventory, camera, weapon/search actions, pause, and exit behave predictably. | Physical controller/action matrix, including digital triggers and stick clicks where used. |
| AC10 | Saves, settings, mappings, save identification, and caches persist correctly across exit, cold restart, and resolution changes. | Save/load round trips, correct room/play-time identification, resumed progression, settings/mapping persistence, safe write-failure behavior; preserve preview images where game provides them. |
| AC11 | Music, speech, effects, and movie audio remain usable without reproducible underruns, looping races, or desynchronization. | Audio checks across gameplay, transitions, movies, save/load, and sustained sessions. |
| AC12 | Long sessions and repeated transitions fit available device memory without OOM kills, unbounded growth, or save corruption. | Peak resident/system memory, relevant GPU allocation/heap telemetry, hot-session clocks, and soak results. |
| AC13 | Builds, device runs, and evidence collection are repeatable using project-owned workflows; original Game data, existing saves/logs, and unrelated ports remain preserved. | Pinned build inputs, scripted run identity, collected results, and integrity checks. |

Stable 30 FPS is target, not established result or average-FPS shortcut. Frame budget is approximately 33.33 ms. Report p50/p95/p99/max, sustained dips, loading stalls, shader warm-up, and audio underruns separately. Exact allowance for rare loading/transition stalls remains open before final acceptance; do not invent a numeric waiver or silently lower target. FMVs retain source media cadence and duration rather than being forced to gameplay frame rate.

## User Stories

1. As an R36S owner, I want to launch Silent Hill 3 from Ports, so that I can play using normal handheld workflow.
2. As a player, I want complete campaign rather than an opening-area demonstration, so that I can finish game.
3. As a player, I want every required area and progression event to work, so that crashes or missing callbacks do not block my playthrough.
4. As a player, I want original ending sequences and credits, so that story remains complete.
5. As a player, I want original FMVs restored, so that upstream's skipped videos do not remove story content.
6. As a player, I want movie audio and subtitles where supported to follow media time, so that dialogue stays understandable.
7. As a player, I want supported movie skip behavior and reliable completion, so that playback always returns control to game.
8. As a player, I want real-time cutscenes to render correctly, so that characters and story scenes remain intact.
9. As a player, I want steady 30 FPS prioritized over optional visual quality, so that gameplay feels consistent.
10. As a player, I want 640×480 Internal resolution attempted first, so that game uses preferred screen detail when performance allows.
11. As a player, I want 320×240 fallback when needed, so that lower GPU load can help meet performance target.
12. As a player, I want correct 640×480 Output resolution in both modes, so that image fills handheld screen with intended aspect ratio.
13. As a player, I want readable menus, maps, inventory, and HUD, so that lower resolution does not prevent normal play.
14. As a player, I want original movement and combat timing, so that frame limiting does not slow game simulation.
15. As a player, I want flashlight, fog, transparency, and essential scene effects to remain correct, so that navigation and atmosphere remain usable.
16. As a player, I want lowest supported graphics choices exposed clearly, so that I can select tested performance profile.
17. As a player, I want resolution/settings choices to persist, so that I do not repeat setup every launch.
18. As a player, I want sticks and d-pad to control movement/camera as intended, so that keyboard is unnecessary.
19. As a player, I want face buttons, shoulders, and digital triggers mapped correctly, so that every normal game action remains accessible.
20. As a player, I want consistent confirm/cancel, pause, map, and inventory actions, so that menus follow understandable controls.
21. As a player, I want supported button remapping to persist, so that preferred controls survive restart.
22. As a player, I want music, dialogue, and effects during gameplay, so that audio remains complete.
23. As a player, I want transitions and long sessions to avoid looping or broken sound, so that I can continue without restarting.
24. As a player, I want save/load to work throughout campaign, so that progress remains safe.
25. As a player, I want saves to survive cold restart, so that handheld power cycles do not lose progress.
26. As a player, I want save previews and settings to match actual state, so that I can identify and resume intended session.
27. As a player, I want write failures reported safely, so that existing saves are not silently damaged.
28. As a player, I want clean exit back to frontend, so that other games remain usable afterward.
29. As a player, I want launch or runtime failure to clean up owned helpers, so that failed run does not leave handheld stuck.
30. As an owner, I want clear checks for matching Game data, so that wrong executable or missing assets are diagnosed before normal play.
31. As an owner, I want original Game data and existing saves preserved, so that port setup remains repeatable and recoverable.
32. As an owner, I want compatibility checked against installed dArkOS build, so that another firmware's results are not mistaken for mine.
33. As an owner, I want port-local dependencies and settings, so that installation does not replace shared system libraries or alter unrelated ports.
34. As a maintainer, I want reusable Linux ARM64 Docker builds, so that runtime artifacts can be reproduced.
35. As a maintainer, I want executable/dependency ABI recorded, so that mixed architectures and incompatible libc requirements are caught.
36. As a maintainer, I want scripted unattended device runs and collected evidence, so that failures can be reproduced and diagnosed locally.
37. As a maintainer, I want separate preserved run results, so that later experiments do not erase earlier evidence or original logs.
38. As a maintainer, I want frame-time, CPU, memory, and thermal measurements, so that optimization targets actual bottleneck.
39. As a maintainer, I want matched scene captures and cold/warm runs, so that rendering or cache regressions remain visible.
40. As a maintainer, I want existing guest-code regressions checked after relevant fixes, so that later areas do not regress while opening room works.
41. As a maintainer, I want credentials and private reference locations kept local, so that shared docs and evidence remain publishable.
42. As an owner, I want personal-device acceptance completed before public submission, so that release work follows proven Full port behavior.

## Implementation Decisions

- Baseline is native Linux ARM64 plus direct GLES3, as accepted in architecture decision. Reuse Linux host runtime and statically recompiled PC game; retain desktop renderer as comparison baseline.
- Adapt existing D3D8 rendering layer, context/function loading, shader generation, resources, and launcher presentation. Required semantics include clip/depth/orientation, culling, precision, packed colors, palette alpha, compressed textures, indexed draws, framebuffers, blits, and readback.
- Select exact GLES profile and extension paths from current device operation tests. GL version spoofing, a context query, or successful triangle does not prove game compatibility. Provide verified fallback for required unsupported operations.
- Keep supported Internal resolutions distinct from fixed handheld Output resolution. Preserve 4:3 layout and readable interface. Lowest graphics must become explicit tested settings; effects cuts must preserve gameplay and required story presentation.
- Preserve translated guest semantics, compiler assumptions, 32-bit guest-address abstraction, and 64-bit host runtime. Sparse virtual reservation does not establish physical-memory requirement or fit.
- Profile CPU, GPU, memory, uploads, I/O, and synchronization before optimizing. Resolution fallback addresses pixel work, not generated-code CPU cost. Changes to allocator quarantine or guest-thread scheduling require regression evidence.
- Restore original-video integration through game-used movie boundary. Identify actual media first; decoder, audio clock, completion, subtitles, skip behavior, and rendering-state restoration are required concerns. FFmpeg is candidate precedent, not confirmed codec solution. Offline transcoding is not pre-approved.
- Reuse SDL audio/input/filesystem foundations. Integrate PortMaster controls and orderly lifecycle while preserving writable save/config/cache ownership and original-data integrity. Reference ports supply patterns, not engine-specific Java/Unity/Mono dependencies.
- Compile executables, libraries, packages, and executable test artifacts only inside reusable Docker Linux ARM environment, defaulting to ARM64. Pin compatible compiler/sysroot/dependencies; verify complete runtime ABI closure and Cortex-A35 compatibility. Reuse environment before creating resources.
- Use saved host/device workflows for every device probe, log inspection, deployment, test, and result collection. Resolve port directory from private local configuration and approved packaging arrangement; document it before first deployment. Preserve separate run evidence and attempt collection after failures.
- Keep device credentials and user-specific reference locations in ignored private configuration; maintain example keys without private values. Verify ignore coverage before private artifacts. Keep dependencies isolated from firmware libraries initially.
- Follow project research workflow for each porting task and new blocker: check official PortMaster guidance, first-hand reports, and comparable working ports, including shared SH2 lineage. Review applicability before executing helpers or copying fixes.
- Work in one-behavior vertical slices with observed RED, minimal GREEN, and reviewed REFACTOR. Preserve launcher-level public boundary; changes to agreed boundary require confirmation.
- Public PortMaster submission follows personal Full port acceptance. Publishing repository documentation or creating implementation issue does not declare game complete.

## Testing Decisions

User explicitly confirmed on 2026-11-11: **installed PortMaster launcher → complete game session → clean return to frontend** is primary public acceptance boundary. This covers game-data validation, runtime startup, rendering, movies, audio, physical input, persistence, performance, and cleanup through observable outcomes. Existing Linux executable/game-directory entry is useful diagnostic interface underneath this boundary; no new renderer-internal public testing seam is selected.

- Good tests assert behavior independently of implementation: resulting game scene, reachable action, saved progress after restart, correct movie completion, useful failure, restored frontend, or preserved file. Avoid internal helper-call assertions and tests that copy implementation logic.
- Host fixture tests exercise launcher failures and cleanup only. Replace external PortMaster helpers/processes/filesystem dependencies at external boundary when necessary. Fixtures cannot pass GPU support, physical controller behavior, decoder performance, or device acceptance.
- Target checks use real package, real SDL/EGL/driver, real media, and physical R36S. Generated test fixtures, desktop success, and reference-port logs remain supporting evidence rather than hardware pass.
- Reuse existing scripted-input, screenshot, FPS/guest-heap, call-trace, ABI, oracle, and lifter regression tools where applicable. Vendored generic Xbox tests do not certify custom game renderer. Reference Delver measurements establish methodology; Cuphead establishes applicable lifecycle precedent, not SH3 compatibility.
- Test runtime/rendering through matched full-game scenes: indoor flashlight, fog, alpha hair, palette updates, shadows, transparency/reflections, fades, map/inventory, save previews, room transitions, and combat. Use trusted original/desktop captures and independent expected outcomes.
- Test movie natural completion and skip separately, including end-of-media when frames are late, subtitles where applicable, audio synchronization, and return to gameplay. Shared SH2 reports motivate these cases without proving SH3 codec compatibility.
- Test save/load after transitions, exit/cold restart, repeated resolution changes, and write failures while preserving prior valid saves. Test controls as full action matrix on hardware.
- Owner confirmed on 2026-11-13 that correct room/play-time identification satisfies issue #8's save-identification requirement. Tested original Load screen shows fixed artwork and slot metadata. Preserve that metadata and any preview images available elsewhere in original game.
- Profile matched 640×480 and conditional 320×240 scenes with same data, save/camera, settings, and comparable thermal state. Record build/input identities, Internal/Output resolutions, cold/warm cache state, CPU/GPU timings, frame-time tails, memory, and clocks.
- Finish with campaign/ending checklist, all-original-video coverage, and long-session/repeated-transition evidence. First launch, one room, aggregate average FPS, or an unresolved blocker report cannot pass Full port acceptance.
- Documentation-only work uses requirements, link, and workflow consistency validation. Future behavior changes follow actual RED–GREEN–REFACTOR; device prerequisites must pass before dependent implementation claims.

### Capability gates and evidence handoff

| Gate | Work unlocked | Evidence required before dependent claims |
| --- | --- | --- |
| G1: inputs and target | Reproducible native runtime work | Matching executable/data; current firmware/kernel/libc/SDL/driver fingerprint; private config/ignore checks; documented scripted device workflow. |
| G2: reproducible ARM64 runtime | Game-level GLES integration | Docker-built AArch64 artifact, dependency closure, guest-memory/thread/runtime diagnostics. |
| G3: actual GLES operations | Renderer compatibility claims | Current hardware context plus representative generated shaders, textures, depth/stencil, indexed draws, FBO/readback, and required fallback results. |
| G4: representative gameplay | Performance/resolution selection | Correct matched scene captures, game timing/audio, per-thread/frame-time/memory measurements. |
| G5: complete integration | Campaign sign-off | All original movies; physical controls; save/load/restart; launcher failures/exit cleanup; bounded hot-session memory. |
| G6: Full port acceptance | Personal-port completion and later release consideration | Complete campaign/ending and media checklist; agreed stability assessment; tested build/evidence identifiers; no unresolved acceptance failures. |

These gates are work dependencies, not claims of sequential completion or separate final products. Prerequisite-free investigation can proceed; dependent implementation requires actual passing capability evidence. At synthesis time, no SH3 gate above has passed on R36S.

## Out of Scope

- Public PortMaster catalogue submission, release promotion, broad handheld/firmware support, and public binary-distribution policy in first personal-device milestone.
- Switch emulation, running Switch NRO directly, Windows/x86 compatibility stacks, and GL4ES-only port as selected implementation route.
- Silent Hill 2 port, Enhanced Edition packs, HD assets, new story content, or 60 FPS target.
- Firmware/kernel replacement, global GPU/library replacement, overclocking, or changes to unrelated ports as assumed prerequisites.
- Bundling owner Game data, publishing credentials/dumps, or silently changing original media through transcoding.
- Treating prototype/probe success as Full port completion, dropping original FMVs, reducing gameplay speed, or accepting lower performance without explicit revised requirement.

## Further Notes

### Confirmed requirements

Conversation settled personal-device-first scope, Full port completeness, original videos, native Linux ARM64/GLES3 architecture, 30 FPS priority, lowest graphics, preferred 640×480 Internal resolution and 320×240 fallback. User separately confirmed launcher-level test boundary during this synthesis. No implementation, build, device run, or performance guarantee is implied by those decisions.

### Baseline and unresolved facts

Reviewed SH3 baseline: `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`. Upstream reference executable: 3,338,240 bytes; SHA-1 `aa2aca6dba19bf510c9c2e92eefdc15e98266581`. Original data is roughly 5 GB. Initial research found local executable/generated game code unavailable; availability must be rechecked through approved workflow.

Owner input update, 2026-11-12: user supplied original-CD installation with
3,338,240-byte `sh3.exe`, SHA-1 `d851669ef609b3164e3581aa8dcfbfaec866cb79`, and
requested targeting this executable because alternative unavailable. Recognize
exact `owner-cd-d851669e` input profile alongside upstream `upstream-aa2aca6d`.
Local checks passed all nine upstream patch preconditions and PE/import parser;
all 79 required data paths present. This establishes preflight input recognition,
not equivalence to upstream executable or native-runtime compatibility. Generate
native game code from selected profile and retain its hash in build identity;
validate address-specific hooks and generated code during runtime work. Do not
reuse generated code from another profile or accept arbitrary hashes. Preserve
original; patches operate on ignored working copy. See [issue #1 evidence](../../reports/issue-01-preflight.md).

Historical Delver evidence recorded owner's Mali-G31 native GLES3.2 on earlier dArkOS configuration. It does not establish current driver extensions, SH3 runtime compatibility, physical RAM fit, or SH3 frame rate. Original SH3 movie codec/container remains unidentified. Thread/audio races, compressed-texture fallbacks, later campaign recompiler faults, and thermal behavior remain empirical risks. Numeric tolerance for rare transition stalls remains open before final performance sign-off.

Current port folder name, exact build image/sysroot, decoder integration, optional extension fallbacks, and any media conversion are not silently settled by this spec. First packaging/device task documents folder consistently with `R36S_PORT` before deployment. Research commands are inputs to saved scripts, not authorization for direct remote shell execution. New build/device guides are created when first needed under project workflow.

Synthesis ignore check found private configuration, temporary reference clones, port cache, and device dumps not yet covered. Follow-up ignore work added and verified coverage for these paths, private configuration variants, caches and generated build outputs while retaining `.env.example`. User-provided `.env` remains ignored and untracked; contents were not read during publication. Shared research uses portable reference-root locators instead of user-specific absolute paths. These checks alone do not pass G1.

### Canonical context and references

- [Domain glossary](../../GLOSSARY.md) and [accepted native Linux/GLES3 ADR](../adr/0001-native-linux-gles3-r36s.md).
- [Full feasibility report](../../reports/Silent%20Hill%203%20R36S%20feasibility.md).
- [Source/renderer research](../../research_notes/Silent%20Hill%203%20R36S%20feasibility/source_feasibility.md), [working-port patterns](../../research_notes/Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md), and [platform/PortMaster research](../../research_notes/Silent%20Hill%203%20R36S%20feasibility/target_and_portmaster.md).
- [Spec source checks and applicability](../../research_notes/Silent%20Hill%203%20R36S%20spec/source-checks.md), including shared SH2 video-completion precedent and first-hand SH3 palette regression.
- [Issue workflow](../agents/issue-tracker.md), [triage roles](../agents/triage-labels.md), and [domain workflow](../agents/domain.md).

Issue tracker: `ktodorow/sh3-nx-r36s`. Initial read-only check found Issues disabled; user subsequently enabled Issues and authorized publication. All [19 implementation issues](../issues/silent-hill-3-r36s/README.md) from approved [breakdown](../issues/silent-hill-3-r36s-ticket-breakdown.md) were published and verified open and unlabeled on 2026-11-11, with 26 native blocking relationships. No `ready-for-agent` tags or other labels applied. GitHub issues and comments hold current task history; local files preserve approved scope. No separate parent issue created or closed. Implementation issues remain open until their own acceptance passes; documentation publication does not establish Full port acceptance.
