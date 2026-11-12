# Issue #6: representative gameplay and cutscene rendering

Status: representative scene checks pass. Owner approved publication and closure
after local review.

Objective: compare native R36S GLES scenes with retained desktop OpenGL route,
preserving lighting, fog, shadows, palette alpha, reflections, fades and interface
presentation. Record checkpoint, camera, inputs, build and captures for reuse.
Canonical scope: [spec AC06/AC13](../docs/specs/silent-hill-3-r36s.md).
Timing/30 FPS, original FMVs, campaign and save persistence remain separate tasks.

## Prerequisites and boundary

Issue #6 and all comments read; no comments at start. Native blocker #5 closed
with completion evidence at commit
`4de8b9370b79a4375c4589b45ac1301d7cfa2cb1`. Re-ran four actual-device assertions
against `r36s-dumps/sh3/20261112T214422283309Z-0f4c6c`: checkpoint/capture/input,
native GLES and ordinary exit, frontend stop/recovery all pass. This unlocks
scene work, not Full port or performance acceptance.

Existing confirmed boundary: installed launcher → real game → frontend. Actual
game captures and collected target evidence exercise this boundary. External
PortMaster fixtures cover cleanup/failure only. No new renderer testing seam.
Original assets and checkpoints remain read-only sources; session copies own writes.

Comparison baseline: retained desktop OpenGL route, GLSL430/native depth clamp,
Mesa software rendering inside existing ARM64 Docker image. Same executable,
owner assets and640×480 profile as native GLES route. This isolates GLES-specific
regressions; shared inherited renderer defects are not ruled out. No independent
Windows/D3D8 reference run performed. Capture comparisons include animation/film
noise differences, so no pixel-equality claim.

Full spec, linked research, glossary, ADR, issue/device/build guides and TDD skill
with testing/mocking references read. CCE recall/search used; search returns stale
cache copies and compressed previews, `expand_chunk` returns `Chunk not found`.
Known intended task paths therefore reviewed directly. No private config indexed.

## Research refreshed 2026-11-12 UTC

