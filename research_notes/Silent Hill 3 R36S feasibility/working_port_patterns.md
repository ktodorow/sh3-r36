# Reusable lessons from Delver and Cuphead

Reference-root names are portable locators; actual user-specific paths stay local. See [locator definitions](../Silent%20Hill%203%20R36S%20spec/source-checks.md).

## What does successful Delver port establish about actual R36S target?

### Takeaway

Cached physical-device logs establish working **Linux aarch64 + proprietary Mali-G31 OpenGL ES 3.2** path on this owner's R36S, plus separate GL4ES path exposing OpenGL 2.1. Native GLES 3.2 is measured capability of October firmware, not merely silicon specification; current firmware must be checked again before choosing exact shader/API subset.

### Cited Findings

- Requested Delver worktree exists at `DELVER_REPO`; metadata `git rev-parse HEAD` returned `9083f5e9c23b63fdc67ae2ce4cbeb374692d10be`. Remote points to `ktodorow/delverengine-mp`; worktree contains substantial uncommitted R36S changes and untracked `ports/`, `docs/`. HEAD alone does **not** identify tested port version. [Upstream snapshot](https://github.com/ktodorow/delverengine-mp/tree/9083f5e9c23b63fdc67ae2ce4cbeb374692d10be); local metadata collected during research, 2026-11-11.
- Existing cached device report records kernel `4.4.189`, aarch64, Debian 13/trixie and Linux-visible `MemTotal: 916912 kB`. EGL/GLES libraries point to proprietary `libMali.so`; installed library includes `libmali-bifrost-g31-rxp0-gbm.so`. Device report (`DELVER_REPO/.port-cache/device-tests/device-report.txt:2`), OS at line 4, RAM at line 19, library links at lines 57–68.
- Native context probe reports `GL_VENDOR=ARM`, `GL_RENDERER=Mali-G31`, `GL_VERSION=OpenGL ES 3.2 v1.r13p0-01rel0.8747d14aec16ec21ac2b2da252c4ec5f`. Firmware metadata reports dArkOS `09022026`, `CFW_GLIBC=241`, aarch64, armhf and aarch64 libraries available, 640×480 panel. `CFW_GLIBC=241` is PortMaster metadata, not independently rerun `ldd --version`. Native probe (`DELVER_REPO/.port-cache/device-tests/cpu7-final-native-probe.log:314`), metadata at lines 38–50.
- Default GL4ES probe instead reports vendor `ptitSeb`, renderer `GL4ES wrapper`, version `2.1 gl4es wrapper 1.1.7`. **Wrapper's desktop GL version must not be confused with underlying Mali GLES version.** Default probe (`DELVER_REPO/.port-cache/device-tests/cpu6-final-default-probe.log:318`).
- Known GL4ES runtime uses GLES 2.0 backend; detection reports full NPOT, highp fragment floats, uint element indices, packed depth/stencil, depth textures, texture RG, float/half-float color buffer extensions. It exposes one color attachment/draw buffer, 8192 maximum texture dimension, 16 vertex attributes and 15 varying vectors. These are **this wrapper configuration's reports**, not exhaustive native GLES limits. GL4ES diagnostic (`DELVER_REPO/.port-cache/device-tests/fixed-render-final-gl4es-recovered.log:230`), limits at lines 254–264.
- Delver uses ARM64 Java 17.0.13, libGDX 1.12.1 and LWJGL 3.3.3 ARM64 native libraries. Integrity manifest also identifies mounted WestonPack `weston_pkg_0.2.squashfs` and Zulu17 runtime images with recorded SHA256 hashes. This is evidence for tested runtime packaging; Java/LWJGL stack is specific to Delver. Manifest (`DELVER_REPO/.port-cache/device-tests/final-device-integrity.json:1`), runtime log (`DELVER_REPO/.port-cache/device-tests/cpu7-cap30-512.log:236`).
- Tested native-GLES display route uses WestonPack `headless noop kiosk crusty_x11egl`, proprietary system EGL/GLES, and Crusty SDL2 backend. GL4ES route uses `crusty_glx_gl4es` with `gl4es_glxpass`/`crusty_glx` libraries. This is tested infrastructure, not proof SH3 needs compositor or Crusty. Native invocation (`DELVER_REPO/.port-cache/device-tests/fixed-render-gles-precision.log:85`), GL4ES route (`DELVER_REPO/.port-cache/device-tests/cpu6-final-default-probe.log:69`).
- Delver GLFW/EGL path encountered 25 raw EGL configs but zero matching window configs; port-local diagnostic proxy adjusted reported surface mask from 2 to 6. This is concrete **shim/configuration-contract** problem; failure creating context did not imply GPU lacked GLES. Config diagnostic (`DELVER_REPO/.port-cache/device-tests/fixed-render-gles-precision.log:270`), mask adjustment at line 288. CCE decision `c7b50cf1226a` additionally records GLES-only libGDX initial-clear override and shader precision repairs; exact source not retrieved through current CCE index.

### Inferences

- For SH3, first try native Linux aarch64 build and explicit GLES 3.x backend against actual Mali capabilities. GL4ES 2.1 wrapper cannot be assumed to supply source renderer's desktop GL 4.5 contract.
- Prefer direct SDL2/EGL/KMSDRM if SH3's existing Linux backend can support it. Use known WestonPack/Crusty route as alternate display integration or diagnostic baseline if direct path fails; do not copy Delver's Java dependencies.
- Keep device graphics libraries outside bundled override set initially. Record exact vendor libraries, ELF ABI and runtime hashes; isolate candidate loader paths per port. Delver's proxy work is evidence to inspect window/config flags before changing firmware or declaring GPU unsupported.

### Gaps

- Historical logs date 2026-10-19 through 2026-10-22; no device contacted in this research. Owner's current “latest dArkOS” image, live driver and GL extensions may differ.
- Native GLES extension/limits dump not found in selected cached probes. GLES 3.2 version string alone does not establish all optional extensions, render-target formats, buffer sizes or specific shader compatibility required by SH3.
- Delver CCE namespace is named/indexed for `delverengine-mp`, and queries retrieve sibling multiplayer material rather than actual worktree's untracked R36S launcher/build source. `expand_chunk` with returned `file:line` identifiers yielded `Chunk not found` in both reference projects. Therefore known cached **diagnostic data** were inspected by exact paths discovered via CCE memory; no source-reading bypass used. Exact native compiler image/sysroot and current launcher implementation remain unverified here.

## Which performance and validation methods transfer?

### Takeaway

Transfer controlled benchmark method, diagnostic ownership and resolution separation. Do not transfer Delver/Cuphead frame rates into SH3 forecast: engines, renderers and workload differ.

### Cited Findings

- Earlier fixed-scene Delver comparison recorded median 21.64 FPS on recovered GL4ES versus 25.62 FPS native GLES with shader precision fix; native VSync-off median 25.13 FPS. These are historical **same-scene samples**, not latest optimized release acceptance. Comparison data (`DELVER_REPO/.port-cache/device-tests/render-comparison-summary.json:1`).
- Later private prototype stamped `2026-10-22T12:23:12Z` used **world 512×384, UI/panel 640×480, linear filter**, native GLES, 30 FPS cap. Warm benchmark windows report approximately 29.94–30.07 FPS; warm-up includes slower samples. UI viewport check and bounded render benchmark passed. This demonstrates internal-resolution tuning in Delver, **not 640×480 internal 30 FPS or full-campaign acceptance**, and says nothing quantitative about SH3. Version stamp (`DELVER_REPO/.port-cache/device-tests/cpu7-cap30-512.log:28`), exact render size (`DELVER_REPO/.port-cache/device-tests/cpu7-cap30-512.log:375`), warm windows at lines 385–408, pass markers at lines 412–413.
- Frame logs track p50/p95/p99/max frame duration, render time, CPU time, GC and heap size rather than average FPS alone. Diagnostic memory samples include process RSS/VmSwap, system available RAM, CPU/GPU clocks and thermal zones; example native sample shows CPU 1.512 GHz and GPU 400 MHz with already warm thermal readings. Frame log (`DELVER_REPO/.port-cache/device-tests/cpu7-cap30-512.log:385`), memory telemetry (`DELVER_REPO/.port-cache/device-tests/fixed-render-gles-memory.jsonl:1`).
- Final integrity record reports frontend active, game inactive, no owned runtime mounts, no temporary paths, and hashes of saves, engine files and shared runtimes. Native context probe also ends with frontend active. Integrity record (`DELVER_REPO/.port-cache/device-tests/final-device-integrity.json:1`), frontend return (`DELVER_REPO/.port-cache/device-tests/cpu7-final-native-probe.log:422`).
- Cuphead's developer docs describe alternating configurations under matched thermal conditions and deterministic screenshot comparison; tests are engine-specific. [Cuphead technical notes, measurement section](https://github.com/wild1walker/portmaster-cuphead/blob/a2e39b5bc192e7bee2d2655a324355c0b9b994b7/docs/technical.md#tests-and-measurements).

### Inferences

- SH3 acceptance should use owner's confirmed target: full game at stable 30 FPS, lowest graphics, prefer 640×480 internal, 320×240 fallback. Record internal 3D size separately from panel/UI dimensions in every benchmark; 320×240 has one quarter of 640×480 pixel count, but CPU/game logic costs will not drop fourfold.
- Build reproducible scene/save/camera test set covering fog, flashlight, shadows, transparent effects, cutscenes and room transitions. Capture frame-time tails, RAM and thermal/clock behavior after warm-up; compare renderers with same assets and state.
- Keep bounded context triangle → asset boot → one room → sustained representative gameplay → campaign acceptance gates. Assert controller/audio readiness, save round trip, exit to frontend and suspend/resume; each catches failure classes absent from launch-only smoke.
- Before implementation, recommend a small SDL2/EGL capability probe launched through intended PortMaster environment: report actual SDL video backend, EGL vendor/version/config, GL vendor/renderer/version/GLSL/extensions, UBO/SSBO/texture-buffer limits and supported target formats needed by source renderer. No firmware writes, package installation or clock changes required. Its implementation and device launch remain future work, not performed research.

### Gaps

- No SH3 benchmark exists on R36S. Stable 30 FPS remains acceptance goal, not established feasibility.
- Owner additionally requires all original FMVs, campaign audio, controls and saves. Neither inspected Delver diagnostics nor Cuphead launcher establishes SH3 FMV codec/container compatibility. Cuphead build docs mention bundled video-decoder licences, but its Android/Unity video path is not evidence SH3's FMVs work. Source/runtime researcher must identify SH3 codec and playback backend; full-port roadmap must include all-FMV playback and audiovisual synchronization tests.
- Selected data are private diagnostics, not full campaign or sleep/resume certification. Later diagnostics may exist; this task did not exhaust entire cache or silently treat earlier performance samples as latest state.

## Which Cuphead build and PortMaster patterns should SH3 reuse?

### Takeaway

Reuse launcher, game-data separation, resumable setup, logs and cleanup conventions. Cuphead's Unity Android runtime, Mono bridge and conversion machinery do not apply to SH3's static-recompiled native engine.

### Cited Findings

- Local Cuphead checkout HEAD is `a2e39b5bc192e7bee2d2655a324355c0b9b994b7`, remote `wild1walker/portmaster-cuphead`; only `.gitignore` modified and `AGENTS.md` untracked at research entry. Upstream files were fetched at exact same commit after CCE previews proved insufficient. [Pinned checkout](https://github.com/wild1walker/portmaster-cuphead/tree/a2e39b5bc192e7bee2d2655a324355c0b9b994b7).
- Launcher locates PortMaster control directory, sources `control.txt` and firmware mod file, calls `get_controls`, captures log and routes by **available userland loader**, not CPU name. It detects `/lib/ld-linux-armhf.so.3`, keeps existing setup's route and sets `PORT_32BIT` before firmware mod handling. [Cuphead.sh, lines 3–32](https://github.com/wild1walker/portmaster-cuphead/blob/a2e39b5bc192e7bee2d2655a324355c0b9b994b7/pm/cuphead/Cuphead.sh#L3).
- 32-bit launcher contains kernel-gated dArkOS audio workaround: pre-5.6 kernels route raw PCM through system aplay, direct hardware first and fallback otherwise; this addresses 32-bit ALSA ioctl mismatch. It then starts exit hotkey helper, calls `pm_platform_helper`, runs process and finishes through `pm_finish`. **Do not copy this workaround into ARM64 SH3 without reproducing same fault.** [Cuphead.sh, lines 99–114](https://github.com/wild1walker/portmaster-cuphead/blob/a2e39b5bc192e7bee2d2655a324355c0b9b994b7/pm/cuphead/Cuphead.sh#L99).
- Separate 64-bit route keeps data and setup markers under its own directory, starts `ua_host64` with platform helper and calls `pm_finish`; it does not prepend 32-bit library directories. [64-bit launcher](https://github.com/wild1walker/portmaster-cuphead/blob/a2e39b5bc192e7bee2d2655a324355c0b9b994b7/pm/cuphead/cuphead/launch64.txt).
- Cuphead uses Unity's ARM Android player hosted on Linux; release accepts owner's macOS game data, not Windows Direct3D-only shader assets. Most performance claims concern RG34XX-SP/H700, not R36S. Therefore success is evidence for **game-specific runtime adaptation**, not generic SH3 compatibility. [README, requirements](https://github.com/wild1walker/portmaster-cuphead/blob/a2e39b5bc192e7bee2d2655a324355c0b9b994b7/README.md#what-you-need).
- Developer build docs support host conversion on Mac/PC and deployment of prepared folder, require external portmaster-unity checkout, and package a static aarch64 setup helper. They document third-party licence collection and game-file exclusion. This dependency is Cuphead-specific; SH3 should use its native build chain. [Building notes](https://github.com/wild1walker/portmaster-cuphead/blob/a2e39b5bc192e7bee2d2655a324355c0b9b994b7/docs/building.md).
- CCE-indexed commit `f1df814` explains why sourced helpers use `.txt`, keeping only `Cuphead.sh` visible in firmware Ports menus. [Commit](https://github.com/wild1walker/portmaster-cuphead/commit/f1df814); launcher sources `launch64.txt`, `setup/cpu.txt` rather than running independent menu entries.

### Inferences

- Proposed SH3 personal-port layout: `ports/Silent Hill 3.sh` plus `ports/sh3/` containing ARM64 ELF, private dependency directory if required, settings, logs, saves and owner-supplied game data. Names are recommendation, not accepted architecture.
- Launcher should use PortMaster-provided directory/control abstractions, explicit GLES environment, mapping and exit helper; include cleanup for owned processes/mounts and return to frontend. Use helper `.txt` files only if launcher actually sources them; avoid cosmetic rename of executable utilities.
- Match architecture of executable **and all dependencies**, EGL provider, libc minimum and kernel interfaces. Cuphead's availability checks illustrate why “both ARM64” is insufficient. Choose SH3 Linux aarch64 toolchain/sysroot explicitly; no reason to inherit 32-bit runtime or Unity conversion.
- Prepare assets/build on host initially, validate exact expected game binary/data hashes before target run, leave original assets read-only, keep saves separate. Add resumable on-device setup only if personal-port workflow benefits; public PortMaster submission is later scope.
- Preserve SDL gamepad mapping via PortMaster; audit SH3 controls for positional A/B conventions and all normal play actions. Exit helper should target exact executable name and perform orderly shutdown where possible.

### Gaps

- Cuphead documentation has internal drift: README reports current 64-bit testing, while sections of technical/build docs still describe draft IL2CPP route and earlier untested state; current `launch64.txt` describes Mono bridge. Use executable launcher/source and pinned revision as authority for copied behavior.
- Exact Delver current build scripts, PortMaster launcher implementation and dependency licence manifests require working CCE index for requested R36S worktree before reuse. Historical memory is useful locator, not substitute for reviewing proposed copied code.
- No source edits, game builds, downloads of commercial assets, device connection, firmware change or deployment performed. Only these research notes created.
