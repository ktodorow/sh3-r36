# Issue #5: first playable checkpoint

Scope: installed Ports launcher, readable initial menus and first interactive
scene through native GLES at 640×480, plus clean frontend return. Full effects,
controller matrix, movies, campaign and 30 FPS acceptance remain later tasks.
Confirmed launcher boundary reused; fixtures cover failures/cleanup, never device
compatibility. Owner approved publication and issue #5 closure on2026-11-12.

Latest status: all four issue #5 milestone criteria pass, including physical
Select+Start/Ports return confirmed by owner. Saved room210 checkpoint replays on
hardware with independently observed640×480 Internal and Output, movement and
orderly close. Application shader-key cold/warm launches and matched stationary
desktop comparison pass. Slow-motion reproduction remains RED; issue #9 timing
and later performance gates are not passed. See issue #5 for final commit and
verified closure state after approved publication.
Earlier sections retain experiment order; final evidence below supersedes earlier
pending states and resolution assumptions.

| Milestone check | Current evidence |
| --- | --- |
| Actual native renderer, desktop route retained | Mali-G31 GLES3.2 device run20261112T214422283309Z-0f4c6c; desktop GL4.5/Mesa reference20261112T214206678794Z. Same native binary/data profile. |
| Internal/Output640×480, readable4:3 menus/scene | Live rendering globals640/480, CreateDevice640×480, drawable640×480; title/menu and matched checkpoint images reviewed. |
| Input, identities, errors, cold/warm, baseline | Physical controls/exit accepted; scripted S changes player X/Z; all79 data SHA-256 match originals; build hash below; cold213744/warm214048 runs, no shader/link/GL fatal; matched images below. |
| Reusable checkpoint/evidence | Original first checkpoint collected in210505 inventory; saved host game workflow replays it, verifies source hashes, collects separate session/service/images. |

## Prerequisites and input

Issues #3/#4 closed with actual hardware evidence. Rechecked prerequisite suite:
47 passing checks, 12 unavailable-environment skips. Fresh target inventory:
`r36s-dumps/sh3/20261112T195307431605Z-d713d8`, execution0/collection0.
Reviewed installed control.txt, device_info.txt, funcs.txt, mod_dArkOS.txt,
PortMasterDialog.txt and mapper.py before sourcing. Helpers unchanged from prior
reviewed inventory. Firmware helpers retain their documented local setup effects;
project starts no global input helper or runtime mount.

Uploaded data preflight: `r36s-dumps/sh3/20261112T195419614385Z-e04ef0`,
execution0/collection0; owner-CD SHA-1
`d851669ef609b3164e3581aa8dcfbfaec866cb79`, 3,338,240 bytes. All 79 required
assets present, 5,208,663,071 bytes, exact per-file size match to local originals.
Full hash run `r36s-dumps/sh3/20261112T200935241496Z-94d0e7` finished
execution0/collection0. Independent Python SHA-256 comparison passes for every
required asset against local originals. Original upload performed by owner via SD.

## Research refreshed 2026-11-12

