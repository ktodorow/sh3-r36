# Validate Game data and record current R36S target

Published as [#1](https://github.com/ktodorow/sh3-nx-r36s/issues/1) on 2026-11-11. No labels assigned. This file preserves approved scope; GitHub issue and comments hold current task history.

## What to build

Launch PortMaster preflight, recognize supported owner data, collect current target identity, then return safely to frontend.

Canonical requirements: [Silent Hill 3 R36S spec](../../specs/silent-hill-3-r36s.md). Relevant criteria: AC01, AC02, AC03, AC13. Read full spec and linked context before work; approved task boundary and capability gates apply.

## Acceptance criteria

- [ ] Verify expected executable size/hash and required-data inventory; show useful errors for wrong or missing inputs without altering originals.
- [ ] Verify private-artifact ignore coverage before local configuration or evidence; document selected port folder and reusable unattended host/device workflow before first deployment.
- [ ] Record installed firmware, kernel, libc, SDL, driver/provider and controller identities through saved scripts; missing tools are findings rather than installation instructions.
- [ ] Collect run identity, stdout, stderr, exit status and failure results separately; keep credentials private and preserve prior logs/saves. Host fixtures cover observable preflight errors and cleanup only.

## Blocked by

None (can start immediately).

Dependencies reference local draft IDs, not GitHub issue numbers. Verify actual prerequisite passes before dependent implementation; blocker reports and reference-port results are not capability passes.
