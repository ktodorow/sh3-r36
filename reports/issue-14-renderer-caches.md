# Issue #14: renderer cache implementation

Status: final local320×240 candidate averages29.97–29.99FPS across sampled
hospital, mall, park, church and handgun combat; minimum complete gameplay
second28FPS, measured park door-loading second25FPS. Final-binary15-minute
hospital replay passes29.8946FPS/minimum28, no logged audio underrun.
First-visit shader stalls/audio recoveries remain limits. Owner approved
publication on 2026-11-14 and closure of #9 only; #13/#14 remain open.
Baseline before these slices:13.5846FPS at640×480 and17.0724FPS
at320×240 in fixed room210,640×480 output. Current artifact and results in
[performance report](issue-13-performance.md); historical slices follow.

## Scope

Implement first renderer steps from [optimization roadmap](Silent%20Hill%203%20optimization%20roadmap.md),
preserving shader output, gameplay speed and required visual effects. Canonical
spec AC06/07/08/12/13 applies. Existing installed launcher → real game → frontend
test boundary retained. Actual hardware performance remains separate from Docker
boundary and pixel checks. No additional handheld exit test requested.

Per-program value reuse follows narrow mechanism identified in pinned
[SH2 renderer cache commit](https://github.com/cutarev/sh2-nx/commit/9edc6c39a318a0b4bc0b6542893b4b7aae521290),
without importing its desktop clip/depth or texture behavior. Current PortMaster
FNA guide and first-hand Cortex-A35/G31 LVGL report rechecked; different runtimes
provide no SH3 speed or compatibility proof. Primary-source research and ABI,
driver and game differences remain in roadmap supporting notes. No downloaded
script executed or new reference clone created.

## RED → GREEN → design review

- Viewport RED: `.port-cache/runtime-tests/20261113T192434572559Z`, real Mesa
  pixels pass but130 viewport updates include110 unchanged payloads. Earlier
  observer setup failure at192401 was corrected before behavioral RED.
- Viewport GREEN: build `.port-cache/builds/20261113T192520200872Z`, suite
  `.port-cache/runtime-tests/20261113T192553874088Z`:30 pass,83 explicit skips.
  Updates20, repeats0. Each linked program retains half-pixel and viewport values
  independently; initial zero values still upload. Design review found small
  explicit blocks clear; no structural refactor needed.
- Constants RED: `.port-cache/runtime-tests/20261113T192651640866Z`,23 constant
  updates include17 unchanged payloads. Existing viewport regression remains green.
- Constants GREEN: build `.port-cache/builds/20261113T192751642769Z`, suite
  `.port-cache/runtime-tests/20261113T193144446511Z`:31 pass,83 explicit skips.
  Constants6 updates,0 repeats; viewport20 updates,0 repeats. Independent indexed,
  skinning, precision, depth/stencil and presentation pixels pass. Compare full
  effective constant arrays **after** vertex declaration overrides; preserve
  original writes to device constants. Byte comparison preserves signed zero and
  NaN payload distinctions. First-use validity belongs to each linked program.
  Design review retains explicit GL calls; no shared abstraction needed.
- Supported capability RED: `.port-cache/runtime-tests/20261113T193514093254Z`,
 381 identical repeated enable/disable requests observed while culling, scissor,
  depth/stencil, preview and presentation pixels pass. Candidate central cache
  covers actual entry points used by draw, Clear, Present and resource helpers.
  Unknown capabilities forward unchanged; loader reload discards valid flags.
  GREEN `.port-cache/runtime-tests/20261113T194056230743Z`:32 pass,83 explicit
  skips; toggles533→152, repeats381→0. Build
  `.port-cache/builds/20261113T193936846506Z` exits0. Design review confirms all
  renderer capability writers use loaded entry points, including Clear, Present
  and copy helpers. Unknown DITHER/depth-clamp calls still forward unchanged.
  No further refactor required. Native candidate
  `r36s-dumps/sh3/20261113T194307194194Z-e58ee8` passes all23 graphics checks.
- Raster-state RED: focused run
  `.port-cache/optimization-uniforms/raster-red` observes606 viewport,
  depth-range/function and color/depth write-mask requests,591 repeats. All
  independent pixel markers pass. Initial full-suite run at194346 used an
  incorrect evidence-marker name; corrected before behavioral RED.
- Raster-state GREEN: build `.port-cache/builds/20261113T194541614970Z`, suite
  `.port-cache/runtime-tests/20261113T194629769109Z`:33 pass,83 explicit skips.
  Raster requests606→15, repeats591→0. Capability requests remain152, repeats0.
  Central wrappers preserve writes from Clear, Present and copy helpers. Invalid
  viewport dimensions/depth functions still reach driver. Loader resets validity;
  depth-range wrapper captures GLES adapter after installation. Design review
  retains this single source of driver state, with no further refactor needed.
  Native `r36s-dumps/sh3/20261113T194851869334Z-3de25e` passes all23 graphics checks.

Uniform candidate SHA-256:
`81bd760861735f06371df7558ac19dd9888eb29fff55850e50db6590a72da2db`.
Native Mali graphics `r36s-dumps/sh3/20261113T193306782175Z-728eb0` exits0,
execution/collection0; all23 actual `GraphicsEvidenceTests` pass. Pixel checks
include indexed/base-vertex, skinning, RHW, palette alpha, texture updates, copies,
preview, depth/stencil and presentation.

## Matched hardware results so far

Fixed room210, identical checkpoint, camera and55–95s warm window; no images.
Draw/CPU/Present measurements overlap and must not be added as independent costs.

| Candidate | Internal | FPS | Median thread CPU ms | Evidence run |
| --- | --- | ---: | ---: | --- |
| Before these slices |640×480|13.5846|42.392|`20261113T174837069025Z-36b849`|
| Before these slices |320×240|17.0724|42.849|`20261113T175211968006Z-bdd0f6`|
| Uniform caches |640×480|13.1401|42.761|`20261113T193508541838Z-55c0e2`|
| Uniform caches |320×240|17.0847|42.834|`20261113T193910083639Z-8cad03`|
| Uniform + capability caches |320×240|17.1826|42.569|`20261113T194523268733Z-d54fc3`|
| Uniform + capability + raster caches |320×240|17.7828|41.337|`20261113T195356612473Z-4943f5`|

All listed hardware runs executed and collected successfully, preserved seed and
restored frontend. **No repeatable material FPS gain demonstrated from these
uniform/capability caches alone yet.** Combined raster candidate shows4.16% more
FPS than17.0724 baseline in one run; confirm with repeat. Driver-call reduction
alone is not acceptance. 30FPS remains unpassed.

## Profiling overhead comparison

Saved `profile-clean-320` plan retains same100s run, Load inputs, checkpoint,
resolution and sparse observations as `profile-static-320`, disables per-frame
CSV and10ms CPU sampling. Public runner fixture RED: missing named plan in
`.port-cache/optimization-uniforms/clean-scene-red`; GREEN: all14 frontend tests
in `.port-cache/optimization-uniforms/clean-scene-green`. Review keeps declarative
plan reuse and no additional execution path.

Sparse observations need native wall time independent of emulated game clock.
Actual-launcher/checkpoint RED:
`.port-cache/issue-13/20261113T194949168327Z-profile-test` has zero native
timestamps. Candidate appends `wall_ms` only to existing60-frame PEEK messages;
preserves old prefix/address fields. Build
`.port-cache/builds/20261113T195326771447Z` succeeds. GREEN real-checkpoint test
`.port-cache/issue-13/20261113T195356602504Z-profile-test` passes:
timestamp sequence increases and matches per-frame native clock. Review keeps
one timestamp call per existing60-frame observation, with unchanged inactive
path and no extra capture. Sparse averages quantify profiler cost; cannot establish
per-frame percentiles or final30FPS acceptance.

Same binary SHA-256
`bf963ff20e2e1970447dcb5b0ce2855d4a52938a6e5aad5b60909002d117bebb`:
profiled run `20261113T195356612473Z-4943f5` sparse17.7709FPS, frames2520–3120,
wall58025–91788ms. Clean run `20261113T195808742430Z-dee5fc` sparse17.9920FPS,
frames2460–3120, wall57062–93745ms; no CSV, source preserved, execution/collection0
and frontend restored. Approximate1.24% difference includes normal run variation;
profiling is not free but cannot explain gap to30. Both retain same sparse PEEK,
stats and5s external monitor. These are coarse averages, not clean percentiles.

## Bounded compiler comparison

Existing host build now accepts only `--optimization O2` or `O3`, default O2,
records selection even if Docker unavailable and forwards explicit RelWithDebInfo
optimization level. Same compiler/image, Cortex-A35, wrap/alias and FP settings;
no fast-math/LTO added. Generation cache reused independently of optimization.
RED `.port-cache/optimization-uniforms/compiler-variant-red.stderr.txt` detects
lost O3 request in failed-build identity. GREEN corresponding
`compiler-variant-green.stderr.txt`: all4 build CLI tests pass. Review retains
small bounded argument and native validation; actual O3 build, compile-command
verification and correctness checks followed. Build
`.port-cache/builds/20261113T195825901189Z` succeeds, reuses verified generated
source; all66 compile commands contain O3 and none O2/fast-math. Runtime SHA-256
`8059e48e75aa218c2365979a7f3e629b4a53fc5ac732838b1f46f4a6fc1383be`,
26,682,856 bytes versus O2's26,551,784. Desktop full pixel reference passes in
`.port-cache/optimization-uniforms/compiler-o3-pixels`; native
`r36s-dumps/sh3/20261113T200322795377Z-1a0c9d` passes all23 graphics checks.
Matched320 `r36s-dumps/sh3/20261113T200538624914Z-34f0d6`:17.4204FPS,
CPU median41.635ms, wall median56.167ms/p9561.940ms; execution/collection0,
seed preserved, frontend restored. This does not improve O2's17.7828FPS and
41.337ms CPU. One run cannot establish a precise regression, but gives no reason
to adopt O3. **O2 retained**, O3 remains an explicit experiment only.

## Sampler object bindings

Source audit: only sampler-binding writer is shader binder; eight objects are
never deleted or rebound by Clear, Present, resources or other shader paths.
Move object binding to creation, retain existing per-stage parameter updates.
This uses existing single-context shader/sampler lifetime, without adding cache
ownership or changing texture state.

Initial full-suite test used wrong palette/mip/DXT marker names; corrected before
behavioral RED. Focused RED
`.port-cache/optimization-uniforms/sampler-bind-focused-red` observes608 object
binds,600 identical repeats; actual sampler, palette, mip, DXT, preview and
presentation pixels pass. GREEN build `.port-cache/builds/20261113T200559560599Z`
and suite `.port-cache/runtime-tests/20261113T200731181991Z`:34 pass,85 explicit
skips; binds608→8, repeats600→0. Refactor review keeps one creation-time loop;
parameter changes still update existing objects, sole binding writer audited.
Native `r36s-dumps/sh3/20261113T200941918250Z-e3148c` passes all23 graphics
checks, execution/collection0. Matched O3 sampler-only320 run
`20261113T201202275972Z-9a1a69` reaches17.9963FPS, median CPU40.765ms,
wall54.764ms/p9559.016ms. Versus O3-only17.4204FPS/41.635ms CPU this is3.31%
more FPS in one run. O2 remains default; do not attribute this comparison to
compiler or compare it as a single-variable change against O2 baseline.

## Linked sampler mask

Source audit found original draw setup visits all8 texture slots and uploads
their dirty textures even if current linked shader cannot sample them. Translated
pixel shaders can still sample a null slot, so null resource alone does not prove
slot inactive. Candidate stores active `s0`–`s7` locations at program link, returns
mask from shader binding, and binds/uploads only mask-selected stages. Active
null slots retain original zero-texture bind. No draw-time GL query added.

Forwarding observer compares texture-unit selections with actual linked-program
uniform reflection at each real draw. RED
`.port-cache/optimization-uniforms/inactive-texture-red` observes532 selections
of inactive slots out of608 selections across76 draws; palette, mips, DXT,
skinning, copy and preview pixels pass. Minimal candidate implemented after RED;
Corrected build `.port-cache/builds/20261113T202055963172Z`, SHA-256
`be19adae08aade1ca6fdce7fef65ed2499034771076db9e20d990bcd2564584c`:
GREEN `.port-cache/runtime-tests/20261113T202134320072Z`,35 pass/85 explicit
skips. Selections608→76, inactive532→0. Native
`r36s-dumps/sh3/20261113T202220817884Z-d96a42` passes all23 graphics checks,
execution/collection0. Matched O2 run `20261113T202425692865Z-6dcda1` reaches
17.9169FPS, CPU median40.659ms, wall55.510ms/p9559.027ms. This includes all
earlier caches; no isolated O2 sampler-binding comparison recorded. Review confirms
dirty uploads do not change program/VAO and persistent cache stores Key, not Prog;
each program's reflected mask rebuilt. No further structural refactor needed.

## Build cache correction

First candidate build `20261113T201522007090Z` recorded current source hashes but
reused older renderer objects. Source edits during preceding snapshot compile
had timestamps older than those objects. Regression correctly stayed RED at532
inactive texture selections; exclude that executable from optimization evidence.
Touch/rebuild of affected sources produced corrected candidate above.

Permanent fix uses content identity to assign stable snapshot timestamps;
changed source gets fresh timestamp even if original file date older than
objects. Snapshot bytes checked against recorded hashes before Docker starts.
Successful compile saves snapshot dates; invalidate before compiling so failed
or interrupted partial object updates cannot poison a source revert.

Public host CLI regression compiles and runs independent tiny native ARM64
fixture inside existing Docker image. RED
`.port-cache/optimization-uniforms/build-cache-red.stderr.txt`: changed source
still prints `first` instead of `second`. GREEN corresponding
`build-cache-green.stderr.txt`: all5 build CLI checks pass. Review replaced
inline dynamic import with ordinary hashlib import; all5 checks remain green.
Extended recovery RED `build-cache-failure-red.stderr.txt`: reverting after
failed compile prints `failed revision` instead of `second`. GREEN
`build-cache-failure-green.stderr.txt`: all5 checks pass. Review retains one
small per-file record and invalidates only compile cache metadata, preserving
prior artifacts/evidence and verified generation cache. Actual game build
`20261113T202723655047Z` uses corrected workflow and recompiles17 native units;
following layout build recompiles only changed units. Both pass runtime checks.

## Program and vertex layout reuse

Program bind RED `.port-cache/optimization-uniforms/program-red`:86 binds,
75 identical repeats. GREEN build `20261113T202723655047Z`, full suite
`20261113T202817486917Z`:36 pass/86 explicit skips;11 binds, zero repeats.
Native `20261113T202919404964Z-30d17b`:all23 graphics checks pass. Matched640
`20261113T203116251937Z-a8584f`:13.1110FPS, CPU median39.903ms,
wall75.939ms/p9579.431ms, Swap27.044ms. Lower driver CPU does not establish
faster full frames; synchronization/GPU work remains material.

Vertex layout/array-buffer RED `.port-cache/optimization-uniforms/layout-red`:
177 pointer updates/157 repeats,198 buffer binds/195 repeats. Minimal GREEN
build `20261113T203251603561Z`, full suite `20261113T203355451596Z`:
37 pass/86 explicit skips.20 pointer updates and3 buffer binds, zero repeats.
Review invalidates pointer cache for noncacheable input, VAO changes and deleted
buffers; preserves buffer-content updates. Final build `20261113T203544536426Z`,
SHA-256 `1ff2ad3add008f1bb0a0a62b6c9d526957fe543b590e4afa52650aebcde66f16`;
focused refactor check remains green. Native `20261113T203733949502Z-cd97da`:
all23 graphics checks pass. Matched320 `20261113T204125528413Z-d265f6`:
18.3734FPS, CPU median39.606ms, wall53.627ms/p9557.614ms, draw13.231ms.
Execution/collection0, source preserved. Comparison includes program-bind cache
and ordinary run variance; do not attribute whole gain solely to vertex cache.

## Mali shader-output experiment

Current comparable-port research: [Halo Mali-G31 notes](https://github.com/kirklandsig/halo-ce-anbernic-rg35xx/blob/e2b0db53e079df7f7cc807e570d3097f9da43edd/docs/MALI-G31-NOTES.md#vertex-shader-outputs-and-gl_pointsize),
exact commit `e2b0db53e079df7f7cc807e570d3097f9da43edd`,
`docs/MALI-G31-NOTES.md`. Author reports unnecessary point-size writes inhibit
Bifrost position/varying shader splitting; also reports declared uniform-array
extent affects driver cost. Hypotheses for SH3, not transferred performance
evidence. Reference H700/Cortex-A53/G31MP2/r20p0/fbdev differs from this port's
RK3326/Cortex-A35/G31/r13p0/KMSDRM. No reference script executed or clone created.
First-hand [R36S issue4](https://github.com/kirklandsig/halo-ce-anbernic-rg35xx/issues/4)
reports working newer release on dArkOS, without establishing SH3 performance.
Official [PortMaster FNA guide](https://portmaster.games/contribute/porting/engines/fna/)
direct fetch unavailable; current indexed full guide describes tile/target costs.
Existing upstream SH3/SH2/PortMaster findings
remain in optimization roadmap; no firmware/driver change inferred here.

SH3 emits point size for every translated draw. Added launcher diagnostic first:
RED `primitive-fixture-red` misses new transition marker; GREEN
`primitive-fixture-green` passes independent triangle/point/line pixels using
unchanged renderer. Four point-draw interfaces covered. Separate real GL observer
RED `primitive-output-red`:79 nonpoint draws write point size; point draws and
all existing pixels pass. Candidate adds primitive bit to program key and omits
write only for nonpoints; invalidates persistent key format explicitly. GREEN
build `20261113T204504889843Z`, suite `20261113T204554113461Z`:39 pass,
86 explicit skips. Observer:4 point draws,79 other draws, no missing or unused
point-size output. Refactor releases original diagnostic index buffer before
replacement; build `20261113T204718752223Z` and both focused checks pass.
Native `20261113T204802314266Z-63a0dd`:all24 graphics checks pass. Matched320
`20261113T205023266100Z-848fa6`:18.0937FPS, CPU median39.567ms,
wall54.667ms/p9558.130ms, draw13.291ms. Previous18.3734FPS/39.606ms CPU;
no gain established at320.640 GPU-bound comparison still needed. No claim that
Halo result transfers. Execution/collection0, source preserved.

## Bounded vertex constants

Following same pinned Mali source, investigate declared array extent and submitted
payload. [Khronos ES3.2 spec](https://registry.khronos.org/OpenGL/specs/es/3.2/es_spec_3.2.pdf)
defines active-array extent and ignores writes beyond highest active element;
those writes still cost host work. Existing diagnostic uses original sample's
color c0 and matrix c2..c5, with relative-index skinning as separate safety case.
Observer queries real linked active extent without changing production GL.
RED `.port-cache/optimization-uniforms/constant-range-red`:450 excess vec4
register uploads while independent pixels pass. Candidate computes conservative
bytecode constant extent, includes every matrix row, retains all96 registers for
any relative source, and bounds declaration/cache/upload to that extent. No
bone-count truncation, changes to declaration overrides, or FP precision change.
GREEN build `20261113T205127762508Z`, full suite `20261113T205155242377Z`:
40 pass/87 explicit skips;6 vertex constant uploads, zero excess registers.
Review confirms count includes matrix expansion, conservatively retains96 for
relative sources, and leaves device declaration constants applied before cache
comparison. No structural refactor needed. Native
`20261113T205436192458Z-070da1`:all24 graphics checks pass. Matched320
`20261113T205728572555Z-df5a0d`:18.5229FPS, CPU median39.918ms,
wall52.952ms/p9558.456ms, draw13.471ms, Swap7.006ms;741 frames in matched
room210 55–95second window. Execution/collection0, source preserved. Small
FPS increase over18.0937 is not proof of isolated gain; CPU median did not fall.

## Worker-context capability probe

Before attempting queued GL execution, verify context transfer with actual
firmware SDL/KMSDRM/Mali, not Halo's fbdev results. SDL documents
[MakeCurrent](https://wiki.libsdl.org/SDL2/SDL_GL_MakeCurrent) and
[SwapWindow](https://wiki.libsdl.org/SDL2/SDL_GL_SwapWindow); its
[development FAQ](https://wiki.libsdl.org/SDL2/FAQDevelopment) cautions that video
backends generally expect main-thread operations. Source for target SDL version,
[`release-2.32.10/src/video/kmsdrm/SDL_kmsdrmopengles.c`](https://github.com/libsdl-org/SDL/blob/release-2.32.10/src/video/kmsdrm/SDL_kmsdrmopengles.c),
waits for previous page flip, swaps EGL buffers, locks GBM front buffer, and queues
DRM page flip. Interval0 is asynchronous only when supported; double-buffer hint
can introduce immediate page-flip wait. Source alone does not prove target's
exact build or worker compatibility. No swap-interval change made.

Launcher-level RED `worker-probe-red` lacks worker marker. Minimal diagnostic
detaches existing context, transfers it to one joined SDL worker, clears/reads
magenta pixel, swaps, detaches and restores original thread before all existing
renderer oracles. GREEN `worker-probe-green`; build `20261113T205759164217Z`,
full suite `20261113T205927592190Z`:41 pass/87 explicit skips. Review confirms
single context owner at a time, joined worker, restoration on failure, and no
worker during normal game rendering. Native `20261113T210303149072Z-ae8b47`:
all25 graphics checks pass, including distinct worker, magenta pixel, swap and
context restoration. No queued GL renderer implemented; probe pass alone does
not establish performance gain.

Latest matched640, including output/constant changes,
`20261113T210643704451Z-9f0789`:13.2611FPS, CPU median39.752ms,
wall75.198ms/p9579.488ms, draw13.575ms, Swap26.301ms.530 matched frames;
execution/collection0, source preserved. No meaningful640 improvement established.

## Last-presented frame texture rotation

Current [PortMaster FNA guidance](https://portmaster.games/contribute/porting/engines/fna/)
and [Arm framebuffer guidance](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-2-how-to-correctly-handle-framebuffers)
identify extra target binds/resolves as avoidable work. Comparable Halo notes
above support hypothesis only. Searches for `PortMaster glBlitFramebuffer stale
framebuffer GetFrontBuffer glReadPixels` and `PortMaster Mali GetFrontBuffer
SwapEffect DISCARD` found no matching SH3-style first-hand fix. No external code
executed. [Microsoft swap-effect contract](https://learn.microsoft.com/en-us/windows/win32/direct3d9/d3dswapeffect)
allows discarded back-buffer contents to change and requires COPY contents to
remain. D3D9 reference is contract comparison, not proof of this D3D8 runtime.

Added requested swap-effect log with launcher regression. Initial test inspected
stdout although `rt_log` uses stderr; discard that failed setup run. Corrected RED
`swap-mode-red-corrected` against previous artifact misses field; GREEN
`swap-mode-green-corrected` passes. Build `20261113T210439022211Z`, runtime suite
`20261113T210644882526Z`:42 pass/88 explicit skips. Design review keeps one
startup-only field, no per-frame logging. Actual640 game run above reports
`swap_effect=1` (DISCARD), establishing eligibility for buffer rotation.

Expanded public Reset/Clear/Present/GetFrontBuffer diagnostic covers three color
frames, DISCARD/COPY modes,64x48 and80x60 resets, destination outside untouched,
opaque returned alpha and COPY back-buffer preservation. RED
`front-modes-fixture-red` misses new marker. Baseline implementation of diagnostic
exposes stale repeated front pixels in Docker Mesa, saved under
`front-modes-fixture-debug`, `front-modes-fixture-debug2` and real forwarding
`front-modes-trace2`; ordinary existing graphics checks still pass. Extra COPY
readback changes result, so do not infer Mali failure or add synchronous readback
as fix. Baseline native `20261113T211508097032Z-bf1e61` passes all26 graphics
checks, including new repeated pixels: observed failure is Mesa-only so far.
Conservative DISCARD texture rotation retains original copy path for other modes,
resets front storage on Reset, and keeps last-presented texture distinct from
next back buffer. No fades, thumbnails or visual features removed. GREEN
`front-rotation-green`, build `20261113T211604706058Z`, full regression
`20261113T211717384637Z`:43 pass/88 explicit skips.

Real GL/SDL forwarding observer separately checks copies before each swap.
Ignore initial cost invocation with nonexistent prior-artifact path: setup error,
not RED. Correct baseline `front-copy-cost-red-corrected` sees one offscreen
snapshot copy for each DISCARD Present. Candidate `front-copy-cost-green` sees
zero; COPY retains one, screen presentation remains one per frame. Original
preview fade and repeated pixels pass. Review confirms texture ownership stays
distinct across rotations, spare matches back-buffer format, next target gets
reattached by existing Present cleanup, and Reset deletes both owned textures
through their respective owners. Indentation-only refactor build
`20261113T211941054646Z`; full review suite
`20261113T212122866310Z`:44 pass/89 explicit skips. Actual candidate native
`20261113T211746797564Z-a879e9`:all26 checks pass, execution/collection0.
Matched640 `20261113T212121691966Z-855220`:13.4006FPS,536 frames,
wall median72.439ms/p9577.333ms, CPU median40.161ms, draw13.341ms,
Swap23.834ms. Includes799.811ms worst frame; no outlier removed. Previous
13.2611FPS does not establish substantial gain. Execution/collection0, source
preserved. Matched320 `20261113T213023229433Z-40bd06`:18.6087FPS,745
frames, wall median52.886ms/p9557.799ms, CPU39.450ms, draw13.204ms,
Swap7.662ms. Execution/collection0, source preserved. Removed call alone is not
FPS acceptance.

## Immutable framebuffer pairs

Current official PortMaster FNA guide remains indexed but direct fetch unavailable.
Searches `site:portmaster.games glCheckFramebufferStatus framebuffer performance`
and `site:github.com PortMaster framebuffer cache Mali glCheckFramebufferStatus`
find no matching SH3 first-hand fix. Pinned Halo architecture
[`e2b0db53e079df7f7cc807e570d3097f9da43edd`](https://raw.githubusercontent.com/kirklandsig/halo-ce-anbernic-rg35xx/e2b0db53e079df7f7cc807e570d3097f9da43edd/docs/ARCHITECTURE.md)
describes framebuffer cache by color texture/mip and depth texture. Its H700
fbdev pacing and newer Mali driver differ from R36S KMSDRM/r13p0; no hardware
pacing code copied. GL framebuffer completeness changes with attachment image
definitions; cache must invalidate when owned texture is deleted or shared depth
storage is resized. Khronos wiki direct fetch now403; ES3.2 spec above remains
normative reference. Comparable port establishes approach only, not acceptance.

Real GL forwarding observer `tests/framebuffer-cost.c` counts attachment calls
and repeated status queries against unchanged framebuffer/storage. Initial
observer compile error (`read` identifier collides with POSIX API) is setup
failure, excluded. Corrected RED `framebuffer-red-corrected`:137 attachment calls,
71 repeated;49 status checks,18 repeated, independent pixel oracles pass.
Minimal candidate caches each color target/face/mip plus depth target/mip,
retains retry/logging for incomplete entries, deletes referencing FBOs before
texture deletion or shared depth redefinition. Present uses separate cached
back-buffer read FBO and cannot mutate cached draw attachments. GREEN
`framebuffer-green`, build `20261113T213134430664Z`:59 attachment calls,
zero repeated;17 status checks, one intentional diagnostic recheck. Full runtime
`20261113T213251620619Z`:45 pass/89 explicit skips. Review confirms attached
images remain fixed until deletion/redefinition, mip/face is part of key, and
temporary read/copy FBOs remain separate; no structural refactor needed. Native
`20261113T213413990250Z-8af939`:all26 graphics checks pass. No visual settings or
guest timing changed. Matched640 `20261113T213702955634Z-f70b12`:14.2216FPS,
569 frames, wall median69.906ms/p9575.926ms, CPU38.989ms, draw13.209ms,
Swap23.206ms. Execution/collection0, source preserved. Matched320
`20261113T214318187972Z-ef7a00`:18.6131FPS,744 frames, wall median52.719ms/
p9557.702ms, CPU39.127ms, draw13.256ms, Swap7.989ms. Execution/collection0,
source preserved. This run's binary includes disabled-by-default queue code;
no queued submission enabled. No320 gain established from framebuffer cache.

## Ordered worker GL submission

Capability probe above passes actual SDL2.32.10/KMSDRM/Mali context transfer.
Pinned Halo architecture lines325–454 provides comparable CPU/GL overlap model;
its H700-specific fbdev timing is excluded. CCE currently returns historical dumps
instead of requested runtime shutdown definitions; scoped source fallback finds
game's existing SDL/game owner thread in `src/runtime/rt_core.c`, with `exit()`
on guest return. No new external code executed.

Launcher RED `thread-red`:all83 draws occur on loader/game thread. Minimal
ordered queue uses three reusable command chunks, one context owner, copied
buffer/uniform payloads, synchronous queries/texture/shader inputs, and at most
one frame ahead. Native renderer supplies VBO/EBO offsets, not client arrays.
Normal exit drains/joins worker and restores original context before deletion.
Initially experimental `SH3_GL_THREAD=1` opt-in. GREEN `thread-green`, build
`20261113T214056079796Z`:all83 draws and86 buffer uploads reach one worker,
zero main-thread submissions; independent pixel/readback/reset/front oracles
pass, context restoration reports success. Full runtime
`20261113T214316995797Z`:46 pass/89 explicit skips. Design review checks chunk
ownership under mutex, ordered synchronous outputs, copied transient inputs,
single producer guard and context restoration; no extra structural refactor.
Follow-up regression `thread-capability-red` exposes context identity bug:
producer's SDL current context is NULL after transfer, so compression capability
cache mistakenly keeps its uninitialized state and decodes supported S3TC.
Explicit owning-context accessor fixes identity without moving GL queries off
worker. GREEN `thread-capability-green`, build `20261113T214508820281Z`, restores
native S3TC selection and all original pixel oracles. Default-profile RED
`thread-default-red` lacks enabled marker; build `20261113T214711301623Z`
enables ordered worker by default while explicit `SH3_GL_THREAD=0` keeps original
submission. GREEN `thread-default-green`; full suite
`20261113T214735724551Z`:48 pass/90 explicit skips. Default and explicit opt-out
both retain pixels and frontend return; review retains same bounded queue design.
Native baseline `thread-native-red.txt` lacks renderer-worker marker. Candidate
`20261113T214746275117Z-117ef9`:all27 native graphics checks pass, including
queued suite completion and context restoration; execution/collection0.
No threaded FPS acceptance yet. With threading, main-thread draw/Swap profiler
columns measure queue work/backpressure rather than worker driver durations.

Snapshots before this task in `.port-cache/optimization-uniforms/before/` preserve
older issue9/13 work. No staging, commit, push, GitHub post or issue closure.


### Queue overlap and actual swap completion follow-up

Queued candidate `20261113T214711301623Z` passes all three actual-checkpoint
movement/collision/combat pairs in `.port-cache/movement-tests/20261113T215042690082Z`.
Movement reference599.996 vs delayed597.513 units/s (ratio0.99586); both fire3 rounds.
Matched room210 producer cadence remains18.1826FPS at320 (`20261113T215004115564Z-4de73c`)
and13.7521FPS at640 (`20261113T215445141045Z-71de82`), versus18.6131/14.2216 for
preceding FBO candidate. All run/collection statuses0 and source checkpoints preserved.
No FPS gain established. Main-thread CPU p50 drops to28.743/28.410ms while draw
elapsed p50 rises to20.837/39.294ms: likely serialization to investigate, not acceptance.
Queued draw/Present/swap fields describe producer recording and backpressure;
actual SDL completion must be measured separately. Frame summaries retain all outliers.

Actual-swap profiler RED `.port-cache/optimization-uniforms/swap-timing-game-red`
reaches real checkpoint but lacks requested completion CSV. Earlier graphics-only
attempt cannot map game globals and is excluded as setup failure. GREEN
`swap-timing-game-green` uses build `20261113T215905792634Z`, real checkpoint and
independent real SDL forwarding observer with20ms boundary delay: completion CSV
matches actual swap count, monotonic frame IDs, room/resolution metadata and >=19ms
worker swap durations. No pixel capture, GPU flush/query or driver substitution.
Producer snapshots guest metadata; worker owns separate `.presents.csv` report.
Design review: no guest reads/shared FILE on worker; disabled mode reads no clock.
Actual device completion measurements pending. No30FPS claim or publication.


Per-API census RED `queue-census-red-corrected` lacks counters for real330 uniform
lookups. GREEN `queue-census-green-corrected`, build `20261113T220243018003Z`,
matches independent GL observer330 locations/107 reads. One earlier context-probe
read is deliberately excluded from observer after setup mismatch; no driver
result replaced. Initial logger compile macro-field collision fixed before
successful build. Whole suite `20261113T220309225507Z` has48passes/90skips and
one old-observer failure; corrected focused census passes. Full suite rerun
required with next candidate. Optional profile mode records waits by API only;
normal gameplay skips timing/counter work. Design review: counters producer-only,
printed after worker drain, no worker races or per-call allocation.

Actual checkpoint census with20ms injected SDL delay (`queue-census-game-green`)
passes completion/pixel-free profile test and finds3399 synchronous sampler-vector
updates taking42789.572ms including queued work.900 uniform lookups equal30programs
with30 initial locations each; no evidence to prioritize three fixed-lighting
lookups in this checkpoint. Native census run pending. Sampler async behavior
RED `sampler-queue-red` preserves existing pixels but reports23 sampler-vector
queue drains; next minimal change copies one scalar/four border components into
ordered owned command memory per Khronos sampler contract. Device throughput
still must establish benefit, with native borders/filtering/preview/reset checks.


Native census build `20261113T220243018003Z`, run `20261113T220350711832Z-1bf1d0`:
actual SDL completion18.79276FPS (752frames,55–95sroom210), wallp50=51.9485ms,
p95=58.213ms,p99=61.370ms,max74.688ms; actual swap p50=6.619ms. Producer
cadence18.79214FPS.11,016 sampler-vector waits total22,966.094ms;2,077 texture
subimage waits6,324.868ms. All statuses0, checkpoint preserved. Totals cover whole
run; not warm-frame GPU execution times and not additive to frame medians.

Sampler owned-payload GREEN `sampler-queue-green`, build
`20261113T220721050757Z`: real23 border updates, zero sampler queue drains,
existing sampler/border/linear/mirror pixels pass. Full suite
`20261113T220758882338Z`:50PASS/90explicitSKIP,140total. Design review keeps
one scalar/four border components per normative parameter width, copies input
before producer stack reuse, retains order/GL errors and single-thread fallback.
Native pixel and matched FPS comparison pending. No30FPS or publication claim.


Sampler candidate native graphics `20261113T220811668193Z-dc999c`:27/27PASS,
all execution/collection statuses0; border/linear/filter/mip/palette/reset/front
pixels and context return retained. Sampler-only320 throughput run started before
next artifact change. Next texture-queue RED `upload-queue-red` reaches all format,
row/mip/palette/copy pixel oracles but still reports104 ordinary and50 compressed
upload queue drains. Production draft copies known packed/byte pixels using
ordered unpack shadow state; unknown formats/PBO offsets stay synchronous.
No acceptance or speed gain inferred before build/native measurement.

Sampler-only320 native run `20261113T221057428281Z-563aae` regresses actual
completion to17.00733FPS (680frames,55–95sroom210): wallp50=65.457ms,
p95=67.006ms,p99=67.953ms,max68.813ms. Actual swap p50=13.8605ms;
main CPU p50=28.0098ms, producer draw=25.7695ms. Sampler waits disappear,
but1,895 texture-subimage waits total19,962.780ms. All statuses0 and source
checkpoint preserved. This moves serialization rather than establishing gain;
proceed with owned texture payloads, then repeat matched actual-completion run.

First texture draft build `20261113T221443309868Z` fails link because initial
unpack queries use raw GL symbols in loader-implementation unit. Correct to
existing loaded pointers before retry. Failed build supplies no runtime evidence.

Texture owned-payload GREEN `upload-queue-green`, build
`20261113T221740790870Z`: real104 ordinary/50 compressed uploads, zero upload
queue drains, all original format/palette/mip/DXT/locked-target/copy-tail pixel
oracles pass. Design review keeps ordered pixel-store shadow, exact last-row
extent, owned copied payload, original null pointer behavior and conservative
unknown-format/PBO fallback. No new GL flush/readback or altered image format.
Full runtime, native27 graphics and real-checkpoint profile regressions pending.

Texture candidate full runtime `20261113T221827218176Z`:51PASS/90explicitSKIP,
141total. Actual-checkpoint completion-profiler test `upload-game-green` passes
with independent20ms SDL boundary delay. Native graphics run
`20261113T221827226850Z-327745`:27/27PASS, all execution/collection statuses0;
pixels, reset, front-image modes and worker context return retained. Matched320
completion throughput run now starts. Thirty-FPS acceptance remains unpassed.

Owned-texture320 run `20261113T222100286164Z-164388` reaches29.97530FPS actual
SDL completion (1199frames,55–95sroom210): mean33.3608ms,p50=33.316ms,
p95=34.200ms,p99=35.266ms,max50.097ms, all outliers retained. Main CPU
p50=28.7875ms,p99=30.5955ms; producer draw p50=3.946ms. Hot sampler/subimage
queue waits all disappear; remaining initialization/output API waits retained.
All statuses0, source checkpoint unchanged. This establishes near30 cadence on
one stationary checkpoint, not acceptance for monster room, movement or campaign.
Same candidate640 run pending; keep all edits local and issues open.

Optional GPU timing RED `gpu-timer-red` retains existing graphics pixels but lacks
requested GPU report. Next diagnostic slice uses eight delayed query objects,
checks availability before64-bit reads, rejects disjoint intervals and never waits
or calls glFinish. Counter bits/entry points must work on actual native provider;
CPU/swap time is not GPU occupancy. No production performance claim from this slice.

Same owned-texture candidate640 run `20261113T222501783735Z-2177ee`: actual SDL
completion21.75640FPS (870frames,55–95sroom210), mean45.9635ms,p50=45.6145ms,
p95=49.885ms,p99=50.684ms,max52.539ms. Main CPU p50=28.2211ms,draw3.793ms;
worker SDL swap p50=33.7505ms. All statuses0 and source checkpoint preserved.
Improvement over queued64013.7521 does not meet30FPS; GPU elapsed region is next
missing attribution. No firmware/clocks/settings/visual-feature changes used.


GPU diagnostic GREEN `gpu-timer-green`, build `20261113T222943152545Z`: real
15 begin/end pairs,14 available64-bit reads; zero premature reads, main-thread
query calls or forced finishes. Unavailable-entry-point and explicit-disable
regressions preserve graphics. Full runtime `20261113T223112178582Z`:
54PASS/90explicitSKIP,144total. Existing pixel/front/depth checks pass.

Native640 diagnostic `20261113T223112187035Z-7965b3`: all statuses0 and source
checkpoint preserved. Provider supplies64 counter bits,3476 rows, zero skipped
frames and one disjoint-discarded interval. Warm55–95sroom210 has824 rows;
raw query mean0.888596ms,p50=0.892129ms,p99=0.970312ms,max1.031177ms.
These small values do not explain actual swap p50=36.739ms. Do not interpret
as full-frame GPU cost or unused GPU capacity. Actual completion20.60076FPS,
wallp50=48.4365ms,p99=52.602ms,max56.380ms, versus21.75640FPS without
queries in preceding same-resolution candidate. Possible instrumentation/driver
ordering effect; queries stay disabled for acceptance cadence. Raw summaries:
`frame-summary.json` and `gpu-summary.json` under native run. External same-family
reports and different-device ANGLE workaround retained in renderer research;
no flush, fence wait, driver change or external code adopted.

Handheld profiling launcher RED `handheld-profile-red` loses requested frame
CSV. GREEN `handheld-profile-green` retains CSV/resolution through detached
service while removing injected input/captures/stats;15 frontend regressions
pass. Host CLI RED `handheld-cli-red.txt` rejects missing option; GREEN
`handheld-cli-green.txt` passes profile payload/failure collection plus existing
persistent import. Shared external-process fixture refactored first and old test
rerun green. Device-workflow first draft test had missing parent directory
(setup failure, not RED). Corrected `handheld-workflow-red-valid` reaches game
but loses CSV; GREEN `handheld-workflow-green` retains selected320 profile,
GPU queries disabled, isolated state and frontend restoration. Full frontend
`handheld-workflow-regression`:16PASS. Design review keeps explicit payload
marker, validates resolution, rejects conflicting persistent/import modes and
forwards GPU-disable setting across service boundary. Device behavior pending
actual run started with owner available; no hardware claim from fixtures.


Final owned-payload/GPU-diagnostic candidate movement suite
`.port-cache/movement-tests/20261113T223934122860Z`:3PASS in480.496s. Real
checkpoint launcher checks retain movement speed under added presentation delay,
collision/wall-clock behavior at lower profile and repeated-fire cadence. This
supports timing correctness; Docker does not pass handheld performance/audio.
Host profile guard regressions `handheld-cli-regression.txt`:3PASS, including
both resolutions, failure collection and rejection of conflicting state/replay.
Shell syntax and `git diff --check` pass. No repository files staged or committed.

Frame-only profiling must not silently enable GPU queries: initial graphics-mode
attempt `gpu-opt-in-red` crashes because ordinary frame profiler reads guest
state unavailable in diagnostic-only process; setup mismatch, not valid RED.
Moved assertion to actual checkpoint boundary: `gpu-opt-in-game-red` fails after
63.137s because requested frame-only run prints GPU-enabled and creates extra
GPU report. Minimal initialization guard now requires explicit GPU flag/path.
Build and GREEN deferred until active device host invocation finishes; current
handheld binary is prior verified candidate with explicit `SH3_GPU_PROFILE=0`.

GPU explicit-opt-in build `20261113T230334757532Z` completes. Real-checkpoint
GREEN `gpu-opt-in-game-green`:1PASS/62.968s. Full runtime
`20261113T231041202708Z`:54PASS/94explicitSKIP,148total. Initialization guard
returns before GL lookup unless GPU flag/path explicitly set; existing1/path/0
behavior retained. No hot-path change for handheld's explicit GPU0 setting.

### Latest handheld evidence and unattended follow-up, 2026-11-14

Handheld320 run `20261113T224430930288Z-893847` collected successfully; execution1
because service timed out at15min31s (exit143), not established game crash.
Frontend active afterward; checkpoint/config/cache hashes preserved. Frame and
actual completion CSVs retained, CPU samples empty because forced stop bypassed
atexit writer. No claim of successful graceful shutdown. Owner clarifies lag was
amusement park, much smoother/playable; audio and controls fine. Room IDs below
are observed identifiers, not independently mapped location names.

Actual completion room210 visits:30.176,28.292,28.775FPS; room211 visits:31.185,
27.837,26.645,27.229,25.457FPS. Busy later visits have p95 around50ms and p99
51–55ms, so20FPS-equivalent slow frames remain. Loading/transition outliers retained
in `handheld-summary.json`, including2783.965ms maximum on first room210 visit.
Light room212 segments average39–53FPS; menus are not excluded, so these are not
established gameplay throughput. Late busy main-thread CPU medians30.8–31.2ms,
draw4.1–4.6ms. Actual swap overlaps producer work; durations are not additive.

Monitor reaches83.076°C; CPU1512MHz drops repeatedly to1296/1248/1200/1008MHz,
GPU520MHz to480/400MHz while performance governors remain selected. Consistent
with thermal management; thermal-trip transitions not directly logged. Target
requires sustained checks, not a cool stationary-room average. No clock, thermal,
firmware or driver policy changes authorized or made.

Owner cannot test further; authorizes unattended movement/combat, other levels
and public saves. Target remains30FPS, brief25FPS dips accepted,15–20 not accepted;
no precise duration allowance agreed. Physical reports above remain scoped to
observed session; automated tests cannot add listening acceptance.

Unattended plan `performance-route-320` CLI RED `auto-route-red.txt` rejects
unknown plan; GREEN `auto-route-green.txt`:4PASS/2.635s. Plan reuses isolated
scene engine,180s, no captures, read-only observations plus movement/turn/fire.
Actual route validation pending; scripted input alone does not prove active play.
Public save-pack provenance and applicability tracked in research notes.

Startup margin RED `startup-margin-red`: external service clock fixture kills
35s startup before requested complete play interval/profile flush (exit124),
frontend recovered. GREEN `startup-margin-green`:17PASS/4.333s with service
startup/flush allowance90s; outer device140s and host180s allowances include
40s stop and cleanup. Ordinary untimed launches remain unbounded. Design review
keeps finite nested watchdogs and existing service/launcher boundary. Actual
native orderly route exit remains required; fixtures do not prove device timing.

First native unattended route `20261113T231916037514Z-88a0a8`: execution and all
collections0, orderly ExitProcess0, source preserved. Room21075–180s actual
completion29.78975FPS/3128frames, p50=33.327ms,p95=34.083ms,p99=35.581ms,
max645.777ms. One-second window minimum11FPS; five-second minimum26FPS. Retain
hitch, so this is not passing profile. Read-only observations find50 distinct
positions, health100 and changing handgun-ammunition values; repeated attacks
occur, though enemy density and other rooms not established. Clocks stay
CPU1512/GPU520MHz, max71.666°C. `route-summary.json`, `cpu-symbols-route.json`
retain raw analysis. Main producer hitch has615.159ms draw wall but38.811ms CPU,
consistent with blocking renderer/driver work; exact cause not yet proven.

Thirty-FPS pacing RED `fps-pacing-red`: real active menu60.02368FPS despite
requested limit30. Initial phase-accumulating candidate `fps-pacing-green`
averages29.60 but repays scheduler delay with short intervals. Per-swap-entry
reset candidate `fps-pacing-green-fixed` falls23.37FPS because render work is
outside budget. Both rejected. Cadence assertion refined from universal30ms
minimum interval to at most31 actual completions per one-second window: variable
swap duration can shift individual timestamps, while debt-driven bursts must
remain bounded. Original valid RED upper30.5FPS assertion unchanged.
Initial regression suite also exposes unprofiled crash: unconditional timing
stamp passed into profiler's zero-stamp disable contract. Restored conditional
stamp at call; no native deployment of failed candidates. Worker-release reset
candidate also fails at26.56FPS. Final candidate keeps absolute phase, includes
render work, discards debt once more than one period late and sleeps without
spinning. GREEN `fps-pacing-green-phase`: actual menu cadence passes target and
one-second burst bound. Full runtime54PASS/97SKIP,151tests/102.342s, evidence
`.port-cache/runtime-tests/20261113T233741829572Z`. Skips include device/owner data,
so these do not establish native performance. Unprofiled graphics passes again.

Detached scene limit RED `fps-scene-red`: requested30 disappears at runtime;
GREEN `fps-scene-green`:18PASS/4.611s after explicit parser/allowlist forwarding.
Route configuration RED `fps-route-red.txt`: deployment lacks requested limit;
GREEN `fps-route-green.txt`:4PASS/2.675s. Only0/30 accepted in scene plans; absent
limit retains default. Runtime completion CSV records actual SDL return before
intentional sleep. Movement/timer/fire regressions now explicitly exercise30 cap.

Paced actual menu29.89428FPS,329frames, max31 completions/one-second window.
Native graphics run `20261113T233928477031Z-09117e`:27PASS, execution/collection0.
Cross-level default-equipment route RED `traverse-route-red.txt` rejects missing
plan; GREEN `traverse-route-green.txt`:5PASS/3.454s. No inventory assumptions,
capture or player-state mutation; actual loaded rooms and traversal still need
device evidence. Public pack entries are not yet verified playable checkpoints.

## Unattended multi-checkpoint evidence and compiled-program cache

30-cap movement suite:3PASS/480.568s,
`.port-cache/movement-tests/20261113T234045162983Z`; actual game walking, collision,
clock and repeated firing retain speed under slow presentation.
Warm key-only original route `20261113T234150572396Z-9d7776`:3112 frames75–180s,
29.63393FPS, p50/p95/p99=33.346/34.341/47.507ms, max394.756ms. Complete1s
minimum19FPS and5s minimum26.8FPS: fails owner floor. CPU1512/GPU520 throughout;
max67.307°C. Cache unchanged46records; programs still compiled46 times.

Public pack17 route `20261113T234758594655Z-18fc9f` loads room149;50 distinct
poses/55 observations, positive health195.6. Actual48–160s:3255 frames,29.06755FPS,
p50/p95/p99=33.422/34.444/49.817ms, max1673.423ms. Two dominant producer draw
stalls1073.571ms and1663.898ms remain in result, not removed as outliers.
Pack6 route `20261113T235340247130Z-a6b560` loads room18;45 distinct poses/55
observations, positive health.3296 frames,29.42778FPS, p50/p95/p99=33.355/34.689/
46.211ms, max1624.656ms. All execution/collections0, source-preserved true. Room
names and difficulty representativeness remain unverified; two additional live
rooms do not establish all-level acceptance.

Compiled-program boundary RED `shader-cache-red-observed`: actual warm launcher
compiles22 translated shaders again. GREEN `shader-cache-green`: cold22 compiles,
warm0/11 binary restores, independent graphics diagnostics retain pixels. Initial
observer setup counted shell/timeout destructor lines and was corrected before
valid RED; setup failure not counted as behavioral evidence. Build
`20261113T235939679106Z`, existing ARM64 image reused. New disposable
`sh3-gl-cache.bin` fingerprints vendor/renderer/driver/GLSL/format list and exact
vertex/fragment source. Bound32MiB total/4MiB binary/1MiB source, validate record
lengths/checksum before driver call, check link status and source fallback.
Uniform/sampler reflection and initialization run after either path. Synchronous
queue calls preserve payload/output lifetime; no shader semantics changed.
Design review retains two-function module and existing key prewarm, no new
package dependency or driver/thermal changes.

Native cold graphics `20261114T000136769101Z-7d9e0c`:27PASS, execution/collection0;
Mali cache150529bytes produced. Warm Mali gameplay acceptance pending.
Cache checkpoint transport RED `binary-cache-seed-red` loses driver cache at
launcher, GREEN `binary-cache-seed-green`:24PASS/1.148s. Host import/scene RED
`binary-cache-cli-red.txt` drops cache; GREEN5PASS/3.323s. Detached scene RED
`binary-cache-service-red` loses cache, GREEN19PASS/4.808s. Inventory RED
`binary-cache-inventory-red` loses cache; GREEN19PASS/4.873s. Source copies
unchanged in fixture checks. New file included in state/import/seed identity,
collected snapshots and replay; no original player-state writes.

First full runtime run after cache code reports54PASS/99SKIP/1FAIL,154tests:
108.950s, `.port-cache/runtime-tests/20261114T000114538879Z`. Single test reports launcher syntax during concurrent host edit; cause consistent
with changing live bind-mounted file. Current bash syntax
and full launcher/frontend classes pass. Treat this run as failed and repeat
after freezing edits; do not count it as successful regression evidence.

Frozen cache regression repeat:158tests/122.923s,57PASS/101 explicit SKIP, exit0,
`.port-cache/runtime-tests/20261114T000818752237Z`. Changed-driver and corrupt-cache
launcher checks each pass: incompatible cache rebuilt from source without loading
old binaries; damaged file rejected before driver call, independent pixels intact.

Native cold route `20261114T000545701336Z-3df01c`:29.69623FPS, max394.588ms,
minimum complete1s19FPS.47 source program compiles,825505-byte driver cache saved.
Matched compiled-cache replay `20261114T001123867295Z-26dcac` restores47 binaries,
zero source compiles/rejections. Prewarm16 programs38ms versus prior717ms.
Actual75–180s room210:3131 completions,29.81975FPS, p50/p95/p99=
33.334/34.174/44.873ms, max61.387ms. Lowest complete1s26FPS/5s28.4FPS. All statuses0,
source-preserved true. Changing player positions, positive health and changing
ammunition observed; short warm route meets owner floor, sustained/all-level
acceptance remains open. Startup ALSA underrun lines remain in logs; automated
runs cannot establish listening acceptance.

Input-schedule cache RED `input-plan-cache-red`:7780 SDL key-name lookups in actual
checkpoint versus bound128. GREEN `input-plan-cache-green`:5 lookups/1547 polls,
62.974s; checkpoint/profile/actual-SDL completion assertions pass. Build
`20261114T001700730866Z`. Parse once at first keyboard poll; retain original wall
clock, holds/overlaps and real-keyboard exclusion. Allocation checked, uncommon
separator-free entries can grow storage safely. No physical-input behavior or
simulation timestep changed; ordinary handheld FPS gain not claimed from scripted
input work. Full movement/combat regressions pending for this build.

Sustained route CLI RED `sustained-route-red.txt`: missing selected scene; GREEN
`sustained-route-final-green.txt`:7PASS, includes independent report fixture.
990-second generic plan attempts walk/turn/ready/attack through976s, no inventory
assumptions or captures. Device sustained run pending. Saved host report CLI RED
`performance-report-red.txt`: missing command; GREEN `performance-report-green.txt`:
1PASS. Independent completion timeline includes2600ms stall and two empty seconds;
report retains both zero-FPS bins, excludes partial final second and retains stall.
Actual warm report is `r36s-dumps/sh3/20261114T001123867295Z-26dcac/performance-summary.json`.

Input-cache movement/timer/collision/repeated-fire suite:3PASS/480.716s,
`.port-cache/movement-tests/20261114T002033392035Z`. Original speed retained through
installed launcher with explicit30 cap and delayed presentation. Local cache
report motion slice RED `route-motion-report-red.txt` omits player observations;
GREEN `route-motion-report-green.txt`:8PASS/4.101s including device CLI regressions.
Independent fixture retains one dead-player observation beside two actual live
positions. Warm original route has52/52 live samples and47 distinct positions;
every sampled30s block includes changing position. No automatic attack pass is
inferred from scheduled keys or movement counts.

Frozen input-cache full regression:161tests/122.857s,59PASS/102 explicit SKIP,
`.port-cache/runtime-tests/20261114T002932216212Z`, exit0. Runtime SHA256
`856d4c930c98d2c257ff3c8dd9e7e53085e5eaa933fbe447bfdd1639bcc9df01`.

## First sustained automated route with compiled cache

Native `20261114T002033400091Z-26cd9f`, build20261114T001700730866Z/O2:990s
clean timer exit, all preparation/execution/collection statuses0, source preserved.
Actual50–975s:29.93885FPS, p50/p95/p99=33.334/34.182/36.122ms, max61.830ms.
Complete1s minimum24FPS at323s and744s; complete5s minimum28FPS. No15–20FPS
windows, but two24FPS windows remain below conservative owner floor: keep30FPS
acceptance open.461/461 live player observations,372 distinct positions, every
sampled30s block contains movement. No death/menu/stuck-only interval credited.
Game clock tracks wall time0.998869× and timer59.999957ticks/s over921.884s.
Generic route leaves ammunition fields unchanged; attack attempts do not prove
firing or combat acceptance. Separate repeated-fire regression covers firing.
47binary restores, zero source compiles/rejections. Monitor CPU1512MHz/GPU520MHz
throughout, temperature57.272–73.750°C, final71.250°C; no observed clock reduction.
Previous physical run reached83.076°C with clock reductions, but route/initial
conditions differ, so this is not a controlled9.3°C improvement claim.

Early75–180s29.93350FPS, main CPU p50/p95=28.631/30.409ms; final900–975s
29.95785FPS, CPU29.061/30.628ms. Slow322–326s CPU max44.902ms, while740–746s CPU
max31.230ms; transient CPU work plus presentation/queue scheduling need headroom.
32768CPU sample slots fill and49540 later samples drop; no late-PC attribution
claimed. Per-frame CPU/completion CSV and5s clocks/thermals continue through end.
Next comparison uses already-supported O3 flag with unchanged FP/wrap/alias rules;
no new game-logic, driver, clock, thermal-policy or graphics cuts.

Additional public save28 captured desktop check passes1test/145.281s with112
captures and clean exit, actual room240. `.port-cache/optimization-uniforms/cross-level-28-captured/`.
Full reference suite with save28 and traverse plan also exits0:161tests/619.740s,
94PASS/67 explicit SKIP, `.port-cache/runtime-tests/20261114T003220348333Z`.
Reference harness uses its own capture/resolution settings; neither desktop run
establishes handheld performance. Captured check validates basic load/render
compatibility only; native room240 performance remains untested.

## O3 comparison after asynchronous upload/cache work

Build `20261114T004219100525Z`, runtime SHA256
`ebcfe2d45c8c06ca18f50db812ec503aea8af617a947674d414d151d052cb7d6`.
Same existing ARM64 image, GCC12.2, CortexA35, wrap/noalias and FP semantics;
only existing optimization option changes O2→O3. ELF text26323689→26554135bytes
(+0.88%); no fast-math, LTO, clock, driver or graphics-feature change.

Native graphics `20261114T004722547069Z-8bcafd`:27PASS, all host stages0.
Movement/timer/collision/repeated-fire regressions:3PASS/480.587s,
`.port-cache/movement-tests/20261114T004722539336Z`. Frozen full runtime:
161tests/123.396s,59PASS/102 explicit SKIP,
`.port-cache/runtime-tests/20261114T005605675422Z`. Skips do not imply device pass.

Matched warm native original route `20261114T005015736467Z-c23446`, same seed/cache
and75–180s comparison window as O2 `20261114T001123867295Z-26dcac`:

| Metric | O2 | O3 |
| --- | ---: | ---: |
| Actual SDL-completion FPS |29.81975|29.97742|
| Lowest complete1s /5s FPS |26 /28.4|29 /29.8|
| Completion p50 /p95 /p99 /max ms |33.334 /34.174 /44.873 /61.387|33.331 /34.219 /35.942 /61.265|
| Main CPU p50 /p95 ms |29.314 /30.846|28.315 /29.943|
| Draw p50 /p95 ms |3.872 /4.181|3.390 /3.717|

O3 run all preparation/execution/collection statuses0, source preserved.52/52 live
observations,47 distinct positions, movement in each sampled30s block; actual
room210.47 binary loads, zero source-compile API calls,16-key prewarm42ms.
Retain O3 for longer and other-level checks, not final performance acceptance.
Different initial thermal conditions and short single route limit causal claims.

O3 gameplay-profile plus30FPS menu checks together first report1PASS/1ERROR:
`.port-cache/optimization-uniforms/current-o3-profile/`,91.321s. Both tests reused
`/evidence/launcher`, so second evidence copy hit FileExistsError; this is test
isolation failure, not a game crash or behavioral TDD RED. Menu test now owns
`/evidence/paced-menu/`; unchanged behavioral assertions pass together:
2PASS/91.181s, `current-o3-profile-isolated/`. No native/runtime change for fix.

Additional captured desktop public checkpoints: save24 room160,1PASS/145.240s,
`cross-level-24-captured/`; save26 room217,1PASS/145.212s,
`cross-level-26-captured/`, under `.port-cache/optimization-uniforms/`.
Screens show flashlight/save-mark room with unverified weapon and dark walkway/open
pit respectively; exact level names unverified. Desktop images are scene/load
evidence only. Prepared isolated native replay copies with47-program cache;
source payload hashes retained in save-bank cache47 manifest.

O3 sustained native run `20261114T005604495710Z-ead2a2` completes990s cleanly;
all host stages0, source preserved.50–975s:29.88588FPS, p50/p95/p99/max=
33.336/34.247/37.295/61.178ms, lowest complete1s24FPS at501s, lowest5s28.2FPS.
Two additional1s windows25FPS. Still below conservative owner floor despite
passing short comparison; do not declare sustained30FPS acceptance. CPU1512MHz
and GPU520MHz throughout, maximum73.750°C; no observed thermal downclocking.
461/461 live observations,382 distinct positions, changing coordinates in every
sampled30s block; full extent4216×2721game units, room210 only. Game clock
0.998004× wall time, timer59.999913ticks/s, simulation steps2/3. Ammunition unchanged;
generic route establishes movement/heat coverage, not repeated firing.

Worker SDL swap p50/p95=14.415/15.579ms; producer CPU p50/p95=
28.694/30.217ms. CPU samples end before slow501s window, so no late-PC claim.
Exact O2 early-slow-window symbol analysis saved in ignored
`.port-cache/optimization-uniforms/o2-sustained-early-cpu.json`; no new dominant
hotspot established by sparse4s sample. Next bounded hypothesis: completion is
currently signaled only after post-swap throttle, reducing available CPU overlap.
Test through actual launcher/SDL input and wait boundaries before runtime change;
retain30 cap, one-frame bound, pixels and simulation speed.

Exploration route CLI RED `exploration-route-red.txt`: missing selected plan;
GREEN `exploration-route-green.txt`:9PASS/4.658s including device CLI and local
report checks.240s declarative plan, long forward/run legs and brief action
presses, no inventory/readied weapon. Design review retains existing plan API,
valid input names and final input ending236s. Captured actual desktop check
`explore-original-captured/`:1PASS/240.227s, live room210 with health100;
substantial movement but several long wall-contact intervals and no room change.
This is scene/load evidence only, not native FPS or successful door traversal.

Hard/Normal archive save26 captured desktop check `cross-level-hard26-captured/`:
1PASS/145.203s, actual room217, positive health100. Difficulty remains archive
source claim; no native stress/performance acceptance inferred.

Native Normal/Beginner save26 `20261114T011752962069Z-2f205d`, same O3 build as
prior short/sustained tests: room217,55/55 live observations,52 distinct positions,
positive health200. All host stages0, source preserved, orderly exit.48–160s
29.40651FPS, complete1s minimum11/5s24FPS; p95/p99/max=
35.626/49.986/659.860ms. Additional1s windows20,19,23FPS retained. Program cache
restores44 binaries and builds5 missing programs (10 shader compiles,5 links);
368.277ms and659.860ms longest completion gaps. Cold new-level acceptance fails;
warm replay still required. CPU/GPU1512/520MHz throughout, maximum69.230°C.

Post-swap overlap regression setup first finds84 destructor reports from inherited
LD_PRELOAD in launcher subprocesses; filter inactive observers rather than count
as behavioral RED. Separate overall-input counter confirms real input remains
active outside test wait. Valid RED `pacing-overlap-red-confirmed`:647 real input
polls overall,72 observed post-swap throttle sleeps,0 productive sleeps; test fails
CPU-overlap ratio. External SDL delay adds40ms only during20–26s diagnostic window;
this artificial stall is not an R36S FPS measurement. Runtime change moves frame
completion signal immediately after actual SDL return, then applies unchanged
absolute-phase throttle. Submitted/completed bound and ordered GL worker unchanged;
no timestep, FP, visual, driver or clock changes. Build
`20261114T012623151186Z` reuses existing ARM64 O3 environment; GREEN pending.

GREEN `pacing-overlap-green`:3PASS/119.840s, including unchanged actual-menu30FPS
cadence/burst bounds and real-checkpoint timing/completion/input assertions.
Overlap observer sees69/70 productive sleeps,69 input polls during waits,
649 overall; prior RED0/72 and647 overall. Runtime SHA256
`7d959cad338b728a135db86e07ca2f70a7a22d803bb5d8551d9c92e045250755`.
Design review: same submitted/completed condition, same ordered three-chunk queue,
same absolute-phase deadline; synchronous renderer still paces after swap.
Worker remains sole owner of pacing state. No new setting, dependency, semantic
FP change or simulation edit. Keep minimal change; native graphics, cadence and
sustained/multi-level results still required before retaining performance claim.

Native candidate graphics run `20261114T012931687284Z-dddf31`:27/27 graphics
evidence checks pass, all host stages0. Actual Mali context/worker lifecycle,
pixels, alpha, culling and precision remain covered; diagnostic run establishes
no gameplay FPS result. Warm room217 replay uses cache collected after prior
first-visit failure, keeping new-program compilation separate from steady play.

Warm room217 candidate replay `20261114T013227135549Z-bdc72c` completes cleanly;
all host stages0, source preserved, frontend restored.48–160s29.88021FPS,
lowest complete1s25FPS (110s),5s29FPS; p50/p95/p99/max=
33.309/34.608/37.675/59.909ms.49 binary restores, no shader-compile/link calls.
56/56 live observations,47 distinct positions, substantial1864×4518unit extent,
health200 throughout. CPU/GPU1512/520MHz throughout, maximum66.153°C.
Short warm route meets25FPS window floor; cold room217 and sustained/all-level
acceptance remain separate. Original park firing route now compares same seed
and cache against prior O3 result; no matched causal claim from different rooms.

Matched original-park candidate `20261114T013812943282Z-514879`,75–180s:
29.83382FPS, complete1s minimum27/5s29, p95/p99/max=
34.342/44.359/61.453ms.47 binary restores, no source compile/link calls;
all host stages0, source preserved, clean exit and frontend active afterward.
53/53 live samples,49 distinct positions, health100, actual room210.
Handgun magazine cycles0–10 and reserve30→20 during measured interval, proving
repeated firing/reload rather than scheduled keys alone. CPU/GPU1512/520MHz,
maximum70.833°C. Prior O3 short run29.97742/minimum29 was better; keep comparison
honest and require sustained candidate result before selecting overlap change.

Frozen candidate full ARM64 launcher/runtime regression:
163tests/122.741s,59PASS/104 explicit SKIP,
`.port-cache/runtime-tests/20261114T014205026493Z`. Optional owner/device checks
remain skipped here; separate actual checkpoint, movement and native checks apply.

Candidate movement/collision/fire regression
`.port-cache/movement-tests/20261114T014420348657Z`:3PASS/481.632s.
Reference579.9953 versus delayed602.5076 game units/s, ratio1.03881454;
collision/timer guards pass, three handgun shots in each cadence run.

Public-route diagnostic `public-smg-red` correctly rejects missing ammunition
observations; `public-smg-green` then fails unchanged ammunition, so is not GREEN.
Its SMG ammunition inference was unsupported by inventory evidence. Captured
public-save Weapons screen identifies Unlimited submachine gun, which consumes
no SMG rounds. Unchanged ammunition therefore cannot establish absence of fire.
Further limited-ammunition selection attempts failed to establish equip/fire.
Unvalidated public-firearm scene and its ammunition-based test removed; no GREEN
claim from this diagnostic. Public movement coverage remains separate.
These setup failures do not override separate passing original-checkpoint handgun
cadence test. No device performance result from desktop diagnostic.

Candidate sustained native run `20261114T014412474477Z-1af1c2`: all stages0,
source preserved, ExitProcess0, frontend active.50–975s29.89885FPS; complete1s
minimum20 at50/51s,24 at297s;5s minimum25.8. Full requested interval retained.
p50/p95/p99/max33.330/34.398/37.002/66.320ms. Room210 live throughout461
observations,378 distinct positions, extent4152×2723units; each complete30s
block has substantial motion. Game clock0.998601× wall, timer60ticks/s,
health100. CPU1512/GPU520MHz for192 samples, maximum73.333°C, minimum
MemAvailable585488KiB.47 program binaries restored, no source misses. CPU
asset/startup work reaches561.490ms at48.837s; initial slow windows follow
first live observation50.203s. Late24FPS window remains separate failure.
75–180s main CPU p50/p95/max28.041/29.721/32.572ms. No sustained floor pass
or causal performance-win claim for overlap change.

Additional automated scenes and actual doorway coverage recorded in
[unattended route notes](../research_notes/Silent%20Hill%203%20optimization%20roadmap/unattended_routes.md):
warm mall29.86288FPS/minimum1s26, warm walkway29.88021/minimum25,
church29.78731/minimum25 with3 first-use programs, warm hospital29.72039/minimum21.
Corrected Q/E route opens room210→211; live65–210s29.79628/minimum27. Door-entry
236.123ms hitch and subsequent death/reset retained separately. Some native
routes report ALSA recoveries during gameplay; no new listening acceptance.

O3+bounded LTO build `20261114T024214154224Z` passes27 native graphics checks,
59 ordinary runtime checks and3 movement/collision/fire checks. Matched hospital
`20261114T025135356723Z-1c1565`,48–160s:29.68077FPS,1s minimum21 at82s,
5s27.2; p50/p95/p99/max33.386/34.776/49.955/61.510ms.51 binary restores,
zero misses/compiles,56 live room160 observations/45 positions. Full1512/520MHz,
33 samples, maximum65.384°C; no ALSA recover line. All stages0/source preserved,
ExitProcess0/frontend active. Different initial heat limits causal comparison;
neither21FPS floor nor average improves, so no LTO performance-win selection.

Timer-budget behavioral RED `.port-cache/optimization-uniforms/frame-budget-red/`
64.903s reproduces exactly20FPS in every complete second52–59. External SDL input
observer adds32ms during live checkpoint, without modifying clocks or game state.
Minimal explicit30FPS-profile candidate caps adaptive synchronization above2
refresh ticks while keeping actual elapsed simulation ticks bounded to133ms;
special/unlocked modes unchanged. Build `20261114T025924275082Z` succeeds but
`frame-budget-green` fails20<25 again; not GREEN. Original timer also insists on
waiting for a future tick after an overdue frame. Focused follow-up consumes
already elapsed ticks while retaining original absolute clock/remainder and
counter semantics; ordinary under-budget waits and special modes stay original.
Build, behavioral test and native comparison pending.

Late-tick catch-up candidate build `20261114T031604763074Z` succeeds, runtime
SHA256 `f972f0f1905d4cc1dc0a5257d0e3d8e070f55b9b6b58858875595c9a1b546e42`.
First controlled rerun fails minimum24; identical repeat passes25–27 in all
complete seconds52–59. Earlier24 retained; actual external sleep overshoot
unmeasured. Independent movement check passes607.4903 versus605.0015units/s,
ratio0.995903, against original600units/s reference. Remaining collision/fire
regressions pending.

Matched native hospital `20261114T032756715409Z-f91bb2`,same plan/save/config/cache
hashes as prior LTO run:48–160s29.981245FPS, minimum complete1s29/5s29.8,
p50/p95/p99/max33.345/34.862/36.040/48.894ms. Previously same hospital floor21.
Heavy110–111s now30 producer frames,CPU median33.270ms/max34.600ms, compared
with22 frames/CPU median32.737ms before timer change. Clock/wait improvement,
not lower simulation/driver CPU claim.51 binary restores,zero misses/compiles;
56 live room160 observations,44 positions,health199.4. Game clock1.002926×wall,
timer59.998728ticks/s.32 frequency samples1512/520MHz,maximum65.384°C.
All stages0/source preserved/ExitProcess0/frontend active. One ALSA recovery
between33.284–35.281s during loading, before live48–160s interval; no listening
pass inferred.

Heavy990s hospital soak `20261114T033440437224Z-079c2d` now passes frame target:
50–975s29.909272FPS,min complete1s28/5s29.2,p99 36.562ms/max52.629ms.
27,666 completions,461/461 alive observations,316 distinct positions in room160.
192 CPU/GPU samples all1512/520MHz,max70.416°C, game clock0.9992187×wall.
All stages0/source preserved/ExitProcess0/frontend restored. Two live-gameplay
ALSA recoveries remain explicit, around103s and559s; no listening verdict.

Movement/collision/fire suite `20261114T032945909488Z`:3PASS/480.823s.
Current native GLES `20261114T035509898075Z-1ec2cf`:27/27PASS, all stages0.
Full runtime `20261114T034435525800Z`:59PASS/109 opt-in SKIP; separately enabled
owner-data frontend suite21PASS/5.660s, including performance menu/deployment.

Observed test SDL sleep overshoots32ms request: median36.0855,max41.876333ms.
Calibrated test-only delay retains real32ms monotonic deadline and same strict
25 complete1s minimum. Preserved old binary fails20FPS in every52–59s window;
current candidate passes twice at28–29FPS, actual mean delays32.004172ms and
32.001605ms. Original24FPS stress result retained as uncalibrated workload,
not removed or marked PASS. No production spin or game clock substitution.

Explicit **Silent Hill 3 Performance** menu selects320×240/30FPS with640×480
output, existing persistent player progress and frontend lifecycle. Ordinary
play has no script/deadline; latest follow-up also selects measured shadow/flare
1/1 while preserving brightness, format and controls. Both launch and
saved deployment behaviors observed RED127missingentry then GREEN before
regression. Same installed menu now used by matching automated scene plans.
Park door/enemy-room, mall and church gameplay checks pass; door-loading pause
still under review. Same-device program-cache prime native audit passes in church
run, matching source/target SHA256; source checkpoint/cache unchanged.24 owner-data
frontend tests and9 saved-host workflow fixtures pass. Changes remain local.


## Ordered resource release, local candidate

Park door trace in native run `20261114T043515654717Z-4d320f` distinguishes
producer queue waits from driver cost: buffer deletion40.503ms/0.013ms,
texture deletion62.109ms/0.100ms. Narrow candidate copies deletion names into
existing ordered worker commands; actual deletes remain, resource owners may be
freed immediately, output/read APIs remain synchronous. No shader/effect/math or
clock change. Temporary trace removed from candidate.

Installed-launcher regression observed RED5.543s before implementation, then
GREEN5.411s with47 actual texture/5buffer releases and existing independent
pixels/frontend passing. Evidence `.port-cache/optimization-uniforms/delete-queue-red`
and `delete-queue-green`. Post-GREEN design review keeps single-context order,
copied payload ownership and bounded existing command chunks; no extra module
or pool needed for this slice.

Build `.port-cache/builds/20261114T044419879221Z`, O3/LTO, SHA256
`2ac6b9c02579ff37d20a920edde36a203458aeded0806f9e86ffecf4bc512ff9`.
Full runtime `.port-cache/runtime-tests/20261114T044911627584Z`:
174tests,60PASS/114explicitSKIP,126.579s. Native Mali graphics
`r36s-dumps/sh3/20261114T045123906063Z-4d0905`: execution/collection0,
27graphics checks pass; optional deployment-trigger rerun skipped because
`SH3_GLES_RUN` unset. Saved host invocation already completed actual deployment.

Clean park replay `20261114T045502889545Z-c7967c` reaches actual210→211.
Live65–130s before death:29.969692FPS,min complete1s29/5s29.8,
p95/p99/max34.063/35.135/79.206ms,32live observations/17positions.
Door59s bin25FPS/max194.551ms, compared with prior23FPS/214.823ms;
single replay does not isolate all scheduler/AI variation. Full48–240s retains
death/reset and9 first-visit program misses, including1.231s stall/1FPS bin.
One live ALSA recovery114.744–116.745s; no listening acceptance inferred.

Independent handgun replay `20261114T050230071532Z-0ddc92`,75–180s:
29.990378FPS,min1s29/5s29.8,p95/p99/max34.226/35.315/60.180ms.
52alive observations/47positions, actual magazine depletion/reload and reserve
30→20 establish repeated firing. Game clock1.000031×wall;47binary restores,
zero misses/writes/rejections, noALSA line. All stages0/source preserved,
ExitProcess0/frontend restored. Multi-area final-binary repeats follow in
[performance report](issue-13-performance.md). All changes remain local.

Final exact-binary hospital15-minute replay `20261114T053122812199Z-42e95c`
passes50–975s at29.894589FPS,min complete1s28/5s29.2,
p95/p99/max34.804/36.680/53.745ms.461alive observations/321positions, movement
in every sampled30s segment, game clock0.999545×wall. All191frequency samples
CPU1512/GPU520MHz,max73.333°C.51binary restores/zero misses, no logged ALSA
recovery, all lifecycle/source/firmware checks pass. Resident peak313524KiB,
latter-half rise1308KiB, minimum MemAvailable558700KiB; available swap falls168KiB.
No full-campaign memory/listening claim. Final church also proves Performance
entry selects measured1/1 from isolated0/0 preferences while preserving source;
all24 launcher settings tests pass.

Final same-executable640 comparison `20261114T055246314042Z-4068d8` uses same
room210 seed, measured settings,30FPS pacing and180s equip/fire/movement plan.
All five original320 seed inputs match byte for byte.75–180s:23.196638FPS,
minimum complete1s19/5s19.8, p50/p95/p99/max42.656/51.373/53.331/82.274ms.
41alive observations/40positions, actual magazine depletion/reload, game clock
1.000329×wall. All36CPU/GPU samples1512/520MHz, maximum75°C;47binary restores,
zero misses/writes/rejections, no logged ALSA recovery and clean lifecycle/source/
firmware checks. Temperature differs from320 maximum71.25°C; no perfectly
identical thermal conditions claimed. Same320 combat window gives29.990378FPS,
minimum1s29/5s29.8. Retain320internal/640output profile; native640 fails owner's
floor. No immutable hardware-ceiling or whole-campaign30FPS claim.
