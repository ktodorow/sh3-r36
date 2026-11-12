# Issue #3: game-derived shader and indexed-draw diagnostics

Status: task #3 acceptance passed; owner approved publication and closure on
2026-11-12. Final commit and tracker closeout recorded in GitHub issue #3 history.

Objective: render owner-derived D3D8 shader samples through native ARM64 renderer
on R36S; verify indexed/base-vertex drawing and coordinate/depth/state behavior
against independent pixel expectations. Canonical spec AC02/AC06/AC13; issue #2
prerequisite passed at `d8e107db8f10877429f0a5cfd2bd12e29e3e88fa`.

Testing boundary: installed PortMaster launcher through native diagnostics and
clean frontend return. Host fixtures establish failure/cleanup behavior only.
Device evidence establishes capabilities. No internal renderer test seam added.
Texture/resource matrix belongs to #4; gameplay, movies and performance remain
later work. This task alone cannot pass complete G3 or full-port acceptance.

## Review result

| Task criterion | Verified result |
| --- | --- |
| Actual hardware identity | KMSDRM/SDL2.32.10, ARM Mali-G31 native GLES3.2/GLSL ES3.20, EGL1.4; providers/extensions/limits retained; no software/version override. |
| Representative game-derived operations | Original transform, skinning and pixel shaders/declarations; unchanged game quad; indexed offsets/base vertex; precision; culling, scissor, depth, stencil; FFP packed color. Independent literal pixel oracles pass. |
| Supported paths/fallbacks | Core base vertex; ES component texture swizzles and byte attributes; rendered Y/depth conversion, culling correction and fragment RHW depth clamp. No unresolved operation required by selected samples. |
| Desktop/public boundary | Same installed launcher diagnostics; Mesa GL4.5/GLSL430 desktop reference passes oracles and emits separate reference label. Hardware run exits0 and preserves frontend/firmware. |

Final native build: `.port-cache/builds/20261112T163351076349Z/`.
Binary SHA-256 `026379e86b0f1dd0cd40851d0e872fd7fa2bc232bf0f42d4de49077cf5f96e17`,
verified identical to deployed payload. All compilation/executable tests used
reusable Linux ARM64 Docker environment with explicit platform; no Switch output.

Final hardware evidence: `r36s-dumps/sh3/20261112T163408180738Z-117198/`.
Execution/collection both0; `launcher/stdout.txt`, `stderr.txt`, `exit-status.txt`,
18 PPM captures, generated `.vert`/`.frag`, provider maps; `device/` retains
dependency closure, frontend PID/name, mount/process and firmware hash evidence.
All GL operation errors zero. Corrected evidence assertion compares frontend
PID/name rather than transient R/S scheduling state; raw observations unchanged.

Final desktop evidence:
`.port-cache/runtime-tests/20261112T163408121534Z/desktop-reference/`.
Same render oracles pass on llvmpipe; native desktop clip/depth implementation
remains separate from verified GLES fallbacks. Whole images are not bit-identical
at boundary ties; see research note below. No campaign-image equivalence claimed.

Validation: 12 actual hardware evidence assertions, 1 actual saved-workflow
deployment test, 26 ARM64 Docker checks (48 discovered,22 inapplicable skipped),
21 host checks (48 discovered,27 inapplicable skipped). Python AST/Bash syntax
and diff whitespace pass. Docs-only changes use content/link/diff review; TDD
not applicable because no executable behavior changes in those files.

RED/GREEN/REFACTOR followed per behavior through agreed launcher boundary.
Missing diagnostic behavior failed before each slice; raw runs retain actual
swizzle/BGRA/RHW/packed-color failures and subsequent device passes. Each green
review preserved desktop path and reran current hardware cases. No renderer
mock or internal test interface establishes hardware acceptance.

