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
Explicit sh3.ini, savedata/disp.ini, data.001 and data.sys copies preserve display
preferences and first checkpoint for replay; source sessions remain untouched.

Scripts live in `scripts/host/` and `scripts/device/`; launcher lives in `ports/`.
Only reviewed project files and explicit native package files deploy. Original
assets do not deploy in these workflows. Missing target tools are recorded, never installed.
Target identity does not prove active SDL backend, GLES operations or gameplay.

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
controls and upstream launcher. Each session owns config/logs/saves under its
new run directory, with 640×480 output; existing owner saves stay separate.
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
in run20261112T204903Z-230962. Normal game speed remains unpassed.
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
Explicit source seed copies only data.001/data.sys, optional disp.ini/key.ini and
sh3-progs.bin into run payload; original assets never uploaded. Omitting program
cache produces cold application-cache replay; seed from completed replay includes
warm cache. Host records plan/runtime/seed hashes and verifies source unchanged;
device records plan, source checksums and after-run checks. Capture receipts log
frame, SDL ticks, drawable and backbuffer size. Match scene and camera visually;
different frame rates mean equal frame numbers do not mean equal scene times.
Watchdog follows declared duration plus45 seconds; forced timeout remains failure.
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
seed/profile/PEEK settings through explicit allowlist. Default Ports launch still starts fresh.
Empty disp.ini from physical run means exact lower menu settings are unavailable;
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
Calibrated comparison currently reproduces slow motion: same four-second input
moves about40% as far with delayed presentation. Guest clock advances normally,
but inherited simulation step caps at3 while elapsed ticks exceed3. Test remains
intentionally RED; no game-timing patch applied. See issue #5 report; intended
speed, collision/combat/animation checks and performance remain issue #9/later work.
