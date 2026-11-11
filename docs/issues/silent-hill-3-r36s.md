# Deliver full Silent Hill 3 port on R36S with native GLES3

Publication draft. Tickets remain unlabeled under latest user instruction; do not apply `ready-for-agent`. Canonical requirements: [Silent Hill 3 R36S spec](../specs/silent-hill-3-r36s.md). Before posting, replace local document links with verified pushed-commit links; keep feature issue open. [Ticket breakdown](silent-hill-3-r36s-ticket-breakdown.md) approved; [individual issue drafts](silent-hill-3-r36s/README.md) remain local at user's request. No parent issue publication implied.

## Problem Statement

Owner needs complete Silent Hill 3 on personal dArkOS R36S. ARM64 parity alone does not supply graphics compatibility, original FMVs, stable performance, or full-campaign correctness.

## Solution

Native Linux ARM64 plus direct GLES3 Full port, launched through PortMaster. Target stable 30 FPS at lowest graphics, prefer 640×480 Internal resolution, fall back to 320×240, retain 640×480 Output resolution and intended game speed.

## User Stories

Canonical spec contains 42 user stories covering complete campaign, original movies, controls, audio, save/load, lifecycle, rendering, performance, reproducible builds, and evidence. Implementation tasks must reference relevant stories and acceptance criteria from that document.

## Implementation Decisions

- Reuse existing Linux runtime and adapted D3D8 renderer; preserve desktop baseline.
- Restore every original FMV; identify real media before choosing decoder integration.
- Preserve original data and saves; isolate compatible ARM64 dependencies.
- Reuse Linux ARM Docker environment and project-owned unattended host/device workflows.
- Personal-device acceptance first; public PortMaster submission later.

## Testing Decisions

User-confirmed public boundary: installed PortMaster launcher → complete game session → clean frontend return. Actual R36S evidence required for graphics, movies, physical input, audio, saves, and performance. Host fixtures cover launcher failures/cleanup only. Behavior changes use observed RED–GREEN–REFACTOR.

First actionable work: verify supported owner data, prepare documented scripted target inventory and reusable build workflow, then establish actual runtime/GLES capabilities. Capability gates in canonical spec prevent dependent implementation from treating blocker reports or another game's results as passes.

Acceptance requires complete campaign and endings, all original movies, correct rendering/timing, reachable controls, persistent saves/settings, reliable audio/cleanup, bounded memory, and measured stability. No SH3 device gate has passed; no 30 FPS result exists.

## Out of Scope

Public catalogue submission, broad device support, Switch emulation, GL4ES-only route, Enhanced Edition/HD content, 60 FPS, firmware replacement, and commercial asset redistribution.

## Further Notes

[Feasibility report](../../reports/Silent%20Hill%203%20R36S%20feasibility.md), [accepted architecture](../adr/0001-native-linux-gles3-r36s.md), and [source checks](../../research_notes/Silent%20Hill%203%20R36S%20spec/source-checks.md) preserve evidence and limits. Movie codec, current device extensions, CPU/RAM fit, exact stability tolerance, and runtime performance require verification. Spec publication does not pass Full port acceptance or authorize closing this feature issue.
