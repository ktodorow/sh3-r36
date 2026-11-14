# R36S measurement, pacing, and 30 FPS profile verification

## What must improve, and how trustworthy are current measurements?

### Takeaway

Current renderer changes produce a measured improvement, but neither resolution passes 30 FPS. Start the next implementation with the bounded SH2 uniform-cache adaptation, while using existing counters to screen instrumentation overhead. Additional profiling infrastructure should answer a specific unresolved question, rather than delay that optimization.

This note is research only. No device runs, executable builds, production changes, publication, or issue changes were performed for it. TDD does not apply to this documentation artifact; proposed executable changes below require the repository's RED–GREEN–REFACTOR process at the already agreed launcher → real game → frontend boundary. Scope and acceptance come from the [canonical spec](../../docs/specs/silent-hill-3-r36s.md), [issue-13 evidence](../../reports/issue-13-performance.md), and [issue-09 evidence](../../reports/issue-09-audio-timing.md).

### Cited Findings

The final measured build is `.port-cache/builds/20261113T174635538228Z`, binary SHA-256 `4120ea8e35da17de1be0acbfa5453e59cb4d6a6aa833d53f7d6e8ff2de9903d0`. Both results below use fixed room 210, the 55–95 second window, no screenshots, 640×480 output, and configuration values `shadow=1`, `lensflare_ztest=1`, `A8R8G8B8`, gamma 1. These values have not yet been certified as the complete lowest supported graphics profile. Sources: [640 evidence](../../r36s-dumps/sh3/20261113T174837069025Z-36b849/frame-summary.json), [320 evidence](../../r36s-dumps/sh3/20261113T175211968006Z-bdd0f6/frame-summary.json), [current scene plans](../../scripts/scenes.json), [report](../../reports/issue-13-performance.md).

| Matched diagnostic | 640×480 internal | 320×240 internal |
|---|---:|---:|
| Frames in analysis window | 543 | 683 |
| Mean FPS, `1000 / mean frame ms` | 13.5846 | 17.0724 |
| Mean frame ms | 73.6130 | 58.5742 |
| Frame p50 / p95 / p99 / max, ms | 73.150 / 78.396 / 80.426 / 84.684 | 58.434 / 60.546 / 63.305 / 121.493 |
| Presenting-thread CPU p50, ms | 42.392 | 42.849 |
| Draw bracket elapsed p50, ms | 16.032 | 16.250 |
| Present bracket elapsed p50, ms | 23.148 | 8.632 |
| Swap bracket elapsed p50, ms | 22.024 | 7.426 |
| Draw calls p50 | 368 | 371 |

At a nominal 30 FPS, frame budget is `1000 / 30 = 33.333… ms`. Relative to these **instrumented static-scene means**, 640 must remove 40.280 ms/frame, or 54.72% of current frame cost, requiring 2.208× throughput. The 320 profile must remove 25.241 ms/frame, or 43.09%, requiring 1.757× throughput. These are arithmetic targets, not predicted gains or extrapolated hardware limits. Input data: [640 summary](../../r36s-dumps/sh3/20261113T174837069025Z-36b849/frame-summary.json), [320 summary](../../r36s-dumps/sh3/20261113T175211968006Z-bdd0f6/frame-summary.json).

The instrumentation records overlapping quantities. Thread CPU includes game, renderer/driver, and profiler execution; draw elapsed includes host work and possible waits; swap is inside Present. Frame boundaries occur before later per-frame diagnostics, so some work appears in the following interval. **Do not add these medians or subtract them as disjoint costs.** No current column is direct GPU execution time. Source: [profile.c](../../src/d3d8/profile.c), [Present implementation](../../src/d3d8/d3d8.c), [profiling report](../../reports/issue-13-performance.md).

The corrected 640 baseline, after removing expensive automated input decoding, was 11.7189 FPS. Final 13.5846 is a valid approximately 15.9% renderer improvement under that comparison. Earlier approximately 9.48/11.73 FPS results included about 19 ms/frame of scripted input overhead; they cannot establish renderer-only gains. No equivalent corrected pre-renderer 320 baseline exists. Source: [issue-13 baseline and experiment table](../../reports/issue-13-performance.md).

