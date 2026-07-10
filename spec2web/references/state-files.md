# State Files

Spec2Web stores project memory in `spec2web/`. These files are the source of truth after initialization.

## Contents

- Required files and readiness statuses
- Project rules, requirements, and system design
- Task plan and loop state
- Validation log and delivery report
- Migration and phase checks

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

## Readiness Statuses

Use explicit top-level statuses so file existence cannot be mistaken for phase readiness:

- `project-rules.md`: `draft` -> `ready`
- `requirements-baseline.md`: `draft` -> `confirmed`
- `system-design.md`: `draft` -> `ready`
- `task-plan.md`: `draft` -> `ready`
- `delivery-report.md`: `draft` -> `complete`
- `loop-state.md`: `active`, `paused`, `blocked`, `disabled`, or terminal `delivered`

Do not change a status merely to satisfy the checker. Change it only after the file's phase exit gate is met.

V1.2 requires `schema_version: 1.2` in `loop-state.md`. For V1 or V1.1 state, run `migrate-state.py --dry-run` and then apply it. A missing version is treated as V1; any other explicit unsupported version stops for manual migration. The migration backs up changed state files, preserves project content, adds review metadata and first-principles sections, and leaves business judgments for explicit repair.

## project-rules.md

Purpose: summarize implementation-relevant instructions from `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, README, and user-provided rules.

Template:

```markdown
# Project Rules

status: draft

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

## First-Principles Analysis

### Core Outcome

- State the user or business outcome that must be true when the work succeeds.

### Hard Constraints and Invariants

- State facts the design must preserve.

### Assumptions and Evidence

- Assumption: evidence and consequence if false.

## Open Questions

- List questions that block safe implementation.
```

## system-design.md

Purpose: freeze design facts before task execution.

Template:

```markdown
# System Design

status: draft

## Technology Strategy

### Existing Stack

- frontend: not recorded
- backend: not recorded
- database: not recorded
- styling: not recorded
- testing: not recorded
- build: not recorded
- deployment: not recorded

### Options Considered

| Option | Best For | Tradeoffs | Decision |
|---|---|---|---|
| Existing stack | Preserve current project conventions. | Replace with project-specific tradeoffs. | selected |

### Selected Stack

- frontend: not recorded
- backend: not recorded
- database: not recorded
- styling: not recorded
- testing: not recorded
- validation: not recorded
- deployment assumption: not recorded

### Dependency Policy

- Reuse existing dependencies first.
- Add new dependencies only with justification.
- Record install commands and lockfile impact.

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

### Component Conventions

- buttons: not recorded
- forms: not recorded
- tables/lists: not recorded
- modals/drawers: not recorded
- feedback/toasts: not recorded
- icons: not recorded

### State Coverage

- loading: not recorded
- empty: not recorded
- error: not recorded
- disabled: not recorded
- success: not recorded
- permission denied: not recorded

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

Use `pr_worktree` with a Git integration strategy for isolated task branches. Use `single_session` with `direct_apply` when accepted changes are already in the main workspace, including non-Git projects.

Template:

```markdown
# Task Plan

status: draft

## Current Strategy

Default to one task at a time. Use controlled multi-worker mode only for no-conflict tasks.
For non-Git or single-session tasks, pair `handoff_mode: single_session` with `integration_strategy: direct_apply`.

## Shared Contract Paths

- spec2web/
- package.json
- pyproject.toml
- migrations/
- openapi/

## Tasks

### TASK-001: Task title

- requirement_ids: REQ-001
- goal: Specific result.
- dependencies: none
- status: pending
- risk_level: standard
- review_mode: standard
- adversarial_review:
  - not applicable
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
- repair_budget: 3
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

Keep the top-level orchestration keys and machine-checked Active Constraints exactly as generated. Add project-specific constraints as new bullets; do not paraphrase or replace protocol markers. Use `unknown` for uninspected host capability or slot counts.

Template:

```markdown
# Loop State

workflow: spec2web
schema_version: 1.2
status: active
current_phase: project_rules
current_task: null
active_parallel_group: null
execution_mode: single
host_agent_capability: unknown
available_child_slots: unknown
selected_workers: 0
checker_strategy: single_session

## Active Constraints

- one task per worker
- continue ready tasks until blocked or delivered
- main session remains Orchestrator
- delegated or parallel tasks use PR/worktree handoff when Git is available
- delegated workers submit, Orchestrator accepts
- unauthorized external AI workers are forbidden
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
- review: standard or adversarial; Tester and Reviewer conclusions for high/critical work
- next_action: continue, repair, blocked
```

## delivery-report.md

Purpose: final user-facing handoff.

Template:

```markdown
# Delivery Report

status: draft

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

## Phase Checks

For existing V1 state, migrate before checking:

```text
python <skill-root>/scripts/migrate-state.py --target <project-root> --dry-run
python <skill-root>/scripts/migrate-state.py --target <project-root>
```

The migration creates a timestamped backup directory under the project's `spec2web/` state folder before writing. Keep it until structure and execution checks pass, then remove it or keep it local; do not commit migration backups.

Run the bundled checker from the installed or project-local Skill directory:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase structure
python <skill-root>/scripts/check-state.py --target <project-root> --phase execution
python <skill-root>/scripts/check-state.py --target <project-root> --phase task --task <TASK-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase parallel --parallel-group <PG-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase delivery
```

- `structure` checks schema, required files, workflow markers, orchestration metadata, design sections, task contracts, and allowed status values.
- `execution` additionally requires confirmed or ready baselines, no placeholder content, and an active workflow.
- `task` additionally checks the selected task, dependencies, execution mode, handoff, workspace, and current-task state.
- `parallel` additionally checks host capacity, group size, dependencies, unique worktrees, path overlap, Shared Contract Paths, and checker independence.
- `delivery` additionally requires all tasks complete, recorded validation evidence, a complete delivery report, and terminal workflow state.
