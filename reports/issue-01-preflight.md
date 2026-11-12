# Issue #1: Game data and target preflight

Date: 2026-11-12. Status: **preflight complete; publication and closure approved**.
[Issue #1](https://github.com/ktodorow/sh3-nx-r36s/issues/1) holds publication and closeout history.
Canonical scope: [spec](../docs/specs/silent-hill-3-r36s.md), AC01/02/03/13, G1.
Issue body and all comments read; no comments or blocking issues existed.

## Implemented changes

- Launcher: executable size/SHA-1, required-data inventory, player error message,
  PortMaster setup diagnostics, cleanup, separate preserved run logs/status.
- Data manifest: 79 nonempty paths observed in owner PC layout, including seven
  original movies. This is a presence/size check, not authoritative data-hash or
  campaign validation. No asset bytes included in repository changes.
- Saved host/device scripts: unattended SSH/SCP, current identity observations,
  source identity, per-run collection and separate deployment/execution/collection
  failures. Review installed helpers before sourcing; compare fresh hashes against
  reviewed inventory. Inventory and installed-launch failure now executed on R36S.
- Workflow guide and private example keys. Project-local `R36S_PORT` changed to
  `sh3`, selecting `/roms2/ports/sh3` rather than another game's folder.
- Thirteen launcher error/cleanup tests, including real ignored owner executable
  with deliberately absent assets; three assertions against actual device evidence.
  Existing untracked `.DS_Store` left alone.

No game runtime, GLES implementation, build environment, package installation,
firmware change, clock change, mount or original-asset conversion performed.
Owner approved publishing reviewed changes and closing issue #1 on 2026-11-12.
Issue history records verified task commit and completion handoff.

## Evidence and acceptance

| Check | Observed result | Limit |
| --- | --- | --- |
| Private-artifact exclusions | `.env`, owner data, temporary repos, builds, caches, dumps ignored; `.env.example` trackable | Connection settings stay local |
| Executable size | 3,338,240 bytes | Size alone insufficient |
| Executable SHA-1 | `d851669ef609b3164e3581aa8dcfbfaec866cb79` | Recognized exact owner-CD input profile after user requested this target; differs from upstream profile |
| Source-input preconditions | Nine upstream byte patches applied to ignored copy; PE/import parser accepts original, 242 imports, no TLS | Does not prove equivalence or native/runtime compatibility |
| Required-data presence | All 79 listed files present/nonempty; seven movies included | Data revision/integrity and media codecs unverified |
| Device attempt 1 | Prepare SSH status 255; execution not reached; collection 255 | No target fingerprint or deployment established |
| Device attempt 2 | Same failure before deployment | Historical failure; superseded by successful runs below |
| Current inventory | Execution 0; collection 0 | Current installed identities below; no active graphics-context claim |
| Installed preflight over SSH | Execution 2; both evidence collections 0; useful missing-data error | Original assets remain on host |
| Physical menu launch | Owner confirmed “Missing sh3.exe” displayed and Ports menu returned on 2026-11-12 | Missing-data/return case only; no game runtime launched |
| Launcher fixtures | Thirteen tests pass | Errors/cleanup only; no R36S gameplay claim |
| Syntax/review | Bash parsing, Python AST, whitespace/secret checks | No compiled runtime or gameplay acceptance |

Ignored local evidence:

- `r36s-dumps/sh3/20261112T132316408290Z-53c34d/`
- `r36s-dumps/sh3/20261112T132729077737Z-a3735f/`
- Each contains `status.json`, local inventory stdout/stderr and transport results.
  Second run adds base commit and source hashes. Original transport diagnostics
  exposed endpoint component despite destination redaction; fixed redactor and
  sanitized saved text logs. New run verifies endpoint components stay redacted.
- `.port-cache/issue-01-review.patch`: complete local task-owned diff.
- `.port-cache/issue-01-validation.txt`: final local checks.
- `r36s-dumps/sh3/20261112T133422024106Z-819536/`: first successful inventory.
- `r36s-dumps/sh3/20261112T133953611394Z-2fd0ed/`: additional installed helper
  dependencies collected for review.
- `r36s-dumps/sh3/20261112T134047911415Z-56395c/`: library identities collected
  after adding administrative paths for read-only `ldconfig -p`.
- `r36s-dumps/sh3/20261112T134345260296Z-dac52b/`: installed headless preflight,
  expected missing-data status 2, collection 0 including launcher logs. Frontend
  PIDs/states unchanged; port mounts empty before/after. All prior runs retained.
- `r36s-dumps/sh3/20261112T134727409519Z-c19bb0/`: latest profile-aware source;
  local owner-data validation 0, installed headless preflight 2 (device assets
  absent), execution collection 0 and launcher collection 0.
- `r36s-dumps/sh3/20261112T135427673754Z-5bde48/`: final inventory, execution 0
  and collection 0; preserves physical menu run
  `device/previous-launches/20261112T135209Z-74471/`, exit 2, expected missing-EXE
  message in separate data stderr. Owner confirmed visible message and return.
- `.port-cache/issue-01-executable.json`: PE/section fingerprints and nine patch
  precondition observations. `.port-cache/issue-01-executable/result.json`: patch
  copy result, parser observations, original integrity. Copy SHA-1
  `658d285fdf0f5f5764f7bd38166c3bef538bd45a`; original remains
  `d851669ef609b3164e3581aa8dcfbfaec866cb79`.
- `.port-cache/issue-01-owner-data.stdout.txt`: recognized owner profile and all
  79 original data paths; validator exit 0, stderr empty.

AC01 preflight now recognizes owner's exact input and reports incomplete data.
Input recognition does not establish generated-code or gameplay compatibility.
AC02 current-target fingerprint collected; native package remains future work.
AC03 installed headless failure/return recorded; owner physically confirmed
visible missing-executable error and return to Ports. AC13 remote execution and
collection demonstrated, including expected validation failure. **Issue #1
preflight acceptance recorded; G1 inputs/target handoff uses exact owner-CD
profile.** Full-port AC02/03/13 and G2–G6 remain unpassed. No dependent runtime
implementation performed. Owner approved publication and closure of reviewed
preflight task on 2026-11-12; capability limits above remain unchanged.

## Owner-CD input decision

User reports original-CD installation, no alternative executable, requests port
target this input. Previous instruction to obtain another EXE is superseded.
Canonical spec now records two exact input profiles; no arbitrary-hash bypass.

Replayed initial rejection: same-size executable failed upstream-only SHA-1 check
with exit 2. Ranked hypotheses before checking: different revision/code layout;
metadata-only difference; different startup code. Observed i386 PE, image base
`0x400000`, entry VA `0x662A6E`, `.text` at file/RVA `0x1000`, and all nine
upstream patch sites match. PE/import parser passes. These findings rule out
mismatches at those nine sites and gross parser/layout rejection. No known-good
upstream binary available for section comparison; root cause of hash difference
remains unknown. Do not claim metadata-only difference or game equivalence.

Reviewed original `tools/patch_exe.py` and `tools/pe2xbe.py` before running patcher
on ignored copy and calling parser functions. No XBE, Switch artifact, generated
C, native executable or library produced. Native code must be generated from
selected original and address-specific manual hooks checked during runtime work.
Launcher cannot run Windows x86 executable directly on AArch64 Linux. Supporting
additional versions means validated per-build profiles, signatures/layout checks,
regeneration and runtime tests. Nine matching patches cannot justify universal
automatic conversion of every unknown executable.

## Current target observations

Installed dArkOS `11072026`; Debian 13.6/trixie; AArch64; kernel 4.4.189
(`Wed Sep 2 04:42:52 EDT 2026`); glibc `2.41-12+deb13u3`; SDL package
`2.32.4+dfsg-1`. Memory total 916,912 kB, swap total 524,284 kB; not memory-fit
or performance acceptance. Physical controller identity: `GO-Super Gamepad`,
bus/vendor/product/version `0019/484b/1100/0100`, `js0/event2`.

Native EGL/GLESv2 links resolve to
`/usr/lib/aarch64-linux-gnu/libmali-bifrost-g31-rxp0-gbm.so`, ELF64 AArch64,
BuildID `b9c47d0da3e8a2153f0286f846c9bc69fb19ed34`, SHA-256
`2a067ea38256c3de139b2a5396d3101f7c7777b1e19d59017b2c02172500d0ea`.
Mesa EGL and ARMHF libraries also installed; their presence is not selected SH3
provider. Runtime context/driver version/extensions remain G3 work.

Resolved native SDL file is `libSDL2-2.0.so.0.3200.10`, BuildID
`e57eddc6d9f937a29f685a200d145a04e1fb9e36`, SHA-256
`f06e06daaf7681aece218f65fec74e351cc07e1ebf0e280b0d66d5de64241de7`.
Filename differs from package-reported version above; retain both identities.
Package metadata alone does not identify library that future runtime loads.

PortMaster `2026.06.23-0015`, device-info `0.1.15`; helper heuristically labels
hardware `RG351MP`. Device tree identifies R35S/R36S; do not treat helper label
as independent physical-model identification. Installed `get_controls` warns
missing `$HOME/.config/.OS`; data diagnostics remain separate and correct.
Reviewed collected control, device-info, funcs, dArkOS mod, dialog and mapper code
plus pugwash startup/entry path before preflight. No external helper changes made.

## TDD and validation scope

Confirmed public seam retained: installed PortMaster launcher → observable result
→ cleanup/return. Fixtures replace external filesystem and PortMaster helpers.
Tests do not import internal functions or stub hashing to manufacture valid data.

Observed RED before GREEN for missing executable, cleanup, run evidence,
wrong size, same-size wrong hash, missing original movie, controls failure,
partial helper-source failure and player message. Player-message follow-up first
reproduced helper warning masking actual data error, then isolated data diagnostics.
Refactor reviews after green retained behavior; validator extraction/formatting
reran suite green. Follow-up RED/GREEN cycles reproduced helper replacing exit
trap, broad helper cleanup affecting unrelated port, headless run opening GUI,
and owner-CD input rejected before missing assets. Minimal fixes preserve cleanup,
disable global gptokeyb kill for preflight (owns none), skip GUI only for saved SSH
run, and add exact input profile. Actual collected evidence checks first failed
for omitted helper dependencies and missing library identities, then passed after
collection extension and PATH correction. No fixture GPU/controller pass implied.
Physical-run collection first failed evidence check, then passed after inventory
included completed menu-run logs. Final check: 13 launcher tests and three checks
against real collected R36S evidence, all passing.

Documentation/research uses consistency and source checks; executable TDD does not
apply to prose. All executed tests/scripts interpreted; no executable, library or
test artifact compilation. Build guide/Docker environment not needed in this task.

## Research checked before approach

External content treated as research data. No downloaded commands executed.
CCE reference search returned role instructions in `SKILLS_PORTMASTER.md`; ignored
as external prompt-like text, not project authority. Another result included
directions for its own agent/session; those were also ignored.

| Source | Snapshot/path | Applicable finding |
| --- | --- | --- |
| [Official template](https://portmaster.games/contribute/porting/script-templates/) | Basic template, checked 2026-11-12 | Control discovery, mappings, `pm_finish`; no runtime/compositor needed for text preflight |
| [Official FAQ](https://portmaster.games/faq/) | Checked 2026-11-12 | Owner-supplied data and useful wrong-version diagnostics |
| [SH3 upstream](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md) | Current main still `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`; README | Upstream supports its exact hash; new owner-CD profile is this project's target, not upstream support claim |
| [Byte patcher](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/tools/patch_exe.py), [PE adapter](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/tools/pe2xbe.py), [generation pipeline](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/tools/regen.sh) | Same exact revision; complete files read, local patcher/adapter read before use | Validated nine sites and parser only; generation/manual addresses make arbitrary-version promise unjustified |
| [Official packaging](https://portmaster.games/contribute/porting/packaging/) | Current guide checked for owner-version question | First-run patching/error patterns; preserve originals rather than copying example deletion steps |
| [First-hand SH3 mod request](https://github.com/cutarev/sh3-nx/issues/8) | Full body/all comments read 2026-11-12 | Compatibility request and mod links, no verified alternate-EXE solution; not evidence this input unsupported |
| [SH2 lineage](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/README.md) | Existing spec-pinned revision | Separate owner data and Linux diagnostics; no SH3 input compatibility inference |
| [Cuphead launcher](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/pm/cuphead/Cuphead.sh) | Current main `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`; compared old spec pin `a2e39b5bc192e7bee2d2655a324355c0b9b994b7` | Discovery/cleanup precedent; Unity, 32-bit audio workaround and CPU changes not applied |
| [First-hand failed launch](https://github.com/DankMiimer/minecraft-bedrock-handheld-port/issues/10) | Body and all comments read 2026-11-12 | Stub `control.txt` can redirect `controlfolder`; distinguish helper/runtime failure from wrong data |
| [Delver evidence](../research_notes/Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md) | Historical `9083f5e9c23b63fdc67ae2ce4cbeb374692d10be` plus uncommitted work/log identities | Run ownership and identity precedent only; historical GLES/ABI not current SH3 proof |
| [dArkOS SSH FAQ](https://github.com/christianhaitian/dArkOS/wiki/Frequently-Asked-Questions) | Checked after connection failure | Remote Services may need enabling after reboot; no service/config changes made |

Local reference-guide comparison attempted through Porting Resources CCE:
`Porting.html`, `Packaging.html`, `Build Environments.html` returned previews;
`expand_chunk("Porting.html:1")` returned `Chunk not found.` Full textual comparison
unavailable; current official template used directly. No claim local guide obsolete.
No new reference clone created; no clone cleanup required.

Searches included `site:portmaster.games contribute porting script templates pm_finish`,
`site:github.com PortMaster R36S control.txt log problem`, upstream EXE hash,
exact local SHA-1, upstream SH3 executable/hash issues, and dArkOS SSH/Wi-Fi timeout.
Follow-up searched `PortMaster ldconfig command not found library`, official
PortMaster SDL/Mali guidance and current comparable launchers. No first-hand exact
same PATH diagnosis found; local repeated device observations establish correction.
No exact local-hash report or verified alternative input found. Search absence
does not prove incompatibility. Known metadata/layout/patch observations support
exact personal input profile; native behavior remains to be checked.

## Handoff

Use owner's existing CD input; no replacement requested. Physical menu error and
return confirmed by owner; review local diff and evidence. Subsequent
runtime work must generate game code from owner-CD profile and check manual
address hooks; it must not borrow generated code for upstream's other executable.
Runtime, graphics, media, performance and campaign gates remain unpassed.

Host workflow intentionally transfers no original assets. Full-data successful
preflight is local; installed device currently tests missing-data failure only.
Future deployment must preserve originals, verify available storage, and collect
successful installed-data preflight before claiming usable device installation.
Current workflow/collection proven for inventory and expected validation failures.

Owner approved publication and closure of reviewed preflight work. Closing issue
#1 records this preflight milestone, not playable game or Full-port acceptance.
