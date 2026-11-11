# Triage labels

Read before setting issue triage status in `ktodorow/sh3-nx-r36s`.

Use one current triage role per issue:

| Label | Meaning |
| --- | --- |
| `needs-triage` | Scope, ownership, or next action has not been assessed. |
| `needs-info` | Required information or decision is missing. State what is needed. |
| `ready-for-agent` | Scope and next agent action are clear. Dependent implementation still waits for verified prerequisite capabilities. |
| `ready-for-human` | Next action requires user review, approval, hardware action, or another human decision. |
| `wontfix` | Explicit decision not to pursue issue; record reason before closure. |

For an approved `to-spec` publication, use `ready-for-agent`; preserve implementation gates in issue body. Before changing labels, inspect existing roles and remove superseded triage roles. Check repository label availability with `gh`; create missing vocabulary only within approved publication scope. Label changes are GitHub writes and follow [issue-tracker.md](issue-tracker.md) approval workflow.
