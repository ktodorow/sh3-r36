# Issue #13: measured performance optimization

Status: reviewed 320×240/30 FPS candidate passes sampled live gameplay in mall,
park, church, hospital and repeated handgun combat. Lowest complete gameplay
second 28 FPS; park door-loading second 25 FPS. Final-binary 15-minute hospital
run passes 29.8946 FPS/minimum 28 with no logged audio underrun. First-visit shader
stalls and audio recoveries remain explicit limits. Owner approved publication
on 2026-11-14 and closure of #9 only; issues #13/#14 stay open. Historical baseline
follows.

## Latest measured candidate, 2026-11-14

Runtime SHA256 `2ac6b9c02579ff37d20a920edde36a203458aeded0806f9e86ffecf4bc512ff9`.
Actual R36S completed presentations,320internal/640output,30FPS limit; no images.
Automatic movement uses ordinary game inputs and isolated public checkpoints.

| Scene/window | Average FPS | Minimum complete1s /5s | Evidence run |
| --- | ---: | ---: | --- |
| Hospital160,50–975s,15-minute run |29.894589|28 /29.2|`20261114T053122812199Z-42e95c`|
| Hospital160,48–160s |29.972849|28 /29.6|`20261114T051236207262Z-4ed67b`|
| Mall18,48–160s |29.989908|29 /29.8|`20261114T051822455921Z-bab6a5`|
| Park211,65–130s before death |29.969692|29 /29.8|`20261114T045502889545Z-c7967c`|
| Church240,48–160s |29.975259|29 /29.8|`20261114T052509963498Z-f9bc5c`|
| Handgun210,75–180s |29.990378|29 /29.8|`20261114T050230071532Z-0ddc92`|

Completed-frame intervals, same windows and artifact:

| Scene | p50 ms | p95 ms | p99 ms | Maximum ms |
| --- | ---: | ---: | ---: | ---: |
| Hospital160,15-minute run |33.363|34.804|36.680|53.745|
| Hospital160 |33.356|34.728|35.768|51.475|
| Mall18 |33.347|34.390|35.210|48.560|
| Park211 before death |33.338|34.063|35.135|79.206|
| Church240 |33.369|34.837|35.933|49.497|
| Handgun210 |33.326|34.226|35.315|60.180|

Each interval includes alive character and changing positions; handgun ammunition
depletes and reloads. Full logs retain loading/death/reset frames. Park door
194.551ms frame gives25FPS in59s window. Full park run includes death/reset,
new-game rooms and9 first-visit shader misses:1.231s stall/minimum1FPS bin.
Broad first-visit/all-transition floor is not declared passed. Park has one live
ALSA recovery; other four final short runs contain none. No new physical listening
claim. Game clocks remain near wall time, CPU/GPU samples1512/520MHz.

Explicit **Silent Hill 3 Performance** menu preserves player progress and selects
tested30/320 profile plus exact measured shadow/flare1/1. These numeric options
are not certified universal lowest quality. Church replay starts from isolated
0/0 copy and proves installed menu writes1/1; source copy stays0/0. Brightness,
format, mappings and progress preservation also pass24 launcher regressions.
Same-device measured program cache primes missing player cache, with hash audit
and no save/config import. Final15-minute hospital interval includes461alive
observations,321positions and motion in every sampled30s segment; health stays
199.399994. Game clock0.999545×wall,191CPU/GPU samples1512/520MHz, maximum73.333°C.
51program binary restores,zero misses/writes/rejections; no logged ALSA recovery.
Resident peak313524KiB,minimum system MemAvailable558700KiB; latter-half RSS
312216→313524KiB over8m10s. This is sampled process/system memory, not complete
GPU allocation accounting or full-campaign memory acceptance. Available swap
falls485020→484852KiB (168KiB consumed). Prior f972 timer
artifact's15-minute run033440 remains historical with two ALSA recoveries.

Current 640 comparison uses the same final executable, room210 seed, measured
shadow/flare1/1, 30FPS limiter and 180s equip/fire/movement schedule. All five seed
inputs match the original320 benchmark byte for byte. Both windows are75–180s:

