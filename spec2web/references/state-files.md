# State Files

Spec2Web stores project memory in `spec2web/`. These files are the source of truth after initialization.

## Required Files

```text
spec2web/
├── project-rules.md
├── requirements-baseline.md
├── system-design.md
├── task-plan.md
├── loop-state.md
├── validation-log.md
└── delivery-report.md
```

## project-rules.md

Purpose: summarize implementation-relevant instructions from `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, README, and user-provided rules.

Template:

```markdown
# Project Rules

## Sources Read

- [ ] CLAUDE.md
- [ ] AGENTS.md
- [ ] GEMINI.md
- [ ] README.md

## Active Rules

- Read existing code before writing.
- State assumptions before implementation.
- Keep changes small and focused.
- Verify before claiming completion.
- Avoid new dependencies unless justified.

## Open Rule Conflicts

- None.
```

## requirements-baseline.md

Purpose: hold confirmed requirements. Do not change without user approval.

Template:

```markdown
# Requirements Baseline

## Status

status: draft

## Requirements

| ID | Requirement | Priority | Acceptance Signal |
|---|---|---|---|
| REQ-001 | Describe the first confirmed requirement. | Must | How it will be verified. |

## Assumptions

- List explicit assumptions.

## Open Questions

- List questions that block safe implementation.
```

## system-design.md

Purpose: freeze design facts before task execution.

Template:

```markdown
# System Design

## Technology Strategy

### Existing Stack

- frontend: not recorded
- backend: not recorded
- database: not recorded
- styling: not recorded
- testing: not recorded
- build: not recorded
- deployment: not recorded

### Selected Stack

- frontend: not recorded
- backend: not recorded
- database: not recorded
- styling: not recorded
- testing: not recorded
- validation: not recorded
- deployment assumption: not recorded

### Verification Commands

- install: not recorded
- build: not recorded
- test: not recorded
- lint/typecheck: not recorded
- browser/manual: not recorded

## Interface Design Baseline

### Product Shape

- audience: not recorded
- primary jobs: not recorded
- density: not recorded
- visual tone: not recorded

### User Flows

| Flow | Entry | Core Steps | Success State | Requirement IDs |
|---|---|---|---|---|

### Pages

| Page | Purpose | Primary Actions | Key States | Requirement IDs |
|---|---|---|---|---|

### Layout Direction

- navigation: not recorded
- page structure: not recorded
- information hierarchy: not recorded
- desktop constraints: not recorded
- mobile constraints: not recorded

### UI Verification

- browser checks: not recorded
- screenshot or visual checks: not recorded
- responsive checks: not recorded
- accessibility checks: not recorded

## Pages

- Page name: purpose, key actions, requirement IDs.

## Data Model

- Entity: fields, relationships, validation.

## API Contract

- Method path: request, response, errors, requirement IDs.

## Permissions

- Role: allowed actions.

## Verification Strategy

- Build command:
- Test command:
- Browser or manual verification:
```

## task-plan.md

Purpose: list tasks, dependencies, allowed paths, validation, parallel groups, and integration policies.

Template:

```markdown
# Task Plan

## Current Strategy

Default to one task at a time. Use controlled multi-worker mode only for no-conflict tasks.

## Tasks

### TASK-001: Task title

- requirement_ids: REQ-001
- goal: Specific result.
- dependencies: none
- status: pending
- handoff_mode: pr_worktree
- integration_strategy: squash_merge
- allowed_paths:
  - path/pattern
- expected_outputs:
  - path or behavior
- verification:
  - exact command or manual check
- completion_criteria:
  - worker-observable condition for submitting the task
- acceptance_gate:
  - Orchestrator check required before accepting or merging
- submission_package:
  - branch name and commit hash
  - worktree path
  - implementation summary
  - changed files
  - verification evidence
  - known risks or follow-up
- risks_or_blockers:
  - none
- execution_workspace: main or worktree
- parallel_group: none
- integration_policy: orchestrator_review_then_serial_integration
```

## loop-state.md

Purpose: record current workflow status and active constraints.

Template:

```markdown
# Loop State

workflow: spec2web
status: active
current_phase: project_rules
current_task: null
active_parallel_group: null

## Active Constraints

- one task per worker
- continue ready tasks until blocked or delivered
- main session remains Orchestrator
- implementation tasks use PR/worktree handoff when Git is available
- delegated workers submit, Orchestrator accepts
- external AI workers are forbidden
- no unplanned full-project generation
- every task maps to requirements
- update state before moving on
- verify before claiming done
- follow project-rules.md
- Orchestrator controls integration

## Worktrees

| Task | Branch | Path | Status |
|---|---|---|---|

## PR Handoffs

| Task | Mode | Branch | Worktree | Commit | PR URL | Integration Strategy | Integration Commit | Status |
|---|---|---|---|---|---|---|---|---|

## Next Step

Read project rules and update project-rules.md.
```

## validation-log.md

Purpose: preserve verification evidence.

Template:

```markdown
# Validation Log

## Entries

### YYYY-MM-DD HH:MM - TASK-001

- command: exact command
- result: passed or failed
- evidence: summary of output
- next_action: continue, repair, blocked
```

## delivery-report.md

Purpose: final user-facing handoff.

Template:

```markdown
# Delivery Report

## Completed

- List completed user-facing features.

## Validation

- List commands and outcomes.

## Run Instructions

- Exact local run steps.

## Known Risks

- List risks or limitations.

## Not Completed

- List intentional omissions or blockers.
```
