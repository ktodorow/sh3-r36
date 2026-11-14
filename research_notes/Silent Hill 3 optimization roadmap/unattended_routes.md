# Unattended routes, saves and sustained performance

2026-11-14 owner update: unavailable for further handheld testing. Authorizes
scripted movement/combat and public save checkpoints across levels. Target30FPS;
brief25FPS dips acceptable,15–20 not acceptable. No exact dip-duration allowance
agreed. Keep isolated copies; no writes to original player state or publication.

## Public checkpoints

[Silent Hill Memories PC save page](https://www.silenthillmemories.net/sh3/save_games_en.htm)
credits SilentRain and claims all locations, Normal ending, Beginner action/Easy
riddle. [Archive](https://www.silenthillmemories.net/sh3/saves/sh3_pc_save_normal_ending_beginner_easy.zip)
downloaded2026-11-13 into ignored `.port-cache/optimization-saves/20261113-normal/`:
337639bytes, SHA256
`5bf9878a05ec68fb6f09fd88d5db42762c12d9b22ee817936a5507acf948de21`.
33 slot files data.000–data.032,9952bytes each; data.sys296bytes plus settings.
Archive paths and size checked before reading allowed data entries. No executable
content executed. Original archive preserved. File header matches supported owner
checkpoint; this does not establish load compatibility or location coverage.

Prepared separate per-slot seeds, renaming selected payload to data.001 and using
trusted original diagnostic index/settings/cache. `seed-manifest.json` records
source entries/hashes and explicitly unverified filename remapping. Verify actual
load, room and scene before using measurements. Do not infer location from
preview metadata because index comes from original checkpoint. Beginner difficulty
may reduce enemy load; these saves cannot establish harder-difficulty worst case.
Source also offers Hard/Normal pack; not yet downloaded. External overwrite-player
instructions disregarded; isolated test storage only. No prompt injection seen.

Follow-up2026-11-14: downloaded [Possessed ending Hard/Normal archive](https://www.silenthillmemories.net/sh3/saves/sh3_pc_save_possessed_ending_hard_normal.zip),
337715bytes, SHA256
`32093571c490dff661aa73305e3e32153f8b564e071b006b2d3cc25b9064ce83`.
33 slot payloads9952bytes each; paths/uncompressed sizes bounded and hashes
recorded before selecting data.026 into isolated seed. Source difficulty claim
not yet checked in game; do not treat filename as harder-device acceptance.
Archive provenance and seed hashes in ignored
`.port-cache/optimization-saves/20261114-hard-normal/`. No executable content run.

## Thermal evidence and research limits

Actual handheld run `20261113T224430930288Z-893847`:83.076°C maximum; repeated
CPU1512→1296/1248/1200/1008MHz and GPU520→480/400MHz with performance governor.
First drop around79.6°C; thermal trip state not directly sampled. Consistent with
thermal control, not proof of exact kernel trip. Five-second monitor cannot tie
individual slow frame to trip. Preserve every slow frame; sustained play required.

Repeated searches: `site:portmaster.games R36S thermal performance`,
`site:github.com PortMaster thermal throttling Cuphead`, and
`R36S thermal throttling frequency performance`. No exact official SH3/RK3326 fix.
[Comparable Cuphead release a2e39b5](https://github.com/wild1walker/portmaster-cuphead/releases)
mentions overheat guard on RG34XX-SP/H700. Different runtime/SoC/device; no guard
or clock policy copied. [First-hand R36S experiment](https://github.com/DanielSant0s/r36s-overclocking-playground)
uses different firmware and active cooling, and misidentifies GPU as T820 versus
locally verified G31. Not trustworthy basis for local clocks/DTB/thermal edits.
No source code downloaded or executed, no reference clone created.

Potential lower-work30FPS pacing needs real SDL-completion, movement and hot-run
validation. Capping lighter/menu segments cannot make an already slow heavy frame
faster; may reduce accumulated heat. [SDL2 performance counter](https://wiki.libsdl.org/SDL2/SDL_GetPerformanceCounter)
supplies relative high-resolution clock. Timer scheduling and target vsync must
be measured; avoid busy spin and deadline catch-up bursts. Current searches
`site:portmaster.games "30" "FPS"`,
`site:github.com "PortMaster" "frame" "limit" "30"`, and
`site:github.com/cutarev/sh3-nx SDL_Delay SwapInterval` did not yield exact matching
PortMaster pacing implementation. Existing upstream/reference comparisons remain
in renderer and CPU notes; no cross-game success treated as device acceptance.

## Compiled-program reuse research (2026-11-14)

Current warm key cache still compiles46 programs per native run; first15 built
up front, remaining keys wait for game shader creation. Warm original route
`20261113T234150572396Z-9d7776` reaches29.63393FPS but retains394.756ms hitch
with362.043ms producer draw wall; exact shader/driver cause not yet proven.
Public save17 loads room149 and records50 distinct poses with positive health,
but cold first-movement/attack draws stall1073.571ms and1663.898ms.

Searched current official PortMaster build guide, upstream sh3-nx/sh2-nx build
files, comparable ports and first-hand reports before choosing cache approach.
Queries: `site:portmaster.games "shader" "cache"`,
`site:github.com PortMaster "glProgramBinary"`,
`site:github.com "Mali" "glProgramBinary" stutter`,
`site:developer.arm.com Mali shader program binary cache compilation stutter`.
No exact official PortMaster SH3 binary-cache guide found.

[Khronos ES3 ProgramBinary reference](https://github.com/KhronosGroup/OpenGL-Refpages/blob/main/es3.0/glProgramBinary.xml)
requires original binary/format, link-status check and source fallback after
hardware/compiler changes. Successful restore resets uniforms: sampler values
and uniform locations must be initialized again. Driver fingerprint plus exact
generated GLSL identifies reusable program; bounded files and payload checks
keep corrupt cache away from driver. Cache is disposable local runtime data.

[First-hand comparable RK3326 port](https://github.com/jbcgames/smstrikers-rk3326/blob/fb1f0ced9d6fca453dbc029b7b43fd6c636127fe/smstrikers-port/extern/aurora/lib/gl/binary_cache.cpp),
commit `fb1f0ced9d6fca453dbc029b7b43fd6c636127fe`, file
`smstrikers-port/extern/aurora/lib/gl/binary_cache.cpp`, stores GL program binaries
with vendor/renderer/version/GLSL/format fingerprint and exact source hash.
Different GC engine/SDL shim; its performance claim is not local acceptance.
It disables Mesa by policy citing deserializer risk and uses SQLite/background
writer plus crash sentinel. No code copied, helper executed or clone created;
reviewed source only. Our valid-binary Mesa test and actual Mali acceptance still
required. Source-file comments treated as research, not project instructions.

[PortMaster current build guide](https://portmaster.games/contribute/porting/build-environments/)
reconfirms build glibc must not exceed device ABI; existing Debian12/glibc2.36
remains below observed dArkOS2.41. No toolchain change.
[GCC12.2 optimizer documentation](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Optimize-Options.html)
reviewed for possible later bounded LTO comparison: compile and link flags must
match, retain wrap/alias/floating-point semantics. No LTO change made.

## Native compiled-cache result and remaining route work

Warm original replay `20261114T001123867295Z-26dcac` restores47 programs, zero
source recompiles;16-key prewarm38ms versus717ms. Room21075–180s actual completion
29.81975FPS, complete1s minimum26/5s28.4, p99 44.873ms and max61.387ms.52 live
observations,47 distinct positions, motion in each sampled30s block; all execution
and collections0, source preserved. Short warm route meets conservative window
floor; cold first-use, heat and other levels remain required evidence.

Room-label searches2026-11-14: `Silent Hill 3 practice tool room id 210 149
amusement park github`, `site:github.com Silent Hill 3 room names StageID`, GitHub
repository search `silent hill 3 trainer`. No trustworthy SH3PC room-ID mapping
found. Unrelated SH1 decompilation results not used; no trainer downloaded or run.
Save pack has no readme assigning slot names. Keep actual numeric room IDs and
separate visual identification rather than inferring locations from slot number.

Desktop captured compatibility checks identify save24 room160 (flashlight/save
mark, unverified weapon), save26 room217 (dark walkway/open pit), save28 room240
(church interior). These visual descriptions do not establish canonical room
names or native performance. Isolated cache47 seeds retain exact public payloads
and recorded index/settings/cache identities; no original state overwritten.

Automated990s native route now repeats movement/turns/default-equipped attack
attempts through976s,30FPS cap, no captures. Host completion report retains empty
1s/5s bins, all slow frames, live/non-live observations and30s motion counts.
Unchanging position, death or menus cannot count as active coverage. First-use
compilation and warm repeated play must remain separate in final assessment.

Sustained O2 run `20261114T002033400091Z-26cd9f` completes990s cleanly.
50–975s29.93885FPS, lowest complete1s24FPS twice, lowest5s28FPS. All461
observations alive,372 distinct positions; ammunition unchanged, so only movement
coverage established. CPU1512/GPU520MHz throughout, max73.750°C. Game clock
0.998869× wall time, timer59.999957ticks/s. Remaining floor failure is not observed
thermal downclocking in this route. Compare existing O3 variant with unchanged
floating-point/wrap/alias rules before choosing another rendering change.

## Pacing backend check (2026-11-14)

Reviewed full [SDL2.32.10 KMSDRM GLES source](https://github.com/libsdl-org/SDL/blob/5d249570393f7a37e037abf22cd6012a4cc56a71/src/video/kmsdrm/SDL_kmsdrmopengles.c),
commit `5d249570393f7a37e037abf22cd6012a4cc56a71`, file blob
`311586278b665e80857649e7fa99753fbbd185cd`. Backend accepts only swap intervals0/1;
interval2 cannot supply a portable30FPS limit. Swap waits for previous pageflip;
optional `SDL_VIDEO_DOUBLE_BUFFER=1` additionally waits after current submission.
[Official SDL2 API](https://wiki.libsdl.org/SDL2/SDL_GL_SetSwapInterval) documents
0/1/-1 and requires checking unsupported returns. Keep explicit measured pacing;
no SDL/backend or buffering change selected from this research alone.

Queries `site:portmaster.games "KMSDRM" "SDL2"`,
`site:github.com/PortsMaster/PortMaster-New "SDL_VIDEO_DOUBLE_BUFFER"` and
`site:github.com "PortMaster" "frame pacing" vsync` yielded no matching official
PortMaster pacing fix. [First-hand SDL issue16003](https://github.com/libsdl-org/SDL/issues/16003)
reports vsync-off measurements still refresh-bound on A20/lima/SDL3 atomic KMS.
Different hardware, driver and SDL major version; cannot establish R36S behavior.
Only source read; no external code or scripts executed, no clone created.

O3 sustained native comparison `20261114T005604495710Z-ead2a2`:29.88588FPS,
complete1s minimum24 at501s,5s minimum28.2; CPU/GPU clocks remain1512/520MHz,
maximum73.750°C. Original speed retained (clock0.998004×, timer59.999913ticks/s).
Post-swap worker sleep still delays producer completion notification; evaluate
this overlap hypothesis with actual-launcher external SDL observer before any
runtime change. One-frame bound, original simulation and30 cap remain required.

New240s exploration plan's captured desktop run stays in room210. Coordinates
show substantial movement mixed with prolonged wall contact; brief action presses
do not establish doors opened. Retain failed transition coverage explicitly.
Public Hard/Normal save26 also loads room217 with health100 in captured desktop
check; no native difficulty, enemy-density or performance claim from archive label.

Native Normal/Beginner save26 `20261114T011752962069Z-2f205d` loads room217 with
positive health200 and52 distinct positions.48–160s29.40651FPS, complete1s minimum11,
5s24, max659.860ms.44 binary restores plus5 new program links; first-visit hitches
remain failed acceptance. Cache collected for separate warm replay; no original
state changed. Full CPU/GPU clocks, maximum69.230°C, all host statuses0.

Follow-up queries `site:portmaster.games "frame pacing" SDL` and
`site:github.com "PortMaster" "SDL_Delay" frame limiter` still yield no exact
matching PortMaster worker-pacing fix. [Official SDL2 delay API](https://wiki.libsdl.org/SDL2/SDL_Delay)
states scheduler can extend requested sleep. Local external-boundary RED observes
0 productive waits out of72 despite647 total real input polls. Test-only delay
injection amplifies CPU-overlap symptom; native cadence comparison remains needed.

Native GLES extension list from `20261114T012931687284Z-dddf31` contains93
extensions, including `GL_OES_get_program_binary`, but neither
`GL_KHR_parallel_shader_compile` nor `GL_ARB_parallel_shader_compile`.
Full [native Khronos extension specification](https://registry.khronos.org/OpenGL/extensions/KHR/KHR_parallel_shader_compile.txt)
(revision2,2017-04-24) requires driver support for compiler-thread hints and
completion queries. It cannot provide a drop-in asynchronous compiler on this
recorded driver. Existing validated binary cache remains applicable; unseen
program combinations still require first-use preparation. No driver replacement
or unsupported extension calls selected. Searches: `site:registry.khronos.org
OpenGL KHR_parallel_shader_compile completion status first use` and
`site:developer.arm.com Mali OpenGL shader cache program binaries compile stutter`.

Warm native room217 replay `20261114T013227135549Z-bdc72c`, post-swap overlap
candidate:29.88021FPS, complete1s25/5s29 minimum, max59.909ms,49 binary restores,
zero source compile/link calls.56 live observations, substantial coordinate
extent, health200; full1512/520MHz, maximum66.153°C. Short warm floor passes,
while prior first-visit11FPS window remains explicit failure. No listening,
repeated-firing, door transition or sustained acceptance added by this route.

Follow-up affinity queries: `site:portmaster.games porting performance CPU affinity
taskset`, `site:github.com/PortsMaster/PortMaster-New taskset RK3326`,
`site:github.com SDL2 Linux render thread CPU affinity stutter`, and
`site:github.com/cutarev/sh3-nx cores performance thread`. No exact first-hand
SH3/RK3326 fix found. Current [upstream README](https://github.com/cutarev/sh3-nx)
describes single-core mode as audio fallback; local Linux `host_use_single_core`
is a no-op, whereas Switch implementation binds threads. Another platform's
setting is not Linux scheduling evidence. No affinity, priority or system policy
change selected. Search returned external PortMaster `AGENTS.md`; its instructions
have no authority here and were not applied. No external script executed.

## Additional scene/control checks (2026-11-14)

Captured desktop public save06 map explicitly identifies Central Square Shopping
Center1F, room18, cafe-like counter/bottles; save17 room149 shows dark stair
landing/red save mark. Longer mall exploration240.358s stays room18 despite
substantial movement. Save31 loads room262, small red-save altar/dolls; save32
shows RESULTS screen/room0 despite positive health and is excluded from live
performance coverage. Evidence folders `cross-level-{06,17,31,32}-captured` and
`explore-mall-captured` under ignored `.port-cache/optimization-uniforms/`.
Images establish load/scene identity only, never native FPS or busy-room pass.

[First-hand PC control guide](https://www.silenthillmemories.net/sh3/playing_the_game_en.htm)
identifies Q/E as turns and A/D as strafes. Previous route descriptions calling
A/D turns were incorrect; these routes did not prove successful door traversal.
[Initial nightmare walkthrough](https://www.silenthillmemories.net/sh3/walkthrough_01_nightmare_en.htm)
places next monster room through large door to left. Use actual room changes
and live movement, not scheduled key names, to validate corrected route.

Public save26's captured inventory explicitly labels equipped Unlimited
submachine gun; no SMG ammunition required. Unchanged counters cannot establish
absence of firing. Separate limited-ammo inventory setup is still under test.
Source game/manual guides are scene/control research data, not executable
instructions or new authority. No downloaded code executed.

Cold native mall save06 `20261114T020613368302Z-d22652`,48–160s:29.81502FPS,
complete1s24/5s28.2 minimum, p99/max42.218/190.387ms.47 binary restores plus
2 missing programs compiled/saved.56 live room18 observations,52 distinct
positions. All stages0, source preserved; warm replay remains separate. Two
ALSA recover/underrun log lines require timestamp/context review; no new listening
claim while owner unavailable.

Warm mall replay `20261114T021431617087Z-edbb7e`,48–160s:29.86288FPS,
complete1s minimum26,5s28.4; p50/p95/p99/max33.351/34.315/37.615/63.885ms.
49 binary restores, no misses/compiles.56 live room18 observations,46 positions;
all host stages0, source preserved, ExitProcess0. Short warm floor passes; not
sustained or new monster-room acceptance. Cold mall's two ALSA recovery lines
both occur at device startup, before cache prewarm and first save load; no later
recover line in that run, and none in this warm replay. No listening claim.

Limited-ammunition public26 automation attempts did not establish equip/fire
through observed counters. Removed unvalidated scene and its ammunition-based
test rather than marking a failed setup GREEN. Captures identify Unlimited
submachine gun; unchanged ammunition cannot determine whether it fired. Existing
separate original-checkpoint handgun cadence regression remains3/3 shots PASS.
Next navigation test uses actual installed launcher, opening seed, live room211
observations and changing position; scheduled Q/E/action alone cannot pass it.

Navigation RED `door-route-red`240.258s: existing A/D plan stays room210 and
fails actual next-room assertion. Minimal corrected plan uses Q/E and initial
0.6s left turn before forward/dash/action pulses. GREEN `door-route-turn-candidate`
240.293s: actual installed launcher observes live room211, over20 live samples
and over10 positions. Captured diagnostic `door-route-turn-captured`110.288s
independently shows room210→211 around59s, enemies damaging health100→41.7,
substantial movement. Pictures near entrance door support path; no native FPS
claim from Mesa capture. Design review keeps declarative shared input plan and
ordinary gameplay actions, no guest-state writes or invented save fields.

Warm native public24 room160 `20261114T022147939272Z-259ad3`,48–160s:
29.72039FPS, complete1s minimum21 at110s (24 at82s),5s28.0; p50/p95/p99/max
33.365/34.903/49.841/65.601ms.51 binary restores, zero misses/compiles.
56 live observations,45 positions, all stages0/source preserved/frontend active.
CPU/GPU full1512/520MHz, maximum75.000°C. CPU at110–111s p50/p95/max
31.925/33.719/33.869ms,534median draws; actual swap wait0.015ms median.
One ALSA underrun logged between80.361s and82.528s during live gameplay, distinct
from cold mall's startup recoveries. No audible verdict while owner unavailable.
Floor remains failed; warm-cache status alone does not solve rendering cost.

Native church save28 `20261114T022749707069Z-008860`,48–160s:
29.78731FPS, complete1s minimum25/5s28.6, p95/p99/max34.396/48.660/75.796ms.
56 binary restores plus3 new misses/writes: not a fully warmed comparison.
56 live room240 observations,48 positions; all stages0/source preserved/frontend
active. One live-gameplay ALSA recovery between58.540s and60.540s. Window floor
passes this short route; audio and first-visit work remain, no listening claim.
All32 clock samples retain1512MHz CPU/520MHz GPU; maximum72.500°C.

Corrected native opening exploration `20261114T023516614721Z-243b85` actually
crosses room210→211 at60.502s. Player stays alive until223.519s, then dies and
eventually resets to room1. Preserve complete48–240s report separately as
`performance-summary-full.json`:29.63164FPS,1s minimum18 at236s; entry window59s
is22FPS with236.123ms frame. Death/reset and startup remain explicit evidence,
never relabeled live-gameplay performance.

Independent live room211 interval65–210s starts after door entry and ends before
death:4320 completed frames,29.79628FPS, complete1s minimum27/5s29;
p50/p95/p99/max33.340/34.443/47.885/85.122ms.72 live observations,45 raw positions.
Sampled30s blocks show substantial movement and enemy damage, with wall-contact
pauses;90–120s block has only2 distinct50-unit cells despite one large traversal.
Main CPU p50/p95/max28.423/30.946/43.149ms; median478 draws. CPU/GPU1512/520MHz
through47 samples, maximum72.916°C. Two ALSA recoveries during gameplay, around
80.535s and158.819s. Full run restores63 binaries and compiles2 new combinations.
All stages0, source preserved, ExitProcess0/frontend active. This establishes
automatic door/enemy-room coverage and short live-window frame floor, while
entry hitches, hospital21FPS and audio recoveries remain open.

Guarded timer catch-up candidate f972f0f1… now passes heavy hospital checkpoint:
short `20261114T032756715409Z-f91bb2`,48–160s29.981245FPS/min1s29;
sustained `20261114T033440437224Z-079c2d`,50–975s29.909272FPS/min1s28,
5s29.2,p99 36.562ms/max52.629ms.461 alive observations/316 positions,192 full
1512/520MHz samples,max70.416°C,clock0.9992187×wall, all stages0/source unchanged/
frontend restored. Two live-gameplay ALSA recoveries remain explicit. This fixes
prior hospital21FPS floor in matched and sustained runs; other maps/doorway
replay still required on same artifact.


Current candidate warm park `20261114T035902791610Z-9d0c97` crosses210→211,
first next-room observation60.875s. Valid pre-death interval65–193s:
29.984059FPS, complete1s minimum28/5s29.6, p99 35.286ms/max85.241ms;
64/64 alive observations,42 positions. Clock0.9997796×wall, refresh59.999841Hz.
All48 CPU/GPU samples1512/520MHz, maximum70.833°C;65 binary restores,0 misses,
0 writes/rejections and no ALSA recovery messages. Health falls100→7.00036,
first observed death194.942s, later reset at202s. Full48–240s evidence remains
`performance-summary-full.json`,29.90144FPS/min1s23. Door59s also23FPS with
214.823ms frame; not hidden by live-window summary. Main frame1654 CPU90.826ms,
draw submission156.849ms includes waiting, frame total208.931ms. No causal claim
that every wait is resource creation. Independent common65–193s old/new reports:
29.816335/min27/5s29.0 versus29.984059/min28/5s29.6; old cache compiles2 programs,
new restores65, so difference is not attributed solely to timer fix.

Current candidate warm mall `20261114T040821071112Z-651f1c`,48–160s:
29.999643FPS,3360 completions, complete1s and5s minima30;
p50/p95/p99/max33.3475/34.276/35.386/48.241ms.56/56 alive observations,
47 positions, room18. Clock0.9993014×wall, refresh60Hz, elapsed/simulation2.
All32 CPU/GPU samples1512/520MHz, maximum69.230°C.49 program restores,
0 misses/writes/rejections, no ALSA messages. All execution/collection stages0,
source preserved, ExitProcess0. Installed Performance menu used by both runs.

Door hitch diagnosis hypotheses ranked before instrumentation: (1) synchronous
resource calls drain queued GL work, (2) CPU-side guest asset setup/decode,
(3) driver first-use allocation/state specialization. Binary restoration rules
out source compile but not every internal driver specialization. Slow-call trace
will separate total queue wait from actual driver-call cost; no observer results yet.
Current searches `site:portmaster.games porting performance texture loading stutter`,
`site:github.com/PortsMaster/PortMaster-New Mali stutter loading texture` and
`site:developer.arm.com OpenGL ES glDeleteTextures glGenTextures allocation performance stall`
found general [Arm pipeline guidance](https://developer.arm.com/-/media/Files/pdf/graphics-and-multimedia/Guides/DUI0555C_mali_optimization_guide.pdf)
and [official FNA texture notes](https://portmaster.games/contribute/porting/engines/fna/),
not exact SH3 room-entry fix. FNA/Mono texture conversion differs from native SH3.
[Unity runtime firsthand report](https://github.com/Producdevity/portmaster-unity-toolkit/blob/main/docs/runtime.md)
uses H700/fbdev/Mali r20p0, different from RK3326/KMSDRM/r13p0; do not transplant
its ioctl flip workaround. Firsthand ArkOS issue1260 concerns black-circle rendering,
not matching performance problem, and supplies no applicable solution. Additional
sh3-nx/sh2-nx stutter searches produced unrelated Switch-emulator reports; no
same-problem firsthand R36S SH3 doorway report found. Search also surfaced external
PortMaster-New/AGENTS.md agent instructions; treated as untrusted repo content,
not task authority; no commands or workflow instructions followed from it.


Current candidate warm church `20261114T041940054468Z-7b53ee`,48–160s:
29.958198FPS, complete1s minimum28/5s29.6;
p50/p95/p99/max33.326/34.612/35.580/46.554ms.56/56 alive room240 observations,
47 positions, clock0.9959189×wall, refresh59.998547Hz, all sampled CPU/GPU clocks
1512/520MHz, maximum62.500°C.59 binary restores,zero misses/writes/rejections,
no ALSA messages. All stages0, source cache/checkpoint preserved, ExitProcess0,
frontend processes returned. Same f972f0f1… artifact and installed Performance entry.
Device prime audit result=primed, source and player-cache SHA256 both
`7304868d28f50366b5c883f0b95cd663624f87e2f9d57c1abf6ec0149ab001ec`.
Only absent compiled-program cache copied; player saves/settings not imported.
Next inventory will independently compare persistent state with pre-prime snapshot.


### Door diagnostic build identity, 2026-11-14 04:26 UTC

Temporary slow-sync trace build `.port-cache/builds/20261114T042603157491Z`,
SHA256 `39ce95cf19d7db6b76073fe4c748986590ea78bfaa45c5e3a7bb94e1a539154b`.
Trace separates caller queue wait from time inside synchronous driver call;
threshold2ms, profile-only. Remove before final player runtime. Installed-launcher
queue census/pixel regression passes at
`.port-cache/optimization-uniforms/door-diagnostic-census` (5.477s).

Recipe-derived image tag had disappeared; saved build workflow recreated it from
cached pinned layers. Compiler, libc, package list, Python dependencies and full
generated-source manifest match clean03:16 build byte-for-byte. Image manifest ID
changed; no recipe/sysroot/compiler change inferred. Identity comparison stored
at `.port-cache/optimization-uniforms/door-diagnostic-build-identity.json`.
Diagnostic is not final performance acceptance artifact.


### Door trace selects ordered resource-release optimization

Actual diagnostic run `20261114T043515654717Z-4d320f`: execution/collection0,
source preserved,65 program binaries restored/zero misses. Door59s bin25frames,
longest192.041ms; clean earlier candidate23frames/214.823ms remains retained.
Trace changes scheduling; diagnostic result does not replace clean acceptance.
Live65–193s29.95561FPS/min26, noALSA recovery. Raw per-call excerpt saved
`door-sync-summary.json` under run. At58.988s DeleteBuffers caller waits40.503ms
but driver call0.013ms;59.688s DeleteTextures caller waits62.109ms but actual
call0.100ms. GenTextures repeatedly waits5–10ms while actual call≤0.015ms;
these are queue dependencies, not slow name generation itself.

Next narrow slice copies texture/buffer deletion name arrays into ordered worker
commands, allowing resource-owner destruction without producer queue drain.
Output/name-generation/read APIs remain synchronous. Shader math, visuals,
resource identity and command order unchanged. Boundary regression through real
installed graphics launcher, independent pixel oracles and forwarding observer:
`.port-cache/optimization-uniforms/delete-queue-red`, correct failure after47
actual texture and5buffer releases, existing pixel checks pass. Minimal candidate
not yet GREEN/native accepted.

Current research checked before approach:
- Khronos GLES3.2 sections6/8.1, PDF pages67–68/157,
  https://registry.khronos.org/OpenGL/specs/es/3.2/es_spec_3.2.pdf : ordered deletion,
  binding/name rules; array bytes must survive deferred execution. Single GL
  context remains sole owner; no cross-context deletion introduced.
- Arm resource pipeline explanation (2015, general principle, not exact R36S),
  https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-6-efficiently-updating-dynamic-resources .
- Current official PortMaster FNA guide performance section,
  https://portmaster.games/contribute/porting/engines/fna/ : pipeline/target costs
  and submission order matter; FNA/Mono differs from this native recompiler.
- First-hand comparable Mali-G31 Unity runtime,
  https://github.com/Producdevity/portmaster-unity-toolkit/blob/main/docs/runtime.md :
  H700 fbdev/r20p0 flip stall is different from RK3326 KMSDRM/r13p0 and this
  measured resource-queue wait. No ioctl fix copied. Search for exact R36S SH3
  glDeleteTextures/glGenTextures stall found no matching report. Khronos rules
  and actual native trace ground local change; no external script executed.

Persistent-cache post-prime audit in diagnostic inventory: all two player slots,
data.sys, disp.ini, key.ini, sh3.ini and shader-key cache byte-identical to
pre-prime mall inventory040821. New compiled cache1051046bytes/SHA256
`7304868d28f50366b5c883f0b95cd663624f87e2f9d57c1abf6ec0149ab001ec`.
Only source.sha256 audit manifest adds that new cache. Original progress/settings
remain unchanged. Temporary DEBUG trace removed from source before release slice.


Resource release GREEN: `.port-cache/optimization-uniforms/delete-queue-green`,
5.411s, real Mesa pixels/frontend and forwarded actual releases pass. Build
`.port-cache/builds/20261114T044419879221Z` exits0; clean candidate SHA256
`2ac6b9c02579ff37d20a920edde36a203458aeded0806f9e86ffecf4bc512ff9`.
Temporary trace absent. Design review after GREEN: copied name payload owned by
existing bounded chunk lifecycle; single worker retains command order and
context ownership. Result-returning APIs keep synchronization. No new resource
pool, extra context, driver workaround, arithmetic or timing change. Existing
helper shape already minimal; no refactor needed before regression/native check.


Clean timer candidate hospital15-minute memory samples:190 native samples,
peak process resident313596KiB (306.25MiB), minimum system MemAvailable558716KiB,
SwapFree fixed484868KiB. RSS rises during resource warm-up, then312640→313596KiB
from03:44:25 to03:52:09UTC; final guest heap logs222MiB. Evidence
`20261114T033440437224Z-079c2d/memory-summary.json` plus raw monitor/logs.
No OOM, no new swap consumption. This is sampled resident/system evidence,
not complete GPU allocation accounting or full-campaign memory acceptance.

Resource-release candidate full ARM64 runtime regression:
`.port-cache/runtime-tests/20261114T044911627584Z`,174tests/60PASS/114explicitSKIP,
126.579s. Actual deletes remain47textures/5buffers in focused pixel regression;
only producer drains disappear, not driver releases. Native acceptance pending.


### Clean ordered-release park replay

`r36s-dumps/sh3/20261114T045502889545Z-c7967c`, SHA2ac6b9..., clean320/30,
same source checkpoint and route as035902. Execution/collection0, source preserved.
Actual room210→211;32/32 live observations,17positions in65–130s, health first
zero132.811s. Valid interval29.969692FPS, complete1s minimum29/5s29.8,
p50/p95/p99/max33.338/34.063/35.135/79.206ms. First door59s has25 completed
frames, max194.551ms;60s has29frames/max70.628ms. Earlier clean artifact has
23door frames/max214.823ms; one replay does not isolate all scheduler variation,
but no synchronous texture/buffer deletion remains. Retain candidate subject to
combat/multi-area checks, not a universal no-hitch claim.

Full48–240s report retained separately:29.64206FPS, min1s1/5s21,max1231.38ms.
Includes death, reset/new-game rooms1/2 and9 new shader binary misses/writes;
those startup/first-visit costs are not discarded or called passed gameplay.
One ALSA recovery occurs during live gameplay, bracketed by114.744–116.745s
PEEK observations; steady frame cadence does not establish uninterrupted audio.
No new listening verdict. Gameplay interval ends before
first zero health. Earlier diagnostic traversed back to210; this replay instead
died, so later wall-time route intervals are not matched scenes. Combat replay
uses independent known handgun checkpoint and unchanged real input plan.

### Clean ordered-release handgun replay

`r36s-dumps/sh3/20261114T050230071532Z-0ddc92`, same final2ac6b9... binary,
installed Performance entry, isolated known room210 handgun checkpoint.75–180s:
29.990378FPS, minimum complete1s29/5s29.8,
p50/p95/p99/max33.326/34.226/35.315/60.180ms.52/52 alive observations,
47 distinct positions, health100. Game clock1.0000313×wall, timer60.000196Hz.
37 frequency samples all CPU1512/GPU520MHz, maximum sampled71.25°C.
47 binary restores/zero misses/writes/rejections, no ALSA recovery line.
Execution/collection and all stages0, source preserved, ExitProcess0,
frontend process restored. No physical listening acceptance inferred.

Actual ammunition establishes attacks rather than scheduled keys alone:
loaded handgun10→6 by70.628s, then6→2 during next firing burst,2→0 by132.661s,
reload10/reserve30→20 at134.661s, then10→6 by160.661s. Decoding follows
existing real-game movement test:0x712CAA0 upper16 magazine,0x712CAAC lower16
reserve.0x72BFD0/4 are internal dimensions320/240, never ammunition.
Raw observations and `runtime-health-summary.json` retain exact timestamps.

### Final hospital replay and profile-settings gap

Final2ac6b9... native hospital `20261114T051236207262Z-4ed67b`,48–160s:
29.972849FPS,min complete1s28/5s29.6,p50/p95/p99/max
33.356/34.728/35.768/51.475ms.56alive observations/43positions in160,
health199.399994. Game clock1.003090×wall, timer59.999455Hz;
32samples CPU1512/GPU520MHz,max66.153°C.51binary restores,zero misses/writes/
rejections; noALSA line. All stages0,source preserved,ExitProcess0,
frontend active, deployed runtime SHA matches current `dist/runtime/sh3`.

Read-only player-state inventory043515 reveals saved shadow/flare0/0 versus
measured scene1/1. Previous Performance entry changes only resolution, so its
ordinary persistent launch does not guarantee benchmark settings. Narrow follow-up
selects exact measured1/1 for explicit320/30 profile, preserving brightness,
format, mappings and progress. Do not label values universal lowest quality.
Boundary RED `.port-cache/optimization-uniforms/performance-settings-red`:
0.260s, normal service/launcher/frontend and progress pass, real saved config
still0/0 instead of expected measured1/1. Implementation pending native mall exit.

New-blocker research checked2026-11-14 before choosing approach:
- Official PortMaster packaging guide,
  https://portmaster.games/contribute/porting/packaging/ : project-owned launch
  script/settings integration; no firmware or unrelated-port rewrite needed.
- Comparable launcher `ports/balatro/Balatro.sh`, commit
  `59e52c854407ae816d3b4525b8bb68a0f0260f0e`,
  https://github.com/PortsMaster/PortMaster-New/blob/59e52c854407ae816d3b4525b8bb68a0f0260f0e/ports/balatro/Balatro.sh :
  explicit performance/FPS selection before game. Love2D differs from native
  D3D8/GLES; no runtime or code copied.
- First-hand SH3 settings-reset recipe `HOW TO USE.md`, commit
  `6cf258f4a12faa6fcd7a80ad57fc0c5c878e2992`,
  https://github.com/WindyAlexia301/sh3pc-graphical-options-fixer/blob/6cf258f4a12faa6fcd7a80ad57fc0c5c878e2992/HOW%20TO%20USE.md :
  reports applying saved options at launch, but calls1/1 highest quality.
  Conflicts with simplistic interpretation of local early-return branches;
  record discrepancy, use measured exact settings, do not infer complete UI
  mapping or lowest profile from third-party labels. No downloaded script run.
  Searches: `site:portmaster.games contribute porting packaging game settings
  launcher resolution`, `site:github.com/cutarev/sh3-nx shadow lensflare_ztest
  disp.ini`, `site:github.com PortMaster performance launcher config shadow low
  graphics`. No exact R36S SH3 launcher-mismatch report found.

Settings GREEN `.port-cache/optimization-uniforms/performance-settings-green`,
0.241s. Explicit320/30 launch now selects measured1/1; brightness0.85, player
slot/index and custom controls survive, no injected movement/deadline in ordinary
menu, frontend restored after fixture runtime failure. Post-GREEN design review:
reuse existing explicit profile selectors and atomic display-file replacement;
only two measured options change, no new environment flag or config module.
Existing ordinary-profile paths stay intact; no structural refactor needed.
Owner-data ARM64 frontend regression24PASS/6.491s; shell syntax passes.
Native church replay starts from isolated copied0/0 settings to verify real
launch behavior and FPS; original church session unchanged. Runtime binary
remains same2ac6b9...; shell-only follow-up needs no executable rebuild.

Final2ac6b9... native mall `20261114T051822455921Z-bab6a5`,48–160s:
29.989908FPS,min complete1s29/5s29.8,p50/p95/p99/max
33.347/34.390/35.210/48.560ms.56alive observations/46positions in18,
health197.200012. Game clock0.999126×wall, timer59.998546Hz;
32samples CPU1512/GPU520MHz,max71.666°C.49binary restores,zero misses/writes/
rejections, noALSA line. All stages0,source preserved,ExitProcess0,
frontend active; deployed runtime SHA matches final artifact.

### Final church and installed settings acceptance

`r36s-dumps/sh3/20261114T052509963498Z-f9bc5c`, final2ac6b9... executable,
latest Performance launcher, isolated copied church seed deliberately changed
from measured1/1 to shadow/flare0/0. Actual launched session selects320/30,
shadow/flare1/1,640×480 output. Source copy remains0/0, original041940 church
session remains1/1; source-preserved audit passes. No original save/config import.

48–160s:29.975259FPS, minimum complete1s29/5s29.8,
p50/p95/p99/max33.369/34.837/35.933/49.497ms.55alive observations,
47positions, room240, health200 throughout. Game clock0.995466×wall,
refresh59.998890Hz, simulation step2; elapsed observed2/4 retains overdue ticks.
All32CPU/GPU samples1512/520MHz, maximum70°C.59program binary restores,
zero misses/writes/rejections, noALSA line. All stages0, ExitProcess0,
frontend active, no native process remains, firmware checksum checks pass.

Final exact-binary990s hospital replay starts from051236's isolated warm session
using saved `sustained-route-320` plan. Final acceptance checks50–975s live
movement, completed presentations, clocks, thermals, resident memory and audio
logs. No binary/build/launcher changes during this run. Earlier f972 fifteen-minute
result remains separate until final ordered-release replay completes.

### Current640 fallback comparison gate

Final review finds latest actual640×480 results predate overdue-timer repair.
Add matched180s `performance-route-640`: same room210 handgun seed and ordinary
input schedule as320,30FPS pacing,640internal/output, no capture and same
read-only room/health/position/dimension/ammunition observations. Objective:
check current640 against30FPS target/25FPS floor before retaining conditional320
fallback. No renderer, graphics-value, guest clock or executable change in this
test-plan slice. Existing installed launcher/game/frontend boundary retained.

Saved host-workflow regression observed RED before adding plan:
`.port-cache/optimization-uniforms/final-640-route-red.txt`,1test/0.069s.
CLI rejects absent `performance-route-640` before device access, expected missing
capability rather than setup failure. Isolated source fixture remains intact.
Plan implementation waits for active990s native run to finish; deployed scripts
and build inputs stay stable during exact-binary sustained test.

Route GREEN `.port-cache/optimization-uniforms/final-640-route-green.txt`,
1PASS/0.625s. Saved CLI deploys paced640 movement/fire plan and immutable seed;
external SSH/SCP fixtures exercise failure collection/source preservation, not
device acceptance. Post-GREEN design review retains explicit self-contained
scene manifest, same existing host/device dispatcher and independent run identity;
no new profile selector, runtime module or inheritance mechanism needed. Inputs,
deadline, observations and stage checks match320 plan; only resolution/description
differ. Full saved-host regression and actual native640 comparison follow.

### Final ordered-release fifteen-minute acceptance

`r36s-dumps/sh3/20261114T053122812199Z-42e95c`, exact2ac6b9... executable,
990s saved hospital route, installed320/30 menu and latest measured1/1 settings.
Live50–975s:27,652completed frames,29.894589FPS, minimum complete1s28/5s29.2,
p50/p95/p99/max33.363/34.804/36.680/53.745ms.461/461alive observations,
321distinct positions, all room160/health199.399994; every sampled30s segment
changes position (minimum3 distinct positions, including partial edge segments).
No menu, death or reset included in this interval. Actual firing separately
proven by final handgun replay; generic ready/action schedule alone is not proof.

Game clock0.999545×wall, refresh60.000390Hz;191CPU/GPU samples all1512/520MHz,
maximum73.333°C.51program restores,zero misses/writes/rejections. No logged ALSA
recovery; this is log evidence, not a new listening claim. Execution/collection
and all stages0, source preserved, ExitProcess0, active frontend, no remaining
runtime process and firmware checks pass. Exact runtime SHA matches host artifact.

190native memory samples: peak VmHWM313524KiB (306.176MiB), minimum system
MemAvailable558700KiB. Latter half05:40:52–05:49:02UTC RSS312216→313524KiB,
range same, rise1308KiB. SwapFree485020→484852KiB (168KiB consumed; not zero).
No native OOM/failure recorded; modest resident growth is not full-campaign leak
or GPU allocation proof. Raw monitor and `memory-summary.json` retained.

Full saved-host regression after640-plan GREEN:10PASS/5.928s,
`.port-cache/optimization-uniforms/final-640-route-regressions.txt`.
640actual comparison starts after sustained host job completes, using final
handgun050230 session whose five seed inputs all match original320 benchmark
byte for byte. Ordinary persistent player state remains separate.

### Final native640 comparison and retained320 profile

`r36s-dumps/sh3/20261114T055246314042Z-4068d8` completes execution/collection0
using final runtime SHA256
`2ac6b9c02579ff37d20a920edde36a203458aeded0806f9e86ffecf4bc512ff9`.
Same180s input plan and original five seed-file hashes as final320 handgun run;
actual session640×480 internal/output,30FPS limit, shadow/flare1/1, A8R8G8B8,
gamma1. Seed identity audit retained at
`.port-cache/optimization-uniforms/final-640-seed-audit.json`.

75–180s:23.196638FPS, minimum complete1s19/5s19.8, completed-frame interval
p50/p95/p99/max42.656/51.373/53.331/82.274ms.41/41alive observations,
40distinct positions, room210/health100. Actual magazine10→7→6→3→2→0,
reload10/reserve30→20, then9→6. Game clock1.000329×wall, refresh60.007728Hz.
All36frequency samples CPU1512/GPU520MHz, maximum75°C;320 comparison maximum
71.25°C. Same sampled clocks, not perfectly identical thermal conditions.
47binary restores/zero misses/writes/rejections; no logged ALSA recovery.
All stages0/source preserved/ExitProcess0/frontend active/no remaining runtime;
firmware checksum checks pass. Raw logs and both summaries retained.

Current native640 therefore fails owner's25FPS floor. Matched320 run gives
29.990378FPS, minimum1s29/5s29.8; final hospital15-minute320 run29.894589FPS,
minimum1s28/5s29.2. Retain measured320internal/640output Performance entry.
Final aggregate separates rejected640 result from six passing warmed320 windows:
`.port-cache/optimization-uniforms/final-profile-evidence.json`.
No sustained15–20FPS window occurs in sampled warmed320 gameplay. Park door25FPS,
first-visit reset/new-game shader stalls (maximum1.231s/1FPS bin), one live park
ALSA recovery and untested campaign areas remain explicit. This is representative
automatic acceptance, not full-campaign, fresh listening or universal lowest-UI
quality acceptance. Issues13/14 remain open; all changes stay local/uncommitted.

Research rechecked2026-11-14 before retaining conditional fallback:

- [Official PortMaster FNA guide](https://portmaster.games/contribute/porting/engines/fna/),
  section `Performance on a handheld GPU`: removing oversized targets, extra
  render-target passes and redundant submissions can matter on Mali. FNA/Mono
  and its2D workload differ from native SH3 D3D8/GLES; reported gains are not SH3
  predictions. No FNA scripts, asset conversion or custom driver changes used.
- [Upstream sh3-nx README](https://github.com/cutarev/sh3-nx), previously reviewed
  source pin `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`: describes first-visit
  shader compilation and later cached visits. Switch/Linux desktop behavior
  motivates cache diagnosis, not R36S frame-time acceptance.
- [Comparable Cuphead releases](https://github.com/wild1walker/portmaster-cuphead/releases),
  current release2026.11.01.2, commit
  `a2e39b5bc192e7bee2d2655a324355c0b9b994b7`: render below display resolution and
  scale to full screen; notes GPU scaling on RK3326. Unity Android/Mono runtime
  differs from this native recompiler; no ABI, scaler or firmware fix copied.
- Searches: `site:portmaster.games performance FNA render resolution GPU profiling`,
  `site:github.com/cutarev/sh3-nx stutter shader cache performance`,
  `site:github.com PortMaster RK3326 GPU resolution 640 320 performance`.
  No exact R36S SH3 same-problem640/30 fix found. Unrelated Box86/Wine, emulator,
  Godot/H700 and PowerVR results do not establish this device's behavior.

External pages treated as research data, no new clone or downloaded script run.
Documentation-only closeout uses local source/link/diff/privacy validation;
no executable behavior changes after640 manifest's observed RED/GREEN and
10-test host regression. No extra native test rerun needed for these report edits.

### Publication approval, 2026-11-14

Owner explicitly approved: "Publish reviewed changes; close #9 only". Reviewed
source, scripts, tests and reports may be committed and pushed; completion and
handoff comments record final commit/evidence. Closure applies only to #9;
#13/#14 stay open for documented profile, first-visit, audiovisual and campaign
limits. Pre-publication diff snapshot matches all64 task-owned paths and contents.
Only publication-status notes change afterwards; no executable change or new
device run. Ignore private data/builds/dumps/caches, exclude unrelated `.DS_Store`.
