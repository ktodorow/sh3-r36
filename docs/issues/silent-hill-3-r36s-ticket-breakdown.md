# Silent Hill 3 R36S — approved ticket breakdown

Current scheduling: [performance-first priority order](silent-hill-3-r36s/README.md#current-priority-order), requested 2026-11-14. #13/#14 take precedence over original-movie implementation. Status statements and initial frontier below describe original 2026-11-11 publication; #1–#9 are now closed. Stable plan IDs, acceptance scopes and native blocking relationships remain unchanged.

Structure and subsequent publication approved by user on 2026-11-11. GitHub holds current task history; this file records approved breakdown. All [19 implementation issues](silent-hill-3-r36s/README.md) are published, verified open and unlabeled, with 26 native blocking relationships. Local files preserve approved scopes. No capability gate passed.

Canonical requirements: [Silent Hill 3 R36S spec](../specs/silent-hill-3-r36s.md). Research, glossary and ADR links remain in spec. Approved scopes below preserve confirmed launcher → game session → frontend boundary. Host fixtures cover launcher failures and cleanup only; runtime/graphics/media/input/performance acceptance needs actual R36S evidence. Future behavior changes require observed RED–GREEN–REFACTOR under project workflow; documentation drafting uses coverage/dependency validation.

User instruction: **tickets carry no `ready-for-agent` tag**. Prepare these tickets unlabeled; do not create or apply triage labels. No inferred readiness from this breakdown. Earlier spec-publication label default is superseded for this batch.

Numbers below are stable plan identifiers; [issue index](silent-hill-3-r36s/README.md) maps them to GitHub issues. Tickets were published in dependency order, with native blocking relationships and canonical spec links pinned to verified pushed source revision. Source was spec file; no separate parent issue created or closed. Existing feature overview remains local documentation.

User initially approved ticket size, blocking edges and split with “Approve structure; keep local,” then authorized commits, push and issue publication. Publication preserves approved scopes and blocker graph. No implementation work, device runs or builds performed; all implementation issues remain open pending their own acceptance.

Blocking edges below gate implementation claims. Prerequisite-free investigation may proceed earlier; completion report alone cannot pass missing capability. No wide prefactor is justified by current evidence. Unknown compatibility/performance/campaign faults become focused follow-up tickets and block affected capability until fixed and rechecked; qualification tickets do not contain unbounded fix-everything scope.

## 01. Validate Game data and record current R36S target

**Blocked by:** None (can start immediately).

**Delivers:** Launch PortMaster preflight, recognize supported owner data, collect current target identity, then return safely to frontend.

**Spec coverage:** AC01, AC02, AC03, AC13.

**Scope and acceptance:**

- [ ] Verify expected executable size/hash and required-data inventory; show useful errors for wrong or missing inputs without altering originals.
- [ ] Verify private-artifact ignore coverage before local configuration or evidence; document selected port folder and reusable unattended host/device workflow before first deployment.
- [ ] Record installed firmware, kernel, libc, SDL, driver/provider and controller identities through saved scripts; missing tools are findings rather than installation instructions.
- [ ] Collect run identity, stdout, stderr, exit status and failure results separately; keep credentials private and preserve prior logs/saves. Host fixtures cover observable preflight errors and cleanup only.

## 02. Launch reproducible Linux ARM64 runtime diagnostics

**Blocked by:** 01.

**Delivers:** Build native runtime in reusable Docker Linux ARM64 environment and launch its diagnostics through installed PortMaster package.

**Spec coverage:** AC02, AC03, AC13.

**Scope and acceptance:**

- [ ] Read or create project build guide before build work; reuse compatible existing environment, pin inputs and provide scoped cleanup preserving source, final artifacts and evidence.
- [ ] Generate matching game code and compile compatible AArch64 artifacts, preserving translated guest semantics and required compiler assumptions; inspect complete dependency closure.
- [ ] On current R36S, verify guest address reservation/commit behavior and relevant thread, signal and timer diagnostics independently of game rendering; reserve versus resident memory remains explicit.
- [ ] Keep private dependencies port-local, retain firmware graphics provider initially, collect actual runtime results and clean frontend return. G2 requires passing runtime evidence, not just successful linking.

## 03. Render game-derived shader and indexed-draw samples on R36S

**Blocked by:** 02.

**Delivers:** Use installed launcher to render and collect known game-derived shader/geometry samples on hardware GLES.

**Spec coverage:** AC02, AC06, AC13.

**Scope and acceptance:**

- [ ] Record actual SDL/EGL backend, hardware renderer, GLES/GLSL versions, relevant extensions and limits; no version spoofing or software-renderer pass.
- [ ] Exercise representative generated vertex/fragment shaders and precision, indexed/base-vertex draws, coordinate/depth conventions, culling, scissor and depth/stencil results against independent expectations.
- [ ] Select supported core/extension paths or verify required fallback through rendered output; report unsupported required operations as unresolved blockers.
- [ ] Retain desktop comparison route. Diagnostics stay under existing launcher/game-directory public boundary; fixtures and triangle-only success cannot pass game-derived operations.

## 04. Render game-derived texture and framebuffer samples on R36S

**Blocked by:** 02.

**Delivers:** Launch resource-operation samples, capture correct images and readback, then return to frontend with format and memory evidence.

**Spec coverage:** AC02, AC06, AC10, AC12, AC13.

**Scope and acceptance:**

- [ ] Verify actual-use BGRA vertex/texture distinctions, packed formats, palette alpha, mip/update behavior and DXT1/3/5 support separately; preserve original data.
- [ ] For required unsupported formats, validate compatible conversion and record source, temporary and GPU memory costs; offline media/texture conversion is not silently approved.
- [ ] Exercise framebuffer attachments, depth/stencil, blit/copy, orientation and legal readback formats against independent reference images, including preview/fade source behavior.
- [ ] Verify required sampler/border/depth-clamp behavior where used. Together with shader/draw results, this provides G3 operation evidence, not complete renderer compatibility.

## 05. Reach menus and first playable scene through native GLES3

**Blocked by:** 03, 04.

**Delivers:** From Ports, enter readable game menus, start game, render first interactive scene at 640×480 and exit to frontend.

**Spec coverage:** AC02, AC03, AC06, AC13.

**Scope and acceptance:**

- [ ] Connect verified GLES paths to actual game renderer, preserving desktop baseline and handling required context/loading/shader/resource semantics.
- [ ] Use 640×480 Internal resolution and Output resolution with correct 4:3 presentation and readable initial menus/HUD.
- [ ] Capture actual scene, input response, build/data identities, shader/GL failures and cold/warm runs; compare against trusted original/desktop baseline.
- [ ] Record first playable checkpoint and reusable scene evidence. This milestone does not pass complete effects, physical-control matrix, campaign, movies or 30 FPS acceptance.

## 06. Preserve representative gameplay and cutscene rendering

**Blocked by:** 05.

**Delivers:** Play repeatable scene set with correct lighting, fog, transparency, reflections, fades and interface presentation.

**Spec coverage:** AC06, AC13.

**Scope and acceptance:**

- [ ] Compare indoor flashlight, fog, retained shadows, palette-dependent hair alpha, transparency/reflections and real-time cutscenes against trusted baseline captures.
- [ ] Exercise map/inventory, transitions and frame snapshots with consistent coordinate, depth, clipping and readback behavior; preview persistence remains separate save/load acceptance.
- [ ] Verify cold/warm shader-cache behavior after renderer changes; no stale-cache workaround or repeated material GL/shader faults.
- [ ] Record scene/checkpoint/camera and build identities so same cases can gate later resolution and performance changes.

## 07. Play normal actions using R36S controls

**Blocked by:** 05.

**Delivers:** Navigate menus and perform normal gameplay actions using handheld controls and PortMaster mappings.

**Spec coverage:** AC09, AC03.

**Scope and acceptance:**

- [ ] Record physical control/action matrix for movement, camera, combat, weapon/search actions, map, inventory, pause, confirm/cancel and exit.
- [ ] Verify both sticks, d-pad, face/shoulder buttons, digital-trigger axis expectations and stick clicks where used; keyboard must not be required for normal play.
- [ ] Check platform/positional button conventions on actual hardware. Remapping choices flow into persistence acceptance rather than being assumed saved.
- [ ] Demonstrate predictable orderly exit and frontend return using physical controls; fixture success cannot pass this matrix.

## 08. Resume saved progress and settings after cold restart

**Blocked by:** 05.

**Delivers:** Save progress, exit, cold-launch and resume correct game state with intact previews and settings.

**Spec coverage:** AC10, AC13.

**Scope and acceptance:**

- [ ] Establish writable save/config/mapping/cache/log ownership while preserving original Game data, existing saves and unrelated ports.
- [ ] Round-trip saves after room transitions; verify thumbnails identify saved state and progression resumes after cold restart.
- [ ] Verify settings and supported mappings persist; exercise resolution-change persistence when that setting becomes available and record it for final integration recheck.
- [ ] Trigger safe write-failure cases through observable public behavior; preserve previous valid save and show useful failure. Device evidence is required for real persistence.

## 09. Preserve game audio and simulation speed at 30 FPS

**Blocked by:** 05.

**Delivers:** Play timed movement/combat/animation sequences with complete gameplay audio and intended game speed under 30 FPS presentation.

**Spec coverage:** AC08, AC11.

**Scope and acceptance:**

- [ ] Compare movement, combat, animation and timers to trusted baseline using repeatable cases; frame cap cannot halve simulation speed.
- [ ] Verify music, speech and effects across representative transitions and repeated playback without reproducible looping races, underruns or drift.
- [ ] If Linux guest-thread/audio faults occur, establish reproduced cause before bounded scheduling changes; do not blindly constrain whole process or alter allocator lifetime policy.
- [ ] Keep gameplay clocks distinct from future movie clock. Repeat timing/audio cases at both supported resolutions during profile acceptance.

## 10. Identify original FMVs and measure native decode feasibility

**Blocked by:** 02.

**Delivers:** Inventory owner-supplied original movies and run repeatable target decode measurements without modifying media.

**Spec coverage:** AC05, AC11, AC12, AC13.

**Scope and acceptance:**

- [ ] Identify actual containers/codecs, variants, dimensions, cadence, duration and audio/subtitle sources; extension and inherited comments are not codec proof.
- [ ] Trace movie calls used by matching game and review shared SH2 precedent before selecting narrow integration; choose decoder from actual support evidence.
- [ ] Compile decoder dependencies only in reusable Docker Linux ARM64 environment and measure original-media decode time, audio handling and peak memory on current R36S.
- [ ] Preserve source cadence/content and original assets. Unsupported or too-slow decode remains explicit blocker; do not substitute offline transcodes or treat inventory report alone as decoder capability pass.

## 11. Play first original FMV and return to gameplay

**Blocked by:** 05, 09, 10.

**Delivers:** Trigger one original movie through real game flow, present synchronized video/audio, finish or skip, then continue gameplay.

**Spec coverage:** AC05, AC11, AC03.

**Scope and acceptance:**

- [ ] Connect actual game-used movie boundary to validated decoder and SDL/GLES outputs, retaining original media cadence and correct aspect ratio.
- [ ] Exercise natural completion and supported skip independently, with synchronized audio and subtitles where applicable.
- [ ] Restore game rendering/audio/input state after playback; exit and failed playback release owned resources and return predictably.
- [ ] Record reproducible game checkpoint and target evidence. One movie passes only this slice, not all-FMV coverage.

## 12. Complete all-original-FMV playback and lifecycle coverage

**Blocked by:** 11.

**Delivers:** Play every inventoried original FMV with correct media timing and reliable return to game.

**Spec coverage:** AC05, AC11, AC12.

**Scope and acceptance:**

- [ ] Record per-movie/required-variant content, aspect, audio/subtitle timing, cadence/duration, natural finish and supported skip results on R36S.
- [ ] Test end-of-media when frames arrive late or are dropped; completion cannot depend on display of last frame. Subtitles follow media clock.
- [ ] Exercise repeated movie/game transitions and supported pause/resume behavior where present; preserve rendering/audio/input state and release decoder resources.
- [ ] Cover failures without silent successful skip or lost story content. Keep movie inventory reconciled with later campaign/ending checklist; this does not yet prove every campaign trigger.

## 13. Profile correct representative gameplay at 640×480

**Blocked by:** 06, 09.

**Delivers:** Run matched scenes at lowest supported graphics and 640×480 Internal resolution with evidence identifying performance limits.

**Spec coverage:** AC06, AC07, AC08, AC12, AC13.

**Scope and acceptance:**

- [ ] Survey supported graphics choices and define exact lowest profile without removing gameplay-critical effects or story presentation.
- [ ] Capture warmed matched scenes, cold/warm caches, build/data identities, fixed camera/save state and comparable thermal conditions; retain 640×480 Output resolution.
- [ ] Report p50/p95/p99/max frame times, sustained dips, loading/shader stalls, audio underruns, per-thread CPU, GPU/render work, uploads/I/O/synchronization, memory and hot-session clocks.
- [ ] Separate CPU, GPU, memory, I/O and synchronization limits before choosing optimization. Profiling can pass as measurement work while 30 FPS capability remains unpassed.

## 14. Select verified 30 FPS profile with conditional 320×240 fallback

**Blocked by:** 08, 13.

**Delivers:** Select and persist evidence-backed lowest-graphics profile, preferring 640×480 and testing 320×240 when 640×480 is unstable.

**Spec coverage:** AC06, AC07, AC08, AC10, AC11.

**Scope and acceptance:**

- [ ] Define user-approved treatment of rare loading/transition stalls before claiming stability; retain 30 FPS requirement rather than inventing numeric waiver.
- [ ] If 640×480 meets agreed target, retain preferred profile. Otherwise expose and measure matched 320×240 Internal resolution with fixed 640×480 Output resolution, correct 4:3 and readable UI.
- [ ] Recheck scene effects, save previews/settings across resolution changes, original simulation speed and audio at both supported modes; record chosen profile and paired evidence.
- [ ] Resolution reduction cannot pass CPU-bound slowdown. Turn any remaining measured bottleneck into bounded follow-up fix tickets that block this capability; do not promise unrestricted optimization within this ticket.

## 15. Return cleanly from complete sessions and failure paths

**Blocked by:** 07, 08, 12.

**Delivers:** Cold/warm launch full integrated package, play/save/watch video, exit or encounter failure, then regain usable frontend.

**Spec coverage:** AC01, AC03, AC10, AC13.

**Scope and acceptance:**

- [ ] Use installed PortMaster lifecycle and compatible private dependencies for actual integrated game, controls, writable state and decoder resources.
- [ ] Exercise bad/missing inputs, runtime failure, movie failure and orderly/physical exit; verify no owned helpers or mounts remain and frontend is usable.
- [ ] Preserve originals, prior valid saves/logs and unrelated ports; distinguish run failures from failed evidence collection and attempt collection after failures.
- [ ] Host fixtures cover launcher failure/cleanup behavior only. Actual R36S evidence covers normal and failing integrated sessions.

## 16. Sustain hot sessions and repeated transitions within memory limits

**Blocked by:** 14, 15.

**Delivers:** Continue selected profile through repeatable gameplay/movie/save/load loops and long hot session without OOM, corruption or resource growth.

**Spec coverage:** AC03, AC05, AC10, AC11, AC12, AC13.

**Scope and acceptance:**

- [ ] Record baseline, warmed and peak process/system memory, relevant GPU/texture/decoder/guest-heap telemetry and thermal/clock behavior; distinguish virtual reservation from residency.
- [ ] Repeat representative room transitions, combat, saves/loads, movies and exits using safe preserved checkpoints; verify no unbounded growth, OOM or reproducible audio races.
- [ ] Retain prior valid saves and confirm clean frontend return after soak. No blind quarantine reduction or gameplay timing change counts as memory fix.
- [ ] State observed duration, loops, pass/fail and untested limits. Successful controls/saves/all movies/cleanup plus bounded hot-session evidence establishes G5 for campaign sign-off.

## 17. Verify complete campaign progression on R36S

**Blocked by:** 16.

**Delivers:** Complete continuous normal campaign route from new game to ending/credits through installed package, preserving traceable checkpoints.

**Spec coverage:** AC04, AC05, AC06, AC08, AC09, AC10, AC11, AC12.

**Scope and acceptance:**

- [ ] Derive complete ordered area/encounter/puzzle/real-time-cutscene checklist from trusted original/desktop baseline; record actual route, checkpoint saves, build/data/profile identities and evidence for each entry.
- [ ] Verify full progression, physical actions, rendering/audio/timing, in-context FMV triggers and save/resume across campaign rather than substituting isolated scene or movie probes.
- [ ] Keep task bounded to qualification and reproduced faults: create focused regression-fix tickets for newly found blockers, retain failing evidence, and recheck affected route after fixes before passing.
- [ ] Full campaign pass requires no unresolved progression/material presentation faults. A checklist draft or blocker report is not campaign completion; additional ending routes remain separate.

## 18. Verify remaining required ending paths and media coverage

**Blocked by:** 17.

**Delivers:** Reach remaining required original ending sequences and credits with intact story media and resumable progression.

**Spec coverage:** AC04, AC05, AC06, AC10, AC11.

**Scope and acceptance:**

- [ ] Reconcile required ending routes and prerequisites against trusted baseline and canonical Full port scope; record which routes normal campaign already covered.
- [ ] Use preserved, traceable on-device progression/checkpoints to exercise remaining paths and actual game-triggered ending media/credits.
- [ ] Reconcile campaign triggers with complete original-movie inventory so no untested movie or story sequence disappears behind standalone playback success.
- [ ] Record build/profile/save provenance, controls/audio/rendering and clean return; newly found faults require focused fixes and recheck before acceptance.

## 19. Qualify Full port against canonical R36S acceptance criteria

**Blocked by:** 18.

**Delivers:** Produce final reproducible evidence that complete personal R36S port meets all canonical requirements on identified build and firmware.

**Spec coverage:** AC01, AC02, AC03, AC04, AC05, AC06, AC07, AC08, AC09, AC10, AC11, AC12, AC13.

**Scope and acceptance:**

- [ ] Audit all thirteen criteria and six capability gates against actual passing evidence, including current target/dependency identity, campaign/endings, every original FMV and integrated controls/saves/audio/cleanup.
- [ ] Re-run performance and timing on campaign-discovered worst cases under agreed stability assessment; early representative samples or average FPS do not pass complete-game performance.
- [ ] Ensure final build/profile has current regression coverage for cold/warm launch, both resolution behaviors, write/runtime failures, bounded memory and clean frontend return; stale pre-fix evidence requires relevant recheck.
- [ ] Keep feature open while any criterion, unresolved blocker or missing hardware result remains. Prepare local closeout for explicit publication/closure review; public PortMaster submission and asset distribution remain out of scope.

## Coverage and frontier

| Spec criterion | Tickets carrying acceptance or supporting proof |
| --- | --- |
| AC01 | 01, 15, 19 |
| AC02 | 01, 02, 03, 04, 05, 19 |
| AC03 | 01, 02, 05, 07, 11, 15, 16, 19 |
| AC04 | 17, 18, 19 |
| AC05 | 10, 11, 12, 16, 17, 18, 19 |
| AC06 | 03, 04, 05, 06, 13, 14, 17, 18, 19 |
| AC07 | 13, 14, 19 |
| AC08 | 09, 13, 14, 17, 19 |
| AC09 | 07, 17, 19 |
| AC10 | 04, 08, 14, 15, 16, 17, 18, 19 |
| AC11 | 09, 10, 11, 12, 14, 16, 17, 18, 19 |
| AC12 | 04, 10, 12, 13, 16, 17, 19 |
| AC13 | 01, 02, 03, 04, 05, 06, 08, 10, 13, 15, 16, 19 |

Gate handoff: G1 → 01; G2 → 02; G3 → 03 + 04; G4 → 06 + 09 + 13; G5 → 07 + 08 + 12 + 15 + 16; G6 → 17 + 18 + 19 with selected-profile proof from 14. These are intended future evidence owners, not passed gates.

Initial frontier: 01. After 02 passes, 03, 04 and 10 can proceed independently. After 05 passes, 06, 07, 08 and 09 can proceed independently. Dependencies are capability prerequisites, not arbitrary serial ordering. Final qualification audits all acceptance evidence despite only listing transitive blockers.

Approved campaign scope: 17 gathers/verifies normal playthrough evidence; new fixes must be separate focused tickets. If trusted route later needs smaller checkpoint groups, propose that scope change with concrete boundaries. No assumption that one pass covers every ending or movie variant.
