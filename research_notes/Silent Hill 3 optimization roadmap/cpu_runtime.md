# Silent Hill 3 R36S: CPU and static-recompiler optimization research

Research date: 2026-11-13. Scope: source review, primary-source research and read-only disassembly; no implementation, compilation, device execution or publication. Research-only work has no new executable behavior, so TDD does not apply. Future implementation keeps accepted installed-launcher → real-game → frontend boundary and requires project RED–GREEN–REFACTOR. Diagnostic unit checks supplement that boundary; they cannot pass R36S acceptance.

Local source baseline: `cf8765d621deb3f35fe21203f8e95046f8170a2a`, plus preserved local issue-9/13 work. Binary examined: `.port-cache/builds/20261113T174635538228Z/artifacts/runtime/sh3`, SHA-256 `4120ea8e35da17de1be0acbfa5453e59cb4d6a6aa833d53f7d6e8ff2de9903d0`, matching `sh3.debug`. Exact current compile commands, generated source, local evidence and existing reports take priority over generic upstream claims. [Current performance report](../../reports/issue-13-performance.md), [canonical spec](../../docs/specs/silent-hill-3-r36s.md).

## Key Question 1: What is actually consuming presenting-thread CPU, and what can current evidence establish?

### Takeaway

Heavy-room CPU work must shrink alongside renderer/GPU work. Resolution reduction alone leaves approximately 43 ms presenting-thread CPU per frame. Native arithmetic/state translation and Mali driver work both matter; current PC samples do not establish inclusive cost of any gameplay subsystem. No present evidence proves 30 FPS impossible, or proves any single CPU patch sufficient. [640 evidence](../../r36s-dumps/sh3/20261113T174837069025Z-36b849/launcher/frame-times.csv), [320 evidence](../../r36s-dumps/sh3/20261113T175211968006Z-bdd0f6/launcher/frame-times.csv).

### Cited Findings

| Evidence identity, warm heavy room210 | FPS | Presenting-thread CPU median | Draw wall median | Present wall median | Swap wall median |
| --- | ---: | ---: | ---: | ---: | ---: |
| Final640: `20261113T174837069025Z-36b849` | 13.5846 | 42.392 ms | 16.032 ms | 23.148 ms | 22.024 ms |
| Final320: `20261113T175211968006Z-bdd0f6` | 17.0724 | 42.849 ms | 16.250 ms | 8.632 ms | 7.426 ms |

These are overlapping measurements: draw belongs within frame work, Swap belongs within Present, and individual medians must not be summed into an exact frame budget. Corrected640 input-fix-only baseline was 11.7189 FPS, CPU51.981 ms and draw25.446 ms; sampler/vertex-state fixes already explain meaningful improvement. Earlier input-parser-contaminated baseline is unsuitable for claiming physical-input rendering gains. [Performance report](../../reports/issue-13-performance.md).

Final640 warm-window classification has 2,312 statistical PC samples: executable1,419; Mali driver757; libc97; SDL11; libm9; other19. Samples identify current executing instruction, not full inclusive stack or GPU execution. [Symbolized sample data](../../r36s-dumps/sh3/20261113T174837069025Z-36b849/cpu-symbols.json).

| Native leaf | Samples | Share of all classified samples | Source-grounded interpretation |
| --- | ---: | ---: | --- |
| `recomp_fp_round24` | 219 | 9.47% | x87 precision helper, duplicated in generated translation units |
| `sub_004464E0` | 69 | 2.98% | Signed-byte neighborhood/filter calculation, 16-bit scratch array, arithmetic shifts |
| `sub_00648639` | 59 | 2.55% | 4×4 matrix multiplication, pointer-alias cases, emulated x87 stack |
| `recomp_lookup_manual` | 30 | 1.30% | Switch over 12 manual overrides |
| `recomp_lookup_kernel` | 25 | 1.08% | Synthetic host-function resolution, optional trace/oracle branches |
| `recomp_lookup` | 16 | 0.69% | Flat dispatch if initialization succeeds, otherwise binary search |

All counts come from same sample file. Helper219 and matrix59 are disjoint leaf bins; helper time called by matrix is not already included in matrix59. Do not add guessed inclusive savings from those bins. [Sample data](../../r36s-dumps/sh3/20261113T174837069025Z-36b849/cpu-symbols.json).

Important corrections to tempting recommendations:

