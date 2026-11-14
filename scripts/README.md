# SH3 host/device workflow

Selected personal-port folder: `/roms2/ports/sh3`, from local `R36S_PORT=sh3`.
Menu entries: `/roms2/ports/Silent Hill 3 Preflight.sh` and
`/roms2/ports/Silent Hill 3 Runtime Diagnostics.sh`, plus
`/roms2/ports/Silent Hill 3 Graphics Diagnostics.sh`. Preflight checks data;
runtime diagnostics exercise native memory, threads, signals and timers without
rendering. Game entry uses separate `sh3-r36s-game.service`, stops
`emulationstation.service` while game runs, then restores it. Diagnostics leave
frontend running. No runtime mounts, package installs, clock or firmware changes.

## Private configuration

Copy keys from `.env.example` into ignored `.env`; existing owner-provided
connection settings stay local. Values are parsed as data, never sourced/evaluated.
`R36S_HOST` contains SSH destination, optionally `user@host`. `R36S_SSH_PORT`
defaults to 22; `R36S_PORT` is game folder, never TCP port. Password goes from
runtime environment to SSH askpass through private process pipe, never arguments
or logs. Key authentication also works. Dedicated known-hosts file lives under
ignored `.port-cache/ssh/`; accept new host once and reject changed keys.

`SH3_GAME_DIR` optionally selects owner data; default is repo-local
`SILENT HILL 3`. No credentials or private reference paths belong in tracked docs.
Verify `.env`, game data, `tmpRepo/`, builds, caches and `r36s-dumps/` remain ignored
before creating artifacts. Never run host workflow with shell tracing enabled.

## Runs

Use `python3 scripts/host/r36s.py inventory` for target-only inventory. Use
`python3 scripts/host/r36s.py preflight --reviewed-helpers r36s-dumps/sh3/<inventory-run-id>`
to validate local inputs and deploy/run preflight. One unattended invocation handles authentication, SCP, execution and
collection. Codex invokes host script only; all device access belongs to script.
Inventory runs first; review collected installed PortMaster helpers before
preflight sources them. No foreign downloaded script is executed automatically.
Host compares freshly collected helper hashes against reviewed inventory before
sourcing. If a helper sources additional code, extend inventory and review that
code first. Folder changes and helper changes require fresh review, not a bypass.

Each invocation owns `/roms2/ports/sh3/runs/<UTC-run-id>/` and collects into
`r36s-dumps/sh3/<UTC-run-id>/`. Preserve separate stdout, stderr, execution status,
collection status, input/source identity and existing SH3 logs. Prior runs, owner
data and saves remain untouched. Attempt collection even after deployment or
execution failure; distinguish unavailable device from validation failure.
Inventory includes completed menu-run logs under `device/previous-launches/`,
so physical menu tests can be collected through same unattended host command.
Completed detached game sessions also include per-session service recovery logs.
Explicit sh3.ini, savedata/disp.ini, key.ini, every three-digit data slot and
data.sys copies preserve player state; source sessions remain untouched.
Inventory also copies current persistent state/cache and records Linux boot ID.

Scripts live in `scripts/host/` and `scripts/device/`; launcher lives in `ports/`.
Only reviewed project files and explicit native package files deploy. Original
assets do not deploy in these workflows. Missing target tools are recorded, never installed.
Target identity does not prove active SDL backend, GLES operations or gameplay.
Inventory also records installed `perf` version and unprivileged software-event
permission probe. Missing profiler or rejected event stays explicit; no tool
installation or kernel permission change occurs.

Task #5 uses owner-copied `/roms2/ports/sh3/gamedata/sh3.exe` and complete
`gamedata/data/`, then fresh inventory and preflight before game execution.
`SH3_DATA_HASHES=1` makes data checker record SHA-256 identities of available assets,
including failed preflights; hashing never changes originals.
Use `python3 scripts/host/r36s.py preflight --hash-data --reviewed-helpers r36s-dumps/sh3/<inventory-run-id>`
for complete local/target SHA-256 inventory. Allow up to ten minutes for SD reads;
host still collects failed runs. Verify with
`SH3_DATA_EVIDENCE=r36s-dumps/sh3/<hash-run-id> PYTHONPATH=tests python3 -m unittest test_game_evidence.GameDataEvidenceTests -v`.