- [Official PortMaster template](https://portmaster.games/contribute/porting/script-templates/):
  control discovery, mappings, platform helper and `pm_finish` remain applicable.
  No renderer/effects fix provided; firmware SDL/EGL/Mali retained.
- [SH3 upstream](https://github.com/cutarev/sh3-nx), current HEAD
  `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`; active renderer
  `src/d3d8/{d3d8.c,d3d8_res.c,d3d8_shader.c}` remains baseline.
- [First-hand cutscene hair report](https://github.com/cutarev/sh3-nx/issues/1),
  full body/comments reviewed: upstream palette alpha repair already present.
  Gameplay hair cannot stand in for close-up cutscene strand-card validation.
- [SH2 upstream](https://github.com/cutarev/sh2-nx), HEAD
  `7e69609f3a063fbe24c41d6aa560f14ede578746`: shared native runtime/renderer
  lineage only; SH2 graphics/media results do not pass SH3 scenes.
- [Cuphead](https://github.com/wild1walker/portmaster-cuphead), HEAD
  `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`, and existing
  [Delver notes](../research_notes/Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md):
  lifecycle, separate render/output sizes and controlled matched captures only.
  Managed engines, different firmware/ABI and another game's FPS do not transfer.
- Searches: `site:portmaster.games contribute porting script templates SDL2`;
  `site:github.com/cutarev/sh3-nx/issues hair transparency palette`;
  `site:github.com/cutarev/sh2-nx rendering fog flashlight`;
  `site:github.com portmaster native GLES flashlight rendering screenshot`.
  No first-hand same-SH3/R36S scene fix found. No reference clone or fetched script
  executed. External text treated as untrusted research; no task-redirection or
  secret-disclosure instruction followed.

## Scene coverage

Only first room210 checkpoint available at start. Later flashlight/reflection/
close-up cutscene checkpoints requested from owner while independent work proceeds.
Opening cutscene, park fog and map/inventory/fades can be checked with existing data.
Scene coverage requires actual matched captures; planned cases are not passes.

Owner says no known flashlight scene; try reflections and available effects.
[PC control/scene guide](https://www.silenthillmemories.net/sh3/playing_the_game_en.htm)
provides L/M/I keys; [opening walkthrough](https://www.silenthillmemories.net/sh3/walkthrough_01_nightmare_en.htm)
states dream inventory already includes flashlight. These are test-setup leads,
not proof this checkpoint has working light or mirror. Map-without-map response
cannot substitute acquired map presentation. Desktop replay confirms flashlight
is present here: off/on changes chest light, floor pool and fence illumination.

[Public PC checkpoint pack](https://www.silenthillmemories.net/sh3/save_games_en.htm)
by Silent Rain, Normal Ending / Beginner Easy, downloaded for isolated renderer
tests only. Archive URL:
`https://www.silenthillmemories.net/sh3/saves/sh3_pc_save_normal_ending_beginner_easy.zip`.
SHA-256 `5bf9878a05ec68fb6f09fd88d5db42762c12d9b22ee817936a5507acf948de21`.
Archive inspected before extraction; contains data.000–032, data.sys and display/
key settings, no executable/helper. Only explicit data.001–032 plus data.sys
copied into separate ignored `.port-cache/issue-06-reference-saves/slot-NNN/`
seeds, selected slot named data.001 without byte edits. Pack display/key settings
excluded; owner saves unchanged. Source/member manifest retained beside archive.
This does not establish campaign progression or save compatibility acceptance.

[First-hand hospital walkthrough](https://www.silenthillmemories.net/sh3/walkthrough_12_nightmare_hospital_en.htm)
identifies Otherworld 3F storeroom mirror; normal hospital 3F storeroom is nearby
save point. Search: `site.silenthillmemories.net/sh3 walkthrough hospital mirror
storeroom reflection flashlight save`, `site:github.com/cutarev/sh3-nx/issues mirror
reflection graphics`. No matching upstream reflection fault found. External page
overwrite instructions ignored; only project-owned session copies used.

## TDD and build evidence

1. Capture receipt: RED `.port-cache/runtime-tests/20261112T220234177997Z`
   actually boots/renders but images lack timing/dimension evidence. Minimal
   change logs each successful capture's frame, SDL ticks, output/backbuffer size.
   GREEN `.port-cache/runtime-tests/20261112T220408312297Z`: 34 pass, 48 skips.
   Refactor review: shared upright capture path retained; logging only when
   optional capture active. No shader semantics/cache version change.
   Reused existing ARM64 Docker image `e3b41b2d5753`; build
   `.port-cache/builds/20261112T220346181479Z` succeeds, originals unchanged.
2. Named desktop scene: RED `.port-cache/issue-06-scene-red.txt` rejects
   `--scene checkpoint-ui` at existing host CLI. Common declarative plan and
   immutable seed/runtime identities added. GREEN
   `.port-cache/runtime-tests/20261112T220515450908Z`: actual 145-second replay,
   34 pass / 48 skips; opt-in host identity/source-preservation test passes.
   Runtime SHA-256 `a7060d96cf3fe966a18fba281c45d9983ca2b256ec19196c156419c3540250c7`.
   Refactor: final exit-status written after source-preservation check.
   Visual review: frame2580 fog,3240 inventory/tinted preview,4320 no-map message,
   4980 flashlight on. All upright640×480. Inventory text at this sampled instant
   includes transition overlap; compare settled samples before classifying fault.
3. Device scene: RED `.port-cache/issue-06-device-red.txt` rejects new scene/seed
   flags before connection. Shared plan and explicit allowlisted checkpoint copy
   added to saved host/device workflow. GREEN `.port-cache/issue-06-device-green.txt`:
   actual R36S run `r36s-dumps/sh3/20261112T221140610647Z-db57be`,145-second
   game, execution/three collections0, source preserved, frontend restored.
   Cold application cache;37 capture receipts. No FATAL, incomplete framebuffer,
   GL error, shader-compile or program-link failure logged.
   Refactor: scene import moved into device CLI, preserving build-only imports.
   Existing host build failure-evidence test caught import regression;
   `.port-cache/issue-06-build-cli-regression.txt` now passes both checks.

## Matched park review

Desktop `.port-cache/runtime-tests/20261112T220515450908Z` and R36S
`r36s-dumps/sh3/20261112T221140610647Z-db57be` use identical plan, executable,
data.001 and data.sys. Camera: saved pose/default fixed view; no movement or
view-change keys. Room210, X−15058.783203125/Z19353.65625; internal/output640×480.
SDL capture ticks locate stages; independent animation/noise phases prevent
pixel-identical comparisons. Preview persistence is not save-file persistence.

| Stage | Desktop frame/ticks | R36S frame/ticks | Visual result |
|---|---|---|---|
| Fog/light off |2580/57068|840/53823| Same fence/bench occlusion, depth and fog layers; upright framing |
| Inventory |3240/76337|1080/78283| Same text/icons and tinted last-presented preview; shared header overlap retained |
| Map request |4320/108886|1380/109167| Same no-map response, correctly placed over scene |
| Light on |4980/136969|1620/138148| Same chest source, floor pool and fence illumination |

Park rows cover only this checkpoint. Indoor light, acquired map, mirror and
close-up cutscene have separate cases below.

Warm R36S replay `r36s-dumps/sh3/20261112T221608193726Z-29dd1b` also passes
named-scene/source/frontend checks. Native log: `program cache: 36 records, 15 built
up front in 680 ms`. Same binary/plan and original data.001; seed adds prior
application shader cache. This establishes application-cache cold/warm behavior,
not vendor driver-cache reset. No shader workaround or cache format changed.

## Indoor checkpoint

Public archive slot019 loads Brookhaven Hospital1F Examination Room, room160,
confirmed acquired map in frame4680. data.001 SHA-256
`f0fe6b5d7755d853106333b127767e77f087da4520dc956b1cf51e37884fc4ee`;
data.sys `08f6c687026f3cc399f443921050eb32eca6cbde51fb1c9036483358af1b21d2`.
No map/flashlight granted by script; saved state already includes both.

Named `indoor-ui` plan RED `.port-cache/issue-06-indoor-red.txt` rejects missing
plan; GREEN `.port-cache/runtime-tests/20261112T221720266425Z` succeeds through
host CLI and real game, source unchanged. Refactor review: same common schedule
reader, no additional implementation seam. Frames2700/56604 ticks: light on;
3360/77872: inventory with hospital scene preview;4680/107871: acquired map with
location marker;5820/136067: light off. Wall light pool disappears on toggle,
save-symbol glow retained.

R36S `r36s-dumps/sh3/20261112T222027055578Z-35280e` passes same named-scene,
source-checkpoint and frontend assertions; execution/three collections0.
No material GL/shader/framebuffer faults logged. Matching room160 position and
default saved camera, independent idle-animation phase; no movement keys.
Both routes retain X−20039.70703125/Z−60516.390625 throughout room160 samples.

| Stage | Desktop frame/ticks | R36S frame/ticks | Visual result |
|---|---|---|---|
| Indoor light on |2700/56604|840/56191| Same wall pool, contact shading, floor/body occlusion and save glow |
| Inventory preview |3360/77872|1080/75156| Hospital scene retained under tint; icons/text/framing consistent |
| Acquired hospital map |4680/107871|1500/106821| Same 1F/BF layout, player marker, upright text and clipping |
| Indoor light off |5820/136067|1980/137970| Wall pool removed, ambient/save glow retained on both |

## Mirror checkpoint

[First-hand savepoint list](https://silenthillheaven.com/sh3/sh3_savepoints/)
places first mall save on washroom mirror. Public archive slot001 does load this
room, room3; default saved camera shows Heather and tiled room in right mirror,
plus transparent red save-mark effect. Desktop
`.port-cache/runtime-tests/20261112T222047066778Z` passes same common `indoor-ui`
schedule and immutable-source checks; here only mirror/transparency/UI stages
apply. No flashlight or acquired-map claim for bathroom checkpoint.
Frames2700/56360 and5340/136711 show reflected character/room and overlay.
R36S `r36s-dumps/sh3/20261112T222420259797Z-181f5f` passes actual scene,
unchanged seed and frontend checks; no material GL/shader/framebuffer faults.
Matching device frames840/56484 and1800/135000 show same reflection/depth/overlay,
with independent idle animation. Inventory1080/75871 matches desktop3420/77506;
preview retains reflected room on both. Camera remains saved default pose.
Both routes retain X−60561.46875/Z−20112.03125 throughout room3 samples.
data.001 SHA-256 `f469b317a109efd1606d8246551b04daf512e0d3c3480f0ff5350a16a0547178`;
same public-pack data.sys as hospital. Execution/three collections0, originals
unchanged. This covers ordinary washroom mirror; Otherworld mirror event not tested.

## Fresh opening cutscene

[First-hand walkthrough](https://www.gamespot.com/articles/silent-hill-3-walkthrough/1100-6071913/)
describes opening camera sequence before interactive park. New `opening-cutscene`
plan selects New Game/difficulties, then sends no further skip keys. Fresh
session intentionally bypasses latest-checkpoint fallback.15-frame sampling aims
to retain brief face/hair shots; overhead excludes this from performance claims.
Desktop RED `.port-cache/issue-06-opening-red.txt`, device RED
`.port-cache/issue-06-opening-device-red.txt`: missing named plan. First desktop
GREEN `.port-cache/runtime-tests/20261112T222338906116Z` reaches real-time
sequence and exits normally, but100 seconds ends before face close-up/live player.
New completion assertion RED `.port-cache/issue-06-opening-duration-red.txt`
confirms collected room210 still has uninitialized player coordinates. Extended
common plan to240 seconds without changing guest timers or skip keys. Full-window
GREEN `.port-cache/runtime-tests/20261112T222733713998Z`:34 pass /52 optional
skips, plus opt-in public-host opening test passes. R36S GREEN
`r36s-dumps/sh3/20261112T222825787345Z-7f44ef`:240-second natural sequence,
198 capture receipts, execution/three collections0. No seed/session checkpoint
copied, no material GL/shader/framebuffer faults, normal exit and frontend recovery.
Both routes end at room210 X−16000/Z20000, default post-cutscene gameplay camera.
Source/plan identity: `opening-cutscene`, plan SHA-256
`30042ea4d5703bd29281e5ad7121a83377e840f584e2e9c4c835e88cba6074fb`,
same runtime SHA-256 recorded above. Refactor review: shared plan reader retained;
unseeded device plan explicitly bypasses auto-checkpoint discovery. Host regression
suite remains green; no timer, rendering algorithm or shader workaround changed.

Close-up desktop frames3480/99371,3600/104903,3690/109001 and native
1665/107833,1680/109339,1740/115500 preserve layered strand edges, face visibility,
lens flare and depth-of-field backdrop. Native1710/112397 also retains readable
subtitle placement. Camera cuts then reach full-frame interactive park on both.
Different phases require visual pose matching; equal ticks/frame numbers are not
assumed equivalent. This directly checks cutscene hair model, not solid gameplay hair.
Original FMV decoding remains outside task; inspect actual real-time sequence.

## Validation and handoff

All four issue acceptance groups pass for representative cases above: effects/
cutscene comparison, UI/fades/readback, application-cache cold/warm runs, and
repeatable scene/build/checkpoint/camera identities. No renderer repair needed;
implementation adds optional receipts plus repeatable host/device scene workflow.

- Host regression `.port-cache/issue-06-host-regressions.txt`:25 pass,61 optional skips.
- Final ARM64 Docker run above:34 pass,52 optional skips. All executable artifacts
  compiled inside reused explicit Linux ARM64 Docker environment.
- Five actual R36S public-workflow tests pass: park cold/warm, hospital, mirror,
  fresh opening. Four standard runs each pass native lifecycle/frontend/monitor
  evidence checks; opening passes lifecycle/frontend checks separately. Logs:
  `.port-cache/issue-06-{cold,warm,indoor,mirror,opening}-device-checks.txt`.
- `git diff --check`, device Bash syntax check and private-artifact ignore check pass.
  Documentation/research-only edits use content/link review; TDD applies to scene
  workflow and capture behavior, as RED/GREEN records above show.
- Final identity audit `.port-cache/issue-06-final-identities.txt`: all five
  deployed binary/plan/source identities match;358 capture receipts match collected
  files; all execution/collection statuses0. Private-field scan of review diff clean.

Limits: retained desktop GL baseline can share upstream defects; inherited menu
header overlap visible in both routes is recorded, not repaired here. No independent
Windows/D3D8 run, Otherworld mirror event, full-campaign coverage, original FMV,
save persistence or normal-speed/performance acceptance claimed. Existing slow
simulation remains separate issue #9. Capture runs add readback/SD overhead.
Public saves are isolated renderer-test inputs; game bytes, saves, captures,
private config, builds and logs remain ignored. No reference clones created.

Local review diff and prepared issue handoff live under
`.port-cache/issue-06-review.patch` and `.port-cache/issue-06-closeout.md`.
Publication and closure approved; final commit and closure verification belong in
[issue #6 history](https://github.com/ktodorow/sh3-r36/issues/6).