| Internal resolution /640×480 output | Average FPS | Minimum complete1s /5s | Evidence run |
| --- | ---: | ---: | --- |
| 320×240, retained profile |29.990378|29 /29.8|`20261114T050230071532Z-0ddc92`|
| 640×480, rejected profile |23.196638|19 /19.8|`20261114T055246314042Z-4068d8`|

640 frame p50/p95/p99/max42.656/51.373/53.331/82.274ms. All41 observations are
alive,40 positions, actual ammunition depletion/reload; game clock1.000329×wall.
All36 CPU/GPU samples1512/520MHz, maximum75°C versus320 run71.25°C; temperature
variation remains a comparison limit.47 binary restores, zero misses/writes/
rejections and no logged ALSA recovery. All lifecycle/source/firmware checks pass.
This result fails owner's25FPS floor and supports conditional320 fallback; it
does not establish an immutable640 hardware ceiling. See
[renderer report](issue-14-renderer-caches.md) and
[route evidence notes](../research_notes/Silent%20Hill%203%20optimization%20roadmap/unattended_routes.md).

Current regression evidence: full Linux ARM64 runtime
`.port-cache/runtime-tests/20261114T044911627584Z`,174tests/60PASS/114explicitSKIP;
actual Mali GLES `20261114T045123906063Z-4d0905`,27graphics checksPASS/one optional
deployment-trigger rerunSKIP. Actual native deployment already completed through
saved host workflow; this skip does not denote missing graphics hardware.
Latest launcher settings suite24PASS/6.491s at
`.port-cache/optimization-uniforms/performance-settings-regressions`.
Latest real-game movement/collision/fire suite3PASS/480.823s at
`.port-cache/movement-tests/20261114T032945909488Z`, with timer changes intact;
ordered deletion is subsequent renderer-only change. Calibrated32ms stress old
binary holds20FPS, current timer passes twice at28–29FPS. Full RED/GREEN/design
reviews and artifact lineage in linked route/renderer notes. No skip or software
fixture establishes physical listening or untested campaign acceptance.
Saved-host regression after current640 scene addition:10PASS/5.928s at
`.port-cache/optimization-uniforms/final-640-route-regressions.txt`.
Local review diff covers task-owned source, tests, scripts and reports:
`.port-cache/optimization-uniforms/final-local-review.diff`; file manifest and
final measurements in adjacent `final-review-files.json` and
`final-profile-evidence.json`. Review snapshot predates publication approval;
raw game data, caches, dumps and build artifacts remain ignored and unpublished.

## Scope and acceptance

Owner requested optimization after both handheld profiles remained slow in heavy
scenes. Existing #13 covers profiling and #14 covers verified profile selection;
no dedicated bottleneck-fix issue exists. Fixes start only after identifying cost
in a reproducible scene. Target is 33.33 ms/frame (30 FPS), preserving required
visuals, gameplay timing and audio. This first local slice does not establish
full-route stability or a rare-stall allowance.

Canonical requirements: `docs/specs/silent-hill-3-r36s.md` AC06/07/08/12/13.
Selected tickets #13/#14, #13 blockers #6/#9, complete comments and linked
research reviewed. #6 actual rendering evidence passes; #9 actual timing/audio
evidence passes locally, publication pending. Tracker state alone is not treated
as a capability pass.

Agreed test boundary remains installed launcher → real game → frontend return.
Implementation uses RED–GREEN–REFACTOR; documentation uses source/link/diff
validation instead. Device results remain necessary; Docker cannot establish R36S
performance. No handheld exit retest requested.

## Method

Fixed room210 checkpoint, isolated writable session, original seed and owner
assets unchanged. Scripted warning/Play/Load keys, fixed initial camera, no
framebuffer capture during measurements. Output remains 640×480. Match build,
seed/config/cache identity, scene window, clocks and thermals for comparisons.
Room210 is an automated heavy reproduction; room14 from prior listening sessions
has not been mapped to owner's exact monster room.

