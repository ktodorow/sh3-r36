# GPU and renderer roadmap for verified 30 FPS

Research date: 2026-11-13. Scope: current native AArch64 Linux/GLES port; no production edits, builds, device runs, publication or issue changes. Documentation research does not introduce testable behavior, so TDD does not apply here. Implementation remains subject to existing launcher → real game → frontend boundary and observed RED–GREEN–REFACTOR. Required visuals, original game speed and audio remain acceptance criteria. [Canonical spec](../../docs/specs/silent-hill-3-r36s.md), [accepted architecture](../../docs/adr/0001-native-linux-gles3-r36s.md).

## 1. What do measurements establish about Mali-G31 headroom?

### Takeaway

Current data identifies substantial avoidable renderer/driver CPU work plus resolution-sensitive presentation cost. It does **not** establish GPU saturation or impossibility of 30 FPS. Next implementation should remove repeated GL work using closely related SH2 precedents, while collecting missing texture-transfer and asynchronous GPU evidence. Resolution alone has already failed to reach target. [Current performance evidence](../../reports/issue-13-performance.md).

### Cited Findings

| Observation | Interpretation supported by evidence |
| --- | --- |
| Final 640×480: 13.5846 FPS; CPU 42.392 ms, draw 16.032 ms, Present 23.148 ms, swap 22.024 ms. Final 320×240: 17.0724 FPS; CPU 42.849 ms, draw 16.250 ms, Present 8.632 ms, swap 7.426 ms. | Internal resolution strongly affects presentation path, while measured CPU/draw intervals remain similar. CPU, draw, Present and swap are overlapping/nested observations; never add their medians. Swap measures a CPU call containing queue/display waits, not GPU execution. [Issue #13 report](../../reports/issue-13-performance.md). |
| About 370 draws and 140,124 vertex/index bytes per frame in matched room 210. Texture bytes absent from counter. | Small vertex payload does not rule out texture conversion/upload, render-target bandwidth or driver submission cost. [Issue #13 report](../../reports/issue-13-performance.md), [draw and buffer counters](../../src/d3d8/d3d8.c). |
| Warm 640 CPU leaf samples: 1,419 native, 757 Mali, 97 libc, 11 SDL, 28 other; 2,312 total. `decode_blocks` and `shader_bind_for_draw` appear in warm samples. | Mali userspace code consumes sampled **CPU** time; neither 32.7% Mali sample share nor individual sample totals equal GPU occupancy or inclusive milliseconds. Warm texture conversion deserves investigation rather than dismissal. [Issue #13 report](../../reports/issue-13-performance.md). |
| Actual context: KMSDRM, ARM Mali-G31, GLES 3.2 `v1.r13p0-01rel0.8747d14aec16ec21ac2b2da252c4ec5f`, SDL 2.32.10. `GL_EXT_disjoint_timer_query` and ASTC advertised; native DXT1/3/5 absent in operation probe. | Native timer/ASTC experiments are plausible with current provider. Advertisement alone does not pass timer correctness or ASTC texture loading; existing tested DXT path expands to RGBA8. [Final hardware log](../../r36s-dumps/sh3/20261113T175641744991Z-7b8214/device/execution.stdout.txt). |
| CPU 1,512 MHz, GPU 520 MHz and DMC 786 MHz recorded in controlled runs. | No recorded clock reduction explains existing comparison; this does not replace hot-session verification. [Issue #13 report](../../reports/issue-13-performance.md). |

**Budget arithmetic, not prediction:** mean periods derived from FPS are approximately 73.61 ms at 640 and 58.57 ms at 320. Reaching 33.33 ms requires roughly 40.28 ms / 25.24 ms less mean wall time, or 2.21× / 1.76× throughput. These figures do not allocate savings among overlapping CPU/GPU/display paths. Current CPU measurement alone exceeds target budget; CPU and graphics-driver work must improve even if GPU pixel work falls. [Measured inputs](../../reports/issue-13-performance.md).

Khronos timer extension defines asynchronous elapsed/timestamp queries, availability polling and disjoint invalidation; CPU timers do not synchronize GPU completion. On tile architectures, completion may refer to tile memory before external framebuffer writeback. Extension query-counter bits and valid timing results have not yet been recorded here. Use delayed whole-frame query ring, discard disjoint results, and compare instrumentation on/off; never insert `glFinish` or blocking per-draw query reads into benchmark. [Khronos EXT_disjoint_timer_query, revision 9](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_disjoint_timer_query.txt).

### Inferences

Ranked, falsifiable hypotheses:

1. **Driver submission redundancy remains material.** Prediction: unchanged-value uniform/program/state reuse lowers GL call count and draw CPU time in same room without changing pixels. Falsified as major opportunity if effective payloads change almost every draw or matched repeated timings show no reproducible gain. Existing sampler and vertex-enable wins establish this port can benefit from call reduction, not expected size of next gain. [Current changes/results](../../reports/issue-13-performance.md).
2. **Presentation includes excess GPU memory work.** Prediction: preserving front image without copying every frame reduces blit count and whole-frame GPU interval, especially at 640. Falsified if copy is small relative to remaining frame interval, or cannot be removed without more expensive synchronization. [Current Present](../../src/d3d8/d3d8.c:330), [front snapshot](../../src/d3d8/d3d8_res.c:478).
3. **Warm texture conversions are avoidable reuploads, resource churn, or actual streaming.** Prediction: per-resource identity/format/mip/dirty-reason/lock-flag counters distinguish these; repeated identical payloads or read-only unlocks would support caching/dirty fixes. Falsified if uploads represent genuinely changed texture bytes and account for little CPU/GPU time. Current warm `decode_blocks` samples establish activity, not cause. [Resource path](../../src/d3d8/d3d8_res.c:319), [samples](../../reports/issue-13-performance.md).
4. **Monster room adds shader/overdraw/geometry or game CPU cost.** Prediction: mapped monster scene has identifiable rise in GPU query interval, draw/fragment workload, transfers, or guest CPU. Current fixed room cannot locate owner's heavy scene. No inference that monster lag is exclusively GPU-bound. [Owner feedback and benchmark limits](../../reports/issue-13-performance.md).

### Gaps

Missing: valid GPU query interval; instrumentation-disabled cost; texture bytes/decode/palette counts; per-program draw/time distribution; readback/lock/copy counts; target dimensions and revisit sequence; heavy monster-room ID/save/camera. Existing 23 GLES operation oracles pass for final binary, but none establishes 30 FPS. Current benchmark seed `shadow=1`, `lensflare_ztest=1` is **not** yet mapped to lowest graphics; slower alternate numeric values do not establish intended quality order. [Current evidence and limits](../../reports/issue-13-performance.md).

## 2. Which exact renderer changes should land first?

### Takeaway

**Adapt small pieces from current SH2 renderer instead of redesigning or replacing GPU stack.** Upstream SH2 already contains program/uniform generations, GL state/binding cache, attachment reuse and UP stream ring. SH3 retains older structure plus newer essential GLES fixes. Narrow adaptation offers concrete starting code while preserving local semantics; another engine's performance claim supplies no R36S acceptance. [SH2 cache change](https://github.com/cutarev/sh2-nx/commit/9edc6c39a318a0b4bc0b6542893b4b7aae521290), [SH2 pinned source](https://github.com/cutarev/sh2-nx/tree/7e69609f3a063fbe24c41d6aa560f14ede578746), [SH3 current renderer](../../src/d3d8/d3d8.c).

### Cited Findings

Reference identities checked through read-only GitHub API/raw source, 2026-11-13:

| Reference | Exact revision / relevant files | Applicability |
| --- | --- | --- |
| SH3 upstream v0.06 | `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`; `src/d3d8/d3d8.c`, `d3d8_shader.c`, `d3d8_res.c`. | Same upstream baseline as project feasibility; no newer upstream SH3 GPU optimization to merge wholesale. [Repository](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98). |
| SH2 upstream v1.03 | `7e69609f3a063fbe24c41d6aa560f14ede578746`; cache introduction `9edc6c39a318a0b4bc0b6542893b4b7aae521290`. | Closest D3D8/SDL/OpenGL lineage. Its desktop/Switch graphics, EE timing and render-scale assumptions differ. [Cache commit](https://github.com/cutarev/sh2-nx/commit/9edc6c39a318a0b4bc0b6542893b4b7aae521290). |
| Cuphead reference | `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`; `pm/cuphead/Cuphead.sh`, Unity/Mono configuration. | Launcher/runtime pattern, not transplantable renderer. Current commit concerns texture quality choice. [Pinned repository](https://github.com/wild1walker/portmaster-cuphead/tree/1b7e7b019dabeb4226a1b4be5bfdd854895242f5). |
| Owner Delver native GLES work | Historical source/evidence locators and pinned tracked ancestor `9083f5e9c23b63fdc67ae2ce4cbeb374692d10be` recorded in existing notes; uncommitted R36S work means this HEAD alone does not identify tested port. | Same owner GPU proves native GLES route useful; Java/libGDX scene and Weston/Crusty route differ. Roughly 30 FPS used 512×384 world / 640×480 UI, not SH3 proof. [Full applicability notes](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md). |

Current SH3 binder uses `glUseProgram` each draw; repeatedly uploads active VS/PS constants, matrices, materials/lights, fog/alpha/scalars; does three repeated uniform-name lookups in lighting path. Matrix products and normal inverse recomputed; normal matrix calculated even if its uniform is inactive. State application repeatedly emits viewport/depth/blend/cull/stencil/mask changes. Texture binding iterates all eight stages; attribute pointers and stream buffer binds still emitted after previous enable-mask optimization. [Shader binder](../../src/d3d8/d3d8_shader.c:758), [state and draw setup](../../src/d3d8/d3d8.c:663).

SH2's `Prog` retains fresh/value/generation state per program; shader construction also uses central program binder, avoiding hidden warmup mutation. Companion `gls_*` cache tracks active texture unit, separate 2D/cube bindings, array/element buffers, read/draw FBOs, enable/write state and program. Device setup resets cache; resource deletion invalidates texture/buffer/attachment state. Constants, transforms, material/light setters and defaults update generations. Attachment reuse compares texture names, face target and mip levels before skipping GL attachment/validation. [SH2 shader source](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/src/d3d8/d3d8_shader.c#L732), [companion cache](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/src/d3d8/d3d8.c#L12), [attachment cache](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/src/d3d8/d3d8_res.c#L320).

**Wholesale cherry-pick would regress SH3:** inspected SH2 P8 upload forces alpha opaque and lacks current SH3 palette-generation path; SH2 still calls desktop clip control/depth clamp. Current SH3 additionally implements GLES packed-color conversion, DXT fallback, RHW fragment depth recovery and spare-depth sizing. Retain each local fix. SH2 UP-ring change also modifies buffer lifetime/mapping behavior; it belongs in separate measured slice. [SH2 resources](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/src/d3d8/d3d8_res.c#L284), [SH2 device](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/src/d3d8/d3d8.c#L305), [SH3 resources](../../src/d3d8/d3d8_res.c), [SH3 shaders](../../src/d3d8/d3d8_shader.c).

### Inferences

Implementation-sized slices, in preferred order. Savings are hypotheses; no invented FPS or milliseconds assigned.

| Slice | Minimal change / counterfactual | Measure; keep/revert rule |
| --- | --- | --- |
| R0: missing workload evidence | Count texture allocated/uploaded bytes by format/mip, decoded pixels, palette expansions, dirty cause/lock flags, readback bytes/time, CopyRects/front blits, target switches/dimensions, program switches and uniform calls/bytes. Aggregate; no per-draw printing. | Compare instrumentation on/off on same binary/profile. Keep bounded diagnostics only if overhead known; counters explain choice, not optimization win. |
| R1: uniform locations | Add `power/ltspec/ltamb` locations at link, matching SH2; remove three draw-loop lookups. No payload or shader change. | Oracle pixels unchanged; count lookups and repeated wall timings. Low-risk first patch, expected small gain; do not market as 30 FPS solution. |
| R2: scalar uniform values | Per-program fresh flag plus viewport/fog/texture factor/alpha reference last effective values. First draw always uploads. | Observe fewer uniforms with unchanged scene images through program A→B→A, menus/doors, reset and warm-cache startup. Revert if first-use/return-to-program state stale. |
| R3: constant/matrix/light values | Cache effective uniform payload per program first; calculate products only when inputs changed and only if active program needs them. Preserve declaration constants merged over device constants. Later replace comparisons with generations after all writers audited. | Count uploads and matrix/light rebuilds, draw CPU time, native/Mali sample shifts. Test switched VS declarations, constant ranges, transformed lights, state-block restoration and defaults/reset. Revert any visual mismatch or no useful gain against complexity. |
| R4: program/state/binding ownership | Central cache wrappers or explicit invalidation at **all** writers; adapt SH2 pattern for GLES-safe states. Start program binder (including link/warmup), then viewport/write/enables, then textures/buffers. Keep current sampler invalidation and device VAO rules. | Same actual GL oracle suite plus game scenes; count each family. Revert stale state after Clear/Present/copy/readback or negligible repeated timing improvement. |
| R5: framebuffer attachment reuse | Reuse actual attachment tuple; preferably separate Present read FBO so Present cannot secretly replace game color attachment. Include effective spare-depth texture and mip/face. | Fewer attachments/status checks; target-to-target scene/fades/save preview unchanged. Check depth-size mismatch and output/internal resolution reset. No arbitrary removal of validation before attachment correctness is proved. |
| R6: redundant upload prevention | Only if R0 shows repeated unchanged/read-only data: retain lock flags, honor valid read-only/no-dirty semantics, update actual dirty rectangles and block-aligned subregions; preserve palette identity/version. Reusable scratch reduces allocation churn but not decode work. | Byte hashes in diagnostic mode distinguish writes from read-only access. Must retain DXT1 transparent mode, DXT2/4 premultiplied bytes, mips, P8 alpha and palette animation. Keep only if warm uploads/decode/time or tails improve without memory growth. |
| R7: UP streaming ring | Adapt SH2 mapped ring only if per-draw allocation/upload CPU cost remains material. Distinct vertex/index rings; no overwrite of in-flight bytes; orphan on wrap, tested fallback if map fails. | Measure allocations, mapped/subdata calls, upload waits, tail latency and RSS. Revert stalls/corruption; 140 KB/frame alone does not justify complex streaming scheme. |

Required ownership rules for R2–R5:

- **Uniform cache belongs to linked program, not global last draw.** Fresh on new/link/relink/context; bytewise effective-value comparison handles signed zero/NaN conservatively. Program A→B→A retains distinct values. Changing program does not itself invalidate its retained uniforms. Declaration overrides (`v->const_set`) must happen before comparison; generation-only scheme must account for VS changes and that merge, not only `SetVertexShaderConstant`. [Existing merge](../../src/d3d8/d3d8_shader.c:819).
- **GL-state cache tracks actual GL, not requested D3D state.** Clear changes color/depth/stencil masks and scissor; Present changes read/draw FBO, scissor, clear state; resource upload/creation/spare depth alter texture bindings; copies/readbacks alter FBOs. Each mutation must update common cache or mark affected slots unknown. Texture cache key includes unit+target, deletion/name reuse; element-buffer/attribute cache scoped to VAO. [Clear](../../src/d3d8/d3d8.c:440), [Present](../../src/d3d8/d3d8.c:330), [resource operations](../../src/d3d8/d3d8_res.c:280).
- **Generation coverage must be complete:** SetTransform, MultiplyTransform, constant setters, material/light setters and light enable, ambient render state, state-block Apply/default/reset, shader recreation, context/VAO creation and any diagnostic writes. Direct state copies cannot bypass increment. First adaptation should favor payload equality over premature dirty bookkeeping. [Current device methods](../../src/d3d8/d3d8.c), [SH2 generations](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/src/d3d8/d3d8.h#L86).
- **Attachment cache tracks actual object identity and storage epoch.** Include color target/face/mip, depth texture/mip and SH3 spare-depth replacement. Preserve D3D SetRenderTarget viewport reset even when attachments match. FBO/texture deletion, resize and helper reattachment invalidate relevant entries; diagnostic captures cannot leave cache lying. [Current target setup](../../src/d3d8/d3d8_res.c:391), [SetRenderTarget](../../src/d3d8/d3d8.c:416).

### Gaps

Cache transfer has not been implemented or benchmarked. SH2 predecessor was inspected as public source, not executed; claimed 60 FPS in its commit title cannot establish SH3/Mali outcome. Need behavioral tests against independent pixels and real game transitions, not tests counting private helpers. Existing final 23 hardware GLES oracles should all remain green; mocked GL call reduction is supporting evidence only. [Final oracle evidence](../../reports/issue-13-performance.md).

## 3. Which larger GPU changes are credible after cheap fixes?

### Takeaway

Prefer removing copies, preserving resident data and reducing demonstrated shader/bandwidth work. GPU already runs translated vertex/fixed-function shaders; moving arbitrary gameplay logic to GPU is a different, high-risk architecture project. Keep 320 internal fallback available with 640 output/readable UI, while measuring whether GPU work rather than CPU limits next stage. [Shader generation](../../src/d3d8/d3d8_shader.c:522), [profile requirements](../../docs/specs/silent-hill-3-r36s.md).

### Cited Findings

Every Present currently scales/flips backbuffer to default framebuffer, then copies same backbuffer into persistent front snapshot. Last-presented image is required by transition cross-fades and save images. Readback synchronously fetches pixels to guest memory; locking render target reads back; unlocking can upload entire image. Dirty DXT levels decode to newly allocated RGBA scratch on upload; paletted textures expand all affected levels when active palette identity/version changes. These operations are distinct from diagnostic screenshot readbacks, which were disabled in controlled run. [Present](../../src/d3d8/d3d8.c:330), [front image/readback/copies/locks](../../src/d3d8/d3d8_res.c:424), [texture conversion](../../src/d3d8/d3d8_res.c:319).

Arm recommends contiguous rendering to each FBO, full clears where previous contents are dead, and invalidating only transient attachments **before** pass completion/unbind. Repeated partial rendering can force tile writeback/reload. These are architectural reasons to measure target switches, not permission to reorder guest effects or discard contents later read by game. [Arm framebuffer guidance](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-2-how-to-correctly-handle-framebuffers).

Current official PortMaster FNA guidance describes a Mali handheld port recovering performance by sizing oversized render targets to actual used dimensions, removing redundant fullscreen target copy and correcting immediate drawing that prevented batching. Same guide discusses unsupported DXT expansion and custom ASTC conversion. FNA/FNA3D and Mono differ from SH3's D3D8 bridge; these are hypotheses to test, not transferable measured gains. [PortMaster FNA guide](https://portmaster.games/contribute/porting/engines/fna/).

Samsung GLES guidance recommends immutable texture storage, load-time upload, explicit multi-buffering/batched updates to avoid driver synchronization and avoiding render-loop allocation. Driver optimizations depend on immutable format/storage and transfer timing. Current SH3 creates mip storage with `glTexImage2D`, then lazily uploads when first sampled. [Samsung GLES recommendations](https://developer.samsung.com/galaxy-gamedev/resources/articles/opengl.html), [current storage](../../src/d3d8/d3d8_res.c:281).

Arm's Mali-G31 counter guide identifies external read/write stalls, fragment/non-fragment utilization, texture/ALU/varying workload and early/late depth metrics. It recommends avoiding unnecessary fragment-depth writes and reducing overdraw. Current GLES generator defaults every float/int/sampler to highp, emits alpha discard where required, and writes `gl_FragDepth` for RHW to retain required depth-clamp behavior. [Mali-G31 guide 102652_0104, sections 3–5](https://documentation-service.arm.com/static/64d496a94a92140bb31d7b96?token=), [shader assembly](../../src/d3d8/d3d8_shader.c:522).

Primary first-hand same-platform search found LVGL author/user discussion of Cortex-A35/Mali-G31 software/GLES split: work only accelerates when drawing actually moves to GPU; reported comparison benchmark was on Raspberry Pi, not G31. No exact SH3/current dArkOS driver performance fix was found. Queries included `"Mali-G31" "OpenGL" "slow" "draw"`, `"sh3-nx" "fps" performance`, and Mali uniform/API overhead. Android R36H reports and emulator advice were excluded as different drivers/engines. [Full LVGL discussion](https://forum.lvgl.io/t/what-is-the-performance-of-lvgl-v9-3-opengl-es-rendering/21917).

### Inferences

| Later experiment | Why applicable / keep conditions | Limits and visual oracle |
| --- | --- | --- |
| Remove front snapshot copy through retained/ping-pong backing | Current exact duplicate full-image blit gives concrete candidate. Rotate physical backbuffer storage so last presented image stays available, while new frame targets separate storage. Keep only if GPU/wall timing improves. | Cannot delete snapshot or lazily read current backbuffer after clear. Need aliases/locks/CopyRects/GetFrontBuffer, fades, save capture, resolution changes and resource lifetime proven. Default window still needs scale/flip blit. |
| Cache FBOs per attachment tuple; invalidate dead depth/stencil | Fewer attachments/status queries plus clearer render-pass lifetime may reduce driver and tile traffic. Start no-op attachment reuse before pass restructuring. | Never invalidate depth/stencil used by later guest pass, lock or copy. Preserve color for textures/front image. Need actual ordered pass trace and dependency lifetime, not just FBO-bind count. |
| Right-size oversized targets / separate world resolution from UI | R0 can reveal fixed 512² or larger passes that do not shrink at 320. SH2 render scale and PortMaster FNA are comparable patterns. Keep if working region/coordinates map correctly and GPU interval falls. | SH3 spare-depth workaround documents real 512² scene target against 640×480 auto-depth; blindly clipping target caused black rows. Reflections, lens flare, postprocessing, UV scales and fullscreen effects require exact mapping. |
| Immutable texture storage; preupload at safe load boundary | GLES3 supports storage approach; current immutable dimensions/levels lend themselves to `glTexStorage2D` followed by subimage. Could reduce first-sample stalls. | Format/compressed/cube/depth and later mip changes must remain legal. Warm steady-state may gain little; evaluate cold and warm separately. Preserve current BGRA conversion and palette updates. |
| Reuse conversion scratch / exact decoded-texture cache | If R0 shows repeated same source across resource churn, hash+format+mip+dimensions cache could avoid repeat DXT conversion. If texture stays dirty despite unchanged bytes, first fix dirty cause. | Bound memory/LRU and original-source lifetime; content hashing has CPU cost. Current code already keeps clean GL image, so adding another cache does not help truly immutable textures unless re-created/re-dirtied. |
| ASTC/ETC2 cache for immutable textures | Actual ASTC support means compressed resident format might reduce texture bandwidth/RAM. Offline sidecar derived from exact owner data avoids runtime transcoding cost. | Additional lossy conversion/asset processing is not preapproved. Need quality/alpha, mips, premultiplied DXT2/4, source hashes, bounded cache, visual acceptance. Do not install custom FNA/driver or claim ASTC operation passed from advertisement. |
| Shader precision/variant audit | Dump actual hot shaders, evaluate Mali Offline Compiler support for G31, compare shader arithmetic/texture/varying estimates, then reduce precision only for proven bounded color/intermediate data. Specialize away RHW fragment-depth output only where depth behavior provably irrelevant. | Keep position/clip/depth/large or projective UV math highp initially. Do not remove alpha discard, fog or flashlight. Required RHW depth recovery remains for depth-tested geometry. Static compiler estimates need actual firmware benchmark and pixels. |
| Order-preserving batching / constant UBO | If R2–R4 leave many compatible adjacent draws or changing uniform blocks, combine without changing effect ordering; GLES3 UBO could reduce calls. | Uniform caches are smaller first step. Alignment/buffer lifetime/new binds may offset UBO benefit. Transparent draws, stencil passes and readbacks prevent arbitrary sorting. No generic instancing without game-level identical geometry evidence. |
| GPU-assisted texture conversion | One-time P8/DXT conversion into retained RGBA texture could replace demonstrated CPU loop, keeping subsequent consumers on GPU. Need byte-exact shader/compute oracle and transfer/barrier accounting. | Palette-index sampling with ordinary bilinear filtering is wrong: color interpolation belongs after palette lookup; mip behavior and alpha matter. Per-fragment DXT decode repeats work on every sample. CPU game reads force synchronization; no benefit assumed. |
| GPU skinning/culling/gameplay offload | Existing fixed-function and translated VS paths already execute skin/vertex math on GPU; first confirm any guest CPU skinning actually dominates via samples. A later GPU-only render-data producer could help if large parallel workload stays resident. | No justification yet for moving AI/collision/x87 guest execution to GPU. Dependence on immediate CPU results, float semantics and readbacks can cost more than CPU loop. GLES3.2 advertisement alone is not safe offload design. |
| Optional shadow profile | Map original menu/config numeric meaning, then measure setting in owner monster room and matched scenes. Retain fog/flashlight/alpha and essential effects. | Current `shadow=0/1` order unverified; `lensflare_ztest` may be correctness control, not quality. Do not label either disabled/lowest from name or one timing run. |

All experiments retain current firmware/libmali/KMSDRM route. Port-local renderer optimization does not require overclock, global library/driver replacement, kernel changes, Switch binaries, or copied Java/Unity/Mono dependencies. [Scope limits](../../docs/specs/silent-hill-3-r36s.md), [working-port differences](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md).

### Gaps

No proposed larger experiment has executed. GPU counters may require unavailable kernel/profiler integration; extension timers are lower-dependency starting point. Arm Offline Compiler landing page redirects and current tutorial yielded unreadable body during fetch; target support/version and host availability remain unchecked. Khronos XHTML reference pages failed content-type extraction; no uncited timing/ownership shortcut inferred from those failures. PortMaster FNA full body was returned by search retrieval but direct open failed once; cited findings limited to fetched material. No new reference clone or downloaded executable/script was created or run.

CCE searches for current shader/resource source returned stale `.port-cache/sh3-source-*` fragments or sampling logs; expansion/index limitations previously recorded. Exact current `src/d3d8/*` paths were then read directly, and upstream references fetched at pinned revisions without cloning. Do not use stale cache source as implementation base. Research retains source URLs, exact revisions, current code paths and evidence above; local implementation remains uncommitted for review. [Context limitations](../../reports/issue-13-performance.md).


## 2026-11-13 worker serialization follow-up

Current official [PortMaster FNA performance guide](https://portmaster.games/contribute/porting/engines/fna/#performance-on-a-handheld-gpu)
was fetched successfully at its new URL. It supports checking target-switch and
ordered-submission costs separately from pixel count; its FNA/Mono fixes are not
SH3 implementations. Searches `site:github.com PortMaster Mali glGetUniformLocation performance`
and `site:github.com PortMaster rendering thread glSamplerParameterfv` found no
first-hand SH3 fix. Relevant first-hand comparable source:
[portmaster-unity glrec.c](https://github.com/wild1walker/portmaster-unity/blob/92e4c37c773e646f5e7774fd669a6397e6e03836/runtime/host/glrec.c),
commit `92e4c37c773e646f5e7774fd669a6397e6e03836`, opening comments describe an
RK3326 Mali worker path and a per-entry-point census to identify commands that
force immediate submission. Its Unity/Android loader, ABI and driver-selection
logic differ from this native AArch64/KMSDRM port. Adapt diagnostic method only;
no external script or code executed, no clone created.

[Khronos uniform-location contract](https://raw.githubusercontent.com/KhronosGroup/OpenGL-Refpages/main/es3.0/glGetUniformLocation.xml)
confirms locations remain valid until relink, including cached inactive `-1`.
[SDL swap contract](https://wiki.libsdl.org/SDL2/SDL_GL_SwapWindow) supplies actual
window-update boundary. Local separate completion CSV passes independent real
SDL forwarding observer with20ms delay. Native queued candidate still measures
18.18/13.75FPS producer cadence at320/640; correctness and lower main CPU time
alone do not establish overlap or30FPS. Next local measurement: optional per-API
synchronous-queue census, then remove proven hot barriers while retaining ordering
and owned input payloads. External content reviewed as untrusted research; no
prompt-injection instructions observed. Documentation-only update needs no TDD.


Texture-wait follow-up searches: `site:github.com PortMaster Mali texture upload render thread copy pixels synchronization`
and `site:portmaster.games texture uploads performance Mali`. No exact SH3 fix;
current official FNA guide and pinned Unity recorder above support per-call census
and owned copied pixel payloads. Native census measured2077 subimage waits across
whole100s run,6.325s including prior queued work. Use local GL formats/pitches,
not Unity's ABI/code. [Khronos pixel-store rules](https://raw.githubusercontent.com/KhronosGroup/OpenGL-Refpages/main/es3/glPixelStorei.xml)
and [subimage input contract](https://raw.githubusercontent.com/KhronosGroup/OpenGL-Refpages/main/es3/glTexSubImage2D.xml)
require copying through last source pixel with row length/alignment/skips retained;
PBO inputs are offsets and require separate treatment. Proposed conservative
fallback leaves unknown formats/PBO offsets synchronous. No source execution or
new reference clone. Actual native sampler candidate passes27 pixel/lifecycle
checks, run `20261113T220811668193Z-dc999c`; throughput retest pending.

Nonblocking GPU timing follow-up: repeated official PortMaster FNA URL fetch
failed this time; prior successful full read remains above. Searches
`site:portmaster.games "GPU" "performance" "timer"` and
`site:github.com PortMaster "GL_EXT_disjoint_timer_query"` found no exact
PortMaster timer implementation. Khronos revision9 linked above requires counter
bits,64-bit results, availability checks and disjoint rejection. Use bounded
delayed query ring; no blocking result reads or glFinish. Timing spans submitted
frame commands, including gaps; not GPU occupancy. Instrumentation overhead still
needs comparison. [Magnum's first-hand driver workaround](https://raw.githubusercontent.com/mosra/magnum/master/src/Magnum/GL/Implementation/driverSpecific.cpp)
reports Android-shell Mali timer OOM; Android/ADB differs from Linux KMSDRM here,
so capability advertisement alone is insufficient. No downloaded code executed.


### Native timer ambiguity, 2026-11-13

Actual r13p0/KMSDRM640 run `20261113T223112187035Z-7965b3` returns64-bit query
results and one disjoint rejection, but warm raw elapsed mean0.889ms does not
explain36.739ms median SDL swap/48.437ms completion cadence. Treat these as raw
provider results, not whole-frame GPU attribution. Query-enabled20.60076FPS is
lower than prior query-disabled21.75640FPS; cadence acceptance disables queries.
Ordinary frame profiler now requires separate explicit GPU opt-in. Real-checkpoint
RED `gpu-opt-in-game-red` reproduced unwanted enable/report; build
`20261113T230334757532Z`, GREEN `gpu-opt-in-game-green` and full runtime suite
`20261113T231041202708Z` pass (54PASS/94explicitSKIP). Handheld profile already
disabled queries explicitly; this guard changes frame-only diagnostic default.

Repeated searches `site:portmaster.games KMSDRM performance GPU timer`,
`Mali GL_EXT_disjoint_timer_query tile based elapsed time query swap buffers`,
`site:github.com Mali GL_TIME_ELAPSED wrong timer query results`. Official
PortMaster FNA URL still fails direct open; earlier successful fetched text
remains basis for general porting advice. First-hand comparable
[Unity runtime timer notes](https://github.com/wild1walker/portmaster-unity/blob/92e4c37c773e646f5e7774fd669a6397e6e03836/docs/runtime.md#L220)
report implausible G31/r20p0 elapsed results despite exposed extension. Same GPU
family, but H700/fbdev/armhf differs from RK3326/r13p0/KMSDRM/nativeAArch64;
not proof of same driver defect. No forced-finish measurement adopted.

[ANGLE commit2afb94dda864711e9684851afb4a183ca59de99d](https://chromium.googlesource.com/angle/angle/+/2afb94dda864711e9684851afb4a183ca59de99d%5E!/)
records native Android timestamp undercounts and Mali-G78 ordering workarounds.
Different GPU, platform and timestamp query kind; evidence for caution, not
permission to add flush/fence/finish to production. [Arm first-hand thread](https://community.arm.com/forums/f/mobile-graphics-and-gaming-forum/6869/gl_ext_disjoint_timer_query-for-performance/27814)
likewise reports tiny timer results on Mali-T760, another different architecture.
No exact SH3/R36S fix found. Source content treated as research only; no injected
instructions observed, no downloaded code executed or reference clones created.

### Unused screen-space depth output candidate, 2026-11-13

Read-only source review while handheld run is active: current GLES program
assembly writes `gl_FragDepth` for every fixed-function RHW draw, regardless of
depth-test state (`src/d3d8/d3d8_shader.c`, `build` and
`shader_bind_for_draw`). Depth-disabled UI/postprocess draws could use a variant
without this output. Keep vertex clip-Z adjustment: disabling depth testing does
not disable clipping. Keep current interpolated/clamped depth for depth-tested
draws, including existing varying-reciprocal-W pixel oracle. No patch or gain
measured; amount of actual game work affected remains unknown.

[Arm Offline Compiler guide, issue8.7.00, section2.7.3](https://documentation-service.arm.com/static/67e15e8c1b5aaa6a3abc2299?token=)
identifies fragment-depth writes as a cause of late depth/stencil tests and lost
hidden-surface removal. This supports checking generated variants, not a promise
that removing output from depth-disabled draws improves this driver. Early depth
testing itself is unavailable when depth testing is disabled. Do not remove
required depth writes, shader discard, fog, lighting or transparency.

Repeated searches: `site:portmaster.games contribute performance depth shader`,
`site:github.com/cutarev/sh2-nx gl_FragDepth`, and
`site.developer.arm.com gl_FragDepth early z Mali performance`. No exact
PortMaster/SH2 fix found. Official PortMaster FNA URL again failed direct fetch;
prior full text remains recorded above. Arm guide is generic Mali guidance,
not R36S acceptance. Compiler landing page returned redirect only; no tool
installed or executed. Any implementation requires real GLES compile/pixel
RED/GREEN, cache-format review and matched native frame timings.
