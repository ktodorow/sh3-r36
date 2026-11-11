---
status: accepted
date: 2026-11-11
---

# Build native Linux ARM64 with GLES3

Use existing Linux host runtime and adapt custom D3D8 renderer directly to GLES3 for personal R36S port. User selected this route after source review found desktop GL4.3+/GLSL430 dependencies outside GL4ES scope, while cached owner-device diagnostics confirmed native Mali-G31 GLES3.2; GLES3 retains more existing shader/resource structure than GL2/GL4ES downgrade.

Keep desktop backend as comparison baseline. Reuse PortMaster launch/control patterns; verify current firmware extensions before selecting optional GLES paths. Renderer adaptation commits project to explicit shader, clip/depth, texture-format and draw compatibility work; stable 30 FPS, physical-memory fit and full campaign correctness remain unproved.

Full-port target includes campaign, original videos, audio, controls and save/load: 30 FPS first, lowest graphics, 640×480 internal preferred, 320×240 fallback. Public PortMaster submission follows personal-device success.

Evidence and validation gates: [research report](../../reports/Silent%20Hill%203%20R36S%20feasibility.md). Terms: [glossary](../../GLOSSARY.md).