`python3 scripts/host/r36s.py game --reviewed-helpers r36s-dumps/sh3/<inventory-run-id>`
installs **Silent Hill 3 Game**, then runs 100-second game probe. Latest completed
first checkpoint is copied into new session when available; otherwise probe
uses opening-sequence keys. Captures initial frames then one every 60 frames for
stationary scene comparison; physical menu launch has no image capture. Game receives
normal window-close request at deadline. 145-second watchdog is diagnostic
failure, never clean-exit acceptance. Physical menu launch uses real
controls and upstream launcher. Diagnostic probes own config/logs/saves under
new run directory. Ordinary play uses persistent `sh3/state/`, with 640×480
output; existing owner saves stay separate. Every ordinary launch snapshots
state into its completed run directory without changing prior snapshots.
Game deployment also installs **Silent Hill 3 Performance**. Select this entry
for explicit30FPS pacing and320×240 internal rendering scaled to640×480 output.
Uses same persistent player progress and control mappings. Selecting it writes
320×240 and measured `shadow=1`/`lensflare_ztest=1` into saved display settings,
while retaining brightness, format, mappings and progress. Numeric values match
benchmarked scenes; complete lowest-quality UI mapping remains unverified.
**Silent Hill 3 Game** continues to use saved settings. Ordinary performance play
has no automatic movement or deadline. Automated320×240/30FPS scene plans run
through this installed entry with their existing isolated saves and deadlines.
Current candidate uses `python3 scripts/host/build.py --optimization O3 --lto`;
reproduce checks on that artifact before selecting another compiler profile.
Saved probe also sets `SH3_INTERNAL_RESOLUTION=640x480`. This opt-in acceptance
profile writes complete display defaults and requested render size into session
copy of disp.ini. Native read-only PEEK verifies actual rendering dimensions;
sh3.ini output alone does not establish Internal resolution. Normal physical
launch leaves game graphics options available without this diagnostic override.
Game entry follows reviewed Delver pattern: detached system service survives
frontend's `KillMode=control-group`; per-run recovery marker arms before stop.
Exit trap and privileged `ExecStopPost` restore frontend after exit or crash.
Only frontend stopped by this session is restarted; unrelated helpers survive.
Normal Ports entry starts asynchronously; saved SSH probe sets
`SH3_SERVICE_WAIT=1` and waits for result and recovery. Service logs, cgroup,
frontend state and before/during/after memory snapshots collect under `service/`.
Saved probe also collects five-second CPU/GPU clock, thermal, memory and native
process samples. Read-only monitor owns only its sleep child; neither monitor nor
captures run during ordinary physical play. FPS/heap logging remains enabled.
Select+Start closes game and upstream launcher through native SDL controls;
neither button alone exits. Owner confirmed physical Select+Start return to Ports
in run20261112T204903Z-230962. Later movement/game-clock checks pass representative
cases; current performance and remaining limits in
[issue13 report](../reports/issue-13-performance.md).
Use normal Ports launch for physical movement/exit checks;
do not treat scripted timing as performance evidence. Validate collected boot and
close evidence with
`SH3_GAME_EVIDENCE=r36s-dumps/sh3/<game-run-id> PYTHONPATH=tests python3 -m unittest test_game_evidence.GameSessionEvidenceTests -v`.
Service evidence:
`SH3_GAME_SERVICE_EVIDENCE=r36s-dumps/sh3/<game-run-id> PYTHONPATH=tests python3 -m unittest test_game_evidence.FrontendSessionEvidenceTests -v`.

Unattended SSH preflight sets `SH3_PREFLIGHT_HEADLESS=1`: reports errors in
collected logs without starting PortMaster dialog over active frontend. Installed
menu entry uses normal player message. Physical menu launch/return needs separate
device observation. Preflight starts no gptokeyb process; cleanup suppresses
PortMaster's global gptokeyb kill and restores launcher exit trap after helpers.

Recognized inputs: 3,338,240 bytes with SHA-1
`aa2aca6dba19bf510c9c2e92eefdc15e98266581` (`upstream-aa2aca6d`) or
`d851669ef609b3164e3581aa8dcfbfaec866cb79` (`owner-cd-d851669e`). Exact owner-CD
profile passed upstream patch/PE preconditions; native game code must be generated
from that input. Recognition does not establish runtime or gameplay compatibility.

## Native runtime diagnostics (task #2)