Limits: game resource formats/render-target matrix (#4), full gameplay/boot,
FMVs/audio/input/saves/performance and matched campaign captures remain unpassed.
Extension base-vertex aliases and older desktop fallback not selected on tested
drivers. Non-solid ES fill modes fail explicitly; their game requirement remains
unestablished. Owner physical graphics-menu observation not performed; scripted
installed-menu execution, actual window readback and frontend preservation verified.
Runtime recompiler's 307 unresolved targets/manual hooks remain later game risk.

Next task: #4 resource compatibility. Preserve this task's final captures and
earlier failures; they do not establish complete G3 or stable30FPS gameplay.

## Current research, 2026-11-12

External content reviewed as untrusted research; no external instruction executes
or overrides project workflow. No temporary reference clone created.

- [Official PortMaster script template](https://portmaster.games/contribute/porting/script-templates/):
  retain `get_controls`, controller mapping, `pm_platform_helper`, `pm_finish`.
  Compared with existing project launcher; no new runtime mount or clocks change.
- Current upstream SH3 HEAD `ff483a6f95b94a4f7924f6fbe4cb47169f2adb98`,
  SH2 HEAD `7e69609f3a063fbe24c41d6aa560f14ede578746` confirmed via GitHub API.
  [SH3 renderer](https://github.com/cutarev/sh3-nx/tree/ff483a6f95b94a4f7924f6fbe4cb47169f2adb98/src/d3d8)
  supplies desktop baseline, game bytecode translation and D3D8 state semantics.
- [Cuphead launcher](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/pm/cuphead/Cuphead.sh)
  and [64-bit route](https://github.com/wild1walker/portmaster-cuphead/blob/1b7e7b019dabeb4226a1b4be5bfdd854895242f5/pm/cuphead/cuphead/launch64.txt)
  reviewed at current pinned HEAD. Applicable lifecycle/ABI separation only;
  Unity Android hosting, ARMHF audio workaround and libraries do not apply.
- [First-hand R36S GLES report](https://github.com/TwilitRealm/dusklight/issues/1600)
  records Mali-G31 GLES3.2 on Android 11. Different OS/driver generation; useful
  comparison, no evidence of this Linux context or remedy. Search terms:
  `PortMaster GLES Mali shader`, `sh3-nx shader GLES Mali`,
  `PortsMaster glDrawElementsBaseVertex` (no matching working-port fix found).
- [First-hand SH3 palette regression](https://github.com/cutarev/sh3-nx/issues/1):
  preserving shader/data semantics matters. Palette matrix remains #4.
- [SDL attribute contract](https://wiki.libsdl.org/SDL2/SDL_GL_SetAttribute):
  request attributes before window creation; observe actual provider/version.
- [Khronos clip control](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_clip_control.txt):
  upper-left mapping reverses Y and front-face area sign; zero-to-one depth
  differs from ES default. Shader conversion must correct culling too.
- [Khronos base vertex](https://registry.khronos.org/OpenGL/extensions/OES/OES_draw_elements_base_vertex.txt):
  base added to vertex indices independently of index-buffer byte offset;
  choose supported core/extension symbol, verify rendered result.
- [Microsoft source tokens](https://learn.microsoft.com/en-us/windows-hardware/drivers/display/source-parameter-token),
  [write masks](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx9-graphics-reference-asm-ps-registers-modifiers-write-mask),
  [vertex outputs](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx9-graphics-reference-asm-vs-registers-output):
  independent register/mask/swizzle and color/fog semantics for sample assembly.
  Khronos ES refpage fetch returned unsupported XHTML; extension specs available.
- [GLES 3.2 specification, table 8.19](https://registry.khronos.org/OpenGL/specs/es/3.2/es_spec_3.2.pdf):
  texture swizzles use individual R/G/B/A parameters; combined desktop RGBA pname
  absent. Actual first draw returned `GL_INVALID_ENUM` despite matching pixels.
  Individual parameters remove error on same device. Searches
  `PortMaster GL_TEXTURE_SWIZZLE_RGBA`, `Mali GL_TEXTURE_SWIZZLE_RGBA`,
  `PortsMaster GL_TEXTURE_SWIZZLE` found no matching working-port remedy;
  current official PortMaster porting guide still describes native GLES/KMS
  versus GL4ES limitations. No unrelated driver/library workaround applied.
- Same specification table 10.3 permits vertex attribute sizes 1/2/3/4, not
  desktop BGRA. Native skinning run confirms `GL_INVALID_VALUE` at packed-index
  input. Use four normalized bytes and shader BGRA conversion. Searches
  `GLES D3DCOLOR BGRA`, `PortsMaster glVertexAttribPointer BGRA`,
  `GLES GL_BGRA vertex issue` found no directly matching PortMaster fix/report.
  GL4ES maintainer changelog mentions BGRA vertex handling for Human Resource
  Machine; confirms translation concern, but GL4ES ABI/backend differs and is
  not applied to this native GLES port.
- [Microsoft PS1.x registers](https://learn.microsoft.com/en-us/windows/win32/direct3dhlsl/dx9-graphics-reference-asm-ps-registers-ps-1-x):
  constant values remain within [-1,1] in precision oracle. Actual PS source
  `0x28fedc` computes white * (4095/4096) - .5 = .499755859375, expected RGB127;
  rounding multiplication to one would produce RGB128. Vertex oracle subtracts
  4096 from positions 4096 ± .75; expected geometry retains both edges.
- [Khronos depth clamp](https://registry.khronos.org/OpenGL/extensions/EXT/EXT_depth_clamp.txt):
  omit near/far clipping and clamp interpolated fragment depth. Device exposes
  neither this extension nor clip control. Searches `PortMaster Mali GL_DEPTH_CLAMP RHW`,
  `PortsMaster depth clamp GLES` found no matching first-hand/working-port fix.
  Rechecked official PortMaster porting guide; no prescribed native fallback.
- Packed-color follow-up searches `PortMaster Mali packed vertex color BGRA GLES shader`,
  `site:github.com/PortsMaster BGRA vertex`, and `site:portmaster.games native GLES SDL context`
  found no directly matching first-hand PortMaster FFP remedy. Same ES table10.3
  constraint applies; no Unity/GL4ES driver wrapper imported.
- [Microsoft rasterization rules](https://learn.microsoft.com/en-us/windows/win32/direct3d9/rasterization-rules)
  define integer pixel centers/top-left filling and acknowledge hardware variation.
  Desktop comparison retains independent interior/depth oracles; it does not
  assert bit-identical complete images at edge/UV/depth ties. Initial full-image
  comparison found indexed bounds Mali `(8,6)-(55,41)` versus Mesa `(8,7)-(55,42)`;
  skin bounds match, color transition pixels differ. These observations remain
  visible in captures; exact driver rounding cause unproven. Matched campaign
  captures and complete image parity remain later validation, not passed here.

## Input and sample provenance

Owner executable: 3,338,240 bytes, SHA-1
`d851669ef609b3164e3581aa8dcfbfaec866cb79`. Build extracts shader assembly from
read-only original, assembles selected instructions into D3D8 tokens, then uses
existing renderer bytecode translator and draw path. This diagnostic assembler
is deliberately limited and fails unknown grammar; it does not replace game's
D3DX runtime assembler. Extracted text/tokens remain ignored build artifacts.

- VS source raw offset `0x2b6af4`; used by guest calls `0x4635f0`/`0x463640`
  through shader creation helper `0x463250`. Matrix transform, UV and constant
  diffuse output.
- PS source raw offset `0x28f300`; texture fetch into output.
- Declaration pointer at raw `0x2b6e50` / guest `0x6b6e50`, selected table index 2;
  points to guest `0x6b5728`: position FLOAT3, normal FLOAT3, UV FLOAT2.
- Geometry is analytic quad in game's exact declaration, not captured campaign
  mesh. Three out-of-view prefix vertices and two poison indices independently
  detect ignored base vertex 3 or start-index 2. Four-color texture supplies
  independent orientation oracle. Synthetic geometry never substitutes for
  shader provenance or eventual matched gameplay captures.
- Original geometry at guest `0x6b0d00` / raw `0x2b0d00`: four 24-byte XYZRHW/UV
  vertices. Disassembly at `0x41e08a` selects FVF `0x104`; `0x41e09d..0x41e0a9`
  passes this pointer, stride 24, triangle strip and two primitives to original
  `DrawPrimitiveUP`. Extract unchanged bytes into private generated header;
  draw through same native method. Quad spans 64x64; 64x48 capture deliberately
  clips bottom quarter, with independent quadrant-color expectations.
- Skin VS raw `0x2b6b70`, declaration table index 1 at `0x6b6e4c`; PS raw
  `0x28f31c` exercises diffuse modulation and coissued alpha. Four bone matrices
  scale by 1/2/3/4, weights 1/8, 1/4, 3/8 and implicit remainder 1/4; expected
  scale 2.75. Packed indices select constant rows 48/51/54/57. Wrong byte order
  produces scale 2.25 and fails edge pixels. Mesh inputs analytic; original
  shader and declaration extracted from recognized owner executable.

## RED/GREEN evidence history

All raw paths below local/ignored under `r36s-dumps/sh3/`.

- `20261112T153656817910Z-a8638e`: context-created tracer, overall UNTESTED,
  exit 9; deployment and collection pass. No renderer operation claimed.
- `20261112T153916850498Z-b3c2f8`: active KMSDRM, SDL 2.32.10, ARM Mali-G31,
  native GLES3.2 r13p0, GLSL ES3.20, EGL1.4 ARM. 93 extensions; 16 vertex attrs,
  15 varying vectors, 1024 uniform vectors per stage, 16 texture units,
  max texture 8192. Both highp ranges 127/127, 23 precision bits. No clip-control;
  EXT/OES base-vertex and texture-border-clamp present. Overall remains UNTESTED.
- `20261112T154043343979Z-b3e4f4`: identity assertion passes, active SDL/Mali
  mappings retained in `launcher/graphics-providers.txt`. Lowercase resolved
  Mali filename included after initial filter omitted it.
- `20261112T154923245522Z-995a58`: real game VS/PS and declaration draw matching
  analytic pixels, but GL error `0x0500`; test correctly fails.
- `20261112T155345607862Z-774145`: same indexed/base-vertex/UV oracle passes,
  GL error zero after GLES component-swizzle fix. Complete task still unpassed.
- `20261112T155540058805Z-993e1c`: unchanged original game quad passes four
  quadrant pixels, `game_quad_gl_error=0000`; all three device assertions pass.
- `20261112T155824748868Z-70b820`: skinning assertion fails black edge pixels
  and GL error `0x0501`, reproducing unsupported BGRA vertex-array size.
- `20261112T160000222870Z-607993`: skinning passes with zero error after vertex
  input conversion. All four current device assertions green.
- `20261112T160132521933Z-11d18e`: original D3D8 Clear rectangle `(4,5)-(20,18)`
  colors only expected top-left region; mirrored and out-of-rect pixels black.
- `20261112T160340080710Z-4c6bb0`: clockwise/counterclockwise strip under both
  D3D cull modes passes four keep/drop images, no GL error. Shader Y conversion
  and front-face correction verified together.
- `20261112T160552790864Z-c7b81d`: zero-to-one near/far clipping, LESS ordering,
  depth-write enable/disable pass three captures with zero GL error.
- `20261112T160822414362Z-631fe1`: stencil REPLACE/EQUAL, write mask and depth-fail
  replacement pass independent pixels; discarded color writes stay suppressed.
- `20261112T161051626222Z-c91cb0`: vertex and fragment precision oracles pass;
  nine current evidence tests green. Generated GLSL retained beside PPMs;
  ES300/highp declarations and successful compile/link observed on Mali.
- `20261112T162125919593Z-7d21fc`: RHW case reproduces missing depth clamp:
  pixel `(32,16)` black instead of green, zero GL error. Quad spans z=-.5..1.5,
  reciprocal W=.5..2; depth clear .125. At y16, interpolated depth near zero
  must pass, while per-vertex clamping would yield .25 and fail. Middle pixel
  must fail LESS. ES fallback retains homogeneous depth varying, puts clip Z
  inside volume, recovers screen-linear depth using `gl_FragCoord.w`, then
  clamps fragment depth. Desktop retains native depth clamp for comparison.
- `20261112T162303671886Z-b3a5e3`: same RHW oracle passes with zero error after
  fragment fallback; all ten hardware evidence tests green. Original quad and
  earlier state/shader cases remain passing. This completes RHW RED/GREEN;
  fallback scoped to ES pretransformed vertices, desktop native path retained.
- `20261112T162611063505Z-52e3a7`: complete graphics run exits 0, collection 0.
  Eleven evidence tests pass. Shared context creator selects native GLES;
  game window now requests profile before window creation too. Original quad
  passes actual window backbuffer readback before swap, upright 640x480;
  colors displayed for three seconds. Frontend PIDs preserved, firmware hashes
  all OK, no runtime process or added mount after return. This is scripted
  device presentation evidence, not owner observation of physical menu launch.
- Desktop RED `.port-cache/runtime-tests/20261112T162800875404Z`: Mesa GL4.5
  reached through installed launcher, correctly fails hardware identity before
  reference mode exists. GREEN `20261112T162902056788Z`: explicit reference
  mode passes all oracles; records Mesa/X.org llvmpipe LLVM15, EGL1.5, GLSL430,
  core clip control/native depth clamp. Emits `desktop_reference=PASS`, never
  `gles=PASS`. All 26 executable/launcher checks pass in ARM64 Docker.
- `20261112T162942144091Z-f3598e`: same final reference-mode binary passes
  hardware rerun through saved-workflow deployment test; no software override.
- `20261112T163132465374Z-5b9b83`: review adds FFP packed-color coverage. With
  original FFP color expression and ES four-byte input, expected RGB224/32/128
  renders RGB128/32/224; GL error zero but diagnostic exits9/FAIL. Shader channel
  conversion must cover fixed-function diffuse/specular as well as game VS input.
- `20261112T163408180738Z-117198`: ES FFP conversion restores RGB224/32/128;
  all 12 native assertions pass, exit0 and clean lifecycle. Desktop regression
  `20261112T163408121534Z` also passes including packed-color case.

CCE search returned short previews; `expand_chunk` returned chunk-not-found.
Relevant known source files reviewed directly. CCE index also includes ignored
historical build/device text; no private configuration submitted to CCE.

Build `20261112T161630598276Z` observed existing image tag resolving to image
`sha256:d62ffe311d93d8ccce4c3c8ebf39d7c5dedad230bf717063008219667a961432`
instead of earlier `sha256:b3b941549d2434078ebe086bffd41b125b536c76be35fa0b5ce323653e82e7a7`.
Recipe unchanged; Linux ARM64, glibc2.36, SDL2.26.5, Mesa22.3.6 recorded. Cache
correctly regenerated selected owner input against changed image identity.
No new image or build environment created by this task.