Current `SH3_PROFILE` invokes about two performance-counter reads per draw, approximately 740 per frame at 370 draws, plus per-frame clock/CSV work and a 10 ms presenting-thread CPU sampler. CSV buffering limits write frequency, but cost of the complete profiler has not been isolated. `SH3_PROFILE` currently starts both detailed counters and the CPU sampler. `SH3_STATS`, sparse PEEK, and five-second host/device monitoring add separate diagnostics. Counter-call count alone does not quantify milliseconds of overhead. Sources: [profile.c](../../src/d3d8/profile.c), [profile_cpu.c](../../src/d3d8/profile_cpu.c), [scene settings](../../scripts/scenes.json), [workflow](../../scripts/README.md).

CPU samples identify where the presenting thread executes, not inclusive call costs or GPU work. Warm 640 window contains 2,312 observations: native code 1,419, Mali library 757, libc 97, SDL 11, other 28. `recomp_fp_round24` accounts for 219 leaf samples, about 9.5% of those observations. Dropped samples were approximately 0.7–1.2% of requested samples; stored PC and x30 return addresses are not an unwound call stack. Sources: [CPU evidence and limitations](../../reports/issue-13-performance.md), [sampler](../../src/d3d8/profile_cpu.c).

CPU/GPU/DMC observations remained 1512/520/786 MHz in these runs; hot temperatures reached approximately 71–73°C and measured resident memory remained far below device capacity. Sequential profiles did not start at identical temperatures. These results do not demonstrate thermal throttling or RAM exhaustion in this scene, and do not certify full-campaign memory behavior. Sources: [issue-13 telemetry](../../reports/issue-13-performance.md), [feasibility assessment](../../reports/Silent%20Hill%203%20R36S%20feasibility.md).

### Inferences

- Reducing resolution substantially reduced Present/swap elapsed while current main-thread CPU remained similar. Investigate both CPU/driver work and GPU/display waits; resolution scaling alone has not removed the current gap. This observation does not assign the resolution-dependent time to GPU execution.
- Current approximately 43 ms CPU median is a real signal to improve, not an immutable ceiling. The timing repair allows elapsed simulation steps to track real time; measured work can change with the elapsed step as FPS improves. At current rates, step counts can be approximately four at 320 and six at 640, while 30 FPS ordinarily corresponds to two 60 Hz ticks. Record step distribution alongside costs to test positive feedback rather than extrapolate fixed CPU cost. Sources: [timing repair](../../src/game/sh3.c), [timing evidence](../../reports/issue-09-audio-timing.md).
- The 512 MB desktop RAM requirement cannot answer the FPS question. Measured per-frame work, hardware/driver throughput, pacing, memory bandwidth, and the selected native translation determine whether this implementation reaches its budget. Current scene memory evidence does not identify memory capacity as the limiting resource.

### Gaps

- No matched profiling-disabled distribution or native GPU timer result exists. Current cost attribution is incomplete.
- Fixed room 210 is not established as the owner's mall monster scene. Existing owner runs visited mall rooms 11–17 and additional rooms at 320; paths and camera/monster states were not matched for performance comparison. Source: [handheld feedback and room history](../../reports/issue-09-audio-timing.md).
- CCE recall/search was used first. Some current-file queries returned compressed first lines or unrelated/stale chunks; known current paths were then reviewed directly. No game data was indexed for this note.

## Which bounded experiments separate work, waits, and measurement cost?

### Takeaway

Use the cheapest existing comparison first: same final binary, checkpoint, route, settings, thermal range, automated input, PEEK, and stats, with `SH3_PROFILE` enabled versus unset. Frame-count slope and existing aggregate FPS can screen a large observer cost. Delayed native GPU queries and a minimal external observer are later tools when the unresolved question requires them.

### Cited Findings

