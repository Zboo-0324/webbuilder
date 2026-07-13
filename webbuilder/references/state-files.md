# State Files

WebBuilder stores project memory in `webbuilder/`. These files are the source of truth after initialization.

## Contents

- Required files and readiness statuses
- Project rules, requirements, and system design
- Task plan and loop state
- Validation log and delivery report
- Migration and phase checks

## Required Files

```text
webbuilder/
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

V1.4 requires `schema_version: 1.4` in `loop-state.md`. For V1, V1.0, V1.1, V1.2, or V1.3 state, run `migrate-state.py --dry-run` and then apply it. A missing version is treated as V1; any other explicit unsupported version stops for manual migration. The migration backs up every changed state file, preserves project content, adds only mechanical metadata, and sets tasks without a documented risk basis to `unclassified` for explicit Planner classification.

## State Kernel Ownership and Recovery

`loop-state.md` is the canonical State Kernel record. Schema 1.4 requires `delivery_mode`, `autonomy_scope`, `stop_reason`, `resume_checkpoint`, `active_run_id`, `state_revision`, and `pending_transition` alongside the existing orchestration fields.

State-changing operations create a journal in `webbuilder/.transitions/` before modifying the participating files. The journal records the original and target hashes and target text; a completed transition is renamed with the `.complete.json` suffix. `transition-state.py --recover` completes a single pending journal only when files match their recorded original, intermediate, or target states, and rejects divergent files or multiple pending journals.

Agents may edit descriptive project content and append evidence, but may not manually set approval, readiness, acceptance, integration, stop/resume, or delivery-success values. The State Kernel owns those control values; use its transition and checker APIs, or stop and ask when no supported transition exists.

Use `transition-state.py --event <event>` for lifecycle changes. Lifecycle events construct their control updates internally and reject `--set`: `confirm-user-discovery`, `confirm-requirements`, `mark-project-rules-ready`, `mark-system-design-ready`, `mark-task-plan-ready`, `start-task --task <TASK-ID>`, `submit-task --task <TASK-ID>`, `accept-task --task <TASK-ID>`, `complete-task-integration --task <TASK-ID>`, `complete-delivery-report`, `pause`, `block --reason <declared-reason>`, `resume`, and `deliver`.

`edit-descriptive-content --set <file:key=value>` is the sole generic update form. It rejects every lifecycle control key, including statuses, readiness, task selection, stop/resume, revision, pending-transition, and orchestration fields. Each lifecycle event validates its source and target status plus its applicable gate before the journaled write.

Readiness-success events validate a proposed state snapshot before writing: `mark-project-rules-ready` requires valid structure and no unchecked Sources Read entry; `confirm-user-discovery` requires valid structure and recorded decisions; `confirm-requirements`, `mark-system-design-ready`, and `mark-task-plan-ready` require valid structure with no checker-defined placeholder content; `complete-delivery-report` and `deliver` require the full delivery gate.

Before every resume, recover and structure-check the State Kernel:

```text
python <skill-root>/scripts/transition-state.py --target <project-root> --recover
python <skill-root>/scripts/check-state.py --target <project-root> --phase structure
```

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

## User Discovery

discovery_status: pending

### AI Working Hypothesis

- not recorded

### Questions Asked

- generated dynamically after reading the user's brief and project context

### User Decisions

- not recorded

## First-Principles Analysis

### Core Outcome

- State the user or business outcome that must be true when the work succeeds.

### Hard Constraints and Invariants

- State facts the design must preserve.

### Assumptions and Evidence

- Assumption: evidence and consequence if false.

## Open Questions

- List questions that block safe implementation.

## Confirmed Requirements

| ID | Requirement | Priority | Acceptance Signal |
|---|---|---|---|
| REQ-001 | Describe the first confirmed requirement. | Must | How it will be verified. |
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

Purpose: list tasks, dependencies, allowed paths, validation, parallel groups, integration policies, and independent repair scopes.

Use `pr_worktree` with a Git integration strategy for isolated task branches. Use `single_session` with `direct_apply` when accepted changes are already in the main workspace, including non-Git projects.

Template:

```markdown
# Task Plan

status: draft

## Current Strategy

Default to one task at a time. Use controlled multi-worker mode only for no-conflict tasks.
For non-Git or single-session tasks, pair `handoff_mode: single_session` with `integration_strategy: direct_apply`.

## Shared Contract Paths

