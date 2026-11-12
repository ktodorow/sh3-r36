# Issue #4: texture and framebuffer operation diagnostics

Status: acceptance passed on actual R36S; owner approved publication and task
closure after local review. Final commit and closure recorded in issue #4 history.

Objective: launch game-derived resource samples on native R36S GLES, capture
independent image/readback checks and memory costs, return cleanly to frontend.
Scope: resource operations supporting G3; full game, scenes, performance and
campaign acceptance remain later tasks. No offline texture/media conversion.

## Context and prerequisite checks

Read canonical spec, issue #4 and blocking #2, prerequisite #3 and all comments,
feasibility report, linked research, glossary/ADR, build/device/tracker guides.
Actual runtime and graphics prerequisite assertions rerun successfully before
dependent implementation: runtime run `20261112T145428930351Z-3b8d27`, graphics
run `20261112T163408180738Z-117198`. Task #3 final published commit:
`339a39b841da9fa09cd2373a3a0e04b6cd290fb3`.

Retained confirmed boundary: installed PortMaster launcher → diagnostic session
→ clean frontend return. Native executable tests run only in reused explicit
Linux ARM64 Docker environment. Hardware checks use saved host/device scripts.
Documentation/research use source and link validation; TDD does not apply there.

## Current primary-source checks (2026-11-12)

External content reviewed as untrusted data; no external instructions executed.
No new temporary reference clones created. Sources accessed read-only.