The current driver advertises `GL_EXT_disjoint_timer_query`: actual KMSDRM context identifies ARM Mali-G31, OpenGL ES 3.2 `v1.r13p0-01rel0.8747d14aec16ec21ac2b2da252c4ec5f`, SDL 2.32.10. Advertisement alone does not prove counter precision, usable entry points, or valid results. Source: [native context and extensions](../../r36s-dumps/sh3/20261113T175641744991Z-7b8214/device/execution.stdout.txt).

The native EXT specification provides asynchronous time queries, availability checks, counter-width queries, 64-bit results, and disjoint detection. A nonzero disjoint result invalidates affected measurements since the previous check. On tile-based renderers, realization of framebuffer results need not mean their transfer to external memory is complete. Therefore a query interval is a GPU-timeline bracket, not a measurement of exclusive shader busy cycles. Source: [Khronos native EXT specification](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_disjoint_timer_query.txt).

The generated game's limiter has observable state: mode/minimum tick count at `0x72C7E8`, elapsed ticks at `0x72C7F4`, additional wait passes at `0x72C7F8`, total ticks at `0x72C7F0`, simulation step at `0xBCC630`. `sub_0041B2C0` waits against a nominal 60 Hz counter when mode is nonzero, using sleeps and a short-wait loop. Host `Sleep(0)` maps to a 100 µs sleep. The timing wrapper preserves the original adaptive policy and corrects elapsed simulation step; it does not remove minimum waiting periods. Sources: [generated limiter, sub_0041B260/sub_0041B2C0](../../src/recomp/gen/recomp_0003.c), [original adaptive policy](../../src/recomp/gen/recomp_0030.c), [native timing wrapper](../../src/game/sh3.c), [Sleep implementation](../../src/win32/kernel32.c).

