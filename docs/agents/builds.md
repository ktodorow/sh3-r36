# Native ARM64 build workflow

Read before build work, environment changes or build cleanup. Native diagnostics
target recorded dArkOS glibc 2.41/kernel 4.4.189, Linux AArch64.

## Environment and inputs

Inspect existing Docker images/containers first; reuse compatible project image.
All compilation and executable tests run with explicit `--platform linux/arm64`.
Use lightweight Debian 12 slim (glibc 2.36, older than target 2.41), pinned image
digest and dated Debian snapshot; record installed package versions and compiler.
Keep Cortex-A35-compatible code, `-fwrapv`, `-fno-strict-aliasing`.
No Switch targets, toolchains or packages. Existing PE-to-XBE step is recompiler
analysis data only, never built or deployed as console executable.

Host script orchestrates Docker; container generates C and compiles native Linux
target. Owner data mounts read-only. Check exact supported executable profile and
data first; preserve original hash. Generated C must derive from selected input.
Pin Python generation dependency; record input/profile, source hashes, image ID,
package versions, generated manifest and resulting artifact hashes.

Use repo `build/` for disposable intermediates and `dist/` for final personal
artifacts. Both ignored. Evidence stays under `.port-cache/` and `r36s-dumps/`.
Check private-artifact ignore coverage before creating these paths.

## ABI and device checks

Inspect ELF64/AArch64 machine, interpreter, DT_NEEDED and symbol versions. Resolve
complete dependency closure on target, recording actual loaded files/hashes.
Keep any required private libraries port-local; retain firmware SDL/EGL/GLES and
graphics provider initially. Linking alone does not pass G2.

Run diagnostics through installed launcher and saved host/device workflow in
[scripts guide](../../scripts/README.md). Check actual guest reservation/commit,
threads, pause/resume signals, crash handler and monotonic timer behavior without
rendering. Record virtual versus resident memory separately. Fixture results
cover launcher failures/cleanup only; actual R36S execution required.

## Cleanup

Provide one project-scoped cleanup command. Remove only disposable project-owned
containers, unused build intermediates and optional unused project image/cache.
Never global Docker prune. Preserve source, owner data, final `dist/` artifacts,
device evidence and existing resources belonging to other projects. Check resolved
paths remain within repo before removal. No shared builder cache deletion.

Commands: `python3 scripts/host/build.py`, then
`python3 scripts/host/test-runtime.py`; device command in scripts guide. Avoid
parallel builds/deployments. Source snapshot read-only; writable mounts restricted
to build intermediates, generated C and run-owned artifact directory. Private
configuration never enters source snapshot. Only selected original EXE mounts,
read-only; hash checked again after build.

Compiler comparisons use `python3 scripts/host/build.py --optimization O3`.
Only O2/O3 accepted; default remains O2. Selected level recorded in build identity
and passed explicitly to CMake RelWithDebInfo flags. Keep Cortex-A35, wrap/alias
and floating-point semantics unchanged; no fast-math option. Verified generation
cache remains shared because optimization level does not change generated source.
Compare actual compile commands, ELF size, launcher/pixel checks and matched
device profiles before retaining variant. Rebuild with `--optimization O2` to
restore baseline; preserve each build's artifacts and evidence.

Pinned base: `debian@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc`.
Main and security snapshot: `20261111T000000Z`; generator wheel: Capstone 5.0.6.
Image tag derives from Dockerfile SHA-256. Existing matching Linux ARM64 image
reused. Installed package versions, compiler, Python dependencies, base commit,
source hashes, selected input hash and generation key recorded per build.
Generation reused only after complete generated-file manifest check.
Source snapshot timestamps follow content hashes from last successful compile,
not original file dates. Changed files get fresh timestamps; unchanged files
retain prior snapshot dates for Ninja reuse. Invalidate this record before
compilation so failed/interrupted builds cannot poison a later source revert.
Saved `source-inputs.json` records actual snapshot hashes/times. Optional host
regression `SH3_REAL_BUILD_TESTS=1 PYTHONPATH=tests python3 -m unittest test_build_cli`
builds/runs a tiny native ARM64 fixture through same Docker CLI and checks stale
mtime plus failed-build recovery; does not establish game/device compatibility.

Graphics builds also extract selected shaders/declarations, original quad and
render-target dimension tables
from recognized owner executable using `scripts/build/shader-samples.py`.
Private header stays in ignored `build/arm64/generated/`; native binary embeds
samples for personal device tests. Source generation cache remains separately
verified. No original game data or extracted samples belong in Git or public
artifacts. Firmware SDL/EGL/Mali remains device provider; Docker Mesa supplies
desktop comparison only, never hardware acceptance.

`python3 scripts/host/clean-build.py` clears `build/`, including generation and
compile caches. `--docker` also removes stopped labelled containers and unused
labelled `sh3-r36s-build` images, without force. Active project container or
unavailable Docker blocks cleanup. No project volume or dedicated builder exists;
shared Docker layer cache intentionally preserved. `.port-cache/builds/` retains
build evidence and package copies; `dist/` retains current and prior final
packages, including host-only debug symbols. Generated C under `src/recomp/gen/`
is preserved as source. No cleanup run deletes device history.

Optional LTO comparison: `python3 scripts/host/build.py --optimization O3 --lto`.
Default remains non-LTO; omit `--lto` to restore it. Build identity records both
choices even if image setup fails. Native script passes `-flto=2` at compile
and link, limiting linker compiler workers to2; no `-flto=auto`, fast-math,
whole-program assumption or floating-point change. Wrap/alias options repeated
at link. Explicit empty LTO flag clears cached CMake settings when disabled.
Production-script ARM64 fixture checks real LTO object sections, runnable
signed-wrap example and successful ON→OFF rebuild; it does not prove game speed.
Follow [GCC12 LTO requirements](https://gcc.gnu.org/onlinedocs/gcc-12.2.0/gcc/Optimize-Options.html#index-flto).