Opt-in `SH3_PROFILE` CSV records each presented frame's wall time, main render
thread CPU time, CPU-side draw submission duration, presentation duration and
swap duration. Swap is included in presentation; draw duration includes upload,
state/shader setup and draw calls. These are CPU-side elapsed observations, not
GPU execution timings. No `glFinish`, pixel capture or forced GPU synchronization
is added. Buffer upload bytes exclude texture transfers. Normal play disables
profiling. Existing five-second process/clock/thermal sampler supplements CSV.

## Research and applicability

Consulted 2026-11-13 before selecting measurement approach:

- [Official PortMaster FNA guide](https://portmaster.games/contribute/porting/engines/fna/):
  search surfaced optimization/draw batching guidance; full page unavailable in
  browser fetch. Different FNA/Mono runtime, so no implementation copied.
- [Arm: checking pipeline](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-1-checking-the-pipeline)
  and [Mali optimization guide](https://developer.arm.com/-/media/Files/pdf/graphics-and-multimedia/Guides/DUI0555C_mali_optimization_guide.pdf):
  distinguish game CPU, driver submission, GPU work and synchronization before
  tuning. Resolution comparison alone cannot identify bottleneck.
- [Upstream sh3-nx](https://github.com/cutarev/sh3-nx) and
  [sh2-nx](https://github.com/cutarev/sh2-nx): shader caching/render-target patterns
  require Linux GLES/firmware checks; Switch results do not establish R36S speed.
- [Cuphead technical notes, commit 1b7e7b019dabeb4226a1b4be5bfdd854895242f5](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/docs/technical.md):
  launcher/measurement reference only; runtime and ABI differ. Current page fetch
  exposed metadata, not complete document; existing spec-linked research retained.
- [First-hand SH3 low-FPS discussion](https://github.com/ThirteenAG/WidescreenFixesPack/issues/285):
  fog/scene-dependent drops and slow motion reported on Windows. Different native
  renderer/runtime; no fix assumed applicable from that report.

No temporary reference clone created or external script executed. CCE retrieval
continues returning stale ignored cache copies instead of requested source
functions; known current source paths reviewed directly after attempted scoped
search. Earlier expansion/reindex failures documented in issue #9 report.

## Evidence

- Diagnostic RED: `.port-cache/issue-13/20261113T170430730152Z-profile-test`.
  Real checkpoint loads, deadline exits cleanly, frontend cleanup passes, no
  capture; requested per-frame report absent on prior binary. Correct failure.
- Initial profiling build: `.port-cache/builds/20261113T170617599577Z`, status0,
  reusable pinned Linux ARM64 Docker environment. Native acceptance recorded
  below for final candidate.
- Diagnostic GREEN: `.port-cache/issue-13/20261113T170635389705Z-profile-test`,
  62-second real checkpoint; warmed room210 frame-cost invariants pass, no capture,
  clean launcher/frontend return. Design review keeps timings in separate module,
  opt-in, buffered and without forced GPU synchronization.
- Detached-service report forwarding, saved scene report retention and physical
  mode suppression each observed failing before minimal implementation. All12
  frontend tests pass in Linux ARM64 Docker, 2.438 seconds. Existing timing test
  refactored into shared saved-device fixture, rerun green before new slice.

## Initial matched device baseline

Same runtime `fb196c2853538994324b35157959714750a7b44da960dbe42d1ff8a6d716d68a`,
seed, room210, position and input; stationary55–95s window, no capture.
Empty original disp.ini means diagnostic defaults: shadow1, lensflare_ztest1,
A8R8G8B8, gamma1. This is a controlled baseline, **not lowest-profile acceptance**.
Isolated alternate-preference seed prepared separately from same checkpoint plus
owner's existing shadow0/lensflare_ztest0 preferences. No original data changed;
preparing experimental input is research, not executable implementation. Numeric
shadow values have not yet been mapped to all in-game quality labels; this seed
is not evidence of the lowest supported configuration.

| Frame metric | 640×480 | 320×240 |
| --- | ---: | ---: |
| Frames | 379 | 469 |
| Mean-derived FPS | 9.48 | 11.73 |
| Wall p50/p95/p99/max ms | 105.621/108.904/115.006/117.387 | 84.444/89.616/94.048/102.764 |
| Main-thread CPU p50 ms | 70.493 | 70.664 |
| Draw submission p50 ms | 25.136 | 25.207 |
| Presentation p50 ms | 27.076 | 9.516 |
| Swap subset p50 ms | 26.151 | 8.452 |
| Draw count p50 | 372 | 372 |
| Vertex/index upload bytes/frame | 140124 | 140124 |

640 evidence `r36s-dumps/sh3/20261113T171038078066Z-5ab24a`;
320 evidence `r36s-dumps/sh3/20261113T171358573596Z-5dca09`.
Both execution/collection0, source preserved, frontend active afterward.
Raw CSV, computed `frame-summary.json`, scene/build/seed identities and five-second
samples retained. CPU1512MHz, GPU520MHz, DMC786MHz throughout both runs; observed
thermal values do not coincide with a clock drop. GPU load is supporting coarse
telemetry, not per-frame GPU execution duration. No memory-pressure conclusion
from virtual address size.

Ranked next hypotheses: game/runtime CPU work outside draw calls (~45ms of main
thread budget), renderer submission (~25ms), then GPU/presentation waits (larger
at640). Resolution lowers waits but leaves CPU cost unchanged. Need CPU samples
to select precise function; do not guess an engine rewrite from these totals.

CPU sampling research: actual inventory
`r36s-dumps/sh3/20261113T171737188064Z-b0588c` records `perf` absent and
`perf_event_paranoid=1`. No installation or permission change. Profiler capability
probe added with observed RED then GREEN; all13 frontend tests pass (2.649s).
[PortMaster Unity profiling notes](https://github.com/Producdevity/portmaster-unity-toolkit/blob/main/docs/profiling.md)
and [PM-Porting-Tools](https://github.com/Knifethrower/PM-Porting-Tools) describe
signal-based sampling on handhelds. Different runtime; no code copied or helper
executed. [Linux timer_create documentation](https://man7.org/linux/man-pages/man2/timer_create.2.html)
confirms thread CPU clocks and targeted delivery supported before target4.4
kernel. Local diagnostic will sample only presenting thread CPU, defer
symbolization/writes until exit, and preserve normal-play disabled behavior.

Sampling RED `.port-cache/issue-13/20261113T172020787566Z-profile-test`:
real scene/cost CSV pass, CPU sample report missing as expected. GREEN
`.port-cache/issue-13/20261113T172259663148Z-profile-test`:62.256s real launcher
checkpoint, named native PC samples and frame-cost invariants pass, clean return.
Build `.port-cache/builds/20261113T172218036298Z` status0, no compiler warnings.
Design review: dedicated Linux AArch64 module, presenting-thread CPU timer,
bounded signal-safe storage, no allocation/locks/I/O or symbolization in handler;
buffer/report work only on opt-in path. Samples join to per-frame CSV; native
offsets require exact build's debug symbols. Actual hardware sampling still
requires next run and overhead comparison against initial baseline.


## Native CPU samples and measurement overhead

R36S `20261113T172439702630Z-3e2e85` passes targeted CPU timer:6916 samples,
zero drops, normal exit/collection, source unchanged. Warm55–95s:2631 samples;
997 native game/runtime,730 firmware Mali,683 libc,201 SDL. Native top leaf:
`recomp_fp_round24`161 samples; matrix routine `sub_00648639`50, then
`sub_004464E0`43. Counts describe statistical CPU observations, not exact time
or GPU execution. Native offsets resolved using matching host-only debug symbols
in ARM64 Docker; mapping retained as run-owned `cpu-symbols.json`.

Opt-in sampler comparison remains ~70.7ms main-thread CPU (previous70.5ms).
Wall~107.7ms versus105.6ms includes variable swap wait; no claim of zero profiling
overhead. Link register added to distinguish library work from calling native
code; it is a return location, not a stack unwinder. Caller-field RED:
`.port-cache/issue-13/20261113T173232958966Z-profile-test`; GREEN:
`.port-cache/issue-13/20261113T173448895732Z-profile-test`, both real checkpoint
62-second runs. Build `.port-cache/builds/20261113T173413278880Z` status0.
Design review: handler still writes only bounded memory; naming remains outside
signal context.

Code review found automated-input overhead: every keyboard poll loops SDL's
keyboard array, reparsing all scheduled events and resolving names for each
scancode. This affects automated timings; physical runs with `SH3_KEYS` unset do
not take that path. Correct measurement first, then compare actual renderer fix
against corrected baseline. No prior physical FPS estimate is changed by this
finding.

Alternate shadow0/lensflare_ztest0 run `20261113T173155332148Z-10ca52` is9.14FPS,
wall p50 108.856ms, main CPU79.139ms, draw28.808ms,382draws, with unchanged
checkpoint/assets. No win demonstrated, and quality-value mapping remains
unverified. Keep original controlled settings for code comparisons.

Additional research: current upstream sh3-nx README confirms shader caching,
but no directly applicable sampler-call fix. R36S scripted-scancode performance
search found no same-problem first-hand report; ONScripter R36S source result
concerns event logging, not this decoder. Khronos OpenGL4.3 sampler-object spec
section8.2 describes persistent sampler parameters; GLES reference page fetch
failed unsupported XHTML. Official PortMaster FNA page remains unavailable.
These are applicability limits, not evidence that another game's fix passes.


## First fixes: automated input and sampler state

Input RED `.port-cache/issue-13/20261113T173629996714Z-profile-test`: real game
loads and profiles successfully, external SDL observer counts7,073,076 name
lookups over2,763 keyboard polls, violating <=16 lookups/poll budget for5 events.
Minimal fix decodes event list once per poll and writes active DIK bytes directly,
retaining default/explicit holds, overlaps, bounds, unknown-key handling and
physical input path. No persistent parser cache or artificial clock change.
GREEN `.port-cache/issue-13/20261113T173846428220Z-profile-test`:13,775 lookups /
2,755 polls, room210 and all frame/sample invariants pass, exit/frontend clean.
Build `.port-cache/builds/20261113T173749169813Z` status0. Refactor review keeps
one poll-sized pass; no further structural change needed. This improves diagnostic
input overhead, not physical game input speed.

Sampler RED via installed graphics launcher in ARM64 Docker: real Mesa pixels,
all existing native diagnostics pass, external SDL/GL observer sees3,648 sampler
parameter calls across76 draws (48/draw), failing <=8/draw budget. Counter only
forwards real boundary calls; no mocked GL result or forced synchronization.
Fix caches seven raw sampler inputs per stage; initializes first use and reapplies
all parameters on any relevant change. Still binds sampler each draw, preserving
binding ownership. Uniforms, draw order, shaders, fog, alpha, shadows and guest
floating-point rounding unchanged. Existing six sampler pixel oracles exercise
wrap/mirror/edge/border and filter changes; full graphics regression still required.

R36S caller capture `20261113T173631211369Z-c0cf58`:9.37FPS, main CPU70.82ms,
zero sample drops. Native external-return locations include shader setup37,
render-state setup17 and input decoder15 of107 directly resolved return samples.
Link registers do not unwind library-internal calls; these counts cannot attribute
all driver/libc CPU cost. Mapping stored `cpu-callers.json` with matching build's
debug symbols.


## Renderer GREEN and second slice

Sampler GREEN `.port-cache/runtime-tests/20261113T174225401939Z`:138 parameter
calls across same76 draws (96.2% fewer); every existing independent pixel oracle
passes. Runtime suite111 tests,28 pass /83 explicitly unavailable skips.
Sampler-only R36S `20261113T174327580891Z-54926b`:12.646FPS, draw p50 17.516ms,
main CPU43.090ms; corrected baseline with same input fix and no renderer cache
`20261113T174000195680Z-4b5840`:11.719FPS, draw25.446ms, CPU51.981ms.
Both same fixed scene/settings, no screenshots, zero status/collection failures.
This is real renderer benefit; earlier9.4→11.7FPS improvement is removal of test
input overhead and cannot be claimed as physical-play speedup.

Second renderer RED: real graphics launcher and external GL observer count1,393
array enable/disable calls for76 draws, violating <=4/draw budget while all pixel
checks pass. Source unconditionally disabled16 arrays then enabled layout for
every draw. Minimal fix tracks enabled-bit mask in device-owned VAO; pointer,
stride/type, streams, base vertex and shader-present metadata unchanged. Only
changed bits issue enable/disable calls. New VAO initially disables all arrays,
per [OpenGL ES3.2 table21.3](https://registry.khronos.org/OpenGL/specs/es/3.2/es_spec_3.2.pdf).
Source review confirms one private VAO, no other enable/disable writers and no
VAO replacement on reset; cache lives with device rather than global unrelated
state. No new OpenGL capability or driver/library replacement.

Build `.port-cache/builds/20261113T174635538228Z` status0. GREEN runtime suite
`.port-cache/runtime-tests/20261113T174719601668Z`:112 tests,29 pass /83 explicit
skips; full desktop pixel/layout/depth/stencil/palette/copy/sampler checks pass.
Refactor removes duplicated GL-observer launch setup in tests only; both affected
checks rerun GREEN at `.port-cache/issue-13/graphics-refactor-20261113T1748Z`.
Same76 draws,138 sampler updates,18 attribute state changes (98.7% fewer).
Final device renderer, movement and profile results follow. Docker checks alone
do not establish Mali compatibility or30FPS.

## Historical first-slice measured result

Final native binary SHA-256:
`4120ea8e35da17de1be0acbfa5453e59cb4d6a6aa833d53f7d6e8ff2de9903d0`.
Build `.port-cache/builds/20261113T174635538228Z` exits0 without compiler warnings;
deployed binary and host-only debug symbols match retained build artifacts.

Same room210 seed, fixed camera, original diagnostic display defaults and55–95s
window. Output remains640×480. FPS is1000 / mean wall milliseconds; p50 is median,
p95/p99 select sorted index floor((n-1)×percentile). Each run retains raw CSV and
`frame-summary.json`. Animated scene draw counts vary slightly across wall-time
sampling; this is one controlled checkpoint comparison, not identical frame replay.

| Metric | Corrected baseline640 | Sampler cache640 | Both caches640 | Both caches320 |
| --- | ---: | ---: | ---: | ---: |
| Frames in window | 469 | 505 | 543 | 683 |
| Mean-derived FPS | 11.72 | 12.65 | **13.58** | **17.07** |
| Wall p50 ms | 84.284 | 79.227 | 73.150 | 58.434 |
| Wall p95 ms | 90.666 | 83.145 | 78.396 | 60.546 |
| Wall p99 ms | 93.145 | 87.264 | 80.426 | 63.305 |
| Wall max ms | 104.175 | 94.287 | 84.684 | 121.493 |
| Main-thread CPU p50 ms | 51.981 | 43.090 | 42.392 | 42.849 |
| Draw submission p50 ms | 25.446 | 17.516 | 16.032 | 16.250 |
| Presentation p50 ms | 26.091 | 26.679 | 23.148 | 8.632 |
| Swap subset p50 ms | 25.117 | 25.662 | 22.024 | 7.426 |
| Draw count p50 | 374 | 366 | 368 | 371 |
| Vertex/index bytes per frame | 140124 | 140124 | 140124 | 140124 |

Runs, in table order:

- `r36s-dumps/sh3/20261113T174000195680Z-4b5840`
- `r36s-dumps/sh3/20261113T174327580891Z-54926b`
- `r36s-dumps/sh3/20261113T174837069025Z-36b849`
- `r36s-dumps/sh3/20261113T175211968006Z-bdd0f6`

Both renderer caches together improve640 mean-derived FPS15.9%, reduce median
draw submission37.0% and main-thread CPU18.4% against corrected baseline.
Attribute-only CPU improvement over sampler cache is about0.7ms; presentation
wait varies, so whole FPS difference cannot be assigned to that change alone.
No corrected renderer-only320 baseline captured; earlier320 figure includes
expensive diagnostic input. Do not present11.73→17.07 as physical renderer gain.

All four runs: execution/collection0, original sources preserved, clean frontend
recovery, CPU1512MHz/GPU520MHz/DMC786MHz throughout recorded samples. Whole-run
temperature ranges include startup: final640 sensors62.5–73.3°C/60.8–72.1°C;
final320 61.7–71.7°C/60.8–70.8°C. No recorded frequency drop. These are sequential
runs with recorded thermal variation, not a claim of identical temperatures.
Sample reports write successfully; corrected baseline5344 captured/38 dropped,
sampler4741/36, final640 4890/57, final320 5731/43. Drops include timer overruns,
under1.2% of requested samples; statistical hotspots remain approximate.

Final640 warm CPU sample distribution:2312 observations,1419 native runtime/game,
757 Mali,97 libc,11 SDL and28 other. Largest native leaf is
`recomp_fp_round24`219 observations (~9.5% of all CPU samples), followed by
`sub_004464E0`69 and matrix routine `sub_00648639`59. Exact-build symbol mapping
retained as final640 `cpu-symbols.json`. These are statistical leaf observations,
not inclusive timings or a stack profile. No guest math semantics changed.

## Historical first-slice validation and limits

- Actual Mali graphics run `r36s-dumps/sh3/20261113T175641744991Z-7b8214`:
  execution/collection0; all23 `GraphicsEvidenceTests` pass. Independent sampler,
  indexed/base-vertex, skinning, RHW, packed color, depth/stencil, texture, palette,
  copy and presentation oracles pass through actual firmware GLES providers.
- Final ARM64 Docker runtime suite112 tests:29 pass,83 explicit environment/data
  skips. Full desktop pixel/reference checks pass. External forwarding observer
  measures138 sampler updates and18 array enable/disable calls across76 draws.
- Real checkpoint movement/collision/combat regression:
  `.port-cache/movement-tests/20261113T174838248125Z`, all3 pass in480.172s.
  Delayed/reference movement ratio1.0474; game-clock rates0.99818/0.99682×wall;
  matching wall endpoint within0.88 units, health100; three handgun rounds in both
  presentation profiles. Delay modifies SDL presentation only, not guest clocks.
- Detached-service/device-plan tests13 pass; profile opt-in, report forwarding,
  physical-mode suppression and missing-profiler handling verified with observed
  RED before GREEN. Focused real-checkpoint profiling test also passes.
- At this first slice, issue #9 implementation, tests and report remained
  byte-identical to preserved pre-optimization snapshot. No full-scene handheld listening/visual reacceptance
  of final renderer candidate claimed; original owner listening results remain
  scoped to issue #9 build.

30FPS requires33.33ms/frame, while final heavy scene has42–43ms main-thread CPU
alone plus presentation/other waits. Lower resolution reduces presentation cost
without reducing that CPU floor. Next candidates are exact-semantics guest math
and remaining renderer/driver work, with behavioral proof before replacement.
These fixes establish measured progress, not30FPS feasibility or acceptance.

Still open for #13/#14: map exact lowest in-game graphics settings, identify
owner's monster room, cover broader representative routes and loading/shader/audio
stalls, quantify full profiling-disabled overhead, obtain direct GPU execution
timing where supported, and agree rare-stall policy. No reduced effects, overclock,
firmware replacement, fast math or allocator changes applied.

Review artifact: `.port-cache/issue-13/performance-local.diff` contains this
slice relative to preserved issue #9 state; existing issue #9 diff remains
`.port-cache/issue-13/issue-09-before.patch`. No commit, push, issue post or closure.
