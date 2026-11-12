# SH3 host/device workflow

Selected personal-port folder: `/roms2/ports/sh3`, from local `R36S_PORT=sh3`.
Menu entries: `/roms2/ports/Silent Hill 3 Preflight.sh` and
`/roms2/ports/Silent Hill 3 Runtime Diagnostics.sh`. Preflight checks data;
runtime diagnostics exercise native memory, threads, signals and timers without
rendering. Workflows do not stop frontend, mount runtimes, install packages,
change clocks or modify firmware.

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
Only reviewed project files and explicit native package files deploy. Original
assets do not deploy in these workflows. Missing target tools are recorded, never installed.
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

## Native runtime diagnostics (task #2)

`python3 scripts/host/build.py` generates owner-profile game code and compiles
Linux ARM64 inside pinned reusable Docker environment. Read
[build guide](../docs/agents/builds.md). Final personal package: `dist/runtime/`.
Run build and deployment serially. Build snapshots allowlisted source without
private configuration; only selected executable mounts read-only. Each build
retains logs, status, hashes and package under `.port-cache/builds/<UTC-id>/`.
Verified generation cache reuses only matching input/generator/image and matching
generated file hashes. Previous final packages remain under `dist/runtime-previous-*`.
Debug symbols stay host-only; device receives stripped AArch64 binary.

`python3 scripts/host/r36s.py runtime --reviewed-helpers r36s-dumps/sh3/<inventory-run-id>`
deploys that package into `/roms2/ports/sh3/runtime/`, checks complete ELF dependency
closure, installs `/roms2/ports/Silent Hill 3 Runtime Diagnostics.sh`, invokes it
headlessly and collects launcher results. Each run preserves deployed binary and
build identity in its own payload. Original assets remain host-only. Diagnostics
open no graphics context, mount no runtime, alter no clocks and need no game data.
Firmware SDL and graphics providers stay in place; no private libraries required
unless actual closure demonstrates otherwise. Physical menu return still needs
owner observation; scripted frontend/process evidence supplements it.
Select **Silent Hill 3 Runtime Diagnostics**, not Preflight, for this check.
Refresh frontend game list if new entry is absent. Runtime menu derives package
folder from its own installed location; no host environment needed.

`python3 scripts/host/test-runtime.py` runs real built binary through launcher in
same ARM64 Docker image with PortMaster fixture. No game data or private config
mounts. RED/GREEN logs stay under `.port-cache/runtime-tests/<UTC-id>/`.
These passes establish launcher behavior in Docker, not device compatibility.

`python3 scripts/host/clean-build.py` removes disposable `build/` tree only after
checking no project container runs. `--docker` additionally removes stopped
labelled containers and unused labelled `sh3-r36s-build` images, without force.
Source, generated C, owner data, `dist/`, `.port-cache/` and `r36s-dumps/` survive.
No named volumes or dedicated builder created; shared Docker layer cache remains
untouched. Generation/build caches inside `build/` are disposable.

## Launcher tests

`python3 -m unittest discover -s tests -v` runs interpreted host fixtures through
actual launcher with filesystem/PortMaster external boundaries. Confirmed seam:
installed launcher → useful preflight result → cleanup/return. Fixtures test
errors and cleanup only; actual device evidence is required for G1. No executable
compilation occurs in task #1; later build work must read/create build guide and
use explicit Docker `--platform linux/arm64`.

Build/cleanup CLI boundary also confirmed by owner for task #2. Its fixtures check
failed-build evidence and scoped cleanup, with Docker mocked only as external
process. Documentation-only edits use link, content and diff checks instead of TDD.

`SH3_TARGET_EVIDENCE=r36s-dumps/sh3/<run-id> python3 -m unittest discover -s tests -v`
also checks actual collected target observations. These assertions consume real
run evidence, never fabricated target files. Without run path, hardware checks
skip. Owner-CD error fixture uses ignored local executable when available, omits
assets to test missing-data error, and never ships game bytes with tests.

`SH3_RUNTIME_EVIDENCE=r36s-dumps/sh3/<native-run-id> python3 -m unittest discover -s tests -v`
checks actual native diagnostics, target dependency closure, firmware hashes,
frontend process preservation and absence of leftover runtime processes/mounts.

`SH3_NATIVE_PHYSICAL_EVIDENCE=r36s-dumps/sh3/<inventory-run-id>` adds assertion over
collected successful physical diagnostics menu log. Collect after owner observes
frontend return using saved `inventory` command; no original game upload needed.