- webbuilder/
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
- risk_level: unclassified
- risk_basis:
  - Record the concrete reason and affected surface before dispatch.
- checker_strategy: single_session
- review_mode: standard
- adversarial_review:
  - not_applicable
- user_approval: not_required
- approval_evidence:
  - not_applicable
- rollback_plan:
  - not_applicable
- recovery_point:
  - not_applicable
- residual_risk_owner: not_applicable
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
- shared_resources:
  - none
- conflict_domains:
  - none
- integration_dependencies:
  - none
- task_repair_attempt: 0
- task_failure_fingerprint: none
- task_same_fingerprint_count: 0
- integration_repair_attempt: 0
- integration_failure_fingerprint: none
- integration_same_fingerprint_count: 0
- integration_policy: orchestrator_review_then_serial_integration
```

## loop-state.md

Purpose: record current workflow status and active constraints.

Keep the top-level orchestration keys and machine-checked Active Constraints exactly as generated. Add project-specific constraints as new bullets; do not paraphrase or replace protocol markers. Use `unknown` for uninspected host capability or slot counts.

Template:

```markdown
# Loop State

workflow: spec2web
schema_version: 1.4
status: active
current_phase: project_rules
current_task: null
active_parallel_group: null
delivery_mode: guided
autonomy_scope: unconfirmed
stop_reason: none
resume_checkpoint: none
active_run_id: null
state_revision: 1
pending_transition: null
execution_mode: single
host_agent_capability: unknown
available_child_slots: unknown
selected_workers: 0
active_checker_strategy: single_session

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

### TASK-001 / acceptance

- gate: acceptance
- task_status: submitted_for_acceptance
- submission_commit: hash or direct_apply
- developer_identity: agent, session, or role
- tester_identity: agent, session, or role
- tester_result: passed | failed | blocked
- reviewer_identity: agent, session, or role
- reviewer_result: approved | repair | blocked
- adversarial_cases_expected: CASE-001, CASE-002, or not_applicable
- adversarial_cases_passed: CASE-001, CASE-002, or not_applicable
- disagreement_status: none | unresolved | resolved
- orchestrator_decision: accepted | repair | blocked
- residual_risk: none or concrete risk

### TASK-001 / integration

- gate: integration
- integration_strategy: merge | squash_merge | cherry_pick | integration_commit | direct_apply
- integration_commit: hash or direct_apply
- main_workspace_verification: passed | failed
- verification_evidence: exact command or durable manual evidence
- final_task_status: complete | needs_repair | blocked
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

The migration creates a timestamped backup directory under the project's `webbuilder/` state folder before writing. Keep it until structure and execution checks pass, then remove it or keep it local; do not commit migration backups.

Run the bundled checker from the installed or project-local Skill directory:

```text
python <skill-root>/scripts/check-state.py --target <project-root> --phase structure
python <skill-root>/scripts/check-state.py --target <project-root> --phase execution
python <skill-root>/scripts/check-state.py --target <project-root> --phase task --task <TASK-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase parallel --parallel-group <PG-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase acceptance --task <TASK-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase integration --task <TASK-ID>
python <skill-root>/scripts/check-state.py --target <project-root> --phase delivery
```

- `structure` checks schema, required files, workflow markers, orchestration metadata, design sections, task contracts, and allowed status values.
- `execution` additionally requires confirmed or ready baselines, no placeholder content, and an active workflow.
- `task` additionally checks the selected task, dependencies, execution mode, task-owned checker strategy, handoff, workspace, repair budget, and current-task state.
- `parallel` additionally checks host capacity, group size, dependencies, unique worktrees, path overlap, Shared Contract Paths, declared shared resources, conflict domains, integration dependencies, and checker independence.
- `acceptance` checks the submitted task package, independent identities, declared review evidence, adversarial coverage, disagreement status, and critical controls.
- `integration` checks accepted status, the declared integration strategy, integration evidence, and successful main-workspace verification.
- `delivery` additionally requires all tasks complete, an acceptance and integration evidence closure for every task, a complete delivery report, and terminal workflow state.

Task and integration repair are independent. `task_repair_attempt`, `task_failure_fingerprint`, and `task_same_fingerprint_count` cover task execution and acceptance within the task's repair budget. `integration_repair_attempt`, `integration_failure_fingerprint`, and `integration_same_fingerprint_count` cover post-acceptance integration, with its separate budget and stop condition. Do not copy a failure count or fingerprint from one scope into the other.
