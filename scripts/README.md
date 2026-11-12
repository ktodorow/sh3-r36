# SH3 host/device workflow

Selected personal-port folder: `/roms2/ports/sh3`, from local `R36S_PORT=sh3`.
Menu entry: `/roms2/ports/Silent Hill 3 Preflight.sh`. This task installs preflight
only; it does not start game runtime, stop frontend, mount runtimes, install
packages, change clocks or modify firmware.

## Private configuration

Copy keys from `.env.example` into ignored `.env`; existing owner-provided
connection settings stay local. Values are parsed as data, never sourced/evaluated.
`R36S_HOST` contains SSH destination, optionally `user@host`. `R36S_SSH_PORT`
defaults to 22; `R36S_PORT` is game folder, never TCP port. Password goes from
runtime environment to SSH askpass through private process pipe, never arguments
or logs. Key authentication also works. Dedicated known-hosts file lives under
ignored `.port-cache/ssh/`; accept new host once and reject changed keys.

`SH3_GAME_DIR` optionally selects owner data; default is repo-local
`SILENT HILL 3`. No credentials or private reference paths belong in tracked docs.
Verify `.env`, game data, `tmpRepo/`, builds, caches and `r36s-dumps/` remain ignored
before creating artifacts. Never run host workflow with shell tracing enabled.

## Runs

Use `python3 scripts/host/r36s.py inventory` for target-only inventory. Use
`python3 scripts/host/r36s.py preflight --reviewed-helpers r36s-dumps/sh3/<inventory-run-id>`
to validate local inputs and deploy/run preflight. One unattended invocation handles authentication, SCP, execution and
collection. Codex invokes host script only; all device access belongs to script.
Inventory runs first; review collected installed PortMaster helpers before
preflight sources them. No foreign downloaded script is executed automatically.
Host compares freshly collected helper hashes against reviewed inventory before
sourcing. If a helper sources additional code, extend inventory and review that
code first. Folder changes and helper changes require fresh review, not a bypass.

Each invocation owns `/roms2/ports/sh3/runs/<UTC-run-id>/` and collects into
`r36s-dumps/sh3/<UTC-run-id>/`. Preserve separate stdout, stderr, execution status,
collection status, input/source identity and existing SH3 logs. Prior runs, owner
data and saves remain untouched. Attempt collection even after deployment or
execution failure; distinguish unavailable device from validation failure.
Inventory includes completed menu-run logs under `device/previous-launches/`,
so physical menu tests can be collected through same unattended host command.

Scripts live in `scripts/host/` and `scripts/device/`; launcher lives in `ports/`.
Only reviewed project preflight files deploy. Original assets do not deploy when
local validation fails. Missing target tools are recorded, never installed.
Target identity does not prove active SDL backend, GLES operations or gameplay.

Unattended SSH preflight sets `SH3_PREFLIGHT_HEADLESS=1`: reports errors in
collected logs without starting PortMaster dialog over active frontend. Installed
menu entry uses normal player message. Physical menu launch/return needs separate
device observation. Preflight starts no gptokeyb process; cleanup suppresses
PortMaster's global gptokeyb kill and restores launcher exit trap after helpers.

Recognized inputs: 3,338,240 bytes with SHA-1
`aa2aca6dba19bf510c9c2e92eefdc15e98266581` (`upstream-aa2aca6d`) or
`d851669ef609b3164e3581aa8dcfbfaec866cb79` (`owner-cd-d851669e`). Exact owner-CD
profile passed upstream patch/PE preconditions; native game code must be generated
from that input. Recognition does not establish runtime or gameplay compatibility.

## Tests

`python3 -m unittest discover -s tests -v` runs interpreted host fixtures through
actual launcher with filesystem/PortMaster external boundaries. Confirmed seam:
installed launcher → useful preflight result → cleanup/return. Fixtures test
errors and cleanup only; actual device evidence is required for G1. No executable
compilation occurs in task #1; later build work must read/create build guide and
use explicit Docker `--platform linux/arm64`.

`SH3_TARGET_EVIDENCE=r36s-dumps/sh3/<run-id> python3 -m unittest discover -s tests -v`
also checks actual collected target observations. These assertions consume real
run evidence, never fabricated target files. Without run path, hardware checks
skip. Owner-CD error fixture uses ignored local executable when available, omits
assets to test missing-data error, and never ships game bytes with tests.