`python3 scripts/host/build.py` generates owner-profile game code and compiles
Linux ARM64 inside pinned reusable Docker environment. Read
[build guide](../docs/agents/builds.md). Final personal package: `dist/runtime/`.
Run build and deployment serially. Build snapshots allowlisted source without
private configuration; only selected executable mounts read-only. Each build
retains logs, status, hashes and package under `.port-cache/builds/<UTC-id>/`.
Verified generation cache reuses only matching input/generator/image and matching
generated file hashes. Previous final packages remain under `dist/runtime-previous-*`.
Debug symbols stay host-only; device receives stripped AArch64 binary.

`python3 scripts/host/r36s.py runtime --reviewed-helpers r36s-dumps/sh3/<inventory-run-id>`
deploys that package into `/roms2/ports/sh3/runtime/`, checks complete ELF dependency
closure, installs `/roms2/ports/Silent Hill 3 Runtime Diagnostics.sh`, invokes it
headlessly and collects launcher results. Each run preserves deployed binary and
build identity in its own payload. Original assets remain host-only. Diagnostics
open no graphics context, mount no runtime, alter no clocks and need no game data.
Firmware SDL and graphics providers stay in place; no private libraries required
unless actual closure demonstrates otherwise. Physical menu return still needs
owner observation; scripted frontend/process evidence supplements it.
Select **Silent Hill 3 Runtime Diagnostics**, not Preflight, for this check.
Refresh frontend game list if new entry is absent. Runtime menu derives package
folder from its own installed location; no host environment needed.

`python3 scripts/host/test-runtime.py` runs real built binary through launcher in
same ARM64 Docker image with PortMaster fixture. No game data or private config
mounts. RED/GREEN logs stay under `.port-cache/runtime-tests/<UTC-id>/`.
These passes establish launcher behavior in Docker, not device compatibility.

`python3 scripts/host/clean-build.py` removes disposable `build/` tree only after
checking no project container runs. `--docker` additionally removes stopped
labelled containers and unused labelled `sh3-r36s-build` images, without force.
Source, generated C, owner data, `dist/`, `.port-cache/` and `r36s-dumps/` survive.
No named volumes or dedicated builder created; shared Docker layer cache remains
untouched. Generation/build caches inside `build/` are disposable.

## GLES diagnostics (tasks #3–4)

`python3 scripts/host/r36s.py gles --reviewed-helpers r36s-dumps/sh3/<inventory-run-id>`
deploys native package, installs `/roms2/ports/Silent Hill 3 Graphics Diagnostics.sh`
and runs GLES probe through same launcher. Uses `/roms2/ports/sh3` and firmware
SDL/EGL/GLES providers. Opens graphics window; frontend remains running. Collects
stdout, stderr, status, generated GLSL, provider mappings, PPM and raw RGBA captures into
run-owned directory. Owner-derived vertex/fragment samples, original quad,
indexed/base-vertex, skinning, precision, culling/scissor/depth/stencil and RHW
depth fallback must all pass before exit0/`gles=PASS`. Final quad presents for
three seconds, then returns through normal PortMaster cleanup. No game-data
upload required; build embeds selected private samples for personal testing.

`SH3_GLES_EVIDENCE=r36s-dumps/sh3/<graphics-run-id> python3 -m unittest tests.test_gles_evidence.GraphicsEvidenceTests -v`
checks independent pixels and actual identity/lifecycle evidence. Resource samples
cover BGRA/packed uploads, palette alpha/selection, mip and lock updates, separate
DXT1/3/5 alpha rules, block edges/tails, framebuffer depth extent, copies, fresh
packed readback, last-presented preview fades and sampler border/filter behavior.
512×512 full-mip uploads log retained source bytes, peak per-level scratch and
logical GPU storage; process peak RSS logged separately. GPU storage excludes
driver padding/metadata. Original bytes retained; unsupported DXT expands during
upload, without offline re-encoding. This probe does not establish gameplay,
complete renderer compatibility, full-game memory fit or performance.

`python3 scripts/host/test-runtime.py` also runs same diagnostic via launcher
with `SH3_GL_BACKEND=desktop`, `SH3_GRAPHICS_REFERENCE=1`, SDL offscreen and Mesa
software rendering inside ARM64 Docker. Desktop uses GLSL430, clip control and
native depth clamp. Captures retained at `.port-cache/runtime-tests/<UTC-id>/desktop-reference/`.
Only `desktop_reference=PASS` may result; software never passes R36S hardware
identity. Ordinary AArch64 game context defaults native GLES; explicit
`SH3_GL_BACKEND=desktop` retains desktop comparison route.

