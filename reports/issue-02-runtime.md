# Issue #2 — native Linux ARM64 runtime diagnostics

Task: https://github.com/ktodorow/sh3-r36/issues/2. Owner approved publication and
closure on 2026-11-12; final commit and tracker state recorded in issue history.
G1 prerequisite: closed #1, commit `89101a1f5345a3f09fb59bc347c89eb48ef243e6`.
Scope: reproducible personal native build and real R36S runtime diagnostics;
renderer, FMVs, audio, gameplay and 30 FPS remain later gates. Linking alone
does not pass G2. Original game data stays ignored and original executable stays
unchanged.

## Inputs and build

Owner-CD profile `owner-cd-d851669e`, 3,338,240 bytes, SHA-1
`d851669ef609b3164e3581aa8dcfbfaec866cb79`. Nine upstream patch preconditions
passed in #1. Generation uses this input, not alternate upstream executable.
Owner-profile/manual-hook equivalence and gameplay remain unproven.

Reusable Debian 12 slim ARM64 image, base digest
`sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc`;
Debian main and security snapshots `20261111T000000Z`, Capstone 5.0.6.
Explicit `--platform linux/arm64`; Cortex-A35 code; retained `-fwrapv` and
`-fno-strict-aliasing`. No Switch toolchain or Switch build target invoked.
Intermediate PE-to-XBE file serves recompiler analysis only.

Initial image build failed because main-only snapshot did not supply matching
security package versions. Matching dated `debian-security` snapshot fixed apt
dependency resolution. This was build setup failure, not target capability result.

Clean generation/build after actual cleanup:
`.port-cache/builds/20261112T144505185617Z/`; final cached repeat with current host
source identity: `.port-cache/builds/20261112T145412135265Z/`. Both status 0, same
stripped binary SHA-256
`259379c9a1c1a566b624d8fe64dec49609efcc4dcc1fa7f3fb4ee1052fa3e614`.
Repeat reused byte-verified generation and required no compile. This establishes
clean build plus stable cached packaging, not two independent clean-build byte
reproducibility. Actual image ID
`sha256:b3b941549d2434078ebe086bffd41b125b536c76be35fa0b5ce323653e82e7a7`.
Original executable SHA-1 unchanged after both builds. Source hashes, complete
generated manifest, generation summary/logs, compile commands, package/compiler
versions, ELF metadata and artifact hashes retained per build.

## Research checked 2026-11-12

External sources treated as untrusted data; no downloaded shell instructions
sourced. Search returned external PortMaster `AGENTS.md`; its agent instructions
were ignored and did not change project scope or authorization.

