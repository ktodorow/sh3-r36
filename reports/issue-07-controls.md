# Issue #7: physical R36S controls

Status: controls acceptance passes. Owner confirms checklist controls and
shooting work; paired actual R36S runs establish full input delivery and physical
Select+Start/frontend return. Owner approved publication and closure on
2026-11-13 after reviewing local diff, matrix/evidence and closeout draft. See
[issue #7](https://github.com/ktodorow/sh3-r36/issues/7) for final commit,
completion handoff and tracker state.

## Scope and prerequisite

Task: [issue #7](https://github.com/ktodorow/sh3-r36/issues/7), canonical
[spec](../docs/specs/silent-hill-3-r36s.md), AC09/AC03. Exercise normal gameplay
with handheld controls and orderly frontend return. Saved remapping persistence,
simulation speed, performance, campaign and suspend/resume remain separate gates.

Direct blocker #5 closed at `4de8b9370b79a4375c4589b45ac1301d7cfa2cb1`.
Its collected checkpoint movement, native game and detached frontend recovery
assertions rerun locally: four passes against
`r36s-dumps/sh3/20261112T214422283309Z-0f4c6c`.
Owner previously confirmed movement and physical Select+Start frontend return;
that evidence does not pass complete current controls matrix.

## Current hardware mapping

Saved `scripts/host/r36s.py inventory` run
`r36s-dumps/sh3/20261113T083359987001Z-649f59`: execution0, collection0.
Kernel identifies combined GO-Super Gamepad, vendor484b/product1100, SDL GUID
`190000004b4800000011000000010000`. Four stick axes; digital L2/R2 buttons6/7.
Installed PortMaster `gamecontrollerdb.txt` and EmulationStation controller config
now retained under `device/input-configs/` alongside `device/controllers.txt`.

Table combines collected mapping, upstream default actions and owner's completed
handheld checklist. Owner reports "Everything works. Controls work. I can shoot."
and "Buttons worked no problem" after printed-label checklist. No label mismatch
reported. Current database maps physical A/east to SDL A, B/south to SDL B,
X/north to SDL X, Y/west to SDL Y; no positional swap added.

| Physical control | SDL binding | Game default / physical check | Result |
| --- | --- | --- | --- |
| Left stick | axes0/1 → leftx/lefty | Movement in four directions; menu navigation | Pass: owner + full signed travel |
| Right stick | axes2/3 → rightx/righty | Camera/look in both directions | Pass: owner + follow-up full signed travel |
| D-pad | buttons8/9/10/11 → up/down/left/right | Movement and menu navigation, all directions | Pass: owner + all cardinal POVs |
| A / east | button1 → A | Action/examine, confirm; attack while ready | Pass: owner + button trace; shooting explicit |
| B / south | button0 → B | Flashlight toggle, cancel/back | Pass: owner checklist + button trace |
| X / north | button2 → X | Dash while moving | Pass: owner checklist + button trace |
| Y / west | button3 → Y | Map or correct unavailable-map response | Pass: owner checklist + button trace |
| L1 / R1 | buttons4/5 → shoulders | Strafe left/right under current control mode | Pass: owner checklist + both button traces |
| L2 | button6 → lefttrigger axis | Search view; released0/pressed32767; game threshold16000 | Pass: owner checklist + actual0/32767 |
| R2 | button7 → righttrigger axis | Ready weapon; R2+A attack; released0/pressed32767 | Pass: owner shooting + actual0/32767 |
| L3 click | button14 → leftstick | Default supply-use action where available | Pass: owner checklist + button trace |
| R3 click | button15 → rightstick | Zoom/look function where available | Pass: owner checklist + button trace |
| Start | button13 → start | Inventory; inventory navigation and weapon equip | Pass: owner checklist + button trace |
| Select | button12 → back | Pause/skip; alone must keep process running | Pass: owner checklist + continued game trace |
| Select+Start | back+start | Orderly game close; frontend active; no game PID/mount | Pass: actual follow-up physical exit |

Combat needs appropriate weapon and safe scene; supplies need available item.
No acquired map at room210 means unavailable-map response only, not acquired-map
screen coverage. Owner's blanket checklist confirmation does not establish an
acquired-map screen or healing consumption under a separately documented item/
health setup. Logs establish delivery, not those scene prerequisites. Owner
completed normal controls and shooting without keyboard input.

## Implementation and validation

Existing DirectInput bridge already exposes both sticks, POV d-pad and twelve
buttons, including trigger-axis threshold and stick clicks. No mapping override
justified by current evidence. `SH3_INPUT_LOG=1` adds applied-controller mapping
and changed input state to launcher stderr. State lists six SDL axes, hexadecimal
game button mask and POV; stick change detection quantized by4096 to limit jitter
logging. Diagnostic log is opt-in; ordinary launches avoid state logging.

Behavioral tests use agreed installed-launcher → game → frontend-return seam.
SDL virtual pad is external input boundary and runs only in ARM64 Docker. Fixture
has same four-axis/button-trigger layout as observed hardware, with unique
vendor/product GUID so SDL custom mapping applies. Anonymous virtual GUID first
kept automatic mapping; those fixture setup failures are not TDD RED evidence.

- Inventory RED: old actual inventory lacked current mapping directory; new saved
  inventory GREEN, one assertion passes. Refactor review: narrow explicit config
  copies; no device settings changed. Retained negative/positive checks in
  `.port-cache/issue-07-inventory-tests/{red,green}.txt`.
- Native trace RED: `.port-cache/runtime-tests/20261113T084321747335Z`, game exits
  successfully via fixture combo, but native applied-mapping trace absent.
- Build: `.port-cache/builds/20261113T084428633676Z`, status0, reused Debian12
  ARM64 image; generated-game cache reused; no Switch target.
- Native trace GREEN: `.port-cache/runtime-tests/20261113T084545619916Z`,
  35 passes/53 skips. Both button-trigger presses report32767 and game masks040/080;
  physical evidence still pending. Refactor review: trace opt-in; existing mapping,
  threshold and game data format unchanged. Ordinary-run trace guard added to
  existing regression cases.

- Detached-service RED: `.port-cache/runtime-tests/20261113T084703329996Z`,
  opt-in value missing inside runtime. GREEN:
  `.port-cache/runtime-tests/20261113T084756637027Z`, 36 passes/53 skips.
  Added one explicit allowlisted setting; existing frontend recovery unchanged.
- Physical-mode RED: `.port-cache/runtime-tests/20261113T084908509828Z`,
  scripted keys/capture inherited and diagnostic settings absent. GREEN:
  `.port-cache/runtime-tests/20261113T085028885332Z`, 37 passes/53 skips.
  Same installed menu now clears diagnostic input/capture and enables only input
  trace on explicit physical-mode request. Host stages marker and extends wait;
  device probe retains seed verification and always-attempt collection. Refactor
  review: shared launcher/service path retained; no separate controls menu.
- Actual run exposed a diagnostic detail: native `SH3_STATS` checks presence, so
  value0 still printed periodic FPS/heap lines. Stronger physical-mode test RED:
  `.port-cache/runtime-tests/20261113T093725719995Z`, one failure at inherited
  stats presence. GREEN: `.port-cache/runtime-tests/20261113T093855345106Z`,
  37 passes/54 skips. Physical mode now unsets stats; ordinary menu keeps default
  logging. Refactor review: same explicit environment boundary; no native input
  or timing change. Both physical runs used prior stats0 menu and retained FPS
  lines, but neither ran captures or external performance sampler. This final
  launcher-only correction verified in ARM64 Docker, not a third device run.
- Python AST and Bash syntax checks pass; CLI rejects physical mode outside game
  action or together with scene replay; `git diff --check` passes.

Documentation/report edits need no executable TDD; validate links and consistency.

## Research checked 2026-11-13

External references treated as research data; no downloaded helper executed.
No reference clone created. Source paths and applicability:

- [Official current PortMaster template](https://portmaster.games/contribute/porting/script-templates/):
  `get_controls` and explicit `SDL_GAMECONTROLLERCONFIG` remain current pattern.
  Native SH3 already follows it. Generic force-kill exit helper unnecessary because
  SH3 handles combo through orderly quit. Local HTML guide cache compared via CCE;
  redirects/previews insufficient, current official template read directly.
- [sh3-nx README](https://github.com/cutarev/sh3-nx/blob/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/README.md):
  current HEAD `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`, controls and
  `src/win32/dinput.c` default actions supply expected matrix; Switch-specific
  A/B swap cannot be transferred to Linux.
- [sh2-nx README](https://github.com/cutarev/sh2-nx/blob/7e69609f3a063fbe24c41d6aa560f14ede578746/README.md):
  HEAD `7e69609f3a063fbe24c41d6aa560f14ede578746`; related native SDL design,
  but trigger actions differ. Not copied as SH3 game-action evidence.
- [Cuphead launcher](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/pm/cuphead/Cuphead.sh):
  current HEAD `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`, explicit SDL mapping
  export matches current official template. Its Android/Unity bridge, 32-bit
  audio workaround and helper exit do not prove native SH3 inputs.
- Delver reference at `9083f5e9c23b63fdc67ae2ce4cbeb374692d10be`:
  CCE again returned multiplayer Java input and unrelated cache instead of
  untracked R36S launcher. No Delver input fix reused. Prior measured cleanup
  method remains in [working-port notes](../research_notes/Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md).
- [First-hand R36S programmer](https://github.com/dov/r36s-programming/blob/6049a6798c3ea8715f3a4dd6aa11ebec5254484f/README.md):
  raw buttons0–13 and four axes match this handheld inventory. Author does not
  establish this port's physical behavior or stick-click acceptance.
- [R36S button-swap utility](https://github.com/Max904/R36S-Button-Swap/tree/c0996c49b735e1a2f334966188daad7b30b7ee3c):
  reports firmware/PortMaster convention differences; no system-wide swap run.
- [R36S mainline mapper](https://github.com/Trijal08/r36s-mapper/tree/94f379f6fea7fc3fb9aa981b6da06b469fbf61fe):
  split GPIO/ADC input problem differs from current combined controller/kernel4.4;
  no mapper daemon added.
- [SDL2 source, release2.26.5](https://github.com/libsdl-org/SDL/blob/ac13ca9ab691e13e8eebe9684740ddcb0d716203/src/joystick/SDL_gamecontroller.c):
  button-to-trigger mapping yields0/32767 and respects mapping database;
  matching Docker version used for fixture. Firmware SDL retained on handheld;
  separate actual mapping/input traces collected in runs below.
- [SDL GUID information](https://wiki.libsdl.org/SDL2/SDL_GetJoystickGUIDInfo)
  and pinned [joystick source](https://github.com/libsdl-org/SDL/blob/ac13ca9ab691e13e8eebe9684740ddcb0d716203/src/joystick/SDL_joystick.c):
  GUID bytes2/3 carry CRC separately from bus/vendor/product/version. Actual
  firmware emitted `1900bb3e4b4800000011000000010000`, while ES/installed database
  used zero CRC. Applied bindings identical. Evidence check now allows only CRC
  variation and still checks controller name, hardware identity and trigger
  bindings; no runtime mapping workaround. First-hand SDL report
  [#6898](https://github.com/libsdl-org/SDL/issues/6898) also reproduces version-
  dependent CRC formats on different hardware; not this port's acceptance.

Searches included official PortMaster SDL/trigger guides, sh3/sh2 controls,
R36S digital-trigger reports and comparable native ports. No first-hand same-SH3
R36S trigger failure found. CCE reference guide hit included role-setting text
(`SKILLS_PORTMASTER.md`); ignored as untrusted instructions. Local CCE returned
cache-heavy previews and failed full-source expansion; known intended edit paths
read directly after retrieval failure. No private paths/config indexed.

## Physical run and handoff

Native log button mask: X001, A002, B004, Y008, L1010, R1020, L2040,
R2080, Select100, Start200, L3400, R3800. POV: neutral−1, up0, right9000,
down18000, left27000, diagonals4500/13500/22500/31500. Axes order:
leftx,lefty,rightx,righty,lefttrigger,righttrigger. Trigger values describe
SDL normalization, not physical analog travel; L2/R2 are digital buttons.

Prepared command (run only when owner ready for handheld actions):

```sh
python3 scripts/host/r36s.py game --physical-controls --reviewed-helpers r36s-dumps/sh3/20261113T083359987001Z-649f59
```

This invokes saved host/device workflow and installed game menu. No keyboard
injection, screenshots or sampling; latest successful checkpoint copied into
fresh session, existing save/config unchanged. Applied service settings retained
in `service/physical-controls.txt`, input trace in `launcher/stderr.txt`.
Physical A advances warning and Play; choose Load and checkpoint via controller.
Check matrix actions, then Select+Start. Owner must confirm actual printed-button
conventions, action effects and frontend return. Game deadline900s and service
limit930s bound unattended session; deadline/service-stop exit cannot pass AC09.

Owner confirmed readiness on 2026-11-13. First run started at09:14:53UTC:
`r36s-dumps/sh3/20261113T091453037985Z-706034`. All execution/collection stages0;
3588 game-read states cover all twelve buttons, left-stick full travel, both
digital triggers0/32767 and every d-pad direction. Right-stick positive travel
absent from this trace; close cause explicitly probe deadline900s, so this run
alone fails complete physical input/exit evidence. Owner confirms controls and
shooting work and frontend return. Native averages are diagnostic observations,
not accepted gameplay-speed/performance benchmark.

Owner approved short follow-up at09:35:19UTC:
`r36s-dumps/sh3/20261113T093519721925Z-71b469`. Execution/collection stages0;
193 states include right X−32768..32494 and right Y−32768..32767. Native log:
`window close requested: Select+Start`, then `ExitProcess(0)`. Launcher/service
exit0, frontend `ActiveState=active`, no native PID or leftover port mount;
firmware library hashes and source checkpoint checks unchanged. Both runs use
runtime SHA-256 `2f7bcba35231d7d3070642455025613c49492374323648a1499034249265ff82`,
matching built `dist/runtime/sh3`. No keyboard injection, screenshots or sampler.

New `InputSessionEvidenceTests` validates complete physical input set and physical
exit from actual saved runs only. Multiple paths use platform path separator;
every run must have same runtime hash, correct mapping and complete cleanup, and
final run must demonstrate physical Select+Start. Negative control rejects prior scripted #5 run
at mode check (`.port-cache/issue-07-session-evidence-negative.txt`); this is
evidence validation, not a new native implementation TDD cycle. First physical
run intentionally fails on missing right-stick positive travel and deadline exit
(`.port-cache/issue-07-first-physical-evidence.txt`). Paired actual input/inventory/
frontend checks pass3 tests (`.port-cache/issue-07-physical-evidence.txt`):

```sh
SH3_INPUT_SESSION_EVIDENCE=r36s-dumps/sh3/20261113T091453037985Z-706034:r36s-dumps/sh3/20261113T093519721925Z-71b469 SH3_INPUT_INVENTORY=r36s-dumps/sh3/20261113T093519721925Z-71b469 SH3_GAME_SERVICE_EVIDENCE=r36s-dumps/sh3/20261113T093519721925Z-71b469 PYTHONPATH=tests python3 -m unittest test_input_evidence test_game_evidence.FrontendSessionEvidenceTests -v
```

Owner reports FPS initially fine, with severe drops in mall/store area. Retained
as concrete scene for [issue #9](https://github.com/ktodorow/sh3-r36/issues/9)
and later performance profiling; no timing/audio/performance fix attempted here.
No quantitative performance acceptance, remapping persistence, acquired-map/
healing-item setup, campaign or suspend/resume pass implied. Task #7 normal
handheld controls and physical exit acceptance covered by owner checklist plus
paired current hardware traces. Ordinary menu remains usable without opt-in run.
Owner's explicit "Publish and close #7" approval authorizes task-owned commit,
push, completion handoff and closure through repository issue-tracker workflow.

Local review artifacts: `.port-cache/issue-07-local.diff`, prepared issue body
`.port-cache/issue-07-issue-body.md`, completion/handoff comment
`.port-cache/issue-07-closeout.md`. Closeout fills commit placeholders after commit
and verifies remote contains task commit before posting handoff and closing issue.
Credentials, owner data, builds, caches and raw dumps remain local/ignored.
