# R36S platform and current PortMaster guidance

Reference-root names are portable locators; actual user-specific paths stay local. See [locator definitions](../Silent%20Hill%203%20R36S%20spec/source-checks.md).

Research checked 2026-11-11. Scope: personal R36S port with PortMaster launcher first; public submission later, per coordinator. User acceptance: full campaign, original FMVs, audio, controls and saves; stable30 FPS, lowest graphics, 640x480 internal preferred with 320x240 fallback. No device contacted; no firmware, libraries, or game files changed. Platform capabilities below separate hardware specification, historical device evidence, upstream software support, and unknown current installed configuration.

## Which R36S and dArkOS target is actually known?

### Takeaway

Standard R36S target is RK3326, 640x480, 1 GB RAM, two analog sticks. “Latest dArkOS” does not identify installed kernel, community build, or GPU libraries. Capture these before choosing renderer and build baseline.

### Cited Findings

- Official PortMaster supported-device list identifies R36S as 640x480, RK3326, 1.0 GB, two sticks; lists ArkOS, AmberELEC, ROCKNIX. This establishes usual model, not proof of user's physical board. [PortMaster supported handhelds](https://portmaster.games/installation/supported-handhelds/)
- Rockchip identifies RK3326 CPU as quad-core ARM64 Cortex-A35 and GPU as Arm G31, with silicon support for GLES 3.2 and Vulkan 1.0. Mali-400/450 belong to other Rockchip models; do not confuse RK3326 with RK3328. Rockchip announcement establishes API capability of silicon, not usable installed dArkOS driver. [Rockchip RK3326 announcement, 2018-04-13](https://www.rock-chips.com/a/en/News/Press_Releases/2018/0413/898.html)
- Upstream dArkOS describes current OS as Debian Trixie with 64-bit and 32-bit userspaces. [dArkOS wiki](https://github.com/christianhaitian/dArkOS/wiki)
- Latest upstream release checked through GitHub releases API: tag `v08272026`, published `2026-08-30T16:13:16Z`. Its named image assets include RG351MP and other models, but none named R36S. Tag date and publication date differ; do not silently call release August 27. Release notes' `g29p1` libmali change explicitly concerns **RK3566**, not RK3326. [Release](https://github.com/christianhaitian/dArkOS/releases/tag/v08272026), [API](https://api.github.com/repos/christianhaitian/dArkOS/releases/latest)
- `southoz/dArkOSRE-R36` describes customized dArkOS for R36S devices and clones, with board/panel compatibility table. Latest release API gives tag `dArkOSRE-R36(03082026)`, published `2026-03-10T08:03:35Z`. [README](https://github.com/southoz/dArkOSRE-R36/blob/main/README.md), [release API](https://api.github.com/repos/southoz/dArkOSRE-R36/releases/latest)
- Another community branch, `djparentx/dArkOSen-R36S`, had latest tag `11112026`, published `2026-11-11T06:51:04Z`. Release explicitly calls this last 4.4-kernel update and says future 5.10 transition can break clone devices; OTA disabled pending deliberate installation. README base is `dArkOS_RG351MP_trixie_07262026`. These statements identify **that branch**, not user's installation. [Release](https://github.com/djparentx/dArkOSen-R36S/releases/tag/11112026), [README](https://github.com/djparentx/dArkOSen-R36S/blob/main/README.md), [API](https://api.github.com/repos/djparentx/dArkOSen-R36S/releases/latest)
- Debian Trixie's current `libc6` package is 2.41; customized firmware may differ, so installed `getconf GNU_LIBC_VERSION` remains authoritative. [Debian package](https://packages.debian.org/trixie/libc6)
- Working-port researcher found historical October diagnostics from user's Delver target: `dArkOS09022026`, `aarch64`, `armhf Y`, glibc241 label, 640x480; report records kernel4.4.189, Debian13 and MemTotal916912kB. Native graphics log identifies ARM/Mali-G31, `OpenGL ES 3.2 v1.r13p0-01rel0.8747d14aec16ec21ac2b2da252c4ec5f`. These are much stronger target evidence than generic wiki, but not a fresh check of November state. Cached native probe, identity lines38–50, graphics lines314–316 (`DELVER_REPO/.port-cache/device-tests/cpu7-final-native-probe.log:314`), Cached report, kernel line2, OS line4, RAM line19, libraries lines57–68 (`DELVER_REPO/.port-cache/device-tests/device-report.txt:2`)

### Inferences

- ARM64 native compilation is compatible with CPU instruction family, but does not supply Switch executable format, OS services, graphics API, or sufficient performance. Existing Linux SH3 runtime is relevant path; running NRO directly is not equivalent to rebuilding native Linux program. [Upstream SH3 architecture](https://github.com/cutarev/sh3-nx)
- Do not require firmware upgrade for project. First evaluate installed environment. Hardware/kernel changes would confound feasibility experiment and can break clone support. [dArkOSen kernel-transition note](https://github.com/djparentx/dArkOSen-R36S/releases/tag/11112026)

### Gaps

- User's current board/panel, firmware/kernel revision since October diagnostics, live RAM available, clocks and active SDL display backend remain unmeasured. Historical GPU/GLES evidence supports ES3 path but does not list every required extension/limit.
- No credible source-backed SH3 frame-rate estimate for RK3326 found. No CPU/GPU speed ratio or promised FPS justified by ISA similarity.

## Can GL4ES, Panfrost, Vulkan, or software rendering bridge desktop GL4.5?

### Takeaway

GL4ES cannot be treated as desktop GL4.5 implementation. Native GLES3 adaptation is stronger research candidate, conditional on actual shader/resource requirements and device driver. Graphics wrappers and software renderers remain controlled experiments, not proven solutions.

### Cited Findings

- GL4ES upstream identifies library as OpenGL 2.x/1.5 over GLES2.0/1.1. README lists crude shader conversion, unsupported multiple color framebuffer attachments, depth/stencil readback limitations, and limited 3D/rectangle texture shader support. It is not a general GL4.5 core translator or Direct3D runtime. [GL4ES README](https://github.com/ptitSeb/gl4es/blob/master/README.md)
- Current Mesa Panfrost feature table lists G31/G51/G52/G76 at GLES3.1 and desktop GL3.1; Vulkan1.3 appears in table with feature/conformance caveats. This is Mesa upstream support, not evidence Panfrost/PanVK is installed on dArkOS or compatible with existing vendor kernel. [Mesa Panfrost](https://docs.mesa3d.org/drivers/panfrost.html)
- ROCKNIX's RG351 family documentation, sharing RK3326, distinguishes libmali GLES3.2 from Panfrost GL3.1/GLES3.1. This corroborates difference between vendor GLES and Mesa desktop GL capabilities, but does not specify user's R36S firmware. [ROCKNIX RK3326 devices](https://rocknix.org/devices/anbernic/rg351pmv/)
- Zink maps OpenGL to Vulkan; feature level depends on Vulkan driver's features and extensions. Mesa provides requirements profile checker. Vulkan silicon branding alone does not establish adequate Zink GL4.5 capability. [Mesa Zink](https://docs.mesa3d.org/drivers/zink.html)
- LLVMpipe is CPU software rasterizer. Documentation provides no SH3/RK3326 benchmark. Rendering on CPU may isolate portability errors but is not evidence of playable handheld performance. [Mesa LLVMpipe](https://docs.mesa3d.org/drivers/llvmpipe.html)
- `MESA_GL_VERSION_OVERRIDE` changes advertised GL version/profile; Mesa warns given version may expose features not actually implemented. `MESA_GLSL_VERSION_OVERRIDE` similarly does not implement missing language features. These are debugging knobs, not capability upgrades. [Mesa environment variables](https://docs.mesa3d.org/envvars.html)

### Inferences

- Renderer requesting desktop GL4.5 cannot be made correct merely by setting `LIBGL_GL=21`, spoofing GL version, or renaming GLES library to libGL. Actual calls/shaders must fit target API. [GL4ES](https://github.com/ptitSeb/gl4es/blob/master/README.md), [Mesa overrides](https://docs.mesa3d.org/envvars.html)
- Source researcher reports conventional VS/FS pipeline, no compute/SSBO/UBO, and desktop APIs with GLES substitutes. That makes GLES3 renderer feasibility worth testing; see sibling source notes for exact source evidence. This is source-based inference, not completed port.
- Prefer renderer capability probe and minimal shader/draw test on existing GPU stack before considering kernel replacement, Panfrost migration, Zink, or a new D3D8 renderer. GL4ES compatibility path would require substantial reduction from current desktop renderer regardless. [Panfrost feature levels](https://docs.mesa3d.org/drivers/panfrost.html), [GL4ES scope](https://github.com/ptitSeb/gl4es/blob/master/README.md)

### Gaps

- Need actual GL vendor/renderer/version, GLSL version, extensions, max vertex attributes/varyings/uniform components/texture units; BGRA uploads, DXT/S3TC, depth clamp, border clamp, base-vertex, and clip-control support require real driver checks.
- No verified existing SH3 PortMaster package found in searches of official PortMaster pages and upstream SH3. Search failure is not proof none exists. Existing upstream explicitly documents Linux x86-64 debugging build. [Upstream SH3](https://github.com/cutarev/sh3-nx), [PortMaster game catalogue](https://portmaster.games/all-games/)
- No evidence supporting playable Switch-emulator path on RK3326. PC Windows binary route adds x86 and Windows compatibility layers; native generated-C/Linux source route avoids those layers. No alternative-route benchmark obtained. [SH3 native recompilation design](https://github.com/cutarev/sh3-nx)

## Which PortMaster build and launcher guidance is current?

### Takeaway

Use current PortMaster native SDL2 launcher conventions and explicit Linux AArch64 build. Select glibc baseline after target fingerprint. Public package review belongs after working personal port.

### Cited Findings

- Current official build page recommends Ubuntu22.04/glibc2.35; Ubuntu20.04/glibc2.31 remains documented for older ArkOS compatibility. `min_glibc` metadata filters supplied binaries requiring newer glibc. Official page links Docker and chroot environments. A generic contemporary ARM64 compiler alone does not guarantee compatible runtime. [Current build environments](https://portmaster.games/contribute/porting/build-environments/)
- Current script templates locate PortMaster across firmware paths, source `control.txt`, optionally source `mod_${CFW_NAME}.txt`, call `get_controls`, set game directory and controller config, use `pm_platform_helper`, and end via `pm_finish`. Start with native SDL2 template, adapting launch argument and paths. Other templates add Weston/Mesa runtimes only when needed; GL4ES/VirGL templates do not promise GL4.5. [Script templates](https://portmaster.games/contribute/porting/script-templates/)
- PortMaster's current portability taxonomy distinguishes native ARM Linux builds, engine runtimes, and instruction translation. PortMaster does not automatically rebuild arbitrary binaries. [What can be ported](https://portmaster.games/contribute/porting/what-can-be-ported/)
- Public package conventions require `port.json`, README, screenshot, gameinfo, launch script, unique lowercase port directory, and `licenses/` for sources and shipped libraries. Architecture metadata must match binaries. These are later release requirements, not prerequisite for renderer experiment. [Packaging](https://portmaster.games/contribute/porting/packaging/)
- PortMaster FAQ describes user-provided commercial data, per-port logs, and save/config isolation inside port folder. Upstream SH3 requires user's own PC game files and exact executable build. [PortMaster FAQ](https://portmaster.games/faq), [SH3 README](https://github.com/cutarev/sh3-nx)

### Inferences

- Reuse known working Delver/Cuphead packaging patterns selectively, but do not carry over managed-runtime-specific launchers. Native SH3 Linux executable needs native SDL/graphics dependencies rather than Mono/Unity runner. [PortMaster native-versus-runtime model](https://portmaster.games/contribute/porting/what-can-be-ported/)
- Pin container/toolchain/sysroot and dependency versions; inspect ELF interpreter, required GLIBC/GLIBCXX symbols, and `DT_NEEDED` closure before on-device launch. Avoid replacing firmware system libraries. Build conservative `armv8-a`/Cortex-A35-compatible code unless measured target supports more. These are recommended checks, not checks performed in research.

### Gaps

- Installed SDL2 ABI/backend and available EGL/GLES libraries not measured. No build image digest selected; final CMake/compiler requirements await source findings.
- User-confirmed personal-first scope does not settle later redistribution permissions for recompiled proprietary game code. Source/license audit remains separate from supplying commercial assets.

## Is local porting guide outdated?

### Takeaway

Local files are saved HTML copies with May2026 filesystem timestamps. Exact source revision and content freshness could not be checked through current CCE retrieval. Current online official documentation is authoritative for proposed instructions.

### Cited Findings

- CCE `context_search` found `Build Environments.html`, `Packaging.html`, `Porting.html`, `Port Tools.html`, but returned only compressed header previews. `expand_chunk` using both returned `filename:1` identifier and filename returned `Chunk not found.` Local content was not bypassed via raw reads. Local guide folder (`PORTING_RESOURCES_REPO`)
- Known-file metadata: `Build Environments.html` 16650 bytes, mtime `2026-05-17T16:01:50.439760Z`; `Packaging.html` 39729 bytes, mtime `2026-05-17T16:01:38.283503Z`; `Porting.html` 36137 bytes, mtime `2026-05-17T16:02:00.167930Z`; `Port Tools.html` 11546 bytes, mtime `2026-05-17T16:01:55.085222Z`. `git -C ... log -1` and `remote -v` report `fatal: not a git repository`. These are file-copy timestamps, not original publication dates or revisions. Local guide folder (`PORTING_RESOURCES_REPO`)
- Old online `/packaging.html` redirects to current `/contribute/porting/packaging/`. Current build documentation explicitly covers newer glibc baseline and filtering; current native script template centralizes cleanup. These are verified current instructions, not demonstrated differences from unread local body. [Packaging](https://portmaster.games/contribute/porting/packaging/), [build environments](https://portmaster.games/contribute/porting/build-environments/), [templates](https://portmaster.games/contribute/porting/script-templates/)

### Inferences

- Do not claim local guide is obsolete solely from mtime. Cite current web instructions in plan, retain local guide as secondary reference until CCE expansion works.

### Gaps

- Local-vs-upstream textual diff, original download date, and source commit cannot be established from retrieved previews.

## Which low-impact device checks settle remaining facts?

### Takeaway

Read system identity and library inventory first. Then run small EGL/SDL GLES probe through actual display path. Do not update firmware or install new graphics stack merely to collect evidence.

### Cited Findings

- Current dArkOS has mixed userland and community forks with different kernels, while graphics API level depends on driver. This justifies identifying running OS/ABI and querying real context rather than relying on model name. [dArkOS wiki](https://github.com/christianhaitian/dArkOS/wiki), [dArkOSen release](https://github.com/djparentx/dArkOSen-R36S/releases/tag/11112026), [Panfrost](https://docs.mesa3d.org/drivers/panfrost.html)

### Inferences

Recommended **future** read-only shell inventory; not executed on user's handheld:

```sh
uname -a
getconf LONG_BIT
getconf GNU_LIBC_VERSION
ldd --version
cat /etc/os-release
tr '\000' '\n' < /proc/device-tree/compatible
tr '\000' '\n' < /proc/device-tree/model
awk '/MemTotal|MemAvailable|SwapTotal/ { print }' /proc/meminfo
ls -l /dev/mali0 /dev/dri
ldconfig -p | rg 'lib(EGL|GLESv2|GL|mali|vulkan|SDL2)'
```

- Missing paths/tools are findings, not reason to install packages. `rg` may be absent on device; ordinary `grep -E` acceptable fallback. Do not mistake `LONG_BIT` for proof game executable or every library uses same architecture; inspect ELF headers too.
- If already present, `eglinfo` identifies EGL implementations/configs. `vulkaninfo --summary` only if installed and Vulkan path already available; absence does not contradict silicon specification. `glxinfo` alone is insufficient on direct KMS/EGL firmware without X11.
- Minimal SDL2/EGL test should log selected SDL video driver, EGL vendor/version, GLES `GL_VENDOR`, `GL_RENDERER`, `GL_VERSION`, GLSL version and extension lists; request GLES3 context explicitly. Query limits listed above; render and check exact SH3 representative shader/FBO/indexing/texture operations. A working context plus successful target shader compilation is first graphics gate; correct first gameplay frame is next gate.
- Graphics probes can contend with frontend for display ownership; plan controlled launch through existing PortMaster environment. Stopping frontend is a separate operational step, not part of this research's read-only inventory.
- User-set acceptance now requires stable30 FPS at lowest graphics, 640x480 preferred and 320x240 fallback, full campaign plus original FMVs/audio/controller/saves. Measure gameplay frame times, peak RSS/available RAM, audio underruns, FMV A/V sync, save/load/restart and exit cleanup. Stable30 is target, not predicted result. Original FMVs remain correctness requirement even if video introduces separate CPU load from rendering.

### Gaps

- None of these device tests ran during research. No native Linux ARM64 SH3 build, renderer smoke test, or gameplay performance result exists from this investigation.