* [Official build guide](https://portmaster.games/contribute/porting/build-environments/):
  Ubuntu 22.04/glibc 2.35 standard, older glibc required for older firmware.
  Debian 12/glibc 2.36 chosen for this recorded dArkOS/glibc 2.41 target only;
  no broad ArkOS compatibility claim.
* [Official native script template](https://portmaster.games/contribute/porting/script-templates/):
  control discovery, controller mapping, platform helper and finish patterns.
* [Debian Snapshot](https://snapshot.debian.org/): separate main/security archive
  snapshots and expired metadata handling. Applied to observed apt failure.
* [sh3-nx host layer](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/runtime/host.c),
  current commit `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`: Linux 4 GiB
  `mmap` reservation, `mprotect` commits, pthread/wake pipe and SIGUSR2,
  per-thread alternate signal stacks. Existing host layer retained for direct
  measurement. Upstream Linux source does not prove this kernel passes.
* [sh2-nx host layer](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/src/runtime/host.c),
  current commit `7e69609f3a063fbe24c41d6aa560f14ede578746`: same Linux arena,
  pthread and signal patterns; comparable design, no imported success claim.
* [Current Cuphead launcher](https://github.com/PortsMaster/PortMaster-New/blob/40186ea1e5d64db3df91cf4ed2437deffc6f50cd/ports/cuphead/Cuphead.sh),
  repository commit `40186ea1e5d64db3df91cf4ed2437deffc6f50cd`: controller
  export/platform helper/finish; its 32-bit Unity/audio workaround does not apply
  to native AArch64 runtime diagnostics. Cuphead reference repository current
  commit `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`.
* Delver reference findings remain in spec-linked
  [working patterns](../research_notes/Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md).
  Current `PortMaster-New/ports/delver/Delver.sh` returned 404; recursive current
  tree contained no Delver shell script. No unavailable current script assumed.

Searches: `site:github.com PortMaster aarch64 mmap signal thread issue`,
`site:github.com/cutarev/sh3-nx Linux arm64 compile`,
`site:github.com/PortsMaster/PortMaster-New AARCH64 SDL2 CMake`,
`site:github.com "PortMaster" "mmap" "Cannot allocate memory"`,
PortMaster apt unmet dependencies, SH2 signal/pthread reports. No first-hand
report matching SH3 ARM64 runtime found. Unrelated 39-bit address-space report
was not used as a fix. Actual target evidence must decide this capability.

Menu-folder blocker searches repeated: `site:github.com "PortMaster" "No such
file" "GAMEDIR"` and `site:github.com/PortsMaster/PortMaster-New "dirname"
"GAMEDIR"`. Official template and pinned Cuphead launcher above explicitly set
game folder. [First-hand RHH report #79](https://github.com/JeodC/RHH-Ports/issues/79)
describes return-to-menu after extraction on Knulli and dArkOS, with different
engines and an illegal-instruction log; it does not establish this wrapper's
cause or supply an applicable fix. No exact SH3 wrapper report found. Local
installed-menu regression establishes root cause and fix.

CCE used before code exploration. `expand_chunk` returned “Chunk not found” for
known source chunks, so known edit files and pinned upstream sources reviewed
directly. No temporary reference clone created.

## Validation and remaining evidence

Launcher fixture RED/GREEN cycles: missing runtime returns 3 with useful error;
native process failure preserves status/stderr, saves and frontend return.
16 launcher fixtures pass. Fixtures do not prove hardware compatibility.

Fresh scripted inventory: `r36s-dumps/sh3/20261112T141417407491Z-e99177/`.
Installed PortMaster helper hashes match reviewed #1 inventory exactly.
Baseline actual native run:
`r36s-dumps/sh3/20261112T142532527136Z-3752c6/`. Unsupported diagnostic flag
reproduced exit 139, matching Docker RED. Execution failed; both collections
succeeded. Frontend PIDs preserved. This failure did not pass G2.

Memory/thread run: `r36s-dumps/sh3/20261112T143737931933Z-a7892d/`, execution
and collection 0. All-four run:
`r36s-dumps/sh3/20261112T144133563249Z-4939f4/`, execution and collection 0.
Three actual-evidence assertions pass: full diagnostics/closure, virtual/resident
observations, unchanged firmware and no leftover process/mount. Owner reported
normal frontend return, but inventory `20261112T144747866274Z-0cbba6` collected
physical run `20261112T144615Z-284463` as missing-data preflight (exit 2), not native
diagnostics. This observation alone does not prove native menu success.

Review also found runtime wrapper relied on host-supplied `SH3_PORT_ROOT`; direct
menu launch resolved nested launcher folder incorrectly. Installed-menu fixture
without host environment reproduced exit 3 (RED). Explicit package root derived
from top-level menu location fixes it; all 16 launcher fixtures GREEN. Minimal
wrapper reviewed after GREEN. Corrected final scripted deployment:
`r36s-dumps/sh3/20261112T145428930351Z-3b8d27/`, local validation, deployment,
execution and both collections all 0.

Final physical menu run `20261112T145735Z-326811`, collected by saved inventory
`r36s-dumps/sh3/20261112T145759741979Z-0bd864/`: all four native checks PASS,
`runtime=PASS rendering=untested`, exit 0. Owner confirmed brief black screen
then normal frontend return after selecting Runtime Diagnostics; earlier accidental
Delver launch is unrelated. Physical diagnostics virtual/resident/peak:
4,337,080 / 26,696 / 26,696 KiB. Logs distinguish this successful native run from
earlier missing-data preflight runs. No graphics are expected in this diagnostic.

Final scripted target observations:

| Observation | Actual result |
| --- | --- |
| Baseline virtual / reserved virtual | 48,220 / 4,242,524 KiB |
| Baseline RSS / reserved RSS | 1,688 / 1,688 KiB |
| RSS after touching committed arena pages | 10,560 KiB |
| Completed diagnostics virtual / resident / process peak resident | 4,337,080 / 26,672 / 26,672 KiB |
| Arena / committed bytes | 4,294,967,296 / 8,392,704 |
| Highest tested guest word | `0xFFFFFFFC`, correct write/read |
| Guard faults / alternate stack | 2 expected faults handled, correct address and active alternate stack |
| Guest threads | isolated registers/TIB/stack; 16 resume-before-pause and 16 external SIGUSR2 pause/resume cycles |
| Win32 timer bridges | frequency 1,000,000,000 Hz; requested 25 ms sleep measured 25,234 us; both millisecond counters advanced 25 ms |
| Binary / loader | ELF64 little-endian AArch64 PIE / `/lib/ld-linux-aarch64.so.1` |
| Required GLIBC maximum | `GLIBC_2.34`, below installed 2.41 |

Target complete ELF dependency closure resolves firmware SDL2, libsamplerate,
libm, libc and AArch64 loader. All inspected ELF libraries AArch64; no missing
dependency, no port-private library required. No SDL/GL/EGL/GLES/driver library
bundled or replaced. Before/after installed library checksums all OK. Installed
PortMaster emits existing missing `.OS` warning; diagnostic result remains 0.

Actual scoped cleanup: `.port-cache/issue-02-cleanup-check.json`; removed disposable
build tree, preserved all 1,403 checked source/config/final/evidence files byte for
byte. Default cleanup retained reusable image. Docker cleanup option tested with
external Docker fixture; no shared layer cache or other project's resources pruned.

Runtime launcher RED/GREEN evidence under `.port-cache/runtime-tests/`:
`20261112T142502455120Z` unsupported flag RED;
`20261112T143053617474Z` memory GREEN;
`20261112T143131107960Z` thread RED;
`20261112T143656781040Z` thread GREEN;
`20261112T143736722548Z` signal RED;
`20261112T143818957730Z` signal GREEN;
`20261112T143913354737Z` timer RED;
`20261112T144100753466Z` timer GREEN;
`20261112T144436212279Z` completed-session resident/peak measurement RED;
`20261112T145353593271Z` completed-session measurement GREEN (22 Docker checks
pass, nine host-data/device checks intentionally skipped).
Each slice reviewed after GREEN; fixture reuse extracted and unused import removed
without changing launcher behavior. Additional build/cleanup CLI seam explicitly
confirmed by owner. Its REDs: missing failed-build input identity; absent cleanup
CLI; optional cleanup left owned resources behind. Three CLI tests subsequently
GREEN. No TDD claim for initial Dockerfile bring-up; actual image/build failures
and clean rebuild validate that environment. Documentation-only changes use
content/link/whitespace checks, not executable TDD.

Final validation: `.port-cache/issue-02-validation/`. Host suite with actual native,
physical-menu and installed-target evidence: 26 pass, five ARM64-executable tests
skipped on host. Docker suite above: 22 pass, nine owner-data/device tests skipped.
All 31 distinct tests pass across these runs. Shell/Python syntax, local doc links,
diff whitespace and ignore checks pass; no private/generated artifacts tracked.
Local review diff including 13 new files:
`.port-cache/issue-02-review.patch` (21 task-owned files total). Owner explicitly
approved publishing reviewed changes and closing task #2 after these checks.

## Limits and next task

Generated 11,977 of 11,981 detected functions, four manual exclusions, zero failed
translations; 307 unresolved call targets stubbed. Generation report also lists
76 unimplemented instruction kinds across 2,731 reported sites; reachability and
correct handling are unverified. Original game code linked from
selected input; diagnostics do not execute gameplay or prove manual hooks and
stubs correct. Preserved semantic compiler flags. No original assets deployed.
Diagnostics' touched RSS is not full-game footprint or peak. Final session/peak
measurements must be read separately. No GPU context or renderer exercised; G3
and later acceptance remain open. Task #3 needs actual game-derived GLES samples,
hardware renderer identity and independently checked output.
