#!/usr/bin/env python3
"""Initialize lightweight Spec2Web state files."""

from __future__ import annotations

import argparse
from pathlib import Path

from state_schema import SCHEMA_VERSION, STATE_DIR_NAME


STATE_GITIGNORE = """.transitions/
.migration-backup-*/
"""


TEMPLATES = {
    "project-rules.md": """# Project Rules

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
""",
    "requirements-baseline.md": """# Requirements Baseline

## Status

status: draft
confirmation_status: pending
contract_revision: 1
approved_contract_revision: null
approval_digest: null
approval_scope: requirements_design_stack_ui_execution
approval_evidence: null
approved_by: null
approved_at: null
discovery_method: interactive

## User Discovery

discovery_status: pending

### AI Working Hypothesis

- not recorded

### Questions Asked

- generated dynamically after reading the user's brief and project context

### User Decisions

- not recorded

## Solution Contract

```json contract-material
{
  "problem": "not recorded",
  "desired_outcome": "not recorded",
  "target_users": [],
  "primary_jobs": [],
  "core_capabilities": [],
  "non_goals": [],
  "primary_workflows": [],
  "page_navigation_summary": "not recorded",
  "ui_direction": "not recorded",
  "technology_profile": "not recorded",
  "public_interfaces": [],
  "data_boundary": "not recorded",
  "permission_boundary": "not recorded",
  "delivery_assumptions": [],
  "material_risks": [],
  "acceptance_signals": [],
  "capabilities": {},
  "workload_envelope": {
    "task_count": "not estimated",
    "browser_flows": [],
    "external_dependencies": [],
    "quality_gates": [],
    "repair_budgets": {"task": 3, "integration": 5},
    "available_concurrency": "unknown"
  }
}
```

## First-Principles Analysis

### Core Outcome

- not recorded

### Hard Constraints and Invariants

- not recorded

### Assumptions and Evidence

- not recorded

## Open Questions

- None recorded yet.

## Confirmed Requirements

| ID | Requirement | Priority | Acceptance Signal |
|---|---|---|---|
| REQ-001 | Replace with the first confirmed requirement. | Must | Replace with verification method. |
""",
    "system-design.md": """# System Design

status: draft
based_on_contract_revision: 1

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

- None recorded yet.

## Data Model

- None recorded yet.

## API Contract

- None recorded yet.

## Permissions

- None recorded yet.

## Verification Strategy

- Build command: not recorded
- Test command: not recorded
- Browser or manual verification: not recorded
""",
    "task-plan.md": """# Task Plan

status: draft
based_on_contract_revision: 1

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

### TASK-001: Replace with first task title

- requirement_ids: REQ-001
- goal: Replace with one concrete outcome.
- dependencies: none
- status: pending
- risk_level: unclassified
- risk_basis:
  - not recorded
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
  - replace/with/path
- expected_outputs:
  - replace with expected output
- verification:
  - replace with exact command or manual check
- completion_criteria:
  - replace with worker-observable condition for submitting the task
- acceptance_gate:
  - replace with Orchestrator check required before accepting or merging
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
- execution_workspace: main
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
""",
    "loop-state.md": f"""# Loop State

workflow: spec2web
schema_version: {SCHEMA_VERSION}
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
""",
    "validation-log.md": """# Validation Log

## Entries

No validation has been recorded yet.
""",
    "delivery-report.md": """# Delivery Report

status: draft

## Completed

- Nothing delivered yet.

## Validation

- No validation recorded yet.

## Run Instructions

- Not recorded yet.

## Known Risks

- None recorded yet.

## Not Completed

- Work has not started.
""",
}


def initialize(target: Path) -> tuple[list[Path], list[Path]]:
    state_dir = target / STATE_DIR_NAME
    state_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []
    skipped: list[Path] = []

    for filename, content in TEMPLATES.items():
        path = state_dir / filename
        if path.exists():
            skipped.append(path)
            continue
        path.write_text(content, encoding="utf-8", newline="\n")
        created.append(path)

    gitignore = state_dir / ".gitignore"
    if gitignore.exists():
        skipped.append(gitignore)
    else:
        gitignore.write_text(STATE_GITIGNORE, encoding="utf-8", newline="\n")
        created.append(gitignore)

    return created, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize WebBuilder state files.")
    parser.add_argument(
        "--target",
        default=".",
        help="Project directory where the webbuilder state folder should be created.",
    )
    args = parser.parse_args()

    target = Path(args.target).resolve()
    created, skipped = initialize(target)

    print(f"WebBuilder state directory: {target / STATE_DIR_NAME}")
    for path in created:
        print(f"created: {path}")
    for path in skipped:
        print(f"exists:  {path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
