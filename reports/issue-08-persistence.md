# Issue #8 — saved progress and settings

Acceptance checks pass; owner approved publication and closure on2026-11-13.
[Issue #8](https://github.com/ktodorow/sh3-r36/issues/8)
implements AC10/AC13 and writable-state ownership from AC03 in
[canonical spec](../docs/specs/silent-hill-3-r36s.md). Renderer, timing, movies,
performance and final release integration remain outside this task.

Current result: owner confirms progress, selected rendering resolution and custom
Dash mapping survive handheld cold restart. Graphics reset reproduced and fixed;
desktop round trip, handheld exit/relaunch and device power cycle pass. Owner
accepts room/play-time identification on original Load screen; canonical spec and
local ticket updated accordingly. Final mapping inventory passes execution and
collection; new boot ID, matching key.ini and clean physical exits corroborate
owner observation.
Owner explicitly approved **"Publish and close #8"** after local diff, evidence,
validation and limits review. Issue records final task commit, completion handoff
and verified tracker state.

Earlier entries retain failures and pending checks as historical evidence;
summary and final closeout sections reflect completed acceptance.

| Acceptance | Result / evidence |
| --- | --- |
| State ownership and original preservation | Ordinary persistent state, isolated diagnostics, safe first-use import; source-integrity and unchanged-slot checks pass |
| Room-transition save and cold load | Owner resumes slot2 after door transition and power cycle; distinct boot IDs and unchanged slots in `20261113T113514792138Z-f66ef7` |
| Save identification | Original Load UI shows room/play time; owner explicitly accepts that identification on2026-11-13 |
| Graphics setting and cold restart | Rendering Resolution512×256 confirmed physically; boot-change and display-file checks in `20261113T143045824276Z-c07eb5` |
| Supported custom mapping and cold restart | Dash btn11 retained physically; matching pre/post-session key.ini, changed boot and clean exits in `20261113T144525123909Z-6ae691` |
| Safe write failure | Real game quicksave and native Options fault injection preserve prior valid files and report errors; actual ARM64 launcher tests pass |
| Regression | 50 ARM64 checks pass /51 explicit skips; 29 host checks pass /72 explicit skips; three actual-device runtime checks pass |

Evidence directories remain ignored/local; report retains run identities and
hashes without distributing owner data. Task does not establish full campaign,
all graphics-format choices, final resolution profiles, performance, or abrupt
power-loss-during-write durability. Final integration must recheck persistence
after later renderer/input changes. Current handheld Dash assignment is L3;
owner can restore X through Button Config. No runtime changes after final
ARM64 regression; subsequent edits document observations and accepted scope.

## Prerequisite and test boundary

Issue #5 is closed at `4de8b9370b79a4375c4589b45ac1301d7cfa2cb1`.
Four actual-device checkpoint/session/frontend evidence checks rerun successfully
against `r36s-dumps/sh3/20261112T214422283309Z-0f4c6c` before implementation.
These establish native gameplay, checkpoint loading/movement, 640×480 rendering
and frontend recovery. They do not establish #8 persistence.

Existing approved boundary remains installed PortMaster launcher → game session →
clean frontend return. Host fixtures cover lifecycle/error handling; real game
tests run in ARM64 Docker. Actual R36S save/load, previews and room transitions
still require device evidence. Original owner data mounts read-only in Docker.

## Ownership

- Ordinary game launches use port-local `state/`; game assets remain in `gamedata/`.
- `state/savedata/` owns game saves, game display preferences and supported mappings.
- `state/sh3.ini` owns native launcher preferences; defaults apply only when absent.
- `state/sh3-progs.bin` owns reusable program cache.
- `runs/<run-id>/` owns separate stdout, stderr, status and post-run state snapshots.
- Explicitly seeded or isolated diagnostics use disposable `runs/<run-id>/session/`.

No symlinks or bind mounts needed: native bridge already separates asset root
from writable working directory. Prior runs and original saves remain untouched.
Explicit first-use import copies all numbered slots, index, supported preferences
and cache into absent player state. Existing state blocks import. Host records
source hashes before deployment and checks them afterward. Diagnostic seed mode
never selects persistent player state. Inventory collects every numbered slot,
current state/cache and boot ID without changing sources.

## RED / GREEN / refactor evidence

| Behavior | Observed RED | GREEN and review |
| --- | --- | --- |
| Failed game followed by fresh launch keeps progress, mappings and settings; logs stay separate | `.port-cache/issue-08-state-red.txt`: second launch lost files and reset `cores=1` to `cores=3` | `.port-cache/issue-08-state-green.txt`: 21 launcher tests pass; state/snapshot ownership reviewed |
| Game exit retains valid display preferences | `.port-cache/runtime-tests/20261113T101720971196Z`: real game truncated `disp.ini` to zero bytes | Build `.port-cache/builds/20261113T101911368029Z`; `.port-cache/runtime-tests/20261113T101958657538Z`: 38 applicable checks pass, 55 explicit capability/evidence skips; staged display replacement reviewed |
| Failed quicksave preserves prior valid slot and reports write failure | `.port-cache/runtime-tests/20261113T102230208165Z/save-write-failure`: normal save created 9,952-byte `data.000`; kernel `RLIMIT_FSIZE=4096` failed overwrite left 4,096-byte fragment | Build `.port-cache/builds/20261113T102838931141Z`; `.port-cache/runtime-tests/20261113T102909794905Z`: all 39 applicable checks pass (55 explicit skips), original quicksave byte-for-byte intact and error logged; error propagation and staging reviewed |
| Unavailable save folder reports useful player error before starting game | `.port-cache/issue-08-state-error-red.txt`: raw mkdir error only | `.port-cache/issue-08-state-error-green.txt`: 22 launcher checks pass; error/cleanup path reviewed |
| First-use import retains all slots/preferences without changing originals or overwriting existing state | `.port-cache/issue-08-import-red.txt`: imported slots absent | `.port-cache/issue-08-import-green.txt` and `issue-08-import-refactor-green.txt`: 23 launcher checks pass, including refused second import |
| Saved physical workflow uses persistent player state instead of latest diagnostic seed | `.port-cache/issue-08-workflow-red.txt`: selected isolated diagnostic session | `.port-cache/issue-08-workflow-green.txt`: 46 applicable ARM64 checks pass, 51 explicit skips; service allowlist and frontend recovery reviewed |
| Inventory preserves all save slots/mappings and current state/cache | `.port-cache/issue-08-inventory-red.txt`: `data.000` absent from collected evidence | `.port-cache/issue-08-inventory-green.txt`: eight saved service/inventory checks pass; originals unchanged |
| Host persistent import stages only owned state and attempts collection after failed deployment | `.port-cache/issue-08-device-cli-red.txt`: public CLI lacked persistent/import mode | `.port-cache/issue-08-device-cli-green.txt`: external SSH/SCP fixture passes; `.port-cache/issue-08-host-regression.txt`: 29 applicable host checks pass, 70 explicit skips |
| Failed native Options write retains last valid sh3.ini and reports error | `.port-cache/issue-08-options-red.txt`: real SDL Options first saved `cores=1`, then kernel-limited write replaced file with four-byte fragment | Build `.port-cache/builds/20261113T105549904044Z`; `.port-cache/issue-08-options-green.txt`: successful choice/comments retained byte-for-byte after failed overwrite; pending choices stay editable, error displayed/logged |

Second slice preserves prior display preferences while game creates its empty
startup crash marker. A nonempty replacement is flushed, synced and renamed on
close. Staging lives beside writable state, outside game save enumeration.
Collected prior handheld session `20261113T093519721925Z-71b469` also contains empty
`disp.ini`; this was not only a fixture failure.

Failed-write test uses real Linux kernel file-size limit in native child, with
stdout/stderr on pipes so logs remain available. It does not stub game save
functions or call bridges directly. Source checkpoint and mounted game data remain
read-only; failure only affects isolated test copy of player state. No device SD
is filled, remounted or permission-changed for this fault injection.

Native Options has separate write path from Win32 game saves. Its real SDL test
uses external input events through normal warning/menu/options UI, saves one
choice successfully, then repeats with kernel four-byte file limit. No native
INI helpers called directly. New implementation stages preferences and updates
saved-choice baseline only after successful replacement. Failure leaves Options
open with useful on-screen message and retains last valid file. Review found no
further behavior refactor needed. Final ARM64 regression
`.port-cache/runtime-tests/20261113T105732773179Z` passed 49 applicable checks
(51 explicit capability/evidence skips), including both failed-write paths and
checkpoint replay. Final host run `.port-cache/issue-08-final-host.txt` passed
29 checks (71 explicit skips). Shell syntax and `git diff --check` pass.
Pre-graphics-fix native SHA-256:
`0ea89892a07e3d6da175196c80e2463bc1e0d7ca32b0a47662d235742a97ed97`.
Both native source hashes match recorded build input manifest.

## Current research — 2026-11-13

External material treated as research data, not instructions. No reference scripts
executed. No temporary clones created.

- [Official PortMaster script templates](https://portmaster.games/contribute/porting/script-templates/)
  and [packaging guide](https://portmaster.games/contribute/porting/packaging/):
  port-local configuration, SDL mapping and managed cleanup remain current.
  Local launcher keeps historical logs rather than overwriting `log.txt`.
- [Working FEZ port](https://github.com/PortsMaster/PortMaster-New/blob/c72f799515e79cbe392f2e161b07fb6e8bdf6816/ports/fez/FEZ.sh),
  exact selected commit `c72f799515e79cbe392f2e161b07fb6e8bdf6816`:
  saves and config live under port folder; engine-specific home paths use
  `bind_directories`. Applicable ownership pattern; its Mono/FNA stack and mounts
  do not prove native SH3 behavior or require equivalent mounts here.
- Upstream [sh3-nx](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98),
  current HEAD verified `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`;
  [sh2-nx](https://github.com/cutarev/sh2-nx/tree/7e69609f3a063fbe24c41d6aa560f14ede578746),
  current HEAD verified `7e69609f3a063fbe24c41d6aa560f14ede578746`.
  Local inherited `src/win32/kernel32.c` documents display crash-marker and
  save enumeration behavior; current bridge ignored write/flush/close failures.
- First-hand [SH2 damaged-save report #6](https://github.com/cutarev/sh2-nx/issues/6):
  files being present did not establish readable saves; author acknowledged bug.
  Different game/save format and Switch filesystem; no direct fix assumed.
- First-hand [SH2 settings report #11](https://github.com/cutarev/sh2-nx/issues/11):
  author distinguishes rewritten game settings from native-port settings.
  [Report #13](https://github.com/cutarev/sh2-nx/issues/13) also reports defaults
  returning at boot; thread does not establish a persistence fix. Read full bodies
  and comments; frame-rate discussion stays outside #8.
- Searches: `site:portmaster.games packaging save config bind directory save data script templates`,
  `site:github.com/cutarev/sh3-nx save data savedata write failure`,
  `site:github.com/cutarev/sh2-nx save file corrupt write failure`,
  `site:github.com/PortsMaster/PortMaster-New savedata save config bind_directories`.
  `gh issue list --repo cutarev/sh3-nx --state all --search save` found no issue.
  Cuphead/Delver CCE searches returned unrelated build/multiplayer previews;
  spec-linked [working patterns](../research_notes/Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md)
  retain their launcher/input/deployment findings. No unverified fix borrowed.
- Failed-write follow-up searches:
  `site:github.com/PortsMaster/PortMaster-New/issues save corrupt "space"` and
  `site:portmaster.games save "corrupt"` found no matching first-hand save failure.
  [Linux rename](https://man7.org/linux/man-pages/man2/rename.2.html) documents
  atomic replacement on same filesystem and prior target surviving failed rename;
  [Linux fsync](https://man7.org/linux/man-pages/man2/fsync.2.html) distinguishes
  file durability from directory-entry durability. Clean process restart and
  observed write failures are tested here; abrupt SD power-loss guarantees are
  not inferred from these calls.

CCE retrieval currently favors ignored build snapshots/device logs; expansion of
known launcher chunk returned `Chunk not found`. Known edit paths read directly
after that failure. No private `.env` values recorded in research or CCE.

## Device work and remaining acceptance

Saved host inventory `python3 scripts/host/r36s.py inventory` succeeded:
`r36s-dumps/sh3/20261113T101247031424Z-05c054`, execution 0, collection 0.
Target remains RK3326/AArch64, kernel 4.4.189, glibc 2.41, SDL 2.32.4 and firmware
Mali provider. Reused pinned Debian 12/glibc 2.36 ARM64 Docker image
`sh3-r36s-build:e6a3402e8f1b23bd` (`e3b41b2d5753`); no build environment changes.

Real-game failed overwrite, unavailable-state errors, safe first-use import and
diagnostic separation are covered by launcher/native checks above. Actual
handheld room-transition/save/preview/cold-load round trip, supported settings/
mappings, frontend recovery and original-data preservation remain pending.
No #8 device acceptance claimed yet.

Fresh inventory `r36s-dumps/sh3/20261113T104809102021Z-74f732` passed execution and
collection; complete PortMaster helper checksums match prior reviewed inventory.
Persistent physical run `20261113T105028135340Z-a42e0f` used latest completed
physical checkpoint `20261113T093519721925Z-71b469-launch/session` from that
inventory. Import completed on actual device; source hashes unchanged.
Owner reported **“I didnt played it”**. Run stayed at native launcher and reached
930-second service deadline: execution 1, service exit143, all three collections0.
Frontend restored active; no native process remained. This is timeout/recovery
evidence only, never manual exit or persistence acceptance. No save/preview/room/
setting/power-cycle observation recorded. Source sessions and all old device runs
remain preserved.

Latest Options-safe native build installed through saved runtime diagnostics:
`r36s-dumps/sh3/20261113T110712425811Z-44eb51`, execution0, collection0 and launcher
collection0. Deployed SHA-256 matches final local package above. Three actual
native runtime/dependency/firmware/lifecycle assertions pass in
`.port-cache/issue-08-device-runtime.txt`. Collected persistent data.001, data.sys,
disp.ini and sh3.ini match imported originals byte-for-byte. These establish
deployment/import and runtime regression only. Normal **Silent Hill 3 Game** Ports
entry is ready without test deadline; manual save/preview/room/settings/mappings,
power-cycle load and manual exit acceptance remain open. Issue stays open and
all task-owned changes remain local/uncommitted pending completed review.

### First manual save — before power cycle

Owner reports changing game graphics to 640×480 (16-bit), rendering resolution
described as “512x2…” (exact suffix not recalled), plus other graphics options;
crossing door/loading transition into another room; killing monster; saving slot2;
then closing through Select+Start. Owner did not observe scene thumbnail and is
unsure this version presents one. Thumbnail acceptance remains unverified rather
than inferred from save file existing.

Inventory `r36s-dumps/sh3/20261113T111610998168Z-31007a` passed execution0 and
collection0. Completed ordinary game run `20261113T111012Z-487158` exited0;
service exited0 and frontend restored active. Native log records physical
Select+Start and `ExitProcess(0)`; no native process remained. Persistent state
matches completed run snapshot. New data.002 is9,952 bytes, SHA-256
`69c00011442e934ea6727a1e4c7fea43f55203d1f87cb960f000137947051450`;
original slot1 remains byte-for-byte unchanged. Program cache is6,248 bytes.
Boot ID before power cycle: `f2cf068f-56b7-4ad9-b204-7fa20caf1927`.
Analysis/check results saved in inventory's `persistence-analysis.json`.

Graphics disp.ini remains empty and data.sys is unchanged. Owner subsequently
confirmed saved progression loads correctly after restart, but graphics changes
are lost. Progress and graphics preferences are independent acceptance checks;
saving progress is not a prerequisite for saving Options changes. Settings
acceptance fails and issue remains open. Supported remapping and actual thumbnail
behavior remain unverified.

First post-restart inventory `20261113T113028863617Z-2d6462` could not deploy or
collect: both connection attempts returned refused SSH connection (255). No
device result inferred from this failed collection. Owner reports device
reconnected; saved inventory workflow retried separately from desktop diagnosis.

Retry `r36s-dumps/sh3/20261113T113514792138Z-f66ef7` passed execution0 and
collection0. New boot ID `2eb35d1f-844c-494f-ac8e-c1a9d04ea997` differs from
pre-restart ID. Run `20261113T112654Z-12645` reads slot2, exits0 through physical
Select+Start, service exits0, frontend restored active. Slot1, slot2, data.sys,
sh3.ini and program cache match pre-restart hashes; disp.ini still empty.
Owner confirms correct saved progress loads, but game graphics choices reset.
Inventory's `persistence-analysis.json` records comparisons. Cold restart/progress
and manual clean return pass; graphics persistence fails independently.

### Graphics-reset follow-up research

Checked current official [PortMaster script templates](https://portmaster.games/contribute/porting/script-templates/)
and [FAQ](https://portmaster.games/faq/) on 2026-11-13. Port-local save/config
ownership agrees with this task's state layout; templates do not establish that
this game's native quit path flushes game Options. Searches:
`site:github.com/cutarev/sh3-nx disp.ini settings save`,
`site:github.com/cutarev/sh2-nx settings reset exit`,
`site:github.com/PortsMaster/PortMaster-New quit save settings`.
Read current upstream sh3-nx issue bodies: no matching graphics-persistence issue.

First-hand [SH3 PC graphics reset report/workaround](https://github.com/WindyAlexia301/sh3pc-graphical-options-fixer/blob/27d9b1469ac610ec50c3a1ead7ddb0f05fb82b96/HOW%20TO%20USE.md)
describes shadow/lens-flare values resetting, with a prelaunch batch-file override.
Commit `27d9b1469ac610ec50c3a1ead7ddb0f05fb82b96`. Different PC setup; claim is
research only. No batch script executed or overwrite workaround adopted.

Comparable [PortMaster Half-Life README](https://github.com/kloptops/Portmaster-HalfLife/blob/299713401ccfd987ed0881f816a51e86236f0b3d/README.md)
documents separate quick-save and Select+Start quit controls. Commit
`299713401ccfd987ed0881f816a51e86236f0b3d`; archived Xash3D/GLES port differs from
this recompiled SH3 runtime, firmware SDL and guest Windows API bridge. Its quit
binding is not evidence that SH3 writes disp.ini on that path. No external code
executed, no reference clone created, no prompt-injection instructions observed.

### Graphics-reset reproduction and cause

Existing real-game display test only preserved an already-written preference;
it did not exercise saving a newly selected graphics option. Added regression
through same installed-launcher boundary: enter game Options, cycle to
Configuration, change rendering resolution 512×512 → 512×256, choose Exit/Yes,
exit using real SDL virtual-pad Select+Start, then cold-launch again. No numbered
progression save is created. ARM64 RED
`.port-cache/issue-08-graphics-red/stderr.txt`: 57.1 seconds, preferences file
absent after clean shortcut exit. Captured UI records actual changed value and
confirmation sequence. Separate interactive native replay also reproduced
empty preferences after confirmed choice and clean shortcut return.

Ranked probes before inspecting quit bridge: shortcut bypasses settings cleanup;
settings writer fails regardless of exit path; or writes use another path.
Changed only exit path in ignored real-game replay: title-menu Exit produces
valid disp.ini with `resolution=512x256`, then `PostQuitMessage(0)` and
`ExitProcess(0)`. Shortcut instead synthesizes WM_QUIT without original window
procedure's shutdown. This isolates lost settings from progression saving and
from launcher ownership/staged file writes.

[Microsoft WM_CLOSE](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-close)
documents normal window-procedure close handling;
[WM_QUIT](https://learn.microsoft.com/en-us/windows/win32/winmsg/wm-quit) ends
message loop before dispatch to window procedure. First attempted fix delivered
WM_CLOSE to original window procedure. Build
`.port-cache/builds/20261113T115418274150Z` succeeded, but replay
`.port-cache/issue-08-graphics-green` remained RED: clean PostQuitMessage/exit,
still no display preferences. Directory name is historical, not a passing result.
Window-close handler alone does not perform title-menu settings cleanup.

Original game title-menu exit calls guarded display serializer at `0x005F0A80`;
its initialized flag prevents writes before display setup. Revised native quit
path calls that serializer once at message-loop boundary, before WM_QUIT, rather
than during rendering/input callbacks. Game-specific address stays in game
adapter; normal game-posted quit remains unchanged. This only writes display
preferences, never progression slots.

Revised build `.port-cache/builds/20261113T120321528860Z` succeeded, source hashes
match manifest. Final build records reused Linux ARM64 image
`sha256:9ba5ba966ebf84ab18220252b3bd72bd474d0a71f75411f9661c786ccba64777`
under recipe tag `sh3-r36s-build:e6a3402e8f1b23bd`; earlier build image identity
above describes those earlier runs. Native SHA-256:
`0984295e667b056a68f1ca92d3841c96f7e9ccd6655af937ed2cf31f4cc47fd0`.
`.port-cache/issue-08-graphics-serializer-green` passed original regression in
99.3 seconds: confirmed rendering choice persists after Select+Start and fresh
game process, with no numbered save created. Both run snapshots contain
`resolution=512x256`; visually reviewed cold-load Configuration capture
`game-graphics-options/reload/cold-options.png` displays 512×256. This verifies
actual Options round trip, rather than only preserving preseeded config.

Refactor review keeps game-specific serializer inside game adapter and invokes
it only for native close requests. Game-posted quit avoids duplicate writes after
original cleanup. Corrected test pad delay to account for five preceding phase
waits; default single-button/combo sequence remains unchanged. Full ARM64 run
`.port-cache/runtime-tests/20261113T121026508170Z`: 50 checks pass in439.1 seconds,
51 explicit skips. Covers new graphics round trip again after fixture refactor,
prior preferences, failed native Options write, failed quicksave retaining valid
slot, actual checkpoint replay, single-button/combo input, native diagnostics and
launcher cleanup. Host run `.port-cache/issue-08-host-graphics-fix.txt`: 29 checks
pass, 72 explicit skips. Shell syntax, local documentation links and diff checks
pass. No production debug instrumentation added; exploratory scripts/captures
remain clearly marked under ignored `.port-cache/debug-options/`.

Fresh inventory `r36s-dumps/sh3/20261113T121311302054Z-409d51` passed execution0
and collection0. All21 helper files match previously reviewed inventory, current
player state/cache unchanged, slot2 remains9,952 bytes with same hash, frontend
active and no native game process running. Analysis saved in inventory's
`persistence-analysis.json`.

Revised package deployed through saved runtime workflow:
`r36s-dumps/sh3/20261113T121759575701Z-4ba638`, execution0, collection0 and launcher
collection0. Collected native binary matches `0984295e…47fd0` above. Three actual
runtime/dependency/firmware/lifecycle checks pass in
`.port-cache/issue-08-graphics-device-runtime.txt`. Current player state/cache
matches predeployment inventory byte-for-byte; slot2 unchanged. Analysis saved
in deployment's `persistence-analysis.json`. Owner asked to change only Rendering
Resolution to512×256, choose Options Exit/Yes, Select+Start, relaunch and inspect
same value without saving progress. Physical graphics round trip and subsequent
cold-restart check remain pending; runtime deployment alone does not pass them.

### Load-screen observation

Inspected real game Load screen using isolated copies of collected slots1/2 and
data.sys in ARM64 Docker; no original save modified. Evidence:
`.port-cache/debug-options/preview-load-slot2.png`, accompanying run logs/captures
and `preview-load-slot2/source-preserved.json`. Slot2 selected: “2nd floor
storeroom”, play time9:38, Easy/Easy, Number of Saves5. Slot1 shows same location,
play time8:33, four saves. Both use same background artwork; tested Load screen
shows metadata rather than captured scene thumbnail. This supports owner's
observation and provides actual saved-state identification UI. Does not establish
a hidden preview elsewhere or satisfy canonical thumbnail wording by assumption;
record that acceptance gap explicitly rather than asking for nonexistent scene
image on this screen. This is observation only, no game/UI implementation change.

### Physical graphics exit/relaunch — passed

Owner confirms Rendering Resolution still shows512×256 after relaunch. Saved
inventory `r36s-dumps/sh3/20261113T141743722307Z-0884fd` passes execution0 and
collection0. Completed physical runs `20261113T141425Z-177590` and
`20261113T141624Z-179030` both exit0 through Select+Start, service exits0 and
frontend restores active. Second run reads existing disp.ini before startup
marker and writes nonempty preferences on exit. Persistent disp.ini is137 bytes,
contains `resolution=512x256`, SHA-256:
`87f4ad3c59903e0ba8d0ce893ffde625750394b3032a972d76b0cc9021306af0`.
Slots1/2, data.sys, native sh3.ini and cache match predeployment hashes. No native
process remains; frontend active. Independent analysis saved in inventory's
`persistence-analysis.json`.

Boot ID remains `2eb35d1f-844c-494f-ac8e-c1a9d04ea997`; this passes game-process
restart, not graphics after device power cycle. Pre-restart evidence collected
before asking owner to power off/on, reopen Configuration, check same value,
exit and leave Wi-Fi/SSH enabled. That physical result/collection remains pending.
This step changes evidence/report only; no new runtime behavior or TDD slice.
CCE session recall/decision recording returned `Transport closed`; current
observation retained here rather than assuming cross-session memory succeeded.

### Physical graphics power cycle — passed

Owner confirms Rendering Resolution still shows512×256 after handheld power
off/on. Saved inventory `r36s-dumps/sh3/20261113T143045824276Z-c07eb5` passes
execution0 and collection0. Boot ID changes from
`2eb35d1f-844c-494f-ac8e-c1a9d04ea997` to
`8047da67-43f8-451a-b89d-80ebcb867095`, establishing actual device restart.
Physical run `20261113T142644Z-6943` reads existing disp.ini, closes through
Select+Start, exits0 and restores frontend active; service exits0 and no native
process remains. Collected progress/preferences match completed session snapshot.
Inventory omits historical-session program cache; current cache comparison below
does not claim that unavailable historical copy was checked.

Display preferences retain `resolution=512x256` and SHA-256
`87f4ad3c59903e0ba8d0ce893ffde625750394b3032a972d76b0cc9021306af0`.
Slots1/2, data.sys, native sh3.ini and program cache remain byte-for-byte unchanged.
Inventory's `persistence-analysis.json` records11 passing evidence checks plus
owner observation. This passes graphics persistence independently of progression
saving. Supported custom remapping and original Load UI/thumbnail requirement
remain open; no additional runtime behavior changed in this evidence-only step.

### Supported mapping observation — desktop

Real game Button Config page2 supports changing Dash from btn01 to btn11 by
selecting Dash, confirming, then clicking virtual left stick. Choosing Exit/Yes
writes key.ini before Select+Start; fresh game process reads it and displays Dash
as btn11. Evidence: `.port-cache/debug-options/pad-button-map`,
`pad-button-reload.png`, accompanying logs and `mapping-observation.json`.
Serialized mapping is `dash=button10` (file uses zero-based button numbers);
key.ini SHA-256:
`dfc4f5942cd0c18d0b4ef456f3548c549cddfe7d1b735b81940102821ae20517`.
Reload probe ends through diagnostic deadline after UI capture, so this is
mapping-read/UI evidence only, not another physical-exit pass.
Separate `pad-button-page-check.png` confirms real SDL right-shoulder/R1 input
switches first Button Config page to page2 containing Dash. That UI-only probe
also ends at diagnostic deadline; it changes no mapping.

Probe uses installed launcher, real game and external SDL virtual controller in
reused Linux ARM64 Docker environment. Owner data remains read-only; mapping
change affects isolated state copy only. No production behavior changed and no
new bug reproduced; RED/GREEN implementation cycle does not apply to this
observation. Actual handheld custom mapping across power cycle remains pending.
Owner asked to assign Dash to L3, choose Exit/Yes, Select+Start, power off/on and
check btn11, then optionally restore Dash to X. Separately asked whether existing
room/play-time identification satisfies this task's thumbnail criterion; current
canonical wording remains unchanged until explicit answer. Issue #8 body and
all comments reread on2026-11-13: still open, no comments, original criteria intact.

### Physical custom mapping power cycle — passed

Owner confirms **"Dash still shows btn11 after power cycle"**. Saved inventory
`r36s-dumps/sh3/20261113T144525123909Z-6ae691` passes execution0 and collection0.
Boot ID changes from `8047da67-43f8-451a-b89d-80ebcb867095` to
`c307f753-d3de-42ed-9fa1-9100c4962446`. Owner's sequence establishes mapping
write before power off and observation after restart; no separate inventory was
collected between that write and power off.

Physical run `20261113T143941Z-51842` starts without key.ini, then writes it after
Button Config change. Subsequent run `20261113T144308Z-4374` reads existing
key.ini. Both snapshots and current player state contain identical713-byte file,
SHA-256 `dfc4f5942cd0c18d0b4ef456f3548c549cddfe7d1b735b81940102821ae20517`,
including `dash=button10` (displayed btn11). Both runs exit0 through physical
Select+Start, service exits0 and frontend restores active. No native process
remains. Slots1/2, data.sys, sh3.ini, disp.ini and current program cache remain
byte-for-byte unchanged from prior graphics-power-cycle inventory. Display still
contains `resolution=512x256`. Inventory's `persistence-analysis.json` records15
passing checks and owner observations. Handheld custom mapping acceptance passes.

### Accepted save identification and local closeout

Owner explicitly accepts **"room/play time identification"** for this task.
Canonical AC10 and selected local ticket now use save identification rather than
unconditional thumbnail wording. Tested original Load screen's fixed artwork and
room/play-time metadata supply that identification; preserve preview images
where original game provides them. No new save-preview UI implemented or claimed.
This resolves earlier recorded acceptance gap by explicit owner decision.

Only evidence/report/spec/workflow documentation changed after final native
regression, so no new runtime TDD slice or rebuild applies. Documentation links,
content consistency and diff checks validate this closeout. CCE recall and
decision recording still return `Transport closed`; decision retained locally.
Prepared review diff and publication/closeout drafts stay under ignored
`.port-cache/`. Owner's explicit **"Publish and close #8"** approval on2026-11-13
authorizes task-owned commit, push, completion handoff and issue closure through
repository issue-tracker workflow. Issue holds final commit and tracker state.