- [PortMaster native script templates](https://portmaster.games/contribute/porting/script-templates/):
  current control/get_controls/platform-helper/pm_finish lifecycle compared with
  project launcher. Firmware helpers collected and fully reviewed before use;
  hash verification prevents changed helper scripts being sourced unnoticed.
- [S3TC extension specification](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_texture_compression_s3tc.txt):
  DXT1 transparency, DXT3 explicit alpha, DXT5 interpolated alpha are separate
  encodings. DXT2/4 have DXT3/5 storage but premultiplied source semantics.
- [BGRA8888 extension specification](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_texture_format_BGRA8888.txt):
  advertised BGRA8888 does not establish validity of desktop RGBA8/BGRA/REV
  combinations or BGRA vertex attribute size. Actual operations decide path.
- [Border clamp extension specification](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_texture_border_clamp.txt):
  device advertises EXT/OES border clamp; rendered behavior still required.
- [ES readback reference, primary XML source](https://github.com/KhronosGroup/OpenGL-Refpages/blob/main/es3/glReadPixels.xml):
  normalized color targets accept RGBA/UNSIGNED_BYTE; other accepted pairs depend
  on bound framebuffer. Registry XHTML could not be fetched by browser tool;
  primary repository source read instead. Final device reports implementation
  pair `1908,1401` and uses that legal core pair before packing BGRA/1555/4444.
- [DXT1 extension](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_texture_compression_dxt1.txt):
  extension guarantees alpha-capable DXT1 format even when Mesa's compressed-format
  list contains only RGB DXT1. Exact format list and named guarantees checked per
  context; no assumed capability based on GPU family.
- [First-hand SH3 palette regression and fix](https://github.com/cutarev/sh3-nx/issues/1):
  hair alpha failure reported by player, fixed in upstream `f43d4ce`; palette
  flags represent alpha, all-zero palette alpha becomes opaque, palette number
  and version changes require re-expansion. Applicable to same D3D8 layer.
- Upstream SH3 HEAD `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`;
  SH2 HEAD `7e69609f3a063fbe24c41d6aa560f14ede578746`. Start with SH3
  resource implementation; other game's compatibility is not evidence here.
- [Cuphead launch64.txt](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/pm/cuphead/cuphead/launch64.txt),
  commit `1b7e7b019dabeb4226a1b4be5bfdd854895242f5`: native launch lifecycle,
  separate game data and runtime setup applicable; Unity/Mono/ARMHF audio fixes
  do not establish renderer/ABI compatibility for this port.
- [PM Porting Tools](https://github.com/Knifethrower/PM-Porting-Tools/tree/218ac4372b0bb04ebdd2bc6c5c6d64e16b1623e4),
  commit `218ac4372b0bb04ebdd2bc6c5c6d64e16b1623e4`: Unity texture conversion
  tools show engine-specific DXT workarounds. Offline re-encoding not approved
  and not adopted. No external script executed.
- [Comparable Unity runtime](https://github.com/Producdevity/portmaster-unity-toolkit/blob/main/docs/runtime.md):
  first-hand framebuffer/flip diagnostics describe H700 Mali-G31 r20p0 fbdev.
  Target here is RK3326, KMSDRM, r13p0; fbdev flip interception not applicable.
- Delver reference findings in
  [working port patterns](../research_notes/Silent%20Hill%203%20R36S%20feasibility/working_port_patterns.md)
  distinguish Java/libGDX/LWJGL/Weston from this native SDL/KMSDRM renderer.
  Reference HEAD `9083f5e9c23b63fdc67ae2ce4cbeb374692d10be` does not identify
  uncommitted tested R36S port. Current Delver CCE query failed `Transport closed`;
  current searches found no exact Delver packed-readback fix. No Delver code copied.

Queries included `PortMaster GLES Mali shader`, `PortMaster Mali DXT texture
BGRA`, `site:github.com/PortsMaster DXT1 DXT5 texture`, `"PortMaster" "GL_BGRA"
textures packed`, `"Mali" "GL_UNSIGNED_SHORT_1_5_5_5_REV"`. No matching
PortMaster fix for this exact Mali-G31 packed-upload failure found. Older
Mali-400 anecdotes and other engine conversions not applied.
Framebuffer follow-up queries: `PortMaster Mali framebuffer readback BGRA
glReadPixels`, `site:github.com/cutarev/sh3-nx GetFrontBuffer CopyRects`,
`site:github.com/ktodorow/delverengine-mp R36S texture framebuffer`. No exact
PortMaster packed-readback workaround found; Khronos legal-pair rules and actual
operation failures determined fix. No untrusted instructions or fetched scripts
executed; no prompt-injection instructions encountered in reviewed source text.

CCE search returned truncated first-file chunks and ignored build-cache copies;
expanding returned chunk IDs failed. Known intended edit paths reviewed directly
after CCE searches. No private configuration sent to CCE.

## Evidence so far

- Fresh firmware-helper inventory: `r36s-dumps/sh3/20261112T175404167639Z-5b24ef`.
- Format RED: launcher lacked resource marker in Docker run
  `.port-cache/runtime-tests/20261112T175305402709Z`. Added real format samples;
  desktop passed, hardware `20261112T175502807249Z-c81372` reproduced black
  BGRA8 (`0502`) and packed 1555/4444 (`0500`); RGB565 passed. Source unchanged.
- Format GREEN: GLES-only RGBA8 scratch conversion, desktop native path retained.
  Build `.port-cache/builds/20261112T175854609010Z`; Docker regression
  `.port-cache/runtime-tests/20261112T175908852588Z` passed. Actual R36S
  `20261112T175910061573Z-a1a5e2`: execution/collection 0, all 13 independent
  graphics assertions pass. Refactor review: scratch bounded to upload size,
  freed immediately; original guest bytes retained.
- Palette RED: `.port-cache/runtime-tests/20261112T180102845858Z`, missing
  palette operation evidence. An earlier assertion was placed in context-failure
  test by mistake; corrected before accepting this meaningful RED.
- Palette GREEN: Docker `.port-cache/runtime-tests/20261112T180242672478Z`;
  hardware `20261112T180243917027Z-8ad6d5`, all 14 checks passed. Alpha bytes
  51/170/119 preserved through initial upload, palette edit and selection;
  all-zero alpha palette becomes 255. Texture indices unchanged. Existing
  production palette logic needed no change; common diagnostic capture helper
  frees transient guest vertex memory after draw.
- Mip RED: `.port-cache/runtime-tests/20261112T180344923380Z`; GREEN desktop
  `.port-cache/runtime-tests/20261112T180440034205Z`; actual mip samples pass in
  `20261112T180640356888Z-84f30c`. Base/middle/1×1 tail selected via UV
  derivatives; lock/unlock update changes selected middle level to yellow.
- DXT RED: `.port-cache/runtime-tests/20261112T180531085648Z`, missing operation
  marker. Added separate block examples; Mesa native S3TC interpolates within one
  UNORM8 step of specification arithmetic, so interpolation checks explicitly
  allow ±1 (uncompressed checks remain exact). Hardware run
  `20261112T180640356888Z-84f30c` advertises none of `83f1/83f2/83f3`; all
  actual DXT1/3/5 uploads fail `0500`, source unchanged. No assumed Mali-wide
  capability rule; production path queries exact compressed format list.

## Completed slices and regressions

- DXT GREEN: runtime expansion leaves original blocks intact; one mip/face scratch
  freed after upload. Desktop `.port-cache/runtime-tests/20261112T180918231427Z`;
  hardware `20261112T180919453356Z-bd3e84`, all 16 then-current checks passed.
  DXT1 transparent code, DXT3 explicit four-bit alpha with reversed endpoints,
  DXT5 both endpoint branches checked separately. Final assertions inspect all
  four encoded columns, including DXT5's explicit zero/one codes.
- Block-edge/update RED `.port-cache/runtime-tests/20261112T181008911129Z`;
  GREEN `20261112T181131861452Z`. 7×5 textures exercise four blocks, cropped
  edges, 1×1 tail, partial block update. Desktop native DXT1 retention RED
  `20261112T181202951576Z`; extension-guarantee fix GREEN
  `20261112T181246726399Z`. Final hardware exercises decoded path; desktop
  exercises native S3TC path.
- Framebuffer RED `20261112T181429477619Z`, missing sample; real operation RED
  `20261112T181906685662Z` returned stale data on second target lock. Refresh
  each render-target lock; desktop GREEN `20261112T181948323036Z`.
  Hardware `20261112T181953302747Z-c4bbaa` reproduced CPU upload `0502` and packed
  readback `0502`; route CPU target uploads through same conversion and use legal
  RGBA readback before packing. Desktop GREEN `20261112T182144019583Z`;
  hardware `20261112T182144031991Z-83ac71`, all 18 checks passed.
- Preview RED `20261112T182257657279Z`; actual sample RED
  `20261112T182351588525Z` showed GetFrontBuffer changed alpha outside copied
  rectangle. Limit alpha writes to copied rows/columns, reuse legal readback;
  GREEN `20261112T182429834530Z`. Last-presented image survives next backbuffer
  clear; oversized CPU row pitch/sentinels retained, alpha opaque, uploaded image
  produces correctly oriented half-alpha fade through fixed-function path.
- Sampler RED `20261112T182451426453Z`; GREEN `20261112T182539248962Z`.
  Wrap, mirror, edge, border, linear border mixing and interior linear filtering
  rendered; existing production sampler path needed no change. Hardware preview
  and samplers GREEN `20261112T182554157154Z-c45f06`, all 20 checks passed.
- Memory RED `20261112T182636788004Z`; GREEN `20261112T182731640347Z`.
  Eight 512×512 full-mip textures actually uploaded/rendered/released sequentially.
  Hardware `20261112T182805687619Z-5ad9b5`, all 21 checks passed. Build/deployment
  briefly overlapped during later sample work; this intermediate run's recorded
  deployed identity remains authoritative. Final verification below used finished
  build, then deployment, sequentially.
- Previously locked target update RED `20261112T182806916077Z`; actual stale GPU
  image reproduced `20261112T182839184600Z`. CPU CopyRects must select GPU target
  path even after readback allocated guest memory. GREEN `20261112T182917220611Z`;
  writable subrectangle lock leaves rest of target unchanged.
- Compressed tail copy RED `20261112T182940952180Z`; actual black tail reproduced
  `20261112T183009352169Z`. Round block-copy width/height up, retaining whole
  1×1 DXT1/3/5 tail block. GREEN `20261112T183104062284Z`.
- Packed alpha evidence RED `20261112T183213187678Z`, missing RGBA captures.
  Capture and check actual alpha (ARGB8/4444 = 51; X formats/RGB565 = 255).
  Final desktop GREEN below. No further production conversion needed.

Each GREEN followed design review before next slice. Shared upload/readback
helpers retain desktop behavior, scratch has bounded lifetime, compressed
capability choice cached per context, creation uses one consistent storage
choice. Refactor reran relevant launcher checks. No new test boundary introduced.

## Sample provenance and acceptance mapping

Recognized owner input SHA1 `d851669ef609b3164e3581aa8dcfbfaec866cb79`,
3,338,240 bytes, unchanged after builds. Original shader/declaration and quad
provenance from task #3 retained. Quad VA `006b0d00`, original DrawPrimitiveUP
call `0041e0a9`, FVF `104`, stride 24. Resource samples use original pixel shader
and quad with diagnostic dimensions/UVs; texture bytes are independent literal
format examples, not redistributed game assets or captures of full game scenes.

Owner executable render-target width/height tables VA `006b1434`/`006b1444`
contain 64/512/256/256; extractor validates exact recognized values. Original
texture wrappers `00427c70`/`00427ce0` use these dimensions; CreateTexture calls
`00427ccc`/`00427d1a` use ARGB8, render-target/managed usage respectively.
DDS format branches `00626fe2`/`00626ff0`/`00626ffe` distinguish DXT1/3/5.

Static address-state audit found 149 immediate-value U/V call sites: 73 edge,
72 wrap, four border. Border call VAs `0041efe5`, `0041eff9`, `0041f92c`,
`0041f940`; audit data `.port-cache/task-04-sampler-calls.json`. This establishes
concrete required border usage; not an exhaustive dynamic state trace. Mirror
also tested. No MIRRORONCE requirement found in inspected immediate calls.

| Issue criterion | Actual evidence |
| --- | --- |
| BGRA vertex vs texture, packed formats | Existing packed vertex color check retained; seven texture formats render independent RGB and alpha values; source bytes unchanged |
| Palette, mip/update, DXT variants | Alpha, all-zero-alpha fallback, palette edit/selection 65535/65534; base/middle/tail and lock update; separate DXT color/alpha rules, cropped blocks and compressed copies |
| Compatible conversion and memory | GLES BGRA/REV → RGBA8; unsupported exact S3TC formats → runtime RGBA8; source kept, per-upload and full-chain costs logged |
| FBO/depth/stencil/copy/orientation/readback | Original 512×512 target with 640×480 depth exercises spare-depth bottom rows; existing stencil tests retained; GPU blit, GPU↔CPU rectangles/pitches, fresh locks, packed readback, last-presented preview fade |
| Required sampler/border/depth clamp | Rendered address/filter/border results; prior RHW shader depth-clamp fallback retained and passes on actual device without depth-clamp extension |

## Measured conversion costs

Final hardware logs record actual chosen storage/upload paths. Full 512×512,
10-level 2D chain; byte counts below. Scratch is largest one-level allocation,
freed before next level. GPU column is logical texture payload, not driver
allocation padding, tiler buffers or metadata. Source excludes resource headers
and palette table (P8 palette adds 1,024 bytes). Process RSS includes driver and
diagnostic work; cannot attribute all RSS to one texture.

| Format | Retained source | Peak upload scratch | Logical GPU |
| --- | ---: | ---: | ---: |
| ARGB8 | 1,398,100 | 1,048,576 | 1,398,100 |
| RGB565 native | 699,050 | 0 | 699,050 |
| ARGB1555 → RGBA8 | 699,050 | 1,048,576 | 1,398,100 |
| ARGB4444 → RGBA8 | 699,050 | 1,048,576 | 1,398,100 |
| P8 → RGBA8 | 349,525 | 1,048,576 | 1,398,100 |
| DXT1 → RGBA8 | 174,776 | 1,048,576 | 1,398,100 |
| DXT3 → RGBA8 | 349,552 | 1,048,576 | 1,398,100 |
| DXT5 → RGBA8 | 349,552 | 1,048,576 | 1,398,100 |

XRGB8/1555/4444 share corresponding storage/conversion with opaque sampling.
64×48 packed readback uses 12,288-byte RGBA scratch plus retained guest surface.
Final diagnostic peak RSS **54,100 KiB**; textures exercised sequentially.
No offline conversion, original asset alteration or claim of full-game memory fit.

## Final validation and handoff

- Reused Linux ARM64 Docker image
  `sha256:d62ffe311d93d8ccce4c3c8ebf39d7c5dedad230bf717063008219667a961432`,
  Debian 12/glibc 2.36 against target glibc 2.41. No new image, builder or volume.
  Final build `.port-cache/builds/20261112T183228760144Z`, status 0.
  Runtime SHA256 `30fed8537d3f46eae83b9f6c7b093f4f5e9c73c5c1b33cbb1c605047100cee7c`;
  collected device `runtime.sha256` matches finished build.
- Final Docker launcher suite `.port-cache/runtime-tests/20261112T183248505975Z`:
  **26 passed, 33 skipped** (device/owner-dependent checks). Desktop GL4.5 Mesa
  uses native S3TC; no hardware pass inferred from software reference.
- Final hardware `r36s-dumps/sh3/20261112T183306330783Z-88f90a`:
  execution **0**, collection **0**, **23 independent assertions pass**,
  `gles=PASS`; **72 PPM + 53 raw RGBA captures**, generated GLSL/provider maps,
  format/memory logs and preserved frontend/process/mount/firmware checks.
  Native ARM Mali-G31 GLES3.2 r13p0, KMSDRM/SDL2.32.10, EGL1.4.
- Host fixtures: **21 passed, 38 skipped**;
  `.port-cache/task-04-final-host.txt`. Hardware assertion output
  `.port-cache/task-04-final-hardware.txt`. Desktop output
  `.port-cache/task-04-final-desktop.txt`. `git diff --check` passed.
- Visual inspection: `.port-cache/task-04-captures.png`, generated from final
  hardware PPMs. Panel order: 512 target, rectangle upload, preview fade, DXT3,
  DXT5 six-entry alpha branch, linear border. Independent pixel assertions use
  literal format examples; interpolated S3TC/filter/fade permits one UNORM8 step.
  Uncompressed point samples remain exact.

Reviewed diff: `.port-cache/task-04-review/changes.diff`. Publication scope:
task-owned source, diagnostic tests, guides and this report. Private configuration,
owner data, build outputs and raw device evidence remain local and ignored.
No temporary clones created; no cleanup removed historical evidence.
Pre-existing untracked `.DS_Store` left untouched.

Remaining limits: resource-operation evidence supports G3 alongside task #3;
complete renderer, exhaustive asset/format inventory, original scene rendering,
performance, concurrent texture residency, full-game memory fit, FMVs/audio,
controls/saves and campaign acceptance remain later tasks. DXT2/4 storage aliases
retain premultiplied source semantics but were not required or separately accepted.