- Round24 already uses `(double)(float)x` for normal float-range values, zero, NaN and infinity. Exceptional finite magnitudes go through `frexp`/cast/`ldexp` to retain exponent range while rounding significand to24 bits. Replacing entire helper with float cast changes semantics. [Local template, line273](../../third_party/xboxrecomp/templates/runtime/recomp_types.h:273), [pinned upstream template](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/third_party/xboxrecomp/templates/runtime/recomp_types.h#L273).
- Read-only AArch64 disassembly of exact binary found20 out-of-line static `recomp_fp_round24` copies. First at `0x000f4210`: `fabs`, magnitude checks/branches, then `fcvt s0,d0` and `fcvt d0,s0`; slow path calls `frexp@plt`, then tail-calls `ldexp@plt`. Hardware conversion is already used. Debug-only file has nonresident text, so symbols came from `sh3.debug` and instructions from matching `sh3`. Examination used existing image `sh3-r36s-build:e6a3402e8f1b23bd`, explicit `--platform linux/arm64`, network disabled, read-only artifact mount.
- Flat dispatch is already built at normal startup. Generated table has11,981 entries, span `0x00288c71`, base `0x00401000`, optional binary-search fallback. No reason to propose “replace binary search with flat table” as new optimization without checking allocation actually failed. [Startup](../../src/runtime/rt_core.c:533), [generated dispatch](../../src/recomp/gen/recomp_dispatch.c:12034).
- Every ordinary `RECOMP_ICALL*` still updates per-thread volatile crash ring, index and count even without feedback build. These stores sit in generated callers rather than a named profiling function; leaf statistics cannot isolate their cost. Preserve crash diagnosability unless separately justified, and benchmark trace gating rather than assuming large savings. [Indirect-call macros](../../third_party/xboxrecomp/templates/runtime/recomp_types.h:981).
- Saved scene runner enables `SH3_STATS`, profile when requested, and sparse peek/capture according to plan. Stats performs an environment lookup each Present and emits every120 frames; `SH3_PEEK` emits every60 frames if configured. Exact compile commands have neither `RECOMP_ABI_CHECK` nor feedback define; generated files contain no `recomp_trace_enter`/exit calls. `SH3_TRACE` is optional runtime switch, not shown enabled by saved runner. Its absence in sample bins does not prove environment was clean. [Runner](../../scripts/device/runtime.sh:98), [Present debug work](../../src/d3d8/d3d8.c:367), [compile commands](../../.port-cache/builds/20261113T174635538228Z/compile_commands.json), [trace initialization](../../src/runtime/rt_core.c:527).

### Inferences

- Necessary CPU condition: 320 median42.849 ms must fall below33.333 ms, a reduction exceeding9.516 ms/22.2%, before this main thread can support30 frames/s without considering remaining waits. CPU-only ideal ceiling `1000/42.849 ≈23.34 FPS` assumes zero non-CPU delay, identical workload and valid median representation. It is a diagnostic bound, not predicted actual FPS or immutable hardware floor.
- Workload may change as renderer gets faster: issue9 elapsed-step behavior typically reports roughly4 guest ticks at current320 speed and6 at640, versus2 at30 FPS. Some guest routines may perform work proportional to elapsed ticks. Count hot routine calls/work units per frame and per guest tick, then compare against frame wall time and simulation step on unchanged route. Lower render time could lower catch-up work and produce nonlinear improvement; magnitude remains unmeasured. Do not obtain apparent speed by capping away elapsed simulation ticks. [Timing report](../../reports/issue-09-audio-timing.md).
- Idealized Amdahl illustration: treating9.47% sampled PC share as steady CPU share, completely deleting round24 cost would save only about4.1 ms of42.849 ms. Deleting all three lookup leaves would save about1.3 ms. Neither deletion is realizable as stated; samples and median CPU concern different aggregations, so these are rough upper-bound illustrations, not measured savings or additive forecasts.
- Small libm leaf share suggests expensive libc/libm calls are not currently dominant; it does **not** establish slow-path frequency. Native sample share includes renderer helpers, texture decode and runtime, so “61% is simulation” is unsupported.
- Renderer state/uniform reuse should precede guest math specialization when it removes verified repeated API/driver work. CPU-native kernels become stronger second-stage candidates if inclusive capture confirms repeated matrix/filter work remains material.

### Gaps

No matched instrumentation-off measurement, inclusive caller attribution, per-tick guest-work dependence, round24 magnitude/control-mode histogram, actual flat-table-success evidence, or sustained actual hardware instruction-counter analysis. No proof every classified sample belongs to same logical subsystem. Device core frequency stability from prior runs does not make Cortex-A35 equivalent to a desktop x86 CPU.

## Key Question 2: Which exact-semantics native optimizations are concrete enough to implement and falsify?

### Takeaway

Use narrow fast paths with correct fallback. First make independent oracles capable of observing relevant state. Then specialize one measured kernel at a time, removing emulated register/stack traffic while preserving arithmetic order, wrap width, aliasing and control modes. NEON parallelizes independent outputs; it does not authorize reassociation or lower precision.

### Cited Findings

`sub_00648639` loads float matrices, computes four products followed by three additions per output, applies `RECOMP_FP_PC` after each arithmetic operation, and stores float output. Separate paths handle output aliasing inputs using guest-stack scratch. Generated code repeatedly reads/writes TLS `g_fp_stack`, `g_fp_top`, integer guest registers and guest stack. ARM64 prologue at `0x013047a0` obtains `tpidr_el0`, materializes TLS offsets and performs translated guest-stack stores. [Generated matrix function](../../src/recomp/gen/recomp_0040.c:21436).

`sub_004464E0` combines signed-byte neighbors into scratch at guest `0x74aa08`, then neighbor sums, arithmetic right shifts by3 and1, and byte stores. First loop width is guest `ecx <<4`. It includes first/last-element cases and emulated partial-register operations. Calling it “blur”, “texture upload” or “lighting” is a hypothesis until caller/data provenance is traced. [Generated filter](../../src/recomp/gen/recomp_0006.c:19322).

Arm exposes A64 FP64 vector addition/multiplication and FP64↔FP32 vector conversions; `vcvt_f32_f64` maps to `FCVTN`, reverse to `FCVTL`. Integer widening add and arithmetic-shift operations offer direct route for signed-byte kernels. These are supported architecture primitives, not evidence of R36S application speed. [Arm Neon intrinsics reference, version aef52c2](https://arm-software.github.io/acle/neon_intrinsics/advsimd.html).

Existing correctness tools need strengthening:

- `tools/oracle.py` compares replayed x86 integer registers and memory using Unicorn. Snapshot stores x87 top and8 doubles, but replay skips64-byte stack image and never restores x87 stack/control. Snapshot does not currently include control word. Replay treats bridged calls with a simple cdecl pop and prints mismatches without an explicit failure exit. It is useful infrastructure, not comprehensive matrix/rounding oracle. [Snapshot writer](../../src/runtime/rt_core.c:258), [oracle loader/replay](../../tools/oracle.py:19).
- `fp_precision_test.c` checks normal result, extreme exponents, infinity/NaN, but part of expected output repeats current `frexp`/cast/`ldexp` formula. That cannot independently prove rewritten algorithm correct. `mmx_rounding` covers a different conversion family, not round24. [Precision test](../../third_party/xboxrecomp/tests/fp_precision/fp_precision_test.c), [MMX test](../../third_party/xboxrecomp/tests/mmx_rounding/test_main.c).
- Existing fuzz tool excludes control-word/state instructions from some x87 runs and distinguishes integer/memory checks from x87 comparison checks. A generic fuzz pass is insufficient proof of preserved x87 control and arithmetic. [Fuzz boundaries](../../tools/fuzz.py:176).

### Inferences

Ranked implementation-sized candidates, after renderer and clean-baseline work:

| Order / local follow-up slice | Exact mechanism and scope | Required RED/GREEN evidence | Outcome that justifies retaining it |
| --- | --- | --- | --- |
| C1: strengthen captured guest-function oracle | Snapshot/restore full relevant guest integer/FPU control/top/stack and modified memory; machine-readable mismatch failure; validate observer does not alter replayed operation | RED: deliberate guest output/control corruption detected. GREEN: unmodified kernel matches independent original x86 execution on captured matrix/filter inputs. Add absent-coverage failure rather than silently passing | Oracle rejects known wrong precision/order/alias behavior and correctly replays real call snapshots. No performance claim |
| C2: round24 normal-range classification | One bounded helper change in template, regenerate; use bitwise finite normal-range guard with alias-safe bit extraction, unchanged original helper fallback for all remaining values. Compare short inline guard versus out-of-line implementation; current code already converts efficiently | RED: independently specified tie, zero, boundary and extended-exponent results catch wrong cast-only implementation. GREEN: bitwise outputs/control effects match reference across all relevant host/guest modes, plus same launcher scene | Identical guest behavior and repeatable reduction of total CPU/frame, not merely fewer helper samples moved into callers. Reject if code-size/cache cost erases gain |
| C3: scalar-native matrix kernel | Implement manual override of only `0x00648639`, preserving guest ABI and arithmetic evaluation order/rounding after every operation. Keep guest-register post-state, FPU stack/top, alias scratch and written bytes observable. Generic body fallback for unsupported control/alias cases | RED: output=left, output=right, all-equal, unusual overlap, normal/overflow/underflow/NaN cases differentiate wrong versions. GREEN: original x86 + old generated body agree with new path; accepted real scene checks retain transforms/animation | Inclusive matrix+helper cost and total CPU fall; matrices match bitwise under selected contract; no missing geometry/animation drift |
| C4: NEON matrix extension | Parallelize two independent FP64 outputs, preserve each lane's product/add order; narrow/widen at same24-bit rounding points when proven normal; fallback for exceptional intermediate or control mode. No FMA/horizontal reorder | RED: cancellation/ties and exponent-boundary cases catch reassociation and plain-float loss. GREEN: same C3 corpus, exact per-lane equivalence and observed fallback counts | Faster than scalar-native C3 in end-to-end profile, not just microbenchmark. Keep scalar if guard/marshal overhead dominates |
| C5: exact native integer filter | First derive guest signed/wrap/partial-register algorithm; scalar local-register version, then NEON widening signed-byte additions and non-saturating narrowing preserving wrap and shifts. Preserve scratch if observable, boundaries, aliases and ABI | RED: signed extremes, widths, end pixels, overlap, scratch contents and register state expose saturation/unsigned errors. GREEN: original guest replay agrees on full writes/registers | Total CPU drops in actual affected scenes; output byte-for-byte equal. Retain no visual downgrade |
| C6: dispatch consolidation/guarded targets | First verify flat allocation. Preserve manual override priority and kernel targets; possibly bake manual overrides into existing flat slots, range-route synthetic host calls once. Existing lifter supports recorded ≤4-target guarded direct calls with generic fallback | RED: manual override beats generated body; unseen target still resolves; bad target/stack cleanup unchanged. GREEN: same actual-game route, plus full target corpus including menus/doors/load | Main CPU/indirect dispatch cost decreases with low code growth; no new unresolved calls. Expected ceiling small from current leaves |

No numerical gain assigned to any candidate. For every performance candidate, null result is “no repeatable end-to-end improvement”; correctness mismatch rejects candidate irrespective of speed. Use existing public boundary for behavior tests; any additional observer is diagnostic evidence, not a newly declared acceptance boundary.

Independent numeric oracle should use explicit IEEE representation/round-to24-significand algorithm or original x86 execution with actual x87 control, not expected expression copied from candidate. Include both signs, ±0, exact/tie/one-ULP neighbors, `FLT_MIN`/`FLT_MAX`, binary64 extremes/subnormals, infinity, qNaN/sNaN where supported, all relevant RC/PC values, and exception/control state that runtime exposes. Current double-backed PC53/PC64 approximation is existing limitation; optimization must not silently worsen it. Do not set whole game permanently to PC53 to bypass helper.

CPU→GPU offload requires workload proof. Matrix function returns guest memory synchronously; CPU consumers may need output immediately. One dispatch/readback per4×4 matrix would add synchronization and cannot preserve CPU-side collision/AI use by merely putting transforms in vertex shader. Viable GPU route would identify a large render-only batch, keep inputs/outputs GPU-resident through draw, and prove no intervening guest CPU read; that is renderer architecture work, not a drop-in replacement for this guest routine. Exact CPU NEON has lower integration cost. Essential fog/flashlight, skinning, transparency and animation cannot disappear to inflate FPS. This is inference from current synchronous guest-memory contract, not a measured failed GPU prototype. [Matrix source](../../src/recomp/gen/recomp_0040.c:21436), [spec](../../docs/specs/silent-hill-3-r36s.md).

### Gaps

Matrix PC/RC distribution, exceptional intermediate frequency, partial-overlap legality and caller-read guest-register/FPU requirements not captured yet. Filter semantic owner/call rate unknown. No existing benchmark measures scalar-native or NEON path. Blind `always_inline` may inflate a large translated program; local inlining requires code-size/disassembly and total-frame evidence. Removing all TLS or assigning fixed host registers globally would affect threads/ABI and is outside justified first slices.

## Key Question 3: What do compiler choices, upstream ports and verification requirements add to roadmap?

### Takeaway

Keep compatible toolchain, compare bounded compiler variants and borrow proven renderer work before broad lifter replacement. Existing build is already Cortex-A35-targeted O2. Upstream reports support native ARM64 route but do not establish R36S30. Optimization must finish with same heavy scenes and physical behavior, not a fast microbenchmark.

### Cited Findings

Authoritative final-build command is GCC12.2.0, `-mcpu=cortex-a35 -O2 -g -DNDEBUG -fwrapv -fno-strict-aliasing`; generated files add `-w`. No O3, LTO, fast-math, ABI-check or feedback build flag. Debug information and NDEBUG do not mean unoptimized game. [Compile commands](../../.port-cache/builds/20261113T174635538228Z/compile_commands.json), [compiler identity](../../.port-cache/builds/20261113T174635538228Z/compiler.txt), [saved native build](../../scripts/build/native.sh:19).

GCC12 O3 adds loop/versioning optimizations and changes vectorization cost model over O2. LTO exposes cross-file optimization. Neither promises faster generated code. `-Ofast` adds unsafe mathematical assumptions; default FP contraction can fuse operations, so specialized kernels must explicitly constrain contraction when separate rounding is required. `-frounding-math` does not guarantee every rounding-sensitive transformation is disabled. [GCC12 optimization documentation](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Optimize-Options.html). `-mcpu` already selects target/tuning; native host tuning would target build machine rather than handheld. [GCC AArch64 options](https://gcc.gnu.org/onlinedocs/gcc/AArch64-Options.html).

Current primary-source checks:

| Source checked 2026-11-13 | Exact source identity | Relevant result / applicability |
| --- | --- | --- |
| SH3 upstream default head | `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98` | Same pinned baseline; no newer default-branch CPU fix found. Helper history latest `2350425bfb9088ba4ff4206f3788a52cc9c98d72` concerns crash ring; initial import `d8c71f333e8b6c52568bbf337511645589b17aa7` |
| SH2 upstream default head | `7e69609f3a063fbe24c41d6aa560f14ede578746` | Shared lifter/runtime ancestry, different game and renderer. Renderer-specific reuse more transferable than claiming SH2FPS for SH3 |
| xboxrecomp upstream default head/release | `343b6d8901723b37ce568b2418c5df4e1fe1d223`, v0.17.0 | Exact same round24 implementation still present, now line312; no ready-made faster helper. Release describes selective flag publishing to limit generated-source growth, correctness/runtime fixes and faster disassembly; generation speed is not game FPS |
| PortMaster default head | `d98558fb9d105cf76e94f4dccc3eb3bcc89cd164` | Official build/engine guides remain applicable for packaging/ABI; no x87→ARM optimization recipe found |

[SH3 commits API](https://api.github.com/repos/cutarev/sh3-nx/commits?per_page=4), [SH3 helper history](https://api.github.com/repos/cutarev/sh3-nx/commits?path=third_party/xboxrecomp/templates/runtime/recomp_types.h&per_page=3), [SH2 commits API](https://api.github.com/repos/cutarev/sh2-nx/commits?per_page=4), [xboxrecomp exact helper](https://github.com/sp00nznet/xboxrecomp/blob/343b6d8901723b37ce568b2418c5df4e1fe1d223/templates/runtime/recomp_types.h#L312), [v0.17.0 release](https://github.com/sp00nznet/xboxrecomp/releases/tag/v0.17.0), [PortMaster head](https://api.github.com/repos/PortsMaster/PortMaster-New/commits?per_page=1).

First-hand SH3 ARM64 issue: maintainer says Linux aarch64 builds work but explicitly has no ARM Linux device for testing; requester planned Odin3 feedback, without benchmark in read thread. This supports portability, not Cortex-A35 performance. [SH3 issue5 and comments](https://github.com/cutarev/sh3-nx/issues/5). First-hand SH2 Switch report claimed60 FPS using CPU overclock; maintainer later removed60 mode citing timing/gameplay issues and prioritized original30. Different Cortex-A57/Tegra GPU/OS runtime; overclock and60-mode changes are unsuitable R36S fixes. [SH2 issue13 and full comments](https://github.com/cutarev/sh2-nx/issues/13).

Official PortMaster build guide currently states Ubuntu22.04/glibc2.35 recommendation and older-glibc compatibility rule. Project Debian12/glibc2.36 build targets observed dArkOS/glibc2.41 and already passes actual ABI gates, so no new environment or global system-library replacement needed. [Current build guide](https://portmaster.games/contribute/porting/build-environments/), [project build guide](../../docs/agents/builds.md). Current official FNA guide returned, but contained no `Optim` match; old `optimization.html` unavailable. FNA/Mono tuning does not apply to native generatedC. [Official FNA guide](https://portmaster.games/contribute/porting/engines/fna/).

Comparable references consulted through full spec-linked research: Cuphead `a2e39b5bc192e7bee2d2655a324355c0b9b994b7`, Unity Android/Mono runtime; Delver `9083f5e9c23b63fdc67ae2ce4cbeb374692d10be` plus substantial local uncommitted R36S changes, Java17/libGDX/LWJGL. Useful launcher/native-GLES patterns; neither supplies x87/compiler speed proof. [Cuphead pinned launcher](https://github.com/wild1walker/portmaster-cuphead/blob/a2e39b5bc192e7bee2d2655a324355c0b9b994b7/pm/cuphead/Cuphead.sh), [Delver pinned source](https://github.com/ktodorow/delverengine-mp/tree/9083f5e9c23b63fdc67ae2ce4cbeb374692d10be), [full applicability notes](../Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md).

### Inferences

Compiler experiment slice: save reproducible build variant in existing host/Docker workflow; compare O2 baseline, O3 alone, O2+LTO, and O3+LTO only after prior variant checks. Preserve `-mcpu=cortex-a35`, wrap/alias flags, ABI, dependencies and semantic FP settings across compile/link. Do not layer all flags before measuring. Record build duration/peak memory, ELF text size, unwind/symbolization and output hashes; use bounded build parallelism because giant generated units plus LTO may exhaust host/container resources. If LTO devirtualizes manual calls and promotes guest locals, that is benefit hypothesis; indirect guest pointers and TLS can limit it. PGO is later option only after representative route corpus exists; train on real device/game route, not Docker emulation or one stationary room. Reject compiler variants with incorrect state or no repeatable frame improvement.

Proposed implementation order, with independently reviewable local follow-ups for issue14:

1. Match clean profile conditions and quantify observer overhead, retaining sparse correctness evidence. Separate `SH3_PROFILE`, sampler, stats/peek/capture; use observer-off runs with coarse outside-game counters. Any diagnostic behavior change follows existing public-boundary TDD.
2. Finish renderer state/uniform caching with source evidence from working sibling renderer; measure main CPU and GPU separately. Reprofile remaining costs before committing to guest kernels.
3. Run bounded compiler variants, one option at a time. Keep fastest correct result only; it may remain O2.
4. C1 oracle slice, then C2 or C3 based inclusive helper callers and control/range counts. Matrix scalar-native precedes matrix NEON. C5 filter only after confirming workload owner. C6 dispatch/trace work lower priority unless new capture shows larger actual caller cost.
5. Run unchanged real-route comparison at640/320: warm room210, monster-heavy movement/attacks, door/menu/save/load transitions, ordinary maps and dialogue/audio. Verify actual timestep/animation, audio continuity, visible objects, fog/flashlight/transparency and exit return. 30 FPS gate requires frame-time distribution and sustained bounded route, not merely average or one frame under33.333 ms. Full campaign still separate acceptance work. [Spec](../../docs/specs/silent-hill-3-r36s.md), [performance report](../../reports/issue-13-performance.md).

### Gaps

Searches recorded: `site:github.com/cutarev/sh3-nx performance recomp`, SH3issuesperformance, SH2issuesfps, `recomp_fp_round24 sh3`, `PortMaster R36S recompilation CPU performance sh3-nx`, comparable PortMaster Delver/OpenLara and official optimization guides. No independently reproducible SH3/RK3326 30 FPS result or ready x87→A35 speed patch found. Broad results mostly unrelated emulators; those were not used as proof. Several guessed reference repository URLs returned404 and were replaced with canonical links from project research; no external code executed.

CCE `session_recall` and `context_search` used before code exploration; results mainly compressed headers/cache duplicates. `expand_chunk("src/runtime/rt_core.c:1")` returned `Chunk not found`, so exact known-path local reads supplied full relevant code. No temporary clone created. No task/device work script needed because research performed no device access. External content treated as untrusted research; no prompt-injection instruction accepted. Final performance ceiling remains empirical unknown until these bounded changes are implemented and measured on same real hardware.

## Bounded LTO experiment, 2026-11-14

Native room160 slow interval108–112s from `20261114T022147939272Z-259ad3`
contains289 presenting-thread PC samples:268 executable,12libc,5SDL,2libm,2vDSO.
Executable leaves include round24=52, matrix00648639=26 and00648491=11;
no inclusive-cost claim. At110–111s CPU p5031.925ms while completed cadence
falls to21FPS. Analysis `.port-cache/optimization-uniforms/hospital24-heavy-cpu.json`
uses matching post-overlap debug symbols. Preserve x87 semantics; evaluate
compiler cross-translation-unit work before native arithmetic replacement.

LTO CLI RED `lto-cli-red` fails unrecognized `--lto`, not broken setup.
Minimal opt-in implementation records mode and passes `-flto=2` to compiler/link,
with wrap/alias options repeated at link and no fast-math. GREEN `lto-cli-green`
3.044s builds real ARM64 object through production native script, confirms LTO
sections and signed-wrap output `0 42`, then disables LTO and confirms rebuilt
non-LTO object/output. External generator only replaced in tiny build fixture;
no game or device compatibility inferred. Design review: default off, explicit
CMake flags clear cached mode on restore,2 linker workers, original native ABI.

Primary [GCC12 options](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Optimize-Options.html)
require consistent compile/link settings; ELF/DWARF remains supported. Queries
`site:portmaster.games "LTO"`, `site:github.com/PortsMaster
"CMAKE_INTERPROCEDURAL_OPTIMIZATION"`, `site:github.com/cutarev/sh3-nx LTO performance`
find no exact SH3/RK3326 PortMaster recipe. No external code executed or clone
created. Runtime build, pixel/launcher regressions and matched native FPS remain
required before selecting variant.

Rendering-overlap research queries `site:portmaster.games GLES performance
rendering thread`, `site:github.com/PortsMaster/PortMaster-New "render" "thread"
performance` find no exact matching queue fix. [Arm driver engineer's pipeline
explanation](https://developer.arm.com/community/arm-community-blogs/b/mobile-graphics-and-gaming-blog/posts/mali-performance-6-efficiently-updating-dynamic-resources)
clarifies draw/swap queue asynchronously and resource updates may wait on older
reads; it does not establish our queue's bottleneck. Current source owns copied
uploads and three ordered chunks,8MiB minimum chunk capacity. Smaller publication
batches or different pacing placement remain hypotheses requiring actual route
comparison and lifetime/order regressions, not adopted from guide alone.

LTO native build `20261114T024214154224Z` succeeds, SHA256
`76712415ac6941b8de63fffe158e93a9d265df7b6fd6153d1b7442abafce4519`.
69 compile commands retain Cortex-A35/O3/wrap/noalias and add `-flto=2`;
ARM64 Linux PIE, unchanged glibc base, no build stderr. Full runtime suite
`20261114T024820879696Z`:165 tests,59 PASS/106 opt-in SKIP,123.219s.
Native GLES `20261114T024820890305Z-f38ddd`:27/27 PASS, all stages0.
Movement/collision/fire suite `20261114T024941997966Z`:3PASS/480.709s.
Matched native hospital `20261114T025135356723Z-1c1565`:29.68077FPS,
complete1s minimum21,5s minimum27.2,51 binary restores/no source misses.
No performance-win selection; native result does not improve prior floor.

## Adaptive timer follow-up, 2026-11-14

Hospital baseline110–111s shows repeated50ms producer frames with31–34ms CPU,
not a50ms CPU workload. Existing generated `sub_005F15E0_gen` chooses integer
refresh-tick synchronization through `0x72C7E8`, retaining prior simulation step
with60-frame hysteresis. `sub_0041B2C0` waits selected refresh ticks. This is a
candidate source of cadence feedback, not yet proven by an isolated experiment.
CCE omits relevant generated bodies and returns stale dump/cache matches;
exact functions reviewed directly in `recomp_0030.c` and `recomp_0003.c`.

Queries `site:github.com/cutarev/sh3-nx "30" "fps" timing`,
`site:github.com/ThirteenAG/WidescreenFixesPack "SH3" "FPS"`,
`site:portmaster.games "frame" "limiter"`, and
`site:github.com "Silent Hill 3" "20 fps"` find no specific PortMaster fix.
[SH3 proxy author's timer explanation](https://github.com/07151129/sh3proxy/wiki/On-FixJitter-and-lag-compensation)
describes divisors-of60 synchronization and lag compensation; its older unlock
lost correct speed, while later replacement retained measured elapsed time but
required animation fixes. [Sync source](https://github.com/07151129/sh3proxy/blob/master/src/sync.c)
replaces several routines and uses spinning. Windows injected x86 implementation
is research only: no patch/scripts copied or executed, no unlock or animation
rewrite selected. Preserve original speed, bounded elapsed compensation and
special clock modes if testing a focused pacing change later. Official
[PortMaster build guide](https://portmaster.games/contribute/porting/build-environments/)
still supports existing older-glibc ARM64 environment, not a new timer recipe.
SH3 proxy source HEAD verified with read-only remote refs:
`2b0070cd403cece844c3621a366f87b7713b6647`, relevant `src/sync.c`, `src/anim.c`
and `src/main.c`. No clone created.

Actual launcher/game RED `frame-budget-red` injects32ms only at external SDL
keyboard poll during48–61s. Room210 live throughout measured52–60s; each complete
second has exactly20 completed presentations.260 delayed polls, normal exit.
First candidate only caps adaptive wait mode at2 in explicit30FPS profile.
Build `20261114T025924275082Z` succeeds, but `frame-budget-green` fails20<25
again (64.722s); this is a failed candidate, not GREEN.

Original timer additionally requires at least one future refresh tick even when
requested ticks have already elapsed. Next focused candidate consumes overdue
ticks before that wait, retaining original absolute QPC target,60Hz division
remainder and cumulative/elapsed counters. Only explicit30FPS profile,normal
mode>=2,60Hz refresh,existing monotonic-nanosecond QPC are eligible; all other
paths and under-budget waits use generated body. Existing133ms simulation-step
bound remains. No audio/movie clock or floating-point change. Behavioral rerun,
independent600units/s movement/collision/fire checks and matched native hospital
comparison remain required; candidate has no performance verdict yet.

Catch-up build `20261114T031016810050Z` fails at compile: runtime has no `MEM64`
accessor. Corrected to paired existing `MEM32` accesses, matching QPC bridge.
This setup failure is not behavioral RED/GREEN evidence; rebuild pending.

Corrected build `20261114T031604763074Z` succeeds without build stderr;
runtime SHA256 `f972f0f1905d4cc1dc0a5257d0e3d8e070f55b9b6b58858875595c9a1b546e42`.
First `frame-budget-catchup-green` rerun improves complete seconds from20 to
24–27 but fails minimum25 (64.707s). Identical `frame-budget-catchup-repeat`
passes64.719s: windows52–59 contain25,26,27,26,25,26,25,26 presentations;
elapsed-span average25.74407FPS. First24FPS observation remains unresolved,
not discarded. Main CPU median2.79ms excludes injected32ms sleep; actual sleep
overshoot has not been measured, so do not assign remaining variation to host
jitter as fact. Native matched hospital and timing regressions now running.

Design review: consume exactly those refresh boundaries at/before current
monotonic time, retaining target plus division remainder; no per-call rounding
drift or independently reset clock. Existing cdecl return and callee-saved
registers retained; no floating-point operation added. Guarded fallback delegates
under-budget waits, other refresh/frequency and special modes to original body.
No refactor beyond shared profile/read/write helpers needed before regressions.

Matched native hospital `20261114T032756715409Z-f91bb2` holds same cache55 seed,
plan and all source hashes:48–160s29.981245FPS,min complete1s29/5s29.8,
p95/p99/max34.862/36.040/48.894ms. Old LTO floor21 no longer reproduced.
Heavy110–111s30 frames at33.270ms median CPU versus old22 at32.737ms CPU;
no reduced arithmetic-work claim.51 restores/zero misses,56 live observations,
44 positions. Game clock1.002926×wall/timer59.998728Hz;32 samples1512/520MHz,
max65.384°C. All statuses0/source preserved/frontend active. One ALSA recovery
in33.284–35.281s loading window; none in live48–160s. Independent movement
regression607.4903/605.0015units/s,ratio0.995903,passes600units/s baseline guard.
Completed movement/collision/fire suite `20261114T032945909488Z`:3PASS/480.823s.
Full runtime `20261114T034047067222Z`:166 tests,59 PASS/107 explicit opt-in SKIP,
123.204s.990s heavy hospital soak remains pending.

## Explicit performance entry, 2026-11-14

Keep existing ordinary launcher graphics persistence; provide explicit
`Silent Hill 3 Performance.sh` entry selecting30FPS/320×240 while delegating
to existing detached service, persistent progress,640×480 output and cleanup.
No ordinary-play keys or deadline. Other graphics options retained. Installer
protects unrelated same-name scripts.320/30 automated plans use installed entry.

Current [official packaging guide](https://portmaster.games/contribute/porting/packaging/)
allows distinct `.sh` menu names with spaces and port-local configuration.
Queries `site:portmaster.games contribute packaging port.json multiple launchers`,
`site:github.com/PortsMaster/PortMaster-New "Performance.sh"` and
`site:github.com/wild1walker/portmaster-cuphead "settings" performance launcher`
find no exact SH3 profile recipe. [Cuphead porter release notes](https://github.com/wild1walker/portmaster-cuphead/releases/tag/2026.10.29),
tag commit `c488ef66d046962d53ec7725fd48c046830968db`, describe persistent
`ports/cuphead/resolution.txt`/`aspect.txt` and GPU scaling on RK3326. Applicable
principle: explicitly chosen render scale with full screen output. Different
Unity Android runtime and firmware: no copied launcher/governor code and no SH3
compatibility/FPS inference. No reference clone or downloaded executable used.

`performance-entry-red` observes missing installed entry, exit127; GREEN0.247s
reaches runtime through service with30FPS/320render/640output, player slots intact,
other display options intact, no scripted keys/deadline, frontend active.
`performance-install-red` likewise observes missing device-installed entry;
GREEN0.493s invokes menu installed by saved deployment and reaches detached
runtime. Design review keeps four-line wrapper and existing lifecycle; no duplicate
save/session/service implementation. Full runtime `20261114T034435525800Z`:
168 tests,59 PASS/109 opt-in SKIP,123.202s. Separate owner-data frontend suite
`performance-frontend-regressions`:21PASS/5.660s, including both new behaviors.
Native entry run pending.

990s native hospital soak `20261114T033440437224Z-079c2d`,50–975s:
27,666 completions,29.909272FPS, complete1s minimum28/5s29.2;
p50/p95/p99/max33.339/34.741/36.562/52.629ms.461/461 observations alive,
316 distinct positions, room160 throughout.192 CPU/GPU samples all1512/520MHz,
maximum70.416°C. Clock0.9992187×wall, refresh59.999306Hz; observed elapsed2/3
ticks and simulation1/2/3. All statuses0/source preserved/ExitProcess0/frontend
active. Two live-gameplay ALSA recoveries,102.812–104.820s and558.339–560.353s.
Measured frame target passes this sustained checkpoint; no listening claim.

Desktop stress calibration: isolated debug observer `frame-budget-measured-run`
actually sleeps median36.0855ms/max41.876333ms for requested32ms, reproducing
24–27 completion windows. This supports excess test workload, not a discarded
FPS result. Keep original results. Repair test-only input delay by sleeping24ms,
then waiting against real monotonic deadline32ms; no guest clock change and no
production spin. Keep original minimum25 complete1s assertion and also verify
actual mean delay32–33ms.

Preserved pre-timer binary SHA76712415… `frame-budget-calibrated-red` fails
20FPS in every52–59s window; measured input mean32.000009/max32.002333ms.
Current candidate `frame-budget-calibrated-green` passes,28,29,29,29,28,29,29,29
completions, mean32.004172/max33.449375ms input delay. Same launcher/checkpoint/
resolution/workload; strict25 assertion unchanged. Identical repeat passes
29,29,28,29,29,29,28,29, input mean32.001605/max32.351083ms. Debug-only
copies stay under explicitly named ignored `frame-budget-measured-debug/`;
no debug trace added to production runtime.

Current artifact native GLES `20261114T035509898075Z-1ec2cf`:27/27 checks PASS,
including actual worker context, pixel/depth/stencil, textures, framebuffer,
samplers, resource lifetime and presentation; execution/collection stages0.


## Same-device program-cache priming, 2026-11-14

Current [upstream README](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md)
fully reviewed at exact HEAD `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`.
Reports first-visit shader stutter and persistent `sh3-progs.bin`; Switch runtime
and key-only cache differ from this GLES program-binary cache. Applicable lesson:
retain programs across launches, without copying Switch build/runtime commands.
[Khronos GLES3.2 section7.5](https://registry.khronos.org/OpenGL/specs/es/3.2/es_spec_3.2.pdf)
allows binary reuse, requires LINK_STATUS inspection and source fallback after
configuration/compiler changes. Local cache already checks complete GL fingerprint,
formats, exact source, record checksums and link status. No new shader semantics.

Queries `site:portmaster.games shader cache stutter`, `site:github.com PortMaster
Mali shader cache stutter`, `site:github.com sh3-nx prewarm shader` and
`site:github.com/cutarev/sh3-nx shader cache SD card` found no exact comparable SH3
PortMaster cache-priming recipe. Official packaging guide and Cuphead persistent
render-scale precedent above remain applicable only to launcher/config layout;
Android/Vulkan/Godot cache recipes do not establish Mali GLES compatibility.
No clone or downloaded executable used; external content treated as research data.

Selected narrow deployment: optional saved-host `--prime-program-cache` copies
only same-device measured `sh3-gl-cache.bin` into already-existing player state,
only when that cache is absent. Never import benchmark saves/settings or overwrite
existing player cache. Do not create state before first-import workflow. Retain
source/target SHA256 audit and runtime rejection fallback. This removes an otherwise
cold first ordinary launch for measured combinations; unknown scenes can still
compile new programs. Park warm run restores65/65 with zero source compiles but
still has214.823ms door frame, so cache priming does not claim to fix asset pauses.

TDD `performance-prime-red` fails absent ordinary-runtime cache; GREEN0.481s
reaches installed Performance entry with known programs and original player progress.
Safety regressions preserve existing cache and absent state. Owner-data frontend
suite `performance-cache-regressions`:24PASS/6.459s. `cache-deploy-red` rejects
unknown CLI flag; GREEN deploys only program cache without persistent/import state.
`cache-bounds-red` shows four malformed/oversized files reaching deployment;
GREEN rejects them before device access. Full host workflow fixtures
`cache-cli-regressions`:9PASS/5.329s, including failed-deployment collection.
Design review reuses existing installer/state/cache validation, with no runtime
binary change or second save lifecycle. Native prime verification pending.