`python3 scripts/host/test-runtime.py --game` includes real owner-data boot,
presentation sequence and virtual-controller exit checks in ARM64 Docker.
`--checkpoint` extends desktop reference to 100-second opening sequence with
sparse captures. `--seed-session <collected-session>` implies checkpoint mode and
replays saved checkpoint at 640×480, matching device Load/movement schedule.
Checkpoint mounts read-only; only fresh session copy receives writes. Review scene
images against device capture and physical observations; timing alone cannot
establish matched interactive state. These references never pass hardware
acceptance by themselves.

Task #6 shared plans live in `scripts/scenes.json`. Desktop:
`python3 scripts/host/test-runtime.py --scene checkpoint-ui --seed-session <session>`.
R36S: `python3 scripts/host/r36s.py game --scene checkpoint-ui --seed-session <session> --reviewed-helpers r36s-dumps/sh3/<reviewed-run>`.
Explicit source seed copies only data.001/data.sys, optional disp.ini/key.ini,
sh3-progs.bin and sh3-gl-cache.bin into run payload; original assets never uploaded.
Omitting both caches produces cold application-cache replay. Completed replay can
carry shader keys and compiled driver programs. Binary cache checks exact driver,
supported formats and shader sources; invalid entries fall back to source compile.
Optional game flag `--prime-program-cache <collected-session>/sh3-gl-cache.bin`
copies only measured compiled programs into existing player state when its cache
is absent. Existing cache, saves and settings remain intact; absent state stays
absent so first-import behavior still works. Host rejects invalid headers or files
above32MiB. Device records result and source/target hashes in
`device/program-cache-prime.txt`; runtime still validates exact driver and sources.
Host records plan/runtime/seed hashes and verifies source unchanged;
device records plan, source checksums and after-run checks. Capture receipts log
frame, SDL ticks, drawable and backbuffer size. Match scene and camera visually;
different frame rates mean equal frame numbers do not mean equal scene times.
Service watchdog allows declared game duration plus90 seconds for startup and
report flush. Device wrapper allows another50 seconds for service stop/cleanup;
host execution allows another40 seconds. Forced timeout remains failure.
`indoor-ui` uses same keys for later checkpoints with map/light. Use
`--scene opening-cutscene` without seed for fresh New Game, difficulty selection
then natural real-time opening sequence; device ignores latest-save fallback.
Opening uses15-frame capture interval for brief hair/camera shots. Other plans
use60; all capture runs are visual evidence, not low-overhead FPS acceptance.

## Launcher tests

`python3 -m unittest discover -s tests -v` runs interpreted host fixtures through
actual launcher with filesystem/PortMaster external boundaries. Confirmed seam:
installed launcher → useful preflight result → cleanup/return. Fixtures test
errors and cleanup only; actual device evidence is required for G1. No executable
compilation occurs in task #1; later build work must read/create build guide and
use explicit Docker `--platform linux/arm64`.

Build/cleanup CLI boundary also confirmed by owner for task #2. Its fixtures check
failed-build evidence and scoped cleanup, with Docker mocked only as external
process. Documentation-only edits use link, content and diff checks instead of TDD.

`SH3_TARGET_EVIDENCE=r36s-dumps/sh3/<run-id> python3 -m unittest discover -s tests -v`
also checks actual collected target observations. These assertions consume real
run evidence, never fabricated target files. Without run path, hardware checks
skip. Owner-CD error fixture uses ignored local executable when available, omits
assets to test missing-data error, and never ships game bytes with tests.

`SH3_RUNTIME_EVIDENCE=r36s-dumps/sh3/<native-run-id> python3 -m unittest discover -s tests -v`
checks actual native diagnostics, target dependency closure, firmware hashes,
frontend process preservation and absence of leftover runtime processes/mounts.

`SH3_NATIVE_PHYSICAL_EVIDENCE=r36s-dumps/sh3/<inventory-run-id>` adds assertion over
collected successful physical diagnostics menu log. Collect after owner observes
frontend return using saved `inventory` command; no original game upload needed.

## Timed checkpoint comparison

`SH3_SEED_SESSION` optionally copies data.001/data.sys, available disp.ini/key.ini
and sh3-progs.bin from collected session into new writable session before launch.
Explicit files only; source save/config/cache unchanged. Detached service forwards
seed/profile/PEEK settings through explicit allowlist. Default Ports launch reuses
player state; diagnostics explicitly request isolated sessions. Native writes
replace save files after successful flush/close; failed replacement keeps prior
file and logs error. Empty startup disp.ini marker preserves last valid settings.
Native Options stages sh3.ini similarly; failed save keeps Options open with
visible error and leaves prior preferences intact.
Empty disp.ini from older physical run means exact lower menu settings are unavailable;
do not assume recorded output resolution equals internal rendering resolution.