- [Official PortMaster templates](https://portmaster.games/contribute/porting/script-templates/):
  retain control discovery, get_controls, SDL controller configuration,
  pm_platform_helper and pm_finish lifecycle. Isolate writable state. Do not copy
  template-wide helper kills when this project owns no helper. Firmware SDL/EGL
  and native AArch64 remain selected; template runtime mounts unnecessary here.
- [Upstream SH3](https://github.com/cutarev/sh3-nx), revision
  `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`: retain actual renderer semantics and
  warning/Play/Options flow; scripted SH3_KEYS bypasses launcher for diagnostics.
- [First-hand palette report](https://github.com/cutarev/sh3-nx/issues/1):
  alpha and palette identities matter in actual scenes; task #4 samples are
  prerequisite evidence, not substitute for game-scene comparison.
- [SH2 reference](https://github.com/cutarev/sh2-nx), revision
  `7e69609f3a063fbe24c41d6aa560f14ede578746`, and
  [Cuphead reference](https://github.com/wild1walker/portmaster-cuphead), revision
  `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`: native Linux/context and launcher
  diagnostic patterns only. Different runtime/ABI and game do not prove SH3 passes.
  No reference scripts executed or new clones created.
- Searches: official native SDL2 port templates; upstream SH3 Linux crash/menu
  SH3_KEYS; Cuphead launch64. No first-hand same-game R36S scene fix found.

CCE session recall used. Code searches returned stale ignored cache copies and
truncated chunks; expansion unavailable. Known intended edit paths read directly
after this retrieval limitation, without indexing private configuration/data.

## TDD evidence

1. Requested asset identity on failed preflight: RED missing SHA-256 line;
   GREEN independently known SHA-256 of literal `abc`; review preserves failure
   status and original bytes; preflight suite 17 checks passes.
2. Actual owner-data session with external failing runtime: RED launcher returned
   preflight success without invoking game; GREEN runtime exit7 retained,
   session cwd/config 640×480 and original save preserved; reviewed shared
   diagnostics path unchanged; preflight suite 18 checks passes.
3. Saved game action: RED public CLI rejects game action. Added bounded deployment
   through existing reviewed helper/runtime workflow. Actual game boots via Mali
   GLES3; first scripted run reached readable title/difficulty menus.
4. SD rejected session symlinks before game launch in
   `r36s-dumps/sh3/20261112T195644946431Z-630c5a` (exit3, collection0).
   Minimized through actual launcher with failing external `ln`: RED exit3 instead
   of retained runtime exit7. GREEN launcher uses separate asset root, no symlinks;
   asset loads routed through existing Win32 path conversion. Config/saves remain
   in session directory. Real owner-data ARM64 desktop game also loads assets
   read-only; target rerun `20261112T200009181511Z-d62052` boots game and renders
   menu with no shader failure, exits at deliberate watchdog124, collection0.
   No leftover sh3 process. This timeout is not clean-return acceptance.
5. Desktop game test RED: internal640×480 but output1280×720. Added validated
   output-resolution setting, retained default desktop dimensions when absent.
   GREEN `.port-cache/runtime-tests/20261112T200148022059Z`: actual owner game,
   desktop GL4.5/Mesa, 640×480 presented frame. 28 pass/34 skip in 62-test suite.
   Refactor review: settings applied before launcher creates window; GL paths
   unchanged. R36S menu capture already measured 640×480 from actual drawable.
6. Normal-close probe RED: actual game ignored absent deadline behavior and
   required watchdog124 in `.port-cache/runtime-tests/20261112T200316423972Z`.
   Added deadline through same WM_QUIT handling as SDL window close. GREEN
   `.port-cache/runtime-tests/20261112T200446318916Z`: game requests close after
   six seconds, calls ExitProcess(0), launcher returns through frontend cleanup.
   Target `20261112T200653368971Z-7cf21c` likewise exits0 at 100 seconds, both
   collections0. No game-memory writes or forced checkpoint jumps used.
7. Full-data evidence check RED against size-only preflight: no target hashes.
   Saved optional `--hash-data` workflow records all originals. GREEN independent
   local hash comparison against target run above. Boot/close evidence validator
   rejects watchdog124 run and passes actual normal-close target run.

Capture refactor packs RGB in place and writes complete rows instead of one write
per pixel, preserving byte ordering and dimensions. ARM64 build
`.port-cache/builds/20261112T201002100864Z` succeeds. Existing independent
presentation/quad oracles and real owner game pass in
`.port-cache/runtime-tests/20261112T201455290704Z`: 28 pass, 35 environment skips.
Capture refactor subsequently deployed with native exit combo. Earlier target-tested runtime
SHA-256: `6607b77e406dffbcd79a6217297178b0f0a3059d7e704ddc9841c513099a3550`.

## Actual game observations and remaining acceptance

Owner observed Konami intro, title/menu and game audio during SSH probe. Owner
also observed flashing while EmulationStation remained active. Collected frontend
PIDs remain 504/691 before and after probe; no leftover sh3 PID or new mount,
all firmware library hashes unchanged. Last target frame contains amusement-park
3D opening scene at 640×480, with cinematic letterboxing. This frame does not
establish interactive movement. No shader compile/link failure or fatal recorded.
Nineteen unbridged imports and missing movie CoCreateInstance class remain logged;
campaign reachability and original-movie support remain later acceptance.

Probe reports 6.3/5.9/4.9 FPS and guest heap up to 176 MB, with simultaneous
frontend drawing and per-frame capture. These are diagnostic observations, not
performance acceptance. Desktop GL comparison currently reaches Konami frame;
matched first interactive scene, physical input, cold/warm runs and ordinary
Ports exit remain pending. Do not mark issue complete from boot/intro evidence.

Display-ownership research refreshed for flashing blocker:
[first-hand PortMaster build notes](https://github.com/Cebion/Portmaster_builds/blob/main/portmaster_readme)
describe SSH testing without X11/window manager and frontend interference;
[working native port guidance](https://github.com/djhardrich/3sx-portmaster-rocknix/blob/main/docs/portmaster.md)
describes direct KMSDRM display path. Different firmware/driver, so their service
commands are not copied. Current official template remains lifecycle reference.
Reviewed revisions: Cebion `12e46f672674889aeef67ba22ca24c0cac6b146b`,
3sx `6f5481bae05496bf7db047291450ca41e10edb18`. Raw documents reviewed in full;
no downloaded commands executed.
Searches: `PortMaster SSH emulationstation flickering KMSDRM`, Cuphead
EmulationStation SIGSTOP KMSDRM, official SSH testing guidance. Selected next
check: normal Ports launch, allowing frontend's own display handoff; no firmware
replacement or service stop. Physical observation requested from owner.

Owner subsequently confirmed: scenes fine, game launches, controls work, returns
to Ports after game-menu quit; gameplay very laggy. Physical run
`20261112T201412Z-118956`, collected by inventory
`20261112T202007697233Z-92aae8`, logs native Mali GLES3.2, both resolutions640×480,
PostQuitMessage(0)/ExitProcess(0). No remaining game PID. No new display fault
reported through normal Ports route. Owner requested Select+Start exit before
completion. This expands task's minimum exit behavior, not full control matrix.

Exit-combo research: [official GPTOKEYB documentation](https://github.com/PortsMaster/PortMaster-Website/blob/main/content/markdown/gptokeyb-documentation.markdown)
defines Select+Start convention. [First-hand SoRR failure/fix](https://github.com/thiagobucca/sorr-trimui-knulli-brick/blob/97b91e6a2b5bc7be814e23fd88c9419de37cf694/README.md)
attributes missing combo to absent helper; different keyboard-only engine and
Knulli, so its launcher/library changes do not apply. Working 3sx reference also
checks combo with native controller input. SH3 already reads SDL controllers:
selected native mapped Back+Start detection feeding ordinary window-close path,
with no additional input-helper ownership. No same-game R36S combo report found
in upstream/Cuphead searches. SDL's documented virtual joystick APIs provide
external input fixture inside ARM64 Docker; this is not physical-input acceptance.

Combo test setup first missed single-button phase during loading; corrected
fixture advances only after each phase has been observed. Valid RED
`.port-cache/runtime-tests/20261112T202031667016Z`: Start alone, Back alone, then
both reach actual game, but watchdog124 required. Fixture subsequently required
`SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1` for hidden offscreen Docker window;
physical foreground game does not set this. GREEN actual game
`.port-cache/runtime-tests/20261112T202254879978Z`. Separate warning/launcher test
RED `.port-cache/runtime-tests/20261112T202454691967Z`, then GREEN
`.port-cache/runtime-tests/20261112T202600781727Z`: 30 pass/36 skip. Combo closes
warning/launcher before CreateDevice, or requests ordinary game WM_QUIT; Start
alone and Select alone do not exit. Native build
`.port-cache/builds/20261112T202541429666Z` succeeds. Refactor review retains cached
SDL controller ownership/disconnect handling, with no gptokeyb process.
Physical combo still requires owner confirmation; FN fallback only if necessary.

## Frontend service lifecycle requested by owner

Owner explicitly requested Delver's whole-service stop/restore to free RAM. This
supersedes earlier no-stop SSH diagnostic approach above. Current official
PortMaster templates still govern PM controls/helper cleanup; service integration
is firmware-specific. [systemd 257 documentation](https://www.freedesktop.org/software/systemd/man/257/systemd-run.html)
confirms transient service has detached environment/parent and `--wait` waits
through deactivation. `Type=exec`, UID/GID, supplementary groups, `--collect` and
ExecStopPost match reviewed Delver pattern. Official systemd.service web fetch
timed out; local reviewed pattern and actual target checks remain required.

Reviewed full owner-provided Delver `ports/r36s/Delver.sh`, `run.sh` and
`restore-frontend.sh`; reference HEAD
`9083f5e9c23b63fdc67ae2ce4cbeb374692d10be` does not include all local port edits.
Transfer only detached service, marker-before-stop, cgroup refusal and restoration
checks. Java/Weston/mounted runtime are unrelated to this native SDL2/Mali build.
Delver CCE transport closed; exact known reference files reviewed directly.
No external script executed, no new clone created. Searches refreshed: official
PortMaster `emulationstation.service`, `systemd-run` stop/start; same-game R36S
frontend stop; native KMSDRM frontend interference. No official firmware-specific
recipe or same-game report found. Earlier first-hand native-port reports remain
supporting context, not SH3 acceptance.

Saved inventory extension RED against `20261112T202007697233Z-92aae8` lacking
service data; GREEN `20261112T202649933157Z-41fe4a`: systemd257.13,
emulationstation.service active, MainPID504, KillMode=control-group, systemd-run
present, noninteractive sudo succeeds. SSH probe belongs to separate user scope.
Refactor review: read-only service metadata, no stop command in inventory.

Installed-menu lifecycle external service-manager fixture RED
`.port-cache/runtime-tests/20261112T203206828157Z`: game observes active frontend,
returns9 instead of expected game failure7. GREEN
`.port-cache/runtime-tests/20261112T203310205459Z`: frontend stop → game → frontend
start, original exit7/save retained; 31 pass/37 skip. Recovery helper is idempotent,
per-run marker retained on failed restart; privileged ExecStopPost handles lost
runner. Fixed `sh3-r36s-game` unit prevents simultaneous sessions. Environment
allowlist excludes credentials and inherited loader overrides. Review retains
separate game/service evidence dirs and only restores frontend stopped by session.
Actual service evidence validator RED against earlier concurrent-frontend run;
new saved device run under verification.

GREEN actual detached game run `20261112T203443382440Z-ee2746`: execution0,
collection0, launcher/service collections0. Native game in
`/system.slice/sh3-r36s-game.service`; frontend inactive/MainPID0 during game,
active with new PID after ordinary ExitProcess(0). Both hardware evidence checks
pass; no leftover native PID/new mount and firmware hashes all OK. Available RAM
411,164 → 758,908 KiB after frontend stop: about339.6 MiB freed. Startup readiness
does not mean frontend finished loading all media, so restored memory snapshot is
not steady-state frontend budget. This probe still captured every frame and
reported9.8/9.0/9.2/5.2 FPS across different scenes; not matched performance result.

Owner reported worsened lag while diagnostic probe ran. Per-frame capture invokes
GPU readback plus 921,600-byte SD write; likely diagnostic overhead, not yet proved
sole cause. [Arm pipeline guidance](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-1-checking-the-pipeline)
explains synchronous readback can drain Mali pipeline. [Arm optimization guide](https://developer.arm.com/-/media/Files/pdf/graphics-and-multimedia/Guides/DUI0555C_mali_optimization_guide.pdf),
section10.3.2, likewise recommends avoiding framebuffer reads. Native port
comparables remain SH3/SH2 and reviewed 3sx; no same-SH3 R36S first-hand capture
regression report found. Searches: official PortMaster performance debugging,
PortsMaster screenshot slow, SH3_SHOT, Mali glReadPixels stalls. Unrelated Safing
Portmaster search result discarded. No engine/runtime changes inferred from it.

Sequence-capture regression RED
`.port-cache/runtime-tests/20261112T203534581210Z`: requesting every frame stops
after first10 because modulo-one condition never matches. GREEN
`.port-cache/runtime-tests/20261112T203811747401Z`:31 pass/38 skip. Sequence now
shares GLES-safe RGBA, upright drawable capture routine; independent last-image
comparison matches presented frame. Invalid/nonpositive interval falls back30.
Refactor review removes duplicate raw GL_RGB capture path and centralizes error
handling. Build `.port-cache/builds/20261112T203746211380Z` succeeds.
Saved device probe now uses first10 then every300 frames, with no continuous
capture. Ordinary Ports launch has no image capture or live sampler; FPS/heap
logging only. Five-second read-only performance sampler records clocks, thermal,
system/process CPU and memory; no governor writes. Actual sampler evidence RED
against previous run lacking samples; fresh probe under verification.

GREEN low-overhead target run `20261112T203949961837Z-3fa3a9`: execution and all
collections0; boot, native scene, frontend stop/recovery and sampler checks pass.
No shader/link fatal, same Mali renderer and original data profile, no remaining
game PID, mount or changed firmware library. Captured13 frames versus every
present; timing reports11.7/12.7/12.5/8.2/6.9/6.5 FPS across changing content.
This improves diagnostic rates but does not isolate same-scene speedup or prove
30 FPS. Normal Ports path captures none. Nineteen live native process samples:
RSS89,116 → 308,188 KiB, available memory remains at least550,004 KiB;
SwapFree510,348–512,568 KiB. Busiest thread lifetime-average CPU78.9–99.1%,
CPU1.296/1.512 GHz, GPU400 MHz with sampled load0–54%. CPU temperature70.4–79.2°C,
GPU-zone68.8–76.2°C. Main-thread/driver cost remains leading hypothesis; these
samples do not separate recompiled game, driver and mixer costs. Kernel omits
`/proc/<pid>/io`; repeated unavailable-file messages are nonfatal, so per-process
I/O attribution remains unavailable. No clock or thermal policy changed.

Desktop opening checkpoint command first RED: CLI rejected `--checkpoint`.
GREEN `.port-cache/runtime-tests/20261112T204053313380Z`:100-second actual owner
game, desktop GL4.5/Mesa, same key schedule, orderly ExitProcess0, 31 pass/39 skip.
Reviewed `game-reference/shots/frame03300.ppm`: Heather standing at Lakeside
Amusement Park entrance, Rabbit bench, gate sign, fog and readable4:3 image.
Device sparse `frame00300.ppm` is readable title menu; `frame00600.ppm` still
shows overhead park introduction. Thus desktop and device are not yet matched
interactive frames; do not claim visual parity from these different checkpoints.
Final native SHA-256:
`a888a4fcc658b522702c8dc9c1d3a7181aa197dcae521acb9bdc24d7ed20f593`.

Recovery regression checks include previously inactive frontend and abrupt loss
of entire session process group. External service-manager fixture executes real
ExecStopPost helper; marker removed only after frontend readiness. ARM64 suite
`.port-cache/runtime-tests/20261112T204402267396Z`:33 pass/40 environment skips.
No additional implementation needed for these edge checks. Physical acceptance
validator deliberately fails old menu run without Select+Start evidence. Owner
asked to test updated capture-free Ports entry, same scene, Select+Start return;
reply pending. Updated inventory collects completed session's service logs too.

Remaining task gate: physical exit-combo confirmation, cold/warm first-playable
checkpoint and matched visual evidence. Overall performance still poor; existing
campaign/FMV/effect/saves/control-matrix and30FPS limits remain. No task publication
or closure authorized.

Filesystem blocker research: official templates explicitly explain exFAT lacks
symlinks and show bind-directory fallback. This native port instead separates
asset root from writable cwd, avoiding mounts and duplicate 5 GB copy. Refreshed
searches: `site:portmaster.games exfat symbolic links bind_directories`,
`site:github.com PortMaster "Operation not permitted" "symlink"`, Cuphead exFAT
savedata patterns. No same-SH3 first-hand report found; unrelated Windows results
discarded. Existing collected helper documents same exFAT constraint. External
claims remain research; actual target failure and rerun provide local evidence.

Documentation uses content/link/diff validation; TDD not applicable to prose.


## Physical exit and slow-motion follow-up

Owner confirms updated Select+Start returns to Ports. Physical run
`20261112T204903Z-230962`, collected in
`r36s-dumps/sh3/20261112T205738868340Z-82a0bc`, logs native Mali,
`window close requested: Select+Start`, ExitProcess0 and service restoration.
Physical evidence assertion passes. Owner tested output640×480/16-bit,
in-game rendering512×256, low lens flare and no realtime shadow: smoother,
but movement/animation slow while audio remains normal. Last gameplay samples
13.4–15.0FPS. This trial is not accepted640×480 internal profile or normal-speed
acceptance. No FN fallback needed after successful native combo.

Inventory display-preference assertion RED against prior inventory missing
session files. Allowlisted collector GREEN in
`r36s-dumps/sh3/20261112T210151362271Z-277279`: sh3.ini records640×480,
but game's disp.ini is empty. Empty source is preserved faithfully; exact menu
choices cannot be replayed from it. Nonempty-file assumption removed after actual
source observation. No claim settings persist across sessions.

First checkpoint collection assertion RED against inventory without saves;
GREEN `r36s-dumps/sh3/20261112T210505273186Z-e9a7a2`: session data.0019952 bytes,
data.sys296 bytes, as independently logged at creation by game. Original session
untouched; only explicit preferences/first-checkpoint files collected, no assets.
Refactor review retains completed-session guard and bounded allowlist.

Checkpoint replay launcher test RED: real launcher fails to supply checkpoint to
external runtime. GREEN: optional SH3_SEED_SESSION copies explicit checkpoint,
index and preferences into fresh writable session; source and original data
untouched even when runtime changes its copy and exits7.19 launcher tests pass.
Review keeps default physical launch unchanged and preserves 640×480 output.

Slow-motion research refreshed:
- [Official PortMaster lifecycle templates](https://portmaster.games/contribute/porting/script-templates/)
  provide launcher/environment patterns, no SH3 simulation-clock fix.
- [First-hand SH3 low-FPS slow-motion reports](https://github.com/ThirteenAG/WidescreenFixesPack/issues/285),
  full body/comments reviewed: weak-PC users report slow motion with frame-rate
  fluctuation modifications. This is a different Windows patch/runtime and not
  proof of this port's cause. Widescreen UI render-resolution label can also be
  misleading in modified games; actual resource dimensions remain required.
- [SH3 Enhanced timing source](https://github.com/amiraliuks/silent-hill-3-enhanced/blob/297ab43fd95365b10190be6e15e67b61faec4e0d/src/patches/frame_rate.cpp),
  revision297ab43fd95365b10190be6e15e67b61faec4e0d, reviewed only, no code executed.
  Windows x86 patch signatures are research, not native ARM64 acceptance.
- [SilentHillDatabase PC addresses](https://github.com/Polymega/SilentHillDatabase/blob/154cc94e6ea596b0fed2d9754b450fb738f21724/SH3/SH3%20PC%20memory%20addresses),
  revision154cc94e6ea596b0fed2d9754b450fb738f21724: fixed player X/Z and health
  addresses offer read-only movement observations. Heap addresses are not assumed
  portable; validate actual checkpoint/input before drawing timing conclusion.
- SH2 release notes distinguish movie timing from game timing; no FMV fix copied.
  Current SH3/SH2/Cuphead/Delver comparisons remain runtime-specific references.
  Searches: SH3-nx slow motion/timing; SH2-nx fps speed; PortMaster performance
  frame-rate game-speed; SH3 PC player coordinates. No same-SH3 R36S report found.
  Irrelevant SH1 decomp/Switch emulator results discarded. No new clones or
  downloaded scripts executed; external content treated as untrusted research.

Automated movement comparison being calibrated through launcher with collected
checkpoint and original assets mounted read-only in existing ARM64 Docker image.
External SDL swap delay is test-only stimulus, never guest-clock modification.
FPS alone does not measure simulation speed; exact movement must compare before
any speed adjustment. No timing fix or new hardware acceptance claimed yet.

Calibration evidence: runs `20261112T210703562290Z`, `20261112T210836237690Z`,
`20261112T211226270065Z` and `20261112T211642153000Z` under ignored
`.port-cache/movement-tests/` fail setup, not simulation-speed assertions. Repeated
intro Return inputs can select New Game before planned Load input; room210
checkpoint and room227 opening scene are not comparable. Last reference confirms
S moves player from checkpoint; arrow keys alone do not. [PC control reference](https://www.silenthillmemories.net/sh3/playing_the_game_en.htm)
lists W/S movement and arrows for menus, validated against actual game movement.
Removed repeated early Return inputs for next calibration. No failed setup is
reported as reproduced slow-motion defect or TDD RED for a timing fix.

First valid movement repro: `python3 scripts/host/test-movement.py --seed
r36s-dumps/sh3/20261112T210505273186Z-e9a7a2/device/previous-launches/20261112T204903Z-230962/session`.
Evidence `.port-cache/movement-tests/20261112T211845075305Z`: both room210,
health100, same initial coordinates and four-second S input. Reference distance
about2400 units (600/s); delayed SDL presentation about960 units (240/s), ratio
0.39998149. Actual assertion fails `movement slows when presentation is slow`.
External delay begins after checkpoint setup; no clock/input mutation inside game.
This reproduces speed dependence in native desktop runtime, not target performance
acceptance. Repeat removing screenshot capture before attributing cause. Original
full game boot/load dominates116.7-second paired run; measured input itself4s.

Screenshot-free repeat `20261112T212104631495Z` remains RED, but its last sparse
sample at tick3293 precedes full input completion; 0.24998843 ratio understates
complete delayed movement and is not accepted final measurement. Added longer
66-second run tail and explicit final tick>3420 guard, preserving four-second
input. Screenshot capture removed permanently from movement measurement.

Ranked predictions shown before code/counter probes: fixed simulation step per
render frame; lost elapsed time in timer bridge; reduced scripted key hold time.
Generated timer counters advance60 ticks per monotonic second in both runs.
Source trace `sub_005F15E0` in `src/recomp/gen/recomp_0030.c` limits adaptive
simulation state at0xBCC630 to3, feeds it to timer-mode0x72C7E8 and animation
update `sub_0060DA50`. Added these existing read-only PEEK addresses to next run;
no timing code changed. CCE returns compressed generated/cache matches without
usable expansion, so intended source files reviewed directly for precise trace.

Completed-input, screenshot-free repro `20261112T212451854654Z` is RED on actual
speed assertion,132.7s paired boot/load+measurement. Both room210, identical
starting X/Z/health; last delayed sample tick3777 exceeds completed-input guard.
Reference599.9967 units/s; delayed239.9876 units/s; ratio0.39998149. Delayed game
reports elapsed_ticks7 while simulation_step/timer_mode remain3; monotonic clock
and timer total still advance60 ticks/s. Source clamp3 therefore explains lost
simulation progress below roughly20 presented frames/s. This is native desktop
reproduction of reported symptom, not exact target-speed measurement. Inference
for14–15FPS is about70–75% intended speed when same limiter applies; target's
exact value still needs matched measurement. No multiplier or cap change applied:
large simulation steps require collision/animation/combat regression work under
issue9; performance optimization and30FPS remain subsequent gates.

Internal-resolution check through actual launcher is RED in
`.port-cache/runtime-tests/20261112T212954328111Z` and
`20261112T213103989020Z`: output640×480, but game rendering globals0x72BFD0/D4
initialize512×512. Optional first-playable640×480 profile now being tested through
session-owned disp.ini, preserving normal Ports trial and source preferences.
Primary resolution research: [WidescreenFix source](https://github.com/ThirteenAG/WidescreenFixesPack/blob/f398c4d75aa2674bf0c3348ec92eecc96305a742/source/SilentHill3.WidescreenFix/dllmain.cpp)
(current revisionf398c4d75aa2674bf0c3348ec92eecc96305a742 is reorganized into
modules, unlike indexed older source); [first-hand menu-label issue571](https://github.com/ThirteenAG/WidescreenFixesPack/issues/571)
body/all comments reviewed. Menu labels can differ from active rendering size;
original generated setters/getters confirm selected executable's addresses.
No Windows patch or fetched script executed. Upstream SH3 README also confirms
W/S movement; [reference](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98).

## Saved-checkpoint acceptance follow-up

Internal-resolution profile first remained RED with minimal disp.ini
(`20261112T213145863926Z`): original game treated incomplete preferences as failed
prior launch and restored safe512×512 defaults. Complete original-format record
plus requested640×480 becomes GREEN in
`.port-cache/runtime-tests/20261112T213244179402Z`:33 pass/44 environment skips;
read-only native globals0x72BFD0/D4 report640/480. Existing nonempty preferences
retain other fields; only session-owned resolution entry changes. Profile opt-in,
never timing patch, lowest-graphics certification or persistent player settings.

Detached-service checkpoint/profile propagation test RED in
`20261112T213329982661Z`: external runtime lacks seed because service allowlist
drops variable. GREEN `20261112T213418644904Z`:34 pass/44 skips. Minimal explicit
SH3_SEED_SESSION, SH3_INTERNAL_RESOLUTION and SH3_PEEK allowlist; no credentials or
loader-override forwarding. Source checkpoint unchanged, frontend restored.

Warm-cache launcher fixture RED before copying sh3-progs.bin; GREEN20 launcher
checks in `.port-cache/issue-05-checkpoint-fixtures.txt`. Copy remains explicit
and source cache unchanged even when runtime updates writable copy. This is
upstream shader-key cache, not persisted vendor program binary.

Actual checkpoint replay test RED against old opening-only run: room210 never
observed. Saved device script now stages latest completed checkpoint, records
cache state, checks original source hashes afterward, loads through game menus
and applies four-second S input at75 seconds. Native PEEK only reads selected
original-executable globals; no forced room/camera/state writes.

Cold application-cache replay `r36s-dumps/sh3/20261112T213744550184Z-ab6afe`:
room210, initial X19353.65625/Z−15058.783203125, health100, Internal640×480,
Output640×480 on Mali-G31 GLES3.2; input changes coordinates. Normal ExitProcess0,
execution/launcher/service/all collections0, source hashes unchanged. No fatal,
shader compile/link or GL error. Scene reports8.5–9.4FPS, not performance pass.

Warm replay `r36s-dumps/sh3/20261112T214048256326Z-41abff` repeats same accepted
state/input/lifecycle. Source was previous completed replay; native cache log:
31 records,13 programs built up front in591ms. Scene8.0–9.0FPS. Application cold
means no copied sh3-progs.bin; no device power-cycle or vendor-cache purge done.
Framebuffer capture and five-second sampler make these diagnostic rates, not
matched performance benchmarks. Original checkpoint/config/cache hashes all OK.

Desktop seed CLI test RED: --seed-session unrecognized. GREEN public workflow
in `.port-cache/runtime-tests/20261112T214206678794Z`:81 tests,34 pass/47 skips.
Full100-second actual-game desktop run matches640×480 and room210 initial X/Z;
read-only source checkpoint hashes unchanged. Stationary capture candidates
frame02400/frame02700/frame03000. Refactor review retains read-only mount and
explicit seed path; no production runtime changes needed.

Image-presence check independently RED against initial cold replay: every300-frame
capture misses settled original pose before movement. Saved probe changed to
one image every60 frames; normal physical play still has no capture or monitor.
Next hardware run verifies settled image, then visual comparison.

GREEN final image run `r36s-dumps/sh3/20261112T214422283309Z-0f4c6c`:
checkpoint image now available before input; both checkpoint assertions pass.
Warm cache34 records,13 built in593ms. Initial live pose stable through
frame01200; later S input moves player. ExitProcess0, execution and every collection0,
frontend stopped during game/restored afterward, no leftover game PID/new mount,
all firmware library and original checkpoint/config/cache hashes unchanged.
No fatal, shader compile/link failure or GL error. Missing optional key.ini falls
back to defaults; known missing movie bridge remains later media work.

Matched image review:
- Desktop `.port-cache/runtime-tests/20261112T214206678794Z/game-reference/shots/frame02700.ppm`.
- Device `r36s-dumps/sh3/20261112T214422283309Z-0f4c6c/launcher/shots/frame01080.ppm`.
- Both room210, X19353.65625/Z−15058.783203125, health100, Internal/Output640×480.
  Same camera/framing, Heather silhouette, gate/doors/fences/lamps, ground texture,
  fog and translucency visible without material first-scene discrepancy. Noise,
  fog motion and idle pose differ because captures are not synchronized animation
  ticks; no pixel-identity claim or complete-effects acceptance.
- Device `shots/frame00600.ppm` has readable title and New Game/Load/Options/Exit
  labels at correct4:3 aspect. Ordinary first scene has no persistent on-screen
  HUD; full map/inventory/control/effect matrix remains later acceptance.
- Local PNG review copies: `.port-cache/issue-05-device-checkpoint.png`,
  `.port-cache/issue-05-desktop-checkpoint.png`, `.port-cache/issue-05-device-menu.png`.
  Original PPM/save/assets remain private/ignored; no game imagery/data committed.

Refactor review retained one shared launcher, explicit copied files/environment
allowlist, run-owned writes and independent real checkpoint/input observations.
Sparse-capture validator replaced old hardcoded300-frame metadata requirement
after observed false failure against valid60-frame run; now checks actual image
gaps at least60 frames after startup. Both historical300-frame and current60-frame
evidence pass. No new production change in this validation refactor.

Final relevant checks:
- `.port-cache/issue-05-final-host-tests.txt`:82 tests,25 pass/57 environment skips.
- `.port-cache/runtime-tests/20261112T214206678794Z`:81 tests,34 pass/47 skips;
  actual owner game, virtual exit combo, service recovery, native/graphics desktop
  regressions; host seed workflow assertion also passes, source hashes unchanged.
- `.port-cache/issue-05-final-device-tests.txt`:8 actual checkpoint, physical combo,
  frontend lifecycle, firmware/process and sparse-monitor evidence checks pass.
- Independent uploaded-data identities and prerequisite G3 operations previously
  passed; shell/Python syntax, ignore coverage and git diff whitespace checks pass.
- Opt-in movement reproduction intentionally fails original-speed assertion in
  `.port-cache/movement-tests/20261112T212451854654Z`; no speed-fix claim.

Review patch: `.port-cache/issue-05-review.patch` includes task-owned files only.
Final native binary SHA-256 remains
`a888a4fcc658b522702c8dc9c1d3a7181aa197dcae521acb9bdc24d7ed20f593`,
build `.port-cache/builds/20261112T203746211380Z`; source/runtime unchanged since
that build. Final640×480 scene8.9–9.4FPS in sparse diagnostic, explicitly unsuitable
as normal-speed or30FPS pass. No Full port/G4 acceptance from this milestone.
Owner explicitly approved publishing and closing this milestone on2026-11-12.
Full port acceptance and later timing/performance tasks remain open.
