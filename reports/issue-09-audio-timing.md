# Issue 9 — gameplay speed and audio

Implementation and representative acceptance reviewed. Owner approved publication
and closure of issue #9 on 2026-11-14. Final commit, evidence links and verified
tracker state are recorded in issue completion comment; issues #13/#14 stay open.
Canonical scope: [Silent Hill 3 R36S spec](../docs/specs/silent-hill-3-r36s.md),
AC08/AC11, [issue 9](https://github.com/ktodorow/sh3-nx-r36s/issues/9).
Movement, combat, animation, timers and gameplay audio; original movie timing
and final performance/profile acceptance remain later tasks.

Performance follow-up,2026-11-14: this report preserves original issue9 evidence,
not current FPS. Later renderer/30FPS timer work reaches29.97–29.99FPS in five
sampled moving/combat scenes; current artifact, sustained checks and explicit
first-visit/audio limits live in [issue13 report](issue-13-performance.md) and
[issue14 report](issue-14-renderer-caches.md). Original listening observations
below do not establish fresh listening acceptance for later binaries.

## Review result

Inherited three-tick simulation clamp caused measured slow motion. Native fix
preserves elapsed60Hz ticks within133ms bound during normal slow frames; original
special/unlocked policy retained. Audio, guest-thread affinity/scheduling,
allocator quarantine and future movie clock unchanged.

| Check | Result | Evidence below |
| --- | --- | --- |
| Movement | RED42.5% speed → GREEN100.4%; actual R36S595/610 units/s versus600 baseline | Paired Docker and both device profiles |
| Collision/timer | Stable wall contact; endpoints1.108 units apart; clock within0.4% of wall |320×240 delayed-presentation regression |
| Combat/animation |3 handgun shots in each3s window; ammunition remains, no reload |640×480 paired real-input case |
| Gameplay audio | Owner accepts shooting/movement/sound at640 and dialogue/audio/movement at320 | Two900s handheld sessions, representative mall transitions |
| Underrun follow-up | One initial640-load ALSA recovery; none during320 session or repeat640 load | Original event retained; no reproducible guest audio fault or scheduling change |
| Lifecycle/profile | Both internal profiles,640×480 output, source preservation, clean exits/frontend return | Device logs and actual-evidence assertion |

At original issue9 completion,30FPS performance did **not** pass: heavy room
remained near10–12FPS. Lower resolution improved several other scenes; later
optimization evidence is linked above. Representative cases do not establish every weapon,
scene or voice-clip repetition count. Stalls beyond133ms remain bounded rather
than fully caught up. Owner requests no repeat of already accepted Select+Start.

## Prerequisite and test boundary

Issue 5 capability rechecked from actual owner-device evidence, not its closed
status: three checkpoint/frontend assertions pass against
`r36s-dumps/sh3/20261112T214422283309Z-0f4c6c` on 2026-11-13.
Existing confirmed test boundary remains installed PortMaster launcher → real
game session → clean frontend return. Read-only guest counters supplement actual
input and checkpoint observations. No new test boundary introduced.

CCE recall consulted. Context searches returned unrelated cache/generated
snippets; expansion returned missing chunks, and scoped reindex indexed zero
files. Known timing, mixer, launcher and test files therefore reviewed directly.
Private configuration/data/build/cache/dump ignore coverage verified before runs.

## RED: repeatable speed defect

Saved command:

```sh
python3 scripts/host/test-movement.py --seed r36s-dumps/sh3/20261112T210505273186Z-e9a7a2/device/previous-launches/20261112T204903Z-230962/session
```

2026-11-13 evidence: `.port-cache/movement-tests/20261113T150044353995Z`.
Existing native artifact SHA-256:
`0984295e667b056a68f1ca92d3841c96f7e9ccd6655af937ed2cf31f4cc47fd0`.
Paired launcher/load/input run takes 132.760 seconds. Test observes same room210,
starting X/Z and health, four-second movement input, completed-input guard and
exit0. External SDL swap wrapper adds67ms only after checkpoint setup; no
screenshots, guest clock writes or shortened input.

Reference599.9967 units/s; delayed254.9868 units/s; ratio0.4249803.
Assertion fails on movement speed, not setup. Slow samples report elapsed7,
simulation step3, timer mode3; timer total remains60 ticks per wall second.

Ranked hypotheses shown before probe: dropped simulation ticks; timer bridge
loses wall time; scripted input ends early. Completed input and clock counters
support first. Generated original `sub_005F15E0` clamps normal adaptive step at3;
`sub_0060DA50` publishes integer/float animation delta. Frame timer
`sub_0041B2C0` accounts elapsed ticks independently. Update/render work interleaves;
repeating whole updates would also repeat input edges and draw work.

First candidate keeps original adaptive/special-mode policy, but normal slow
frames consume actual elapsed ticks up to8 (133ms). Larger stalls remain bounded.
At this stage candidate still required movement/collision/combat/animation and
device tests; later sections record results. It does not pass30FPS performance. Audio
rate, guest-thread scheduling, allocator quarantine and movie clock unchanged.

## Candidate build

Saved `python3 scripts/host/build.py` passes in explicit Linux ARM64 Docker.
Evidence `.port-cache/builds/20261113T150941748283Z`; selected owner input SHA-1
`d851669ef609b3164e3581aa8dcfbfaec866cb79` preserved. Artifact SHA-256
`f23cf5750d13c5e52eab05d8d151fc76287d105b9fa438ab6cd0512305bb185b`;
ELF64/AArch64, interpreter `/lib/ld-linux-aarch64.so.1`, stripped, separate host
debug symbols. Recipe unchanged. Helper refreshed image tag from cached layers
after initial inspect failed; resulting image ID
`sha256:d26fee9c901e7c80dd8e3cbe30ad30aa2433bc282fe23bc75dc87aaddc82d108`.
No Switch toolchain or output used. Full generated-file manifest retained.

Movement GREEN: same saved command, evidence
`.port-cache/movement-tests/20261113T151835325372Z`,132.672s.
Reference594.9961 units/s; delayed597.5044 units/s; ratio1.0042157, within agreed
10% tolerance. Both checkpoint/input guards and exit0 pass. Normal reference
still uses two-tick updates. Review found no useful structural refactor in
13-line wrapper; original generated body and guest calling convention retained.
At this stage only measured movement passed; larger-step regressions follow below.

## Diagnostic scene correction

Before handheld measurement, launcher fixture reproduced two harness defects:
requested320×240 plan became640×480, and `capture_every=0` still enabled capture.
Initial test setup omitted parent directory creation and errored; corrected
setup then produced valid assertion RED in
`.port-cache/issue-09-checks/timing-scene-valid-red`. Partial device-script fix
exposed primary launcher's640-only whitelist (return3); final minimal correction
allows both spec profiles, retains640×480 output, and disables capture explicitly.
GREEN `.port-cache/issue-09-checks/timing-scene-green-2`; refactor restores required
scene fields while defaulting only optional profile. Nine frontend/launcher
regressions pass in `timing-scene-regression`. Source seed and frontend recovery
assertions remain green. New900-second handheld plans keep real pad input and
read-only clocks, with isolated saves and no framebuffer capture.

Native regression before this scene correction:
`.port-cache/runtime-tests/20261113T152120542053Z`,174.754s,101 total,49 pass,
52 explicit evidence-dependent skips. Includes desktop GLES/reference, input,
save-failure, runtime/thread/timer and launcher checks. Skips do not pass hardware
or listening acceptance. Subsequent nine frontend checks cover launcher changes.

Fresh device inventory `r36s-dumps/sh3/20261113T153021291646Z-b82d5f` executes
and collects successfully. Current helpers checked against previously reviewed
inventory before deployment; persistent player state copied locally, not changed.

Expanded Docker regression in
`.port-cache/movement-tests/20261113T152936239827Z` reconfirms640×480 movement:
602.4966 versus595.0092 units/s, ratio0.9875728. Collision and repeated-fire
cases fail setup guards, not established game defects: sparse PEEK samples miss
five-second contact window; offscreen SDL suppresses virtual-pad events without
background-input hint. Same collision endpoints differ by1.2 units. Contact
input/window extended; fixture adopts existing game-input test's
`SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS=1`, also documented by
[official SDL2 guide](https://wiki.libsdl.org/SDL2/SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS).
No production input/mixer/scheduling changes from these setup failures. Later
fixture review removes virtual pad entirely: existing scripted keyboard suffices
through same real launcher/game boundary; original swap-delay helper restored.
First selective rerun fails Docker nested-file mount setup (exit125); second
copies already-built external fixture with recorded hash, no new compilation.

R36S640 timing run `r36s-dumps/sh3/20261113T153402195172Z-62d223`:
execution/collection/service/launcher collection all0, seed preserved, actual
640×480 internal/output, no capture, clean ExitProcess0 and frontend restored.
Same room210/player start; four-second movement595.0097 units/s against600
baseline; game clock1.000744× wall time. Gameplay samples8.1–10.1FPS; no30FPS
performance acceptance claimed. PEEK shows simulation steps6–7 rather than
inherited3 cap. Readouts occur at different update phases, so individual elapsed
and step samples need not match each other. Timer, displacement and complete
input establish behavior independently of exact sampled-step equality.

R36S320 run `r36s-dumps/sh3/20261113T153756765133Z-36d407` also exits/collects0,
preserves same seed and runtime identity, and restores frontend. Actual320×240
internal/640×480 drawable verified;610.0054 units/s, game clock1.000350× wall;
gameplay samples9.7–11.9FPS. Both independent60Hz timer rates measured60.0000.
`SH3_TIMING_EVIDENCE` paired actual-evidence assertion passes via
`tests/test_timing_evidence.py`; per-run `timing-analysis.json` retains samples
and metrics. Both profiles meet10% movement and5% game-clock tolerances for
this case. No capture, firmware changes or source writes; this remains first
checkpoint timing evidence, not full-game or final performance acceptance.

Selective regression rerun
`.port-cache/movement-tests/20261113T153827856027Z-regression`: collision and
settled game timer pass at320×240. Input remains held through80s; multiple sparse
samples establish stable wall contact before release. Final endpoints differ by
1.108 units, both health100/room210. Reference game-clock rate0.998184;
delayed0.996852, both within5% of wall time. No collision tunneling observed in
this case; other collision geometry/enemy interactions remain handheld checks.
Repeated-fire setup guard failed here: SDL trace confirmed ready/attack
buttons delivered at requested times, but observed ammunition unchanged. No
cadence verdict at this stage; later inventory probes establish weapon setup. Owner
available for handheld checks;640 profile started with explicit isolated seed.

Explicit scene deadlines originally bounded only game after Play, leaving launcher
wait unbounded. Added launcher-seam test: valid RED
`.port-cache/issue-09-checks/launcher-deadline-red` (missing RuntimeMaxSec930),
GREEN `launcher-deadline-green`, then10 frontend checks pass in
`launcher-deadline-regression`. Existing physical-mode930 policy now derives from
explicit positive integer game deadline plus30s, including diagnostic scenes;
ordinary launches have no deadline. Review removes duplicated physical-only
assignment; regression remains green. First640 listening session had already
started with previous launcher; subsequent deployments receive bound.

640×480 listening session `r36s-dumps/sh3/20261113T154503981772Z-4bc8f9`
executes/collects0, preserves source state and restores active frontend with no
native leftovers. Read-only samples show actual640×480 and seven visited rooms
(11–17). It ends by900-second probe deadline, not proven physical exit. Owner reports shooting, movement and sound fine, but severe lag near large
mall monsters and asks whether final exit was crash. Log ends with explicit
900-second deadline and ExitProcess0: clean diagnostic exit, not recorded crash.
Speech and specific playback observations were still pending at this stage;
later owner feedback completes representative listening check. Room visits alone
do not pass audio acceptance. Local `listening-analysis.json` retains samples.
Stats vary by room: room11 median19.9FPS (15.2–21.2), room14 median11.1FPS
(9.3–19.9), room17 median14.35FPS (13.2–18.1). UI/cutscene samples may inflate
other room medians, so these are diagnostic readouts, not matched performance
acceptance. Owner monster-room identification is not yet mapped to room ID.

This uses current persistent mall checkpoint, distinct from fixed room210
movement checkpoint. Both listening profiles use same explicit source copy.

Initial combat UI probes under `.port-cache/issue-09-combat-ui*` and
`.port-cache/issue-09-combat-keys` showed melee attack and inventory; later
probes9–12 establish firearm selection and Equip flow. These use framebuffer dumps and are setup diagnostics, never
performance evidence. Keyboard controls checked against upstream README and
[game control reference](https://www.silenthillmemories.net/sh3/playing_the_game_en.htm);
weapon selection remains through actual inventory input, with no guest writes.

One ALSA `snd_pcm_recover` underrun appears during640 session's initial save
loading, between timer142.2s/room0 and149.9s/room12; following elapsed sample138
ticks spans load stall. No later underrun in this900-second log; owner reports
sound fine. This is observed backend recovery, not yet a reproduced audible
loop/race or diagnosis. Second profile and repeat-load results follow below.

Fresh blocker searches: official PortMaster SDL2/ALSA underrun guidance;
PortMaster comparable-port ALSA underrun; upstream SH3 native audio. Official
[FNA guide](https://portmaster.games/contribute/porting/engines/fna/) search result
concerns FAudio/default-device detection; full page unavailable through web tool.
Reviewed Cuphead launcher already documents ARMHF/old-kernel route, different ABI.
[Unity toolkit runtime](https://github.com/Producdevity/portmaster-unity-toolkit/blob/main/docs/runtime.md)
search describes ARMv7 Android/FMOD queue; not this native AArch64 SDL mixer.
Neither pattern transferred. [SDL first-hand issue539](https://github.com/libsdl-org/sdl2-compat/issues/539)
reports startup-only and sustained underruns with SDL2-compat/ALSA, different SDL
implementation; full issue/comments reviewed, no fix copied.
[ALSA PCM reference](https://www.alsa-project.org/alsa-doc/alsa-lib/pcm.html)
identifies playback underrun as stream starvation and recoverable XRUN. Exact
cause on R36S remains unverified; no affinity, scheduling or buffer-size change.

Combat setup rerun `.port-cache/movement-tests/20261113T161341355071Z-regression`
still rejects0 shots (156.768s). Inventory probe sequence now confirms Weapons
category, handgun selection and Equip submenu. First Return opens action list,
second confirms; explicit inventory close required before ready/fire. Probe
images/logs remain under `.port-cache/issue-09-combat-ui-9` through`-12`.
Current case uses only real scripted keyboard actions, three-second firing
window, nonempty-magazine/no-reload guards and one-round comparison tolerance.
No cadence claim from earlier invalid setup runs.

320×240 listening run `r36s-dumps/sh3/20261113T160212510154Z-5665ee`
also executes/collects0, preserves same source/runtime identity, uses actual
320×240 internal/640×480 drawable and restores frontend with no leftover runtime.
321 active observations span rooms11–17,20,21,23. No logged ALSA underrun across
900 seconds; end again explicit native probe deadline/ExitProcess0. Owner reports
noticeably smoother rendering, but heavy mall rooms and some maps still lag;
spoken dialogue smoother, audio and movement fine. Both profiles traverse shared
mall rooms, with repeated movement/effects and dialogue in owner playthroughs.
No owner report of looping/crackle/drift. Individual voice clip repetition count
not recorded; final physical Select+Start not repeated in these timed runs.

320 diagnostic room medians: room11=19.9FPS, room13=29.4FPS, room14=11.75FPS,
room17=21.1FPS. Lower resolution improves several visited scenes but leaves
heavy room14 near10–12FPS. Paths/actions and UI/cutscene time differ between
runs, so medians are not matched optimization benchmark or30FPS acceptance.
`listening-analysis.json` retains player/room/ammunition/rate and FPS samples.
Short additional640 load run reuses saved automated plan with explicit current
mall checkpoint; it checks underrun recurrence only, not room210 movement case.

Combat/animation regression GREEN:
`.port-cache/movement-tests/20261113T161722991869Z-regression`,156.727s.
Explicit inventory close completes setup. Reference and delayed runs each fire
three handgun rounds in three-second held-action window, retaining seven in
magazine and30 reserve; no reload or SMG consumption. Same room210, live health,
completed-input and clean exits pass. Delayed gameplay samples8.7–9.7FPS; firing
cadence matches reference despite delayed presentation. This is
representative handgun animation/cadence evidence, not all weapons/enemy AI.
Review retains shared launcher/checkpoint helper; no useful production refactor
needed after green. Removed temporary virtual-pad implementation from host
helper, restoring original SDL swap-only fixture.

Owner additionally confirms dialogue actually heard and both listening runs
ended by timer. Owner states Select+Start works and requests no repeat of that
already accepted control test; retain existing issue7 acceptance. No further
physical-exit test needed for this task.

## Current source research

External sources treated as untrusted research; no fetched code executed.

- [Official PortMaster native launcher template](https://portmaster.games/contribute/porting/script-templates/):
  control directory discovery, input mapping, platform helper and cleanup remain
  applicable. No game simulation timing prescription.
- [Official build environments](https://portmaster.games/contribute/porting/build-environments/):
  current general recommendation differs from project's pinned Debian12. Existing
  Linux ARM64/glibc2.36 image remains older than recorded target glibc2.41; no new
  image or sysroot warranted for this change.
- [sh3-nx](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98),
  HEAD `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`, README and existing local source:
  native runtime baseline; Switch core-affinity workaround cannot establish
  Linux audio correctness.
- [sh2-nx](https://github.com/cutarev/sh2-nx/tree/7e69609f3a063fbe24c41d6aa560f14ede578746),
  HEAD `7e69609f3a063fbe24c41d6aa560f14ede578746`: separate movie timing remains
  applicable architecture guidance; no gameplay timing patch copied.
- [Cuphead launcher](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/pm/cuphead/Cuphead.sh),
  HEAD `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`: lifecycle/input patterns reviewed.
  Its pre5.6-kernel ARMHF ALSA pipe workaround belongs to different runtime/ABI;
  not transferred to native AArch64 SH3.
- [Working-port notes](../research_notes/Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md):
  Delver reference includes local uncommitted implementation beyond pinned HEAD;
  its working status does not prove SH3 scheduling or audio acceptance.
- [First-hand SH3 low-FPS reports](https://github.com/ThirteenAG/WidescreenFixesPack/issues/285):
  full body and26 comments reviewed. Slow motion under fluctuating performance
  reported on Windows. Different runtime; motivates repeatable speed test only.
- [SH3 Enhanced timing source](https://github.com/amiraliuks/silent-hill-3-enhanced/blob/297ab43fd95365b10190be6e15e67b61faec4e0d/src/patches/frame_rate.cpp),
  HEAD `297ab43fd95365b10190be6e15e67b61faec4e0d`: 60FPS mode changes wait-count
  adjustment; 30FPS mode forces nonzero limiter mode2 while preserving unlocked
  mode0. Windows x86 hooks are not native Linux fix; neither removes measured
  simulation clamp by itself.
- [Rebirth](https://github.com/IvanBarbosaFilho/Silent-Hill-3-Rebirth/tree/4fd3f0717a288373e096edd66d401e8f557a5ee3),
  HEAD `4fd3f0717a288373e096edd66d401e8f557a5ee3`: repository tree contains README
  and notices only, so advertised clock changes cannot be source-audited here.
- [SH3 memory research](https://github.com/Polymega/SilentHillDatabase/blob/154cc94e6ea596b0fed2d9754b450fb738f21724/SH3/SH3%20PC%20memory%20addresses),
  revision `154cc94e6ea596b0fed2d9754b450fb738f21724`: full address list reviewed.
  Documented player position/health, game-time and ammunition observations can
  supplement real input; no test writes these fields.

Searches: PortMaster performance/audio SDL2; sh3-nx audio race/looping Linux;
sh2-nx FPS/speed; SH3 5F1940/5F6760 simulation. No first-hand same-game native
R36S audio-race report found. Unrelated HD-console/emulator reports discarded.
No temporary reference clones created.

## Final validation

Repeat640 load `r36s-dumps/sh3/20261113T161952466156Z-e4bb4d` executes and
collects0, reaches live mall room12, reports actual Mali GLES/640×480, preserves
all input hashes, exits0 and restores frontend with no native leftovers. No
underrun in this100-second saved-scene run. Initial640 event therefore did not
recur in either follow-up; cause and audible impact remain unverified. Do not
claim event never happened or copy unrelated scheduling workaround.

Final launcher regression:10 checks pass in2.043s,
`.port-cache/issue-09-checks/reviewed-launcher-regression`. Actual paired timing
assertion rerun passes; scene JSON, changed Python syntax, shell syntax and
`git diff --check` pass. Documentation-only evidence/guide edits validated by
source/diff review; no executable behavior to test separately.

## Remaining limits and handoff

Movement, wall collision, settled timers and repeated handgun cadence pass
recorded cases. Actual R36S movement/game clock pass both internal profiles;
owner accepts representative gameplay sound and320 spoken dialogue. One
initial-load ALSA recovery did not repeat in two follow-ups; no bounded
scheduling or allocator changes justified. Keep this evidence for future
regressions. Individual voice-clip repetition counts, every weapon/enemy and
all scenes remain untested. Owner confirms existing physical exit works and
requests no retest. Both timed sessions end by native deadline, with clean
frontend recovery. Final30FPS performance and movie-clock acceptance remain
later tasks, not passed by this issue's timing fix.

Owner approved reviewed timing/optimization changes for publication and closure
of #9 only under `docs/agents/issue-tracker.md`; #13/#14 remain open. Future performance
work should use representative heavy mall rooms, with matched paths/actions and
separate UI/cutscene samples; raw medians here are diagnostic, not controlled
profile benchmarks.