Saved device game probe chooses latest successful checkpoint session, verifies
source hashes after replay and records `device/checkpoint-probe.txt`. First replay
has cold application shader-key cache; subsequent replay copies cache generated
by prior replay and records warm state. This is not device power-cycle or vendor
driver-cache reset. Native warm-cache count/build log supplies independent evidence.
Validate collected checkpoint/image/input evidence with
`SH3_CHECKPOINT_EVIDENCE=r36s-dumps/sh3/<game-run-id> PYTHONPATH=tests python3 -m unittest test_game_evidence.CheckpointGameEvidenceTests -v`.

`python3 scripts/host/test-movement.py --seed r36s-dumps/sh3/<inventory>/device/previous-launches/<physical-run>/session`
calibrates timed movement through real game in existing ARM64 Docker environment.
Owner assets/checkpoint mount read-only. Read-only SH3_PEEK observes documented
player coordinates, health and room, plus guest timer counters. Test-only SDL swap
delay varies presentation cost; it never writes guest clocks. Reject runs that
miss live checkpoint, fail to move, end before full input or compare different rooms. Retain private
samples/logs/images under ignored `.port-cache/movement-tests/`.
Calibrated issue #9 baseline reproduces slow motion: same four-second input moves
42.5% as far with delayed presentation. Guest clock advances normally, but
inherited simulation step caps at3 while elapsed ticks exceed3. Local candidate
honors elapsed ticks within133ms bound; representative timing/audio acceptance
recorded locally, publication pending. Runner now also checks sustained wall
contact/timer at320×240 and handgun cadence at640×480. Use collected room210
nightmare checkpoint: inventory path assumes knife equipped and loaded handgun
available. Setup/nonempty-ammunition guards reject unsuitable seeds. See
[issue #9 report](../reports/issue-09-audio-timing.md) for RED/GREEN evidence and
collision/combat/animation/audio limits. Neither this comparison nor native
Docker results establish R36S performance or listening acceptance.

Issue #9 handheld plans `timing-audio-640` and `timing-audio-320` use real pad
input, read-only clock/player/room/dimension observations, no screenshots, and
900-second game deadline and990-second service limit, including launcher wait.
Explicit integer diagnostic deadlines set service limit with90-second allowance;
ordinary launches without deadline stay unbounded.
Both keep640×480 output; selected internal profile applies
only to isolated session copy. Launch each with explicit collected checkpoint:

```sh
python3 scripts/host/r36s.py game --scene timing-audio-640 --seed-session r36s-dumps/sh3/<inventory>/device/persistent-state --reviewed-helpers r36s-dumps/sh3/<reviewed-inventory>
```

Repeat with `timing-audio-320`. Do not add `--physical-controls`: that mode
deliberately removes read-only timing observations. Empty scripted-key plan
leaves real pad usable; owner advances warning/Play/Load. Check walking/running,
wall contact, weapon ready/repeated attacks, music, speech and effects; cross
doors/menu fades and repeat available sound/voice sequences. Note scene, action,
profile and symptom for any loop, dropout or drift. Exit with Select+Start;
deadline exit does not establish physical return. Source saves stay unchanged;
in-session diagnostic progress remains in separate run snapshot. Listening and
observable animation acceptance require owner report, not counter agreement.
Automated `timing-movement-640` and `timing-movement-320` reuse same diagnostics
with100-second duration and four-second movement at75s, loaded from fixed
room210 checkpoint. Keep handheld controls untouched during these runs. Compare
position displacement against original600 units/s baseline, require live state
before/after full input, and inspect wall/game-clock rates and bounded steps.
Validate paired collected runs with
`SH3_TIMING_EVIDENCE=r36s-dumps/sh3/<640-run>:r36s-dumps/sh3/<320-run> PYTHONPATH=tests python3 -m unittest test_timing_evidence -v`.
Checks actual Mali GLES identity, complete input/live state, baseline speed,
wall/game-clock rates, both internal profiles,640×480 drawable, source preservation
and frontend recovery. Listening and physical exit remain separate observations.

## Frame-cost profiling (task #13)

Plans `profile-static-640` and `profile-static-320` replay fixed room210 checkpoint
for100 seconds without movement or screenshots. Use same collected seed and
reviewed inventory for both; keep handheld controls untouched. Example:

```sh
python3 scripts/host/r36s.py game --scene profile-static-640 --seed-session r36s-dumps/sh3/<inventory>/device/previous-launches/<run>/session --reviewed-helpers r36s-dumps/sh3/<reviewed-inventory>
```

Plan's opt-in `profile: true` sets `SH3_PROFILE` to new launch's `frame-times.csv`;
detached service forwards path and ordinary launch collection retains file.
Other plans disable profiling. Ordinary physical controls check clears profiling;
explicit `--physical-profile` keeps it with real pad input. Existing source hashes
and isolated state remain enforced.

Analyze stationary room210 frames from55–95 seconds. CSV reports per-frame wall,
main-thread CPU, draw submission, presentation and swap milliseconds, draw count,
vertex/index upload bytes and actual internal dimensions. Swap is subset of
presentation. Draw includes GL state/shader setup and uploads. CPU-side elapsed
durations include possible driver waits; they are not GPU execution timings.
No forced synchronization or extra readback added. Report p50/p95/p99/max and
clocks/thermals/process observations, match cache/config identities, then change
one measured cost and repeat. Profiling overhead needs comparison with disabled
run before treating instrumentation as free. Docker test alone proves CSV
behavior, not device speed. See [performance report](../reports/issue-13-performance.md).

Renderer optimization checks use forwarding SDL/GL observers in ARM64 Docker:
`tests/uniform-cost.c` counts identical effective uniform payloads per program;
`tests/state-cost.c` counts repeated supported capability toggles. Both forward
every observed call to real Mesa and require existing independent pixel checks
through installed graphics launcher. Run with `python3 scripts/host/test-runtime.py`.
Boundary counts establish removed driver work; actual Mali graphics checks and
matched device profiles establish compatibility and FPS. Neither count alone
passes 30 FPS. Per-slice evidence: [renderer cache report](../reports/issue-14-renderer-caches.md).

`profile-clean-320` repeats same checkpoint, input schedule, resolution and100s
duration as `profile-static-320`, with CSV and CPU sampler disabled. Existing
60-frame PEEK lines append native SDL `wall_ms`; retain only room210 observations
inside55–95s for coarse frame-number/wall-time comparison. Sparse sampling cannot
establish per-frame percentiles. Do not compare emulated game time as wall time.

Linux AArch64 profiling also writes `frame-times.csv.samples` at normal exit:
presenting thread PC and AArch64 link-register return location sampled every10ms
of its CPU time, frame-tagged and named outside signal handler. Return location
is not a stack unwind and may point inside a library. Bounded32768 records; log includes dropped samples and
write status. Handler allocates nothing, takes no lock and performs no I/O.
Use matching build's host-only `sh3.debug` to name native offsets; join frame IDs
to CSV for warmed-window CPU distribution. Abnormal exit can lose samples;
unsupported timer logs unavailable, never substitutes a capability pass.
This diagnostic avoids unavailable target `perf`; no package or kernel changes.

Queued profile runs also write `frame-times.csv.presents.csv` at actual worker
SDL swap completion, with producer-owned frame/room/resolution metadata. Use this
cadence for FPS; producer draw/Present columns measure queue submission and waits.
Explicit `SH3_GPU_PROFILE=1` adds GPU-region report `frame-times.csv.gpu.csv`;
frame profiling alone leaves GPU queries disabled. Eight reusable timer
queries, delayed three frames, poll availability before64-bit result reads;
busy slots skip timing rather than wait. Disjoint intervals are discarded.
Unsupported API/counter bits print `gpu_profile=unavailable`; no GPU pass implied.
Region spans submitted frame commands before swap, including command gaps, and
is not GPU occupancy. No forced GPU finish or pixel capture. Direct diagnostic runs can set `SH3_GPU_PROFILE` to
explicit report path or `0` to disable queries; ordinary unprofiled game does no
query work. Reports and final discard/skip totals flush on orderly worker stop.
Native Mali run `20261113T223112187035Z-7965b3` returns64-bit query data but small
reported intervals do not explain actual swap cost. Treat as raw driver results,
not established whole-frame GPU time. Enabling queries coincides with20.60FPS
versus21.76FPS without them in same stationary640 checkpoint; keep queries off
for acceptance cadence measurements.

For measured real-pad gameplay, use:

```sh
python3 scripts/host/r36s.py game --physical-profile 320x240 --reviewed-helpers r36s-dumps/sh3/<reviewed-inventory-run-id>
```

Use `640x480` for full-size internal comparison; output stays640×480. Profile uses
latest successful checkpoint copied into isolated session, real controls and same
900-second deadline. Adds frame/completion CSVs, room IDs, actual dimensions, CPU
samples and five-second clocks/thermals/process monitor. Disables GPU queries,
scripted input, PEEK, screenshots and FPS/heap console spam. Cannot combine with
scene replay, explicit seed or persistent/import options. Ordinary controls check
and saved player state stay separate. Advance warning/Play/Load manually; spend
at least a minute moving/fighting in owner-reported monster room, plus transitions.
Report room/action and audio/animation/visual symptoms; room IDs in collected CSV
tie feedback to measured cadence. Existing Select+Start return already accepted;
exit when finished so saved host command can collect. Fixture tests prove workflow
only; actual handheld logs and owner report still required.

## Unattended performance routes

`performance-route-320` replays isolated room210 checkpoint for180 seconds with
walking, strafing, weapon ready and repeated fire; captures disabled, frame and
completion CSVs plus read-only player/room/health/ammunition observations enabled.
Plan requests `fps_limit: 30`; `SH3_FPS_LIMIT=30` reaches detached runtime and
paces worker completion without spinning. Ordinary launches retain current default.
Run with handheld untouched:

```sh
python3 scripts/host/r36s.py game --scene performance-route-320 --seed-session r36s-dumps/sh3/<inventory>/device/previous-launches/<run>/session --reviewed-helpers r36s-dumps/sh3/<reviewed-inventory>
```

Inventory/equip sequence assumes original nightmare checkpoint's available handgun.
Verify completed inputs, changing position, live state and actual repeated attacks
from collected evidence. A stuck wall, menu or dead player does not pass route
coverage. Record room visits, actual completion cadence, one/five-second windows,
frame tails, temperatures and frequencies. Other saves require compatibility and
scene checks first; original player state and downloaded archive stay unchanged.
Automatic checks cannot establish new listening or physical-control acceptance.

`performance-route-640` repeats same180s movement/equip/fire sequence at640×480
internal/output with same30FPS pacing and no captures. Use same immutable seed
as320 comparison; verify actual dimensions, room, live movement and ammunition.
This is diagnostic comparison through installed Game entry, not a new persistent
player preset. Existing Performance menu continues to select measured320 profile.

`traverse-route-320` uses same isolated seed workflow for160 seconds, requests30
FPS, walks/strafes and attempts default equipped attacks without navigating inventory.
Use for compatible public saves; verify actual room/position/health after load.
Key replay does not prove an attack or room transition occurred. Run separate
scene captures for identification; performance run keeps captures disabled.

`sustained-route-320` extends generic checkpoint workflow to990 seconds, repeating
walking, strafing and ready/attack inputs through976 seconds. Same30FPS cap,320×240
internal/640×480 output, read-only room/position/health observations and no captures.
Runtime decodes fixed key schedule once, preserving wall-time holds and overlaps;
ordinary physical play never uses this script. Reject dead/stuck/menu intervals
and report cold shader compilation separately from repeated warm play.

`explore-route-320` uses Q/E turns, longer walking/running legs, backing away and
brief action presses for240 seconds, without weapon-ready or inventory input.
Use same isolated seed command with this scene name. Original A/D exploration
stayed room210. Corrected route passes installed-launcher navigation test and
native room210→211 transition; enemies eventually kill player. Review actual
room/health/coordinate evidence, exclude death/menu intervals from gameplay FPS,
and retain transition hitches separately. Wall-contact intervals remain present.

Collected completion reports can be checked locally without device access:

```sh
python3 scripts/host/performance.py r36s-dumps/sh3/<run> --start 50 --end 975
```

Writes `performance-summary.json` in selected run. FPS uses elapsed time between
first/last completed frame; fixed1s/5s windows retain empty bins and exclude partial
edges. All long frames retained. Report includes rooms, internal sizes, frame tails
and20 longest completions. Review actual movement/health/attacks, transitions,
execution/collection status, clocks and thermals alongside cadence; report alone
does not pass gameplay acceptance.

## Physical controls check

Prepare native build and review current inventory helpers before run. Owner must
be ready at handheld; command starts installed game menu and collects after exit:

```sh
python3 scripts/host/r36s.py game --physical-controls --reviewed-helpers r36s-dumps/sh3/<reviewed-inventory-run-id>
```

Uses `/roms2/ports/sh3`, latest successful checkpoint copied into fresh session,
640×480 internal/output, firmware SDL/Mali and same detached game service. Sets
`SH3_INPUT_LOG=1`; removes scripted keys, PEEK, captures and performance sampler.
Physical mode unsets FPS/heap logging too; native stats flag checks presence.
No key injection or keyboard step. Physical A advances warning screen and Play;
load checkpoint with handheld controls. Standard Ports entry remains ordinary
game launch; flag affects this run only.

Game safety deadline900s; systemd service limit990s also covers waiting at launcher.
Deadline or service stop does not pass physical exit. Finish with Select+Start
and observe frontend return before deadline. Host execution limit1080s allows
cleanup and separate result collection; all waits remain inside saved host script.

Check left/right sticks in each direction, d-pad, A/B/X/Y, L1/R1, L2/R2, L3/R3,
Start and Select alone, then Select+Start. Observe movement, camera, dash, action,
weapon ready/attack/equip, search, flashlight, map, inventory, pause and confirm/
cancel. Controls/default-action matrix and scene limits in
[issue #7 report](../reports/issue-07-controls.md). Record actual printed-button
conventions and unavailable actions explicitly. No saved-remapping pass implied.

Evidence: `device/game-probe.txt` records physical mode; `service/physical-controls.txt`
records applied launcher settings; `launcher/stderr.txt` records SDL mapping,
changed six-axis/game-button/POV states and physical exit; service logs record
frontend recovery. Logs prove input delivery; owner observations prove actions.
Regular inventory now collects installed SDL database and EmulationStation input
config under `device/input-configs/`. Validate current sources with:

```sh
SH3_INPUT_INVENTORY=r36s-dumps/sh3/<inventory-run-id> PYTHONPATH=tests python3 -m unittest test_input_evidence -v
```

After complete handheld checklist and physical exit, validate collected input
set, digital-trigger values and frontend cleanup:

```sh
SH3_INPUT_SESSION_EVIDENCE=r36s-dumps/sh3/<physical-run-id> PYTHONPATH=tests python3 -m unittest test_input_evidence.InputSessionEvidenceTests -v
```

Multiple actual runs may be joined with `:` on this host; input coverage combines
only identical runtime builds, every run must restore frontend and preserve
firmware, and final run must exit through physical Select+Start. Example paired
runs and completed matrix in [issue #7 report](../reports/issue-07-controls.md).
This asserts input delivery and lifecycle; actual game-action results still need
owner observations. Missing inputs or final deadline exit leave check failing.

## Persistent save/settings check (task #8)

Use reviewed inventory and current native package. First use can copy an explicit
collected session into absent `/roms2/ports/sh3/state/`:

```sh
python3 scripts/host/r36s.py game --persistent-state --import-session r36s-dumps/sh3/<inventory>/device/previous-launches/<run>/session --reviewed-helpers r36s-dumps/sh3/<inventory>
```

Copies all three-digit savedata slots, data.sys, disp.ini, key.ini, sh3.ini and
both shader-key/compiled-program caches; ignores unrelated files. Records source hashes and verifies source
unchanged after run. Import refuses existing player state; later checks omit
`--import-session`. Source sessions/assets remain untouched. This mode implies
physical controls, clears diagnostic seed/resolution overrides and uses ordinary
player state. Normal Ports entry uses same state without host connection.

Check graphics independently: change rendering resolution in game Options,
choose Exit, confirm Yes, then close with Select+Start. Relaunch and inspect same
Options value; no progression save needed. Also verify selected value after
power cycle. Native launcher Options uses separate sh3.ini preferences.

For progress, cross room boundary, save to spare slot and check available preview.
Exit with Select+Start; collect inventory before power cycle. Power off/on, launch
**Silent Hill 3 Game**, load saved slot, check room/progress/available preview,
then exit. Collect another inventory; different boot IDs establish device restart.
Record unavailable preview behavior explicitly rather than assuming thumbnail
exists. Owner accepts room/play-time identification on tested Load screen for
task #8. To check custom mappings, open Options → Button Config, use R1 to reach
page2, select Dash, confirm with A, then click L3. Dash should show btn11. Choose
Exit/Yes, close with Select+Start, power off/on, reopen same page and inspect
mapping. Optional restore: assign Dash to X, then Exit/Yes. Collect inventory
after exit; inspect key.ini, new boot ID, saved-state hashes and frontend return.
Launcher snapshots preserve
each run separately. Docker failure injection proves native failure path only;
actual device round trip remains required.
