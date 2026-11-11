# Issue tracker workflow

Read before fetching work, preparing tracker changes, or publishing task results.

## Read task context

1. Use `gh` against `ktodorow/sh3-nx-r36s`. Read selected issue body, every comment, linked blocking issues, and their evidence.
2. Read linked canonical spec in `docs/specs/`, its research, glossary, and relevant ADRs in full. Treat issue history as task history; spec defines current feature acceptance.
3. Verify prerequisite capabilities from actual evidence. A report describing a blocker, another game's result, or a fixture pass is not an R36S capability pass.

When drafting a new feature spec without a selected issue, inspect existing issues for overlap. Keep canonical requirements in repository spec; issue body links spec and states scope, acceptance, prerequisites, and remaining limits.

## Prepare local review

Keep task-owned edits uncommitted. Prepare issue text locally before asking for publication. Show changed files, validation, evidence paths, and limits. Apply triage vocabulary from [triage-labels.md](triage-labels.md) when publication is approved.

Ask: **"Approve publishing and close this task, or leave changes local for review?"** Wait for explicit approval of reviewed work before committing, pushing, posting GitHub content, or closing an issue. Publication-only approval leaves issue open. Creating a feature issue does not authorize closing that new feature before implementation acceptance passes.

## Publish approved work

1. Inspect task-owned diff and staged paths; exclude unrelated work and ignored private data. Commit concrete changes without attribution trailers or automatic issue-closing references.
2. Push and verify remote branch contains final task commit. If no edits remain, verify existing task commits are pushed.
3. Create or update approved issue content with `gh`, using a body file for multiline text. Link canonical spec to pushed commit. Preserve task history; post useful handoff with evidence, limits, and next steps.
4. Close selected verified issue only when approval explicitly includes its closure and its acceptance criteria pass. Verify resulting issue state. A feature spec's publication does not satisfy full-port implementation acceptance.
5. Report final commit link, issue link/state, and any separate publication/collection failure.

Completion requires verified remote commit and requested tracker state, or an explicit report that local review remains pending.