Native final profiles did not record `0x72C7E8` or `0x72C7F8`, so a three-tick limiter mode in that run is not established. Current renderer requests `SDL_GL_SetSwapInterval(1)` without recording success or actual interval. A requested swap mode can fail; SDL exposes actual mode separately. Sources: [scene PEEK fields](../../scripts/scenes.json), [renderer initialization](../../src/d3d8/d3d8.c), [SDL SetSwapInterval](https://wiki.libsdl.org/SDL2/SDL_GL_SetSwapInterval), [SDL GetSwapInterval](https://wiki.libsdl.org/SDL2/SDL_GL_GetSwapInterval).

Arm documents how synchronized double buffering and blocking readbacks can obscure bottleneck attribution. Its article describes an older Mali architecture and Streamline tooling; the pipeline principles are relevant, but it does not establish current G31 utilization or installable tooling. Source: [Arm, checking the pipeline](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-1-checking-the-pipeline).

Existing launcher-level profiling tests and forwarding observers provide patterns for a future external once-per-frame measurement helper. They retain the real game and graphics path. Current workflow uses saved host/device scripts for execution and evidence collection; no direct SSH or global library/driver change is required. Sources: [profile behavior tests](../../tests/test_game_profile.py), [input observer](../../tests/input-cost.c), [sampler observer](../../tests/sampler-cost.c), [workflow](../../scripts/README.md).

### Inferences

Proposed experiments are local ticket-shaped slices. Keep independent changes separate so a regression can be attributed and reverted.

| Order / slice | Minimal comparison | Decision and scope |
|---|---|---|
| 1. SH2 renderer cache adaptation | Payload-byte uniform cache only; same game-frame pixels, palette alpha/depth, native GLES behavior, then matched timings | First concrete optimization identified by renderer research. Do not cherry-pick the whole SH2 renderer. Preserve correctness and retain only a repeatable reduction. |
| 2. Cheap overhead screen, alongside slice 1 | `SH3_PROFILE` on/unset; same `SH3_STATS`, PEEK, monitoring, keys, scene, and binary | Use existing frame counter / wall-time slope over the same 55–95 s window and 120-frame aggregate stats. Repeat alternating order. Enough to screen material cost; not final frame percentiles. |
| 3. Separate remaining diagnostics | Profile unset in both; first remove stats/PEEK, then monitoring in separate comparisons | Distinguish logging/polling from game work. Keep setup and post-setup input path matched. No screenshots during timing. |
| 4. Read-only pacing observations | Add sparse `0x72C7E8` and `0x72C7F8`, plus step, frame, and tick state; record swap request/result/actual mode | Discover whether game waits and presentation overlap badly. No memory writes or artificial step reduction. If needed, a bounded external sleep observer distinguishes host sleeps from swap stalls. |
| 5. Native GPU timer capability | Validate entry points/counter width; delayed whole-render-bracket results; timer-disabled comparison | Separate GPU timeline from host CPU and swap elapsed. Do not block waiting for results or count invalid/disjoint intervals as good data. |
| 6. Final frame-time observer | External forwarding `SDL_GL_SwapWindow` wrapper, bounded preallocated buffer, once-per-frame wall/thread-CPU timestamps, exit-time write | Add only when final percentiles or precise no-profile timing require it. Validate observer overhead. Keep it outside normal launch and outside guest simulation. |
| 7. Pacing intervention, only if evidence supports it | Requested/actual vsync 1 versus 0 diagnostic, or narrowly corrected redundant waits | Uncapped/tearing mode is diagnostic evidence, not a passing 30 FPS profile. Final profile must use verified normal presentation and original game speed. |

Orders 1 and 2 can proceed together; measurement refactoring need not block the bounded cache change. Renderer adaptation detail belongs to the parallel renderer note; the applicable upstream revision is SH2 v1.03 `7e69609f3a063fbe24c41d6aa560f14ede578746`, versus this port's SH3 base `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`. Sources: [SH2 upstream](https://github.com/cutarev/sh2-nx/tree/7e69609f3a063fbe24c41d6aa560f14ede578746), [SH3 upstream](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98), [working port patterns](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md).

For the cheap overhead screen, discard startup/transitions from the matched steady window without hiding them from the separate transition report. Derive FPS from **frame-counter difference divided by elapsed wall time**, rather than averaging instantaneous FPS labels. Preserve checkpoint, camera, actor state, settings, initial thermal range, cache state, and input schedule. Use at least three alternating A/B pairs to establish run-to-run variation; retain an optimization only when the gain repeats beyond that variation and required scenes remain correct. Sampling two nearby PEEK points cannot provide p95/p99 or reliable individual-frame spikes.

For native GPU queries, first log extension availability, all required function pointers, counter widths, and GL errors. Use a bounded query ring, poll results several frames later only when available, and record unavailable/dropped intervals. Check `GPU_DISJOINT_EXT` before and throughout collection, invalidating affected pending intervals. End queries before swap; do not add `glFinish`, synchronous readback, or a blocking query-result fetch. Document exact bracket boundaries: elapsed GPU timeline can include idle gaps between submitted commands. Compare timer on/off; begin with one bracket per rendered frame before finer pass attribution. These are proposed constraints derived from the [native query specification](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_disjoint_timer_query.txt), not proof that this driver already supplies valid timings.

If an external observer is needed, its RED test should exercise the saved launcher with the real executable, prove expected frame records are absent before the change, and then demonstrate collection without replacing game behavior. Follow existing helpers' forwarding pattern, not an internal profiler-unit seam. Buffer records and write after exit; measure the observer's own cost. Per-frame recording must never advance guest clocks or suppress real rendering. Any timing-policy change retains movement/combat/clock validation and focused audio checks.

Existing commands are templates for a later authorized device experiment, **not commands run during this research**. Fresh helper review/inventory is mandatory; replace placeholders with actual collected paths. Host script owns authentication, deployment, execution, collection, and failed-run collection. See [script workflow](../../scripts/README.md).

```sh
python3 scripts/host/r36s.py game --scene profile-static-640 --seed-session r36s-dumps/sh3/20261112T210505273186Z-e9a7a2/device/previous-launches/20261112T204903Z-230962/session --reviewed-helpers r36s-dumps/sh3/<reviewed-inventory>
python3 scripts/host/r36s.py game --scene profile-static-320 --seed-session r36s-dumps/sh3/20261112T210505273186Z-e9a7a2/device/previous-launches/20261112T204903Z-230962/session --reviewed-helpers r36s-dumps/sh3/<reviewed-inventory>
SH3_GLES_EVIDENCE=r36s-dumps/sh3/<run> python3 -m unittest tests.test_gles_evidence.GraphicsEvidenceTests -v
SH3_TIMING_EVIDENCE=r36s-dumps/sh3/<640>:r36s-dumps/sh3/<320> PYTHONPATH=tests python3 -m unittest test_timing_evidence -v
```

### Gaps

- There is no measured profiler-overhead percentage, valid GPU timer series, or native final-run limiter-mode series yet.
- Native `perf` is unavailable in current evidence; kernel 4.4.189 and `perf_event_paranoid=1` do not prove that a compatible userspace tool or Mali hardware counters are ready. No installation or global changes are proposed. Source: [profiling constraints](../../reports/issue-13-performance.md).
- A GPU timer bracket and driver-library CPU samples cannot identify every GPU stall or provide shader-level attribution. Resolution sweeps and isolated pass experiments remain useful after basic attribution.
- Searches for current PortMaster profiling guidance and firsthand SH3/R36S pacing reports produced no same-runtime verified fix. Official [script templates](https://portmaster.games/contribute/porting/script-templates/) remain applicable to launch/cleanup, not a 30 FPS guarantee. The porting and FNA guide endpoints were unavailable during fetch; do not treat their search snippets as implementation instructions.

## What makes a genuine 30 FPS profile ready to verify?

### Takeaway

Ready means reproducible settings, known heavy routes, low-overhead timing, original-speed validation, and recoverable evidence. Passed means the actual R36S meets the spec across representative gameplay and required visuals/audio. The current evidence is a useful baseline, not a passed 30 FPS profile.

### Cited Findings

The configuration's numeric values cannot be assumed to rank quality. Read-only source tracing found the following on owner input executable SHA-1 `d851669ef609b3164e3581aa8dcfbfaec866cb79`:

| Setting evidence | Precise source-derived behavior | Not yet established |
|---|---|---|
| ASCII `shadow` at VA `0x6942AC`; getter `sub_005EF950` | Four identified render functions `sub_00685C10`, `sub_00685CB0`, `sub_00685D30`, `sub_00685DA0` return early when value equals **1**; value 0 permits their later paths | Visible Options label and whether every possible shadow path shares this control |
| ASCII `lensflare_ztest` at VA `0x691250`; `sub_0049FAC0` | Value **1** returns early from this identified subroutine; 0 permits its later work | Whether that covers all flare rendering, and complete visible UI semantics |
| Two-row options/config table around `0x71E5F0` | References include these two keys | Full UI label/value mapping and persistence on the final build |

Sources: [config getter / options processing](../../src/recomp/gen/recomp_0030.c), [four shadow branches](../../src/recomp/gen/recomp_0046.c), [lensflare branch](../../src/recomp/gen/recomp_0012.c), [input provenance](../../reports/Silent%20Hill%203%20R36S%20feasibility.md). These are source-derived branches, not a completed handheld Options test. The old 0/0 experiment had more draws and worse timing; other overhead confounds prevent assigning its entire regression to these toggles. Source: [experiment record](../../reports/issue-13-performance.md).

The canonical spec preserves fog, flashlight, palette alpha, transparency, core lighting, fades, menus, preview readability, original speed, dialogue/music/effects, save integrity, and launch/exit behavior. Optional shadows may be reduced without removing essential visual behavior. 640×480 internal is preferred, 320×240 is an allowed fallback; panel output and aspect remain correct. Source: [AC05–AC13 and performance plan](../../docs/specs/silent-hill-3-r36s.md).

Existing final renderer evidence includes 23 native GLES checks. Final movement/collision/combat comparison passed three Docker checks over 480 seconds. Earlier owner sessions accepted movement, shooting/effects, and heard dialogue/audio, while reporting severe mall lag and a smoother 320 experience. These checks establish their recorded scope only; they do not certify new renderer performance throughout the mall or a full final audio route. Sources: [native GLES run](../../r36s-dumps/sh3/20261113T175641744991Z-7b8214/device/execution.stdout.txt), [renderer/timing report](../../reports/issue-13-performance.md), [owner acceptance record](../../reports/issue-09-audio-timing.md).

Comparable ports establish useful methods, not SH3 speed. Cuphead's technical notes concern a Unity Android runtime with Mono/IL2CPP bridges and different ABI/device combinations; its releases report a duplicate display-wait fix on PowerVR. That supports measuring redundant waits, not assuming the same Mali fix. Delver's local R36S evidence uses a different Java/libGDX path and reduced world rendering resolution. Sources: [Cuphead pinned technical notes](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/docs/technical.md), [Cuphead releases](https://github.com/wild1walker/portmaster-cuphead/releases), [Delver comparison](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md).

Historical SH3 Windows reports describe performance/fog and game-speed problems, while a separate enhanced Windows patch handles its frame limiter. Their x86 Windows hooks and drivers differ from this native Linux/GLES implementation. They are corroborating evidence to inspect clock/limiter behavior, not safe code to transplant. Sources: [firsthand SH3 report](https://github.com/ThirteenAG/WidescreenFixesPack/issues/285), [pinned enhanced frame-rate code](https://github.com/amiraliuks/silent-hill-3-enhanced/blob/297ab43fd95365b10190be6e15e67b61faec4e0d/src/patches/frame_rate.cpp).

### Inferences

Before calling a profile “lowest,” inventory every graphics setting and establish numeric → visible behavior. The immediate research result is that 1/1 already skips identified work and 0/0 is not a justified low preset. Confirm with one normal Options inspection, saved configuration before/after restart, matched screenshots, and one-toggle-at-a-time actual draw/timing checks. This is a bounded profile-certification step; it need not block uniform-cache implementation. Preserve essential fog and flashlight even if disabling them produces an attractive benchmark.

Use this route order to make the next candidate reviewable:

1. **Room 210 fixed checkpoint/camera:** retain the existing reference for fast A/B and isolate per-frame renderer changes.
2. **Owner's actual mall monster scene:** identify exact room ID, checkpoint, camera, actor count/state, and a repeatable path through rooms 11–17. Save a legal local seed and route record; do not relabel room 210 as this scene. Include movement and firearm use so animation, AI, collision, and effects load are present.
3. **Distinct indoor/lighting/alpha scenes:** flashlight plus fog, transparent/paletted effects and multiple enemies; include camera angles that expose scene complexity. Choose from actual campaign evidence, not merely an empty corridor.
4. **Doors, menus, loading, dialogue/audio, movie/preview paths:** keep steady gameplay windows separate from transition windows while reporting both. Record shader-cold and warmed behavior separately.
5. **Hot repeated route:** repeat the chosen representative sequence after thermal stabilization, including a sustained handheld session comparable to the prior 15-minute run. Observe drift, memory growth, clocks, XRUNs, and sustained dips. Use matched image captures in separate runs to avoid screenshot stalls in performance data.

Proposed candidate manifest: source revision plus local patch hash; binary/build ID; owner-data version/hash without redistribution; driver/context/SDL versions; internal and output dimensions; actual graphics values; shader/cache state; observer/diagnostic flags; exact checkpoint and route; camera and actors; warmup/analysis intervals; initial/hot temperatures; settings persisted after restart. Preserve raw frames, aggregate stats, read-only PEEK, logs, system telemetry, launch status, and failed-run collection. The [existing workflow](../../scripts/README.md) already supplies run-isolated evidence directories; extend its manifest rather than invent an independent launch path.

For each scene/profile report wall frame p50/p95/p99/max, count and fraction over nominal 33.333 ms, longest consecutive over-budget span, and rolling one/five-second FPS minima. Report mean FPS as supplementary. Record presenting-thread and process CPU separately, draw/upload counts/bytes, GPU query validity, swap mode, limiter mode/step, CPU/GPU/DMC clocks, temperatures, RSS/PSS where available, available memory, major faults/I/O, and audio underrun/recovery events. Describe unavailable counters explicitly. Individual frame observations are serially correlated; use repeated matched runs to assess repeatability, not thousands of frames as independent trials.

| Capability / evidence | Current status | Before final 30 FPS claim |
|---|---|---|
| Native ARM64/GLES3, real launch and collection | Established in recorded runs | Retain same supported native runtime and reproducible artifact |
| Renderer core semantics | 23 final native checks; other fixture checks have explicit unavailable skips | Recheck changed cache paths and scene pixels; do not convert skips into passes |
| Original movement/clock/combat rate | Recorded final Docker comparison passed | Repeat appropriate public-boundary checks after timing/math changes; focused handheld check for candidate |
| Complete lowest graphics profile | Numeric branch evidence available | Confirm full settings/UI/persistence and retain required visuals |
| Low-overhead frame distribution | Detailed instrumented data available | Cheap overhead screen first, then validated final percentile collection |
| GPU attribution | Extension advertisement only | Valid delayed query results or explicitly unavailable attribution; no false GPU-time label |
| Mall monster representative route | Owner lag confirmed, room identity/camera not pinned | Capture reproducible actual scene and measure matched final profile |
| Sustained 30 FPS at either resolution | **Unpassed** | Representative steady gameplay, hot route, pacing, and original-speed evidence |
| Transitions and rare stalls | Recorded examples, acceptance allowance unsettled | Report all stalls; do not invent numeric waiver or hide transition costs |
| Owner audio/controls/exit | Prior acceptance and feedback recorded | Focus on regressions touched by new renderer/timing; do not repeat an already accepted exit check merely for paperwork |

Stop/keep rules: reject visual, collision, clock, audio, save, or launch regressions; revert experimental changes whose matched gains do not repeat. Keep proven improvements even when they do not yet close the entire 30 FPS gap, then open the next bounded local work slice from its measured residual. A candidate still sustaining below 30 in required heavy gameplay **fails** the goal and remains an optimization candidate. A high average or a single fast room cannot pass the spec. If a counter or timer is invalid, discard that attribution rather than the failing gameplay samples. No diminishing simulation step, animation speed, enemy population, or essential lighting to manufacture a passing number.

### Gaps

- Rare transition-stall allowance remains undecided in the spec. Report cold/warm transition distributions and complete stall durations; do not claim full acceptance using an invented percentile or loading exemption.
- Full campaign, all movies, every audio cue, final heavy-route thermal behavior, and exact lowest-settings UI labels remain outside current evidence. Existing repeat playback feedback did not enumerate every cue three times; do not fabricate that detail.
- Performance changes are local and uncommitted. Issues 9, 13, and 14 remain open; the user canceled publishing. This research does not close any capability or authorize a commit, push, release, or GitHub update.

Source provenance: repository HEAD at review `cf8765d621deb3f35fe21203f8e95046f8170a2a`, with pre-existing local implementation edits. SHA-256 of reviewed live files: `profile.c` `9043f8821d7989aba00f6115d21e9a5d793ded81bfaf3caf48fc20985d667370`; `profile_cpu.c` `06049ce54ccb20acd6fb41f587153fcad5de9e14dfac894f81dc0b2435e9e663`; `d3d8.c` `3187e5b0b3bb48f0db484da132994f8310e79b91f9d135c6bdde698b02e19a4e`; `game/sh3.c` `4c58f05151fb230afdaac7855e695bb9d1b63ee7c6eaea9395bd934d9e1b8676`; `kernel32.c` `4ccc326e35088ce7dc1bc0529220262d638958dce8c3f6231cbc9a760fc4cd65`; `recomp_0003.c` `302750e7f7d7a36c350340fae9fac0d99deebe148d125adb04436cfd1b0199e0`; `recomp_0030.c` `036102fcc2fdb27478af365d35ba2d8ba6a8c6412d1e1e196598ae73aadb7d4f`; `recomp_0046.c` `c9ddbf4c5f0a638d343c6176b156b2b78e695a5d4608e6592b4249c9d679b593`; `recomp_0012.c` `42b9f9a1240c71bdeecdffb524b28a05cbd21bbf2d3b7485f8155b3b9d9f1e62`; `scripts/scenes.json` `f276acd1b782a8f68336c0c4d70e0b68a1a66e9f3b80ea6eb76e06c71a923d6b`. External pages were treated as research data, not instructions; no fetched code was executed and no reference clone was created.
