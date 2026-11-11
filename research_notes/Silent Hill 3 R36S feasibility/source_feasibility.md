# Silent Hill 3 source and renderer feasibility

## What source exists and which baseline is being ported?

### Takeaway

Feasible-looking source adaptation, already containing Linux host path; far more promising than running Switch NRO on R36S. ARM64 parity helps generated C execution, but current graphics backend and target performance remain unproved. Research only: no game build, run, deployment, or implementation changes performed.

### Cited Findings

- Local git metadata: HEAD `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`, commit dated 2026-10-22 11:54:12 -0300, subject `README: v0.06 launcher and pause menu`; origin `git@github.com:ktodorow/sh3-nx-r36s.git`. Initial dirty paths only `.gitignore` and untracked `AGENTS.md`. Source evidence below retrieved from upstream at same exact commit, so does not represent unrelated latest-main changes. [Exact upstream revision](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98)
- Actual baseline: PC executable statically translated from x86 to C, subsequently compiled for Switch ARM64 or Linux x86-64. Source Windows API replacements use SDL2/OpenGL; executable is not Switch engine source or console emulation. [README, lines 16–37](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md#L16)
- Top-level build combines generated C with `src/runtime`, `src/win32`, `src/d3d8`, `src/game`; Linux links SDL2, libm, pthread. Switch-specific link libraries and NRO production are isolated under `NINTENDO_SWITCH`. Flags preserving wrapping arithmetic and guest-memory type punning are essential: `-fwrapv`, `-fno-strict-aliasing`. No top-level link to vendored xboxrecomp Xbox D3D/CPU/runtime libraries. [CMakeLists.txt, lines 8–35](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/CMakeLists.txt#L8)
- Generation pipeline patches PC EXE, wraps PE as XBE, discovers/disassembles functions, repairs boundaries, analyzes ABI, and emits C in batches with manual game-function exclusions. Python generator runs on build host; generated output can then be compiled using Linux aarch64 compiler. [tools/regen.sh, lines 1–30](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/tools/regen.sh#L1)
- User-provided game version must match 3,338,240-byte `sh3.exe`, SHA-1 `aa2aca6dba19bf510c9c2e92eefdc15e98266581`; original `data/` is about 5 GB. Current upstream lists skipped FMVs and limited testing beyond opening areas. [README, lines 82–109](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md#L82)

### Inferences

- Build starting point should be existing Linux branch compiled as aarch64 ELF, not devkitPro-produced NRO, Switch loader, Wine, Box64, or Switch emulator.
- General-purpose Linux cross toolchain plus target SDL2/sysroot needed; libnx, Switch EGL/nouveau libraries, and NRO metadata not needed in Linux target.
- Vendored Xbox-specific backend/test descriptions can mislead architecture analysis: actual game uses custom top-level `src/d3d8` implementation. Reusing vendored Xbox GL3 backend would require adaptation to different API/resource model; not immediate alternative.

### Gaps

- CCE operational, but all searches returned truncated ~300-character file previews without usable opaque chunk IDs. `expand_chunk` attempts with displayed `path:line` labels returned `Chunk not found`; disabling compression did not help. Root coordinator notified. Local exploration used CCE first throughout; deeper evidence fetched from primary upstream exact-revision source via GitHub connector. No direct local source reads used.
- Metadata check showed absent `src/recomp/gen`, `game/sh3.exe`, `build/linux/sh3`; clean checkout currently cannot produce game executable until matching user EXE and generation step supplied. This is file-existence observation, not game-data inspection.
- No source build/run validation, no measured ARM64 Linux compatibility or device FPS from this project. Existing ARM64 Switch and Linux x86-64 paths support feasibility inference, not proof.

## What does renderer really require, and can GL4ES bridge it?

### Takeaway

Current renderer cannot run unchanged through GL4ES. Actual pipeline is conventional enough that native GLES3 adaptation looks materially smaller than renderer rewrite or GL2/GL4ES downgrade; installed GLES version/extensions must select minimum target. This recommendation depends on working hardware-accelerated GLES3 stack, not desktop GL version string alone.

### Cited Findings

- Context tries desktop core 4.6, 4.5, then 4.3 and aborts below 4.3. Launcher opens this same context before gameplay. Thus even CPU-rendered launcher cannot establish proof of game compatibility by itself. [d3d8.c, lines 130–160](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8.c#L130); [launcher.c, lines 430–469](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/launcher.c#L430)
- Loader treats every listed symbol as mandatory and aborts if missing, including symbols not called by active renderer. Changing SDL context request alone still leaves loading failures. [gl.c, lines 8–10](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/gl.c#L8); [gl.h, lines 7–102](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/gl.h#L7)
- Generated vertex/fragment shaders declare GLSL430 core, explicit attribute locations, ordinary uniforms, varyings, 2D/cube samplers. Vertex translator supports 16 attributes and 96 vec4 constants; shader wrapper declares ten vec4 varyings plus two floats and eight fragment samplers. No UBO/SSBO, compute shader, geometry/tessellation stage, texture-array pipeline, or indirect draw dependency found in active top-level shader/device/resource code. This is static source census, not runtime capture of actual variants. [d3d8_shader.c, lines 218–239](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8_shader.c#L218); [shader generation, lines 516–587](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8_shader.c#L516)
- GL4ES upstream targets GL2.1/1.5 to GLES2/1.1, with partial extra extensions and limited shader conversion. Its scope does not promise modern GL4.3 core/shader semantics. [GL4ES README](https://github.com/ptitSeb/gl4es#readme)
- Clip behavior currently relies on upper-left origin plus zero-to-one depth. GLES extension equivalent exists as `GL_EXT_clip_control` and `glClipControlEXT`, including same Direct3D-convention purpose; extension presence still needs runtime check. [d3d8.c, lines 155–160](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8.c#L155); [Khronos EXT_clip_control](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_clip_control.txt)

### Inferences

Static API census suggests following adaptation matrix. Rows marked conditional require target probe and gameplay trace; do not remove supported features merely because device is Mali.

| Area | Source evidence | GLES3 adaptation |
| --- | --- | --- |
| Context/loader | `d3d8.c:130`, `gl.c:8`, `gl.h:7` | Request SDL ES profile; resolve only required GLES core functions plus checked extensions; keep desktop backend. |
| Shader language | `d3d8_shader.c:518–553` | Generate suitable GLSL ES profile, explicit float/int precision, preserving attributes, uniforms, arithmetic and discard. GLES3 supports much current syntax. |
| Precision | helpers at `d3d8_shader.c:182–188` | Helpers use values near float maximum; default mediump could overflow. Start highp and lower selectively only with evidence. |
| Clip/depth/orientation | `d3d8.c:155–160`, `:314–317`, `:631–657` | Use EXT_clip_control if present; otherwise adapt vertex y and depth with coordinated viewport/scissor, culling, render-target texture orientation, blits/readbacks. Single y flip insufficient correctness proof. |
| Base vertex | `d3d8.c:792–802` | GLES3.2 core or extension path where available; otherwise rebase vertex attribute offsets for all streams or indices with correct signed/range behavior. |
| Depth functions | `gl.h`, `d3d8.c:633` | GLES float forms for clear-depth/depth-range. |
| BGRA vertex color | `d3d8.c:688–695` | Desktop BGRA attribute-size token needs RGBA attribute plus shader swizzle or CPU repack. BGRA texture support does not imply BGRA vertex-size support. |
| Texture formats | `d3d8_res.c:25–45`, `:170–216` | Check BGRA upload formats and reversed packed 16-bit variants; repack unsupported formats to GLES-compatible RGBA/RGB. Preserve P8 palette alpha. |
| DXT/S3TC | `d3d8_res.c:37–41`, `:180–216` | Query compressed-format support; retain native path if supported. Otherwise CPU decode once per texture/mip or validated offline conversion. Expect additional RAM/upload cost; don't assume all Mali drivers lack support. |
| Swizzle/R/RG/row length | `d3d8_res.c:32–34`, `:177`, `:332–335`, `:376–380` | Mostly retained on GLES3; GLES2 downgrade requires additional extensions/fallbacks. |
| Framebuffers/blit | `d3d8.c:304–318`, `d3d8_res.c:246–318`, `:348–362` | GLES3 retains separate read/draw FBO and blit approach. Check attachment formats and orientation, including launcher. |
| Depth clamp | `d3d8.c:757–759` | Extension if present; otherwise preserve screen-space UI clipping semantics in shader/geometry path; don't blindly drop and accept missing quads. |
| Polygon mode | `d3d8.c:667` | GLES has no generic desktop polygon mode; trace whether game needs non-solid modes, use no-op for solid with explicit handling of others. |
| Border addressing | `d3d8_shader.c:844–862` | ES version/extension support check; emulate border sampling if used and unavailable. CLAMP_TO_EDGE substitution changes visuals. |
| Readback/save thumbnails | `d3d8_res.c:295–339` | GLES readback-format validation and BGRA repack. Preserve front-frame snapshot used for fades and save previews. |
| VAO, VBO, samplers | `d3d8.c:164–168`, `:763–770`; `d3d8_shader.c:845–862` | GLES3 retains structure; verify limits and sampler states. |

All matrix file references target [device code](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8.c), [resource code](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8_res.c), [shader code](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8_shader.c) at pinned revision; matrix remedies are recommendations, not implemented facts.

- GLES2 fallback would additionally constrain attributes/varyings/uniforms, replace shader input/output syntax, VAOs, integer indices, FBO blits, row-length operations, texture formats, sampler objects, and shader operations. Actual variants could fit reduced limits after specialization, but this is substantially more adaptation than GLES3.
- GL4ES remains possible only after explicit GL2-compatible backend work; successful Delver GL4ES does not establish this game's compatibility. For current shader-heavy D3D8 layer, direct GLES3 avoids redundant desktop-to-ES conversion.
- No modern features found does not mean two-line shader/context fix. Format/orientation/resource readback are correctness-sensitive and affect full-game scenes, saves, post effects.

### Gaps

- Actual target extension list, maximum vertex/fragment uniforms/varyings, packed formats, compressed formats, depth-clamp/clip-control/border-address behavior not measured here.
- Other researcher reported cached real-device Mali-G31 GLES3.2 evidence; report writer must cite that research directly and distinguish cached prior firmware from current device probe.
- Source census did not enumerate runtime-used shader variants or texture formats per scene. Need representative scene captures and API instrumentation before pruning generic paths.

## Is 32-bit guest memory or Switch-specific runtime a blocker?

### Takeaway

Existing 64-bit-host abstraction handles 32-bit guest addresses and sparse virtual memory; ARM64 Linux should reuse it. Four-GiB reservation is address space, not four GiB physical RAM. Main unknowns are resident memory, generated-code CPU cost, and audio-related thread scheduling.

### Cited Findings

- Guest addresses remain uint32 while host offset is pointer-sized. Guest-to-host conversions add arena base; host pointers are converted back to guest offsets, avoiding accidental truncation as design principle. [rt.h, lines 8–17](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/rt.h#L8); [rt_core.c, lines 17–31](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/rt_core.c#L17)
- Linux reserves 4 GiB with inaccessible anonymous mmap and no-reserve flag, committing requested pages with mprotect. Switch's special libnx process-memory mapping is separate preprocessor branch. [host.c, lines 99–130 and 218–228](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/host.c#L218)
- Guest allocator rounds allocations to powers of two, can waste nearly half each block, commits in 8 MiB steps, keeps freed-block quarantine capped at 64 MiB, and retains free lists. Quarantine compensates for observed use-after-free behavior, not arbitrary disposable cache. [rt_core.c, lines 124–197](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/rt_core.c#L124)
- Linux host uses pthreads and SIGUSR2/pipe-based pause/resume. `host_use_single_core` is no-op. Switch code explains CRI audio races in parallel guest threads and provides actual affinity workaround. [host.c, lines 38–55](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/host.c#L38); [Linux thread code, lines 151–216](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/host.c#L151)
- Runtime creates game host thread with 16 MiB stack and 1 MiB guest-stack setup. These are stack capacities, not proof of fully resident allocation. [rt_core.c, lines 489–522](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/rt_core.c#L489)
- Helper template emulates registers, x87/SSE/MMX state and uses C math/atomic builtins; x86 intrinsics guarded, ARM fallback provided for MMX float conversion. This is translated guest semantics, not original game's ideal optimized ARM source. [recomp_types.h, lines 44–69, 167–230, 1130–1140](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/third_party/xboxrecomp/templates/runtime/recomp_types.h#L1130)

### Inferences

- Preserve 64-bit process, guest-offset model and correctness compiler flags. An aarch64 build need not re-address original guest pointers or load original x86 code as native machine instructions.
- Generated semantic operations, register/TLS traffic, indirect-call dispatch, and game main-thread dependence can still dominate CPU. More cores and ARM64 label do not guarantee 30 FPS; reducing resolution helps GPU cost but may not help CPU bottleneck.
- Profile guest heap high-water mark, RSS/PSS, GPU allocation, CPU per thread, and draw/upload counts. Pixel work at 320×240 is one quarter 640×480, but frame rate will not necessarily quadruple.
- If audio races appear, provide real Linux per-guest-thread affinity or launcher-level taskset experiment before claiming `cores=1` works. Whole-process affinity also constrains audio/render work; compare against narrower thread policy.
- Do not simply shrink quarantine or replace allocator before save/combat/door/load soak tests: documented lifetime behavior can regress.

### Gaps

- Device RSS, heap high-water, native code footprint, compile size/time, CPU frame time unknown. Upstream Switch title-takeover requirement is qualitative memory warning, not measured minimum RAM.
- ARM64 Linux host combination not independently executed; guest unaligned access, math rounding, atomics, signals, and suspend/resume still require target checks.

## What full-port behavior already exists or remains missing?

### Takeaway

Input, audio, save paths, timing and Windows filesystem bridge already have Linux-friendly foundations. Baseline still skips FMVs and has incomplete campaign validation; matching upstream behavior alone does not meet user's finished-port requirement.

### Cited Findings

- Input exposes one SDL controller plus keyboard; controller lookup requires SDL GameController recognition. Switch changes face-button mapping under conditional compilation; Linux uses Xbox convention. Trigger actions read SDL trigger axes. [dinput.c, lines 13–20 and 320–346](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/win32/dinput.c#L320)
- DirectSound software mixer uses SDL float stereo 44.1 kHz output, 1024-sample buffer and up to 512 guest buffers. Mixer itself adds CPU work; CRI scheduling issue is distinct from graphics. [dsound.c, lines 1–21 and 444–451](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/win32/dsound.c#L444)
- File bridge maps Windows-style paths and case-insensitive names to host filesystem, including virtual CD movie path. Save settings handled through original savedata paths. Timers use monotonic host clock; Sleep(0) is intentionally tiny sleep to limit busy waiting. [kernel32.c, lines 21–57, 456–483, 621–643](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/win32/kernel32.c#L21)
- Linux startup accepts game directory by argv or SH3_DIR, changes current directory, then opens game/settings relative to it. Savedata and logs therefore need writable correct working directory; no Switch SD prefix needed. [rt_core.c, lines 500–522](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/rt_core.c#L500)
- Parser already accepts 320×240 through 1920×1440. Default remains 1280×720. Launcher currently offers 1280×720, 1920×1080, 960×720, 640×480, but no 320×240 option. SDL window initially requests 1280×720 independent of game setting; launcher renders CPU 1280×720 canvas. [rt_core.c, lines 461–478](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/rt_core.c#L461); [launcher.c, lines 1–11 and 181](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/launcher.c#L181); [user32.c, lines 81–91](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/win32/user32.c#L81)
- Shader cache stores state/guest-shader hashes and reconstructs programs, rather than serialized GL program binaries. Renderer changes still warrant versioning/invalidating cache layout/semantics to avoid stale interpretations. [d3d8_shader.c, lines 592–685](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8_shader.c#L592)

### Inferences

- For user-confirmed goal: start 640×480 internal, low graphics, stable 30 FPS; fallback 320×240 internal while keeping 640×480 panel output if measurements require. Existing parser makes fallback technically expressible, but UI/font/save-thumbnail/fades/resolution scaling still need validation.
- SDL controller mapping from PortMaster can avoid invasive input rewrite, provided digital R36S triggers map to SDL trigger axes and all campaign actions are reachable. Check left/right sticks, clicks, menu face layout, shoulder/trigger distinction and clean exit.
- Full-port acceptance should cover campaign progression, endings, combat, item/map screens, real-time cutscenes, sound/music/dialogue, save/load/new game, exit/restart and SD-write failures. FMV behavior remains explicit user decision: upstream skipped movies must be surfaced, not silently treated as finished.
- Original-video support now required: user confirmed 'Yes — include original videos' through coordinator. Movie playback is separate decode/timing/audio-sync work; current skip is source baseline limitation. Exact `.000` codec not established, so no assertion that FFmpeg drop-in solves it.
- Thirty-FPS target is presentation/performance requirement, not permission to halve game timers, simulation speed or audio rate. Source advertises 60 Hz display modes and requests vsync, but complete game timing model not traced. Validate movement/combat/animation/door timing against original alongside audio/movie clocks at both internal resolutions; avoid applying frame skipping globally without evidence.

### Gaps

- Full campaign currently unverified by us and upstream README warns about opening-area testing. Known prior missing-function/recompiler fixes show latent progression crashes remain plausible.
- Original FMV containers/codec unconfirmed; no original data inspected. Completeness settled: original videos included in full-port goal.
- No performance settings map beyond resolution/thread configuration audited. 'Lowest graphics' needs concrete supported game-setting survey and scene-specific effects trade-offs after renderer works.

## What gates turn feasibility into finished port evidence?

### Takeaway

Small rendering and runtime probes should be early milestones inside full-port project, never substitute final deliverable. Scope now personal R36S dArkOS with PortMaster launcher; public submission later.

### Cited Findings

- Built-in checks include FPS and guest-heap logging, screenshot dumps, scripted inputs, call traces, guest memory probes, ABI checks and Unicorn differential tests. These provide reproducible baseline captures. [README debugging aids, lines 191–205](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md#L191)
- Root build does not register project test targets or link vendored test runtimes. Vendored recompiler regression tests and game-level oracle/fuzz tools exist, but generic Xbox D3D smoke tests do not automatically validate custom `src/d3d8` renderer. [Root CMake](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/CMakeLists.txt); [tracked test inventory](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/third_party/xboxrecomp/tools/recomp)

### Inferences

Recommended dependency-ordered gates:

1. Fingerprint current firmware/kernel/SDL/libc/GLES/renderer/extensions and controller mapping; verify hardware renderer, not software fallback. Obtain matching EXE hash and data locally.
2. Generate C on workstation; reproduce existing desktop Linux baseline if suitable environment available. Compile aarch64 Linux ELF against compatible sysroot, preserving semantic flags. Test sparse arena/signals/threads and diagnostics independently of renderer.
3. Device SDL/EGL/GLES capability probe with real FBO texture, depth/stencil, indexed draw, shader precision, BGRA/repack, DXT fallback and UI/orientation checks. Select minimal backend only after this evidence.
4. Add conditional GLES3 backend/context/loader/shader/format/clip adaptation while retaining desktop baseline. Validate representative frames side by side, including alpha hair, fog, shadows, indoor flashlight, palette textures, transitions, reflections, menus and save thumbnails.
5. Use frame-time/RSS/CPU data at 640×480 to separate GPU vs CPU bound scenes. Try 320×240 only when needed. Measure percentile frame times, long stalls and audio underruns, not only average FPS or title screen.
6. Integrate PortMaster launcher, game-data checks, writable saves/cache/logs, controller mapping and predictable exit. Test both cold and warm runs plus restart/save persistence.
7. Full campaign test matrix, crash logs/guest traces for every progression stop, movie decision/support, low-memory and long-session soak. Define stable-30 tolerance before declaring done; first successful launch does not pass this gate.

### Gaps

- No defensible effort-hours or FPS prediction without first native GLES draw and representative gameplay profile. Renderer downgrade has bounded seams; campaign/recompiler correctness and performance tail have open-ended risk.
- User confirmed target, low-visual performance goal and original videos to coordinator; actual 'stable' percentile/tolerance remains open.

## What documentation and release constraints remain?

### Takeaway

User selected native Linux ARM64 plus GLES3 baseline after reviewing findings; implementation remains unstarted. Glossary records agreed vocabulary only; report writer will capture route trade-offs in ADR. Commercial game data remains user-supplied, while engine/runtime licensing needs explicit review before public distribution.

### Cited Findings

- Root pinned tree lacks top-level LICENSE, GLOSSARY.md, GLOSSARY-MAP.md and docs/adr; local metadata confirmed glossary/ADR paths absent before this task. Vendored xboxrecomp has MIT LICENSE plus separate LGPL source notices. Do not infer entire custom port is MIT from dependency license. [Root tree](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98); [xboxrecomp license](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/third_party/xboxrecomp/LICENSE); [third-party license note](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/third_party/xboxrecomp/LICENSES/README.md)
- Source legal section states user must provide own game; generated commercial code not tracked in upstream tree. Widescreen fix credited MIT. [README legal and credits](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md#L207)

### Inferences

- Personal build can proceed through feasibility work without deciding public binary distribution. Before PortMaster submission, clarify license for custom root runtime and how generated-code binaries can be packaged, include applicable notices, and exclude original assets/EXE from downloadable package. This is release-policy work, not claim about jurisdiction-specific legality.
- Glossary created at root after coordinator delegation, using domain-modeling format: full port, internal resolution, output resolution, game data, PortMaster package. Full port now includes campaign, original videos, audio, controls and save/load, following user confirmation. No backend or performance spec inserted into definitions.

## How should required original-video playback be researched and restored?

### Takeaway

Upstream lacks DirectShow object creation, so movie restoration needs real integration. First identify actual original `.000` media, then implement narrow game-call bridge to decoder and existing SDL/GLES outputs. Do not infer codec from extension or inherited SH2-era `.bik` comments.

### Cited Findings

- OLE bridge's `CoCreateInstance` always clears output and returns class-not-registered. No DirectShow graph implementation present in this active Windows bridge. [user32.c, lines 200–209](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/win32/user32.c#L200)
- README explicitly identifies movie files under `data/movie/*.000` and DirectShow playback on original PC, currently skipped. [README known issues](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md#L82)
- Virtual-CD path comment refers to `Open.bik`, but bridge is shared lineage from SH2 and no actual SH3 assets were inspected. This comment alone is not evidence that SH3 `.000` files contain Bink video. [kernel32.c, lines 762–766](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/win32/kernel32.c#L762)
- FFprobe reports format/stream information; libavcodec provides decoder interfaces for FFmpeg-supported media. This establishes tooling and integration option, not support/performance for uninspected files. [FFprobe documentation](https://ffmpeg.org/ffprobe.html); [libavcodec documentation](https://ffmpeg.org/libavcodec.html)

### Inferences

- Add movie inventory gate once user assets available: file signature, ffprobe format/codec, width/height, frame rate, audio streams, duration and all variants/localizations. Inspect actual source/lifted DirectShow call sequence and failure-path handling at same EXE revision.
- Candidate route: decode originals through libavformat/libavcodec, bridge only game-used graph/video calls or replace identified game movie-play function, upload frames via GLES texture path, route audio through SDL with media clock, handle finish/cancel/failure deterministically and restore game rendering/audio state.
- Check subtitle presentation source, aspect ratio/letterbox behavior, input skip, pause/resume, audio/video sync, decode latency, frame pacing and return to campaign. Test all required movies, not just opening logo.
- Prefer original media decoded unchanged when CPU permits; offline transcode is separate user-visible trade-off only if original decode cannot meet target. No automatic conversion or media redistribution performed.
- CPU software decode first is portable feasibility route; VPU decoder integration would be firmware/kernel-specific extra work. Neither decode speed nor hardware availability established here.
- Vendored xboxrecomp Media Foundation video code is not automatically portable to Linux SDL/GLES nor linked by root CMake; useful interface precedent only.

### Gaps

- Decoder codec, container compatibility, required bandwidth/RAM/CPU, licensing of linked decoder configuration, and game movie-call boundaries unresolved until assets and call traces exist. Original-video requirement therefore increases scope beyond upstream parity.

## What are exact source-level memory bounds and texture fallback costs?

### Takeaway

No credible claim that game fits device RAM yet. Sparse arena reservation and heap address limits establish virtual bounds only; resident allocations must be measured on campaign scenes.

### Cited Findings

- Guest heap starts at `0x10000000` and ends before `0xF0000000`: 3.5 GiB guest virtual range, with 8 MiB commitment increments and 64 MiB freed-block quarantine cap. No device-RAM budget enforcement in allocator. [rt_core.c, lines 116–197](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/rt_core.c#L116)
- Original guest texture/surface copies remain in guest memory; GL textures and render targets created separately, P8 expanded on CPU. Resource memory therefore can include original CPU copy, conversion buffer and GPU copy. [d3d8_res.c, lines 1–3 and 170–216](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8_res.c#L170)
- DXT1 uses 8-byte blocks and DXT3/5 use 16-byte blocks for 4×4 pixels in format table. [d3d8_res.c, lines 37–41](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8/d3d8_res.c#L37)

### Inferences

- If S3TC unavailable, RGBA8 expansion costs 8× compressed DXT1 storage or 4× DXT3/5 storage for GPU copy, plus temporary decode buffer and preserved guest compressed data. Full mip chain adds roughly one third over top mip for ordinary power-of-two textures. This arithmetic is not measured game memory.
- Offline ETC2 transcoding could reduce GPU storage on GLES3-capable drivers, but adds preprocessing and quality/time trade-offs, complicates dynamic/updated textures and does not remove original guest-memory copies. CPU on-demand RGBA fallback is simpler correctness baseline if memory permits; prefer native S3TC when supported.
- At 640×480 one RGBA8 color image is 1,228,800 bytes, about 1.17 MiB; at 320×240, 307,200 bytes. Lower render resolution reduces framebuffer/depth/snapshot costs; does not proportionally shrink game textures, generated code, guest heap or audio.
- Exact runtime heap/image/stack/texture allocation totals unavailable because original EXE/data absent and game unexecuted. Report limits honestly; never present 3.5 GiB virtual heap ceiling as required RAM or 4 GiB arena as physical allocation.

### Gaps

- No complete-game per-area resident-memory census, texture-size distribution, fragmentation trace, warm-cache growth profile or measured decoder buffers. These remain mandatory feasibility gates for 1 GiB-class handheld.

### Gaps

- No legal advice or distribution-rights conclusion; absent root license needs maintainer clarification if public release pursued.
- No ADR written by this researcher; coordinator has confirmed user-selected native Linux ARM64/GLES3 route and delegated final decision record to report writer. Device tests can still change implementation details.
